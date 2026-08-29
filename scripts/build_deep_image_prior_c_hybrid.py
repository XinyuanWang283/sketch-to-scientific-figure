#!/usr/bin/env python3
"""Build a high-fidelity hybrid reconstruction of Deep Image Prior candidate C.

The selected ImageGen PNG is used only as a visual reference and as the source
for two explicitly approved, replaceable raster atoms: the dense noise input
and the synthetic mountain reconstruction.  Structure, arrows, plots, network
layers, labels, and equations are rebuilt as native/vector objects.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from PIL import Image
from pypdf import PdfReader

from figure_artifacts import write_json
from render_equations import render_latex, render_mathjax
from workflow_v3 import write_text


CANVAS_WIDTH = 1672
CANVAS_HEIGHT = 941
CANDIDATE_RELATIVE_PATH = Path("candidates") / "C-presentation.png"
SELECTION_RELATIVE_PATH = Path("candidate_selection_c_only.json")
FIGURE_ID = "deep-image-prior-c-high-fidelity-hybrid"
LOCAL_PATH_MARKERS = (
    "/" + "Users" + "/",
    "/" + "private" + "/" + "tmp" + "/",
)

COLORS = {
    "background": "#FFFFFF",
    "navy": "#0D2F6E",
    "purple": "#5A258C",
    "teal": "#0B6262",
    "orange": "#C57300",
    "panel": "#EDF4FC",
    "generator": "#F7F2FC",
    "operator": "#FFF8EC",
    "grid": "#D7E0EC",
    "muted": "#65748A",
}

APPROVED_RASTER_ATOMS = {
    "noise": {
        "crop_box": [44, 219, 266, 441],
        "target": {"left": 45, "top": 219, "width": 219, "height": 222},
        "description": "Synthetic dense noise texture; replaceable visual atom, not measured data.",
    },
    "reconstruction": {
        "crop_box": [834, 224, 1056, 451],
        "target": {"left": 833, "top": 224, "width": 223, "height": 227},
        "description": "Synthetic mountain visual anchor; replaceable visual atom, not a research result.",
    },
}

EQUATIONS = [
    {
        "id": "eq-z",
        "equation_id": "eq_z",
        "latex_source": r"z",
        "color": COLORS["navy"],
        "position": {"left": 132, "top": 145, "width": 55, "height": 47},
        "role": "input-label",
    },
    {
        "id": "eq-generator",
        "equation_id": "eq_generator",
        "latex_source": r"G_{\theta}",
        "color": COLORS["purple"],
        "position": {"left": 521, "top": 199, "width": 78, "height": 55},
        "role": "generator-label",
    },
    {
        "id": "eq-xhat",
        "equation_id": "eq_xhat",
        "latex_source": r"\hat{x}",
        "color": COLORS["teal"],
        "position": {"left": 918, "top": 145, "width": 57, "height": 58},
        "role": "reconstruction-label",
    },
    {
        "id": "eq-operator",
        "equation_id": "eq_operator",
        "latex_source": r"A",
        "color": COLORS["orange"],
        "position": {"left": 1170, "top": 302, "width": 52, "height": 61},
        "role": "operator-label",
    },
    {
        "id": "eq-yhat",
        "equation_id": "eq_yhat",
        "latex_source": r"\hat{y}",
        "color": COLORS["navy"],
        "position": {"left": 1457, "top": 116, "width": 59, "height": 54},
        "role": "predicted-measurement-label",
    },
    {
        "id": "eq-y",
        "equation_id": "eq_y",
        "latex_source": r"y",
        "color": COLORS["navy"],
        "position": {"left": 1471, "top": 651, "width": 35, "height": 48},
        "role": "observed-measurement-label",
    },
    {
        "id": "eq-loss",
        "equation_id": "eq_loss",
        "latex_source": r"\lVert\hat{y}-y\rVert_{2}^{2}",
        "color": COLORS["navy"],
        "position": {"left": 1441, "top": 392, "width": 94, "height": 39},
        "role": "measurement-residual",
    },
    {
        "id": "eq-objective",
        "equation_id": "eq_objective",
        "latex_source": (
            r"\theta^{\ast}=\operatorname*{arg\,min}_{\theta}"
            r"\left\lVert A G_{\theta}(z)-y\right\rVert_{2}^{2}"
        ),
        "color": COLORS["navy"],
        "position": {"left": 325, "top": 780, "width": 700, "height": 72},
        "role": "optimization-objective",
    },
    {
        "id": "eq-reconstruction",
        "equation_id": "eq_reconstruction",
        "latex_source": r"\hat{x}=G_{\theta^{\ast}}(z)",
        "color": COLORS["navy"],
        "position": {"left": 1068, "top": 780, "width": 277, "height": 72},
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


def _polygon(points: Sequence[Sequence[float]], fill: Any, stroke: str, width: float) -> dict[str, Any]:
    return {
        "points": [[float(x), float(y)] for x, y in points],
        "fill": fill,
        "line": {"style": "solid", "fill": stroke, "width": width},
    }


def _gradient(start: str, end: str, angle: float = 0) -> dict[str, Any]:
    return {
        "type": "gradient",
        "gradientKind": "linear",
        "angleDeg": angle,
        "stops": [
            {"offset": 0, "color": start},
            {"offset": 100000, "color": end},
        ],
    }


def _network_layer(identifier: str, x: float, y: float, width: float, height: float, *, mirror: bool) -> dict[str, Any]:
    depth = 10.0
    if mirror:
        face = [[x + depth, y + 5], [x + width + depth, y], [x + width + depth, y + height], [x + depth, y + height - 5]]
        top = [[x, y], [x + width, y - 5], [x + width + depth, y], [x + depth, y + 5]]
        side = [[x, y], [x + depth, y + 5], [x + depth, y + height - 5], [x, y + height - 10]]
    else:
        face = [[x, y], [x + width, y + 5], [x + width, y + height - 5], [x, y + height]]
        top = [[x, y], [x + depth, y - 6], [x + width + depth, y - 1], [x + width, y + 5]]
        side = [[x + width, y + 5], [x + width + depth, y - 1], [x + width + depth, y + height - 11], [x + width, y + height - 5]]
    return {
        "id": identifier,
        "face": _polygon(
            face,
            _gradient("#4F4A87", "#AAA7D1", 0 if mirror else 180),
            "#3F3B75",
            1.5,
        ),
        "top": _polygon(top, "#DAD8EC", "#7772A8", 1.0),
        "side": _polygon(side, "#8681B4", "#504A85", 1.0),
        "shadow": "2px 4px 9px #312E5B/18",
    }


def build_network_layers() -> list[dict[str, Any]]:
    center = 341.0
    encoder = [
        (388, 28, 226),
        (422, 30, 194),
        (459, 31, 160),
        (496, 30, 126),
        (532, 24, 90),
    ]
    decoder = [
        (579, 24, 90),
        (615, 30, 126),
        (652, 31, 160),
        (689, 30, 194),
        (723, 28, 226),
    ]
    layers = [
        _network_layer(f"encoder-{index}", x, center - height / 2, width, height, mirror=False)
        for index, (x, width, height) in enumerate(encoder, start=1)
    ]
    layers.append(
        _network_layer("bottleneck", 558, center - 54 / 2, 17, 54, mirror=False)
    )
    layers.extend(
        _network_layer(f"decoder-{index}", x, center - height / 2, width, height, mirror=True)
        for index, (x, width, height) in enumerate(decoder, start=1)
    )
    return layers


def _signal_values(count: int, observed: bool) -> list[float]:
    raw: list[float] = []
    for index in range(count):
        t = index / (count - 1)
        shift = 0.012 if observed else 0.0
        value = (
            0.10 * math.sin(2 * math.pi * (5.0 * t + 0.06))
            + 0.76 * math.exp(-((t - 0.39 - shift) / 0.10) ** 2)
            - 0.20 * math.exp(-((t - 0.62) / 0.11) ** 2)
            + 0.07 * math.sin(2 * math.pi * (2.2 * t + (0.05 if observed else 0.0)))
        )
        if observed:
            value += 0.012 * math.sin(2 * math.pi * 13.0 * t)
        raw.append(value)
    minimum = min(raw)
    span = max(raw) - minimum
    return [(value - minimum) / span for value in raw]


def _plot(identifier: str, frame: Mapping[str, float], *, observed: bool) -> dict[str, Any]:
    left = frame["left"] + 14
    top = frame["top"] + 14
    width = frame["width"] - 28
    height = frame["height"] - 28
    grid_lines: list[dict[str, Any]] = []
    for index in range(1, 5):
        x = left + width * index / 5
        grid_lines.append({
            "id": f"{identifier}-grid-v-{index}",
            "points": [[x, top], [x, top + height]],
            "line": {"style": "solid", "fill": COLORS["grid"], "width": 1.2},
        })
    for index in range(1, 3):
        y = top + height * index / 3
        grid_lines.append({
            "id": f"{identifier}-grid-h-{index}",
            "points": [[left, y], [left + width, y]],
            "line": {"style": "solid", "fill": COLORS["grid"], "width": 1.2},
        })
    values = _signal_values(120, observed)
    curve = [
        [left + index * width / (len(values) - 1), top + height - value * height]
        for index, value in enumerate(values)
    ]
    return {
        "id": identifier,
        "grid_lines": grid_lines,
        "curves": [{
            "id": f"{identifier}-curve",
            "points": curve,
            "line": {"style": "solid", "fill": COLORS["navy"], "width": 3.2},
        }],
    }


def build_spec(example_root: Path) -> dict[str, Any]:
    candidate = example_root / CANDIDATE_RELATIVE_PATH
    selection = example_root / SELECTION_RELATIVE_PATH
    if not candidate.is_file() or not selection.is_file():
        raise FileNotFoundError("candidate C and its hash-bound selection record are required")
    with Image.open(candidate) as image:
        if image.size != (CANVAS_WIDTH, CANVAS_HEIGHT):
            raise ValueError(f"candidate C must be {CANVAS_WIDTH}x{CANVAS_HEIGHT}; got {image.size}")

    frames = [
        {
            "id": "measurement-panel",
            "geometry": "roundRect",
            "position": {"left": 1334, "top": 100, "width": 306, "height": 624},
            "fill": COLORS["panel"],
            "line": {"style": "dashed", "fill": "#5D8FC6", "width": 3.2},
            "radius": 26,
        },
        {
            "id": "noise-frame",
            "geometry": "roundRect",
            "position": {"left": 40, "top": 214, "width": 228, "height": 230},
            "fill": "transparent",
            "line": {"style": "solid", "fill": COLORS["navy"], "width": 3.4},
            "radius": 15,
        },
        {
            "id": "generator-frame",
            "geometry": "roundRect",
            "position": {"left": 366, "top": 191, "width": 386, "height": 296},
            "fill": COLORS["generator"],
            "line": {"style": "solid", "fill": COLORS["purple"], "width": 3.4},
            "radius": 20,
            "shadow": "2px 5px 15px #3F2C60/10",
        },
        {
            "id": "reconstruction-frame",
            "geometry": "roundRect",
            "position": {"left": 829, "top": 220, "width": 231, "height": 234},
            "fill": "transparent",
            "line": {"style": "solid", "fill": COLORS["teal"], "width": 3.4},
            "radius": 14,
        },
        {
            "id": "operator-frame",
            "geometry": "roundRect",
            "position": {"left": 1137, "top": 279, "width": 117, "height": 114},
            "fill": COLORS["operator"],
            "line": {"style": "solid", "fill": COLORS["orange"], "width": 3.0},
            "radius": 15,
            "shadow": "2px 4px 10px #7B4A00/10",
        },
        {
            "id": "predicted-frame",
            "geometry": "roundRect",
            "position": {"left": 1365, "top": 182, "width": 245, "height": 130},
            "fill": "#FFFFFF",
            "line": {"style": "solid", "fill": COLORS["navy"], "width": 3.0},
            "radius": 12,
        },
        {
            "id": "loss-node",
            "geometry": "ellipse",
            "position": {"left": 1434, "top": 363, "width": 108, "height": 107},
            "fill": "#FFFFFF",
            "line": {"style": "solid", "fill": COLORS["navy"], "width": 3.0},
        },
        {
            "id": "observed-frame",
            "geometry": "roundRect",
            "position": {"left": 1365, "top": 518, "width": 245, "height": 128},
            "fill": "#FFFFFF",
            "line": {"style": "solid", "fill": COLORS["navy"], "width": 3.0},
            "radius": 12,
        },
    ]

    connectors = [
        {
            "id": "flow-z-generator",
            "source_id": "noise-frame",
            "target_id": "generator-frame",
            "points": [[268, 330], [358, 330]],
            "line": {"style": "solid", "fill": COLORS["navy"], "width": 4.0},
            "head": "triangle",
            "relation_type": "generator-input",
        },
        {
            "id": "flow-generator-reconstruction",
            "source_id": "generator-frame",
            "target_id": "reconstruction-frame",
            "points": [[752, 330], [821, 330]],
            "line": {"style": "solid", "fill": COLORS["navy"], "width": 4.0},
            "head": "triangle",
            "relation_type": "reconstruction",
        },
        {
            "id": "flow-reconstruction-operator",
            "source_id": "reconstruction-frame",
            "target_id": "operator-frame",
            "points": [[1060, 330], [1129, 330]],
            "line": {"style": "solid", "fill": COLORS["navy"], "width": 4.0},
            "head": "triangle",
            "relation_type": "forward-model-input",
        },
        {
            "id": "flow-operator-predicted",
            "source_id": "operator-frame",
            "target_id": "predicted-frame",
            "points": [[1254, 330], [1328, 330], [1328, 247], [1357, 247]],
            "line": {"style": "solid", "fill": COLORS["navy"], "width": 4.0},
            "head": "triangle",
            "relation_type": "predicted-measurement",
        },
        {
            "id": "flow-predicted-loss",
            "source_id": "predicted-frame",
            "target_id": "loss-node",
            "points": [[1488, 312], [1488, 355]],
            "line": {"style": "solid", "fill": COLORS["navy"], "width": 3.4},
            "head": "triangle",
            "relation_type": "residual-input",
        },
        {
            "id": "flow-observed-loss",
            "source_id": "observed-frame",
            "target_id": "loss-node",
            "points": [[1488, 518], [1488, 478]],
            "line": {"style": "solid", "fill": COLORS["navy"], "width": 3.4},
            "head": "triangle",
            "relation_type": "residual-input",
        },
        {
            "id": "feedback-optimize-generator",
            "source_id": "loss-node",
            "target_id": "generator-frame",
            "points": [[1434, 417], [1335, 417], [1335, 668], [568, 668], [568, 495]],
            "line": {"style": "dashed", "fill": COLORS["purple"], "width": 4.0},
            "head": "triangle",
            "relation_type": "parameter-optimization",
        },
    ]

    image_modules = [
        {
            "id": "noise-raster-atom",
            "asset": "noise.png",
            "position": APPROVED_RASTER_ATOMS["noise"]["target"],
            "fit": "cover",
            "geometry": "roundRect",
            "radius": 12,
            "alt": APPROVED_RASTER_ATOMS["noise"]["description"],
            "scientific_data": False,
            "replaceable": True,
        },
        {
            "id": "reconstruction-raster-atom",
            "asset": "reconstruction.png",
            "position": APPROVED_RASTER_ATOMS["reconstruction"]["target"],
            "fit": "cover",
            "geometry": "roundRect",
            "radius": 10,
            "alt": APPROVED_RASTER_ATOMS["reconstruction"]["description"],
            "scientific_data": False,
            "replaceable": True,
        },
    ]

    predicted_frame = next(item["position"] for item in frames if item["id"] == "predicted-frame")
    observed_frame = next(item["position"] for item in frames if item["id"] == "observed-frame")

    return {
        "schema_version": "1.0",
        "figure_id": FIGURE_ID,
        "status": "AWAITING_FINAL_RESEARCHER_REVIEW",
        "canvas": {"width": CANVAS_WIDTH, "height": CANVAS_HEIGHT, "background": COLORS["background"]},
        "visual_reference": {
            "path": "../candidates/C-presentation.png",
            "sha256": sha256_file(candidate),
            "width": CANVAS_WIDTH,
            "height": CANVAS_HEIGHT,
            "role": "selected visual reference; never embedded as a whole-canvas background",
        },
        "selection": {
            "path": "../candidate_selection_c_only.json",
            "sha256": sha256_file(selection),
            "final_scientific_approval": None,
        },
        "colors": COLORS,
        "image_modules": image_modules,
        "frames": frames,
        "network_layers": build_network_layers(),
        "plot_paths": [
            _plot("predicted-plot", predicted_frame, observed=False),
            _plot("observed-plot", observed_frame, observed=True),
        ],
        "connectors": connectors,
        "labels": [
            {
                "id": "feedback-caption",
                "text": "optimize θ",
                "position": {"left": 841, "top": 680, "width": 170, "height": 30},
                "font_size": 21,
                "font_family": "Arial",
                "color": COLORS["purple"],
                "align": "center",
            }
        ],
        "equation_objects": [
            {**equation, "asset": f"{equation['equation_id']}.svg"}
            for equation in EQUATIONS
        ],
        "editability_contract": {
            "whole_canvas_raster": False,
            "approved_raster_atom_count": 2,
            "raster_atoms": ["noise-raster-atom", "reconstruction-raster-atom"],
            "native_or_vector": ["frames", "network layers", "plot paths", "connectors", "labels", "equations"],
            "latex_is_authoritative": True,
            "pptx_equations_are_vector_objects_not_character_editable": True,
            "drawio_role": "STRUCTURAL_EDITING_VIEW",
            "pdf_role": "MIXED_MEDIA_PREVIEW_EXPORT",
        },
        "validation_scope": "File structure, approved raster boundaries, topology, and formula provenance; not scientific correctness or final approval.",
    }


def _write_equation_sources(source_dir: Path, math_dir: Path) -> list[dict[str, Any]]:
    tex_blocks: list[str] = []
    manifest_equations: list[dict[str, Any]] = []
    math_dir.mkdir(parents=True, exist_ok=True)
    for equation in EQUATIONS:
        latex_source = str(equation["latex_source"])
        tex_blocks.append(f"% equation-id: {equation['equation_id']}\n\\[\n{latex_source}\n\\]")
        output_path = math_dir / str(equation["asset"] if "asset" in equation else f"{equation['equation_id']}.svg")
        render_record = {
            "equation_id": equation["equation_id"],
            "latex_source": latex_source,
            "role": equation["role"],
            "paper_source": {"kind": "synthetic-public-demo", "reference": "Deep Image Prior principle"},
            "display_mode": "display" if equation["role"] in {"optimization-objective", "reconstruction-equation"} else "inline",
            "anchor_id": equation["id"],
            "alignment": "center",
            "style_role": equation["role"],
            "platform_render_policy": {"svg": "vector-paths", "pptx": "vector-svg", "drawio": "latex-metadata-plus-text"},
            "checksum": sha256_text(latex_source),
        }
        result = render_latex(render_record, output_path)
        if result.get("status") != "VERIFIED":
            result = render_mathjax(render_record, output_path)
        if result.get("status") != "VERIFIED" or not output_path.is_file():
            raise RuntimeError(f"equation render failed for {equation['equation_id']}: {result}")
        _recolor_svg(output_path, str(equation["color"]))
        manifest_equations.append(render_record)
    write_text(source_dir / "equations.tex", "\n\n".join(tex_blocks) + "\n")
    write_json(
        source_dir / "equation_manifest.json",
        {"schema_version": "1.0", "authoritative_tex": "equations.tex", "equations": manifest_equations},
    )
    return manifest_equations


def _recolor_svg(path: Path, color: str) -> None:
    tree = ET.parse(path)
    root = tree.getroot()
    root.set("style", f"color:{color};fill:{color}")
    for element in root.iter():
        if element.tag.endswith("path"):
            fill = element.get("fill")
            if not fill or fill.lower() in {"#000", "#000000", "black", "currentcolor"}:
                element.set("fill", color)
    tree.write(path, encoding="unicode", xml_declaration=True)


def _crop_assets(candidate: Path, output_dir: Path) -> list[dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    with Image.open(candidate) as source:
        source = source.convert("RGB")
        for name, policy in APPROVED_RASTER_ATOMS.items():
            box = tuple(int(value) for value in policy["crop_box"])
            crop = source.crop(box)
            output = output_dir / f"{name}.png"
            crop.save(output, format="PNG", optimize=False, compress_level=9)
            records.append({
                "id": name,
                "path": f"assets/{name}.png",
                "source_crop_box": list(box),
                "width": crop.width,
                "height": crop.height,
                "sha256": sha256_file(output),
                "target": policy["target"],
                "description": policy["description"],
                "scientific_data": False,
                "replaceable": True,
            })
    return records


def _points_path(points: Sequence[Sequence[float]]) -> str:
    return " ".join(
        ("M" if index == 0 else "L") + f" {point[0]:.2f} {point[1]:.2f}"
        for index, point in enumerate(points)
    )


def _data_uri(path: Path, media_type: str) -> str:
    return f"data:{media_type};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def _svg_fill(fill: Any, gradient_ids: dict[str, str], defs: list[str], key: str) -> str:
    if not isinstance(fill, Mapping) or fill.get("type") != "gradient":
        return str(fill)
    gradient_id = f"gradient-{key}"
    gradient_ids[key] = gradient_id
    stops = fill.get("stops", [])
    stop_markup = "".join(
        f'<stop offset="{float(stop["offset"]) / 1000:.3f}%" stop-color="{html.escape(str(stop["color"]))}"/>'
        for stop in stops
    )
    angle = float(fill.get("angleDeg", 0)) % 360
    x2 = 100 if angle in {0, 180} else 0
    y2 = 0 if angle in {0, 180} else 100
    if angle == 180:
        x1, x2 = 100, 0
    else:
        x1 = 0
    defs.append(
        f'<linearGradient id="{gradient_id}" x1="{x1}%" y1="0%" x2="{x2}%" y2="{y2}%">{stop_markup}</linearGradient>'
    )
    return f"url(#{gradient_id})"


def render_svg(spec: Mapping[str, Any], asset_dir: Path, equation_dir: Path, output_path: Path) -> dict[str, Any]:
    defs = [
        '<filter id="soft-shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="2" dy="4" stdDeviation="4" flood-color="#1F2B44" flood-opacity="0.12"/></filter>',
        '<marker id="arrow-navy" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="12" markerHeight="12" orient="auto"><path d="M 0 1 L 11 6 L 0 11 z" fill="#0D2F6E"/></marker>',
        '<marker id="arrow-purple" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="12" markerHeight="12" orient="auto"><path d="M 0 1 L 11 6 L 0 11 z" fill="#5A258C"/></marker>',
    ]
    gradient_ids: dict[str, str] = {}
    network_markup: list[str] = []
    for layer in spec["network_layers"]:
        group: list[str] = []
        for face_name in ("top", "side", "face"):
            face = layer[face_name]
            fill = _svg_fill(face["fill"], gradient_ids, defs, f"{layer['id']}-{face_name}")
            points = " ".join(f"{x:.2f},{y:.2f}" for x, y in face["points"])
            line = face["line"]
            group.append(
                f'<polygon id="{layer["id"]}-{face_name}" points="{points}" fill="{fill}" stroke="{line["fill"]}" stroke-width="{line["width"]}"/>'
            )
        network_markup.append(f'<g id="{layer["id"]}" data-editable="true" filter="url(#soft-shadow)">{"".join(group)}</g>')

    connector_markup: list[str] = []
    for connector in spec["connectors"]:
        line = connector["line"]
        marker = "arrow-purple" if line["fill"] == COLORS["purple"] else "arrow-navy"
        dash = ' stroke-dasharray="18 16"' if line["style"] == "dashed" else ""
        connector_markup.append(
            f'<path id="{connector["id"]}" data-source="{connector["source_id"]}" data-target="{connector["target_id"]}" d="{_points_path(connector["points"])}" fill="none" stroke="{line["fill"]}" stroke-width="{line["width"]}" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#{marker})"{dash}/>'
        )

    frame_markup: list[str] = []
    for frame in spec["frames"]:
        position = frame["position"]
        line = frame["line"]
        dash = ' stroke-dasharray="11 10"' if line["style"] == "dashed" else ""
        fill = "none" if frame["fill"] == "transparent" else frame["fill"]
        if frame["geometry"] == "ellipse":
            frame_markup.append(
                f'<ellipse id="{frame["id"]}" cx="{position["left"] + position["width"] / 2}" cy="{position["top"] + position["height"] / 2}" rx="{position["width"] / 2}" ry="{position["height"] / 2}" fill="{fill}" stroke="{line["fill"]}" stroke-width="{line["width"]}"/>'
            )
        else:
            radius = frame.get("radius", 0)
            shadow = ' filter="url(#soft-shadow)"' if frame.get("shadow") else ""
            frame_markup.append(
                f'<rect id="{frame["id"]}" x="{position["left"]}" y="{position["top"]}" width="{position["width"]}" height="{position["height"]}" rx="{radius}" fill="{fill}" stroke="{line["fill"]}" stroke-width="{line["width"]}"{dash}{shadow}/>'
            )

    image_markup: list[str] = []
    for item in spec["image_modules"]:
        position = item["position"]
        image_markup.append(
            f'<image id="{item["id"]}" data-approved-raster-atom="true" data-scientific-data="false" href="{_data_uri(asset_dir / item["asset"], "image/png")}" x="{position["left"]}" y="{position["top"]}" width="{position["width"]}" height="{position["height"]}" preserveAspectRatio="xMidYMid slice"/>'
        )

    plot_markup: list[str] = []
    for plot in spec["plot_paths"]:
        for line_item in plot["grid_lines"]:
            line = line_item["line"]
            plot_markup.append(
                f'<path id="{line_item["id"]}" d="{_points_path(line_item["points"])}" fill="none" stroke="{line["fill"]}" stroke-width="{line["width"]}"/>'
            )
        for curve in plot["curves"]:
            line = curve["line"]
            plot_markup.append(
                f'<path id="{curve["id"]}" data-editable="true" d="{_points_path(curve["points"])}" fill="none" stroke="{line["fill"]}" stroke-width="{line["width"]}" stroke-linecap="round" stroke-linejoin="round"/>'
            )

    equation_markup: list[str] = []
    for equation in spec["equation_objects"]:
        position = equation["position"]
        uri = _data_uri(equation_dir / equation["asset"], "image/svg+xml")
        equation_markup.append(
            f'<image id="{equation["id"]}" data-equation-id="{equation["equation_id"]}" data-latex="{html.escape(equation["latex_source"], quote=True)}" href="{uri}" x="{position["left"]}" y="{position["top"]}" width="{position["width"]}" height="{position["height"]}" preserveAspectRatio="xMidYMid meet"/>'
        )

    label_markup: list[str] = []
    for label in spec["labels"]:
        position = label["position"]
        label_markup.append(
            f'<text id="{label["id"]}" x="{position["left"] + position["width"] / 2}" y="{position["top"] + label["font_size"]}" text-anchor="middle" font-family="{label["font_family"]}" font-size="{label["font_size"]}" font-weight="600" fill="{label["color"]}">{html.escape(label["text"])}</text>'
        )

    content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" viewBox="0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}" role="img" aria-labelledby="title description">
  <title id="title">Deep Image Prior high-fidelity hybrid scientific schematic</title>
  <desc id="description">Candidate C composition with two replaceable synthetic raster atoms, native vector structure, and LaTeX-derived vector equations. Awaiting final researcher review.</desc>
  <metadata>{html.escape(json.dumps({"figure_id": FIGURE_ID, "status": spec["status"], "validation_scope": spec["validation_scope"]}, ensure_ascii=False))}</metadata>
  <defs>{''.join(defs)}</defs>
  <rect id="background" x="0" y="0" width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" fill="#FFFFFF"/>
  <g id="panel-layer">{frame_markup[0]}</g>
  <g id="connector-layer">{''.join(connector_markup)}</g>
  <g id="surface-layer">{''.join(frame_markup[1:])}</g>
  <g id="raster-atom-layer">{''.join(image_markup)}</g>
  <g id="native-network-layer">{''.join(network_markup)}</g>
  <g id="native-plot-layer">{''.join(plot_markup)}</g>
  <g id="label-layer">{''.join(label_markup)}</g>
  <g id="latex-equation-layer">{''.join(equation_markup)}</g>
</svg>
'''
    write_text(output_path, content)
    ET.parse(output_path)
    report = {
        "status": "VERIFIED_HYBRID",
        "path": "delivery/svg/master.svg",
        "sha256": sha256_file(output_path),
        "approved_raster_atom_count": 2,
        "whole_canvas_raster": False,
        "latex_vector_object_count": len(spec["equation_objects"]),
        "native_network_layer_count": len(spec["network_layers"]),
        "native_connector_count": len(spec["connectors"]),
        "semantic_editability": "major structure and modules",
        "raster_editability": "two atoms are replaceable/croppable but their internal pixels are not vector-editable",
    }
    write_json(output_path.parent / "svg_export_report.json", report)
    return report


def _mx_geometry(parent: ET.Element, position: Mapping[str, float]) -> None:
    ET.SubElement(parent, "mxGeometry", {
        "x": str(position["left"]),
        "y": str(position["top"]),
        "width": str(position["width"]),
        "height": str(position["height"]),
        "as": "geometry",
    })


def render_drawio(spec: Mapping[str, Any], output_path: Path) -> dict[str, Any]:
    model = ET.Element("mxGraphModel", {
        "dx": str(CANVAS_WIDTH),
        "dy": str(CANVAS_HEIGHT),
        "grid": "1",
        "gridSize": "10",
        "page": "1",
        "pageWidth": str(CANVAS_WIDTH),
        "pageHeight": str(CANVAS_HEIGHT),
    })
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})
    frame_ids = {item["id"] for item in spec["frames"]}
    for frame in spec["frames"]:
        line = frame["line"]
        fill = "none" if frame["fill"] == "transparent" else frame["fill"].lstrip("#")
        style = (
            "rounded=1;whiteSpace=wrap;html=1;"
            f"fillColor={fill};strokeColor={line['fill'].lstrip('#')};strokeWidth={line['width']};"
        )
        if frame["geometry"] == "ellipse":
            style += "ellipse;"
        if line["style"] == "dashed":
            style += "dashed=1;dashPattern=11 10;"
        cell = ET.SubElement(root, "mxCell", {
            "id": frame["id"], "value": "", "style": style,
            "vertex": "1", "parent": "1", "semanticType": "native-structure",
        })
        _mx_geometry(cell, frame["position"])
    for item in spec["image_modules"]:
        label = "Synthetic noise texture\n(replaceable raster atom)" if item["id"].startswith("noise") else "Synthetic reconstruction visual\n(replaceable raster atom)"
        style = "rounded=1;whiteSpace=wrap;html=1;fillColor=F4F6F8;strokeColor=9AA8BA;dashed=1;fontColor=526174;fontSize=16;align=center;verticalAlign=middle;"
        cell = ET.SubElement(root, "mxCell", {
            "id": item["id"], "value": label, "style": style,
            "vertex": "1", "parent": "1", "semanticType": "replaceable-raster-placeholder",
            "sourceAsset": item["asset"], "scientificData": "false",
        })
        _mx_geometry(cell, item["position"])
    for layer in spec["network_layers"]:
        points = layer["face"]["points"]
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        position = {"left": min(xs), "top": min(ys), "width": max(xs) - min(xs), "height": max(ys) - min(ys)}
        cell = ET.SubElement(root, "mxCell", {
            "id": layer["id"], "value": "", "style": "rounded=1;fillColor=7772A8;strokeColor=4F4A87;strokeWidth=1.5;",
            "vertex": "1", "parent": "1", "semanticType": "network-layer",
        })
        _mx_geometry(cell, position)
    for equation in spec["equation_objects"]:
        position = equation["position"]
        cell = ET.SubElement(root, "mxCell", {
            "id": equation["id"], "value": html.escape(equation["latex_source"]),
            "style": "text;html=1;strokeColor=none;fillColor=none;fontColor=0D2F6E;fontSize=20;align=center;verticalAlign=middle;",
            "vertex": "1", "parent": "1", "semanticType": "latex-equation",
            "equationId": equation["equation_id"], "latexSource": equation["latex_source"],
        })
        _mx_geometry(cell, position)
    for connector in spec["connectors"]:
        if connector["source_id"] not in frame_ids or connector["target_id"] not in frame_ids:
            raise ValueError(f"draw.io connector endpoint is not a frame: {connector['id']}")
        line = connector["line"]
        style = f"edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;strokeColor={line['fill'].lstrip('#')};strokeWidth={line['width']};"
        if line["style"] == "dashed":
            style += "dashed=1;dashPattern=18 16;"
        edge = ET.SubElement(root, "mxCell", {
            "id": connector["id"], "value": "", "style": style,
            "edge": "1", "parent": "1", "source": connector["source_id"], "target": connector["target_id"],
            "relationType": connector["relation_type"],
        })
        geometry = ET.SubElement(edge, "mxGeometry", {"relative": "1", "as": "geometry"})
        if len(connector["points"]) > 2:
            points = ET.SubElement(geometry, "Array", {"as": "points"})
            for x, y in connector["points"][1:-1]:
                ET.SubElement(points, "mxPoint", {"x": str(x), "y": str(y)})
    tree = ET.ElementTree(model)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output_path, encoding="unicode", xml_declaration=True)
    ET.parse(output_path)
    report = {
        "status": "STRUCTURAL_EDITING_VIEW",
        "path": "delivery/drawio/figure.drawio",
        "sha256": sha256_file(output_path),
        "native_edge_count": len(spec["connectors"]),
        "whole_canvas_raster": False,
        "high_fidelity_visual_master": False,
        "note": "draw.io preserves topology and replaceable module placeholders; use SVG or PPTX for the high-fidelity visual master.",
    }
    write_json(output_path.parent / "drawio_export_report.json", report)
    return report


def _portable_pptx_report(report_path: Path) -> None:
    if not report_path.is_file():
        raise FileNotFoundError(report_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    for key in ("spec", "source", "canonical_source"):
        if key in report:
            report[key] = "source/hybrid_figure.json"
    for key in ("output", "pptx", "preview", "layout", "inspection"):
        if key not in report:
            continue
        value = str(report[key])
        name = Path(value).name
        report[key] = f"delivery/pptx/{name}"
    write_json(report_path, report)


def _run_pptx_export(spec_path: Path, asset_dir: Path, equation_dir: Path, output_dir: Path) -> dict[str, Any]:
    node = os.environ.get("RUNTIME_NODE")
    modules = os.environ.get("RUNTIME_NODE_MODULES")
    if not node or not modules:
        raise RuntimeError("RUNTIME_NODE and RUNTIME_NODE_MODULES are required for the hybrid PPTX")
    script = Path(__file__).resolve().with_name("export_deep_image_prior_c_hybrid_pptx.mjs")
    command = [
        node, str(script),
        "--spec", str(spec_path),
        "--asset-dir", str(asset_dir),
        "--equation-dir", str(equation_dir),
        "--output-dir", str(output_dir),
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=240, env=dict(os.environ))
    if result.returncode != 0:
        raise RuntimeError(f"hybrid PPTX export failed:\n{result.stdout[-2000:]}\n{result.stderr[-4000:]}")
    report_path = output_dir / "pptx_artifact_report.json"
    _portable_pptx_report(report_path)
    return json.loads(report_path.read_text(encoding="utf-8"))


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


def _export_pdf(pptx_path: Path, output_dir: Path, soffice: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    # A private profile prevents an already-running desktop LibreOffice process
    # from silently swallowing the headless conversion request.
    with tempfile.TemporaryDirectory(prefix="hybrid-soffice-") as profile_dir:
        profile_uri = Path(profile_dir).resolve().as_uri()
        result = subprocess.run(
            [
                soffice,
                f"-env:UserInstallation={profile_uri}",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(output_dir),
                str(pptx_path),
            ],
            capture_output=True,
            text=True,
            timeout=240,
        )
    generated = output_dir / "figure.pdf"
    if result.returncode != 0 or not generated.is_file():
        raise RuntimeError(f"LibreOffice PDF conversion failed:\n{result.stdout[-2000:]}\n{result.stderr[-4000:]}")
    publication = output_dir / "publication.pdf"
    shutil.copyfile(generated, publication)
    generated.unlink()
    reader = PdfReader(publication)
    if len(reader.pages) != 1:
        raise ValueError("hybrid PDF must contain exactly one page")
    write_json(output_dir / "pdf_export_report.json", {
        "status": "VERIFIED_HYBRID_PREVIEW",
        "path": "delivery/pdf/publication.pdf",
        "sha256": sha256_file(publication),
        "page_count": 1,
        "role": "MIXED_MEDIA_PREVIEW_EXPORT",
        "semantic_editability": False,
        "scientific_validation": False,
    })
    return publication


def _render_preview(pdf_path: Path, output_path: Path, pdftoppm: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prefix = output_path.with_suffix("")
    result = subprocess.run(
        [pdftoppm, "-png", "-singlefile", "-r", "144", str(pdf_path), str(prefix)],
        capture_output=True,
        text=True,
        timeout=180,
    )
    generated = prefix.with_suffix(".png")
    if result.returncode != 0 or not generated.is_file():
        raise RuntimeError(f"PDF preview render failed:\n{result.stdout[-1000:]}\n{result.stderr[-2000:]}")


def validate_package(output_dir: Path) -> dict[str, Any]:
    spec_path = output_dir / "source" / "hybrid_figure.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    svg_path = output_dir / "delivery" / "svg" / "master.svg"
    svg = ET.parse(svg_path).getroot()
    hrefs = [
        element.get("href") or element.get("{http://www.w3.org/1999/xlink}href") or ""
        for element in svg.findall(".//{http://www.w3.org/2000/svg}image")
    ]
    raster_hrefs = [value for value in hrefs if value.startswith("data:image/png;base64,")]
    vector_hrefs = [value for value in hrefs if value.startswith("data:image/svg+xml;base64,")]
    external_hrefs = [value for value in hrefs if not value.startswith("data:")]
    if len(raster_hrefs) != 2 or len(vector_hrefs) != 9 or external_hrefs:
        raise ValueError("hybrid SVG must contain exactly two PNG atoms, nine SVG equations, and no external images")

    pptx_path = output_dir / "delivery" / "pptx" / "figure.pptx"
    with zipfile.ZipFile(pptx_path) as archive:
        media = [name for name in archive.namelist() if name.startswith("ppt/media/")]
        raster_media = [
            name
            for name in media
            if name.lower().endswith((".png", ".jpg", ".jpeg"))
            and archive.getinfo(name).file_size > 1000
        ]
        svg_fallback_media = [
            name
            for name in media
            if name.lower().endswith(".png")
            and archive.getinfo(name).file_size <= 1000
        ]
        vector_media = [name for name in media if name.lower().endswith(".svg")]
        notes = b"\n".join(
            archive.read(name)
            for name in archive.namelist()
            if name.startswith("ppt/notesSlides/") and name.endswith(".xml")
        )
    if len(raster_media) != 2 or len(vector_media) != 9 or len(svg_fallback_media) != 9:
        raise ValueError(
            "hybrid PPTX media mismatch: "
            f"substantive-raster={len(raster_media)} vector={len(vector_media)} "
            f"transparent-svg-fallback={len(svg_fallback_media)}"
        )
    if any(marker.encode("utf-8") in notes for marker in LOCAL_PATH_MARKERS):
        raise ValueError("hybrid PPTX notes contain a local absolute path")

    drawio_path = output_dir / "delivery" / "drawio" / "figure.drawio"
    drawio = ET.parse(drawio_path)
    edges = [item for item in drawio.findall(".//mxCell") if item.get("edge") == "1"]
    if len(edges) != 7:
        raise ValueError("hybrid draw.io must preserve seven directed edges")

    pdf_path = output_dir / "delivery" / "pdf" / "publication.pdf"
    if len(PdfReader(pdf_path).pages) != 1:
        raise ValueError("hybrid PDF must be a readable one-page preview")

    serialized_paths = [
        path
        for path in output_dir.rglob("*.json")
        if any(
            marker in path.read_text(encoding="utf-8")
            for marker in LOCAL_PATH_MARKERS
        )
    ]
    if serialized_paths:
        raise ValueError("portable JSON contains local absolute paths: " + ", ".join(path.name for path in serialized_paths))

    report = {
        "schema_version": "1.0",
        "status": "VERIFIED_HYBRID_REVIEW_DRAFT",
        "figure_id": spec["figure_id"],
        "validation_scope": spec["validation_scope"],
        "checks": {
            "candidate_reference_bound": spec["visual_reference"]["sha256"],
            "approved_raster_atom_count": 2,
            "whole_canvas_raster": False,
            "svg_embedded_png_count": len(raster_hrefs),
            "svg_vector_equation_count": len(vector_hrefs),
            "pptx_raster_picture_count": len(raster_media),
            "pptx_vector_equation_count": len(vector_media),
            "pptx_transparent_svg_fallback_count": len(svg_fallback_media),
            "drawio_directed_edge_count": len(edges),
            "pdf_page_count": 1,
            "portable_records": True,
        },
        "claims": {
            "svg": "high-fidelity hybrid visual master; major structure and modules editable",
            "pptx": "high-fidelity hybrid with two replaceable raster atoms and vector equations",
            "drawio": "structural editing view; not the high-fidelity visual master",
            "pdf": "mixed-media preview/export; no semantic-editability claim",
            "scientific_correctness": "not automated; final researcher approval remains pending",
        },
        "artifacts": {
            "source": {"path": "source/hybrid_figure.json", "sha256": sha256_file(spec_path)},
            "svg": {"path": "delivery/svg/master.svg", "sha256": sha256_file(svg_path)},
            "pptx": {"path": "delivery/pptx/figure.pptx", "sha256": sha256_file(pptx_path)},
            "drawio": {"path": "delivery/drawio/figure.drawio", "sha256": sha256_file(drawio_path)},
            "pdf": {"path": "delivery/pdf/publication.pdf", "sha256": sha256_file(pdf_path)},
            "preview": {"path": "preview.png", "sha256": sha256_file(output_dir / "preview.png")},
        },
        "final_scientific_approval": None,
    }
    write_json(output_dir / "validation" / "hybrid_validation_report.json", report)
    return report


def build_package(
    example_root: Path,
    output_dir: Path,
    *,
    soffice: str | None,
    pdftoppm: str | None,
) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing hybrid output: {output_dir}")
    candidate = example_root / CANDIDATE_RELATIVE_PATH
    spec = build_spec(example_root)
    source_dir = output_dir / "source"
    asset_dir = source_dir / "assets"
    equation_dir = source_dir / "math"
    source_dir.mkdir(parents=True)
    asset_records = _crop_assets(candidate, asset_dir)
    write_json(source_dir / "asset_manifest.json", {
        "schema_version": "1.0",
        "visual_reference_sha256": spec["visual_reference"]["sha256"],
        "whole_canvas_raster": False,
        "approved_raster_atoms": asset_records,
    })
    _write_equation_sources(source_dir, equation_dir)
    spec_path = source_dir / "hybrid_figure.json"
    write_json(spec_path, spec)

    svg_dir = output_dir / "delivery" / "svg"
    svg_dir.mkdir(parents=True)
    render_svg(spec, asset_dir, equation_dir, svg_dir / "master.svg")
    drawio_dir = output_dir / "delivery" / "drawio"
    render_drawio(spec, drawio_dir / "figure.drawio")
    pptx_dir = output_dir / "delivery" / "pptx"
    pptx_dir.mkdir(parents=True)
    _run_pptx_export(spec_path, asset_dir, equation_dir, pptx_dir)

    soffice_path = _resolve_executable(
        soffice,
        ("soffice", "/Applications/LibreOffice.app/Contents/MacOS/soffice"),
    )
    if not soffice_path:
        raise RuntimeError("LibreOffice soffice is required to create the high-fidelity PDF preview")
    pdf_path = _export_pdf(pptx_dir / "figure.pptx", output_dir / "delivery" / "pdf", soffice_path)
    pdftoppm_path = _resolve_executable(pdftoppm, ("pdftoppm",))
    if not pdftoppm_path:
        raise RuntimeError("pdftoppm is required to render the review preview")
    _render_preview(pdf_path, output_dir / "preview.png", pdftoppm_path)
    report = validate_package(output_dir)
    write_json(output_dir / "delivery" / "delivery_manifest.json", {
        "schema_version": "1.0",
        "figure_id": FIGURE_ID,
        "status": report["status"],
        "canonical_source": "source/hybrid_figure.json",
        "validation_report": "validation/hybrid_validation_report.json",
        "formats": [
            {"format": "svg", "path": "delivery/svg/master.svg", "status": "VERIFIED_HYBRID", "editability": "major structure plus replaceable raster atoms"},
            {"format": "pptx", "path": "delivery/pptx/figure.pptx", "status": "VERIFIED_HYBRID", "editability": "native modules plus vector equations and two replaceable raster atoms"},
            {"format": "drawio", "path": "delivery/drawio/figure.drawio", "status": "STRUCTURAL_EDITING_VIEW", "editability": "topology and module placeholders"},
            {"format": "pdf", "path": "delivery/pdf/publication.pdf", "status": "VERIFIED_HYBRID_PREVIEW", "editability": "no semantic-editability claim"},
        ],
        "final_scientific_approval": None,
    })
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--example-root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "examples" / "deep_image_prior",
    )
    parser.add_argument("--soffice")
    parser.add_argument("--pdftoppm")
    args = parser.parse_args()
    report = build_package(
        args.example_root.resolve(),
        args.output_dir.resolve(),
        soffice=args.soffice,
        pdftoppm=args.pdftoppm,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
