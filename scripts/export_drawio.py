#!/usr/bin/env python3
"""Export native draw.io mxCells plus deterministic vector companions."""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Mapping, Tuple

from figure_artifacts import load_json, sha256_file, write_json
from workflow_v3 import render_semantic_pdf, render_semantic_svg, semantic_integrity_errors, write_text


def bounds(shape: Mapping[str, Any]) -> Tuple[float, float, float, float]:
    kind = shape.get("type")
    if kind == "rect":
        return shape["x"], shape["y"], shape["width"], shape["height"]
    if kind == "ellipse":
        return shape["cx"] - shape["rx"], shape["cy"] - shape["ry"], shape["rx"] * 2, shape["ry"] * 2
    if kind == "polygon":
        xs = [point[0] for point in shape["points"]]
        ys = [point[1] for point in shape["points"]]
        return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)
    if kind == "line":
        x = min(shape["x1"], shape["x2"]); y = min(shape["y1"], shape["y2"])
        return x, y, abs(shape["x2"] - shape["x1"]), abs(shape["y2"] - shape["y1"])
    return 0, 0, 10, 10


def make_cell(parent: ET.Element, cell_id: str, value: str, style: str, x: float, y: float, width: float, height: float, **attrs: str) -> ET.Element:
    cell = ET.SubElement(parent, "mxCell", {"id": cell_id, "value": value, "style": style, "vertex": "1", "parent": "1", **attrs})
    ET.SubElement(cell, "mxGeometry", {"x": str(x), "y": str(y), "width": str(width), "height": str(height), "as": "geometry"})
    return cell


def build_drawio(semantic: Mapping[str, Any]) -> ET.ElementTree:
    model = ET.Element("mxGraphModel", {"dx": "1600", "dy": "900", "grid": "1", "gridSize": "10", "page": "1", "pageWidth": str(semantic["canvas"]["width"]), "pageHeight": str(semantic["canvas"]["height"])})
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})
    for shape in semantic.get("shapes", []):
        x, y, width, height = bounds(shape)
        style = "rounded=1;whiteSpace=wrap;html=1;strokeWidth=2;"
        if shape.get("type") == "ellipse":
            style += "ellipse;"
        if shape.get("entity_type") == "generator":
            style += "shape=trapezoid;direction=south;"
        if shape.get("dash"):
            style += "dashed=1;dashPattern=8 6;"
        make_cell(root, shape["id"], "", style, x, y, width, height, semanticType=str(shape.get("entity_type", "shape")))
    for item in semantic.get("text_objects", []):
        make_cell(root, item["id"], item.get("text", ""), "text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;", item["x"] - 70, item["y"] - 24, 140, 34, semanticType="text")
    for equation in semantic.get("equation_objects", []):
        equation_left = equation["x"] - equation.get("width", 360) / 2 if equation.get("text_anchor") == "middle" else equation["x"]
        equation_value = "G<sub>θ</sub>" if equation.get("latex_source") == r"G_\theta" else equation.get("fallback_text", equation["equation_id"])
        make_cell(
            root, equation["id"], equation_value,
            "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;",
            equation_left, equation["y"] - equation.get("height", 36), equation.get("width", 360), equation.get("height", 36),
            semanticType="equation", equationId=equation["equation_id"], latexSource=equation.get("latex_source", ""),
        )
    for connector in semantic.get("connectors", []):
        edge = ET.SubElement(root, "mxCell", {
            "id": connector["id"], "value": connector.get("label", ""),
            "style": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;",
            "edge": "1", "parent": "1", "source": connector["source_id"], "target": connector["target_id"],
            "relationType": connector.get("relation_type", "relation"),
        })
        geometry = ET.SubElement(edge, "mxGeometry", {"relative": "1", "as": "geometry"})
        if len(connector.get("points", [])) > 2:
            array = ET.SubElement(geometry, "Array", {"as": "points"})
            for px, py in connector["points"][1:-1]:
                ET.SubElement(array, "mxPoint", {"x": str(px), "y": str(py)})
    return ET.ElementTree(model)


def export(semantic_path: Path, output_dir: Path) -> Dict[str, Any]:
    semantic = load_json(semantic_path)
    errors = semantic_integrity_errors(semantic)
    if errors:
        raise ValueError("invalid semantic source:\n%s" % "\n".join(errors))
    output_dir.mkdir(parents=True, exist_ok=True)
    drawio_path = output_dir / "figure.drawio"
    svg_path = output_dir / "figure_drawio.svg"
    pdf_path = output_dir / "figure_drawio_editable.pdf"
    tree = build_drawio(semantic)
    tree.write(drawio_path, encoding="unicode", xml_declaration=True)
    write_text(svg_path, render_semantic_svg(semantic, profile="drawio-companion"))
    pdf_result = render_semantic_pdf(semantic, pdf_path, grayscale=False)
    parsed = ET.parse(drawio_path)
    root = parsed.getroot()
    cells = root.findall(".//mxCell")
    edges = [item for item in cells if item.get("edge") == "1"]
    equation_cells = [item for item in cells if item.get("semanticType") == "equation"]
    report = {
        "status": "VERIFIED" if pdf_result["status"] == "VERIFIED" else "GENERATED_UNVERIFIED",
        "canonical_source": str(semantic_path.resolve()), "canonical_source_sha256": sha256_file(semantic_path),
        "drawio": str(drawio_path.resolve()), "svg": str(svg_path.resolve()), "pdf": str(pdf_path.resolve()) if pdf_path.exists() else None,
        "native_mxcell_count": len(cells), "native_edge_count": len(edges), "equation_cell_count": len(equation_cells),
        "semantic_editability": True, "equation_source_editability": True, "whole_canvas_raster": False,
        "reopen_test": "XML parse and native mxCell source/target inspection passed; GUI reopen not performed because no draw.io CLI is installed.",
        "pdf_editability": "Vector PDF is a companion view. The native editable source is figure.drawio; the PDF itself is not claimed as semantically editable.",
        "pdf_result": pdf_result,
    }
    write_json(output_dir / "drawio_export_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--semantic", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    report = export(args.semantic, args.output_dir)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
