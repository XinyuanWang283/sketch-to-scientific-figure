#!/usr/bin/env python3
"""Regression tests for fail-closed multi-format delivery validation."""

from __future__ import annotations

import importlib.util
import json
import math
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPOSITORY_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from export_drawio import build_drawio  # noqa: E402
from export_pptx import _repair_connector_references  # noqa: E402
from figure_artifacts import write_json  # noqa: E402
from validate_delivery import (  # noqa: E402
    check_drawio,
    check_pdf,
    check_pptx,
    check_svg,
    create_preview,
    validate,
)
from validate_semantic_svg import validate_svg  # noqa: E402
from workflow_v3 import (  # noqa: E402
    _pillow_font_supports_text,
    render_semantic_pdf,
    render_semantic_svg,
)


def semantic_fixture() -> dict:
    return {
        "schema_version": "1.0",
        "figure_id": "synthetic-delivery-validation",
        "canvas": {
            "width": 1200,
            "height": 675,
            "background": "#FCFCFD",
            "physical_width_mm": 180,
            "physical_height_mm": 101.25,
        },
        "entities": [
            {"id": "measurement", "entity_type": "measurement", "stage": "input"},
            {"id": "model", "entity_type": "model", "stage": "process"},
        ],
        "groups": [
            {"id": "stage-input", "role": "stage", "member_ids": ["measurement", "measurement-label"]},
            {"id": "stage-process", "role": "stage", "member_ids": ["model", "model-label"]},
        ],
        "shapes": [
            {
                "id": "measurement",
                "type": "ellipse",
                "entity_type": "measurement",
                "group_id": "stage-input",
                "cx": 190,
                "cy": 330,
                "rx": 70,
                "ry": 70,
                "fill": "#DBEAFE",
                "stroke": "#2563EB",
            },
            {
                "id": "model",
                "type": "rect",
                "entity_type": "model",
                "group_id": "stage-process",
                "x": 500,
                "y": 250,
                "width": 240,
                "height": 160,
                "fill": "#E0E7FF",
                "stroke": "#7C3AED",
            },
        ],
        "text_objects": [
            {
                "id": "measurement-label",
                "text": "Measurement",
                "x": 190,
                "y": 440,
                "font_size": 22,
                "group_id": "stage-input",
            }
        ],
        "equation_objects": [
            {
                "id": "model-label",
                "equation_id": "model_label",
                "latex_source": "f_\\theta",
                "fallback_text": "Model",
                "x": 620,
                "y": 340,
                "width": 120,
                "height": 48,
                "font_size": 30,
                "text_anchor": "middle",
            }
        ],
        "ports": [],
        "connectors": [
            {
                "id": "flow-input-model",
                "source_id": "measurement",
                "target_id": "model",
                "relation_type": "feeds",
                "points": [[260, 330], [500, 330]],
                "arrow": "end",
            }
        ],
        "z_order": [
            "measurement",
            "model",
            "flow-input-model",
            "measurement-label",
            "model-label",
        ],
        "style_tokens": {
            "colors": {
                "ink": "#1F2937",
                "muted": "#64748B",
                "cool": "#2563EB",
                "accent": "#7C3AED",
                "surface": "#F8FAFC",
                "surface2": "#E0E7FF",
            },
            "stroke_width": 2.6,
            "font_family": "Arial, Helvetica, sans-serif",
        },
        "platform_overrides": {
            "figma": {"flatten_equations": False},
            "pptx": {"native_shapes": True, "equations_as_svg_groups": True},
            "drawio": {"native_mxcell": True},
            "pdf": {"vector_only": True},
        },
        "provenance": {
            "truth_source": "synthetic-fixture",
            "equation_manifest": "equations.json",
            "generated_at": "2000-01-01T00:00:00+00:00",
            "source_hashes": {},
        },
    }


def _fixture_paint(value: object, semantic: dict, fallback: str) -> str:
    colors = semantic["style_tokens"]["colors"]
    raw = str(value or "").strip()
    variable = re.fullmatch(r"var\(--([A-Za-z0-9_-]+)\)", raw)
    if variable:
        raw = str(colors.get(variable.group(1), fallback))
    elif raw in colors:
        raw = str(colors[raw])
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", raw):
        raw = fallback
    return raw.upper()


def _fixture_text_width(item: dict, canvas_width: float) -> float:
    font_size = float(item.get("font_size", 18))
    value = str(item.get("text") or "\n".join(item.get("lines", [])))
    longest = max((len(line) for line in value.split("\n")), default=0)
    estimated = math.ceil(longest * font_size * 0.62 + font_size)
    return min(max(180.0, float(estimated)), max(1.0, canvas_width - 24.0))


def _shape_xml(
    numeric_id: int,
    name: str,
    bounds: tuple[float, float, float, float],
    text: str = "",
    primitive: str = "rect",
    fill_color: str = "none",
    stroke_color: str = "none",
) -> str:
    x, y, width, height = (round(value * 10000) for value in bounds)
    fill_xml = (
        "<a:noFill/>" if fill_color == "none"
        else '<a:solidFill><a:srgbClr val="%s"/></a:solidFill>' % fill_color.lstrip("#")
    )
    stroke_xml = (
        "<a:ln><a:noFill/></a:ln>" if stroke_color == "none"
        else '<a:ln><a:solidFill><a:srgbClr val="%s"/></a:solidFill></a:ln>' % stroke_color.lstrip("#")
    )
    return f"""
      <p:sp>
        <p:nvSpPr><p:cNvPr id="{numeric_id}" name="{name}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
        <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{width}" cy="{height}"/></a:xfrm>
        <a:prstGeom prst="{primitive}"><a:avLst/></a:prstGeom>{fill_xml}{stroke_xml}</p:spPr>
        <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>{text}</a:t></a:r></a:p></p:txBody>
      </p:sp>"""


def write_pptx(path: Path, semantic: dict, *, picture_only: bool = False, miswired: bool = False) -> None:
    numeric_ids: dict[str, int] = {}
    parts: list[str] = []
    next_id = 2
    if picture_only:
        parts.append("""
      <p:pic>
        <p:nvPicPr><p:cNvPr id="2" name="entire-slide.png"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr>
        <p:blipFill><a:blip r:embed="rIdPicture"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
        <p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="12000000" cy="6750000"/></a:xfrm></p:spPr>
      </p:pic>""")
    else:
        for item in semantic["shapes"]:
            numeric_ids[item["id"]] = next_id
            if item["type"] == "rect":
                bounds = (item["x"], item["y"], item["width"], item["height"])
                primitive = "rect"
            else:
                bounds = (item["cx"] - item["rx"], item["cy"] - item["ry"], item["rx"] * 2, item["ry"] * 2)
                primitive = "ellipse"
            fill = "none" if item["type"] == "line" else _fixture_paint(
                item.get("fill"), semantic, semantic["style_tokens"]["colors"]["surface"],
            )
            stroke = _fixture_paint(
                item.get("stroke"), semantic, semantic["style_tokens"]["colors"]["ink"],
            )
            parts.append(_shape_xml(
                next_id, item["id"], bounds, primitive=primitive,
                fill_color=fill, stroke_color=stroke,
            ))
            next_id += 1
        for item in semantic["text_objects"]:
            numeric_ids[item["id"]] = next_id
            font_size = item.get("font_size", 18)
            text_width = _fixture_text_width(item, semantic["canvas"]["width"])
            left = item["x"] - text_width / 2 if item.get("text_anchor") == "middle" else item["x"]
            parts.append(_shape_xml(
                next_id, item["id"], (left, item["y"] - font_size * 1.2, text_width, font_size * 1.7), item["text"]
            ))
            next_id += 1
        for item in semantic["equation_objects"]:
            numeric_ids[item["id"]] = next_id
            width, height = item.get("width", 360), item.get("height", 36)
            left = item["x"] - width / 2 if item.get("text_anchor") == "middle" else item["x"]
            parts.append(_shape_xml(
                next_id, item["id"], (left, item["y"] - height, width, height), item["fallback_text"]
            ))
            next_id += 1
        for item in semantic["connectors"]:
            source = numeric_ids[item["source_id"]]
            target = numeric_ids[item["target_id"]]
            if miswired:
                source, target = target, source
            parts.append(f"""
      <p:cxnSp>
        <p:nvCxnSpPr>
          <p:cNvPr id="{next_id}" name="{item['id']}"/>
          <p:cNvCxnSpPr><a:stCxn id="{source}" idx="0"/><a:endCxn id="{target}" idx="0"/></p:cNvCxnSpPr>
          <p:nvPr/>
        </p:nvCxnSpPr>
        <p:spPr><a:xfrm><a:off x="2600000" y="3300000"/><a:ext cx="2400000" cy="0"/></a:xfrm>
        <a:prstGeom prst="line"><a:avLst/></a:prstGeom></p:spPr>
      </p:cxnSp>""")
            next_id += 1

    slide = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
 <p:cSld><p:spTree><p:nvGrpSpPr/><p:grpSpPr/>{''.join(parts)}</p:spTree></p:cSld>
</p:sld>"""
    notes_text = " | ".join(
        f"{item['equation_id']}: {item['latex_source']}"
        for item in semantic["equation_objects"]
    )
    notes = f"""<?xml version="1.0" encoding="UTF-8"?>
<p:notes xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
 <p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>{notes_text}</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld>
</p:notes>"""
    presentation = """<?xml version="1.0" encoding="UTF-8"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
 <p:sldSz cx="12000000" cy="6750000"/><p:sldIdLst><p:sldId id="256" r:id="rId1"/></p:sldIdLst>
</p:presentation>"""
    content_types = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
 <Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
 <Override PartName="/ppt/notesSlides/notesSlide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"/>
</Types>"""
    root_rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>"""
    presentation_rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/>
</Relationships>"""
    slide_rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Id="rIdNotes" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide" Target="../notesSlides/notesSlide1.xml"/>
</Relationships>"""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("ppt/presentation.xml", presentation)
        archive.writestr("ppt/_rels/presentation.xml.rels", presentation_rels)
        archive.writestr("ppt/slides/slide1.xml", slide)
        archive.writestr("ppt/slides/_rels/slide1.xml.rels", slide_rels)
        archive.writestr("ppt/notesSlides/notesSlide1.xml", notes)
        if picture_only:
            archive.writestr("ppt/media/image1.png", b"not-a-real-image")


def rewrite_zip_member(path: Path, member_name: str, transform) -> None:
    with zipfile.ZipFile(path) as archive:
        members = [(item, archive.read(item.filename)) for item in archive.infolist()]
    with zipfile.ZipFile(path, "w") as archive:
        for item, payload in members:
            archive.writestr(item, transform(payload) if item.filename == member_name else payload)


def write_pdf(path: Path, *, raster_only: bool, width: float, height: float) -> None:
    if raster_only:
        resources = b"<< /XObject << /Im0 5 0 R >> >>"
        content = b"q 510 0 0 287 0 0 cm /Im0 Do Q"
        extra = b"<< /Type /XObject /Subtype /Image /Width 1 /Height 1 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Length 3 >>\nstream\n\xff\xff\xff\nendstream"
    else:
        resources = b"<< /Font << /F1 5 0 R >> >>"
        content = b"BT /F1 12 Tf 20 40 Td (Synthetic vector figure) Tj ET 10 10 m 100 100 l S"
        extra = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width:.3f} {height:.3f}] /Resources 6 0 R /Contents 4 0 R >>".encode(),
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
        extra,
        resources,
    ]
    payload = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, body in enumerate(objects, start=1):
        offsets.append(len(payload))
        payload.extend(f"{index} 0 obj\n".encode())
        payload.extend(body)
        payload.extend(b"\nendobj\n")
    xref = len(payload)
    payload.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    payload.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        payload.extend(f"{offset:010d} 00000 n \n".encode())
    payload.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    path.write_bytes(payload)


class DeliveryValidationTests(unittest.TestCase):
    def test_renderer_and_svg_validator_preserve_exact_topology(self) -> None:
        semantic = semantic_fixture()
        with tempfile.TemporaryDirectory(prefix="delivery-svg-") as temporary:
            svg_path = Path(temporary) / "figure.svg"
            svg_path.write_text(render_semantic_svg(semantic), encoding="utf-8")
            result = check_svg(svg_path, semantic, "svg")
            self.assertEqual(result["status"], "VERIFIED", result)

            tree = ET.parse(svg_path)
            connector = next(node for node in tree.getroot().iter() if node.get("id") == "flow-input-model")
            connector.set("data-target", "measurement")
            connector.set("data-target-id", "measurement")
            tree.write(svg_path, encoding="utf-8", xml_declaration=True)
            result = check_svg(svg_path, semantic, "svg")
            self.assertEqual(result["status"], "BLOCKED")
            self.assertIn("flow-input-model", result["connector_mismatches"])

    def test_renderer_output_passes_repository_semantic_svg_checker(self) -> None:
        semantic = semantic_fixture()
        spec = {
            "semantic_group_inventory": [{"id": "stage-input"}, {"id": "stage-process"}],
            "exact_text": ["Measurement"],
            "exact_equations": ["f_\\theta"],
            "relation_type_contracts": {
                "feeds": {"source_types": ["measurement"], "target_types": ["model"]}
            },
            "geometry_policy": {
                "entity_counts_by_stage": {
                    "input": {"measurement": 1},
                    "process": {"model": 1},
                },
                "relation_counts": {"feeds": 1},
            },
            "style_tokens": {
                "background": "#FCFCFD",
                "ink": "#1F2937",
                "muted": "#64748B",
                "cool": "#2563EB",
                "accent": "#7C3AED",
                "surface": "#F8FAFC",
                "surface2": "#E0E7FF",
            },
            "raster_asset_policy": {"allowed": False},
        }
        with tempfile.TemporaryDirectory(prefix="semantic-render-") as temporary:
            directory = Path(temporary)
            svg_path = directory / "figure.svg"
            spec_path = directory / "spec.json"
            svg_path.write_text(render_semantic_svg(semantic), encoding="utf-8")
            write_json(spec_path, spec)
            report = validate_svg(svg_path, spec_path)
            self.assertEqual(report["summary"]["overall"], "pass", report)

    def test_svg_rejects_embedded_raster_standin(self) -> None:
        semantic = semantic_fixture()
        with tempfile.TemporaryDirectory(prefix="raster-svg-") as temporary:
            path = Path(temporary) / "raster.svg"
            path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"><image id="measurement" href="data:image/png;base64,AAAA"/></svg>',
                encoding="utf-8",
            )
            result = check_svg(path, semantic, "svg")
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["raster_element_count"], 1)

    def test_svg_rejects_metadata_only_geometry_and_active_content(self) -> None:
        semantic = semantic_fixture()
        with tempfile.TemporaryDirectory(prefix="metadata-svg-") as temporary:
            path = Path(temporary) / "metadata-only.svg"
            path.write_text(render_semantic_svg(semantic), encoding="utf-8")
            tree = ET.parse(path)
            namespace = "{http://www.w3.org/2000/svg}"
            targets = {
                item["id"]
                for collection in ("shapes", "equation_objects", "connectors")
                for item in semantic[collection]
            }
            for element in tree.getroot().iter():
                if element.get("id") in targets:
                    element.tag = namespace + "g"
                if element.get("id") == "measurement":
                    element.set("style", "fill:url(https://invalid.example/payload.svg)")
            ET.SubElement(tree.getroot(), namespace + "script").text = "alert(1)"
            tree.write(path, encoding="utf-8", xml_declaration=True)
            result = check_svg(path, semantic, "svg")
            self.assertEqual(result["status"], "BLOCKED")
            self.assertTrue(result["shape_mismatches"])
            self.assertIn("script", result["active_content_tags"])
            self.assertTrue(result["external_or_embedded_image_refs"])

    def test_renderer_rejects_unsafe_css_token(self) -> None:
        semantic = semantic_fixture()
        semantic["style_tokens"]["colors"]["ink"] = "#000;@import url(https://invalid.example)"
        with self.assertRaisesRegex(ValueError, "unsafe SVG paint"):
            render_semantic_svg(semantic)

    def test_drawio_requires_exact_editable_nodes_and_edges(self) -> None:
        semantic = semantic_fixture()
        with tempfile.TemporaryDirectory(prefix="delivery-drawio-") as temporary:
            path = Path(temporary) / "figure.drawio"
            build_drawio(semantic).write(path, encoding="unicode", xml_declaration=True)
            result = check_drawio(path, semantic)
            self.assertEqual(result["status"], "VERIFIED", result)

            tree = ET.parse(path)
            edge = next(cell for cell in tree.getroot().iter("mxCell") if cell.get("id") == "flow-input-model")
            edge.set("target", "measurement")
            tree.write(path, encoding="unicode", xml_declaration=True)
            result = check_drawio(path, semantic)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertIn("flow-input-model", result["edge_mismatches"])

    def test_drawio_requires_canonical_semantic_paints(self) -> None:
        semantic = semantic_fixture()
        semantic["shapes"][1]["fill"] = "var(--surface2)"
        semantic["shapes"][1]["stroke"] = "accent"
        with tempfile.TemporaryDirectory(prefix="drawio-paint-") as temporary:
            path = Path(temporary) / "figure.drawio"
            build_drawio(semantic).write(path, encoding="unicode", xml_declaration=True)
            self.assertEqual(check_drawio(path, semantic)["status"], "VERIFIED")

            tree = ET.parse(path)
            model = next(cell for cell in tree.getroot().iter("mxCell") if cell.get("id") == "model")
            model.set("style", re.sub(r"fillColor=#[0-9A-Fa-f]{6}", "fillColor=#000000", model.get("style", "")))
            tree.write(path, encoding="unicode", xml_declaration=True)
            result = check_drawio(path, semantic)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertIn("model", result["paint_mismatches"])

    def test_drawio_rejects_embedded_picture_standin(self) -> None:
        semantic = semantic_fixture()
        with tempfile.TemporaryDirectory(prefix="picture-drawio-") as temporary:
            path = Path(temporary) / "picture.drawio"
            path.write_text(
                '<mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/>'
                '<mxCell id="measurement" vertex="1" parent="1" style="shape=image;image=data:image/png;base64,AAAA;"/>'
                '</root></mxGraphModel>',
                encoding="utf-8",
            )
            result = check_drawio(path, semantic)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertTrue(result["picture_standin_cells"])

    def test_drawio_rejects_zero_geometry_and_missing_arrow(self) -> None:
        semantic = semantic_fixture()
        with tempfile.TemporaryDirectory(prefix="zero-drawio-") as temporary:
            path = Path(temporary) / "zero.drawio"
            tree = build_drawio(semantic)
            for geometry in tree.getroot().iter("mxGeometry"):
                if geometry.get("relative") != "1":
                    geometry.set("x", "0")
                    geometry.set("y", "0")
                    geometry.set("width", "0")
                    geometry.set("height", "0")
            edge = next(cell for cell in tree.getroot().iter("mxCell") if cell.get("edge") == "1")
            edge.set("style", edge.get("style", "").replace("endArrow=block", "endArrow=none"))
            tree.write(path, encoding="unicode", xml_declaration=True)
            result = check_drawio(path, semantic)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertTrue(result["node_mismatches"])
            self.assertTrue(result["edge_mismatches"])

    def test_pptx_requires_native_shapes_text_and_exact_connector_topology(self) -> None:
        semantic = semantic_fixture()
        with tempfile.TemporaryDirectory(prefix="delivery-pptx-") as temporary:
            directory = Path(temporary)
            valid = directory / "valid.pptx"
            write_pptx(valid, semantic)
            result = check_pptx(valid, semantic)
            self.assertEqual(result["status"], "VERIFIED", result)

            miswired = directory / "miswired.pptx"
            write_pptx(miswired, semantic, miswired=True)
            result = check_pptx(miswired, semantic)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertIn("flow-input-model", result["connector_mismatches"])

            repair = _repair_connector_references(miswired, semantic)
            self.assertEqual(repair["repaired_connector_count"], 1)
            result = check_pptx(miswired, semantic)
            self.assertEqual(result["status"], "VERIFIED", result)

    def test_pptx_resolves_semantic_paints_and_rejects_black_regression(self) -> None:
        semantic = semantic_fixture()
        semantic["shapes"][1]["fill"] = "var(--surface2)"
        semantic["shapes"][1]["stroke"] = "accent"
        pml = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
        aml = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}

        def blacken_model(payload: bytes) -> bytes:
            root = ET.fromstring(payload)
            for shape in root.findall(".//p:sp", pml):
                properties = shape.find(".//p:cNvPr", pml)
                if properties is None or properties.get("name") != "model":
                    continue
                fill = shape.find("./p:spPr/a:solidFill/a:srgbClr", {**pml, **aml})
                stroke = shape.find("./p:spPr/a:ln/a:solidFill/a:srgbClr", {**pml, **aml})
                assert fill is not None and stroke is not None
                fill.set("val", "000000")
                stroke.set("val", "000000")
            return ET.tostring(root, encoding="utf-8", xml_declaration=True)

        with tempfile.TemporaryDirectory(prefix="pptx-paint-") as temporary:
            path = Path(temporary) / "figure.pptx"
            write_pptx(path, semantic)
            result = check_pptx(path, semantic)
            self.assertEqual(result["status"], "VERIFIED", result)
            rewrite_zip_member(path, "ppt/slides/slide1.xml", blacken_model)
            result = check_pptx(path, semantic)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertIn("model", result["native_paint_mismatches"])

    def test_pptx_text_width_expands_long_centered_title_but_keeps_short_label(self) -> None:
        semantic = semantic_fixture()
        label = semantic["text_objects"][0]
        self.assertEqual(_fixture_text_width(label, semantic["canvas"]["width"]), 180)
        label.update(text="Synthetic restoration", x=600, y=72, font_size=30, text_anchor="middle")
        self.assertEqual(_fixture_text_width(label, semantic["canvas"]["width"]), 421)

        pml = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
        aml = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}

        def restore_legacy_width(payload: bytes) -> bytes:
            root = ET.fromstring(payload)
            for shape in root.findall(".//p:sp", pml):
                properties = shape.find(".//p:cNvPr", pml)
                if properties is None or properties.get("name") != "measurement-label":
                    continue
                offset = shape.find(".//a:xfrm/a:off", aml)
                extent = shape.find(".//a:xfrm/a:ext", aml)
                assert offset is not None and extent is not None
                offset.set("x", str(round((600 - 90) * 10000)))
                extent.set("cx", str(180 * 10000))
            return ET.tostring(root, encoding="utf-8", xml_declaration=True)

        with tempfile.TemporaryDirectory(prefix="pptx-text-width-") as temporary:
            path = Path(temporary) / "figure.pptx"
            write_pptx(path, semantic)
            self.assertEqual(check_pptx(path, semantic)["status"], "VERIFIED")
            rewrite_zip_member(path, "ppt/slides/slide1.xml", restore_legacy_width)
            result = check_pptx(path, semantic)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertIn("measurement-label", result["native_geometry_mismatches"])

    def test_pptx_binds_slide_id_and_requires_content_type_declarations(self) -> None:
        semantic = semantic_fixture()
        with tempfile.TemporaryDirectory(prefix="pptx-package-contract-") as temporary:
            directory = Path(temporary)
            broken_binding = directory / "broken-binding.pptx"
            write_pptx(broken_binding, semantic)
            rewrite_zip_member(
                broken_binding,
                "ppt/presentation.xml",
                lambda payload: payload.replace(b'r:id="rId1"', b'r:id="rIdMissing"'),
            )
            result = check_pptx(broken_binding, semantic)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertFalse(result["slide_relationship_ok"])

            invalid_content_types = directory / "invalid-content-types.pptx"
            write_pptx(invalid_content_types, semantic)
            rewrite_zip_member(
                invalid_content_types,
                "[Content_Types].xml",
                lambda _payload: b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>',
            )
            result = check_pptx(invalid_content_types, semantic)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertFalse(result["content_types_ok"])

    def test_pptx_requires_canonical_connector_and_fallback_equation_geometry(self) -> None:
        semantic = semantic_fixture()
        pml = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
        aml = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}

        def mutate_slide(payload: bytes) -> bytes:
            root = ET.fromstring(payload)
            for connector in root.findall(".//p:cxnSp", pml):
                properties = connector.find(".//p:cNvPr", pml)
                if properties is not None and properties.get("name") == "flow-input-model":
                    offset = connector.find(".//a:xfrm/a:off", aml)
                    extent = connector.find(".//a:xfrm/a:ext", aml)
                    assert offset is not None and extent is not None
                    offset.set("x", "9000000")
                    offset.set("y", "6000000")
                    extent.set("cx", "1000000")
                    extent.set("cy", "1000000")
            for shape in root.findall(".//p:sp", pml):
                properties = shape.find(".//p:cNvPr", pml)
                if properties is not None and properties.get("name") == "model-label":
                    text = shape.find(".//a:t", aml)
                    offset = shape.find(".//a:xfrm/a:off", aml)
                    assert text is not None and offset is not None
                    text.text = "Wrong model"
                    offset.set("x", "0")
            return ET.tostring(root, encoding="utf-8", xml_declaration=True)

        with tempfile.TemporaryDirectory(prefix="pptx-canonical-geometry-") as temporary:
            path = Path(temporary) / "bad-geometry.pptx"
            write_pptx(path, semantic)
            rewrite_zip_member(path, "ppt/slides/slide1.xml", mutate_slide)
            result = check_pptx(path, semantic)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertIn("flow-input-model", result["connector_geometry_mismatches"])
            self.assertIn("fallback equation text mismatch", result["equation_mismatches"]["model-label"])
            self.assertIn("fallback equation geometry mismatch", result["equation_mismatches"]["model-label"])

    def test_pptx_rejects_single_picture_zero_shape_package(self) -> None:
        semantic = semantic_fixture()
        with tempfile.TemporaryDirectory(prefix="pseudo-pptx-") as temporary:
            path = Path(temporary) / "picture-only.pptx"
            write_pptx(path, semantic, picture_only=True)
            result = check_pptx(path, semantic)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["native_shape_count"], 0)
            self.assertTrue(result["whole_canvas_picture_ids"])

    def test_pdf_raster_only_never_verifies(self) -> None:
        semantic = semantic_fixture()
        with tempfile.TemporaryDirectory(prefix="raster-pdf-") as temporary:
            path = Path(temporary) / "raster.pdf"
            width = 180 * 72 / 25.4
            height = width * 675 / 1200
            write_pdf(path, raster_only=True, width=width, height=height)
            result = check_pdf(path, "publication-pdf", semantic)
            self.assertEqual(result["status"], "BLOCKED")
            if importlib.util.find_spec("pypdf") is not None:
                self.assertGreater(result["embedded_image_count"], 0)
                self.assertFalse(result["vector_evidence"])
            else:
                self.assertIn("pypdf", result["reason"])

    @unittest.skipUnless(importlib.util.find_spec("pypdf"), "pypdf is not installed")
    def test_unrelated_vector_pdf_does_not_satisfy_semantic_text_checks(self) -> None:
        semantic = semantic_fixture()
        with tempfile.TemporaryDirectory(prefix="unrelated-vector-pdf-") as temporary:
            path = Path(temporary) / "unrelated.pdf"
            width = 180 * 72 / 25.4
            height = width * 675 / 1200
            write_pdf(path, raster_only=False, width=width, height=height)
            result = check_pdf(path, "publication-pdf", semantic)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertIn("Measurement", result["missing_text_labels"])

    @unittest.skipUnless(importlib.util.find_spec("pypdf"), "pypdf is not installed")
    def test_pdf_positive_requires_page_geometry_text_and_vector_evidence(self) -> None:
        semantic = semantic_fixture()
        with tempfile.TemporaryDirectory(prefix="vector-pdf-") as temporary:
            path = Path(temporary) / "vector.pdf"
            export_result = render_semantic_pdf(semantic, path)
            self.assertEqual(export_result["status"], "VERIFIED", export_result)
            result = check_pdf(path, "publication-pdf", semantic)
            self.assertEqual(result["status"], "VERIFIED", result)
            self.assertEqual(result["missing_equation_labels"], [])
            self.assertEqual(result["missing_shape_fill_colors"], [])
            self.assertEqual(result["missing_shape_stroke_colors"], [])

    def test_pdf_preserves_unicode_equation_and_token_paints(self) -> None:
        semantic = semantic_fixture()
        semantic["equation_objects"][0].update(
            fallback_text="y → x̂",
            latex_source=r"\hat{x}=f_\theta(y)",
            font_style="italic",
        )
        semantic["shapes"][1]["fill"] = "var(--surface2)"
        semantic["shapes"][1]["stroke"] = "accent"
        with tempfile.TemporaryDirectory(prefix="unicode-vector-pdf-") as temporary:
            path = Path(temporary) / "figure.pdf"
            export_result = render_semantic_pdf(semantic, path)
            self.assertEqual(export_result["status"], "VERIFIED", export_result)
            result = check_pdf(path, "publication-pdf", semantic)
            self.assertEqual(result["status"], "VERIFIED", result)
            self.assertEqual(result["missing_equation_labels"], [])
            self.assertEqual(result["missing_shape_fill_colors"], [])
            self.assertEqual(result["missing_shape_stroke_colors"], [])

    def test_pillow_font_coverage_rejects_replacement_glyphs(self) -> None:
        class Mask:
            def __init__(self, payload: bytes) -> None:
                self.payload = payload
                self.size = (len(payload), 1)

            def __bytes__(self) -> bytes:
                return self.payload

        class Font:
            def __init__(self, missing_arrow: bool) -> None:
                self.missing_arrow = missing_arrow

            def getmask(self, character: str) -> Mask:
                if character == "�" or (character == "→" and self.missing_arrow):
                    return Mask(b"replacement")
                return Mask(character.encode("utf-8"))

        self.assertFalse(_pillow_font_supports_text(Font(True), "y → x̂"))
        self.assertTrue(_pillow_font_supports_text(Font(False), "y → x̂"))

    def test_invalid_semantic_source_blocks_without_inspecting_adapters(self) -> None:
        with tempfile.TemporaryDirectory(prefix="invalid-semantic-") as temporary:
            run_dir = Path(temporary) / "run"
            source = run_dir / "source"
            source.mkdir(parents=True)
            (source / "semantic_figure.json").write_text('{"figure_id": "broken"}', encoding="utf-8")
            report = validate(run_dir)
            self.assertEqual(report["status"], "BLOCKED")
            self.assertEqual(len(report["checks"]), 1)
            self.assertTrue((run_dir / "validation" / "cross_format_report.json").is_file())

    def test_nested_semantic_objects_fail_closed_without_adapter_crashes(self) -> None:
        valid_semantic = semantic_fixture()
        malformed_semantic = semantic_fixture()
        malformed_semantic["shapes"][0] = {}
        malformed_semantic["connectors"] = []
        with tempfile.TemporaryDirectory(prefix="nested-semantic-") as temporary:
            run_dir = Path(temporary) / "run"
            source = run_dir / "source"
            delivery = run_dir / "delivery" / "svg"
            source.mkdir(parents=True)
            delivery.mkdir(parents=True)
            svg_path = delivery / "master.svg"
            svg_path.write_text(render_semantic_svg(valid_semantic), encoding="utf-8")
            direct = check_svg(svg_path, malformed_semantic, "svg")
            self.assertEqual(direct["status"], "BLOCKED")
            self.assertEqual(direct["reason"], "invalid canonical semantic source")

            write_json(source / "semantic_figure.json", malformed_semantic)
            report = validate(run_dir)
            self.assertEqual(report["status"], "BLOCKED")
            self.assertEqual(len(report["checks"]), 1)
            self.assertTrue(any("shapes[0].id" in error for error in report["checks"][0]["errors"]))

    def test_validate_binds_equations_tex_ids_and_exact_latex(self) -> None:
        semantic = semantic_fixture()
        with tempfile.TemporaryDirectory(prefix="equation-source-") as temporary:
            run_dir = Path(temporary) / "run"
            source = run_dir / "source"
            source.mkdir(parents=True)
            write_json(source / "semantic_figure.json", semantic)
            equations = source / "equations.tex"
            equations.write_text("% equation-id: model_label\n\\[f_\\theta\\]\n", encoding="utf-8")
            report = validate(run_dir)
            semantic_check = report["checks"][0]
            self.assertEqual(semantic_check["status"], "VERIFIED", semantic_check)
            self.assertTrue(semantic_check["equation_source_editability"])
            self.assertIn("equation_source_sha256", semantic_check)

            equations.write_text("% equation-id: model_label\n\\[g_\\phi\\]\n", encoding="utf-8")
            report = validate(run_dir)
            self.assertEqual(report["status"], "BLOCKED")
            self.assertEqual(len(report["checks"]), 1)
            self.assertTrue(any("LaTeX differs" in error for error in report["checks"][0]["errors"]))

    def test_unsupported_ports_block_formats_that_do_not_preserve_them(self) -> None:
        semantic = semantic_fixture()
        semantic["ports"] = [{"id": "measurement.out", "node_id": "measurement", "name": "out", "position": "right"}]
        with tempfile.TemporaryDirectory(prefix="unsupported-ports-") as temporary:
            directory = Path(temporary)
            drawio = directory / "figure.drawio"
            pptx = directory / "figure.pptx"
            build_drawio(semantic).write(drawio, encoding="unicode", xml_declaration=True)
            write_pptx(pptx, semantic)
            self.assertEqual(check_drawio(drawio, semantic)["status"], "BLOCKED")
            self.assertEqual(check_pptx(pptx, semantic)["status"], "BLOCKED")

    def test_incomplete_preview_is_blocked(self) -> None:
        semantic = semantic_fixture()
        with tempfile.TemporaryDirectory(prefix="incomplete-preview-") as temporary:
            run_dir = Path(temporary) / "run"
            result = create_preview(run_dir, semantic)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(
                set(result["missing_panels"]),
                {"SVG", "Figma-ready", "draw.io", "PPTX"},
            )


if __name__ == "__main__":
    unittest.main()
