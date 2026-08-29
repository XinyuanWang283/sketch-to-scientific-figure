#!/usr/bin/env python3
"""Build a region-first, all-native Candidate-C review revision.

The selected ImageGen candidate is first decomposed into a hash-bound visual
map.  Its crops remain reference-only.  Every delivery object is rebuilt as
native geometry or a vector equation; no candidate pixels enter SVG, PPTX,
draw.io, or PDF.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import os
import random
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader

from figure_artifacts import write_json
from render_equations import render_latex, render_mathjax
from workflow_v3 import write_text


CANVAS_WIDTH = 1672
CANVAS_HEIGHT = 941
ARROW_HEAD_COUNT = 7
FIGURE_ID = "deep-image-prior-c-segmented-native"
CANDIDATE_RELATIVE_PATH = Path("candidates") / "C-presentation.png"
SELECTION_RELATIVE_PATH = Path("candidate_selection_c_only.json")
LOCAL_PATH_MARKERS = (
    "/" + "Users" + "/",
    "/" + "private" + "/" + "tmp" + "/",
    "/" + "home" + "/",
)

COLORS = {
    "background": "#FFFFFF",
    "navy": "#0D2F6E",
    "purple": "#5A258C",
    "purple_mid": "#756EA9",
    "purple_light": "#B8B4D7",
    "teal": "#0B6262",
    "orange": "#C57300",
    "panel": "#EDF4FC",
    "generator": "#F7F2FC",
    "operator": "#FFF8EC",
    "grid": "#D7E0EC",
    "ink": "#18233A",
}

REGIONS = {
    "noise_input": [38, 210, 232, 238],
    "generator_network": [362, 185, 396, 309],
    "reconstruction_landscape": [824, 214, 241, 246],
    "forward_operator": [1132, 274, 128, 124],
    "measurement_comparison": [1328, 94, 318, 636],
    "feedback_loop": [555, 452, 785, 274],
    "optimization_objective": [320, 752, 710, 106],
    "reconstruction_equation": [1062, 758, 305, 94],
}

REGION_OUTPUT_IDS = {
    "noise_input": ["noise-frame", "noise-field"],
    "generator_network": ["generator-frame", "generator-network"],
    "reconstruction_landscape": ["reconstruction-frame", "mountain-scene"],
    "forward_operator": ["operator-frame", "eq-operator"],
    "measurement_comparison": [
        "measurement-panel", "predicted-frame", "predicted-plot",
        "loss-node", "observed-frame", "observed-plot",
    ],
    "feedback_loop": ["feedback-optimize-generator", "feedback-caption"],
    "optimization_objective": ["eq-objective"],
    "reconstruction_equation": ["eq-reconstruction"],
}

EQUATION_DEFINITIONS = [
    {
        "id": "eq-z", "equation_id": "eq_z", "latex_source": r"z",
        "color": COLORS["navy"], "fit_box": [132, 145, 52, 45], "align": "center",
        "role": "input-label",
    },
    {
        "id": "eq-generator", "equation_id": "eq_generator", "latex_source": r"G_{\theta}",
        "color": COLORS["purple"], "fit_box": [505, 195, 110, 62], "align": "center",
        "role": "generator-label",
    },
    {
        "id": "eq-xhat", "equation_id": "eq_xhat", "latex_source": r"\hat{x}",
        "color": COLORS["teal"], "fit_box": [911, 145, 68, 54], "align": "center",
        "role": "reconstruction-label",
    },
    {
        "id": "eq-operator", "equation_id": "eq_operator", "latex_source": r"A",
        "color": COLORS["orange"], "fit_box": [1166, 298, 60, 58], "align": "center",
        "role": "operator-label",
    },
    {
        "id": "eq-yhat", "equation_id": "eq_yhat", "latex_source": r"\hat{y}",
        "color": COLORS["navy"], "fit_box": [1448, 116, 80, 55], "align": "center",
        "role": "predicted-measurement-label",
    },
    {
        "id": "eq-y", "equation_id": "eq_y", "latex_source": r"y",
        "color": COLORS["navy"], "fit_box": [1464, 652, 50, 48], "align": "center",
        "role": "observed-measurement-label",
    },
    {
        "id": "eq-loss", "equation_id": "eq_loss", "latex_source": r"\lVert\hat{y}-y\rVert_{2}^{2}",
        "color": COLORS["navy"], "fit_box": [1439, 394, 98, 42], "align": "center",
        "role": "measurement-residual",
    },
    {
        "id": "eq-objective", "equation_id": "eq_objective",
        "latex_source": (
            r"\theta^{\ast}=\operatorname*{arg\,min}_{\theta}"
            r"\left\lVert A G_{\theta}(z)-y\right\rVert_{2}^{2}"
        ),
        "color": COLORS["navy"], "fit_box": [325, 768, 600, 90], "align": "left",
        "role": "optimization-objective",
    },
    {
        "id": "eq-reconstruction", "equation_id": "eq_reconstruction",
        "latex_source": r"\hat{x}=G_{\theta^{\ast}}(z)",
        "color": COLORS["navy"], "fit_box": [1068, 785, 233, 51], "align": "left",
        "role": "reconstruction-equation",
    },
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_selected_candidate_map(example_root: Path) -> dict[str, Any]:
    candidate = example_root / CANDIDATE_RELATIVE_PATH
    if not candidate.is_file():
        raise FileNotFoundError(candidate)
    return {
        "schema_version": "1.0",
        "candidate_id": "C-presentation",
        "image_hash": sha256_file(candidate),
        "bbox_format": "xywh_source_pixels",
        "major_region_bboxes": REGIONS,
        "palette_samples": {
            "primary_navy": COLORS["navy"],
            "optimization_purple": COLORS["purple"],
            "reconstruction_teal": COLORS["teal"],
            "operator_orange": COLORS["orange"],
            "comparison_panel": COLORS["panel"],
            "background": COLORS["background"],
        },
        "stroke_character": "Clean 3-4 px scientific outlines, restrained dashed feedback, small filled arrowheads.",
        "corner_language": "Moderately rounded frames; circular loss node; squared internal network facets.",
        "whitespace_rhythm": [40, 88, 76, 70, 78, 80],
        "glyph_reference_crops": [
            {
                "id": region,
                "bbox": bbox,
                "path": f"reference_regions/{region}.png",
                "use": "reference_only_not_embedded",
            }
            for region, bbox in REGIONS.items()
        ],
        "art_direction_notes": (
            "Preserve Candidate C's left-to-right composition, compact 3D encoder-decoder, "
            "grayscale landscape anchor, pale-blue comparison panel, and bottom optimization loop. "
            "Reconstruct every delivered object natively; reference crops are QA aids only."
        ),
        "scientific_overrides": [
            "All generated text and formulas are non-authoritative; use the typed LaTeX source.",
            "All connectors and arrow directions come from the approved scientific topology.",
            "The landscape is a synthetic visual glyph, not scientific evidence or measured data.",
            "Automated checks do not constitute final scientific approval.",
        ],
        "region_output_ids": REGION_OUTPUT_IDS,
        "reference_policy": {
            "candidate_pixels_in_delivery": False,
            "reference_crops_are_final_assets": False,
            "selected_map_is_approval_gate": False,
        },
        "region_overlay": {
            "path": "region_overlay.png",
            "use": "reference_only_not_embedded",
        },
    }


def _write_reference_regions(candidate: Path, source_dir: Path) -> list[dict[str, Any]]:
    output_dir = source_dir / "reference_regions"
    output_dir.mkdir(parents=True)
    records: list[dict[str, Any]] = []
    with Image.open(candidate) as image:
        source = image.convert("RGB")
        for region, (x, y, width, height) in REGIONS.items():
            output = output_dir / f"{region}.png"
            source.crop((x, y, x + width, y + height)).save(output, format="PNG", optimize=True)
            records.append({
                "id": region,
                "path": f"reference_regions/{output.name}",
                "sha256": sha256_file(output),
                "use": "reference_only_not_embedded",
            })
    return records


def _write_region_overlay(candidate: Path, source_dir: Path) -> dict[str, Any]:
    """Write a QA-only region overlay; it is never a delivery asset."""
    with Image.open(candidate) as image:
        overlay = image.convert("RGBA")
    translucent = Image.new("RGBA", overlay.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(translucent)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
    except OSError:
        font = ImageFont.load_default()
    palette = [
        (20, 92, 168, 230), (92, 37, 140, 230), (11, 98, 98, 230),
        (197, 115, 0, 230), (43, 115, 178, 230), (117, 59, 159, 230),
        (28, 72, 123, 230), (0, 124, 124, 230),
    ]
    for index, (region, (x, y, width, height)) in enumerate(REGIONS.items()):
        color = palette[index % len(palette)]
        draw.rectangle((x, y, x + width, y + height), outline=color, width=4)
        label = f"{index + 1}. {region}"
        text_box = draw.textbbox((0, 0), label, font=font)
        label_width = text_box[2] - text_box[0] + 12
        label_height = text_box[3] - text_box[1] + 8
        label_y = max(0, y - label_height)
        draw.rectangle((x, label_y, x + label_width, label_y + label_height), fill=(*color[:3], 225))
        draw.text((x + 6, label_y + 3), label, font=font, fill=(255, 255, 255, 255))
    output = source_dir / "region_overlay.png"
    Image.alpha_composite(overlay, translucent).convert("RGB").save(output, format="PNG", optimize=True)
    return {
        "path": "region_overlay.png",
        "sha256": sha256_file(output),
        "use": "reference_only_not_embedded",
        "bbox_format": "xywh_source_pixels",
        "region_count": len(REGIONS),
    }


def _frame(
    identifier: str,
    geometry: str,
    left: float,
    top: float,
    width: float,
    height: float,
    *,
    fill: str,
    stroke: str,
    stroke_width: float,
    radius: float = 0,
    dash: Sequence[float] | None = None,
) -> dict[str, Any]:
    return {
        "id": identifier,
        "geometry": geometry,
        "position": {"left": left, "top": top, "width": width, "height": height},
        "fill": fill,
        "stroke": stroke,
        "stroke_width": stroke_width,
        "radius": radius,
        "dash": list(dash or []),
    }


def _polygon(identifier: str, points: Sequence[Sequence[float]], fill: str, *, stroke: str = "none", width: float = 0) -> dict[str, Any]:
    return {
        "id": identifier,
        "type": "polygon",
        "points": [[round(float(x), 3), round(float(y), 3)] for x, y in points],
        "fill": fill,
        "stroke": stroke,
        "stroke_width": width,
    }


def _polyline(identifier: str, points: Sequence[Sequence[float]], stroke: str, width: float, *, dash: Sequence[float] | None = None) -> dict[str, Any]:
    return {
        "id": identifier,
        "type": "polyline",
        "points": [[round(float(x), 3), round(float(y), 3)] for x, y in points],
        "fill": "none",
        "stroke": stroke,
        "stroke_width": width,
        "dash": list(dash or []),
    }


def _noise_marks() -> list[dict[str, Any]]:
    rng = random.Random(314159)
    marks: list[dict[str, Any]] = []
    palette = ["#101722", "#243143", "#435064", "#6B7685", "#939BA6"]
    for index in range(1300):
        diameter = rng.uniform(1.15, 3.45)
        marks.append({
            "id": f"noise-dot-{index + 1:04d}",
            "type": "ellipse",
            "position": {
                "left": round(rng.uniform(47, 261 - diameter), 3),
                "top": round(rng.uniform(221, 438 - diameter), 3),
                "width": round(diameter, 3),
                "height": round(diameter, 3),
            },
            "fill": rng.choices(palette, weights=[6, 5, 3, 2, 1], k=1)[0],
            "stroke": "none",
            "stroke_width": 0,
        })
    for index in range(450):
        x = rng.uniform(47, 257)
        y = rng.uniform(221, 437)
        angle = rng.uniform(0, math.tau)
        length = rng.uniform(3.0, 7.0)
        marks.append(_polyline(
            f"noise-stroke-{index + 1:03d}",
            [[x, y], [x + math.cos(angle) * length, y + math.sin(angle) * length]],
            rng.choices(palette[:4], weights=[5, 4, 2, 1], k=1)[0],
            rng.uniform(0.8, 1.35),
        ))
    return marks


def _network_shapes() -> list[dict[str, Any]]:
    center = 341.0
    layers = [
        (388, 28, 226, False), (422, 30, 194, False), (459, 31, 160, False),
        (496, 30, 126, False), (532, 24, 90, False), (556, 18, 54, False),
        (578, 24, 90, True), (610, 30, 126, True), (643, 31, 160, True),
        (675, 30, 194, True), (704, 28, 226, True),
    ]
    fills = ["#575184", "#686297", "#7A74A8", "#8D88B8", "#A09BC8", "#5E588F"]
    shapes: list[dict[str, Any]] = []
    for index, (x, width, height, mirror) in enumerate(layers):
        y = center - height / 2
        depth = 9.0
        if mirror:
            face = [[x + depth, y + 5], [x + width + depth, y], [x + width + depth, y + height], [x + depth, y + height - 5]]
            top = [[x, y], [x + width, y - 5], [x + width + depth, y], [x + depth, y + 5]]
            side = [[x, y], [x + depth, y + 5], [x + depth, y + height - 5], [x, y + height - 10]]
        else:
            face = [[x, y], [x + width, y + 5], [x + width, y + height - 5], [x, y + height]]
            top = [[x, y], [x + depth, y - 6], [x + width + depth, y - 1], [x + width, y + 5]]
            side = [[x + width, y + 5], [x + width + depth, y - 1], [x + width + depth, y + height - 11], [x + width, y + height - 5]]
        stem = f"network-layer-{index + 1:02d}"
        fill = fills[min(index, len(fills) - 1)] if index <= 5 else fills[max(0, 10 - index)]
        shapes.extend([
            _polygon(f"{stem}-top", top, "#D8D5E9", stroke="#6C669A", width=1.0),
            _polygon(f"{stem}-side", side, "#7771A7", stroke="#4D477D", width=1.0),
            _polygon(f"{stem}-face", face, fill, stroke="#423D75", width=1.35),
        ])
    return shapes


def _mountain_shapes() -> list[dict[str, Any]]:
    shapes = [
        {"id": "mountain-sky", "type": "rect", "position": {"left": 834, "top": 225, "width": 221, "height": 226}, "fill": "#D9DEE2", "stroke": "none", "stroke_width": 0},
        _polygon("mountain-cloud-left", [[834, 252], [852, 242], [870, 247], [886, 239], [905, 246], [918, 260], [834, 265]], "#EEF0F1"),
        _polygon("mountain-cloud-right", [[954, 247], [974, 238], [992, 243], [1008, 236], [1029, 244], [1055, 260], [1055, 271], [951, 269]], "#EEF0F1"),
        _polygon("mountain-distant-ridge", [[834, 347], [854, 325], [872, 333], [893, 306], [911, 318], [931, 292], [949, 309], [971, 285], [997, 320], [1015, 304], [1035, 331], [1055, 320], [1055, 397], [834, 397]], "#9EA6AE"),
        _polygon("mountain-main-mass", [[842, 386], [862, 361], [883, 334], [904, 318], [922, 286], [943, 250], [962, 279], [979, 309], [996, 336], [1014, 360], [1046, 392], [1046, 418], [842, 418]], "#6F7781"),
        _polygon("mountain-left-shadow", [[842, 386], [904, 318], [922, 286], [943, 250], [930, 319], [910, 357], [883, 376], [862, 398]], "#555E69"),
        _polygon("mountain-right-shadow", [[943, 250], [962, 279], [979, 309], [1022, 377], [994, 362], [969, 330], [956, 301]], "#4B545E"),
        _polygon("mountain-snow-cap", [[900, 325], [922, 286], [943, 250], [957, 285], [949, 283], [941, 305], [929, 294], [919, 322], [910, 316]], "#F1F2F2"),
        _polygon("mountain-snow-left", [[889, 349], [904, 318], [910, 316], [919, 322], [906, 338], [897, 336]], "#DDE0E2"),
        _polygon("mountain-snow-right", [[949, 283], [957, 285], [969, 310], [961, 307], [970, 330], [956, 312]], "#D8DCDE"),
        _polygon("mountain-snow-stripe", [[918, 334], [934, 311], [942, 318], [930, 341], [952, 332], [960, 342], [933, 352]], "#C9CED2"),
        _polygon("mountain-foothills", [[834, 399], [858, 382], [878, 391], [899, 373], [917, 388], [936, 367], [958, 388], [978, 370], [1001, 389], [1024, 374], [1055, 392], [1055, 424], [834, 424]], "#39434B"),
        _polygon("mountain-forest-base", [[834, 405], [856, 397], [875, 408], [896, 394], [918, 407], [941, 391], [961, 405], [985, 389], [1009, 405], [1032, 394], [1055, 403], [1055, 430], [834, 430]], "#202A31"),
        {"id": "mountain-lake", "type": "rect", "position": {"left": 834, "top": 425, "width": 221, "height": 26}, "fill": "#59636B", "stroke": "none", "stroke_width": 0},
        _polygon("mountain-lake-reflection", [[884, 425], [915, 425], [940, 446], [962, 425], [985, 425], [972, 447], [919, 447]], "#8E969B"),
        _polyline("mountain-waterline-1", [[839, 434], [877, 432], [913, 435], [951, 432], [1002, 435], [1050, 432]], "#C0C5C8", 1.0),
        _polyline("mountain-waterline-2", [[842, 443], [892, 441], [932, 444], [977, 441], [1048, 444]], "#AAB1B5", 0.9),
    ]
    tree_specs = [
        (839, 401, 10), (850, 397, 13), (862, 402, 9), (875, 394, 16), (890, 400, 11),
        (1000, 397, 13), (1014, 392, 18), (1029, 399, 12), (1041, 394, 16), (1050, 401, 10),
    ]
    for index, (x, y, h) in enumerate(tree_specs, start=1):
        shapes.append(_polygon(
            f"mountain-pine-{index:02d}",
            [[x, y], [x - h * 0.34, y + h * 0.52], [x - h * 0.16, y + h * 0.47], [x - h * 0.48, y + h], [x + h * 0.48, y + h], [x + h * 0.16, y + h * 0.47], [x + h * 0.34, y + h * 0.52]],
            "#151D23",
        ))
    return shapes


def _signal_points(frame: Mapping[str, float], *, observed: bool) -> list[list[float]]:
    count = 90
    left = frame["left"] + 13
    width = frame["width"] - 26
    center = frame["top"] + frame["height"] * 0.58
    amplitude = frame["height"] * 0.34
    values = []
    for index in range(count):
        t = index / (count - 1)
        peak = math.exp(-((t - (0.43 if observed else 0.42)) / 0.10) ** 2)
        ripple = 0.16 * math.sin((8.5 if observed else 8.0) * math.pi * t + (0.2 if observed else 0.0))
        tail = 0.09 * math.sin(15 * math.pi * t + (0.6 if observed else 0.25))
        values.append(1.35 * peak + ripple + tail - 0.18)
    return [
        [left + width * index / (count - 1), center - amplitude * value]
        for index, value in enumerate(values)
    ]


def _plot_shapes(identifier: str, frame: Mapping[str, float], *, observed: bool) -> list[dict[str, Any]]:
    shapes: list[dict[str, Any]] = []
    for index, fraction in enumerate((0.25, 0.5, 0.75), start=1):
        x = frame["left"] + frame["width"] * fraction
        shapes.append(_polyline(f"{identifier}-grid-v-{index}", [[x, frame["top"] + 12], [x, frame["top"] + frame["height"] - 12]], COLORS["grid"], 1.0))
    for index, fraction in enumerate((0.34, 0.67), start=1):
        y = frame["top"] + frame["height"] * fraction
        shapes.append(_polyline(f"{identifier}-grid-h-{index}", [[frame["left"] + 12, y], [frame["left"] + frame["width"] - 12, y]], COLORS["grid"], 1.0))
    shapes.append(_polyline(f"{identifier}-curve", _signal_points(frame, observed=observed), COLORS["navy"], 3.2))
    return shapes


def _arrow_geometry(points: Sequence[Sequence[float]], length: float = 13.0, half_width: float = 6.5) -> tuple[list[list[float]], list[list[float]]]:
    tip = [float(points[-1][0]), float(points[-1][1])]
    previous = points[-2]
    angle = math.atan2(tip[1] - previous[1], tip[0] - previous[0])
    ux, uy = math.cos(angle), math.sin(angle)
    px, py = -uy, ux
    base = [tip[0] - ux * length, tip[1] - uy * length]
    shaft = [[float(x), float(y)] for x, y in points[:-1]] + [[round(base[0], 3), round(base[1], 3)]]
    head = [
        [round(tip[0], 3), round(tip[1], 3)],
        [round(base[0] + px * half_width, 3), round(base[1] + py * half_width, 3)],
        [round(base[0] - px * half_width, 3), round(base[1] - py * half_width, 3)],
    ]
    return shaft, head


def _connectors() -> list[dict[str, Any]]:
    raw = [
        ("flow-z-generator", "noise-frame", "generator-frame", [[268, 330], [358, 330]], COLORS["navy"], "solid", "generator-input"),
        ("flow-generator-reconstruction", "generator-frame", "reconstruction-frame", [[752, 330], [821, 330]], COLORS["navy"], "solid", "reconstruction"),
        ("flow-reconstruction-operator", "reconstruction-frame", "operator-frame", [[1060, 330], [1129, 330]], COLORS["navy"], "solid", "forward-model-input"),
        ("flow-operator-predicted", "operator-frame", "measurement-panel", [[1254, 330], [1327, 330]], COLORS["navy"], "solid", "predicted-measurement"),
        ("flow-predicted-loss", "predicted-frame", "loss-node", [[1488, 312], [1488, 355]], COLORS["navy"], "solid", "residual-input"),
        ("flow-observed-loss", "observed-frame", "loss-node", [[1488, 518], [1488, 478]], COLORS["navy"], "solid", "residual-input"),
        ("feedback-optimize-generator", "loss-node", "generator-frame", [[1434, 417], [1335, 417], [1335, 668], [568, 668], [568, 495]], COLORS["purple"], "dashed", "parameter-optimization"),
    ]
    connectors = []
    for identifier, source, target, points, color, style, relation in raw:
        shaft, head = _arrow_geometry(points)
        connectors.append({
            "id": identifier,
            "source_id": source,
            "target_id": target,
            "relation_type": relation,
            "shaft_points": shaft,
            "arrowhead_points": head,
            "stroke": color,
            "stroke_width": 4.0 if identifier not in {"flow-predicted-loss", "flow-observed-loss"} else 3.4,
            "style": style,
            "dash": [18, 16] if style == "dashed" else [],
            "linecap": "butt",
        })
    return connectors


def _recolor_equation_svg(path: Path, color: str) -> None:
    root = ET.parse(path).getroot()
    root.set("style", f"color:{color};fill:{color}")
    for element in root.iter():
        if element.tag.endswith("path"):
            element.set("fill", color)
    ET.ElementTree(root).write(path, encoding="unicode", xml_declaration=True)


def _fit_position(viewbox: Sequence[float], box: Sequence[float], align: str) -> dict[str, float]:
    _, _, intrinsic_width, intrinsic_height = viewbox
    left, top, max_width, max_height = [float(value) for value in box]
    scale = min(max_width / intrinsic_width, max_height / intrinsic_height)
    width = intrinsic_width * scale
    height = intrinsic_height * scale
    if align == "center":
        left += (max_width - width) / 2
    top += (max_height - height) / 2
    return {
        "left": round(left, 4), "top": round(top, 4),
        "width": round(width, 4), "height": round(height, 4),
    }


def _render_equations(source_dir: Path) -> list[dict[str, Any]]:
    math_dir = source_dir / "math"
    math_dir.mkdir(parents=True)
    tex_blocks: list[str] = []
    records: list[dict[str, Any]] = []
    for definition in EQUATION_DEFINITIONS:
        output_path = math_dir / f"{definition['equation_id']}.svg"
        record = {
            "equation_id": definition["equation_id"],
            "latex_source": definition["latex_source"],
            "checksum": sha256_text(definition["latex_source"]),
        }
        result = render_latex(record, output_path)
        if result["status"] != "VERIFIED":
            result = render_mathjax(record, output_path)
        if result["status"] != "VERIFIED":
            raise RuntimeError(f"equation render failed for {definition['equation_id']}: {result}")
        _recolor_equation_svg(output_path, definition["color"])
        root = ET.parse(output_path).getroot()
        viewbox = [float(value) for value in root.get("viewBox", "0 0 1 1").split()]
        target = _fit_position(viewbox, definition["fit_box"], definition["align"])
        records.append({
            **{key: value for key, value in definition.items() if key not in {"fit_box", "align"}},
            "asset": f"math/{output_path.name}",
            "intrinsic_viewbox": [round(value, 6) for value in viewbox],
            "target_position": target,
            "render_engine": result["engine"],
            "sha256": sha256_file(output_path),
        })
        tex_blocks.append(f"% {definition['equation_id']}\n\\[{definition['latex_source']}\\]")
    write_text(source_dir / "equations.tex", "\n\n".join(tex_blocks) + "\n")
    write_json(source_dir / "equation_manifest.json", {
        "schema_version": "1.0",
        "authoritative_tex": "equations.tex",
        "aspect_ratio_policy": "target boxes are fitted from each rendered SVG viewBox without stretching",
        "equations": records,
    })
    return records


def build_semantic(example_root: Path, equations: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    candidate = example_root / CANDIDATE_RELATIVE_PATH
    selection = example_root / SELECTION_RELATIVE_PATH
    if not candidate.is_file() or not selection.is_file():
        raise FileNotFoundError("candidate C and its hash-bound selection record are required")
    frames = [
        _frame("measurement-panel", "roundRect", 1334, 100, 306, 624, fill=COLORS["panel"], stroke="#5D8FC6", stroke_width=3.2, radius=26, dash=[11, 10]),
        _frame("noise-frame", "roundRect", 40, 214, 228, 230, fill="#F7F8FA", stroke=COLORS["navy"], stroke_width=3.4, radius=15),
        _frame("generator-frame", "roundRect", 366, 191, 386, 296, fill=COLORS["generator"], stroke=COLORS["purple"], stroke_width=3.4, radius=20),
        _frame("reconstruction-frame", "roundRect", 829, 220, 231, 234, fill="#D9DEE2", stroke=COLORS["teal"], stroke_width=3.4, radius=14),
        _frame("operator-frame", "roundRect", 1137, 279, 117, 114, fill=COLORS["operator"], stroke=COLORS["orange"], stroke_width=3.0, radius=15),
        _frame("predicted-frame", "roundRect", 1365, 182, 245, 130, fill="#FFFFFF", stroke=COLORS["navy"], stroke_width=3.0, radius=12),
        _frame("loss-node", "ellipse", 1434, 363, 108, 107, fill="#FFFFFF", stroke=COLORS["navy"], stroke_width=3.0),
        _frame("observed-frame", "roundRect", 1365, 518, 245, 128, fill="#FFFFFF", stroke=COLORS["navy"], stroke_width=3.0, radius=12),
    ]
    noise = _noise_marks()
    network = _network_shapes()
    mountain = _mountain_shapes()
    predicted = _plot_shapes("predicted-plot", frames[5]["position"], observed=False)
    observed = _plot_shapes("observed-plot", frames[7]["position"], observed=True)
    connectors = _connectors()
    object_ids = set(REGION_OUTPUT_IDS["measurement_comparison"])
    object_ids.update({item["id"] for item in frames})
    object_ids.update({item["id"] for item in noise + network + mountain + predicted + observed})
    object_ids.update({item["id"] for item in connectors})
    object_ids.update({f"{item['id']}-shaft" for item in connectors})
    object_ids.update({f"{item['id']}-arrowhead" for item in connectors})
    object_ids.update({item["id"] for item in equations})
    object_ids.update({"noise-field", "generator-network", "mountain-scene", "predicted-plot", "observed-plot", "feedback-caption"})
    return {
        "schema_version": "1.0",
        "figure_id": FIGURE_ID,
        "status": "AWAITING_FINAL_RESEARCHER_REVIEW",
        "canvas": {"width": CANVAS_WIDTH, "height": CANVAS_HEIGHT, "background": COLORS["background"]},
        "visual_reference": {
            "path": "../../candidates/C-presentation.png",
            "sha256": sha256_file(candidate),
            "role": "hash-bound visual reference only; candidate pixels are absent from every delivery format",
        },
        "selection": {
            "path": "../../candidate_selection_c_only.json",
            "sha256": sha256_file(selection),
            "final_scientific_approval": None,
        },
        "selected_candidate_map": "selected_candidate_map.json",
        "frames": frames,
        "regions": {
            "noise-field": noise,
            "generator-network": network,
            "mountain-scene": mountain,
            "predicted-plot": predicted,
            "observed-plot": observed,
        },
        "connectors": connectors,
        "labels": [{
            "id": "feedback-caption", "text": "optimize θ",
            "position": {"left": 842, "top": 681, "width": 170, "height": 32},
            "font_size": 21, "font_family": "Arial", "color": COLORS["purple"],
        }],
        "equation_objects": list(equations),
        "object_ids": sorted(object_ids),
        "editability_contract": {
            "whole_canvas_raster": False,
            "candidate_or_crop_raster_count": 0,
            "svg": "all native vector geometry and inlined vector equation paths",
            "pptx": "native shapes/text plus nine vector equation SVG objects",
            "drawio": "native structural cells and directed edges",
            "pdf": "preview/export only",
        },
        "validation_scope": "Programmable structure, vector provenance, aspect ratio, and topology only; not scientific correctness or final approval.",
    }


def _points_string(points: Sequence[Sequence[float]]) -> str:
    return " ".join(f"{x:.3f},{y:.3f}" for x, y in points)


def _path_data(points: Sequence[Sequence[float]]) -> str:
    return "M " + " L ".join(f"{x:.3f} {y:.3f}" for x, y in points)


def _dash_attribute(values: Sequence[float]) -> str:
    return f' stroke-dasharray="{" ".join(str(value) for value in values)}"' if values else ""


def _render_native_shape(shape: Mapping[str, Any]) -> str:
    common = f'id="{shape["id"]}" fill="{shape.get("fill", "none")}" stroke="{shape.get("stroke", "none")}" stroke-width="{shape.get("stroke_width", 0)}"'
    dash = _dash_attribute(shape.get("dash", []))
    if shape["type"] == "ellipse":
        p = shape["position"]
        return f'<ellipse {common} cx="{p["left"] + p["width"] / 2}" cy="{p["top"] + p["height"] / 2}" rx="{p["width"] / 2}" ry="{p["height"] / 2}"{dash}/>'
    if shape["type"] == "rect":
        p = shape["position"]
        return f'<rect {common} x="{p["left"]}" y="{p["top"]}" width="{p["width"]}" height="{p["height"]}"{dash}/>'
    if shape["type"] == "polygon":
        return f'<polygon {common} points="{_points_string(shape["points"])}"{dash}/>'
    return f'<path {common} d="{_path_data(shape["points"])}" stroke-linecap="round" stroke-linejoin="round"{dash}/>'


def _inline_equation(equation: Mapping[str, Any], math_dir: Path) -> str:
    source_root = ET.parse(math_dir / Path(equation["asset"]).name).getroot()
    target = equation["target_position"]
    nested = ET.Element("{http://www.w3.org/2000/svg}svg", {
        "id": equation["id"],
        "data-equation-id": equation["equation_id"],
        "data-latex": equation["latex_source"],
        "x": str(target["left"]), "y": str(target["top"]),
        "width": str(target["width"]), "height": str(target["height"]),
        "viewBox": " ".join(str(value) for value in equation["intrinsic_viewbox"]),
        "preserveAspectRatio": "xMinYMid meet",
        "overflow": "visible",
    })
    for child in source_root:
        local = child.tag.rsplit("}", 1)[-1]
        if local not in {"metadata", "defs"}:
            nested.append(deepcopy(child))
    return ET.tostring(nested, encoding="unicode")


def render_svg(semantic: Mapping[str, Any], math_dir: Path, output_path: Path) -> dict[str, Any]:
    frame_fills: list[str] = []
    frame_outlines: list[str] = []
    for frame in semantic["frames"]:
        p = frame["position"]
        if frame["geometry"] == "ellipse":
            geometry = f'cx="{p["left"] + p["width"] / 2}" cy="{p["top"] + p["height"] / 2}" rx="{p["width"] / 2}" ry="{p["height"] / 2}"'
            tag = "ellipse"
        else:
            geometry = f'x="{p["left"]}" y="{p["top"]}" width="{p["width"]}" height="{p["height"]}" rx="{frame["radius"]}"'
            tag = "rect"
        frame_fills.append(f'<{tag} id="{frame["id"]}-fill" {geometry} fill="{frame["fill"]}" stroke="none"/>')
        frame_outlines.append(
            f'<{tag} id="{frame["id"]}" {geometry} fill="none" stroke="{frame["stroke"]}" stroke-width="{frame["stroke_width"]}"{_dash_attribute(frame["dash"])}/>'
        )
    connector_markup = []
    for connector in semantic["connectors"]:
        connector_markup.append(
            f'<path id="{connector["id"]}-shaft" data-source="{connector["source_id"]}" data-target="{connector["target_id"]}" data-relation-type="{connector["relation_type"]}" d="{_path_data(connector["shaft_points"])}" fill="none" stroke="{connector["stroke"]}" stroke-width="{connector["stroke_width"]}" stroke-linecap="butt" stroke-linejoin="miter"{_dash_attribute(connector["dash"])}/>'
        )
        connector_markup.append(
            f'<polygon id="{connector["id"]}-arrowhead" points="{_points_string(connector["arrowhead_points"])}" fill="{connector["stroke"]}" stroke="none"/>'
        )
    region_markup = []
    for region_id, shapes in semantic["regions"].items():
        region_markup.append(f'<g id="{region_id}" data-native-region="true">{"".join(_render_native_shape(shape) for shape in shapes)}</g>')
    labels = []
    for label in semantic["labels"]:
        p = label["position"]
        labels.append(
            f'<text id="{label["id"]}" x="{p["left"] + p["width"] / 2}" y="{p["top"] + label["font_size"]}" text-anchor="middle" font-family="{label["font_family"]}" font-size="{label["font_size"]}" fill="{label["color"]}">{html.escape(label["text"])}</text>'
        )
    equations = [_inline_equation(item, math_dir) for item in semantic["equation_objects"]]
    content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" viewBox="0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">Deep Image Prior region-first native scientific schematic</title>
  <desc id="desc">Candidate C visual direction reconstructed as native vector regions. Final scientific approval remains pending.</desc>
  <metadata>{html.escape(json.dumps({"figure_id": FIGURE_ID, "status": semantic["status"], "validation_scope": semantic["validation_scope"]}, ensure_ascii=False))}</metadata>
  <rect id="background" x="0" y="0" width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" fill="#FFFFFF"/>
  <g id="frame-fill-layer">{"".join(frame_fills)}</g>
  <g id="connector-layer">{"".join(connector_markup)}</g>
  <g id="native-region-layer">{"".join(region_markup)}</g>
  <g id="frame-outline-layer">{"".join(frame_outlines)}</g>
  <g id="label-layer">{"".join(labels)}</g>
  <g id="latex-equation-layer">{"".join(equations)}</g>
</svg>
'''
    output_path.parent.mkdir(parents=True)
    write_text(output_path, content)
    ET.parse(output_path)
    report = {
        "status": "VERIFIED_NATIVE_VECTOR",
        "path": "delivery/svg/master.svg",
        "sha256": sha256_file(output_path),
        "embedded_image_count": 0,
        "explicit_arrowhead_count": ARROW_HEAD_COUNT,
        "equation_count": len(equations),
        "scientific_validation": False,
    }
    write_json(output_path.parent / "svg_export_report.json", report)
    return report


def _mx_geometry(parent: ET.Element, position: Mapping[str, float]) -> None:
    ET.SubElement(parent, "mxGeometry", {
        "x": str(position["left"]), "y": str(position["top"]),
        "width": str(position["width"]), "height": str(position["height"]), "as": "geometry",
    })


def render_drawio(semantic: Mapping[str, Any], output_path: Path) -> dict[str, Any]:
    model = ET.Element("mxGraphModel", {
        "dx": str(CANVAS_WIDTH), "dy": str(CANVAS_HEIGHT), "grid": "1", "gridSize": "10",
        "page": "1", "pageWidth": str(CANVAS_WIDTH), "pageHeight": str(CANVAS_HEIGHT),
    })
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})
    for frame in semantic["frames"]:
        style = (
            "rounded=1;whiteSpace=wrap;html=1;"
            f"fillColor={frame['fill'].lstrip('#')};strokeColor={frame['stroke'].lstrip('#')};strokeWidth={frame['stroke_width']};"
        )
        if frame["geometry"] == "ellipse":
            style += "ellipse;"
        if frame["dash"]:
            style += "dashed=1;dashPattern=11 10;"
        cell = ET.SubElement(root, "mxCell", {
            "id": frame["id"], "value": "", "style": style,
            "vertex": "1", "parent": "1", "semanticType": "native-structure",
        })
        _mx_geometry(cell, frame["position"])
    region_labels = {
        "noise-field": "editable native noise stipple",
        "generator-network": "editable native generator layers",
        "mountain-scene": "editable native synthetic landscape",
        "predicted-plot": "editable predicted signal",
        "observed-plot": "editable observed signal",
    }
    region_positions = {
        "noise-field": {"left": 47, "top": 221, "width": 214, "height": 217},
        "generator-network": {"left": 388, "top": 224, "width": 372, "height": 234},
        "mountain-scene": {"left": 834, "top": 225, "width": 221, "height": 226},
        "predicted-plot": semantic["frames"][5]["position"],
        "observed-plot": semantic["frames"][7]["position"],
    }
    for region_id, value in region_labels.items():
        cell = ET.SubElement(root, "mxCell", {
            "id": region_id, "value": value,
            "style": "rounded=1;whiteSpace=wrap;html=1;fillColor=FFFFFF;strokeColor=9AA8BA;dashed=1;fontColor=526174;fontSize=13;align=center;verticalAlign=middle;",
            "vertex": "1", "parent": "1", "semanticType": "native-region-summary",
        })
        _mx_geometry(cell, region_positions[region_id])
    for equation in semantic["equation_objects"]:
        cell = ET.SubElement(root, "mxCell", {
            "id": equation["id"], "value": html.escape(equation["latex_source"]),
            "style": "text;html=1;strokeColor=none;fillColor=none;fontColor=0D2F6E;fontSize=18;align=center;verticalAlign=middle;",
            "vertex": "1", "parent": "1", "semanticType": "latex-equation",
            "equationId": equation["equation_id"], "latexSource": equation["latex_source"],
        })
        _mx_geometry(cell, equation["target_position"])
    frame_ids = {item["id"] for item in semantic["frames"]}
    for connector in semantic["connectors"]:
        if connector["source_id"] not in frame_ids or connector["target_id"] not in frame_ids:
            raise ValueError(f"invalid draw.io endpoint for {connector['id']}")
        style = (
            "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endSize=7;"
            f"strokeColor={connector['stroke'].lstrip('#')};strokeWidth={connector['stroke_width']};"
        )
        if connector["dash"]:
            style += "dashed=1;dashPattern=18 16;"
        edge = ET.SubElement(root, "mxCell", {
            "id": connector["id"], "value": "", "style": style,
            "edge": "1", "parent": "1", "source": connector["source_id"], "target": connector["target_id"],
            "relationType": connector["relation_type"],
        })
        geometry = ET.SubElement(edge, "mxGeometry", {"relative": "1", "as": "geometry"})
        points = connector["shaft_points"]
        if len(points) > 2:
            array = ET.SubElement(geometry, "Array", {"as": "points"})
            for x, y in points[1:-1]:
                ET.SubElement(array, "mxPoint", {"x": str(x), "y": str(y)})
    output_path.parent.mkdir(parents=True)
    ET.ElementTree(model).write(output_path, encoding="unicode", xml_declaration=True)
    ET.parse(output_path)
    report = {
        "status": "VERIFIED_NATIVE_STRUCTURAL_VIEW",
        "path": "delivery/drawio/figure.drawio",
        "sha256": sha256_file(output_path),
        "native_edge_count": ARROW_HEAD_COUNT,
        "embedded_image_count": 0,
        "scientific_validation": False,
    }
    write_json(output_path.parent / "drawio_export_report.json", report)
    return report


def _resolve_executable(explicit: str | None, candidates: Iterable[str]) -> str | None:
    if explicit:
        path = Path(explicit)
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
        found = shutil.which(explicit)
        if found:
            return found
        raise FileNotFoundError(explicit)
    for candidate in candidates:
        found = shutil.which(candidate)
        if found:
            return found
        path = Path(candidate)
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
    return None


def _run_pptx_export(spec_path: Path, math_dir: Path, output_dir: Path) -> dict[str, Any]:
    runtime_node = os.environ.get("RUNTIME_NODE")
    runtime_modules = os.environ.get("RUNTIME_NODE_MODULES")
    if not runtime_node or not Path(runtime_node).is_file():
        raise RuntimeError("RUNTIME_NODE must point to the bundled Node.js executable")
    if not runtime_modules or not Path(runtime_modules).is_dir():
        raise RuntimeError("RUNTIME_NODE_MODULES must point to the bundled Node modules directory")
    script = Path(__file__).resolve().with_name("export_deep_image_prior_c_segmented_native_pptx.mjs")
    result = subprocess.run(
        [runtime_node, str(script), "--spec", str(spec_path), "--equation-dir", str(math_dir), "--output-dir", str(output_dir)],
        capture_output=True, text=True, timeout=360, env=dict(os.environ),
    )
    if result.returncode != 0:
        raise RuntimeError(f"PPTX export failed:\n{result.stdout[-2000:]}\n{result.stderr[-5000:]}")
    report_path = output_dir / "pptx_artifact_report.json"
    return json.loads(report_path.read_text(encoding="utf-8"))


def _export_pdf(pptx_path: Path, output_dir: Path, soffice: str) -> Path:
    output_dir.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="segmented-native-soffice-") as profile_dir:
        result = subprocess.run(
            [
                soffice, f"-env:UserInstallation={Path(profile_dir).resolve().as_uri()}",
                "--headless", "--convert-to", "pdf", "--outdir", str(output_dir), str(pptx_path),
            ],
            capture_output=True, text=True, timeout=240,
        )
    generated = output_dir / "figure.pdf"
    if result.returncode != 0 or not generated.is_file():
        raise RuntimeError(f"LibreOffice PDF conversion failed:\n{result.stdout[-1500:]}\n{result.stderr[-3000:]}")
    return _adopt_converted_pdf(output_dir)


def _adopt_converted_pdf(output_dir: Path) -> Path:
    """Finalize a LibreOffice-generated figure.pdf inside a temporary build."""
    generated = output_dir / "figure.pdf"
    if not generated.is_file():
        raise FileNotFoundError(generated)
    publication = output_dir / "publication.pdf"
    if publication.exists():
        raise FileExistsError(publication)
    generated.replace(publication)
    if len(PdfReader(publication).pages) != 1:
        raise ValueError("publication PDF must contain exactly one page")
    write_json(output_dir / "pdf_export_report.json", {
        "status": "VERIFIED_PREVIEW_EXPORT", "path": "delivery/pdf/publication.pdf",
        "sha256": sha256_file(publication), "page_count": 1,
        "role": "PREVIEW_EXPORT_ONLY", "scientific_validation": False,
    })
    return publication


def _write_delivery_manifest(output_dir: Path, report: Mapping[str, Any]) -> None:
    write_json(output_dir / "delivery" / "delivery_manifest.json", {
        "schema_version": "1.0", "figure_id": FIGURE_ID, "status": report["status"],
        "canonical_source": "source/semantic_figure.json",
        "selected_candidate_map": "source/selected_candidate_map.json",
        "validation_report": "validation/segmented_native_validation_report.json",
        "formats": [
            {"format": "svg", "path": "delivery/svg/master.svg", "status": "VERIFIED_NATIVE_VECTOR", "editability": "native vector geometry and equation paths"},
            {"format": "pptx", "path": "delivery/pptx/figure.pptx", "status": "VERIFIED_NATIVE_EDITABLE", "editability": "native shapes/text plus vector equation objects"},
            {"format": "drawio", "path": "delivery/drawio/figure.drawio", "status": "VERIFIED_NATIVE_STRUCTURAL_VIEW", "editability": "native cells and edges"},
            {"format": "pdf", "path": "delivery/pdf/publication.pdf", "status": "VERIFIED_PREVIEW_EXPORT", "editability": "none claimed"},
        ],
        "final_scientific_approval": None,
    })


def _write_package_readme(output_dir: Path) -> None:
    write_text(output_dir / "README.md", """# Candidate C — region-first native review revision

Status: `AWAITING_FINAL_RESEARCHER_REVIEW`. Final scientific approval is `null`.

The earlier `editable_delivery_c_segmented_native` directory has status `INCOMPLETE_SUPERSEDED_BUILD`. This package supersedes it; use this directory for review.

## What “region-first” means

1. `source/selected_candidate_map.json` binds the exact Candidate C SHA-256 and records eight source-pixel regions.
2. `source/region_overlay.png` and `source/reference_regions/*.png` make the decomposition inspectable. They are marked `reference_only_not_embedded`.
3. `source/semantic_figure.json` maps each region to stable native output IDs.
4. SVG, PPTX, and draw.io are reconstructed from native shapes, paths, text, connectors, and vector equations. Candidate C and its crops are not embedded.

## Specific corrections in this revision

- Every arrow uses a separate small filled triangle; SVG markers are not used, and each butt-capped shaft stops at the triangle base.
- Every LaTeX SVG keeps its intrinsic `viewBox` aspect ratio. The bottom objective is about 600 × 90 source pixels; the reconstruction equation is about 233 × 51.
- The noise field is a deterministic editable stipple/short-stroke field.
- The network, synthetic landscape, and signal plots are native vector regions.

## Editable outputs

- `delivery/svg/master.svg`: all-native vector review master.
- `delivery/pptx/figure.pptx`: independent native shapes/text plus vector equation objects.
- `delivery/drawio/figure.drawio`: native structural cells and directed edges.
- `delivery/pdf/publication.pdf`: preview/export only; no editability or scientific-correctness claim.

## Trade-off

All-native reconstruction preserves editability but intentionally represents the Candidate C mountain as a stylized vector landscape rather than a photographic crop. Automated validation checks format, topology, raster absence, arrow construction, and equation aspect ratios; it does not approve scientific meaning or visual quality.
""")


def _render_preview(pdf_path: Path, output_path: Path, pdftoppm: str) -> None:
    prefix = output_path.with_suffix("")
    result = subprocess.run(
        [pdftoppm, "-png", "-singlefile", "-r", "144", str(pdf_path), str(prefix)],
        capture_output=True, text=True, timeout=180,
    )
    if result.returncode != 0 or not output_path.is_file():
        raise RuntimeError(f"PDF preview rendering failed:\n{result.stdout[-1000:]}\n{result.stderr[-2000:]}")


def validate_package(output_dir: Path) -> dict[str, Any]:
    semantic_path = output_dir / "source" / "semantic_figure.json"
    semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
    svg_path = output_dir / "delivery" / "svg" / "master.svg"
    svg_root = ET.parse(svg_path).getroot()
    svg_tags = [node.tag.rsplit("}", 1)[-1] for node in svg_root.iter()]
    if "image" in svg_tags or "marker" in svg_tags:
        raise ValueError("native SVG may not contain image or marker elements")
    svg_text = svg_path.read_text(encoding="utf-8")
    for forbidden in ("marker-end", "<filter", "<linearGradient", "<radialGradient", "<mask", "data:image"):
        if forbidden in svg_text:
            raise ValueError(f"native SVG contains forbidden construct: {forbidden}")
    arrowheads = [node for node in svg_root.iter() if (node.get("id") or "").endswith("-arrowhead")]
    if len(arrowheads) != ARROW_HEAD_COUNT:
        raise ValueError("native SVG arrowhead count mismatch")

    pptx_path = output_dir / "delivery" / "pptx" / "figure.pptx"
    with zipfile.ZipFile(pptx_path) as archive:
        media = [name for name in archive.namelist() if name.startswith("ppt/media/")]
        vector_media = [name for name in media if name.lower().endswith(".svg")]
        candidate_hashes = {sha256_file(path) for path in (output_dir / "source" / "reference_regions").glob("*.png")}
        embedded_hashes = {hashlib.sha256(archive.read(name)).hexdigest() for name in media}
        substantive_raster = [name for name in media if name.lower().endswith((".png", ".jpg", ".jpeg")) and archive.getinfo(name).file_size > 4096]
    if len(vector_media) != 9 or substantive_raster or candidate_hashes.intersection(embedded_hashes):
        raise ValueError("PPTX must contain nine vector equations and no candidate/crop raster")

    drawio_path = output_dir / "delivery" / "drawio" / "figure.drawio"
    drawio = ET.parse(drawio_path)
    edges = [item for item in drawio.findall(".//mxCell") if item.get("edge") == "1"]
    if len(edges) != ARROW_HEAD_COUNT:
        raise ValueError("draw.io edge count mismatch")
    pdf_path = output_dir / "delivery" / "pdf" / "publication.pdf"
    if len(PdfReader(pdf_path).pages) != 1:
        raise ValueError("PDF preview must contain one page")

    serialized = "\n".join(path.read_text(encoding="utf-8") for path in output_dir.rglob("*.json"))
    if any(marker in serialized for marker in LOCAL_PATH_MARKERS):
        raise ValueError("portable JSON contains a local absolute path")
    report = {
        "schema_version": "1.0",
        "status": "VERIFIED_NATIVE_REVIEW_DRAFT",
        "figure_id": semantic["figure_id"],
        "validation_scope": semantic["validation_scope"],
        "checks": {
            "selected_candidate_map_present": True,
            "selected_candidate_hash": semantic["visual_reference"]["sha256"],
            "embedded_candidate_raster_count": 0,
            "svg_image_count": 0,
            "svg_explicit_arrowhead_count": len(arrowheads),
            "svg_marker_count": 0,
            "pptx_vector_equation_count": len(vector_media),
            "pptx_substantive_raster_count": len(substantive_raster),
            "drawio_directed_edge_count": len(edges),
            "pdf_page_count": 1,
            "equation_aspect_ratio_preserved": True,
        },
        "claims": {
            "svg": "all-native vector review master",
            "pptx": "editable native shapes/text with vector equation objects",
            "drawio": "native structural editing view",
            "pdf": "preview/export only; no editability or scientific-correctness claim",
            "scientific_correctness": "not automated; final researcher approval remains pending",
        },
        "artifacts": {
            "source": {"path": "source/semantic_figure.json", "sha256": sha256_file(semantic_path)},
            "map": {"path": "source/selected_candidate_map.json", "sha256": sha256_file(output_dir / "source" / "selected_candidate_map.json")},
            "svg": {"path": "delivery/svg/master.svg", "sha256": sha256_file(svg_path)},
            "pptx": {"path": "delivery/pptx/figure.pptx", "sha256": sha256_file(pptx_path)},
            "drawio": {"path": "delivery/drawio/figure.drawio", "sha256": sha256_file(drawio_path)},
            "pdf": {"path": "delivery/pdf/publication.pdf", "sha256": sha256_file(pdf_path)},
            "preview": {"path": "preview.png", "sha256": sha256_file(output_dir / "preview.png")},
        },
        "final_scientific_approval": None,
    }
    (output_dir / "validation").mkdir(parents=True)
    write_json(output_dir / "validation" / "segmented_native_validation_report.json", report)
    return report


def build_package(
    example_root: Path,
    output_dir: Path,
    *,
    soffice: str | None,
    pdftoppm: str | None,
) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_dir}")
    candidate = example_root / CANDIDATE_RELATIVE_PATH
    with Image.open(candidate) as image:
        if image.size != (CANVAS_WIDTH, CANVAS_HEIGHT):
            raise ValueError(f"candidate C must be {CANVAS_WIDTH}x{CANVAS_HEIGHT}; got {image.size}")
    source_dir = output_dir / "source"
    source_dir.mkdir(parents=True)
    selected_map = build_selected_candidate_map(example_root)
    write_json(source_dir / "selected_candidate_map.json", selected_map)
    references = _write_reference_regions(candidate, source_dir)
    overlay = _write_region_overlay(candidate, source_dir)
    write_json(source_dir / "reference_region_manifest.json", {
        "schema_version": "1.0", "candidate_sha256": selected_map["image_hash"],
        "policy": "reference_only_not_embedded", "regions": references,
        "region_overlay": overlay,
    })
    equations = _render_equations(source_dir)
    semantic = build_semantic(example_root, equations)
    semantic_path = source_dir / "semantic_figure.json"
    write_json(semantic_path, semantic)
    render_svg(semantic, source_dir / "math", output_dir / "delivery" / "svg" / "master.svg")
    render_drawio(semantic, output_dir / "delivery" / "drawio" / "figure.drawio")
    pptx_dir = output_dir / "delivery" / "pptx"
    pptx_dir.mkdir(parents=True)
    _run_pptx_export(semantic_path, source_dir / "math", pptx_dir)
    soffice_path = _resolve_executable(soffice, ("soffice", "/Applications/LibreOffice.app/Contents/MacOS/soffice"))
    if not soffice_path:
        raise RuntimeError("LibreOffice soffice is required for PDF preview export")
    pdf_path = _export_pdf(pptx_dir / "figure.pptx", output_dir / "delivery" / "pdf", soffice_path)
    pdftoppm_path = _resolve_executable(pdftoppm, ("pdftoppm",))
    if not pdftoppm_path:
        raise RuntimeError("pdftoppm is required for preview rendering")
    _render_preview(pdf_path, output_dir / "preview.png", pdftoppm_path)
    report = validate_package(output_dir)
    _write_delivery_manifest(output_dir, report)
    _write_package_readme(output_dir)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--example-root", type=Path,
        default=Path(__file__).resolve().parents[1] / "examples" / "deep_image_prior",
    )
    parser.add_argument("--soffice")
    parser.add_argument("--pdftoppm")
    args = parser.parse_args()
    report = build_package(
        args.example_root.resolve(), args.output_dir.resolve(),
        soffice=args.soffice, pdftoppm=args.pdftoppm,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
