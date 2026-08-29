#!/usr/bin/env python3
"""Shared deterministic helpers for the V3 scientific-figure workflow."""

from __future__ import annotations

import html
import json
import os
import shutil
import subprocess
import tempfile
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from figure_artifacts import json_schema_errors, load_json, sha256_file, write_json


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
SCHEMA_DIR = REPO_ROOT / "schemas"


def resolve_hex_paint(value: Any, colors: Mapping[str, Any], fallback: str) -> str:
    """Resolve a CSS variable or token name to a safe six-digit hex paint."""

    def candidate(raw_value: Any, seen_tokens: set[str]) -> str | None:
        if not isinstance(raw_value, str):
            return None
        raw = raw_value.strip()
        if not raw:
            return None
        if raw == "none":
            return "none"
        variable = re.fullmatch(r"var\(--([A-Za-z0-9_-]+)\)", raw)
        token = variable.group(1) if variable else (raw if raw in colors else None)
        if token is not None:
            if token in seen_tokens:
                return None
            return candidate(colors.get(token), {*seen_tokens, token})
        match = re.fullmatch(r"#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})", raw)
        if match is None:
            return None
        digits = match.group(1)
        if len(digits) == 3:
            digits = "".join(character * 2 for character in digits)
        return "#" + digits.upper()

    return candidate(value, set()) or candidate(fallback, set()) or "#000000"


def _pillow_font_supports_text(font: Any, value: str) -> bool:
    """Return false when a requested glyph maps to the font's replacement glyph."""
    try:
        missing = font.getmask("\N{REPLACEMENT CHARACTER}")
        missing_signature = (missing.size, bytes(missing))
        for character in set(value):
            if character.isspace() or character == "\N{REPLACEMENT CHARACTER}":
                continue
            glyph = font.getmask(character)
            if (glyph.size, bytes(glyph)) == missing_signature:
                return False
        return True
    except Exception:
        return False


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def validate_schema(instance: Any, schema_name: str) -> List[str]:
    schema = load_json(SCHEMA_DIR / schema_name)
    return json_schema_errors(instance, schema)


def require_valid(instance: Any, schema_name: str) -> None:
    errors = validate_schema(instance, schema_name)
    if errors:
        raise ValueError("%s validation failed:\n%s" % (schema_name, "\n".join(errors)))


def artifact_record(path: Path, base: Path) -> Dict[str, str]:
    return {
        "path": str(path.resolve().relative_to(base.resolve())),
        "sha256": sha256_file(path),
    }


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def find_chrome() -> Path | None:
    candidates = [
        Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    command = shutil.which("google-chrome") or shutil.which("chromium")
    return Path(command) if command else None


def find_soffice() -> Path | None:
    candidates = [
        Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"),
        Path("/usr/bin/libreoffice"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    command = shutil.which("soffice") or shutil.which("libreoffice")
    return Path(command) if command else None


def find_pdftoppm() -> Path | None:
    command = shutil.which("pdftoppm")
    return Path(command) if command else None


def convert_svg_to_pdf(svg_path: Path, pdf_path: Path) -> Dict[str, Any]:
    soffice = find_soffice()
    if soffice is None:
        return {"status": "BLOCKED", "reason": "LibreOffice not found"}
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="figure-soffice-") as temporary:
        temporary_path = Path(temporary)
        result = subprocess.run([
            str(soffice), "--headless", "--convert-to", "pdf", "--outdir",
            str(temporary_path), str(svg_path.resolve()),
        ], capture_output=True, text=True, timeout=120)
        converted = temporary_path / (svg_path.stem + ".pdf")
        if result.returncode != 0 or not converted.exists():
            return {"status": "BLOCKED", "reason": "LibreOffice SVG-to-PDF failed", "stderr": result.stderr[-1000:], "stdout": result.stdout[-1000:]}
        shutil.copyfile(converted, pdf_path)
    return {"status": "VERIFIED", "path": str(pdf_path.resolve()), "sha256": sha256_file(pdf_path)}


def render_svg_to_png(svg_path: Path, png_path: Path, width: int, height: int) -> Dict[str, Any]:
    """Render the workflow's native SVG subset with Pillow, without browser state."""
    try:
        from PIL import Image, ImageColor, ImageDraw, ImageFont
        root = ET.parse(svg_path).getroot()
        viewbox = [float(value) for value in root.get("viewBox", "0 0 %s %s" % (width, height)).split()]
        sx, sy = width / viewbox[2], height / viewbox[3]
        image = Image.new("RGBA", (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image, "RGBA")

        def color(value: str | None, opacity: float = 1.0) -> tuple[int, int, int, int] | None:
            if not value or value in {"none", "transparent"} or value.startswith("url("):
                return None
            try:
                rgb = ImageColor.getrgb(value)
                return (rgb[0], rgb[1], rgb[2], max(0, min(255, int(255 * opacity))))
            except ValueError:
                return None

        def font(size: float, bold: bool = False, italic: bool = False, family: str = "", text: str = ""):
            serif = "serif" in family.lower() or "georgia" in family.lower() or "times" in family.lower()
            if serif:
                if bold and italic:
                    candidates = ["/System/Library/Fonts/Supplemental/Georgia Bold Italic.ttf", "/System/Library/Fonts/Supplemental/STIXGeneralBolIta.otf"]
                elif bold:
                    candidates = ["/System/Library/Fonts/Supplemental/Georgia Bold.ttf", "/System/Library/Fonts/Supplemental/STIXGeneralBol.otf"]
                elif italic:
                    candidates = ["/System/Library/Fonts/Supplemental/STIXTwoText-Italic.ttf", "/System/Library/Fonts/Supplemental/Georgia Italic.ttf"]
                else:
                    candidates = ["/System/Library/Fonts/Supplemental/STIXTwoText.ttf", "/System/Library/Fonts/Supplemental/Georgia.ttf"]
            else:
                candidates = [
                    "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
                    "/System/Library/Fonts/Supplemental/Arial.ttf",
                ]
            unicode_candidates = [
                "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf" if italic else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation2/LiberationSans-Italic.ttf" if italic else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSansOblique.ttf" if italic else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            ]
            candidates.extend(path for path in unicode_candidates if path not in candidates)
            pixel_size = max(8, int(size * (sx + sy) / 2))
            for candidate in candidates:
                if Path(candidate).exists():
                    selected = ImageFont.truetype(candidate, pixel_size)
                    if not text or _pillow_font_supports_text(selected, text):
                        return selected
            selected = ImageFont.load_default()
            if text and not _pillow_font_supports_text(selected, text):
                raise ValueError("no local Pillow font covers required text glyphs: %r" % text)
            return selected

        def translate(node: ET.Element, dx: float, dy: float) -> tuple[float, float]:
            match = re.search(r"translate\(([-\d.]+)(?:[, ]+)([-\d.]+)\)", node.get("transform", ""))
            return (dx + float(match.group(1)), dy + float(match.group(2))) if match else (dx, dy)

        def walk(node: ET.Element, dx: float = 0, dy: float = 0) -> None:
            dx, dy = translate(node, dx, dy)
            tag = node.tag.rsplit("}", 1)[-1]
            opacity = float(node.get("opacity", "1"))
            fill = color(node.get("fill"), opacity * float(node.get("fill-opacity", "1")))
            stroke = color(node.get("stroke"), opacity * float(node.get("stroke-opacity", "1")))
            stroke_width = max(1, int(float(node.get("stroke-width", "1")) * (sx + sy) / 2))
            def px(value: str | None, offset: float, scale: float) -> float:
                return (float(value or 0) + offset) * scale
            if tag == "rect":
                box = [px(node.get("x"), dx, sx), px(node.get("y"), dy, sy), px(node.get("x"), dx, sx) + float(node.get("width", "0")) * sx, px(node.get("y"), dy, sy) + float(node.get("height", "0")) * sy]
                radius = float(node.get("rx", "0")) * min(sx, sy)
                draw.rounded_rectangle(box, radius=radius, fill=fill, outline=stroke, width=stroke_width)
            elif tag == "ellipse":
                cx, cy = px(node.get("cx"), dx, sx), px(node.get("cy"), dy, sy)
                rx, ry = float(node.get("rx", "0")) * sx, float(node.get("ry", "0")) * sy
                draw.ellipse([cx-rx, cy-ry, cx+rx, cy+ry], fill=fill, outline=stroke, width=stroke_width)
            elif tag == "circle":
                cx, cy = px(node.get("cx"), dx, sx), px(node.get("cy"), dy, sy)
                radius = float(node.get("r", "0")) * min(sx, sy)
                draw.ellipse([cx-radius, cy-radius, cx+radius, cy+radius], fill=fill, outline=stroke, width=stroke_width)
            elif tag in {"polygon", "polyline"}:
                pts = []
                for pair in node.get("points", "").strip().split():
                    x_value, y_value = [float(value) for value in pair.split(",")]
                    pts.append(((x_value + dx) * sx, (y_value + dy) * sy))
                if pts:
                    if tag == "polygon":
                        draw.polygon(pts, fill=fill)
                        if stroke:
                            draw.line(pts + [pts[0]], fill=stroke, width=stroke_width, joint="curve")
                    elif stroke:
                        draw.line(pts, fill=stroke, width=stroke_width, joint="curve")
                        if node.get("marker-end") and len(pts) >= 2:
                            x1, y1 = pts[-2]; x2, y2 = pts[-1]
                            angle = __import__("math").atan2(y2-y1, x2-x1); size = max(8, stroke_width * 3)
                            left = (x2-size*__import__("math").cos(angle-0.55), y2-size*__import__("math").sin(angle-0.55))
                            right = (x2-size*__import__("math").cos(angle+0.55), y2-size*__import__("math").sin(angle+0.55))
                            draw.polygon([(x2, y2), left, right], fill=stroke)
            elif tag == "line":
                if stroke:
                    x1, y1 = px(node.get("x1"), dx, sx), px(node.get("y1"), dy, sy)
                    x2, y2 = px(node.get("x2"), dx, sx), px(node.get("y2"), dy, sy)
                    draw.line([x1, y1, x2, y2], fill=stroke, width=stroke_width)
                    if node.get("marker-end"):
                        angle = __import__("math").atan2(y2-y1, x2-x1); size = max(8, stroke_width * 3)
                        left = (x2-size*__import__("math").cos(angle-0.55), y2-size*__import__("math").sin(angle-0.55))
                        right = (x2-size*__import__("math").cos(angle+0.55), y2-size*__import__("math").sin(angle+0.55))
                        draw.polygon([(x2, y2), left, right], fill=stroke)
            elif tag == "text":
                size = float(node.get("font-size", "16"))
                is_bold = int(node.get("font-weight", "400")) >= 600 if node.get("font-weight", "400").isdigit() else node.get("font-weight") == "bold"
                x_value, y_value = px(node.get("x"), dx, sx), px(node.get("y"), dy, sy)
                anchor = node.get("text-anchor", "start")
                family = node.get("font-family", "")
                italic = node.get("font-style") == "italic"
                subspans = [child for child in list(node) if child.tag.rsplit("}", 1)[-1] == "tspan" and child.get("baseline-shift") == "sub"]
                if subspans and (node.text or "").strip():
                    base_value = (node.text or "").strip()
                    sub_value = "".join(subspans[0].itertext()).strip()
                    selected_font = font(size, is_bold, italic, family, base_value)
                    sub_size_text = subspans[0].get("font-size", "65%")
                    sub_scale = float(sub_size_text[:-1]) / 100 if sub_size_text.endswith("%") else float(sub_size_text) / size
                    sub_font = font(size * sub_scale, is_bold, italic, family, sub_value)
                    base_bbox = draw.textbbox((0, 0), base_value, font=selected_font)
                    sub_bbox = draw.textbbox((0, 0), sub_value, font=sub_font)
                    base_width = base_bbox[2] - base_bbox[0]; sub_width = sub_bbox[2] - sub_bbox[0]
                    total_width = base_width + sub_width
                    if anchor == "middle": x_value -= total_width / 2
                    if anchor == "end": x_value -= total_width
                    draw.text((x_value, y_value - (base_bbox[3] - base_bbox[1])), base_value, font=selected_font, fill=fill or (31, 41, 55, 255))
                    draw.text((x_value + base_width, y_value + size * 0.18 - (sub_bbox[3] - sub_bbox[1])), sub_value, font=sub_font, fill=fill or (31, 41, 55, 255))
                else:
                    value = "".join(node.itertext()).strip()
                    selected_font = font(size, is_bold, italic, family, value)
                    bbox = draw.textbbox((0, 0), value, font=selected_font)
                    if anchor == "middle": x_value -= (bbox[2] - bbox[0]) / 2
                    if anchor == "end": x_value -= bbox[2] - bbox[0]
                    draw.text((x_value, y_value - (bbox[3] - bbox[1])), value, font=selected_font, fill=fill or (31, 41, 55, 255))
            elif tag == "image":
                href = node.get("href") or node.get("{http://www.w3.org/1999/xlink}href")
                if href and not href.startswith(("data:", "http:" , "https:")):
                    source = (svg_path.parent / href).resolve()
                    if source.exists():
                        raster = Image.open(source).convert("RGBA")
                        target_width = max(1, int(float(node.get("width", str(raster.width))) * sx))
                        target_height = max(1, int(float(node.get("height", str(raster.height))) * sy))
                        raster = raster.resize((target_width, target_height))
                        if opacity < 1:
                            raster.putalpha(raster.getchannel("A").point(lambda value: int(value * opacity)))
                        image.alpha_composite(raster, (int(px(node.get("x"), dx, sx)), int(px(node.get("y"), dy, sy))))
            for child in list(node):
                walk(child, dx, dy)

        walk(root)
        png_path.parent.mkdir(parents=True, exist_ok=True)
        flattened = Image.new("RGB", image.size, "white")
        flattened.paste(image, mask=image.getchannel("A"))
        flattened.save(png_path)
        return {"status": "VERIFIED", "path": str(png_path), "sha256": sha256_file(png_path), "renderer": "pillow-native-svg-subset"}
    except Exception as error:
        return {"status": "BLOCKED", "reason": "Pillow SVG subset render failed", "error": str(error)}


def render_semantic_pdf(semantic: Mapping[str, Any], output_path: Path, grayscale: bool = False) -> Dict[str, Any]:
    """Draw a vector-only PDF directly from canonical semantic objects."""
    try:
        from reportlab.lib.colors import Color, HexColor
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfgen import canvas as pdfcanvas
        width = float(semantic["canvas"]["width"]); height = float(semantic["canvas"]["height"])
        physical_width_mm = semantic["canvas"].get("physical_width_mm")
        if physical_width_mm:
            page_width = float(physical_width_mm) * 72 / 25.4
            page_height = page_width * height / width
        else:
            page_width = width; page_height = height
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pdf = pdfcanvas.Canvas(str(output_path), pagesize=(page_width, page_height), pageCompression=1)
        if physical_width_mm:
            pdf.scale(page_width / width, page_height / height)
        font_files = {
            "ArialUnicode": "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "ArialBold": "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "STIXTwoText": "/System/Library/Fonts/Supplemental/STIXTwoText.ttf",
            "STIXTwoTextItalic": "/System/Library/Fonts/Supplemental/STIXTwoText-Italic.ttf",
            "DejaVuSans": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "DejaVuSansOblique": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
            "LiberationSans": "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
            "LiberationSansItalic": "/usr/share/fonts/truetype/liberation2/LiberationSans-Italic.ttf",
        }
        available_fonts = set(pdfmetrics.getRegisteredFontNames())
        for font_name, font_path in font_files.items():
            if font_name not in available_fonts and Path(font_path).exists():
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                available_fonts.add(font_name)
        pdf.setTitle(semantic["figure_id"])
        pdf.setSubject(json.dumps({"equations": [{"id": item["equation_id"], "latex": item.get("latex_source", "")} for item in semantic.get("equation_objects", [])]}, ensure_ascii=False))
        tokens = semantic.get("style_tokens", {}).get("colors", {})

        def pdf_color(value: str | None, fallback: str = "#20252B"):
            target = resolve_hex_paint(value, tokens, fallback)
            if target == "none":
                target = resolve_hex_paint(fallback, tokens, "#20252B")
            base = HexColor(target)
            if grayscale:
                gray = 0.299 * base.red + 0.587 * base.green + 0.114 * base.blue
                return Color(gray, gray, gray)
            return base

        def pdf_font_supports_text(font_name: str, value: str) -> bool:
            try:
                face = pdfmetrics.getFont(font_name).face
                glyphs = getattr(face, "charToGlyph", {})
                return all(character.isspace() or ord(character) in glyphs for character in value)
            except Exception:
                return False

        def unicode_pdf_font(value: str, italic: bool = False) -> str:
            candidates = [
                "ArialUnicode",
                "DejaVuSansOblique" if italic else "DejaVuSans",
                "LiberationSansItalic" if italic else "LiberationSans",
            ]
            for candidate in candidates:
                if candidate in available_fonts and pdf_font_supports_text(candidate, value):
                    return candidate
            raise ValueError("no local PDF font covers required text glyphs: %r" % value)

        pdf.setFillColor(pdf_color(semantic["canvas"].get("background", "#FFFFFF"), "#FFFFFF"))
        pdf.rect(0, 0, width, height, fill=1, stroke=0)
        for item in semantic.get("shapes", []):
            fill = pdf_color(item.get("fill"), tokens.get("surface", "#F2F4F6"))
            stroke = pdf_color(item.get("stroke"), tokens.get("ink", "#20252B"))
            pdf.setFillColor(fill); pdf.setStrokeColor(stroke); pdf.setLineWidth(float(item.get("stroke_width", semantic.get("style_tokens", {}).get("stroke_width", 2.2))))
            if item.get("dash"): pdf.setDash(7, 5)
            else: pdf.setDash()
            kind = item.get("type")
            if kind == "rect": pdf.roundRect(item["x"], height-item["y"]-item["height"], item["width"], item["height"], item.get("rx", 6), fill=1, stroke=1)
            elif kind == "ellipse": pdf.ellipse(item["cx"]-item["rx"], height-item["cy"]-item["ry"], item["cx"]+item["rx"], height-item["cy"]+item["ry"], fill=1, stroke=1)
            elif kind == "polygon":
                path = pdf.beginPath(); path.moveTo(item["points"][0][0], height-item["points"][0][1])
                for x_value, y_value in item["points"][1:]: path.lineTo(x_value, height-y_value)
                path.close(); pdf.drawPath(path, fill=1, stroke=1)
            elif kind == "line": pdf.line(item["x1"], height-item["y1"], item["x2"], height-item["y2"])
        for connector in semantic.get("connectors", []):
            color_token = connector.get("color_token", "ink")
            color_token = connector.get("stroke_token", color_token)
            pdf.setStrokeColor(pdf_color(tokens.get(color_token), "#20252B")); pdf.setFillColor(pdf_color(tokens.get(color_token), "#20252B")); pdf.setLineWidth(float(semantic.get("style_tokens", {}).get("stroke_width", 2.2)))
            if connector.get("dash"):
                pdf.setDash(7, 5)
            else:
                pdf.setDash()
            points = connector.get("points", [])
            path = pdf.beginPath(); path.moveTo(points[0][0], height-points[0][1])
            for x_value, y_value in points[1:]: path.lineTo(x_value, height-y_value)
            pdf.drawPath(path, fill=0, stroke=1)
            if len(points) >= 2:
                x2, y2 = points[-1][0], height-points[-1][1]; x1, y1 = points[-2][0], height-points[-2][1]
                angle = __import__("math").atan2(y2-y1, x2-x1); size = 8
                left = (x2-size*__import__("math").cos(angle-0.5), y2-size*__import__("math").sin(angle-0.5))
                right = (x2-size*__import__("math").cos(angle+0.5), y2-size*__import__("math").sin(angle+0.5))
                arrow = pdf.beginPath(); arrow.moveTo(x2, y2); arrow.lineTo(*left); arrow.lineTo(*right); arrow.close(); pdf.drawPath(arrow, fill=1, stroke=0)
        for item in semantic.get("text_objects", []):
            pdf.setFillColor(pdf_color(tokens.get(item.get("fill_token", "ink")), "#20252B"))
            serif = "serif" in item.get("font_family", "").lower() or "georgia" in item.get("font_family", "").lower()
            italic = item.get("font_style") == "italic"
            bold = item.get("font_weight", 400) >= 600
            if serif:
                font_name = "STIXTwoTextItalic" if italic and "STIXTwoTextItalic" in available_fonts else ("STIXTwoText" if "STIXTwoText" in available_fonts else ("Times-Bold" if bold else "Times-Roman"))
            else:
                font_name = "ArialBold" if bold and "ArialBold" in available_fonts else ("ArialUnicode" if "ArialUnicode" in available_fonts else ("Helvetica-Bold" if bold else "Helvetica"))
            text_value = item.get("text", "")
            if any(ord(character) > 127 for character in text_value):
                font_name = unicode_pdf_font(text_value, italic)
            pdf.setFont(font_name, item.get("font_size", 18))
            anchor = item.get("text_anchor", "start")
            draw_text = pdf.drawCentredString if anchor == "middle" else (pdf.drawRightString if anchor == "end" else pdf.drawString)
            draw_text(item["x"], height-item["y"], text_value)
        for equation in semantic.get("equation_objects", []):
            pdf.setFillColor(pdf_color(tokens.get("ink"), "#20252B"))
            font_size = equation.get("font_size", 18)
            if equation.get("latex_source") == r"G_\theta":
                from reportlab.pdfbase.pdfmetrics import stringWidth
                theta_size = font_size * 0.65
                math_font = "STIXTwoTextItalic" if "STIXTwoTextItalic" in available_fonts else "Times-Italic"
                theta_font = "STIXTwoText" if "STIXTwoText" in available_fonts else math_font
                g_width = stringWidth("G", math_font, font_size)
                theta_width = stringWidth("θ", theta_font, theta_size)
                start_x = equation["x"] - (g_width + theta_width) / 2 if equation.get("text_anchor") == "middle" else equation["x"]
                baseline = height - equation["y"]
                pdf.setFont(math_font, font_size); pdf.drawString(start_x, baseline, "G")
                pdf.setFont(theta_font, theta_size); pdf.drawString(start_x + g_width, baseline - font_size * 0.18, "θ")
            else:
                equation_text = equation.get("fallback_text", equation["equation_id"])
                italic = equation.get("font_style") == "italic"
                preferred_math_font = "STIXTwoTextItalic" if italic else "STIXTwoText"
                if (
                    preferred_math_font in available_fonts
                    and pdf_font_supports_text(preferred_math_font, equation_text)
                ):
                    font_name = preferred_math_font
                elif any(ord(character) > 127 for character in equation_text):
                    font_name = unicode_pdf_font(equation_text, italic)
                else:
                    font_name = "Times-Italic" if italic else "Times-Roman"
                pdf.setFont(font_name, font_size)
                draw_equation = pdf.drawCentredString if equation.get("text_anchor") == "middle" else pdf.drawString
                draw_equation(equation["x"], height-equation["y"], equation_text)
        pdf.showPage(); pdf.save()
        return {"status": "VERIFIED", "path": str(output_path.resolve()), "sha256": sha256_file(output_path), "renderer": "reportlab-native-vector"}
    except Exception as error:
        return {"status": "BLOCKED", "reason": "ReportLab vector PDF export failed", "error": str(error)}


def svg_document(
    width: float,
    height: float,
    body: str,
    metadata: Mapping[str, Any] | None = None,
    physical_width_mm: float | None = None,
    physical_height_mm: float | None = None,
) -> str:
    meta = ""
    if metadata is not None:
        meta = "<metadata>%s</metadata>" % html.escape(json.dumps(metadata, ensure_ascii=False))
    display_width = "%smm" % physical_width_mm if physical_width_mm else str(width)
    display_height = "%smm" % physical_height_mm if physical_height_mm else str(height)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" '
        'viewBox="0 0 %s %s" role="img">%s%s</svg>\n'
        % (display_width, display_height, width, height, meta, body)
    )


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _safe_svg_paint(value: Any, colors: Mapping[str, Any], fallback: str) -> str:
    """Resolve a paint token without emitting executable CSS or external URLs."""
    raw = str(value if value not in (None, "") else fallback).strip()
    variable = re.fullmatch(r"var\(--([A-Za-z0-9_-]+)\)", raw)
    if variable:
        raw = str(colors.get(variable.group(1), fallback)).strip()
    if re.search(r"(?:url\s*\(|@import|javascript:|data:|[{};<>\"'])", raw, re.IGNORECASE):
        raise ValueError("unsafe SVG paint value")
    if not re.fullmatch(
        r"(?:none|#[0-9A-Fa-f]{3,8}|[A-Za-z]+|rgba?\([0-9.,%\s]+\)|hsla?\([0-9.,%\s]+\))",
        raw,
    ):
        raise ValueError("unsupported SVG paint value")
    return raw


def polyline_points(points: Sequence[Sequence[float]]) -> str:
    return " ".join("%s,%s" % (point[0], point[1]) for point in points)


def render_semantic_svg(
    semantic: Mapping[str, Any],
    *,
    profile: str = "svg",
    grayscale: bool = False,
    include_metadata: bool = True,
) -> str:
    """Render canonical semantic JSON without consulting any delivery artifact."""
    canvas = semantic["canvas"]
    tokens = semantic.get("style_tokens", {})
    colors = dict(tokens.get("colors", {}))
    if grayscale:
        colors.update({
            "ink": "#111111", "muted": "#555555", "warm": "#444444",
            "cool": "#777777", "accent": "#222222", "surface": "#F5F5F5",
            "surface2": "#E6E6E6", "white": "#FFFFFF",
        })
    stroke_width = float(tokens.get("stroke_width", 2.2))
    font_family = tokens.get("font_family", "Arial, Helvetica, sans-serif")
    background = _safe_svg_paint(canvas.get("background"), colors, "#FFFFFF")
    ink = _safe_svg_paint(colors.get("ink"), colors, "#1F2937")
    warm = _safe_svg_paint(colors.get("warm"), colors, "#B45309")
    muted = _safe_svg_paint(colors.get("muted"), colors, "#5F6B78")
    css_tokens = {"background": background}
    for name, value in colors.items():
        if not re.fullmatch(r"[A-Za-z0-9_-]+", str(name)):
            raise ValueError("unsafe SVG style-token name")
        css_tokens[str(name)] = _safe_svg_paint(value, colors, "#000000")
    style = '<style>:root{%s}</style>' % "".join(
        "--%s:%s;" % (name.replace("_", "-"), value)
        for name, value in sorted(css_tokens.items())
    )
    defs = (
        '%s<defs><marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" '
        'orient="auto" markerUnits="strokeWidth"><path d="M0,0 L10,4 L0,8 z" fill="%s"/></marker>'
        '<marker id="arrow-warm" markerWidth="10" markerHeight="8" refX="9" refY="4" '
        'orient="auto" markerUnits="strokeWidth"><path d="M0,0 L10,4 L0,8 z" fill="%s"/></marker>'
        '<marker id="arrow-muted" markerWidth="10" markerHeight="8" refX="9" refY="4" '
        'orient="auto" markerUnits="strokeWidth"><path d="M0,0 L10,4 L0,8 z" fill="%s"/></marker></defs>'
        % (style, ink, warm, muted)
    )
    layers: Dict[str, List[str]] = {"background": [], "semantic": [], "shapes": [], "connectors": [], "text": [], "equations": []}
    layers["background"].append(
        '<rect id="canvas-background" x="0" y="0" width="%s" height="%s" fill="%s"/>'
        % (canvas["width"], canvas["height"], esc(background))
    )
    for group in semantic.get("groups", []):
        layers["semantic"].append(
            '<g id="%s" data-semantic-id="%s" data-role="%s" data-members="%s"/>' % (
                esc(group["id"]), esc(group["id"]), esc(group.get("role", "group")),
                esc(" ".join(str(value) for value in group.get("member_ids", []))),
            )
        )
    for port in semantic.get("ports", []):
        layers["semantic"].append(
            '<g id="%s" data-semantic-id="%s" data-role="port" data-node-id="%s" '
            'data-port-name="%s" data-position="%s"/>' % (
                esc(port["id"]), esc(port["id"]), esc(port.get("node_id", "")),
                esc(port.get("name", "")), esc(port.get("position", "")),
            )
        )
    entity_stages = {
        str(item["id"]): str(item.get("stage", "global"))
        for item in semantic.get("entities", [])
        if item.get("id")
    }
    for shape in semantic.get("shapes", []):
        sid = esc(shape["id"])
        role = shape.get("style_role", "surface")
        fill = _safe_svg_paint(
            colors.get(shape.get("fill_token", role), shape.get("fill")),
            colors,
            str(colors.get("surface", "#F5F5F5")),
        )
        stroke = _safe_svg_paint(
            colors.get(shape.get("stroke_token", "ink"), shape.get("stroke")),
            colors,
            str(colors.get("ink", "#1F2937")),
        )
        dash = ' stroke-dasharray="%s"' % esc(shape["dash"]) if shape.get("dash") else ""
        shape_stroke_width = shape.get("stroke_width", stroke_width)
        common = 'id="%s" data-semantic-id="%s" data-entity-type="%s" data-stage="%s" data-group-id="%s" fill="%s" stroke="%s" stroke-width="%s"%s' % (
            sid, sid, esc(shape.get("entity_type", "shape")), esc(entity_stages.get(str(shape["id"]), "global")),
            esc(shape.get("group_id", "") or ""), esc(fill), esc(stroke), shape_stroke_width, dash
        )
        kind = shape.get("type", "rect")
        if kind == "rect":
            markup = '<rect %s x="%s" y="%s" width="%s" height="%s" rx="%s"/>' % (
                common, shape["x"], shape["y"], shape["width"], shape["height"], shape.get("rx", 8)
            )
        elif kind == "ellipse":
            markup = '<ellipse %s cx="%s" cy="%s" rx="%s" ry="%s"/>' % (
                common, shape["cx"], shape["cy"], shape["rx"], shape["ry"]
            )
        elif kind == "polygon":
            markup = '<polygon %s points="%s"/>' % (common, polyline_points(shape["points"]))
        elif kind == "line":
            markup = '<line %s x1="%s" y1="%s" x2="%s" y2="%s"/>' % (
                common, shape["x1"], shape["y1"], shape["x2"], shape["y2"]
            )
        else:
            continue
        layers["shapes"].append(markup)
    for connector in semantic.get("connectors", []):
        color_token = connector.get("color_token", "ink")
        color_token = connector.get("stroke_token", color_token)
        color = _safe_svg_paint(colors.get(color_token), colors, "#1F2937")
        marker = "arrow-warm" if color_token == "warm" else ("arrow-muted" if color_token == "muted" else "arrow")
        dash = ' stroke-dasharray="7 5"' if connector.get("dash") else ""
        marker_end = ' marker-end="url(#%s)"' % marker if connector.get("arrow", "end") == "end" else ""
        layers["connectors"].append(
            '<polyline id="%s" data-semantic-id="%s" data-role="connector" data-relation-type="%s" '
            'data-source="%s" data-target="%s" data-source-id="%s" data-target-id="%s" '
            'data-direction="%s" points="%s" fill="none" '
            'stroke="%s" stroke-width="%s" stroke-linejoin="round"%s%s/>' % (
                esc(connector["id"]), esc(connector["id"]), esc(connector.get("relation_type", "relation")),
                esc(connector.get("source_id", "")), esc(connector.get("target_id", "")),
                esc(connector.get("source_id", "")), esc(connector.get("target_id", "")),
                esc(connector.get("direction", connector.get("arrow", "end"))),
                polyline_points(connector["points"]), esc(color), stroke_width, dash, marker_end
            )
        )
    for item in semantic.get("text_objects", []):
        font_size = item.get("font_size", 22)
        weight = item.get("font_weight", 400)
        anchor = item.get("text_anchor", "middle")
        fill = _safe_svg_paint(colors.get(item.get("fill_token", "ink")), colors, "#1F2937")
        item_font_family = item.get("font_family", font_family)
        font_style = item.get("font_style", "normal")
        lines = item.get("lines", [item.get("text", "")])
        tspans = []
        for index, line in enumerate(lines):
            dy = "0" if index == 0 else str(item.get("line_height", font_size * 1.25))
            tspans.append('<tspan x="%s" dy="%s">%s</tspan>' % (item["x"], dy, esc(line)))
        layers["text"].append(
            '<text id="%s" data-semantic-id="%s" data-group-id="%s" x="%s" y="%s" text-anchor="%s" '
            'font-family="%s" font-size="%s" font-weight="%s" font-style="%s" fill="%s">%s</text>' % (
                esc(item["id"]), esc(item["id"]), esc(item.get("group_id", "") or ""), item["x"], item["y"], anchor,
                esc(item_font_family), font_size, weight, esc(font_style), esc(fill), "".join(tspans)
            )
        )
    for equation in semantic.get("equation_objects", []):
        x, y = equation["x"], equation["y"]
        label = equation.get("fallback_text", equation["equation_id"])
        latex = equation.get("latex_source", "")
        label_markup = 'G<tspan baseline-shift="sub" font-size="65%">θ</tspan>' if latex == r"G_\theta" else esc(label)
        equation_font_family = equation.get("font_family", font_family)
        equation_font_style = equation.get("font_style", "normal")
        layers["equations"].append(
            '<g id="%s" data-semantic-id="%s" data-group-id="%s" data-equation-id="%s" data-latex="%s" '
            'transform="translate(%s,%s)"><text x="0" y="0" font-family="%s" font-size="%s" '
            'font-style="%s" text-anchor="%s" fill="%s">%s</text></g>' % (
                esc(equation["id"]), esc(equation["id"]), esc(equation.get("group_id", "") or ""),
                esc(equation["equation_id"]), esc(latex),
                x, y, esc(equation_font_family), equation.get("font_size", 20), esc(equation_font_style),
                esc(equation.get("text_anchor", "start")), esc(ink), label_markup
            )
        )
    body = defs
    order = ["background", "semantic", "shapes", "connectors", "text", "equations"]
    for layer in order:
        body += '<g id="layer-%s" data-layer="%s">%s</g>' % (layer, layer, "".join(layers[layer]))
    metadata = None
    if include_metadata:
        metadata = {
            "figure_id": semantic["figure_id"], "schema_version": semantic["schema_version"],
            "profile": profile, "source_hashes": semantic.get("provenance", {}).get("source_hashes", {}),
        }
    physical_width_mm = canvas.get("physical_width_mm") if profile == "svg" else None
    physical_height_mm = canvas.get("physical_height_mm") if profile == "svg" else None
    return svg_document(canvas["width"], canvas["height"], body, metadata, physical_width_mm, physical_height_mm)


def semantic_ids(semantic: Mapping[str, Any]) -> List[str]:
    result: List[str] = []
    for collection in ("groups", "shapes", "text_objects", "equation_objects", "ports", "connectors"):
        result.extend(str(item["id"]) for item in semantic.get(collection, []) if "id" in item)
    return result


def semantic_integrity_errors(semantic: Mapping[str, Any]) -> List[str]:
    errors = validate_schema(semantic, "semantic_figure.schema.json")
    ids = semantic_ids(semantic)
    if len(ids) != len(set(ids)):
        errors.append("semantic IDs are not globally unique")
    known = set(ids)
    for connector in semantic.get("connectors", []):
        if connector.get("source_id") not in known:
            errors.append("connector %s has unknown source %s" % (connector.get("id"), connector.get("source_id")))
        if connector.get("target_id") not in known:
            errors.append("connector %s has unknown target %s" % (connector.get("id"), connector.get("target_id")))
    equation_ids = [item.get("equation_id") for item in semantic.get("equation_objects", [])]
    if len(equation_ids) != len(set(equation_ids)):
        errors.append("equation IDs are not unique")
    return errors


def save_validated_json(path: Path, data: Mapping[str, Any], schema_name: str) -> None:
    require_valid(data, schema_name)
    write_json(path, data)
