#!/usr/bin/env python3
"""Validate a contract-driven semantic SVG with stable IDs and metadata."""

from __future__ import annotations

import argparse
import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

from figure_artifacts import load_json, normalize_whitespace, write_json


FORBIDDEN_TAGS = {
    "script",
    "foreignObject",
    "animate",
    "animateMotion",
    "animateTransform",
    "set",
    "filter",
    "linearGradient",
    "radialGradient",
    "mask",
}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_number(value: Optional[str], default: float = 0.0) -> float:
    if value is None:
        return default
    match = re.match(r"\s*(-?\d+(?:\.\d+)?)", value)
    return float(match.group(1)) if match else default


def parse_points(value: str) -> List[Tuple[float, float]]:
    numbers = [float(item) for item in re.findall(r"-?\d+(?:\.\d+)?", value)]
    return list(zip(numbers[0::2], numbers[1::2]))


def element_center(element: ET.Element) -> Optional[Tuple[float, float]]:
    tag = local_name(element.tag)
    if tag in {"circle", "ellipse"}:
        return parse_number(element.get("cx")), parse_number(element.get("cy"))
    if tag in {"rect", "text", "image"}:
        x_value = parse_number(element.get("x"))
        y_value = parse_number(element.get("y"))
        return (
            x_value + parse_number(element.get("width")) / 2,
            y_value + parse_number(element.get("height")) / 2,
        )
    if tag in {"polygon", "polyline"}:
        values = parse_points(element.get("points", ""))
        if values:
            return (
                sum(point[0] for point in values) / len(values),
                sum(point[1] for point in values) / len(values),
            )
    return None


def normalized_geometry(element: ET.Element) -> Optional[Tuple[Tuple[float, float], ...]]:
    tag = local_name(element.tag)
    if tag in {"polygon", "polyline"}:
        values = parse_points(element.get("points", ""))
    elif tag == "path":
        numbers = [float(item) for item in re.findall(r"-?\d+(?:\.\d+)?", element.get("d", ""))]
        values = list(zip(numbers[0::2], numbers[1::2]))
    elif tag == "rect":
        values = [
            (0.0, 0.0),
            (parse_number(element.get("width")), 0.0),
            (parse_number(element.get("width")), parse_number(element.get("height"))),
            (0.0, parse_number(element.get("height"))),
        ]
    else:
        return None
    if not values:
        return None
    minimum_x = min(point[0] for point in values)
    minimum_y = min(point[1] for point in values)
    return tuple((round(point[0] - minimum_x, 3), round(point[1] - minimum_y, 3)) for point in values)


def connector_is_orthogonal(element: ET.Element) -> bool:
    tag = local_name(element.tag)
    if tag == "line":
        x1, y1 = parse_number(element.get("x1")), parse_number(element.get("y1"))
        x2, y2 = parse_number(element.get("x2")), parse_number(element.get("y2"))
        return abs(x1 - x2) < 1e-6 or abs(y1 - y2) < 1e-6
    if tag in {"polyline", "polygon"}:
        values = parse_points(element.get("points", ""))
        return bool(values) and all(
            abs(left[0] - right[0]) < 1e-6 or abs(left[1] - right[1]) < 1e-6
            for left, right in zip(values, values[1:])
        )
    if tag == "path":
        path = element.get("d", "")
        if re.search(r"[CQSAcqsa]", path):
            return False
        if re.search(r"[HVhv]", path) and not re.search(r"[Ll]", path):
            return True
        numbers = [float(item) for item in re.findall(r"-?\d+(?:\.\d+)?", path)]
        values = list(zip(numbers[0::2], numbers[1::2]))
        return bool(values) and all(
            abs(left[0] - right[0]) < 1e-6 or abs(left[1] - right[1]) < 1e-6
            for left, right in zip(values, values[1:])
        )
    return False


def result(rule_id: str, passed: bool, evidence: Any, severity: str = "blocker") -> Dict[str, Any]:
    return {
        "rule_id": rule_id,
        "severity": severity,
        "status": "pass" if passed else "fail",
        "evidence": evidence,
    }


def validate_svg(svg_path: Path, spec_path: Path) -> Dict[str, Any]:
    spec = load_json(spec_path)
    checks: List[Dict[str, Any]] = []
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
        checks.append(result("SVG_PARSEABLE", True, "XML parsed"))
    except ET.ParseError as exc:
        return {
            "schema_version": "1.0",
            "svg": str(svg_path),
            "spec": str(spec_path),
            "checks": [result("SVG_PARSEABLE", False, str(exc))],
            "summary": {"overall": "fail", "passed": 0, "failed": 1, "blockers": 1},
        }

    elements = list(root.iter())
    identifiers = [element.get("id") for element in elements if element.get("id")]
    duplicate_ids = sorted({value for value in identifiers if identifiers.count(value) > 1})
    checks.append(result("SVG_UNIQUE_IDS", not duplicate_ids, {"duplicates": duplicate_ids}))
    id_map = {element.get("id"): element for element in elements if element.get("id")}

    forbidden_tags = [local_name(element.tag) for element in elements if local_name(element.tag) in FORBIDDEN_TAGS]
    forbidden_attributes = []
    for element in elements:
        for key, value in element.attrib.items():
            key_name = local_name(key).lower()
            lowered = value.lower()
            if key_name.startswith("on"):
                forbidden_attributes.append("%s:%s" % (element.get("id"), key_name))
            if key_name in {"href", "xlink:href"} and lowered.startswith(("http:", "https:", "file:")):
                forbidden_attributes.append("%s:%s" % (element.get("id"), value))
            if "url(http" in lowered or "url(file" in lowered:
                forbidden_attributes.append("%s:%s" % (element.get("id"), value))
    checks.append(result("SVG_FORBIDDEN_CONTENT", not forbidden_tags and not forbidden_attributes, {"tags": forbidden_tags, "attributes": forbidden_attributes}))

    images = [element.get("id") for element in elements if local_name(element.tag) == "image"]
    raster_allowed = bool(spec.get("raster_asset_policy", {}).get("allowed"))
    checks.append(result("SVG_NO_WHOLE_RASTER", raster_allowed or not images, {"image_ids": images, "raster_allowed": raster_allowed}))

    expected_groups = [item["id"] for item in spec.get("semantic_group_inventory", [])]
    missing_groups = [group_id for group_id in expected_groups if group_id not in id_map]
    checks.append(result("SVG_SEMANTIC_GROUPS", not missing_groups, {"missing": missing_groups}))

    visible_text = normalize_whitespace(" ".join("".join(element.itertext()) for element in elements if local_name(element.tag) == "text"))
    missing_text = [value for value in spec.get("exact_text", []) if normalize_whitespace(value) not in visible_text]
    latex_values = {element.get("data-latex") for element in elements if element.get("data-latex")}
    missing_equations = [value for value in spec.get("exact_equations", []) if value not in latex_values]
    checks.append(result("SVG_LIVE_TEXT_AND_EQUATIONS", not missing_text and not missing_equations, {"missing_text": missing_text, "missing_equations": missing_equations}))

    connectors = [element for element in elements if element.get("data-role") == "connector"]
    missing_metadata = []
    broken_refs = []
    for connector in connectors:
        source = connector.get("data-source")
        target = connector.get("data-target")
        if not source or not target:
            missing_metadata.append(connector.get("id"))
            continue
        if source not in id_map:
            broken_refs.append("%s source=%s" % (connector.get("id"), source))
        if target not in id_map:
            broken_refs.append("%s target=%s" % (connector.get("id"), target))
    checks.append(result("SVG_SOURCE_TARGET_METADATA", not missing_metadata and not broken_refs, {"missing_metadata": missing_metadata, "broken_refs": broken_refs}))

    endpoint_contracts = spec.get("relation_type_contracts", {})
    endpoint_type_problems = []
    for connector in connectors:
        relation_type = connector.get("data-relation-type")
        contract = endpoint_contracts.get(relation_type)
        if not contract:
            continue
        source = id_map.get(connector.get("data-source", ""))
        target = id_map.get(connector.get("data-target", ""))
        if source is None or target is None:
            continue
        source_type = source.get("data-entity-type")
        target_type = target.get("data-entity-type")
        if source_type not in contract.get("source_types", []) or target_type not in contract.get("target_types", []):
            endpoint_type_problems.append("%s %s->%s" % (connector.get("id"), source_type, target_type))
    checks.append(result("SVG_RELATION_ENDPOINT_TYPES", not endpoint_type_problems, endpoint_type_problems or "typed endpoints match the spec"))

    require_orthogonal = bool(spec.get("geometry_policy", {}).get("orthogonal_connectors", False))
    non_orthogonal = [element.get("id") for element in connectors if require_orthogonal and not connector_is_orthogonal(element)]
    checks.append(result("SVG_ORTHOGONAL_CONNECTORS", not non_orthogonal, {"required": require_orthogonal, "non_orthogonal": non_orthogonal}))

    expected_counts = spec.get("geometry_policy", {}).get("entity_counts_by_stage", {})
    count_problems = []
    for stage, type_counts in expected_counts.items():
        for entity_type, expected in type_counts.items():
            actual = sum(1 for element in elements if element.get("data-stage") == stage and element.get("data-entity-type") == entity_type)
            if actual != expected:
                count_problems.append("%s/%s=%d expected %d" % (stage, entity_type, actual, expected))
    checks.append(result("SVG_ENTITY_COUNTS", not count_problems, count_problems or "entity counts match"))

    centroid_tolerance = float(spec.get("geometry_policy", {}).get("centroid_tolerance_normalized", 0.005))
    view_box = [float(value) for value in root.get("viewBox", "0 0 1 1").split()]
    absolute_tolerance = centroid_tolerance * max(view_box[2], view_box[3])
    placement_problems = []
    for element in elements:
        if element.get("data-placement-rule") != "mean-of-member-centers":
            continue
        center = element_center(element)
        members = [id_map.get(member) for member in element.get("data-members", "").split()]
        member_centers = [element_center(member) for member in members if member is not None]
        member_centers = [value for value in member_centers if value is not None]
        if center is None or not member_centers:
            placement_problems.append("%s missing geometry/members" % element.get("id"))
            continue
        expected = (
            sum(value[0] for value in member_centers) / len(member_centers),
            sum(value[1] for value in member_centers) / len(member_centers),
        )
        if math.dist(center, expected) > absolute_tolerance:
            placement_problems.append("%s actual=%s expected=%s" % (element.get("id"), center, expected))
    checks.append(result("SVG_DERIVED_PLACEMENT", not placement_problems, placement_problems or "derived placements match"))

    congruence_problems = []
    for entity_type in spec.get("geometry_policy", {}).get("congruent_entity_types", []):
        matching = [element for element in elements if element.get("data-entity-type") == entity_type]
        geometries = [normalized_geometry(element) for element in matching]
        if len(matching) > 1 and any(value is None or value != geometries[0] for value in geometries):
            congruence_problems.append(entity_type)
    checks.append(result("SVG_CONGRUENT_REPETITIONS", not congruence_problems, congruence_problems or "repeated geometry is congruent"))

    minimum_font = float(spec.get("geometry_policy", {}).get("minimum_font_size_pt", 7.5))
    font_problems = []
    for element in elements:
        if local_name(element.tag) != "text":
            continue
        size = parse_number(element.get("font-size"))
        if size and size < minimum_font:
            font_problems.append("%s=%.2f" % (element.get("id"), size))
    checks.append(result("SVG_MIN_FONT_SIZE", not font_problems, font_problems or "font sizes pass"))

    min_x, min_y, width, height = view_box
    max_x, max_y = min_x + width, min_y + height
    bounds_problems = []
    for element in elements:
        center = element_center(element)
        if center is not None and not (min_x <= center[0] <= max_x and min_y <= center[1] <= max_y):
            bounds_problems.append(element.get("id"))
    checks.append(result("SVG_OBJECT_BOUNDS", not bounds_problems, bounds_problems or "object centers in bounds"))

    styles = "\n".join("".join(element.itertext()) for element in elements if local_name(element.tag) == "style")
    token_problems = []
    for token, value in spec.get("style_tokens", {}).items():
        css_name = "--" + token.replace("_", "-")
        if value == "pending_gate_2" or css_name not in styles or str(value).lower() not in styles.lower():
            token_problems.append(token)
    checks.append(result("SVG_GLOBAL_STYLE_TOKENS", not token_problems, token_problems or "tokens declared"))

    relation_count_problems = []
    for relation_type, expected in spec.get("geometry_policy", {}).get("relation_counts", {}).items():
        actual = sum(1 for element in connectors if element.get("data-relation-type") == relation_type)
        if actual != expected:
            relation_count_problems.append("%s=%d expected %d" % (relation_type, actual, expected))
    checks.append(result("SVG_RELATION_COUNTS", not relation_count_problems, relation_count_problems or "relation counts match"))

    failed_blockers = [check for check in checks if check["status"] == "fail" and check["severity"] == "blocker"]
    return {
        "schema_version": "1.0",
        "svg": str(svg_path),
        "spec": str(spec_path),
        "checks": checks,
        "summary": {
            "overall": "pass" if not failed_blockers else "fail",
            "passed": sum(check["status"] == "pass" for check in checks),
            "failed": sum(check["status"] == "fail" for check in checks),
            "blockers": len(failed_blockers),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--svg", required=True, type=Path)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = validate_svg(args.svg.resolve(), args.spec.resolve())
    if args.report:
        write_json(args.report.resolve(), report)
    print(json.dumps(report["summary"], indent=2))
    return 0 if report["summary"]["overall"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
