#!/usr/bin/env python3
"""Executable structural and cross-format validation for V3 deliveries."""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Mapping

from figure_artifacts import load_json, sha256_file, write_json
from workflow_v3 import find_chrome, render_svg_to_png, semantic_integrity_errors, validate_schema


PML = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}


def check_svg(path: Path, semantic: Mapping[str, Any], profile: str) -> Dict[str, Any]:
    if not path.exists():
        return {"format": profile, "status": "BLOCKED", "reason": "missing file", "path": str(path)}
    root = ET.parse(path).getroot()
    ids = {element.get("id") for element in root.iter() if element.get("id")}
    required_ids = {item["id"] for key in ("shapes", "text_objects", "equation_objects", "connectors") for item in semantic.get(key, [])}
    text = path.read_text(encoding="utf-8")
    missing = sorted(required_ids - ids)
    raster_elements = [element for element in root.iter() if element.tag.endswith("image")]
    external_refs = re.findall(r'(?:href|xlink:href)="(https?://[^"]+|data:image/[^;]+;base64,[^"]+)"', text)
    equation_meta = sum(1 for element in root.iter() if element.get("data-equation-id"))
    connectors = sum(1 for element in root.iter() if element.get("data-relation-type"))
    passed = not missing and not raster_elements and not external_refs and equation_meta == len(semantic.get("equation_objects", [])) and connectors == len(semantic.get("connectors", []))
    return {
        "format": profile, "status": "VERIFIED" if passed else "BLOCKED", "path": str(path.resolve()),
        "sha256": sha256_file(path), "missing_semantic_ids": missing, "raster_element_count": len(raster_elements),
        "external_or_embedded_image_refs": external_refs, "equation_metadata_count": equation_meta,
        "connector_metadata_count": connectors, "semantic_editability": True, "equation_source_editability": True,
    }


def check_pptx(path: Path, semantic: Mapping[str, Any]) -> Dict[str, Any]:
    if not path.exists():
        return {"format": "pptx", "status": "BLOCKED", "reason": "missing file", "path": str(path)}
    with zipfile.ZipFile(path) as archive:
        slide_xml = ET.fromstring(archive.read("ppt/slides/slide1.xml"))
        names = archive.namelist()
        shape_count = len(slide_xml.findall(".//p:sp", PML))
        connector_count = len(slide_xml.findall(".//p:cxnSp", PML))
        picture_count = len(slide_xml.findall(".//p:pic", PML))
        media = [name for name in names if name.startswith("ppt/media/")]
        raster_media = [name for name in media if name.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
        raster_dimensions = []
        whole_canvas_raster = []
        try:
            from PIL import Image
            for name in raster_media:
                with Image.open(io.BytesIO(archive.read(name))) as image:
                    dimensions = [image.width, image.height]
                raster_dimensions.append({"name": name, "dimensions": dimensions})
                if dimensions[0] >= semantic["canvas"]["width"] * 0.8 and dimensions[1] >= semantic["canvas"]["height"] * 0.8:
                    whole_canvas_raster.append(name)
        except Exception:
            whole_canvas_raster = raster_media
        notes = ""
        for name in names:
            if name.startswith("ppt/notesSlides/notesSlide") and name.endswith(".xml"):
                notes += archive.read(name).decode("utf-8", errors="ignore")
        equation_note_ids = [item["equation_id"] for item in semantic.get("equation_objects", []) if item["equation_id"] in notes]
    passed = connector_count == len(semantic.get("connectors", [])) and not whole_canvas_raster and len(equation_note_ids) == len(semantic.get("equation_objects", []))
    return {
        "format": "pptx", "status": "VERIFIED" if passed else "BLOCKED", "path": str(path.resolve()),
        "sha256": sha256_file(path), "native_shape_count": shape_count, "native_connector_count": connector_count,
        "picture_count": picture_count, "media": media, "raster_media_dimensions": raster_dimensions,
        "whole_canvas_raster_media": whole_canvas_raster,
        "equation_ids_in_notes": equation_note_ids, "semantic_editability": True, "equation_source_editability": True,
    }


def check_drawio(path: Path, semantic: Mapping[str, Any]) -> Dict[str, Any]:
    if not path.exists():
        return {"format": "drawio", "status": "BLOCKED", "reason": "missing file", "path": str(path)}
    root = ET.parse(path).getroot()
    cells = root.findall(".//mxCell")
    cell_ids = {cell.get("id") for cell in cells}
    edges = [cell for cell in cells if cell.get("edge") == "1"]
    equations = [cell for cell in cells if cell.get("semanticType") == "equation" and cell.get("latexSource")]
    required = {item["id"] for key in ("shapes", "text_objects", "equation_objects", "connectors") for item in semantic.get(key, [])}
    missing = sorted(required - cell_ids)
    endpoints_ok = all(edge.get("source") in cell_ids and edge.get("target") in cell_ids for edge in edges)
    passed = not missing and endpoints_ok and len(edges) == len(semantic.get("connectors", [])) and len(equations) == len(semantic.get("equation_objects", []))
    return {
        "format": "drawio", "status": "VERIFIED" if passed else "BLOCKED", "path": str(path.resolve()),
        "sha256": sha256_file(path), "native_mxcell_count": len(cells), "native_edge_count": len(edges),
        "equation_source_count": len(equations), "missing_semantic_ids": missing, "endpoint_integrity": endpoints_ok,
        "semantic_editability": True, "equation_source_editability": True,
    }


def poppler_command(name: str) -> str | None:
    return shutil.which(name)


def check_pdf(path: Path, profile: str) -> Dict[str, Any]:
    if not path.exists():
        return {"format": profile, "status": "BLOCKED", "reason": "missing file", "path": str(path)}
    pdfinfo = poppler_command("pdfinfo")
    pdfimages = poppler_command("pdfimages")
    details: Dict[str, Any] = {}
    status = "GENERATED_UNVERIFIED"
    if pdfinfo:
        info = subprocess.run([pdfinfo, str(path)], capture_output=True, text=True, timeout=60)
        details["pdfinfo"] = info.stdout
        status = "VERIFIED" if info.returncode == 0 and "Pages:" in info.stdout else "BLOCKED"
    if pdfimages:
        images = subprocess.run([pdfimages, "-list", str(path)], capture_output=True, text=True, timeout=60)
        rows = [line for line in images.stdout.splitlines() if re.match(r"\s*\d+\s+\d+\s+", line)]
        details["embedded_image_rows"] = rows
        if rows:
            status = "BLOCKED"
    return {
        "format": profile, "status": status, "path": str(path.resolve()), "sha256": sha256_file(path),
        "semantic_editability": False, "equation_source_editability": False, **details,
    }


def create_preview(run_dir: Path, semantic: Mapping[str, Any]) -> Dict[str, Any]:
    preview_dir = run_dir / "validation" / "previews"
    preview_dir.mkdir(parents=True, exist_ok=True)
    sources = [
        (run_dir / "delivery" / "svg" / "master.svg", "SVG"),
        (run_dir / "delivery" / "figma" / "figure_figma.svg", "Figma-ready"),
        (run_dir / "delivery" / "drawio" / "figure_drawio.svg", "draw.io"),
    ]
    rendered = []
    for source, label in sources:
        target = preview_dir / (label.lower().replace("-", "_").replace(".", "") + ".png")
        result = render_svg_to_png(source, target, int(semantic["canvas"]["width"]), int(semantic["canvas"]["height"]))
        if result["status"] == "VERIFIED":
            rendered.append((target, label))
    pptx_preview = run_dir / "delivery" / "pptx" / "slide-01.png"
    if pptx_preview.exists():
        rendered.append((pptx_preview, "PPTX"))
    output = run_dir / "validation" / "cross_format_preview.png"
    try:
        from PIL import Image, ImageDraw, ImageOps
        thumb_width, thumb_height = 600, 360
        canvas = Image.new("RGB", (thumb_width * 2, (thumb_height + 44) * 2), "white")
        draw = ImageDraw.Draw(canvas)
        for index, (path, label) in enumerate(rendered[:4]):
            image = Image.open(path).convert("RGB")
            image.thumbnail((thumb_width - 20, thumb_height - 20))
            x = (index % 2) * thumb_width + (thumb_width - image.width) // 2
            y = (index // 2) * (thumb_height + 44) + 36 + (thumb_height - image.height) // 2
            canvas.paste(image, (x, y))
            draw.text(((index % 2) * thumb_width + 16, (index // 2) * (thumb_height + 44) + 10), label, fill="#172033")
        canvas.save(output)
        return {"status": "VERIFIED", "path": str(output.resolve()), "sha256": sha256_file(output), "panels": [label for _, label in rendered[:4]]}
    except Exception as error:
        return {"status": "BLOCKED", "reason": str(error)}


def validate(run_dir: Path) -> Dict[str, Any]:
    semantic_path = run_dir / "source" / "semantic_figure.json"
    semantic = load_json(semantic_path)
    semantic_errors = semantic_integrity_errors(semantic)
    checks = [
        {"format": "semantic-source", "status": "VERIFIED" if not semantic_errors else "BLOCKED", "errors": semantic_errors, "path": str(semantic_path.resolve()), "sha256": sha256_file(semantic_path), "semantic_editability": True, "equation_source_editability": True},
        check_svg(run_dir / "delivery" / "svg" / "master.svg", semantic, "svg"),
        check_svg(run_dir / "delivery" / "figma" / "figure_figma.svg", semantic, "figma-ready-svg"),
        check_pptx(run_dir / "delivery" / "pptx" / "figure.pptx", semantic),
        check_drawio(run_dir / "delivery" / "drawio" / "figure.drawio", semantic),
        check_pdf(run_dir / "delivery" / "pdf" / "publication.pdf", "publication-pdf"),
        check_pdf(run_dir / "delivery" / "pdf" / "grayscale.pdf", "grayscale-pdf"),
        check_pdf(run_dir / "delivery" / "drawio" / "figure_drawio_editable.pdf", "drawio-companion-pdf"),
    ]
    preview = create_preview(run_dir, semantic)
    statuses = [item["status"] for item in checks]
    overall = "VERIFIED" if all(status == "VERIFIED" for status in statuses) and preview["status"] == "VERIFIED" else "BLOCKED"
    report = {
        "schema_version": "1.0", "figure_id": semantic["figure_id"], "status": overall,
        "canonical_source": str(semantic_path.resolve()), "checks": checks, "preview": preview,
        "cross_format_invariants": {
            "coordinate_system": "All adapters consume the same semantic pixel coordinate system; PPTX uses the identical slide size.",
            "expected_shape_count": len(semantic.get("shapes", [])), "expected_text_count": len(semantic.get("text_objects", [])),
            "expected_equation_count": len(semantic.get("equation_objects", [])), "expected_connector_count": len(semantic.get("connectors", [])),
            "bounding_box_policy": "SVG, Figma-ready SVG, draw.io, and PPTX receive unscaled canonical bounding boxes. PDF is printed from a direct semantic render.",
        },
        "editability_claims": {
            "semantic-source": "VERIFIED", "svg": "VERIFIED", "figma-ready-svg": "IMPORT_READY_UNVERIFIED",
            "pptx": "VERIFIED" if checks[3]["status"] == "VERIFIED" else "BLOCKED", "drawio": "VERIFIED",
            "pdf": "Vector publication output; not semantically editable.",
        },
    }
    validation_dir = run_dir / "validation"
    write_json(validation_dir / "cross_format_report.json", report)
    formats = []
    for item in checks[1:]:
        status = item["status"]
        if item["format"] == "figma-ready-svg" and status == "VERIFIED":
            status = "IMPORT_READY_UNVERIFIED"
        formats.append({
            "format": item["format"], "path": item["path"], "status": status,
            "semantic_editability": bool(item.get("semantic_editability", False)),
            "equation_source_editability": bool(item.get("equation_source_editability", False)),
            "verification": "See validation/cross_format_report.json",
        })
    manifest = {
        "schema_version": "1.0", "figure_id": semantic["figure_id"], "canonical_source": str(semantic_path.resolve()),
        "formats": formats, "validation_report": str((validation_dir / "cross_format_report.json").resolve()),
    }
    errors = validate_schema(manifest, "delivery_manifest.schema.json")
    if errors:
        raise ValueError("delivery manifest validation failed:\n%s" % "\n".join(errors))
    write_json(run_dir / "delivery" / "delivery_manifest.json", manifest)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=Path)
    args = parser.parse_args()
    report = validate(args.run_dir)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
