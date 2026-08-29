#!/usr/bin/env python3
"""Executable structural and cross-format validation for V3 deliveries."""

from __future__ import annotations

import argparse
from collections import Counter
import html
import json
import math
import posixpath
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Mapping

from figure_artifacts import load_json, sha256_file, write_json
from workflow_v3 import (
    render_svg_to_png,
    resolve_hex_paint,
    semantic_integrity_errors,
    validate_schema,
)


PML = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
AML = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
RML = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
CONTENT_TYPES = {"ct": "http://schemas.openxmlformats.org/package/2006/content-types"}
OFFICE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
SVG_BLIP = "{http://schemas.microsoft.com/office/drawing/2016/SVG/main}svgBlip"
EMBED = "{%s}embed" % OFFICE_REL
RELATIONSHIP_ID = "{%s}id" % OFFICE_REL


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _normalized_text(value: str) -> str:
    return " ".join(value.split())


def _pptx_text_box_width(item: Mapping[str, Any], canvas_width: Any) -> float:
    """Mirror export_pptx.mjs textBoxWidth for deterministic live-text geometry."""
    font_size = _finite_float(item.get("font_size", 18))
    value = str(item.get("text") or "\n".join(item.get("lines", [])))
    longest_line = max((len(line) for line in value.split("\n")), default=0)
    estimated_width = math.ceil(longest_line * font_size * 0.62 + font_size)
    available_width = max(1.0, _finite_float(canvas_width) - 24.0)
    return min(max(180.0, float(estimated_width)), available_width)


def _finite_float(value: Any) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("number is not finite")
    return result


def _numbers_match(actual: Any, expected: Any, tolerance: float = 1e-6) -> bool:
    try:
        return abs(_finite_float(actual) - _finite_float(expected)) <= tolerance
    except (TypeError, ValueError, OverflowError):
        return False


def _canonical_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _points(value: str) -> List[List[float]]:
    points: List[List[float]] = []
    for chunk in value.replace(",", " ").split():
        # Parsed below in x/y pairs after normalizing comma separators.
        try:
            number = _finite_float(chunk)
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError("invalid point list") from error
        if not points or len(points[-1]) == 2:
            points.append([number])
        else:
            points[-1].append(number)
    if any(len(point) != 2 for point in points):
        raise ValueError("point list must contain x/y pairs")
    return points


def _point_lists_match(actual: Any, expected: Any, tolerance: float = 1e-6) -> bool:
    try:
        actual_points = _points(actual) if isinstance(actual, str) else actual
        if len(actual_points) != len(expected):
            return False
        return all(
            len(actual_point) == 2
            and len(expected_point) == 2
            and _numbers_match(actual_value, expected_value, tolerance)
            for actual_point, expected_point in zip(actual_points, expected)
            for actual_value, expected_value in zip(actual_point, expected_point)
        )
    except (TypeError, ValueError, OverflowError):
        return False


def _valid_point_list(value: Any, minimum: int) -> bool:
    return (
        isinstance(value, list)
        and len(value) >= minimum
        and all(
            isinstance(point, list)
            and len(point) == 2
            and all(_canonical_number(coordinate) for coordinate in point)
            for point in value
        )
    )


def _blocked(format_name: str, path: Path, reason: str, **details: Any) -> Dict[str, Any]:
    return {
        "format": format_name,
        "status": "BLOCKED",
        "reason": reason,
        "path": str(path.resolve()),
        "semantic_editability": False,
        "equation_source_editability": False,
        "scientific_validation": False,
        **details,
    }


def _semantic_preflight_errors(semantic: Any) -> List[str]:
    """Validate nested fields used directly by delivery adapters before dereferencing them."""
    if not isinstance(semantic, Mapping):
        return ["canonical semantic source must be a JSON object"]

    errors: List[str] = []
    try:
        errors.extend(semantic_integrity_errors(semantic))
    except Exception as error:
        errors.append("canonical semantic integrity inspection failed: %s" % error)

    collection_names = (
        "entities", "groups", "shapes", "text_objects", "equation_objects", "ports", "connectors",
    )
    collections: Dict[str, List[Mapping[str, Any]]] = {}
    for name in collection_names:
        value = semantic.get(name)
        if not isinstance(value, list):
            errors.append("%s must be an array" % name)
            collections[name] = []
            continue
        valid_items: List[Mapping[str, Any]] = []
        for index, item in enumerate(value):
            if not isinstance(item, Mapping):
                errors.append("%s[%d] must be an object" % (name, index))
                continue
            identifier = item.get("id")
            if not isinstance(identifier, str) or not identifier.strip():
                errors.append("%s[%d].id must be a non-empty string" % (name, index))
            valid_items.append(item)
        collections[name] = valid_items

    canvas = semantic.get("canvas")
    if not isinstance(canvas, Mapping):
        errors.append("canvas must be an object")
    else:
        for field in ("width", "height"):
            try:
                if not _canonical_number(canvas.get(field)) or _finite_float(canvas.get(field)) <= 0:
                    raise ValueError("must be positive")
            except (TypeError, ValueError, OverflowError):
                errors.append("canvas.%s must be a positive finite number" % field)
        for field in ("physical_width_mm", "physical_height_mm"):
            if canvas.get(field) is not None:
                try:
                    if not _canonical_number(canvas.get(field)) or _finite_float(canvas.get(field)) <= 0:
                        raise ValueError("must be positive")
                except (TypeError, ValueError, OverflowError):
                    errors.append("canvas.%s must be a positive finite number" % field)

    for index, item in enumerate(collections["groups"]):
        members = item.get("member_ids", [])
        if not isinstance(members, list) or any(not isinstance(value, str) or not value for value in members):
            errors.append("groups[%d].member_ids must be an array of non-empty strings" % index)

    shape_fields = {
        "rect": ("x", "y", "width", "height"),
        "ellipse": ("cx", "cy", "rx", "ry"),
        "line": ("x1", "y1", "x2", "y2"),
    }
    for index, item in enumerate(collections["shapes"]):
        kind = item.get("type")
        if kind == "polygon":
            points = item.get("points")
            if not _valid_point_list(points, 3):
                errors.append("shapes[%d].points must contain at least three finite x/y pairs" % index)
            continue
        fields = shape_fields.get(str(kind))
        if fields is None:
            errors.append("shapes[%d].type is unsupported" % index)
            continue
        try:
            if any(not _canonical_number(item.get(field)) for field in fields):
                raise ValueError("geometry fields must be numbers")
            values = {field: _finite_float(item.get(field)) for field in fields}
            if kind == "rect" and (values["width"] <= 0 or values["height"] <= 0):
                raise ValueError("non-positive rectangle")
            if kind == "ellipse" and (values["rx"] <= 0 or values["ry"] <= 0):
                raise ValueError("non-positive ellipse")
            if kind == "line" and values["x1"] == values["x2"] and values["y1"] == values["y2"]:
                raise ValueError("zero-length line")
        except (TypeError, ValueError, OverflowError):
            errors.append("shapes[%d] has invalid canonical geometry" % index)

    for index, item in enumerate(collections["text_objects"]):
        text = item.get("text")
        lines = item.get("lines")
        if not isinstance(text, str) and not (
            isinstance(lines, list) and all(isinstance(value, str) for value in lines)
        ):
            errors.append("text_objects[%d] must provide text or string lines" % index)
        try:
            if not _canonical_number(item.get("x")) or not _canonical_number(item.get("y")):
                raise ValueError("coordinates must be numbers")
            _finite_float(item.get("x"))
            _finite_float(item.get("y"))
            if item.get("font_size") is not None and (
                not _canonical_number(item.get("font_size")) or _finite_float(item.get("font_size")) <= 0
            ):
                raise ValueError("non-positive font size")
        except (TypeError, ValueError, OverflowError):
            errors.append("text_objects[%d] has invalid canonical geometry" % index)

    for index, item in enumerate(collections["equation_objects"]):
        if not isinstance(item.get("equation_id"), str) or not str(item.get("equation_id", "")).strip():
            errors.append("equation_objects[%d].equation_id must be a non-empty string" % index)
        if not isinstance(item.get("latex_source"), str) or not str(item.get("latex_source", "")).strip():
            errors.append("equation_objects[%d].latex_source must be a non-empty string" % index)
        try:
            numeric_values = (item.get("x"), item.get("y"), item.get("width", 360), item.get("height", 36))
            if any(not _canonical_number(value) for value in numeric_values):
                raise ValueError("equation geometry fields must be numbers")
            _finite_float(item.get("x"))
            _finite_float(item.get("y"))
            if _finite_float(item.get("width", 360)) <= 0 or _finite_float(item.get("height", 36)) <= 0:
                raise ValueError("non-positive equation bounds")
        except (TypeError, ValueError, OverflowError):
            errors.append("equation_objects[%d] has invalid canonical geometry" % index)

    for index, item in enumerate(collections["ports"]):
        if not isinstance(item.get("node_id"), str) or not item.get("node_id"):
            errors.append("ports[%d].node_id must be a non-empty string" % index)

    for index, item in enumerate(collections["connectors"]):
        for field in ("source_id", "target_id"):
            if not isinstance(item.get(field), str) or not item.get(field):
                errors.append("connectors[%d].%s must be a non-empty string" % (index, field))
        points = item.get("points")
        if not _valid_point_list(points, 2):
            errors.append("connectors[%d].points must contain at least two finite x/y pairs" % index)

    return list(dict.fromkeys(errors))


def _equation_source_errors(path: Path, semantic: Mapping[str, Any]) -> List[str]:
    if not path.is_file():
        return ["source/equations.tex is missing"]
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return ["source/equations.tex could not be read: %s" % error]

    pattern = re.compile(
        r"^%\s*equation-id:\s*([^\s]+)\s*\r?\n\s*\\\[(.*?)\\\]\s*$",
        flags=re.MULTILINE | re.DOTALL,
    )
    matches = list(pattern.finditer(source))
    residual = list(source)
    for match in matches:
        residual[match.start():match.end()] = " " * (match.end() - match.start())

    errors: List[str] = []
    if "".join(residual).strip():
        errors.append("source/equations.tex contains malformed or unparsed content")
    identifiers = [match.group(1) for match in matches]
    duplicates = sorted(identifier for identifier, count in Counter(identifiers).items() if count > 1)
    if duplicates:
        errors.append("source/equations.tex has duplicate equation IDs: %s" % ", ".join(duplicates))
    actual = {match.group(1): match.group(2).strip() for match in matches}
    expected = {
        str(item.get("equation_id", "")): str(item.get("latex_source", ""))
        for item in semantic.get("equation_objects", [])
    }
    missing = sorted(set(expected) - set(actual))
    unexpected = sorted(set(actual) - set(expected))
    mismatched = sorted(identifier for identifier in set(expected) & set(actual) if actual[identifier] != expected[identifier])
    if missing:
        errors.append("source/equations.tex is missing equation IDs: %s" % ", ".join(missing))
    if unexpected:
        errors.append("source/equations.tex has unexpected equation IDs: %s" % ", ".join(unexpected))
    if mismatched:
        errors.append("source/equations.tex LaTeX differs for equation IDs: %s" % ", ".join(mismatched))
    return errors


def check_svg(path: Path, semantic: Mapping[str, Any], profile: str) -> Dict[str, Any]:
    semantic_errors = _semantic_preflight_errors(semantic)
    if semantic_errors:
        return _blocked(profile, path, "invalid canonical semantic source", errors=semantic_errors)
    if not path.is_file():
        return _blocked(profile, path, "missing file")
    try:
        root = ET.parse(path).getroot()
        text = path.read_text(encoding="utf-8")
    except (ET.ParseError, OSError, UnicodeError) as error:
        return _blocked(profile, path, "SVG parse failed", error=str(error))
    if _local_name(root.tag) != "svg":
        return _blocked(profile, path, "root element is not svg")

    elements = list(root.iter())
    identifiers = [str(element.get("id")) for element in elements if element.get("id")]
    duplicate_ids = sorted(identifier for identifier, count in Counter(identifiers).items() if count > 1)
    id_map = {str(element.get("id")): element for element in elements if element.get("id")}
    required_ids = {
        str(item["id"])
        for key in ("groups", "shapes", "text_objects", "equation_objects", "ports", "connectors")
        for item in semantic.get(key, [])
    }
    missing = sorted(required_ids - set(id_map))
    actual_semantic_ids = {
        str(element.get("data-semantic-id"))
        for element in elements
        if element.get("data-semantic-id")
    }
    unexpected_semantic_ids = sorted(actual_semantic_ids - required_ids)
    raster_elements = [element for element in elements if _local_name(element.tag) == "image"]
    active_tags = sorted({
        _local_name(element.tag)
        for element in elements
        if _local_name(element.tag).lower() in {
            "script", "foreignobject", "iframe", "object", "embed", "animate", "animatemotion",
            "animatetransform", "set",
        }
    })
    active_attributes = sorted({
        "%s:%s" % (element.get("id", _local_name(element.tag)), _local_name(name))
        for element in elements
        for name in element.attrib
        if _local_name(name).lower().startswith("on")
    })
    external_refs: List[str] = []
    for element in elements:
        for name, value in element.attrib.items():
            normalized_value = str(value).strip()
            if _local_name(name).lower() == "href" and not normalized_value.startswith("#"):
                external_refs.append("non-fragment href")
            if re.search(r"(?:javascript:|data:|file:|https?://)", normalized_value, flags=re.IGNORECASE):
                external_refs.append("active or external attribute reference")
            for match in re.findall(r"url\s*\(\s*['\"]?([^)'\"\s]+)", normalized_value, flags=re.IGNORECASE):
                if not match.startswith("#"):
                    external_refs.append("external attribute url")
    css_text = " ".join("".join(element.itertext()) for element in elements if _local_name(element.tag) == "style")
    if re.search(r"@import", css_text, flags=re.IGNORECASE):
        external_refs.append("CSS @import")
    for match in re.findall(r"url\s*\(\s*['\"]?([^)'\"\s]+)", css_text, flags=re.IGNORECASE):
        if not match.startswith("#"):
            external_refs.append("CSS url")

    canvas_geometry_ok = False
    try:
        view_box = [_finite_float(value) for value in str(root.get("viewBox", "")).replace(",", " ").split()]
        canvas_geometry_ok = (
            len(view_box) == 4
            and _numbers_match(view_box[0], 0)
            and _numbers_match(view_box[1], 0)
            and _numbers_match(view_box[2], semantic["canvas"]["width"])
            and _numbers_match(view_box[3], semantic["canvas"]["height"])
        )
    except (KeyError, TypeError, ValueError, OverflowError):
        canvas_geometry_ok = False

    group_mismatches: Dict[str, List[str]] = {}
    for item in semantic.get("groups", []):
        identifier = str(item["id"])
        element = id_map.get(identifier)
        expected_members = " ".join(str(value) for value in item.get("member_ids", []))
        if element is None or _local_name(element.tag) != "g" or (
            element.get("data-semantic-id"), element.get("data-role"), element.get("data-members")
        ) != (identifier, str(item.get("role", "group")), expected_members):
            group_mismatches[identifier] = ["group metadata mismatch"]

    port_mismatches: Dict[str, List[str]] = {}
    for item in semantic.get("ports", []):
        identifier = str(item["id"])
        element = id_map.get(identifier)
        expected = (
            identifier, "port", str(item.get("node_id", "")), str(item.get("name", "")),
            str(item.get("position", "")),
        )
        actual = (
            element.get("data-semantic-id"), element.get("data-role"), element.get("data-node-id"),
            element.get("data-port-name"), element.get("data-position"),
        ) if element is not None and _local_name(element.tag) == "g" else None
        if actual != expected:
            port_mismatches[identifier] = ["port metadata mismatch"]

    shape_mismatches: Dict[str, List[str]] = {}
    shape_tags = {"rect": "rect", "ellipse": "ellipse", "polygon": "polygon", "line": "line"}
    for item in semantic.get("shapes", []):
        identifier = str(item["id"])
        element = id_map.get(identifier)
        kind = str(item.get("type", "rect"))
        problems: List[str] = []
        if element is None or _local_name(element.tag) != shape_tags.get(kind):
            problems.append("native shape type mismatch")
        else:
            if element.get("data-semantic-id") != identifier:
                problems.append("semantic ID metadata mismatch")
            if element.get("data-group-id", "") != str(item.get("group_id", "") or ""):
                problems.append("group metadata mismatch")
            attributes = {
                "rect": ("x", "y", "width", "height"),
                "ellipse": ("cx", "cy", "rx", "ry"),
                "line": ("x1", "y1", "x2", "y2"),
            }
            if kind in attributes and any(
                not _numbers_match(element.get(name), item.get(name)) for name in attributes[kind]
            ):
                problems.append("geometry mismatch")
            if kind == "polygon" and not _point_lists_match(element.get("points", ""), item.get("points", [])):
                problems.append("geometry mismatch")
        if problems:
            shape_mismatches[identifier] = problems

    text_mismatches = {}
    for item in semantic.get("text_objects", []):
        element = id_map.get(str(item["id"]))
        expected = _normalized_text(str(item.get("text") or "\n".join(item.get("lines", []))))
        actual = _normalized_text("".join(element.itertext())) if element is not None else ""
        geometry_ok = element is not None and _numbers_match(element.get("x"), item.get("x")) and _numbers_match(element.get("y"), item.get("y"))
        if element is None or _local_name(element.tag) != "text" or actual != expected or not geometry_ok:
            text_mismatches[str(item["id"])] = {"actual": actual, "expected": expected, "geometry_ok": geometry_ok}

    equation_mismatches = {}
    for item in semantic.get("equation_objects", []):
        element = id_map.get(str(item["id"]))
        visible_text = _normalized_text("".join(element.itertext())) if element is not None else ""
        transform = element.get("transform", "") if element is not None else ""
        translate = re.fullmatch(r"translate\(\s*([^,\s]+)[,\s]+([^\s)]+)\s*\)", transform)
        geometry_ok = bool(translate) and _numbers_match(translate.group(1), item.get("x")) and _numbers_match(translate.group(2), item.get("y"))
        expected_visible = _normalized_text(str(item.get("fallback_text", item.get("equation_id", ""))))
        if element is None or _local_name(element.tag) != "g" or (
            element.get("data-equation-id"), element.get("data-latex")
        ) != (str(item.get("equation_id", "")), str(item.get("latex_source", ""))) or not geometry_ok or visible_text != expected_visible:
            equation_mismatches[str(item["id"])] = {
                "reason": "source, visible fallback, or geometry mismatch",
                "visible_text": visible_text,
                "expected_visible_text": expected_visible,
                "geometry_ok": geometry_ok,
            }

    expected_connectors = {str(item["id"]): item for item in semantic.get("connectors", [])}
    connector_elements = [
        element
        for element in elements
        if element.get("data-role") == "connector" or element.get("data-relation-type") is not None
    ]
    actual_connector_ids = {str(element.get("id")) for element in connector_elements if element.get("id")}
    missing_connector_ids = sorted(set(expected_connectors) - actual_connector_ids)
    unexpected_connector_ids = sorted(actual_connector_ids - set(expected_connectors))
    connector_mismatches: Dict[str, List[str]] = {}
    for identifier, item in expected_connectors.items():
        element = id_map.get(identifier)
        expected = (
            "connector", str(item.get("source_id", "")), str(item.get("target_id", "")),
            str(item.get("relation_type", "relation")), str(item.get("direction", item.get("arrow", "end"))),
        )
        actual = (
            element.get("data-role"), element.get("data-source"), element.get("data-target"),
            element.get("data-relation-type"), element.get("data-direction"),
        ) if element is not None else None
        aliases_match = element is not None and (
            element.get("data-source-id"), element.get("data-target-id")
        ) == expected[1:3]
        arrow_ok = element is not None and (
            (expected[4] in {"end", "forward"} and str(element.get("marker-end", "")).startswith("url(#"))
            or (expected[4] not in {"end", "forward"} and not element.get("marker-end"))
        )
        geometry_ok = element is not None and _local_name(element.tag) == "polyline" and _point_lists_match(
            element.get("points", ""), item.get("points", [])
        )
        if actual != expected or not aliases_match or not arrow_ok or not geometry_ok:
            connector_mismatches[identifier] = {
                "actual": actual, "expected": expected, "geometry_ok": geometry_ok, "arrow_ok": arrow_ok,
            }

    equation_meta = sum(1 for element in elements if element.get("data-equation-id"))
    passed = not any((
        missing,
        unexpected_semantic_ids,
        duplicate_ids,
        not canvas_geometry_ok,
        raster_elements,
        active_tags,
        active_attributes,
        external_refs,
        group_mismatches,
        port_mismatches,
        shape_mismatches,
        text_mismatches,
        equation_mismatches,
        missing_connector_ids,
        unexpected_connector_ids,
        connector_mismatches,
    ))
    effective_status = (
        "IMPORT_READY_UNVERIFIED" if passed and profile == "figma-ready-svg"
        else ("VERIFIED" if passed else "BLOCKED")
    )
    return {
        "format": profile, "status": effective_status, "path": str(path.resolve()),
        "sha256": sha256_file(path), "missing_semantic_ids": missing,
        "unexpected_semantic_ids": unexpected_semantic_ids,
        "duplicate_ids": duplicate_ids, "canvas_geometry_ok": canvas_geometry_ok,
        "raster_element_count": len(raster_elements),
        "active_content_tags": active_tags, "active_content_attributes": active_attributes,
        "external_or_embedded_image_refs": external_refs, "group_mismatches": group_mismatches,
        "port_mismatches": port_mismatches, "shape_mismatches": shape_mismatches,
        "equation_metadata_count": equation_meta,
        "connector_metadata_count": len(connector_elements), "text_mismatches": text_mismatches,
        "equation_mismatches": equation_mismatches,
        "missing_connector_ids": missing_connector_ids, "unexpected_connector_ids": unexpected_connector_ids,
        "connector_mismatches": connector_mismatches, "semantic_editability": passed,
        "equation_source_editability": passed and bool(semantic.get("equation_objects")),
        "scientific_validation": False,
    }


def _pptx_properties(element: ET.Element) -> ET.Element | None:
    return element.find(".//p:cNvPr", PML)


def _pptx_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return _normalized_text(" ".join(node.text or "" for node in element.findall(".//a:t", AML)))


def _pptx_xfrm(element: ET.Element | None) -> tuple[float, float, float, float] | None:
    if element is None:
        return None
    transform = element.find(".//a:xfrm", AML)
    offset = transform.find("a:off", AML) if transform is not None else None
    extent = transform.find("a:ext", AML) if transform is not None else None
    if offset is None or extent is None:
        return None
    try:
        return tuple(
            _finite_float(value)
            for value in (
                offset.get("x"), offset.get("y"), extent.get("cx"), extent.get("cy"),
            )
        )  # type: ignore[return-value]
    except (TypeError, ValueError, OverflowError):
        return None


def _pptx_paint(element: ET.Element | None, *, line: bool = False) -> str:
    if element is None:
        return ""
    namespaces = {**PML, **AML}
    container = element.find("./p:spPr/a:ln", namespaces) if line else element.find("./p:spPr", namespaces)
    if container is None:
        return ""
    if container.find("./a:noFill", AML) is not None:
        return "none"
    color = container.find("./a:solidFill/a:srgbClr", AML)
    if color is None:
        return ""
    value = str(color.get("val", "")).strip()
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", value):
        return ""
    return "#" + value.upper()


def _pptx_bounds(item: Mapping[str, Any]) -> tuple[float, float, float, float]:
    kind = str(item.get("type", "rect"))
    if kind == "rect":
        return tuple(_finite_float(item[name]) for name in ("x", "y", "width", "height"))  # type: ignore[return-value]
    if kind == "ellipse":
        cx, cy, rx, ry = (_finite_float(item[name]) for name in ("cx", "cy", "rx", "ry"))
        return cx - rx, cy - ry, rx * 2, ry * 2
    if kind == "polygon":
        points = item.get("points", [])
        xs = [_finite_float(point[0]) for point in points]
        ys = [_finite_float(point[1]) for point in points]
        if not xs or not ys:
            raise ValueError("polygon has no points")
        return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)
    if kind == "line":
        x1, y1, x2, y2 = (_finite_float(item[name]) for name in ("x1", "y1", "x2", "y2"))
        return min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)
    raise ValueError("unsupported shape type")


def _pptx_geometry_matches(
    actual: tuple[float, float, float, float] | None,
    expected: tuple[float, float, float, float],
    scale_x: float,
    scale_y: float,
    tolerance: float = 2.0,
) -> bool:
    if actual is None:
        return False
    scaled = (
        expected[0] * scale_x, expected[1] * scale_y,
        expected[2] * scale_x, expected[3] * scale_y,
    )
    return all(_numbers_match(found, wanted, tolerance) for found, wanted in zip(actual, scaled))


def _pptx_custom_path_matches(
    element: ET.Element | None,
    points: List[List[Any]],
    left: float,
    top: float,
    width: float,
    height: float,
    scale_x: float,
    scale_y: float,
) -> bool:
    if element is None:
        return False
    paths = element.findall(".//a:custGeom/a:pathLst/a:path", AML)
    if len(paths) != 1:
        return False
    path = paths[0]
    commands = list(path)
    if len(commands) != len(points):
        return False
    expected_commands = ["moveTo", *("lnTo" for _ in points[1:])]
    actual_points: List[List[Any]] = []
    for command, expected_command in zip(commands, expected_commands):
        point = command.find("a:pt", AML)
        if _local_name(command.tag) != expected_command or point is None:
            return False
        actual_points.append([point.get("x"), point.get("y")])
    expected_points = [
        [(_finite_float(point[0]) - left) * scale_x, (_finite_float(point[1]) - top) * scale_y]
        for point in points
    ]
    return (
        _numbers_match(path.get("w"), width * scale_x, 2.0)
        and _numbers_match(path.get("h"), height * scale_y, 2.0)
        and _point_lists_match(actual_points, expected_points, 2.0)
    )


def _relationships(archive: zipfile.ZipFile, part: str) -> Dict[str, Dict[str, str]]:
    root = ET.fromstring(archive.read(part))
    return {
        str(item.get("Id")): {"type": str(item.get("Type", "")), "target": str(item.get("Target", ""))}
        for item in root.findall("r:Relationship", RML)
        if item.get("Id")
    }


def _resolved_part(source_part: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(source_part), target))


def check_pptx(path: Path, semantic: Mapping[str, Any]) -> Dict[str, Any]:
    semantic_errors = _semantic_preflight_errors(semantic)
    if semantic_errors:
        return _blocked("pptx", path, "invalid canonical semantic source", errors=semantic_errors)
    if not path.is_file():
        return _blocked("pptx", path, "missing file")
    required_relationship_parts = {
        "_rels/.rels", "ppt/_rels/presentation.xml.rels", "ppt/slides/_rels/slide1.xml.rels",
    }
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            corrupt_member = archive.testzip()
            slide_names = sorted(
                name for name in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
            )
            required_parts = {"[Content_Types].xml", "ppt/presentation.xml", *required_relationship_parts}
            missing_package_parts = sorted(required_parts - set(names))
            if missing_package_parts or not slide_names or corrupt_member:
                return _blocked("pptx", path, "missing required OOXML presentation parts")
            content_types_root = ET.fromstring(archive.read("[Content_Types].xml"))
            content_type_overrides = {
                str(item.get("PartName", "")).lstrip("/"): str(item.get("ContentType", ""))
                for item in content_types_root.findall("ct:Override", CONTENT_TYPES)
            }
            content_type_defaults = {
                str(item.get("Extension", "")).lower(): str(item.get("ContentType", ""))
                for item in content_types_root.findall("ct:Default", CONTENT_TYPES)
            }

            def content_type_for(part: str) -> str:
                return content_type_overrides.get(
                    part, content_type_defaults.get(part.rsplit(".", 1)[-1].lower(), ""),
                )

            content_types_ok = (
                _local_name(content_types_root.tag) == "Types"
                and content_type_for("ppt/presentation.xml")
                == "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"
                and content_type_for("ppt/slides/slide1.xml")
                == "application/vnd.openxmlformats-officedocument.presentationml.slide+xml"
            )
            presentation = ET.fromstring(archive.read("ppt/presentation.xml"))
            slides = [ET.fromstring(archive.read(name)) for name in slide_names]
            root_relationships = _relationships(archive, "_rels/.rels")
            presentation_relationships = _relationships(archive, "ppt/_rels/presentation.xml.rels")
            slide_relationships = _relationships(archive, "ppt/slides/_rels/slide1.xml.rels")
            office_document_ok = any(
                item["type"].endswith("/officeDocument")
                and _resolved_part("", item["target"]) == "ppt/presentation.xml"
                for item in root_relationships.values()
            )
            slide_ids = presentation.findall(".//p:sldId", PML)
            slide_relationship = (
                presentation_relationships.get(str(slide_ids[0].get(RELATIONSHIP_ID, "")))
                if len(slide_ids) == 1 else None
            )
            slide_relationship_ok = bool(
                slide_relationship
                and slide_relationship["type"].endswith("/slide")
                and _resolved_part("ppt/presentation.xml", slide_relationship["target"])
                == "ppt/slides/slide1.xml"
                and "ppt/slides/slide1.xml" in names
            )
            notes = ""
            for name in names:
                if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name):
                    notes += " " + _pptx_text(ET.fromstring(archive.read(name)))
            package_names = set(names)
            slide_xml = slides[0] if len(slides) == 1 else None
            vector_targets: List[str] = []
            invalid_vector_relationships: List[str] = []
            if slide_xml is not None:
                for svg_blip in slide_xml.findall(".//" + SVG_BLIP):
                    relationship_id = str(svg_blip.get(EMBED, ""))
                    relationship = slide_relationships.get(relationship_id)
                    target = _resolved_part("ppt/slides/slide1.xml", relationship["target"]) if relationship else ""
                    if (
                        not relationship
                        or not relationship["type"].endswith("/image")
                        or target not in package_names
                        or not target.lower().endswith(".svg")
                        or content_type_for(target) != "image/svg+xml"
                    ):
                        invalid_vector_relationships.append(relationship_id or "missing relationship ID")
                        continue
                    try:
                        media_root = ET.fromstring(archive.read(target))
                        if _local_name(media_root.tag) != "svg":
                            raise ET.ParseError("vector image root is not svg")
                        for media_element in media_root.iter():
                            if _local_name(media_element.tag).lower() in {
                                "script", "foreignobject", "iframe", "object", "embed",
                            }:
                                raise ET.ParseError("vector media contains active content")
                            for attribute, value in media_element.attrib.items():
                                if _local_name(attribute).lower().startswith("on"):
                                    raise ET.ParseError("vector media contains an event attribute")
                                if _local_name(attribute).lower() == "href" and not str(value).startswith("#"):
                                    raise ET.ParseError("vector media contains a non-fragment reference")
                    except (KeyError, ET.ParseError):
                        invalid_vector_relationships.append(relationship_id)
                        continue
                    vector_targets.append(target)
    except (OSError, KeyError, ET.ParseError, ValueError, zipfile.BadZipFile) as error:
        return _blocked("pptx", path, "invalid OOXML presentation", error=str(error))

    shapes = [item for slide in slides for item in slide.findall(".//p:sp", PML)]
    connectors = [item for slide in slides for item in slide.findall(".//p:cxnSp", PML)]
    pictures = [item for slide in slides for item in slide.findall(".//p:pic", PML)]
    named_objects: Dict[str, ET.Element] = {}
    numeric_names: Dict[str, str] = {}
    all_named_elements = [*shapes, *pictures, *connectors]
    object_names: List[str] = []
    numeric_ids: List[str] = []
    for element in all_named_elements:
        properties = _pptx_properties(element)
        if properties is None:
            continue
        name = properties.get("name", "")
        if name:
            named_objects[name] = element
            object_names.append(name)
        if properties.get("id"):
            numeric_names[str(properties.get("id"))] = name
            numeric_ids.append(str(properties.get("id")))
    duplicate_object_names = sorted(name for name, count in Counter(object_names).items() if count > 1)
    duplicate_numeric_ids = sorted(identifier for identifier, count in Counter(numeric_ids).items() if count > 1)

    def attached_name(reference: ET.Element | None) -> str:
        if reference is None:
            return ""
        return numeric_names.get(reference.get("id", ""), "")

    try:
        slide_size = presentation.find(".//p:sldSz", PML)
        slide_width = _finite_float(slide_size.get("cx")) if slide_size is not None else 0.0
        slide_height = _finite_float(slide_size.get("cy")) if slide_size is not None else 0.0
        canvas_width = _finite_float(semantic["canvas"]["width"])
        canvas_height = _finite_float(semantic["canvas"]["height"])
        scale_x = slide_width / canvas_width if canvas_width else 0.0
        scale_y = slide_height / canvas_height if canvas_height else 0.0
        slide_geometry_ok = (
            slide_width > 0 and slide_height > 0 and scale_x > 0 and scale_y > 0
            and abs(scale_x - scale_y) <= max(scale_x, scale_y) * 0.005
        )
    except (KeyError, TypeError, ValueError, OverflowError):
        slide_width = slide_height = scale_x = scale_y = 0.0
        slide_geometry_ok = False

    expected_native_names = {
        str(item["id"])
        for collection in ("shapes", "text_objects")
        for item in semantic.get(collection, [])
    }
    native_shape_names = {
        str(properties.get("name"))
        for shape in shapes
        if (properties := _pptx_properties(shape)) is not None and properties.get("name")
    }
    missing_native_object_names = sorted(expected_native_names - native_shape_names)
    allowed_helper_names = {
        "%s-%s" % (item["id"], suffix)
        for item in semantic.get("connectors", [])
        for suffix in ("visible-path", "visible-arrowhead")
    }
    allowed_equation_fallback_names = {
        str(item["id"]) for item in semantic.get("equation_objects", [])
    }
    unexpected_native_shape_names = sorted(
        native_shape_names - expected_native_names - allowed_helper_names - allowed_equation_fallback_names
    )
    live_text_mismatches = {
        str(item["id"]): _pptx_text(named_objects.get(str(item["id"])))
        for item in semantic.get("text_objects", [])
        if _pptx_text(named_objects.get(str(item["id"])))
        != _normalized_text(str(item.get("text") or "\n".join(item.get("lines", []))))
    }
    native_geometry_mismatches: Dict[str, List[str]] = {}
    native_paint_mismatches: Dict[str, List[str]] = {}
    expected_primitives = {"rect": "rect", "ellipse": "ellipse", "line": "line", "polygon": "custom"}
    style_tokens = semantic.get("style_tokens", {})
    colors_value = style_tokens.get("colors", {}) if isinstance(style_tokens, Mapping) else {}
    colors = colors_value if isinstance(colors_value, Mapping) else {}
    for item in semantic.get("shapes", []):
        identifier = str(item["id"])
        element = named_objects.get(identifier)
        problems: List[str] = []
        try:
            expected_bounds = _pptx_bounds(item)
        except (KeyError, TypeError, ValueError, OverflowError):
            expected_bounds = (0.0, 0.0, 0.0, 0.0)
            problems.append("invalid canonical geometry")
        if element is None or not _pptx_geometry_matches(_pptx_xfrm(element), expected_bounds, scale_x, scale_y):
            problems.append("geometry mismatch")
        preset = element.find(".//a:prstGeom", AML) if element is not None else None
        custom = element.find(".//a:custGeom", AML) if element is not None else None
        expected_primitive = expected_primitives.get(str(item.get("type", "rect")))
        rounded_rects = bool(
            semantic.get("platform_overrides", {})
            .get("pptx", {})
            .get("rounded_rects", False)
        )
        if (
            rounded_rects
            and str(item.get("type", "rect")) == "rect"
            and _finite_float(item.get("rx", 0)) > 0
        ):
            expected_primitive = "roundRect"
        actual_primitive = preset.get("prst") if preset is not None else ("custom" if custom is not None else "")
        if expected_primitive != actual_primitive:
            problems.append("native primitive mismatch")
        if problems:
            native_geometry_mismatches[identifier] = problems
        expected_fill = (
            "none" if str(item.get("type")) == "line"
            else resolve_hex_paint(item.get("fill"), colors, str(colors.get("surface", "#F2F4F6")))
        )
        expected_stroke = resolve_hex_paint(
            item.get("stroke"), colors, str(colors.get("ink", "#20252B")),
        )
        actual_fill = _pptx_paint(element)
        actual_stroke = _pptx_paint(element, line=True)
        paint_problems: List[str] = []
        if actual_fill != expected_fill:
            paint_problems.append("fill=%r expected=%r" % (actual_fill, expected_fill))
        if actual_stroke != expected_stroke:
            paint_problems.append("stroke=%r expected=%r" % (actual_stroke, expected_stroke))
        if paint_problems:
            native_paint_mismatches[identifier] = paint_problems
    for item in semantic.get("text_objects", []):
        identifier = str(item["id"])
        try:
            font_size = _finite_float(item.get("font_size", 18))
            x_value = _finite_float(item.get("x"))
            y_value = _finite_float(item.get("y"))
            text_width = _pptx_text_box_width(item, semantic["canvas"]["width"])
            expected_bounds = (
                x_value - text_width / 2 if item.get("text_anchor") == "middle" else x_value,
                y_value - font_size * 1.2, text_width, font_size * 1.7,
            )
            geometry_ok = _pptx_geometry_matches(_pptx_xfrm(named_objects.get(identifier)), expected_bounds, scale_x, scale_y)
        except (TypeError, ValueError, OverflowError):
            geometry_ok = False
        if not geometry_ok:
            native_geometry_mismatches.setdefault(identifier, []).append("text geometry mismatch")

    connector_map = {
        str(properties.get("name")): connector
        for connector in connectors
        if (properties := _pptx_properties(connector)) is not None and properties.get("name")
    }
    expected_connectors = {str(item["id"]): item for item in semantic.get("connectors", [])}
    missing_connector_ids = sorted(set(expected_connectors) - set(connector_map))
    unexpected_connector_ids = sorted(set(connector_map) - set(expected_connectors))
    connector_mismatches: Dict[str, List[str]] = {}
    for identifier, item in expected_connectors.items():
        connector = connector_map.get(identifier)
        start = connector.find(".//a:stCxn", AML) if connector is not None else None
        end = connector.find(".//a:endCxn", AML) if connector is not None else None
        actual = (
            attached_name(start),
            attached_name(end),
        )
        expected = (str(item.get("source_id", "")), str(item.get("target_id", "")))
        if actual != expected:
            connector_mismatches[identifier] = ["endpoints=%r expected=%r" % (actual, expected)]

    vector_pictures = [picture for picture in pictures if picture.find(".//" + SVG_BLIP) is not None]
    raster_pictures = [picture for picture in pictures if picture.find(".//" + SVG_BLIP) is None]
    raster_picture_ids = [
        (_pptx_properties(picture).get("name", "") if _pptx_properties(picture) is not None else "")
        for picture in raster_pictures
    ]
    equation_mismatches: Dict[str, List[str]] = {}
    expected_vector_bounds: List[tuple[str, tuple[float, float, float, float]]] = []
    for item in semantic.get("equation_objects", []):
        identifier = str(item["id"])
        equation_id = str(item.get("equation_id", ""))
        latex = str(item.get("latex_source", ""))
        fallback_shape = named_objects.get(identifier) if identifier in native_shape_names else None
        native_fallback = _pptx_text(fallback_shape)
        expected_fallback = _normalized_text(str(item.get("fallback_text", "")))
        native_fallback_present = fallback_shape is not None
        native_fallback_found = native_fallback_present and bool(expected_fallback) and native_fallback == expected_fallback
        notes_have_source = bool(equation_id) and bool(latex) and equation_id in notes and latex in notes
        problems: List[str] = []
        try:
            width = _finite_float(item.get("width", 360))
            height = _finite_float(item.get("height", 36))
            x_value = _finite_float(item.get("x"))
            y_value = _finite_float(item.get("y"))
            left = x_value - width / 2 if item.get("text_anchor") == "middle" else x_value
            equation_bounds = (left, y_value - height, width, height)
        except (TypeError, ValueError, OverflowError):
            equation_bounds = (0.0, 0.0, 0.0, 0.0)
            problems.append("invalid equation geometry")
        if native_fallback_present:
            if not native_fallback_found:
                problems.append("fallback equation text mismatch")
            if not _pptx_geometry_matches(_pptx_xfrm(fallback_shape), equation_bounds, scale_x, scale_y):
                problems.append("fallback equation geometry mismatch")
        else:
            expected_vector_bounds.append((identifier, equation_bounds))
        if not notes_have_source:
            problems.append("missing equation source in notes")
        if problems:
            equation_mismatches[identifier] = problems

    unmatched_vector_pictures = list(vector_pictures)
    for identifier, expected_bounds in expected_vector_bounds:
        match = next((
            picture for picture in unmatched_vector_pictures
            if _pptx_geometry_matches(_pptx_xfrm(picture), expected_bounds, scale_x, scale_y)
        ), None)
        if match is None:
            equation_mismatches.setdefault(identifier, []).append("missing vector equation object at canonical geometry")
        else:
            unmatched_vector_pictures.remove(match)
    if unmatched_vector_pictures:
        equation_mismatches.setdefault("unexpected-vector-equations", []).append(
            "%d unmatched vector pictures" % len(unmatched_vector_pictures)
        )
    if invalid_vector_relationships:
        equation_mismatches.setdefault("vector-relationships", []).append("invalid SVG media relationships")

    whole_canvas_picture_ids: List[str] = []
    for picture in pictures:
        properties = _pptx_properties(picture)
        geometry = _pptx_xfrm(picture)
        if properties is None or geometry is None or not slide_geometry_ok:
            continue
        width, height = geometry[2], geometry[3]
        if width >= slide_width * 0.8 and height >= slide_height * 0.8:
            whole_canvas_picture_ids.append(properties.get("name", ""))

    connector_geometry_mismatches: List[str] = []
    for identifier, item in expected_connectors.items():
        try:
            points = item["points"]
            xs = [_finite_float(point[0]) for point in points]
            ys = [_finite_float(point[1]) for point in points]
            native_bounds = (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
            helper_bounds = (
                native_bounds[0], native_bounds[1], max(1.0, native_bounds[2]), max(1.0, native_bounds[3]),
            )
            native_geometry_ok = _pptx_geometry_matches(
                _pptx_xfrm(connector_map.get(identifier)), native_bounds, scale_x, scale_y,
            )
            helper = named_objects.get(identifier + "-visible-path")
            helper_geometry_ok = bool(
                helper is not None
                and _pptx_geometry_matches(_pptx_xfrm(helper), helper_bounds, scale_x, scale_y)
                and _pptx_custom_path_matches(
                    helper,
                    points,
                    native_bounds[0],
                    native_bounds[1],
                    helper_bounds[2],
                    helper_bounds[3],
                    scale_x,
                    scale_y,
                )
            )
        except (KeyError, TypeError, ValueError, OverflowError):
            native_geometry_ok = helper_geometry_ok = False
        if not native_geometry_ok and not helper_geometry_ok:
            connector_geometry_mismatches.append(identifier)
    unsupported_ports = [str(item.get("id", "")) for item in semantic.get("ports", [])]

    passed = not any((
        len(slides) != 1,
        not content_types_ok,
        not office_document_ok,
        not slide_relationship_ok,
        not slide_geometry_ok,
        not shapes,
        duplicate_object_names,
        duplicate_numeric_ids,
        missing_native_object_names,
        unexpected_native_shape_names,
        native_geometry_mismatches,
        native_paint_mismatches,
        live_text_mismatches,
        missing_connector_ids,
        unexpected_connector_ids,
        connector_mismatches,
        equation_mismatches,
        connector_geometry_mismatches,
        whole_canvas_picture_ids,
        raster_picture_ids,
        unsupported_ports,
    ))
    return {
        "format": "pptx", "status": "VERIFIED" if passed else "BLOCKED", "path": str(path.resolve()),
        "sha256": sha256_file(path), "slide_count": len(slides), "slide_geometry_ok": slide_geometry_ok,
        "content_types_ok": content_types_ok,
        "office_document_relationship_ok": office_document_ok,
        "slide_relationship_ok": slide_relationship_ok,
        "duplicate_object_names": duplicate_object_names, "duplicate_numeric_ids": duplicate_numeric_ids,
        "native_shape_count": len(shapes), "native_connector_count": len(connectors),
        "live_text_shape_count": sum(bool(_pptx_text(shape)) for shape in shapes),
        "picture_count": len(pictures), "missing_native_object_names": missing_native_object_names,
        "unexpected_native_shape_names": unexpected_native_shape_names,
        "live_text_mismatches": live_text_mismatches, "native_geometry_mismatches": native_geometry_mismatches,
        "native_paint_mismatches": native_paint_mismatches,
        "missing_connector_ids": missing_connector_ids,
        "unexpected_connector_ids": unexpected_connector_ids, "connector_mismatches": connector_mismatches,
        "equation_mismatches": equation_mismatches, "whole_canvas_picture_ids": whole_canvas_picture_ids,
        "vector_picture_count": len(vector_pictures), "vector_media_targets": vector_targets,
        "invalid_vector_relationships": invalid_vector_relationships,
        "raster_picture_ids": raster_picture_ids,
        "connector_geometry_mismatches": connector_geometry_mismatches,
        "unsupported_port_ids": unsupported_ports,
        "port_preservation": "BLOCKED_UNSUPPORTED" if unsupported_ports else "NOT_APPLICABLE",
        "semantic_editability": passed,
        "equation_source_editability": passed and bool(semantic.get("equation_objects")),
        "scientific_validation": False,
    }


def check_drawio(path: Path, semantic: Mapping[str, Any]) -> Dict[str, Any]:
    semantic_errors = _semantic_preflight_errors(semantic)
    if semantic_errors:
        return _blocked("drawio", path, "invalid canonical semantic source", errors=semantic_errors)
    if not path.is_file():
        return _blocked("drawio", path, "missing file")
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as error:
        return _blocked("drawio", path, "draw.io XML parse failed", error=str(error))
    if _local_name(root.tag) != "mxGraphModel":
        return _blocked("drawio", path, "root must be an editable mxGraphModel")
    cells = root.findall(".//mxCell")
    cell_ids = [str(cell.get("id")) for cell in cells if cell.get("id")]
    duplicate_cell_ids = sorted(identifier for identifier, count in Counter(cell_ids).items() if count > 1)
    cell_map = {str(cell.get("id")): cell for cell in cells if cell.get("id")}
    vertices = [cell for cell in cells if cell.get("vertex") == "1"]
    edges = [cell for cell in cells if cell.get("edge") == "1"]
    picture_standin_cells = sorted(
        str(cell.get("id"))
        for cell in cells
        if re.search(
            r"(?:shape\s*=\s*image|image\s*=|data:image/|<\s*img\b|image/svg\+xml)",
            "%s %s" % (cell.get("style", ""), cell.get("value", "")),
            flags=re.IGNORECASE,
        )
    )

    expected_nodes = {
        str(item["id"])
        for collection in ("shapes", "text_objects", "equation_objects")
        for item in semantic.get(collection, [])
    }
    vertex_ids = {str(cell.get("id")) for cell in vertices if cell.get("id")}
    missing_node_ids = sorted(expected_nodes - vertex_ids)
    unexpected_node_ids = sorted(vertex_ids - expected_nodes)
    node_mismatches: Dict[str, List[str]] = {}
    paint_mismatches: Dict[str, List[str]] = {}
    style_tokens = semantic.get("style_tokens", {})
    colors_value = style_tokens.get("colors", {}) if isinstance(style_tokens, Mapping) else {}
    colors = colors_value if isinstance(colors_value, Mapping) else {}
    expected_stroke_width = _finite_float(
        style_tokens.get("stroke_width", 2.2) if isinstance(style_tokens, Mapping) else 2.2
    )

    def style_values(cell: ET.Element | None) -> Dict[str, str]:
        style = str(cell.get("style", "")) if cell is not None else ""
        return {
            key.strip(): value.strip()
            for chunk in style.split(";") if "=" in chunk
            for key, value in [chunk.split("=", 1)]
        }

    def normalized_drawio_color(value: str | None) -> str:
        raw = str(value or "").strip()
        if raw.lower() == "none":
            return "none"
        return raw.upper() if re.fullmatch(r"#[0-9A-Fa-f]{6}", raw) else ""

    def geometry_matches(cell: ET.Element | None, expected: tuple[float, float, float, float]) -> bool:
        geometry = cell.find("mxGeometry") if cell is not None else None
        return geometry is not None and all(
            _numbers_match(geometry.get(name), value)
            for name, value in zip(("x", "y", "width", "height"), expected)
        )

    for item in semantic.get("shapes", []):
        identifier = str(item["id"])
        cell = cell_map.get(identifier)
        problems: List[str] = []
        try:
            kind = str(item.get("type", "rect"))
            if kind == "rect":
                expected_geometry = (
                    _finite_float(item["x"]), _finite_float(item["y"]),
                    _finite_float(item["width"]), _finite_float(item["height"]),
                )
            elif kind == "ellipse":
                expected_geometry = (
                    _finite_float(item["cx"]) - _finite_float(item["rx"]),
                    _finite_float(item["cy"]) - _finite_float(item["ry"]),
                    _finite_float(item["rx"]) * 2, _finite_float(item["ry"]) * 2,
                )
            else:
                expected_geometry = (0.0, 0.0, 0.0, 0.0)
                problems.append("native shape type is not supported by the draw.io adapter")
        except (KeyError, TypeError, ValueError, OverflowError):
            expected_geometry = (0.0, 0.0, 0.0, 0.0)
            problems.append("invalid canonical geometry")
            kind = str(item.get("type", ""))
        style = str(cell.get("style", "")) if cell is not None else ""
        parsed_style = style_values(cell)
        if cell is None or cell.get("vertex") != "1":
            problems.append("missing independent native vertex")
        elif not geometry_matches(cell, expected_geometry):
            problems.append("geometry mismatch")
        if kind == "ellipse" and "ellipse;" not in style:
            problems.append("native shape type mismatch")
        if kind == "rect" and re.search(r"(?:^|;)(?:ellipse|shape\s*=\s*(?:image|trapezoid))(?:;|$)", style):
            problems.append("native shape type mismatch")
        if problems:
            node_mismatches[identifier] = problems
        expected_fill = resolve_hex_paint(
            item.get("fill"), colors, str(colors.get("surface", "#F2F4F6")),
        )
        expected_stroke = resolve_hex_paint(
            item.get("stroke"), colors, str(colors.get("ink", "#20252B")),
        )
        paint_problems: List[str] = []
        if normalized_drawio_color(parsed_style.get("fillColor")) != expected_fill:
            paint_problems.append("fillColor mismatch")
        if normalized_drawio_color(parsed_style.get("strokeColor")) != expected_stroke:
            paint_problems.append("strokeColor mismatch")
        expected_width = _finite_float(item.get("stroke_width", expected_stroke_width))
        if not _numbers_match(parsed_style.get("strokeWidth"), expected_width):
            paint_problems.append("strokeWidth mismatch")
        if paint_problems:
            paint_mismatches[identifier] = paint_problems
    for item in semantic.get("text_objects", []):
        cell = cell_map.get(str(item["id"]))
        expected = _normalized_text(str(item.get("text") or "\n".join(item.get("lines", []))))
        actual = _normalized_text(html.unescape(re.sub(r"<[^>]+>", " ", cell.get("value", "")))) if cell is not None else ""
        try:
            expected_geometry = (
                _finite_float(item.get("x")) - 70, _finite_float(item.get("y")) - 24, 140, 34,
            )
        except (TypeError, ValueError, OverflowError):
            expected_geometry = (0.0, 0.0, 0.0, 0.0)
        if cell is None or cell.get("semanticType") != "text" or actual != expected or not geometry_matches(cell, expected_geometry):
            node_mismatches[str(item["id"])] = ["live text or geometry mismatch"]
        parsed_style = style_values(cell)
        expected_color = resolve_hex_paint(
            item.get("fill") or item.get("fill_token", "ink"), colors, str(colors.get("ink", "#20252B")),
        )
        text_paint_problems: List[str] = []
        if normalized_drawio_color(parsed_style.get("fontColor")) != expected_color:
            text_paint_problems.append("fontColor mismatch")
        if not _numbers_match(parsed_style.get("fontSize"), item.get("font_size", 18)):
            text_paint_problems.append("fontSize mismatch")
        if text_paint_problems:
            paint_mismatches[str(item["id"])] = text_paint_problems
    for item in semantic.get("equation_objects", []):
        cell = cell_map.get(str(item["id"]))
        actual = (cell.get("equationId"), cell.get("latexSource")) if cell is not None else None
        expected = (str(item.get("equation_id", "")), str(item.get("latex_source", "")))
        try:
            width = _finite_float(item.get("width", 360))
            height = _finite_float(item.get("height", 36))
            left = _finite_float(item.get("x")) - width / 2 if item.get("text_anchor") == "middle" else _finite_float(item.get("x"))
            expected_geometry = (left, _finite_float(item.get("y")) - height, width, height)
        except (TypeError, ValueError, OverflowError):
            expected_geometry = (0.0, 0.0, 0.0, 0.0)
        visible = _normalized_text(html.unescape(re.sub(r"<[^>]+>", " ", cell.get("value", "")))) if cell is not None else ""
        expected_visible = _normalized_text(str(item.get("fallback_text", item.get("equation_id", ""))))
        if cell is None or cell.get("semanticType") != "equation" or actual != expected or not geometry_matches(cell, expected_geometry) or visible != expected_visible:
            node_mismatches[str(item["id"])] = ["equation source, visible fallback, or geometry mismatch"]
        parsed_style = style_values(cell)
        equation_paint_problems: List[str] = []
        expected_color = resolve_hex_paint("ink", colors, "#20252B")
        if normalized_drawio_color(parsed_style.get("fontColor")) != expected_color:
            equation_paint_problems.append("fontColor mismatch")
        if not _numbers_match(parsed_style.get("fontSize"), item.get("font_size", 18)):
            equation_paint_problems.append("fontSize mismatch")
        if equation_paint_problems:
            paint_mismatches[str(item["id"])] = equation_paint_problems

    expected_edges = {str(item["id"]): item for item in semantic.get("connectors", [])}
    edge_ids = {str(edge.get("id")) for edge in edges if edge.get("id")}
    missing_edge_ids = sorted(set(expected_edges) - edge_ids)
    unexpected_edge_ids = sorted(edge_ids - set(expected_edges))
    edge_mismatches: Dict[str, List[str]] = {}
    for identifier, item in expected_edges.items():
        edge = cell_map.get(identifier)
        actual = (
            edge.get("source"), edge.get("target"), edge.get("relationType")
        ) if edge is not None and edge.get("edge") == "1" else None
        expected = (
            str(item.get("source_id", "")), str(item.get("target_id", "")),
            str(item.get("relation_type", "relation")),
        )
        geometry = edge.find("mxGeometry") if edge is not None else None
        style = str(edge.get("style", "")) if edge is not None else ""
        expected_arrow = str(item.get("arrow", "end")) in {"end", "forward"}
        arrow_ok = ("endArrow=block;" in style) if expected_arrow else ("endArrow=block;" not in style)
        actual_points = []
        if geometry is not None:
            array = geometry.find("Array[@as='points']")
            if array is not None:
                actual_points = [[point.get("x"), point.get("y")] for point in array.findall("mxPoint")]
        expected_points = item.get("points", [])[1:-1]
        points_ok = _point_lists_match(actual_points, expected_points)
        if actual != expected or geometry is None or geometry.get("relative") != "1" or not arrow_ok or not points_ok:
            edge_mismatches[identifier] = [
                "edge=%r expected=%r arrow_ok=%s points_ok=%s" % (actual, expected, arrow_ok, points_ok)
            ]
        parsed_style = style_values(edge)
        edge_paint_problems: List[str] = []
        color_token = item.get("stroke_token", item.get("color_token", "ink"))
        expected_color = resolve_hex_paint(color_token, colors, str(colors.get("ink", "#20252B")))
        if normalized_drawio_color(parsed_style.get("strokeColor")) != expected_color:
            edge_paint_problems.append("strokeColor mismatch")
        if not _numbers_match(parsed_style.get("strokeWidth"), expected_stroke_width):
            edge_paint_problems.append("strokeWidth mismatch")
        if edge_paint_problems:
            paint_mismatches[identifier] = edge_paint_problems

    unsupported_ports = [str(item.get("id", "")) for item in semantic.get("ports", [])]

    passed = not any((
        picture_standin_cells,
        duplicate_cell_ids,
        missing_node_ids,
        unexpected_node_ids,
        node_mismatches,
        missing_edge_ids,
        unexpected_edge_ids,
        edge_mismatches,
        paint_mismatches,
        unsupported_ports,
    ))
    return {
        "format": "drawio", "status": "VERIFIED" if passed else "BLOCKED", "path": str(path.resolve()),
        "sha256": sha256_file(path), "native_mxcell_count": len(cells), "native_vertex_count": len(vertices),
        "native_edge_count": len(edges),
        "picture_standin_cells": picture_standin_cells, "missing_node_ids": missing_node_ids,
        "duplicate_cell_ids": duplicate_cell_ids, "unexpected_node_ids": unexpected_node_ids,
        "node_mismatches": node_mismatches,
        "paint_mismatches": paint_mismatches,
        "missing_edge_ids": missing_edge_ids, "unexpected_edge_ids": unexpected_edge_ids,
        "edge_mismatches": edge_mismatches, "endpoint_integrity": not edge_mismatches,
        "semantic_editability": passed,
        "equation_source_editability": passed and bool(semantic.get("equation_objects")),
        "unsupported_port_ids": unsupported_ports,
        "port_preservation": "BLOCKED_UNSUPPORTED" if unsupported_ports else "NOT_APPLICABLE",
        "scientific_validation": False,
    }


def _pdf_object(value: Any) -> Any:
    getter = getattr(value, "get_object", None)
    return getter() if callable(getter) else value


def _pdf_image_count(resources: Any, seen: set[int] | None = None) -> int:
    resources = _pdf_object(resources)
    if resources is None:
        return 0
    seen = seen or set()
    if id(resources) in seen:
        return 0
    seen.add(id(resources))
    try:
        xobjects = _pdf_object(resources.get("/XObject")) or {}
    except (AttributeError, TypeError):
        return 0
    count = 0
    for value in xobjects.values():
        item = _pdf_object(value)
        subtype = str(item.get("/Subtype", "")) if hasattr(item, "get") else ""
        if subtype == "/Image":
            count += 1
        elif subtype == "/Form":
            count += _pdf_image_count(item.get("/Resources"), seen)
    return count


def _expected_pdf_size(semantic: Mapping[str, Any]) -> tuple[float, float]:
    canvas = semantic["canvas"]
    if canvas.get("physical_width_mm") is not None:
        width = float(canvas["physical_width_mm"]) * 72.0 / 25.4
    else:
        width = float(canvas["width"])
    height = width * float(canvas["height"]) / float(canvas["width"])
    return width, height


def check_pdf(path: Path, profile: str, semantic: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    if semantic is None:
        return _blocked(profile, path, "canonical semantic source is required for PDF validation")
    semantic_errors = _semantic_preflight_errors(semantic)
    if semantic_errors:
        return _blocked(profile, path, "invalid canonical semantic source", errors=semantic_errors)
    if not path.is_file():
        return _blocked(profile, path, "missing file")
    try:
        from pypdf import PdfReader
        from pypdf.generic import ContentStream
    except ImportError:
        return _blocked(
            profile,
            path,
            "pypdf is required for structural PDF validation; install the declared full-delivery dependencies",
            dependency="pypdf",
        )
    try:
        reader = PdfReader(str(path), strict=True)
        if reader.is_encrypted:
            return _blocked(profile, path, "encrypted PDF cannot be structurally validated")
        pages = list(reader.pages)
    except Exception as error:
        return _blocked(profile, path, "pypdf parse failed", error=str(error))
    if len(pages) != 1:
        return _blocked(profile, path, "PDF must contain exactly one page", page_count=len(pages))

    expected_width, expected_height = _expected_pdf_size(semantic)
    page = pages[0]
    try:
        width, height = float(page.mediabox.width), float(page.mediabox.height)
        extracted_text = page.extract_text() or ""
        page_content = page.get_contents()
        content = page_content.get_data() if page_content is not None else b""
        content_operations = ContentStream(page_content, reader).operations if page_content is not None else []
        embedded_image_count = _pdf_image_count(page.get("/Resources"))
    except Exception as error:
        return _blocked(profile, path, "PDF page inspection failed", error=str(error))
    geometry_ok = abs(width - expected_width) <= 1.0 and abs(height - expected_height) <= 1.0

    vector_path = bool(re.search(rb"(?:^|\s)(?:m|l|c|v|y|re)(?:\s|$)", content))
    vector_paint = bool(re.search(rb"(?:^|\s)(?:S|s|f|F|f\*|B|B\*|b|b\*)(?:\s|$)", content))
    vector_evidence = vector_path and vector_paint
    text_operators = bool(re.search(rb"(?:^|\s)(?:Tj|TJ)(?:\s|$)", content))
    text_evidence = bool(_normalized_text(extracted_text)) and text_operators
    normalized_extracted = _normalized_text(extracted_text)
    required_text_labels = [
        _normalized_text(str(item.get("text") or "\n".join(item.get("lines", []))))
        for item in semantic.get("text_objects", [])
    ]
    missing_text_labels = sorted(
        label for label in required_text_labels if label and label not in normalized_extracted
    )
    compact_extracted = "".join(unicodedata.normalize("NFC", extracted_text).split())
    required_equation_labels = [
        "".join(
            unicodedata.normalize(
                "NFC", str(item.get("fallback_text", item.get("equation_id", ""))),
            ).split()
        )
        for item in semantic.get("equation_objects", [])
    ]
    missing_equation_labels = sorted(
        label for label in required_equation_labels if label and label not in compact_extracted
    )

    actual_fill_colors = [
        tuple(float(value) for value in operands)
        for operands, operator in content_operations
        if operator == b"rg" and len(operands) == 3
    ]
    actual_stroke_colors = [
        tuple(float(value) for value in operands)
        for operands, operator in content_operations
        if operator == b"RG" and len(operands) == 3
    ]
    style_tokens = semantic.get("style_tokens", {})
    colors_value = style_tokens.get("colors", {}) if isinstance(style_tokens, Mapping) else {}
    colors = colors_value if isinstance(colors_value, Mapping) else {}

    def expected_rgb(paint: str) -> tuple[float, float, float]:
        values = tuple(int(paint[index:index + 2], 16) / 255.0 for index in (1, 3, 5))
        if profile == "grayscale-pdf":
            gray = 0.299 * values[0] + 0.587 * values[1] + 0.114 * values[2]
            return (gray, gray, gray)
        return values

    def color_is_present(expected: tuple[float, float, float], actual: List[tuple[float, ...]]) -> bool:
        return any(
            len(found) == 3 and all(abs(left - right) <= 0.00001 for left, right in zip(found, expected))
            for found in actual
        )

    expected_shape_fills = {
        resolve_hex_paint(item.get("fill"), colors, str(colors.get("surface", "#F2F4F6")))
        for item in semantic.get("shapes", [])
        if str(item.get("type")) != "line"
    }
    expected_shape_strokes = {
        resolve_hex_paint(item.get("stroke"), colors, str(colors.get("ink", "#20252B")))
        for item in semantic.get("shapes", [])
    }
    missing_fill_colors = sorted(
        paint for paint in expected_shape_fills
        if paint != "none" and not color_is_present(expected_rgb(paint), actual_fill_colors)
    )
    missing_stroke_colors = sorted(
        paint for paint in expected_shape_strokes
        if paint != "none" and not color_is_present(expected_rgb(paint), actual_stroke_colors)
    )
    raster_only = embedded_image_count > 0 and not vector_evidence and not text_evidence
    vector_only = bool(semantic.get("platform_overrides", {}).get("pdf", {}).get("vector_only", True))
    passed = not any((
        not geometry_ok,
        not vector_evidence,
        not text_evidence,
        missing_text_labels,
        missing_equation_labels,
        missing_fill_colors,
        missing_stroke_colors,
        raster_only,
        vector_only and embedded_image_count,
    ))
    return {
        "format": profile, "status": "VERIFIED" if passed else "BLOCKED",
        "path": str(path.resolve()), "sha256": sha256_file(path), "parser": "pypdf",
        "page_count": 1, "page_geometry_points": [[width, height]],
        "expected_page_geometry_points": [expected_width, expected_height], "geometry_ok": geometry_ok,
        "embedded_image_count": embedded_image_count, "vector_evidence": vector_evidence,
        "text_evidence": text_evidence, "missing_text_labels": missing_text_labels,
        "missing_equation_labels": missing_equation_labels,
        "missing_shape_fill_colors": missing_fill_colors,
        "missing_shape_stroke_colors": missing_stroke_colors,
        "paint_validation_scope": "required semantic shape colors present in vector PDF operators",
        "raster_only": raster_only, "semantic_editability": False,
        "equation_source_editability": False, "scientific_validation": False,
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
        if not source.is_file():
            continue
        target = preview_dir / (label.lower().replace("-", "_").replace(".", "") + ".png")
        result = render_svg_to_png(source, target, int(semantic["canvas"]["width"]), int(semantic["canvas"]["height"]))
        if result.get("status") == "VERIFIED" and target.is_file():
            rendered.append((target, label))
    pptx_preview = run_dir / "delivery" / "pptx" / "slide-01.png"
    if pptx_preview.is_file():
        rendered.append((pptx_preview, "PPTX"))
    required_panels = ["SVG", "Figma-ready", "draw.io", "PPTX"]
    rendered_labels = [label for _, label in rendered]
    missing_panels = [label for label in required_panels if label not in rendered_labels]
    if missing_panels:
        return {
            "status": "BLOCKED",
            "reason": "cross-format preview requires all four independently rendered panels",
            "panels": rendered_labels,
            "missing_panels": missing_panels,
        }
    output = run_dir / "validation" / "cross_format_preview.png"
    try:
        from PIL import Image, ImageDraw
        thumb_width, thumb_height = 600, 360
        canvas = Image.new("RGB", (thumb_width * 2, (thumb_height + 44) * 2), "white")
        draw = ImageDraw.Draw(canvas)
        for index, (path, label) in enumerate(rendered):
            with Image.open(path) as source_image:
                source_image.verify()
            with Image.open(path) as source_image:
                image = source_image.convert("RGB")
            image.thumbnail((thumb_width - 20, thumb_height - 20))
            x = (index % 2) * thumb_width + (thumb_width - image.width) // 2
            y = (index // 2) * (thumb_height + 44) + 36 + (thumb_height - image.height) // 2
            canvas.paste(image, (x, y))
            draw.text(((index % 2) * thumb_width + 16, (index // 2) * (thumb_height + 44) + 10), label, fill="#172033")
        canvas.save(output)
        return {
            "status": "VERIFIED", "path": str(output.resolve()), "sha256": sha256_file(output),
            "panels": rendered_labels, "missing_panels": [],
        }
    except Exception as error:
        return {"status": "BLOCKED", "reason": "preview composition failed: %s" % error,
                "panels": rendered_labels, "missing_panels": []}


def validate(run_dir: Path) -> Dict[str, Any]:
    semantic_path = run_dir / "source" / "semantic_figure.json"
    equation_source_path = run_dir / "source" / "equations.tex"
    validation_dir = run_dir / "validation"
    try:
        loaded_semantic = load_json(semantic_path)
        semantic_errors = _semantic_preflight_errors(loaded_semantic)
        semantic = loaded_semantic if isinstance(loaded_semantic, Mapping) else {}
        if not semantic_errors:
            semantic_errors.extend(_equation_source_errors(equation_source_path, semantic))
    except Exception as error:
        semantic = {}
        semantic_errors = ["canonical semantic source could not be inspected: %s" % error]
    if semantic_errors:
        semantic_check: Dict[str, Any] = {
            "format": "semantic-source", "status": "BLOCKED", "errors": semantic_errors,
            "path": str(semantic_path.resolve()), "semantic_editability": False,
            "equation_source_editability": False, "scientific_validation": False,
            "equation_source_path": str(equation_source_path.resolve()),
        }
        if semantic_path.is_file():
            semantic_check["sha256"] = sha256_file(semantic_path)
        if equation_source_path.is_file():
            semantic_check["equation_source_sha256"] = sha256_file(equation_source_path)
        report = {
            "schema_version": "1.0", "figure_id": str(semantic.get("figure_id", "invalid-semantic-source")),
            "status": "BLOCKED", "canonical_source": str(semantic_path.resolve()),
            "canonical_equation_source": str(equation_source_path.resolve()),
            "checks": [semantic_check],
            "preview": {"status": "BLOCKED", "reason": "delivery adapters were not inspected because the canonical source is invalid"},
            "validation_scope": "Programmable structure only; not scientific correctness or Gate 3 approval.",
            "editability_claims": {"semantic-source": {
                "status": "BLOCKED", "semantic_editability": False,
                "equation_source_editability": False, "scientific_validation": False,
            }},
        }
        write_json(validation_dir / "cross_format_report.json", report)
        return report

    checks = [
        {
            "format": "semantic-source", "status": "VERIFIED", "errors": [],
            "path": str(semantic_path.resolve()), "sha256": sha256_file(semantic_path),
            "equation_source_path": str(equation_source_path.resolve()),
            "equation_source_sha256": sha256_file(equation_source_path),
            "semantic_editability": True,
            "equation_source_editability": bool(semantic.get("equation_objects")),
            "scientific_validation": False,
        },
        check_svg(run_dir / "delivery" / "svg" / "master.svg", semantic, "svg"),
        check_svg(run_dir / "delivery" / "figma" / "figure_figma.svg", semantic, "figma-ready-svg"),
        check_pptx(run_dir / "delivery" / "pptx" / "figure.pptx", semantic),
        check_drawio(run_dir / "delivery" / "drawio" / "figure.drawio", semantic),
        check_pdf(run_dir / "delivery" / "pdf" / "publication.pdf", "publication-pdf", semantic),
        check_pdf(run_dir / "delivery" / "pdf" / "grayscale.pdf", "grayscale-pdf", semantic),
        check_pdf(run_dir / "delivery" / "drawio" / "figure_drawio_preview.pdf", "drawio-companion-pdf", semantic),
    ]
    preview = create_preview(run_dir, semantic)
    statuses = [item["status"] for item in checks]
    acceptable_statuses = {"VERIFIED", "IMPORT_READY_UNVERIFIED"}
    overall = "VERIFIED" if all(status in acceptable_statuses for status in statuses) and preview["status"] == "VERIFIED" else "BLOCKED"
    report = {
        "schema_version": "1.0", "figure_id": semantic["figure_id"], "status": overall,
        "canonical_source": str(semantic_path.resolve()),
        "canonical_equation_source": str(equation_source_path.resolve()),
        "checks": checks, "preview": preview,
        "validation_scope": "Programmable structure only; not scientific correctness or Gate 3 approval.",
        "cross_format_invariants": {
            "coordinate_system": "All adapters consume the same semantic pixel coordinate system; PPTX uses the identical slide size.",
            "expected_shape_count": len(semantic.get("shapes", [])), "expected_text_count": len(semantic.get("text_objects", [])),
            "expected_equation_count": len(semantic.get("equation_objects", [])), "expected_connector_count": len(semantic.get("connectors", [])),
            "bounding_box_policy": "SVG, Figma-ready SVG, draw.io, and PPTX receive unscaled canonical bounding boxes. PDF is printed from a direct semantic render.",
        },
        "editability_claims": {
            item["format"]: {
                "status": item["status"],
                "semantic_editability": item["status"] in acceptable_statuses and bool(item.get("semantic_editability", False)),
                "equation_source_editability": item["status"] in acceptable_statuses and bool(item.get("equation_source_editability", False)),
                "scientific_validation": False,
            }
            for item in checks
        },
    }
    write_json(validation_dir / "cross_format_report.json", report)
    formats = []
    for item in checks[1:]:
        status = item["status"]
        formats.append({
            "format": item["format"], "path": item["path"], "status": status,
            "semantic_editability": status in acceptable_statuses and bool(item.get("semantic_editability", False)),
            "equation_source_editability": status in acceptable_statuses and bool(item.get("equation_source_editability", False)),
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
