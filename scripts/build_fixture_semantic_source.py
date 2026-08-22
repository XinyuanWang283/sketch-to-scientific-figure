#!/usr/bin/env python3
"""Convert an ID-rich semantic SVG into the V3 canonical semantic source.

The historical filename is kept for compatibility with the fixture runner. The
converter also supports production runs when truth, wireframe, and selected PNG
provenance are supplied explicitly.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from figure_artifacts import load_json, sha256_bytes, sha256_file, write_json
from workflow_v3 import save_validated_json, semantic_integrity_errors, utc_now, write_text


SVG_NS = "{http://www.w3.org/2000/svg}"


def number(value: str | None, default: float = 0) -> float:
    if value is None:
        return default
    match = re.match(r"[-+]?\d+(?:\.\d+)?", value)
    return float(match.group(0)) if match else default


def style_number(element: ET.Element, name: str, default: float) -> float:
    direct = element.get(name)
    if direct is not None:
        return number(direct, default)
    match = re.search(r"(?:^|;)\s*%s\s*:\s*([-+]?\d+(?:\.\d+)?)" % re.escape(name), element.get("style", ""))
    return float(match.group(1)) if match else default


def points(value: str) -> List[List[float]]:
    return [[float(part) for part in pair.split(",")] for pair in value.strip().split()]


def group_for(element: ET.Element, root: ET.Element) -> str | None:
    target = element.get("id")
    for group in root.findall(".//%sg" % SVG_NS):
        if any(child.get("id") == target for child in list(group)):
            return group.get("id")
    return None


def inferred_stage(element: ET.Element) -> str:
    explicit = element.get("data-stage")
    return explicit or "global"


def inferred_entity_type(element: ET.Element, tag: str) -> str:
    explicit = element.get("data-entity-type")
    if explicit:
        return explicit
    identifier = element.get("id", "")
    if "guide" in identifier:
        return "guide"
    if "axis" in identifier or "bracket" in identifier or "cue" in identifier:
        return "axis"
    return "shape"


def equation_alignment(text_anchor: str) -> str:
    """Map SVG text anchors to the public equation-manifest vocabulary."""
    return {
        "start": "left",
        "middle": "center",
        "end": "right",
    }.get(text_anchor, "center")


def element_colors(element: ET.Element, tag: str) -> tuple[str, str]:
    classes = set(element.get("class", "").split())
    fill = element.get("fill")
    stroke = element.get("stroke")
    if fill is None:
        fill = "#1B2632" if "node" in classes else ("none" if tag == "line" else "#F2F4F6")
    if stroke is None:
        if classes.intersection({"soft", "guide", "bracket", "connector-secondary", "state-glyph"}):
            stroke = "#5F6B78"
        elif tag == "line" or classes.intersection({"ink", "axis-line", "connector"}):
            stroke = "#1B2632"
        else:
            stroke = fill if fill != "none" else "#1B2632"
    return fill, stroke


def simple_path_segments(path_data: str) -> List[tuple[float, float, float, float]]:
    """Convert paths made only of M/L/H/V commands into straight segments."""
    tokens = re.findall(r"[MmLlHhVvZzCcSsQqTtAa]|[-+]?(?:\d+(?:\.\d*)?|\.\d+)", path_data)
    if any(token in "CcSsQqTtAa" for token in tokens if len(token) == 1):
        return []
    segments: List[tuple[float, float, float, float]] = []
    index = 0
    command = ""
    x_value = 0.0
    y_value = 0.0
    while index < len(tokens):
        token = tokens[index]
        if len(token) == 1 and token.isalpha():
            command = token
            index += 1
            if command in "Zz":
                continue
        if command in "MmLl":
            if index + 1 >= len(tokens):
                break
            next_x = float(tokens[index]); next_y = float(tokens[index + 1]); index += 2
            if command.islower():
                next_x += x_value; next_y += y_value
            if command in "Ll":
                segments.append((x_value, y_value, next_x, next_y))
            x_value, y_value = next_x, next_y
            if command in "Mm":
                command = "l" if command == "m" else "L"
        elif command in "Hh":
            next_x = float(tokens[index]); index += 1
            if command == "h":
                next_x += x_value
            segments.append((x_value, y_value, next_x, y_value)); x_value = next_x
        elif command in "Vv":
            next_y = float(tokens[index]); index += 1
            if command == "v":
                next_y += y_value
            segments.append((x_value, y_value, x_value, next_y)); y_value = next_y
        else:
            return []
    return segments


def shape_center(shape: Mapping[str, Any]) -> tuple[float, float]:
    kind = shape.get("type")
    if kind == "rect":
        return shape["x"] + shape["width"] / 2, shape["y"] + shape["height"] / 2
    if kind == "ellipse":
        return shape["cx"], shape["cy"]
    if kind == "polygon":
        xs = [point[0] for point in shape["points"]]; ys = [point[1] for point in shape["points"]]
        return sum(xs) / len(xs), sum(ys) / len(ys)
    if kind == "line":
        return (shape["x1"] + shape["x2"]) / 2, (shape["y1"] + shape["y2"]) / 2
    return 0, 0


def descendants(group_id: str, group_members: Mapping[str, Sequence[str]], shape_ids: set[str]) -> set[str]:
    found: set[str] = set()
    pending = list(group_members.get(group_id, []))
    while pending:
        item = pending.pop()
        if item in shape_ids:
            found.add(item)
        elif item in group_members:
            pending.extend(group_members[item])
    return found


def resolve_endpoint(
    reference: str | None,
    endpoint: Sequence[float],
    shapes_by_id: Mapping[str, Mapping[str, Any]],
    group_members: Mapping[str, Sequence[str]],
) -> str | None:
    if reference in shapes_by_id:
        return reference
    candidates = descendants(reference or "", group_members, set(shapes_by_id))
    if not candidates:
        return reference
    return min(candidates, key=lambda candidate: math.dist(shape_center(shapes_by_id[candidate]), (float(endpoint[0]), float(endpoint[1]))))


def source_hashes(paths: Mapping[str, Path | None]) -> Dict[str, str]:
    return {name: sha256_file(path) for name, path in paths.items() if path is not None and path.exists()}


def build(
    svg_path: Path,
    spec_path: Path,
    run_dir: Path,
    *,
    figure_id: str | None = None,
    truth_path: Path | None = None,
    wireframe_path: Path | None = None,
    candidate_path: Path | None = None,
) -> Dict[str, Any]:
    root = ET.parse(svg_path).getroot()
    spec = load_json(spec_path)
    canvas_width = number(root.get("width"), 1000)
    canvas_height = number(root.get("height"), 600)

    groups = [
        {
            "id": item.get("id"),
            "role": item.get("data-role", "group"),
            "member_ids": [child.get("id") for child in list(item) if child.get("id")],
        }
        for item in root.findall(".//%sg" % SVG_NS)
        if item.get("id")
    ]
    group_members = {item["id"]: item["member_ids"] for item in groups}

    shapes: List[Dict[str, Any]] = []
    entities: List[Dict[str, Any]] = []
    for tag in ("rect", "circle", "ellipse", "polygon", "line"):
        for element in root.findall(".//%s%s" % (SVG_NS, tag)):
            sid = element.get("id")
            if not sid or sid in {"canvas", "paper-background"}:
                continue
            if element.get("data-role") == "connector" or sid.startswith("arrowhead-"):
                continue
            entity_type = inferred_entity_type(element, tag)
            fill, stroke = element_colors(element, tag)
            shape: Dict[str, Any] = {
                "id": sid,
                "type": "ellipse" if tag in {"circle", "ellipse"} else tag,
                "entity_type": entity_type,
                "group_id": group_for(element, root),
                "style_role": "surface",
                "fill_token": "literal",
                "stroke_token": "literal",
                "fill": fill,
                "stroke": stroke,
                "stroke_width": style_number(element, "stroke-width", 2.6),
            }
            if tag == "rect":
                shape.update(x=number(element.get("x")), y=number(element.get("y")), width=number(element.get("width")), height=number(element.get("height")), rx=number(element.get("rx"), 6))
            elif tag == "circle":
                shape.update(cx=number(element.get("cx")), cy=number(element.get("cy")), rx=number(element.get("r")), ry=number(element.get("r")))
            elif tag == "ellipse":
                shape.update(cx=number(element.get("cx")), cy=number(element.get("cy")), rx=number(element.get("rx")), ry=number(element.get("ry")))
            elif tag == "polygon":
                shape["points"] = points(element.get("points", ""))
            elif tag == "line":
                shape.update(x1=number(element.get("x1")), y1=number(element.get("y1")), x2=number(element.get("x2")), y2=number(element.get("y2")))
            if element.get("stroke-dasharray") or set(element.get("class", "").split()).intersection({"dash", "guide"}):
                shape["dash"] = element.get("stroke-dasharray", "7 7")
            shapes.append(shape)
            entities.append({"id": sid, "entity_type": entity_type, "stage": inferred_stage(element)})

    for element in root.findall(".//%spath" % SVG_NS):
        sid = element.get("id")
        if not sid or not ("bracket" in sid or element.get("data-entity-type") == "bracket"):
            continue
        fill, stroke = element_colors(element, "line")
        for index, (x1, y1, x2, y2) in enumerate(simple_path_segments(element.get("d", "")), start=1):
            segment_id = "%s-segment-%d" % (sid, index)
            shapes.append({
                "id": segment_id,
                "type": "line",
                "entity_type": "axis",
                "group_id": group_for(element, root),
                "style_role": "surface",
                "fill_token": "literal",
                "stroke_token": "literal",
                "fill": fill,
                "stroke": stroke,
                "stroke_width": style_number(element, "stroke-width", 2.4),
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
            })
            entities.append({"id": segment_id, "entity_type": "axis", "stage": inferred_stage(element)})

    shapes_by_id = {item["id"]: item for item in shapes}
    connectors: List[Dict[str, Any]] = []
    arrowheads = {
        element.get("id", "").removeprefix("arrowhead-"): points(element.get("points", ""))
        for element in root.findall(".//%spolygon" % SVG_NS)
        if element.get("id", "").startswith("arrowhead-")
    }
    connector_elements: Iterable[ET.Element] = list(root.findall(".//%spolyline" % SVG_NS)) + list(root.findall(".//%sline" % SVG_NS))
    for element in connector_elements:
        cid = element.get("id")
        if not cid or element.get("data-role") != "connector":
            continue
        connector_points = (
            points(element.get("points", ""))
            if element.tag.endswith("polyline")
            else [[number(element.get("x1")), number(element.get("y1"))], [number(element.get("x2")), number(element.get("y2"))]]
        )
        if cid in arrowheads and len(connector_points) >= 2:
            prior = connector_points[-2]
            endpoint = connector_points[-1]
            dx = endpoint[0] - prior[0]; dy = endpoint[1] - prior[1]
            connector_points[-1] = max(arrowheads[cid], key=lambda point: (point[0] - endpoint[0]) * dx + (point[1] - endpoint[1]) * dy)
        original_source = element.get("data-source")
        original_target = element.get("data-target")
        source_id = resolve_endpoint(original_source, connector_points[0], shapes_by_id, group_members)
        target_id = resolve_endpoint(original_target, connector_points[-1], shapes_by_id, group_members)
        classes = set(element.get("class", "").split())
        connectors.append({
            "id": cid,
            "source_id": source_id,
            "target_id": target_id,
            "source_group_id": original_source if original_source != source_id else None,
            "target_group_id": original_target if original_target != target_id else None,
            "relation_type": element.get("data-relation-type", "relation"),
            "points": connector_points,
            "arrow": "end",
            "multiplicity": int(element.get("data-multiplicity", "1")),
            "stroke_token": "muted" if "connector-secondary" in classes else "ink",
        })

    texts: List[Dict[str, Any]] = []
    equation_objects: List[Dict[str, Any]] = []
    equations: List[Dict[str, Any]] = []
    for element in root.findall(".//%stext" % SVG_NS):
        tid = element.get("id")
        if not tid:
            continue
        text = "".join(element.itertext()).strip()
        latex = element.get("data-latex")
        if latex:
            equation_id = tid.replace("eq-", "eq_").replace("-", "_")
            checksum = sha256_bytes(latex.encode("utf-8"))
            equation_width = number(element.get("data-equation-width"), 240)
            equation_height = number(element.get("data-equation-height"), 48)
            equation_objects.append({
                "id": tid,
                "equation_id": equation_id,
                "x": number(element.get("x")),
                "y": number(element.get("y")),
                "width": equation_width,
                "height": equation_height,
                "latex_source": latex,
                "fallback_text": text,
                "font_size": style_number(element, "font-size", 18),
                "text_anchor": element.get("text-anchor", "middle"),
                "font_family": element.get("font-family", "Georgia, Times New Roman, serif"),
                "font_style": element.get("font-style", "italic"),
            })
            equations.append({
                "equation_id": equation_id,
                "latex_source": latex,
                "role": element.get("data-equation-role", "primary"),
                "paper_source": {"path": str((truth_path or spec_path).resolve()), "locator": tid},
                "display_mode": element.get("data-display-mode", "inline"),
                "anchor_id": tid,
                "alignment": equation_alignment(element.get("text-anchor", "middle")),
                "style_role": "equation",
                "platform_render_policy": {
                    "svg": "live metadata plus vector glyphs",
                    "figma": "vector group plus LaTeX metadata",
                    "pptx": "equation SVG group plus LaTeX notes",
                    "drawio": "HTML label with LaTeX source",
                    "pdf": "vector glyphs",
                },
                "checksum": checksum,
            })
        else:
            classes = set(element.get("class", "").split())
            is_math = "math-label" in classes
            is_relation = "relation-label" in classes
            texts.append({
                "id": tid,
                "text": text,
                "x": number(element.get("x")),
                "y": number(element.get("y")),
                "font_size": max(12, style_number(element, "font-size", 12)),
                "font_weight": 700 if tid.startswith(("label", "stage-label")) else (500 if is_relation else 400),
                "font_family": "Georgia, Times New Roman, serif" if is_math else "Arial, Helvetica, sans-serif",
                "font_style": "italic" if is_math else "normal",
                "text_anchor": element.get("text-anchor", "middle" if classes.intersection({"stage-label", "math-label", "relation-label"}) else "start"),
                "fill_token": "muted" if is_relation else "ink",
                "group_id": group_for(element, root),
            })

    source_dir = run_dir / "source"
    math_dir = run_dir / "math"
    equation_tex = "\n\n".join("%% equation-id: %s\n\\[%s\\]" % (item["equation_id"], item["latex_source"]) for item in equations) + "\n"
    write_text(math_dir / "equations.tex", equation_tex)
    write_text(source_dir / "equations.tex", equation_tex)
    manifest = {"schema_version": "1.0", "authoritative_tex": "equations.tex", "equations": equations}
    save_validated_json(math_dir / "equation_manifest.json", manifest, "equation_manifest.schema.json")

    spec_tokens = spec.get("style_tokens", {})
    semantic = {
        "schema_version": "1.0",
        "figure_id": figure_id or spec.get("spec_id", "generic-semantic-fixture-v1"),
        "canvas": {
            "width": canvas_width,
            "height": canvas_height,
            "background": spec_tokens.get("background", "#FFFFFF"),
            "physical_width_mm": 180.0,
            "physical_height_mm": 180.0 * canvas_height / canvas_width,
        },
        "entities": entities,
        "groups": groups,
        "shapes": shapes,
        "text_objects": texts,
        "equation_objects": equation_objects,
        "ports": spec.get("ports", []),
        "connectors": connectors,
        "z_order": [item["id"] for item in shapes + connectors + texts + equation_objects],
        "style_tokens": {
            "colors": {
                "ink": spec_tokens.get("ink", "#1B2632"),
                "muted": spec_tokens.get("secondary_ink", "#5F6B78"),
                "warm": spec_tokens.get("warm", "#B45309"),
                "cool": spec_tokens.get("cool", "#4F7CAC"),
                "accent": spec_tokens.get("accent", "#7C6BAA"),
                "surface": spec_tokens.get("surface", "#FAFBFC"),
                "surface2": spec_tokens.get("surface2", "#E5EEF5"),
                "white": "#FFFFFF",
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
            "truth_source": str((truth_path or spec_path).resolve()),
            "equation_manifest": "../math/equation_manifest.json",
            "generated_at": utc_now(),
            "source_hashes": source_hashes({
                "semantic_svg": svg_path,
                "reconstruction_spec": spec_path,
                "scientific_truth": truth_path,
                "approved_wireframe": wireframe_path,
                "approved_png_direction": candidate_path,
            }),
            "source_roles": {
                "semantic_svg": "researcher-approved semantic geometry",
                "approved_wireframe": "binding macro-layout",
                "approved_png_direction": "art direction only; never embedded or traced",
            },
        },
    }
    errors = semantic_integrity_errors(semantic)
    if errors:
        raise ValueError("semantic source failed validation:\n%s" % "\n".join(errors))
    semantic_path = source_dir / "semantic_figure.json"
    write_json(semantic_path, semantic)
    report = {
        "semantic_source": str(semantic_path.resolve()),
        "equation_manifest": str((math_dir / "equation_manifest.json").resolve()),
        "equations_tex": str((math_dir / "equations.tex").resolve()),
        "source_svg_hash": sha256_file(svg_path),
        "shape_count": len(shapes),
        "text_count": len(texts),
        "equation_count": len(equations),
        "connector_count": len(connectors),
        "raster_assets_embedded": 0,
    }
    write_json(source_dir / "semantic_build_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--svg", required=True, type=Path)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--figure-id")
    parser.add_argument("--truth", type=Path)
    parser.add_argument("--wireframe", type=Path)
    parser.add_argument("--candidate", type=Path)
    args = parser.parse_args()
    print(json.dumps(build(
        args.svg,
        args.spec,
        args.run_dir,
        figure_id=args.figure_id,
        truth_path=args.truth,
        wireframe_path=args.wireframe,
        candidate_path=args.candidate,
    ), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
