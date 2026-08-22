#!/usr/bin/env python3
"""Render deterministic SVG/PNG topology skeletons from one blueprint scene."""

from __future__ import annotations

import argparse
import json
import math
import struct
import sys
import zlib
from html import escape
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple

from figure_artifacts import (
    load_json,
    node_ref_index,
    relation_endpoint_pairs,
    truth_instance_index,
    write_json,
)


WIDTH = 1600
HEIGHT = 900
MARGIN = 24

TYPE_CODES = {
    "measurement": "Y",
    "model": "F",
    "process": "F",
    "operator": "F",
    "estimate": "X",
    "output": "X",
    "input": "Y",
    "state": "X",
    "parameter": "T",
}

COLORS = {
    "background": "#FFFFFF",
    "ink": "#28323C",
    "structure": "#9BA8B4",
    "region": "#F4F7F9",
    "input": "#DCEAF7",
    "process": "#E7E2F3",
    "output": "#DCEFE7",
    "neutral": "#F2EEE3",
}


def pixel_bbox(normalized: Sequence[float]) -> List[float]:
    x, y, width, height = normalized
    return [
        MARGIN + x * (WIDTH - 2 * MARGIN),
        MARGIN + y * (HEIGHT - 2 * MARGIN),
        width * (WIDTH - 2 * MARGIN),
        height * (HEIGHT - 2 * MARGIN),
    ]


def centers_for_node(node: Mapping[str, Any], count: int) -> List[Tuple[float, float]]:
    x, y, width, height = pixel_bbox(node["bbox"])
    if count <= 0:
        return []
    layout = node.get("layout", "horizontal")
    if layout == "vertical":
        return [(x + width / 2, y + (index + 0.5) * height / count) for index in range(count)]
    if layout == "grid":
        columns = max(1, int(node.get("columns", math.ceil(math.sqrt(count)))))
        rows = int(math.ceil(count / columns))
        result = []
        for index in range(count):
            column = index % columns
            row = index // columns
            result.append(
                (
                    x + (column + 0.5) * width / columns,
                    y + (row + 0.5) * height / rows,
                )
            )
        return result
    return [(x + (index + 0.5) * width / count, y + height / 2) for index in range(count)]


def object_dimensions(instance: Mapping[str, Any], node: Mapping[str, Any], count: int) -> Tuple[float, float]:
    _, _, width, height = pixel_bbox(node["bbox"])
    layout = node.get("layout", "horizontal")
    instance_type = str(instance.get("type", "entity"))
    shape = str(instance.get("shape", ""))
    if shape in {"operator", "trapezoid"} or instance_type in {"model", "process", "operator"}:
        return min(width * 0.9, 150), min(height * 0.75, 70)
    if shape == "circle" or instance_type in {"measurement", "input", "parameter"}:
        diameter = min(24.0, max(14.0, min(width, height) / max(2, count)))
        return diameter, diameter
    if layout == "vertical":
        cell_width, cell_height = width, height / max(1, count)
    elif layout == "grid":
        columns = max(1, int(node.get("columns", math.ceil(math.sqrt(count)))))
        rows = int(math.ceil(count / columns))
        cell_width, cell_height = width / columns, height / rows
    else:
        cell_width, cell_height = width / max(1, count), height
    if shape == "square" or instance_type in {"state", "estimate", "output"}:
        side = min(54.0, cell_width * 0.62, cell_height * 0.72)
        return max(side, 22), max(side, 22)
    return max(20.0, cell_width * 0.5), max(18.0, cell_height * 0.5)


def make_object(
    instance: Mapping[str, Any],
    node: Mapping[str, Any],
    center: Tuple[float, float],
    count: int,
) -> Dict[str, Any]:
    width, height = object_dimensions(instance, node, count)
    return {
        "id": instance["id"],
        "node_id": node["id"],
        "type": instance["type"],
        "stage": instance.get("stage"),
        "status": instance.get("status"),
        "label": instance.get("label", TYPE_CODES.get(instance["type"], "?")),
        "short_label": TYPE_CODES.get(instance["type"], "?"),
        "shape": instance.get("shape", "auto"),
        "visual_role": instance.get("visual_role", "neutral"),
        "bbox": [center[0] - width / 2, center[1] - height / 2, width, height],
        "center": [center[0], center[1]],
        "source_node": node["id"],
    }


def build_scene(truth: Mapping[str, Any], blueprint: Mapping[str, Any]) -> Dict[str, Any]:
    instances = truth_instance_index(truth)
    relations = truth.get("relations", [])
    nodes = {node["id"]: node for node in blueprint.get("nodes", [])}
    objects: Dict[str, Dict[str, Any]] = {}

    for node in blueprint.get("nodes", []):
        refs = node.get("instance_refs", [])
        centers = centers_for_node(node, len(refs))
        for ref, center in zip(refs, centers):
            objects[ref] = make_object(instances[ref], node, center, len(refs))

    instance_to_node = node_ref_index(blueprint)
    connectors: List[Dict[str, Any]] = []
    relation_by_type: Dict[str, List[Mapping[str, Any]]] = {}
    for relation in relations:
        relation_by_type.setdefault(relation.get("type", ""), []).append(relation)

    for edge in blueprint.get("edges", []):
        source_node = edge["source"].rsplit(".", 1)[0]
        target_node = edge["target"].rsplit(".", 1)[0]
        for relation_type in edge.get("relation_types", []):
            for relation in relation_by_type.get(relation_type, []):
                for pair_index, (source, target) in enumerate(relation_endpoint_pairs(relation)):
                    if source not in objects or target not in objects:
                        continue
                    if instance_to_node.get(source) != source_node:
                        continue
                    if instance_to_node.get(target) != target_node:
                        continue
                    points = orthogonal_points(
                        objects[source], objects[target], edge.get("routing", "auto")
                    )
                    connector_id = relation["id"]
                    if len(relation_endpoint_pairs(relation)) > 1:
                        connector_id = "%s--%02d" % (relation["id"], pair_index + 1)
                    connectors.append(
                        {
                            "id": connector_id,
                            "edge_id": edge["id"],
                            "relation_id": relation["id"],
                            "relation_type": relation_type,
                            "source": source,
                            "target": target,
                            "points": points,
                            "arrow": edge.get("arrow", True),
                            "rule_ids": relation.get("rule_ids", []),
                        }
                    )

    return {
        "schema_version": "1.0",
        "candidate_id": blueprint["candidate_id"],
        "truth_figure_id": truth["figure_id"],
        "width": WIDTH,
        "height": HEIGHT,
        "regions": [
            {
                "id": region["id"],
                "label": region.get("label", region["id"]),
                "bbox": pixel_bbox(region["bbox"]),
            }
            for region in blueprint.get("regions", [])
        ],
        "objects": list(objects.values()),
        "connectors": connectors,
        "layout_fingerprint": blueprint["layout_fingerprint"],
    }


def edge_point(obj: Mapping[str, Any], toward: Mapping[str, Any]) -> Tuple[float, float]:
    x, y, width, height = obj["bbox"]
    cx, cy = obj["center"]
    tx, ty = toward["center"]
    dx, dy = tx - cx, ty - cy
    if abs(dx) > abs(dy):
        return (x + width if dx >= 0 else x, cy)
    return (cx, y + height if dy >= 0 else y)


def orthogonal_points(
    source: Mapping[str, Any], target: Mapping[str, Any], routing: str
) -> List[List[float]]:
    start = edge_point(source, target)
    end = edge_point(target, source)
    sx, sy = start
    ex, ey = end
    if routing == "horizontal" or (routing == "auto" and abs(ex - sx) >= abs(ey - sy)):
        middle_x = (sx + ex) / 2
        return [[sx, sy], [middle_x, sy], [middle_x, ey], [ex, ey]]
    middle_y = (sy + ey) / 2
    return [[sx, sy], [sx, middle_y], [ex, middle_y], [ex, ey]]


def svg_polygon_points(obj: Mapping[str, Any]) -> str:
    x, y, width, height = obj["bbox"]
    top_inset = width * 0.08
    bottom_inset = width * 0.22
    return "%.2f,%.2f %.2f,%.2f %.2f,%.2f %.2f,%.2f" % (
        x + top_inset,
        y,
        x + width - top_inset,
        y,
        x + width - bottom_inset,
        y + height,
        x + bottom_inset,
        y + height,
    )


def svg_object(obj: Mapping[str, Any]) -> str:
    x, y, width, height = obj["bbox"]
    cx, cy = obj["center"]
    common = (
        'id="%s" data-entity-type="%s" data-stage="%s"'
        % (escape(obj["id"]), escape(obj["type"]), escape(str(obj.get("stage") or "")))
    )
    if obj.get("placement_rule"):
        common += ' data-placement-rule="%s" data-members="%s"' % (
            obj["placement_rule"],
            " ".join(obj.get("members", [])),
        )
    shape_name = obj.get("shape", "auto")
    visual_role = str(obj.get("visual_role", "neutral"))
    fill = COLORS.get(visual_role, COLORS["neutral"])
    if shape_name == "circle" or obj["type"] in {"measurement", "input", "parameter"}:
        shape = '<circle %s cx="%.2f" cy="%.2f" r="%.2f" fill="%s" stroke="%s"/>' % (
            common,
            cx,
            cy,
            min(width, height) / 2,
            fill,
            COLORS["ink"],
        )
    elif shape_name in {"operator", "trapezoid"} or obj["type"] in {"model", "process", "operator"}:
        shape = '<polygon %s points="%s" fill="%s" stroke="%s" stroke-width="2"/>' % (
            common,
            svg_polygon_points(obj),
            fill,
            COLORS["ink"],
        )
    else:
        dash = ' stroke-dasharray="7 5"' if obj.get("status") == "temporary" else ""
        shape = (
            '<rect %s x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="5" '
            'fill="%s" stroke="%s" stroke-width="2"%s/>'
            % (common, x, y, width, height, fill, COLORS["ink"], dash)
        )
    label = escape(str(obj.get("short_label", "")))
    return shape + (
        '<text x="%.2f" y="%.2f" text-anchor="middle" dominant-baseline="middle" '
        'font-size="14" fill="%s">%s</text>'
        % (cx, cy, COLORS["ink"], label)
    )


def arrow_polygon(points: Sequence[Sequence[float]]) -> str:
    if len(points) < 2:
        return ""
    x2, y2 = points[-1]
    x1, y1 = points[-2]
    size = 8.0
    if abs(x2 - x1) >= abs(y2 - y1):
        sign = 1 if x2 >= x1 else -1
        values = [(x2, y2), (x2 - sign * size, y2 - size / 2), (x2 - sign * size, y2 + size / 2)]
    else:
        sign = 1 if y2 >= y1 else -1
        values = [(x2, y2), (x2 - size / 2, y2 - sign * size), (x2 + size / 2, y2 - sign * size)]
    return " ".join("%.2f,%.2f" % value for value in values)


def render_svg(scene: Mapping[str, Any]) -> str:
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
        % (WIDTH, HEIGHT, WIDTH, HEIGHT),
        '<rect id="canvas" x="0" y="0" width="%d" height="%d" fill="%s"/>'
        % (WIDTH, HEIGHT, COLORS["background"]),
        '<g id="regions" font-family="Arial, Helvetica, sans-serif">',
    ]
    for region in scene["regions"]:
        x, y, width, height = region["bbox"]
        parts.append(
            '<g id="region-%s"><rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" '
            'rx="10" fill="%s" stroke="%s" stroke-width="1.5"/>'
            '<text x="%.2f" y="%.2f" font-size="16" fill="%s">%s</text></g>'
            % (
                escape(region["id"]),
                x,
                y,
                width,
                height,
                COLORS["region"],
                COLORS["structure"],
                x + 10,
                y + 22,
                COLORS["ink"],
                escape(region["label"]),
            )
        )
    parts.append("</g><g id=\"connectors\" fill=\"none\" stroke-linecap=\"butt\">")
    for connector in scene["connectors"]:
        color = COLORS["ink"]
        points = " ".join("%.2f,%.2f" % tuple(point) for point in connector["points"])
        parts.append(
            '<polyline id="%s" data-role="connector" data-relation-type="%s" '
            'data-source="%s" data-target="%s" data-rule-ids="%s" points="%s" '
            'stroke="%s" stroke-width="2"/>'
            % (
                escape(connector["id"]),
                escape(connector["relation_type"]),
                escape(connector["source"]),
                escape(connector["target"]),
                escape(" ".join(connector.get("rule_ids", []))),
                points,
                color,
            )
        )
        if connector["arrow"]:
            parts.append(
                '<polygon id="arrow-%s" points="%s" fill="%s" stroke="none"/>'
                % (escape(connector["id"]), arrow_polygon(connector["points"]), color)
            )
    parts.append("</g><g id=\"objects\" font-family=\"Arial, Helvetica, sans-serif\">")
    parts.extend(svg_object(obj) for obj in scene["objects"])
    parts.append("</g></svg>")
    return "\n".join(parts) + "\n"


FONT = {
    "0": ("111", "101", "101", "101", "111"), "1": ("010", "110", "010", "010", "111"),
    "2": ("111", "001", "111", "100", "111"), "3": ("111", "001", "111", "001", "111"),
    "4": ("101", "101", "111", "001", "001"), "5": ("111", "100", "111", "001", "111"),
    "6": ("111", "100", "111", "101", "111"), "7": ("111", "001", "010", "010", "010"),
    "8": ("111", "101", "111", "101", "111"), "9": ("111", "101", "111", "001", "111"),
    "A": ("010", "101", "111", "101", "101"), "B": ("110", "101", "110", "101", "110"),
    "D": ("110", "101", "101", "101", "110"), "G": ("111", "100", "101", "101", "111"),
    "M": ("10001", "11011", "10101", "10101", "10101"), "S": ("111", "100", "111", "001", "111"),
    "U": ("101", "101", "101", "101", "111"), "V": ("101", "101", "101", "101", "010"),
    "X": ("101", "101", "010", "101", "101"), "Z": ("111", "001", "010", "100", "111"),
    "=": ("000", "111", "000", "111", "000"), "-": ("000", "000", "111", "000", "000"),
}


class Raster:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.pixels = bytearray([255] * width * height * 3)

    @staticmethod
    def color(hex_value: str) -> Tuple[int, int, int]:
        value = hex_value.lstrip("#")
        return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))  # type: ignore[return-value]

    def point(self, x: int, y: int, color: Tuple[int, int, int]) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            offset = (y * self.width + x) * 3
            self.pixels[offset : offset + 3] = bytes(color)

    def line(self, start: Sequence[float], end: Sequence[float], color: Tuple[int, int, int], width: int = 2) -> None:
        x0, y0 = int(round(start[0])), int(round(start[1]))
        x1, y1 = int(round(end[0])), int(round(end[1]))
        dx, sx = abs(x1 - x0), 1 if x0 < x1 else -1
        dy, sy = -abs(y1 - y0), 1 if y0 < y1 else -1
        error = dx + dy
        while True:
            for yy in range(y0 - width // 2, y0 + width // 2 + 1):
                for xx in range(x0 - width // 2, x0 + width // 2 + 1):
                    self.point(xx, yy, color)
            if x0 == x1 and y0 == y1:
                break
            twice = 2 * error
            if twice >= dy:
                error += dy
                x0 += sx
            if twice <= dx:
                error += dx
                y0 += sy

    def rect(self, bbox: Sequence[float], color: Tuple[int, int, int], dashed: bool = False) -> None:
        x, y, width, height = [int(round(value)) for value in bbox]
        segments = [((x, y), (x + width, y)), ((x + width, y), (x + width, y + height)), ((x + width, y + height), (x, y + height)), ((x, y + height), (x, y))]
        for start, end in segments:
            if not dashed:
                self.line(start, end, color)
                continue
            length = max(abs(end[0] - start[0]), abs(end[1] - start[1]))
            for offset in range(0, length + 1, 12):
                fraction_start = offset / max(1, length)
                fraction_end = min(offset + 7, length) / max(1, length)
                a = (start[0] + (end[0] - start[0]) * fraction_start, start[1] + (end[1] - start[1]) * fraction_start)
                b = (start[0] + (end[0] - start[0]) * fraction_end, start[1] + (end[1] - start[1]) * fraction_end)
                self.line(a, b, color)

    def circle(self, center: Sequence[float], radius: float, color: Tuple[int, int, int]) -> None:
        steps = max(24, int(radius * 5))
        points = [
            (
                center[0] + radius * math.cos(2 * math.pi * index / steps),
                center[1] + radius * math.sin(2 * math.pi * index / steps),
            )
            for index in range(steps + 1)
        ]
        for left, right in zip(points, points[1:]):
            self.line(left, right, color)

    def polygon(self, points: Sequence[Sequence[float]], color: Tuple[int, int, int]) -> None:
        for left, right in zip(points, list(points[1:]) + [points[0]]):
            self.line(left, right, color)

    def text(self, x: int, y: int, value: str, color: Tuple[int, int, int], scale: int = 3) -> None:
        cursor = x
        for character in value.upper():
            glyph = FONT.get(character)
            if glyph is None:
                cursor += 4 * scale
                continue
            glyph_width = len(glyph[0])
            for row, bits in enumerate(glyph):
                for column, bit in enumerate(bits):
                    if bit == "1":
                        for yy in range(scale):
                            for xx in range(scale):
                                self.point(cursor + column * scale + xx, y + row * scale + yy, color)
            cursor += (glyph_width + 1) * scale

    def save_png(self, path: Path) -> None:
        rows = bytearray()
        stride = self.width * 3
        for row in range(self.height):
            rows.append(0)
            start = row * stride
            rows.extend(self.pixels[start : start + stride])

        def chunk(kind: bytes, payload: bytes) -> bytes:
            return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)

        png = b"\x89PNG\r\n\x1a\n"
        png += chunk(b"IHDR", struct.pack(">IIBBBBB", self.width, self.height, 8, 2, 0, 0, 0))
        png += chunk(b"IDAT", zlib.compress(bytes(rows), 9))
        png += chunk(b"IEND", b"")
        path.write_bytes(png)


def render_png(scene: Mapping[str, Any], path: Path) -> None:
    raster = Raster(WIDTH, HEIGHT)
    ink = Raster.color(COLORS["ink"])
    structure = Raster.color(COLORS["structure"])
    for region in scene["regions"]:
        raster.rect(region["bbox"], structure)
        x, y, _, _ = region["bbox"]
        raster.text(int(x + 8), int(y + 8), region["label"], ink, 3)
    for connector in scene["connectors"]:
        color = ink
        for start, end in zip(connector["points"], connector["points"][1:]):
            raster.line(start, end, color, 2)
        if connector["arrow"]:
            polygon = [tuple(map(float, pair.split(","))) for pair in arrow_polygon(connector["points"]).split()]
            raster.polygon(polygon, color)
    for obj in scene["objects"]:
        shape_name = obj.get("shape", "auto")
        if shape_name == "circle" or obj["type"] in {"measurement", "input", "parameter"}:
            raster.circle(obj["center"], min(obj["bbox"][2], obj["bbox"][3]) / 2, ink)
        elif shape_name in {"operator", "trapezoid"} or obj["type"] in {"model", "process", "operator"}:
            x, y, width, height = obj["bbox"]
            raster.polygon(
                [
                    (x + width * 0.08, y),
                    (x + width * 0.92, y),
                    (x + width * 0.78, y + height),
                    (x + width * 0.22, y + height),
                ],
                ink,
            )
        else:
            raster.rect(obj["bbox"], ink, dashed=obj.get("status") == "temporary")
        label = obj.get("short_label", "")
        scale = 2
        approx_width = len(label) * 4 * scale
        raster.text(
            int(obj["center"][0] - approx_width / 2),
            int(obj["center"][1] - 5 * scale / 2),
            label,
            ink,
            scale,
        )
    raster.save_png(path)


def render(truth_path: Path, blueprint_path: Path, output_dir: Path) -> Dict[str, str]:
    truth = load_json(truth_path)
    blueprint = load_json(blueprint_path)
    scene = build_scene(truth, blueprint)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = blueprint["candidate_id"] + "_skeleton"
    scene_path = output_dir / (stem + ".scene.json")
    svg_path = output_dir / (stem + ".svg")
    png_path = output_dir / (stem + ".png")
    write_json(scene_path, scene)
    svg_path.write_text(render_svg(scene), encoding="utf-8")
    render_png(scene, png_path)
    return {"scene": str(scene_path), "svg": str(svg_path), "png": str(png_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--truth", required=True, type=Path)
    parser.add_argument("--blueprint", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        outputs = render(args.truth.resolve(), args.blueprint.resolve(), args.output_dir.resolve())
    except (OSError, ValueError, KeyError) as exc:
        print("RENDER FAIL: %s" % exc, file=sys.stderr)
        return 1
    print(json.dumps(outputs, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
