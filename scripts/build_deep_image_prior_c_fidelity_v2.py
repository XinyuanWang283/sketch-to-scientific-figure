#!/usr/bin/env python3
"""Build Candidate C fidelity v2 without flattening the editable figure.

The selected Candidate C PNG is a hash-bound visual reference. The builder
uses it only for two explicitly approved replaceable raster atoms, two local
synthetic plot-curve fits, and region-level visual QA. Generator layers,
frames, connectors, labels, and equations remain vector objects. Automated
checks never create scientific or publication approval.
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
import statistics
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps, ImageStat
from pypdf import PdfReader

import build_deep_image_prior_c_region_fidelity as fidelity
import build_deep_image_prior_c_segmented_native as native
import render_equations
from figure_artifacts import write_json
from workflow_v3 import write_text


CANVAS_WIDTH = native.CANVAS_WIDTH
CANVAS_HEIGHT = native.CANVAS_HEIGHT
ARROW_HEAD_COUNT = 7
FIGURE_ID = "deep-image-prior-c-fidelity-v2"
CANDIDATE_RELATIVE_PATH = native.CANDIDATE_RELATIVE_PATH
COLORS = native.COLORS
REGIONS = native.REGIONS
LOCAL_PATH_MARKERS = native.LOCAL_PATH_MARKERS
APPROVED_RASTER_ATOMS = fidelity.APPROVED_RASTER_ATOMS
REFERENCE_CASE_MANIFEST = "reference_case_v0_1.json"
REFERENCE_CASE_ID = "deep-image-prior-synthetic-v0.1"
DELIVERY_REVISION = "fidelity-v2"
RECIPE_ID = "deep-image-prior-c-fidelity-v2"
CANDIDATE_PROVENANCE_STATUS = "repository_registered_operator_attested"

FACE_PALETTES = [
    ("#5E5A93", "#736CAE", "#958BC3"),
    ("#736CAE", "#958BC3", "#B3AAD4"),
    ("#958BC3", "#B3AAD4", "#C0B8DF"),
    ("#B3AAD4", "#C0B8DF", "#D8D1EB"),
    ("#C0B8DF", "#D8D1EB", "#EEEAF5"),
    ("#958BC3", "#B3AAD4", "#D8D1EB"),
]
LEVEL_BY_LAYER = [0, 1, 2, 3, 4, 5, 4, 3, 2, 1, 0]

EQUATION_DEFINITIONS = [
    {
        "id": "eq-z", "equation_id": "eq_z", "latex_source": r"z",
        "render_latex_source": r"{\color[HTML]{0D2F6E}z}",
        "fit_box": [132, 145, 52, 45], "align": "center", "role": "input-label",
    },
    {
        "id": "eq-generator", "equation_id": "eq_generator", "latex_source": r"G_{\theta}",
        "render_latex_source": r"{\color[HTML]{5A258C}G_{\theta}}",
        "fit_box": [524, 211, 80, 44], "align": "center", "role": "generator-label",
    },
    {
        "id": "eq-xhat", "equation_id": "eq_xhat", "latex_source": r"\hat{x}",
        "render_latex_source": r"{\color[HTML]{0B6262}\hat{x}}",
        "fit_box": [911, 145, 68, 54], "align": "center", "role": "reconstruction-label",
    },
    {
        "id": "eq-operator", "equation_id": "eq_operator", "latex_source": r"A",
        "render_latex_source": r"{\color[HTML]{C46A00}A}",
        "fit_box": [1166, 298, 60, 58], "align": "center", "role": "operator-label",
    },
    {
        "id": "eq-yhat", "equation_id": "eq_yhat", "latex_source": r"\hat{y}",
        "render_latex_source": r"{\color[HTML]{0D2F6E}\hat{y}}",
        "fit_box": [1448, 116, 80, 55], "align": "center", "role": "predicted-measurement-label",
    },
    {
        "id": "eq-y", "equation_id": "eq_y", "latex_source": r"y",
        "render_latex_source": r"{\color[HTML]{0D2F6E}y}",
        "fit_box": [1464, 652, 50, 48], "align": "center", "role": "observed-measurement-label",
    },
    {
        "id": "eq-loss", "equation_id": "eq_loss", "latex_source": r"\lVert\cdot\rVert_{2}^{2}",
        "render_latex_source": r"{\color[HTML]{0D2F6E}\lVert\cdot\rVert_{2}^{2}}",
        "fit_box": [1439, 394, 98, 42], "align": "center", "role": "measurement-residual",
    },
    {
        "id": "eq-objective", "equation_id": "eq_objective",
        "latex_source": (
            r"\theta^{\ast}\;=\;\operatorname*{arg\,min}_{\theta}"
            r"\left\lVert A\,G_{\theta}(z)-y\right\rVert_{2}^{2}"
        ),
        "render_latex_source": (
            r"{\color[HTML]{000000}"
            r"{\color[HTML]{5A258C}\theta^{\ast}}\;=\;"
            r"\operatorname*{arg\,min}_{{\color[HTML]{5A258C}\theta}}"
            r"\left\lVert A\,{\color[HTML]{5A258C}G_{\theta}}"
            r"({\color[HTML]{0D2F6E}z})-{\color[HTML]{5A258C}y}"
            r"\right\rVert_{2}^{2}}"
        ),
        "fit_box": [326, 769, 647, 94], "align": "left", "role": "optimization-objective",
        "expected_optical_bbox": [328, 769, 599, 89],
    },
    {
        "id": "eq-reconstruction", "equation_id": "eq_reconstruction",
        "latex_source": r"\hat{x}\;=\;G_{\theta^{\ast}}(z)",
        "render_latex_source": (
            r"{\color[HTML]{000000}{\color[HTML]{0B6262}\hat{x}}\;=\;"
            r"{\color[HTML]{5A258C}G_{\theta^{\ast}}}({\color[HTML]{0D2F6E}z})}"
        ),
        "fit_box": [1067, 785, 251, 50], "align": "left", "role": "reconstruction-equation",
        "expected_optical_bbox": [1067, 785, 251, 50],
    },
]

COLOR_TEX_TEMPLATE = r"""\documentclass[12pt]{article}
\usepackage[active,tightpage]{preview}
\usepackage{amsmath,amssymb,bm}
\usepackage{xcolor}
\PreviewEnvironment{equation*}
\setlength\PreviewBorder{2pt}
\begin{document}
\begin{equation*}
%s
\end{equation*}
\end{document}
"""


def sha256_file(path: Path) -> str:
    return native.sha256_file(path)


def _resolve_case_file(example_root: Path, relative_path: str, *, label: str) -> Path:
    raw = Path(relative_path)
    if raw.is_absolute() or "\\" in relative_path or any(
        part in {"", ".", ".."} for part in relative_path.split("/")
    ):
        raise ValueError(f"{label} must use a portable case-relative path")
    try:
        root = example_root.resolve(strict=True)
        resolved = (root / raw).resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as error:
        raise ValueError(f"{label} escapes the reference case or does not exist") from error
    if not resolved.is_file():
        raise ValueError(f"{label} must resolve to a regular file")
    return resolved


def verify_reference_case_inputs(example_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Fail closed on the exact v0.1 Candidate C selection and approved region map."""
    manifest_path = example_root / REFERENCE_CASE_MANIFEST
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("the v0.1 reference-case manifest is missing or invalid") from error
    if (
        manifest.get("schema_version") != "1.0"
        or manifest.get("case_id") != REFERENCE_CASE_ID
        or manifest.get("delivery_revision") != DELIVERY_REVISION
    ):
        raise ValueError("unsupported fidelity-v2 reference-case manifest")
    selection = manifest.get("selection")
    if not isinstance(selection, Mapping) or any(
        selection.get(key) != expected
        for key, expected in {
            "slot": "C",
            "candidate_id": "C-presentation",
        }.items()
    ):
        raise ValueError("fidelity-v2 requires the exact selected Candidate C")
    candidates = manifest.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != 5:
        raise ValueError("reference case must contain exactly five active candidate records")
    if {item.get("slot") for item in candidates if isinstance(item, Mapping)} != set("ABCDE"):
        raise ValueError("reference case must contain active slots A through E")
    event_ids = [
        item.get("generation_event_id")
        for item in candidates
        if isinstance(item, Mapping)
    ]
    if len(event_ids) != 5 or any(not isinstance(item, str) or not item for item in event_ids):
        raise ValueError("every candidate requires a repository-local generation_event_id")
    if len(set(event_ids)) != 5:
        raise ValueError("candidate generation_event_id values must be unique")
    native_ids = [
        item.get("native_tool_call_id")
        for item in candidates
        if isinstance(item, Mapping) and item.get("native_tool_call_id") is not None
    ]
    if any(not isinstance(item, str) or not item for item in native_ids) or len(
        native_ids
    ) != len(set(native_ids)):
        raise ValueError("native tool-call IDs must be non-empty and unique when present")
    for item in candidates:
        assert isinstance(item, Mapping)
        path = _resolve_case_file(
            example_root, str(item.get("path")), label=f"candidate {item.get('slot')}"
        )
        if item.get("sha256") != sha256_file(path):
            raise ValueError(f"candidate {item.get('slot')} hash is stale")
        for field in ("candidate_id", "design_note", "registered_at"):
            if not isinstance(item.get(field), str) or not item.get(field):
                raise ValueError(f"candidate {item.get('slot')} is missing {field}")
        if item.get("provenance_status") != CANDIDATE_PROVENANCE_STATUS:
            raise ValueError(
                f"candidate {item.get('slot')} provenance_status must be "
                f"{CANDIDATE_PROVENANCE_STATUS}"
            )
    candidate_record = next(
        (
            item
            for item in manifest.get("candidates", [])
            if isinstance(item, Mapping) and item.get("slot") == "C"
        ),
        None,
    )
    if not isinstance(candidate_record, Mapping):
        raise ValueError("reference case is missing Candidate C")
    candidate = _resolve_case_file(
        example_root, str(candidate_record.get("path")), label="Candidate C"
    )
    if candidate_record.get("sha256") != sha256_file(candidate):
        raise ValueError("reference-case Candidate C record hash is stale")
    candidate_hash = sha256_file(candidate)
    if selection.get("sha256") != candidate_hash:
        raise ValueError("reference-case selection is not bound to Candidate C bytes")
    record = selection.get("record")
    if not isinstance(record, Mapping):
        raise ValueError("reference-case selection record is missing")
    selection_path = _resolve_case_file(
        example_root, str(record.get("path")), label="Candidate C selection record"
    )
    if record.get("sha256") != sha256_file(selection_path):
        raise ValueError("reference-case selection record hash is stale")
    parsed_selection = json.loads(selection_path.read_text(encoding="utf-8"))
    selected = parsed_selection.get("selected_candidate")
    if (
        parsed_selection.get("decision") != "APPROVE_IMAGEGEN_CANDIDATE"
        or parsed_selection.get("status") != "approved_for_editable_reconstruction"
        or parsed_selection.get("editable_reconstruction_authorized") is not True
        or parsed_selection.get("final_scientific_approval") is not None
        or not isinstance(selected, Mapping)
        or any(
            selected.get(key) != selection.get(key)
            for key in ("slot", "candidate_id", "sha256")
        )
    ):
        raise ValueError("Candidate C selection record is not an explicit hash-bound approval")
    region = manifest.get("approved_region_map")
    if not isinstance(region, Mapping):
        raise ValueError("reference case is missing its approved region map")
    region_path = _resolve_case_file(
        example_root, str(region.get("path")), label="approved region map"
    )
    if region.get("sha256") != sha256_file(region_path):
        raise ValueError("approved region-map hash is stale")
    region_approval = region.get("approval_record")
    if not isinstance(region_approval, Mapping):
        raise ValueError("reference case is missing the region-map approval record")
    approval_path = _resolve_case_file(
        example_root,
        str(region_approval.get("path")),
        label="region-map approval record",
    )
    if region_approval.get("sha256") != sha256_file(approval_path):
        raise ValueError("region-map approval-record hash is stale")
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    if (
        approval.get("decision") != "APPROVE_REGION_MAP_FOR_RECONSTRUCTION"
        or approval.get("case_id") != REFERENCE_CASE_ID
        or approval.get("delivery_revision") != DELIVERY_REVISION
        or approval.get("region_map_sha256") != region.get("sha256")
        or approval.get("recipe_id") != RECIPE_ID
        or approval.get("scientific_approval_created") is not False
    ):
        raise ValueError("region-map approval is not bound to the v0.1 reference case")
    reconstruction = manifest.get("reconstruction")
    if not isinstance(reconstruction, Mapping) or reconstruction.get("recipe_id") != RECIPE_ID:
        raise ValueError("reference case names an unsupported reconstruction recipe")
    approved_rasters = manifest.get("approved_raster_atoms")
    if not isinstance(approved_rasters, Mapping):
        raise ValueError("reference case is missing its approved raster-atom manifest")
    raster_manifest_path = _resolve_case_file(
        example_root,
        str(approved_rasters.get("path")),
        label="approved raster-atom manifest",
    )
    if approved_rasters.get("sha256") != sha256_file(raster_manifest_path):
        raise ValueError("approved raster-atom manifest hash is stale")
    review_record = approved_rasters.get("review_decision")
    if not isinstance(review_record, Mapping):
        raise ValueError("reference case is missing its raster-atom review decision")
    review_path = _resolve_case_file(
        example_root,
        str(review_record.get("path")),
        label="raster-atom review decision",
    )
    if review_record.get("sha256") != sha256_file(review_path):
        raise ValueError("raster-atom review decision hash is stale")
    approved_map = json.loads(region_path.read_text(encoding="utf-8"))
    return manifest, approved_map


def _gradient(colors: Sequence[str], angle: float) -> dict[str, Any]:
    offsets = [0, 55000, 100000] if len(colors) == 3 else [0, 100000]
    return {
        "type": "gradient",
        "gradientKind": "linear",
        "angleDeg": angle,
        "stops": [
            {"offset": offset, "color": color}
            for offset, color in zip(offsets, colors, strict=True)
        ],
    }


def build_selected_candidate_map(example_root: Path) -> dict[str, Any]:
    result = fidelity.build_selected_candidate_map(example_root)
    result["schema_version"] = "1.2"
    result["fidelity_version"] = "candidate-c-fidelity-v2"
    result["art_direction_notes"] = (
        "Preserve the hash-bound Candidate C region anchors. Use native gradient paint for the "
        "11 generator layers, smaller explicit arrows, colored intrinsic-aspect LaTeX, and two "
        "local reference-fitted synthetic plot paths. Keep exactly two replaceable raster atoms."
    )
    result["reference_fit_policy"] = {
        "scope": "two decorative synthetic signal glyphs only",
        "scientific_data": False,
        "whole_image_tracing": False,
        "method": "local navy-pixel median fit plus RDP simplification",
        "final_visual_approval": None,
        "final_scientific_approval": None,
    }
    return result


def validate_selected_candidate_map(
    selected_map: Mapping[str, Any],
    *,
    candidate_sha256: str,
    approved_map: Mapping[str, Any],
) -> dict[str, list[int]]:
    """Validate the exact case-specific eight-region conversion contract."""
    normalized = json.loads(json.dumps(selected_map, ensure_ascii=False))
    normalized_approved = json.loads(json.dumps(approved_map, ensure_ascii=False))
    if normalized != normalized_approved:
        raise ValueError("selected candidate map differs from the approved fidelity-v2 map")
    if selected_map.get("candidate_id") != "C-presentation" or selected_map.get(
        "image_hash"
    ) != candidate_sha256:
        raise ValueError("selected candidate map is not bound to Candidate C")
    if selected_map.get("bbox_format") != "xywh_source_pixels":
        raise ValueError("selected candidate map uses an unsupported bbox format")
    boxes = selected_map.get("major_region_bboxes")
    conversions = selected_map.get("region_conversions")
    output_ids = selected_map.get("region_output_ids")
    expected_regions = set(REGIONS)
    if not isinstance(boxes, Mapping) or set(boxes) != expected_regions:
        raise ValueError("selected candidate map must contain exactly eight declared regions")
    if not isinstance(conversions, Mapping) or set(conversions) != expected_regions:
        raise ValueError("region conversion policy must cover exactly the eight declared regions")
    if not isinstance(output_ids, Mapping) or set(output_ids) != expected_regions:
        raise ValueError("region output-ID mapping must cover exactly the eight declared regions")
    verified: dict[str, list[int]] = {}
    for region_id, expected_bbox in REGIONS.items():
        bbox = boxes.get(region_id)
        expected = list(expected_bbox)
        if not isinstance(bbox, (list, tuple)) or list(bbox) != expected:
            raise ValueError(f"approved bbox changed for region {region_id}")
        x, y, width, height = expected
        if min(x, y, width, height) < 0 or width <= 0 or height <= 0:
            raise ValueError(f"region {region_id} has an invalid bbox")
        if x + width > CANVAS_WIDTH or y + height > CANVAS_HEIGHT:
            raise ValueError(f"region {region_id} escapes the Candidate C canvas")
        conversion = conversions.get(region_id)
        if not isinstance(conversion, Mapping) or list(
            conversion.get("source_bbox", [])
        ) != expected:
            raise ValueError(f"region conversion bbox changed for {region_id}")
        native_ids = conversion.get("native_output_ids")
        if not isinstance(native_ids, list) or native_ids != output_ids.get(region_id):
            raise ValueError(f"region conversion output IDs changed for {region_id}")
        if not native_ids or len(native_ids) != len(set(native_ids)):
            raise ValueError(f"region {region_id} has missing or duplicate output IDs")
        verified[region_id] = expected
    return verified


def _is_curve_pixel(pixel: tuple[int, int, int]) -> bool:
    red, green, blue = pixel
    return (
        blue - red >= 28
        and blue - green >= 14
        and red < 110
        and green < 125
        and blue < 180
    )


def _perpendicular_distance(
    point: Sequence[float], start: Sequence[float], end: Sequence[float]
) -> float:
    x, y = point
    x1, y1 = start
    x2, y2 = end
    if x1 == x2 and y1 == y2:
        return math.hypot(x - x1, y - y1)
    numerator = abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1)
    return numerator / math.hypot(y2 - y1, x2 - x1)


def _rdp(points: Sequence[Sequence[float]], epsilon: float) -> list[list[float]]:
    if len(points) < 3:
        return [[float(x), float(y)] for x, y in points]
    distances = [
        _perpendicular_distance(point, points[0], points[-1])
        for point in points[1:-1]
    ]
    maximum = max(distances, default=0.0)
    if maximum <= epsilon:
        return [[float(points[0][0]), float(points[0][1])], [float(points[-1][0]), float(points[-1][1])]]
    index = distances.index(maximum) + 1
    return _rdp(points[: index + 1], epsilon)[:-1] + _rdp(points[index:], epsilon)


def _interpolated_y(points: Sequence[Sequence[float]], x: float) -> float:
    for left, right in zip(points, points[1:]):
        if left[0] <= x <= right[0]:
            span = right[0] - left[0]
            if span == 0:
                return float(left[1])
            fraction = (x - left[0]) / span
            return float(left[1] + fraction * (right[1] - left[1]))
    return float(points[-1][1])


def _extract_reference_curve(
    candidate: Image.Image,
    *,
    identifier: str,
    frame: Mapping[str, float],
    candidate_sha256: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Fit one editable polyline to a synthetic decorative plot glyph.

    This deliberately rejects any scientific-data mode. It is not a general
    chart digitizer and must not be reused to recover experimental values.
    """
    left = int(frame["left"])
    top = int(frame["top"])
    height = int(frame["height"])
    local_xs = list(range(14, 231))
    column_points: list[list[float]] = []
    missing: list[int] = []
    pixels = candidate.convert("RGB")
    for local_x in local_xs:
        absolute_x = left + local_x
        ys = [
            top + local_y
            for local_y in range(14, height - 14)
            if _is_curve_pixel(pixels.getpixel((absolute_x, top + local_y)))
        ]
        if ys:
            column_points.append([float(absolute_x), float(statistics.median(ys))])
        else:
            missing.append(absolute_x)
    coverage = len(column_points) / len(local_xs)
    if coverage < 0.98 or missing:
        raise ValueError(f"{identifier} curve coverage is {coverage:.3f}; missing columns: {missing[:8]}")
    smoothed: list[list[float]] = []
    for index, (x, _) in enumerate(column_points):
        window = column_points[max(0, index - 2): min(len(column_points), index + 3)]
        smoothed.append([x, float(statistics.median(point[1] for point in window))])
    simplified = _rdp(smoothed, 0.5)
    simplified = [
        [round(x * 4) / 4, round(y * 4) / 4]
        for x, y in simplified
    ]
    residuals = [
        abs(y - _interpolated_y(simplified, x))
        for x, y in smoothed
    ]
    fit = {
        "origin": "mechanically_fitted_from_hash_bound_selected_candidate",
        "candidate_sha256": candidate_sha256,
        "source_frame": [left, top, int(frame["width"]), height],
        "scientific_status": "synthetic_visual_only",
        "scientific_data": False,
        "reference_fit": True,
        "algorithm": "navy-pixel column median; five-column median filter; RDP epsilon 0.5 px",
        "coverage": round(coverage, 6),
        "source_column_count": len(column_points),
        "simplified_point_count": len(simplified),
        "median_vertical_error_px": round(statistics.median(residuals), 4),
        "max_vertical_error_px": round(max(residuals), 4),
        "human_review_required": True,
    }
    shape = {
        "id": f"{identifier}-curve",
        "type": "polyline",
        "points": simplified,
        "fill": "none",
        "stroke": COLORS["navy"],
        "stroke_width": 3.2,
        "linecap": "round",
        "linejoin": "round",
        "reference_fit": fit,
    }
    return shape, fit


def _plot_shapes(
    candidate: Image.Image,
    *,
    identifier: str,
    frame: Mapping[str, float],
    candidate_sha256: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    shapes: list[dict[str, Any]] = []
    for index, local_x in enumerate((14, 55, 96, 137, 178, 220), start=1):
        x = frame["left"] + local_x
        shapes.append(native._polyline(
            f"{identifier}-grid-v-{index}",
            [[x, frame["top"] + 12], [x, frame["top"] + frame["height"] - 12]],
            COLORS["grid"], 1.0, dash=[5, 5],
        ))
    for index, fraction in enumerate((0.25, 0.67), start=1):
        y = frame["top"] + frame["height"] * fraction
        shapes.append(native._polyline(
            f"{identifier}-grid-h-{index}",
            [[frame["left"] + 12, y], [frame["left"] + frame["width"] - 12, y]],
            COLORS["grid"], 1.0, dash=[5, 5],
        ))
    curve, fit = _extract_reference_curve(
        candidate,
        identifier=identifier,
        frame=frame,
        candidate_sha256=candidate_sha256,
    )
    shapes.append(curve)
    return shapes, fit


def _network_shapes() -> list[dict[str, Any]]:
    shapes = deepcopy(native._network_shapes())
    for shape in shapes:
        layer_index = int(shape["id"].split("-")[2]) - 1
        face_type = shape["id"].rsplit("-", 1)[-1]
        level = LEVEL_BY_LAYER[layer_index]
        mirror = layer_index >= 6
        if face_type == "face":
            shape["fill"] = _gradient(FACE_PALETTES[level], 180 if mirror else 0)
        elif face_type == "top":
            shape["fill"] = "#E6E2F1"
            shape["fill_opacity"] = 0.78
        else:
            shape["fill"] = "#7771A7"
            shape["fill_opacity"] = 0.88
    return shapes


def _connectors() -> list[dict[str, Any]]:
    raw = [
        ("flow-z-generator", "noise-frame", "generator-frame", [[268, 330], [358, 330]], COLORS["navy"], "solid", "generator-input"),
        ("flow-generator-reconstruction", "generator-frame", "reconstruction-frame", [[752, 330], [821, 330]], COLORS["navy"], "solid", "reconstruction"),
        ("flow-reconstruction-operator", "reconstruction-frame", "operator-frame", [[1060, 330], [1129, 330]], COLORS["navy"], "solid", "forward-model-input"),
        ("flow-operator-predicted", "operator-frame", "measurement-panel", [[1254, 330], [1327, 330]], COLORS["navy"], "solid", "predicted-measurement"),
        ("flow-predicted-loss", "predicted-frame", "loss-node", [[1488, 312], [1488, 355]], COLORS["navy"], "solid", "residual-input"),
        ("flow-observed-loss", "observed-frame", "loss-node", [[1488, 518], [1488, 478]], COLORS["navy"], "solid", "residual-input"),
        ("feedback-optimize-generator", "loss-node", "generator-frame", [[1334, 668], [568, 668], [568, 495]], COLORS["purple"], "dashed", "parameter-optimization"),
    ]
    connectors: list[dict[str, Any]] = []
    for identifier, source, target, points, color, style, relation in raw:
        residual = identifier in {"flow-predicted-loss", "flow-observed-loss"}
        shaft, head = native._arrow_geometry(
            points,
            length=12.0 if residual else 13.0,
            half_width=6.0 if residual else 6.5,
        )
        connectors.append({
            "id": identifier,
            "source_id": source,
            "target_id": target,
            "relation_type": relation,
            "shaft_points": shaft,
            "arrowhead_points": head,
            "stroke": color,
            "stroke_width": 3.4 if residual else 4.0,
            "style": style,
            "dash": [18, 16] if style == "dashed" else [],
            "linecap": "butt",
        })
    return connectors


def _render_colored_latex(
    definition: Mapping[str, Any], output_path: Path
) -> dict[str, Any]:
    latex = native._resolve_executable(None, ("latex", "/Library/TeX/texbin/latex"))
    dvisvgm = native._resolve_executable(None, ("dvisvgm", "/Library/TeX/texbin/dvisvgm"))
    if not latex or not dvisvgm:
        raise RuntimeError("latex and dvisvgm are required for the colored equation assets")
    record = {
        "equation_id": definition["equation_id"],
        "latex_source": definition["latex_source"],
        "checksum": native.sha256_text(definition["latex_source"]),
    }
    with tempfile.TemporaryDirectory(prefix="candidate-c-v2-equation-") as temporary:
        temporary_path = Path(temporary)
        tex_path = temporary_path / "equation.tex"
        write_text(tex_path, COLOR_TEX_TEMPLATE % definition["render_latex_source"])
        compile_result = subprocess.run(
            [latex, "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
            cwd=temporary_path,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if compile_result.returncode != 0:
            raise RuntimeError(f"LaTeX failed for {definition['equation_id']}: {compile_result.stdout[-2000:]}")
        convert_result = subprocess.run(
            [
                dvisvgm,
                "--no-fonts",
                "--exact-bbox",
                f"--output={output_path.resolve()}",
                str(temporary_path / "equation.dvi"),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if convert_result.returncode != 0 or not output_path.is_file():
            raise RuntimeError(f"dvisvgm failed for {definition['equation_id']}: {convert_result.stderr[-2000:]}")
    render_equations.annotate_svg(output_path, record, "latex+xcolor+dvisvgm")
    return {"status": "VERIFIED", "engine": "latex+xcolor+dvisvgm"}


def _render_equations(source_dir: Path) -> list[dict[str, Any]]:
    math_dir = source_dir / "math"
    math_dir.mkdir(parents=True)
    records: list[dict[str, Any]] = []
    tex_blocks: list[str] = []
    for definition in EQUATION_DEFINITIONS:
        output_path = math_dir / f"{definition['equation_id']}.svg"
        result = _render_colored_latex(definition, output_path)
        root = ET.parse(output_path).getroot()
        viewbox = [float(value) for value in root.get("viewBox", "0 0 1 1").split()]
        target = native._fit_position(viewbox, definition["fit_box"], definition["align"])
        records.append({
            **{
                key: value
                for key, value in definition.items()
                if key not in {"fit_box", "align", "render_latex_source"}
            },
            "render_latex_source": definition["render_latex_source"],
            "asset": f"math/{output_path.name}",
            "intrinsic_viewbox": [round(value, 6) for value in viewbox],
            "target_position": target,
            "render_engine": result["engine"],
            "sha256": sha256_file(output_path),
        })
        tex_blocks.append(
            f"% {definition['equation_id']}\n\\[{definition['render_latex_source']}\\]"
        )
    write_text(source_dir / "equations.tex", "\n\n".join(tex_blocks) + "\n")
    write_json(source_dir / "equation_manifest.json", {
        "schema_version": "1.1",
        "authoritative_tex": "equations.tex",
        "aspect_ratio_policy": "target boxes contain each SVG viewBox without stretching",
        "color_policy": "xcolor token roles are retained in each raster-free SVG equation object",
        "equations": records,
    })
    return records


def build_semantic(
    example_root: Path,
    equations: Sequence[Mapping[str, Any]],
    asset_manifest: Mapping[str, Any],
) -> dict[str, Any]:
    semantic = fidelity.build_semantic(example_root, equations, asset_manifest)
    semantic["figure_id"] = FIGURE_ID
    semantic["package_label"] = "Candidate C fidelity v2 review package"
    candidate_path = example_root / CANDIDATE_RELATIVE_PATH
    candidate_hash = sha256_file(candidate_path)
    frame_by_id = {frame["id"]: frame for frame in semantic["frames"]}
    frame_by_id["generator-frame"]["fill"] = _gradient(("#F7F2FC", "#F7F1FB"), 0)
    frame_by_id["measurement-panel"]["fill"] = _gradient(("#EFF6FF", "#E7F1FD"), 0)
    frame_by_id["operator-frame"]["fill"] = _gradient(("#FFF9EF", "#FFF3E4"), 0)
    with Image.open(candidate_path) as candidate:
        predicted, predicted_fit = _plot_shapes(
            candidate,
            identifier="predicted-plot",
            frame=frame_by_id["predicted-frame"]["position"],
            candidate_sha256=candidate_hash,
        )
        observed, observed_fit = _plot_shapes(
            candidate,
            identifier="observed-plot",
            frame=frame_by_id["observed-frame"]["position"],
            candidate_sha256=candidate_hash,
        )
    semantic["regions"] = {
        "generator-network": _network_shapes(),
        "predicted-plot": predicted,
        "observed-plot": observed,
    }
    semantic["plot_reference_fits"] = {
        "predicted-plot": predicted_fit,
        "observed-plot": observed_fit,
    }
    semantic["connectors"] = _connectors()
    semantic["network_layer_groups"] = [f"network-layer-{index:02d}" for index in range(1, 12)]
    semantic["editability_contract"].update({
        "native_region_shape_minimum": 40,
        "generator_gradients": "11 editable native two/three-stop gradient faces",
        "plot_curves": "two editable native reference-fitted polylines; no cosmetic sample-dot objects",
        "drawio": "native structural editing view with 11 layer cells, two curve cells, and two replaceable image cells",
    })
    semantic["validation_scope"] = (
        "Programmable provenance, exact crop pixels, local synthetic curve-fit error, vector structure, "
        "equation aspect ratio, cross-format parse validity, and topology only; not scientific correctness, "
        "publication approval, or pixel editability of the two image atoms."
    )
    object_ids = {item["id"] for item in semantic["frames"]}
    object_ids.update(item["id"] for shapes in semantic["regions"].values() for item in shapes)
    object_ids.update(semantic["regions"])
    object_ids.update(item["id"] for item in semantic["image_modules"])
    object_ids.update(item["id"] for item in semantic["connectors"])
    object_ids.update(f"{item['id']}-shaft" for item in semantic["connectors"])
    object_ids.update(f"{item['id']}-arrowhead" for item in semantic["connectors"])
    object_ids.update(item["id"] for item in semantic["labels"])
    object_ids.update(item["id"] for item in equations)
    semantic["object_ids"] = sorted(object_ids)
    return semantic


def _split_alpha_color(value: str) -> tuple[str, float | None]:
    if value.startswith("#") and len(value) == 9:
        return value[:7], int(value[7:9], 16) / 255
    if "/" in value and value.startswith("#"):
        color, alpha = value.split("/", 1)
        return color, max(0.0, min(1.0, float(alpha) / 100))
    return value, None


def _svg_paint(fill: Any, *, key: str, defs: list[str]) -> tuple[str, float | None]:
    if not isinstance(fill, Mapping) or fill.get("type") != "gradient":
        return _split_alpha_color(str(fill))
    gradient_id = f"gradient-{key}"
    angle = math.radians(float(fill.get("angleDeg", 0)))
    dx = math.cos(angle) * 50
    dy = math.sin(angle) * 50
    stops = []
    for stop in fill["stops"]:
        color, opacity = _split_alpha_color(str(stop["color"]))
        opacity_markup = f' stop-opacity="{opacity:.4f}"' if opacity is not None else ""
        stops.append(
            f'<stop offset="{float(stop["offset"]) / 1000:.3f}%" '
            f'stop-color="{html.escape(color)}"{opacity_markup}/>'
        )
    defs.append(
        f'<linearGradient id="{gradient_id}" x1="{50 - dx:.3f}%" y1="{50 - dy:.3f}%" '
        f'x2="{50 + dx:.3f}%" y2="{50 + dy:.3f}%">{"".join(stops)}</linearGradient>'
    )
    return f"url(#{gradient_id})", None


def _render_native_shape(shape: Mapping[str, Any], defs: list[str]) -> str:
    paint, alpha = _svg_paint(shape.get("fill", "none"), key=shape["id"], defs=defs)
    opacity = float(shape.get("fill_opacity", 1.0))
    if alpha is not None:
        opacity *= alpha
    fill_opacity = f' fill-opacity="{opacity:.4f}"' if opacity < 0.9999 else ""
    common = (
        f'id="{shape["id"]}" fill="{paint}"{fill_opacity} '
        f'stroke="{shape.get("stroke", "none")}" stroke-width="{shape.get("stroke_width", 0)}"'
    )
    dash = native._dash_attribute(shape.get("dash", []))
    if shape["type"] == "ellipse":
        position = shape["position"]
        return (
            f'<ellipse {common} cx="{position["left"] + position["width"] / 2}" '
            f'cy="{position["top"] + position["height"] / 2}" rx="{position["width"] / 2}" '
            f'ry="{position["height"] / 2}"{dash}/>'
        )
    if shape["type"] == "rect":
        position = shape["position"]
        return (
            f'<rect {common} x="{position["left"]}" y="{position["top"]}" '
            f'width="{position["width"]}" height="{position["height"]}"{dash}/>'
        )
    if shape["type"] == "polygon":
        return f'<polygon {common} points="{native._points_string(shape["points"])}"{dash}/>'
    return (
        f'<path {common} d="{native._path_data(shape["points"])}" '
        f'stroke-linecap="{shape.get("linecap", "round")}" '
        f'stroke-linejoin="{shape.get("linejoin", "round")}"{dash}/>'
    )


def render_svg(
    semantic: Mapping[str, Any], math_dir: Path, output_path: Path, source_dir: Path
) -> dict[str, Any]:
    defs: list[str] = []
    frame_fills: list[str] = []
    frame_outlines: list[str] = []
    for frame in semantic["frames"]:
        position = frame["position"]
        if frame["geometry"] == "ellipse":
            geometry = (
                f'cx="{position["left"] + position["width"] / 2}" '
                f'cy="{position["top"] + position["height"] / 2}" '
                f'rx="{position["width"] / 2}" ry="{position["height"] / 2}"'
            )
            tag = "ellipse"
        else:
            geometry = (
                f'x="{position["left"]}" y="{position["top"]}" '
                f'width="{position["width"]}" height="{position["height"]}" rx="{frame["radius"]}"'
            )
            tag = "rect"
        paint, alpha = _svg_paint(frame["fill"], key=f"{frame['id']}-fill", defs=defs)
        opacity_markup = f' fill-opacity="{alpha:.4f}"' if alpha is not None else ""
        frame_fills.append(f'<{tag} id="{frame["id"]}-fill" {geometry} fill="{paint}"{opacity_markup} stroke="none"/>')
        frame_outlines.append(
            f'<{tag} id="{frame["id"]}" {geometry} fill="none" stroke="{frame["stroke"]}" '
            f'stroke-width="{frame["stroke_width"]}"{native._dash_attribute(frame["dash"])}/>'
        )
    connectors: list[str] = []
    for connector in semantic["connectors"]:
        connectors.append(
            f'<path id="{connector["id"]}-shaft" data-source="{connector["source_id"]}" '
            f'data-target="{connector["target_id"]}" data-relation-type="{connector["relation_type"]}" '
            f'd="{native._path_data(connector["shaft_points"])}" fill="none" stroke="{connector["stroke"]}" '
            f'stroke-width="{connector["stroke_width"]}" stroke-linecap="butt" stroke-linejoin="miter"'
            f'{native._dash_attribute(connector["dash"])}/>'
        )
        connectors.append(
            f'<polygon id="{connector["id"]}-arrowhead" '
            f'points="{native._points_string(connector["arrowhead_points"])}" '
            f'fill="{connector["stroke"]}" stroke="none"/>'
        )
    assets_dir = output_path.parent / "assets"
    assets_dir.mkdir(parents=True)
    image_markup: list[str] = []
    for module in semantic["image_modules"]:
        source = source_dir / module["asset"]
        destination = assets_dir / Path(module["svg_href"]).name
        if destination.exists():
            raise FileExistsError(destination)
        shutil.copyfile(source, destination)
        if sha256_file(destination) != module["sha256"]:
            raise ValueError(f"copied SVG asset hash mismatch for {module['id']}")
        position = module["position"]
        image_markup.append(
            f'<image id="{module["id"]}" href="{module["svg_href"]}" '
            f'x="{position["left"]}" y="{position["top"]}" width="{position["width"]}" '
            f'height="{position["height"]}" preserveAspectRatio="xMidYMid meet" '
            f'data-replaceable="true" data-pixel-editable="false" '
            f'data-scientific-status="synthetic_visual_only"/>'
        )
    region_markup = [
        f'<g id="{region_id}" data-native-region="true">'
        f'{"".join(_render_native_shape(shape, defs) for shape in shapes)}</g>'
        for region_id, shapes in semantic["regions"].items()
    ]
    labels = []
    for label in semantic["labels"]:
        position = label["position"]
        labels.append(
            f'<text id="{label["id"]}" x="{position["left"] + position["width"] / 2}" '
            f'y="{position["top"] + label["font_size"]}" text-anchor="middle" '
            f'font-family="{label["font_family"]}" font-size="{label["font_size"]}" '
            f'fill="{label["color"]}">{html.escape(label["text"])}</text>'
        )
    equations = [native._inline_equation(item, math_dir) for item in semantic["equation_objects"]]
    content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" viewBox="0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">Deep Image Prior Candidate C fidelity v2 review</title>
  <desc id="desc">Editable mixed-media composition with native gradients, reference-fitted synthetic plot paths, colored vector equations, and two replaceable raster atoms. Final scientific approval is pending.</desc>
  <metadata>{html.escape(json.dumps({"figure_id": FIGURE_ID, "status": semantic["status"], "approved_raster_atom_count": 2, "validation_scope": semantic["validation_scope"]}, ensure_ascii=False))}</metadata>
  <defs>{"".join(defs)}</defs>
  <rect id="background" x="0" y="0" width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" fill="#FFFFFF"/>
  <g id="frame-fill-layer">{"".join(frame_fills)}</g>
  <g id="connector-layer">{"".join(connectors)}</g>
  <g id="replaceable-raster-atom-layer">{"".join(image_markup)}</g>
  <g id="native-region-layer">{"".join(region_markup)}</g>
  <g id="frame-outline-layer">{"".join(frame_outlines)}</g>
  <g id="label-layer">{"".join(labels)}</g>
  <g id="latex-equation-layer">{"".join(equations)}</g>
</svg>
'''
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_text(output_path, content)
    ET.parse(output_path)
    report = {
        "status": "VERIFIED_FIDELITY_V2_MIXED_MEDIA_SVG",
        "path": "delivery/svg/master.svg",
        "sha256": sha256_file(output_path),
        "replaceable_raster_atom_count": 2,
        "whole_candidate_raster_count": 0,
        "gradient_count": len(defs),
        "generator_face_gradient_count": 11,
        "explicit_arrowhead_count": ARROW_HEAD_COUNT,
        "equation_count": len(equations),
        "scientific_validation": False,
    }
    write_json(output_path.parent / "svg_export_report.json", report)
    return report


def _first_gradient_color(value: Any) -> str:
    if isinstance(value, Mapping) and value.get("type") == "gradient":
        return str(value["stops"][0]["color"])
    return str(value)


def render_drawio(
    semantic: Mapping[str, Any], output_path: Path, source_dir: Path
) -> dict[str, Any]:
    structural = deepcopy(semantic)
    for frame in structural["frames"]:
        frame["fill"] = _first_gradient_color(frame["fill"])
    fidelity.render_drawio(structural, output_path, source_dir)
    tree = ET.parse(output_path)
    graph_root = tree.find(".//root")
    if graph_root is None:
        raise ValueError("draw.io graph root missing")
    frame_by_id = {item["id"]: item for item in semantic["frames"]}
    for frame_id in ("generator-frame", "measurement-panel", "operator-frame"):
        frame = frame_by_id[frame_id]
        cell = next(item for item in graph_root.findall("mxCell") if item.get("id") == frame_id)
        colors = frame["fill"]["stops"]
        style = cell.get("style", "")
        style += (
            f"gradientColor={str(colors[-1]['color']).lstrip('#')};"
            "gradientDirection=east;"
        )
        cell.set("style", style)
    network = semantic["regions"]["generator-network"]
    for layer_index in range(1, 12):
        prefix = f"network-layer-{layer_index:02d}-"
        layer_shapes = [item for item in network if item["id"].startswith(prefix)]
        points = [point for item in layer_shapes for point in item["points"]]
        minimum_x = min(point[0] for point in points)
        maximum_x = max(point[0] for point in points)
        minimum_y = min(point[1] for point in points)
        maximum_y = max(point[1] for point in points)
        face = next(item for item in layer_shapes if item["id"].endswith("-face"))
        colors = face["fill"]["stops"]
        cell = ET.SubElement(graph_root, "mxCell", {
            "id": f"network-layer-{layer_index:02d}",
            "value": "",
            "style": (
                "rounded=0;whiteSpace=wrap;html=1;"
                f"fillColor={str(colors[0]['color']).lstrip('#')};"
                f"gradientColor={str(colors[-1]['color']).lstrip('#')};"
                "gradientDirection=east;strokeColor=423D75;strokeWidth=1.2;opacity=96;"
            ),
            "vertex": "1",
            "parent": "1",
            "semanticType": "editable-generator-layer",
        })
        native._mx_geometry(cell, {
            "left": minimum_x,
            "top": minimum_y,
            "width": maximum_x - minimum_x,
            "height": maximum_y - minimum_y,
        })
    for identifier in ("predicted-plot", "observed-plot"):
        curve = next(
            item for item in semantic["regions"][identifier]
            if item["id"] == f"{identifier}-curve"
        )
        points = curve["points"]
        edge = ET.SubElement(graph_root, "mxCell", {
            "id": curve["id"],
            "value": "",
            "style": "edgeStyle=none;rounded=1;html=1;endArrow=none;startArrow=none;strokeColor=0D2F6E;strokeWidth=3.2;",
            "edge": "1",
            "parent": "1",
            "semanticType": "editable-reference-fitted-synthetic-curve",
            "scientificData": "false",
        })
        geometry = ET.SubElement(edge, "mxGeometry", {"relative": "1", "as": "geometry"})
        ET.SubElement(geometry, "mxPoint", {"x": str(points[0][0]), "y": str(points[0][1]), "as": "sourcePoint"})
        ET.SubElement(geometry, "mxPoint", {"x": str(points[-1][0]), "y": str(points[-1][1]), "as": "targetPoint"})
        array = ET.SubElement(geometry, "Array", {"as": "points"})
        for x, y in points[1:-1]:
            ET.SubElement(array, "mxPoint", {"x": str(x), "y": str(y)})
    tree.write(output_path, encoding="unicode", xml_declaration=True)
    ET.parse(output_path)
    report = {
        "status": "VERIFIED_FIDELITY_V2_STRUCTURAL_EDITING_VIEW",
        "path": "delivery/drawio/figure.drawio",
        "sha256": sha256_file(output_path),
        "directed_topology_edge_count": ARROW_HEAD_COUNT,
        "generator_layer_cell_count": 11,
        "synthetic_plot_curve_cell_count": 2,
        "replaceable_raster_atom_count": 2,
        "visual_equivalence_claimed": False,
        "scientific_validation": False,
    }
    write_json(output_path.parent / "drawio_export_report.json", report)
    return report


def _run_pptx_export(
    spec_path: Path, math_dir: Path, source_dir: Path, output_dir: Path
) -> dict[str, Any]:
    runtime_node = os.environ.get("RUNTIME_NODE")
    runtime_modules = os.environ.get("RUNTIME_NODE_MODULES")
    if not runtime_node or not Path(runtime_node).is_file():
        raise RuntimeError("RUNTIME_NODE must point to the bundled Node.js executable")
    if not runtime_modules or not Path(runtime_modules).is_dir():
        raise RuntimeError("RUNTIME_NODE_MODULES must point to the bundled Node modules directory")
    script = Path(__file__).resolve().with_name("export_deep_image_prior_c_fidelity_v2_pptx.mjs")
    result = subprocess.run(
        [
            runtime_node, str(script), "--spec", str(spec_path),
            "--equation-dir", str(math_dir), "--asset-dir", str(source_dir),
            "--output-dir", str(output_dir),
        ],
        capture_output=True,
        text=True,
        timeout=360,
        env=dict(os.environ),
    )
    if result.returncode != 0:
        raise RuntimeError(f"PPTX export failed:\n{result.stdout[-2000:]}\n{result.stderr[-5000:]}")
    return json.loads((output_dir / "pptx_artifact_report.json").read_text(encoding="utf-8"))


def _edge_mask(image: Image.Image) -> Image.Image:
    grayscale = ImageOps.grayscale(image.convert("RGB"))
    return grayscale.filter(ImageFilter.FIND_EDGES).point(lambda value: 255 if value >= 32 else 0)


def _pixel_values(image: Image.Image) -> Iterable[Any]:
    getter = getattr(image, "get_flattened_data", None)
    return getter() if getter is not None else image.getdata()


def _edge_f1(reference: Image.Image, rendered: Image.Image) -> float:
    reference_edges = _edge_mask(reference)
    rendered_edges = _edge_mask(rendered)
    reference_dilated = reference_edges.filter(ImageFilter.MaxFilter(3))
    rendered_dilated = rendered_edges.filter(ImageFilter.MaxFilter(3))
    reference_count = sum(1 for value in _pixel_values(reference_edges) if value)
    rendered_count = sum(1 for value in _pixel_values(rendered_edges) if value)
    if not reference_count or not rendered_count:
        return 0.0
    matched_rendered = sum(
        1 for edge, nearby in zip(_pixel_values(rendered_edges), _pixel_values(reference_dilated), strict=True)
        if edge and nearby
    )
    matched_reference = sum(
        1 for edge, nearby in zip(_pixel_values(reference_edges), _pixel_values(rendered_dilated), strict=True)
        if edge and nearby
    )
    precision = matched_rendered / rendered_count
    recall = matched_reference / reference_count
    return 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)


def _edge_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    return _edge_mask(image).getbbox()


def _bbox_edge_error(reference: Image.Image, rendered: Image.Image) -> float | None:
    first = _edge_bbox(reference)
    second = _edge_bbox(rendered)
    if first is None or second is None:
        return None
    return float(max(abs(a - b) for a, b in zip(first, second, strict=True)))


def _formula_dark_bbox(image: Image.Image, bbox: Sequence[int]) -> tuple[int, int, int, int] | None:
    left, top, width, height = bbox
    crop = image.crop((left, top, left + width, top + height)).convert("RGB")
    mask = Image.new("L", crop.size, 0)
    mask.putdata([
        255 if min(pixel) < 165 and max(pixel) - min(pixel) > 8 else 0
        for pixel in _pixel_values(crop)
    ])
    local = mask.getbbox()
    if local is None:
        return None
    return (left + local[0], top + local[1], left + local[2], top + local[3])


def write_visual_qa(
    candidate_path: Path, rendered_path: Path, output_dir: Path
) -> dict[str, Any]:
    with Image.open(candidate_path) as reference_image, Image.open(rendered_path) as rendered_image:
        reference = reference_image.convert("RGB")
        rendered = rendered_image.convert("RGB")
    if reference.size != (CANVAS_WIDTH, CANVAS_HEIGHT):
        raise ValueError("reference image has an unexpected size")
    if rendered.size != reference.size:
        raise ValueError(f"PPTX render must be {reference.size}; got {rendered.size}")
    comparison_dir = output_dir / "validation" / "region_comparisons"
    comparison_dir.mkdir(parents=True, exist_ok=True)
    metrics: dict[str, Any] = {}
    for region_id, (left, top, width, height) in REGIONS.items():
        box = (left, top, left + width, top + height)
        reference_crop = reference.crop(box)
        rendered_crop = rendered.crop(box)
        difference = ImageChops.difference(reference_crop, rendered_crop)
        amplified = difference.point(lambda value: min(255, value * 4))
        triptych = Image.new("RGB", (width * 3, height + 28), "white")
        triptych.paste(reference_crop, (0, 28))
        triptych.paste(rendered_crop, (width, 28))
        triptych.paste(amplified, (width * 2, 28))
        draw = ImageDraw.Draw(triptych)
        draw.text((6, 7), "reference", fill="#0D2F6E")
        draw.text((width + 6, 7), "PPTX render", fill="#0D2F6E")
        draw.text((width * 2 + 6, 7), "difference x4", fill="#0D2F6E")
        comparison_path = comparison_dir / f"{region_id}.png"
        triptych.save(comparison_path, format="PNG", compress_level=6)
        mean_channels = ImageStat.Stat(difference).mean
        metrics[region_id] = {
            "source_bbox_xywh": [left, top, width, height],
            "comparison": f"region_comparisons/{region_id}.png",
            "comparison_sha256": sha256_file(comparison_path),
            "mean_absolute_rgb_error": round(sum(mean_channels) / 3, 4),
            "normalized_mean_absolute_rgb_error": round(sum(mean_channels) / (3 * 255), 6),
            "edge_f1_with_one_pixel_tolerance": round(_edge_f1(reference_crop, rendered_crop), 6),
            "bbox_edge_error_px": _bbox_edge_error(reference_crop, rendered_crop),
            "human_review_required": True,
        }
    formula_bboxes = {
        "optimization_objective": REGIONS["optimization_objective"],
        "reconstruction_equation": REGIONS["reconstruction_equation"],
    }
    formula_metrics = {}
    for name, bbox in formula_bboxes.items():
        expected = _formula_dark_bbox(reference, bbox)
        actual = _formula_dark_bbox(rendered, bbox)
        error = None
        if expected is not None and actual is not None:
            error = max(abs(a - b) for a, b in zip(expected, actual, strict=True))
        formula_metrics[name] = {
            "reference_dark_bbox": expected,
            "rendered_dark_bbox": actual,
            "max_edge_error_px": error,
            "human_review_required": True,
        }
    report = {
        "schema_version": "1.0",
        "status": "MEASURED_FOR_HUMAN_VISUAL_REVIEW",
        "reference": "../../candidates/C-presentation.png",
        "rendered": "../delivery/pptx/slide-01.png",
        "reference_sha256": sha256_file(candidate_path),
        "rendered_sha256": sha256_file(rendered_path),
        "canvas": [CANVAS_WIDTH, CANVAS_HEIGHT],
        "regions": metrics,
        "formula_optical_bbox_checks": formula_metrics,
        "interpretation": (
            "These metrics and triptychs are diagnostic review aids. They do not establish visual, "
            "scientific, or publication approval."
        ),
        "final_visual_approval": None,
        "final_scientific_approval": None,
    }
    write_json(output_dir / "validation" / "visual_fidelity_report.json", report)
    return report


def _resolve_file_within(root: Path, relative_path: str, *, label: str) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute():
        raise ValueError(f"{label} must use a relative path")
    try:
        resolved_root = root.resolve(strict=True)
        resolved = (resolved_root / relative).resolve(strict=True)
    except OSError as error:
        raise ValueError(f"{label} does not exist") from error
    try:
        resolved.relative_to(resolved_root)
    except ValueError as error:
        raise ValueError(f"{label} escapes its package directory") from error
    if not resolved.is_file():
        raise ValueError(f"{label} must resolve to a file")
    return resolved


def validate_package(
    output_dir: Path,
    *,
    candidate_path: Path | None = None,
    write_report: bool = True,
) -> dict[str, Any]:
    source_dir = output_dir / "source"
    semantic_path = source_dir / "semantic_figure.json"
    semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
    selected_map = json.loads((source_dir / "selected_candidate_map.json").read_text(encoding="utf-8"))
    asset_manifest = json.loads((source_dir / "asset_manifest.json").read_text(encoding="utf-8"))
    decision = json.loads((source_dir / "raster_atom_review_decision.json").read_text(encoding="utf-8"))
    if semantic["figure_id"] != FIGURE_ID or semantic["status"] != "AWAITING_FINAL_RESEARCHER_REVIEW":
        raise ValueError("semantic status or figure id is incorrect")
    if decision["final_publication_approval"] is not None or decision["final_scientific_approval"] is not None:
        raise ValueError("review-draft decision must not contain final approval")
    if len(asset_manifest["assets"]) != 2:
        raise ValueError("exactly two raster atoms are required")
    if asset_manifest.get("review_decision") != {
        "path": "raster_atom_review_decision.json",
        "status": "APPROVED_FOR_REVIEW_DRAFT_ONLY",
        "required": True,
    }:
        raise ValueError("raster asset manifest is missing its required review decision")
    expected_authorized_atoms = [
        {
            "atom_id": item["id"],
            "region_id": item["region_id"],
            "bbox": item["bbox"],
            "asset_path": item["path"],
            "asset_sha256": item["sha256"],
        }
        for item in asset_manifest["assets"]
    ]
    expected_constraints = {
        "synthetic_visual_only": True,
        "scientific_evidence": False,
        "independently_replaceable": True,
        "pixel_editable": False,
        "whole_candidate_embedding_allowed": False,
        "reference_crop_embedding_allowed": False,
        "baked_in_scientific_annotation_allowed": False,
    }
    if (
        decision.get("status") != "APPROVED_FOR_REVIEW_DRAFT_ONLY"
        or decision.get("scope") != "review-draft-only"
        or decision.get("bbox_format") != asset_manifest.get("bbox_format")
        or decision.get("authorized_atoms") != expected_authorized_atoms
        or decision.get("constraints") != expected_constraints
        or decision.get("candidate")
        != {
            "id": asset_manifest.get("candidate_id"),
            "path": asset_manifest.get("candidate_path"),
            "sha256": asset_manifest.get("candidate_sha256"),
        }
    ):
        raise ValueError("raster-atom review decision is missing or not bound to the asset manifest")
    if {item.get("id") for item in asset_manifest["assets"]} != set(
        APPROVED_RASTER_ATOMS
    ):
        raise ValueError("raster asset identities do not match the approved case contract")
    approved_hashes = {item["sha256"] for item in asset_manifest["assets"]}
    candidate_path = candidate_path or output_dir.parent / CANDIDATE_RELATIVE_PATH
    candidate_path = candidate_path.resolve()
    if candidate_path.name != "C-presentation.png" or candidate_path.parent.name != "candidates":
        raise ValueError("fidelity-v2 validation requires the exact Candidate C file")
    _case_manifest, approved_map = verify_reference_case_inputs(candidate_path.parents[1])
    candidate_hash = sha256_file(candidate_path)
    verified_regions = validate_selected_candidate_map(
        selected_map,
        candidate_sha256=candidate_hash,
        approved_map=approved_map,
    )
    declared_candidate_hashes = {
        selected_map["image_hash"],
        semantic["visual_reference"]["sha256"],
        asset_manifest["candidate_sha256"],
    }
    if declared_candidate_hashes != {candidate_hash}:
        raise ValueError("selected candidate hash binding is inconsistent")
    if decision["candidate"]["sha256"] != candidate_hash:
        raise ValueError("raster review decision candidate hash is inconsistent")
    selection_record = _case_manifest["selection"]["record"]
    if semantic.get("selection", {}).get("sha256") != selection_record["sha256"]:
        raise ValueError("semantic source is not bound to the approved Candidate C selection")
    if semantic.get("selected_candidate_map") != "selected_candidate_map.json":
        raise ValueError("semantic source does not reference the validated region map")
    for item in asset_manifest["assets"]:
        if {
            item["candidate_sha256"],
            item["origin"]["candidate_sha256"],
        } != {candidate_hash}:
            raise ValueError(f"raster atom candidate provenance is inconsistent: {item['id']}")
        left, top, right, bottom = item["bbox"]
        atom_path = _resolve_file_within(source_dir, item["path"], label=f"raster atom {item['id']}")
        if sha256_file(atom_path) != item["sha256"]:
            raise ValueError(f"raster atom hash mismatch: {item['id']}")
        with Image.open(candidate_path) as candidate:
            expected = candidate.crop((left, top, right, bottom)).convert("RGBA")
        with Image.open(atom_path) as actual:
            if ImageChops.difference(expected, actual.convert("RGBA")).getbbox() is not None:
                raise ValueError(f"raster atom changed pixels: {item['id']}")
    for identifier, fit in semantic["plot_reference_fits"].items():
        if fit["candidate_sha256"] != candidate_hash:
            raise ValueError(f"{identifier} candidate provenance is inconsistent")
        if fit["scientific_data"] or not fit["reference_fit"]:
            raise ValueError(f"{identifier} lost its synthetic-only reference-fit boundary")
        if fit["coverage"] < 0.98 or not 30 <= fit["simplified_point_count"] <= 50:
            raise ValueError(f"{identifier} fit coverage or point count is invalid")
        if fit["median_vertical_error_px"] > 1.5 or fit["max_vertical_error_px"] > 4:
            raise ValueError(f"{identifier} fit error is too large")
    all_shapes = [item for shapes in semantic["regions"].values() for item in shapes]
    if any("-sample-" in item["id"] for item in all_shapes):
        raise ValueError("cosmetic plot sample dots are forbidden in v2")
    curves = [item for item in all_shapes if item["id"].endswith("-curve")]
    gradients = [
        item for item in semantic["regions"]["generator-network"]
        if item["id"].endswith("-face") and isinstance(item["fill"], Mapping)
    ]
    if len(curves) != 2 or len(gradients) != 11:
        raise ValueError("v2 requires two native curves and eleven native generator gradients")

    svg_path = output_dir / "delivery" / "svg" / "master.svg"
    svg_root = ET.parse(svg_path).getroot()
    svg_text = svg_path.read_text(encoding="utf-8")
    images = [node for node in svg_root.iter() if node.tag.rsplit("}", 1)[-1] == "image"]
    if len(images) != 2 or any((node.get("href") or "").startswith("data:") for node in images):
        raise ValueError("SVG must contain exactly two relative raster atoms")
    for forbidden in ("marker-end", "<marker", "<filter", "<radialGradient", "<mask"):
        if forbidden in svg_text:
            raise ValueError(f"SVG contains forbidden construct: {forbidden}")
    if svg_text.count("<linearGradient") < 14:
        raise ValueError("SVG gradients are missing")
    svg_asset_hashes = {
        sha256_file(_resolve_file_within(svg_path.parent, node.get("href") or "", label="SVG raster atom"))
        for node in images
    }
    if svg_asset_hashes != approved_hashes:
        raise ValueError("SVG raster atom hashes do not match the approved manifest")
    arrows = [node for node in svg_root.iter() if (node.get("id") or "").endswith("-arrowhead")]
    if len(arrows) != ARROW_HEAD_COUNT:
        raise ValueError("SVG arrowhead count mismatch")
    for arrow in arrows:
        points = [tuple(map(float, value.split(","))) for value in arrow.get("points", "").split()]
        extent = max(
            max(point[0] for point in points) - min(point[0] for point in points),
            max(point[1] for point in points) - min(point[1] for point in points),
        )
        if not 12.0 <= extent <= 14.5:
            raise ValueError(f"arrowhead extent out of v2 range: {extent}")

    equation_manifest = json.loads((source_dir / "equation_manifest.json").read_text(encoding="utf-8"))
    if len(equation_manifest["equations"]) != 9:
        raise ValueError("nine equations are required")
    equation_paths: dict[str, Path] = {}
    for equation in equation_manifest["equations"]:
        equation_path = _resolve_file_within(
            source_dir,
            equation["asset"],
            label=f"equation {equation['equation_id']}",
        )
        if sha256_file(equation_path) != equation["sha256"]:
            raise ValueError(f"equation hash mismatch: {equation['equation_id']}")
        equation_paths[equation["equation_id"]] = equation_path
        intrinsic = equation["intrinsic_viewbox"]
        target = equation["target_position"]
        intrinsic_ratio = intrinsic[2] / intrinsic[3]
        target_ratio = target["width"] / target["height"]
        if abs(target_ratio - intrinsic_ratio) / intrinsic_ratio > 0.005:
            raise ValueError(f"equation aspect ratio changed: {equation['equation_id']}")
    objective_text = equation_paths["eq_objective"].read_text(encoding="utf-8").lower()
    reconstruction_text = equation_paths["eq_reconstruction"].read_text(encoding="utf-8").lower()
    if not {"#5a258c", "#0d2f6e"}.issubset(set(_hex_colors(objective_text))):
        raise ValueError("objective equation token colors are incomplete")
    if not {"#5a258c", "#0b6262", "#0d2f6e"}.issubset(set(_hex_colors(reconstruction_text))):
        raise ValueError("reconstruction equation token colors are incomplete")

    pptx_path = output_dir / "delivery" / "pptx" / "figure.pptx"
    with zipfile.ZipFile(pptx_path) as archive:
        media = [name for name in archive.namelist() if name.startswith("ppt/media/")]
        vector_media = [name for name in media if name.lower().endswith(".svg")]
        substantive_rasters = [
            name for name in media
            if name.lower().endswith((".png", ".jpg", ".jpeg"))
            and archive.getinfo(name).file_size > 4096
        ]
        embedded_hashes = {hashlib.sha256(archive.read(name)).hexdigest() for name in substantive_rasters}
        embedded_vector_hashes = {hashlib.sha256(archive.read(name)).hexdigest() for name in vector_media}
        slide_xml = archive.read("ppt/slides/slide1.xml")
    if len(vector_media) != 9 or len(substantive_rasters) != 2 or embedded_hashes != approved_hashes:
        raise ValueError("PPTX media boundary is incorrect")
    if embedded_vector_hashes != {equation["sha256"] for equation in equation_manifest["equations"]}:
        raise ValueError("PPTX equation SVG hashes do not match the equation manifest")
    if slide_xml.count(b"<p:sp>") < semantic["editability_contract"]["native_region_shape_minimum"]:
        raise ValueError("PPTX native shape count is below the declared minimum")
    if b"<a:gradFill" not in slide_xml or b"<a:alpha" not in slide_xml or b"<a:custGeom" not in slide_xml:
        raise ValueError("PPTX native gradient, alpha, or custom geometry is missing")

    drawio_path = output_dir / "delivery" / "drawio" / "figure.drawio"
    drawio = ET.parse(drawio_path)
    cells = drawio.findall(".//mxCell")
    if len([item for item in cells if item.get("semanticType") == "editable-generator-layer"]) != 11:
        raise ValueError("draw.io generator layer cells are missing")
    if len([item for item in cells if item.get("semanticType") == "editable-reference-fitted-synthetic-curve"]) != 2:
        raise ValueError("draw.io curve cells are missing")
    if len([item for item in cells if item.get("relationType")]) != ARROW_HEAD_COUNT:
        raise ValueError("draw.io topology edge count is incorrect")
    drawio_atoms = [item for item in cells if item.get("semanticType") == "replaceable-raster-atom"]
    if len(drawio_atoms) != 2:
        raise ValueError("draw.io raster atom count is incorrect")
    drawio_hashes = set()
    for cell in drawio_atoms:
        style = cell.get("style") or ""
        if "base64," not in style:
            raise ValueError("draw.io raster atom is not embedded as a portable data URI")
        encoded = style.split("base64,", 1)[1].split(";", 1)[0]
        try:
            embedded = base64.b64decode(encoded, validate=True)
        except ValueError as error:
            raise ValueError("draw.io raster atom contains invalid base64") from error
        embedded_hash = hashlib.sha256(embedded).hexdigest()
        if cell.get("assetSha256") != embedded_hash:
            raise ValueError("draw.io raster atom hash metadata is incorrect")
        drawio_hashes.add(embedded_hash)
    if drawio_hashes != approved_hashes:
        raise ValueError("draw.io raster atoms do not match the approved manifest")

    pdf_path = output_dir / "delivery" / "pdf" / "publication.pdf"
    if len(PdfReader(pdf_path).pages) != 1:
        raise ValueError("PDF preview must contain one page")
    visual_report = json.loads((output_dir / "validation" / "visual_fidelity_report.json").read_text(encoding="utf-8"))
    if visual_report["final_visual_approval"] is not None or visual_report["final_scientific_approval"] is not None:
        raise ValueError("visual QA must not create final approval")
    if set(visual_report["regions"]) != set(REGIONS):
        raise ValueError("visual QA must cover all eight declared regions")
    rendered_path = _resolve_file_within(output_dir, "delivery/pptx/slide-01.png", label="PPTX render")
    if visual_report["reference_sha256"] != candidate_hash:
        raise ValueError("visual QA reference hash is stale or incorrect")
    if visual_report["rendered_sha256"] != sha256_file(rendered_path):
        raise ValueError("visual QA render hash is stale or incorrect")
    for region_id, item in visual_report["regions"].items():
        comparison_path = _resolve_file_within(
            output_dir / "validation",
            item["comparison"],
            label=f"visual QA triptych {region_id}",
        )
        if item["comparison_sha256"] != sha256_file(comparison_path):
            raise ValueError(f"visual QA triptych hash mismatch: {region_id}")
    _resolve_file_within(output_dir, "preview.png", label="package preview")
    json_files = [
        _resolve_file_within(
            output_dir,
            path.relative_to(output_dir).as_posix(),
            label=f"package JSON {path.relative_to(output_dir).as_posix()}",
        )
        for path in output_dir.rglob("*.json")
    ]
    serialized = "\n".join(path.read_text(encoding="utf-8") for path in json_files)
    portable_markers = (
        *LOCAL_PATH_MARKERS,
        "/" + "private/",
        "/" + "home/",
        "C:" + "\\Users\\",
        "file" + "://",
    )
    if any(marker.lower() in serialized.lower() for marker in portable_markers):
        raise ValueError("portable JSON contains a local absolute path")
    report = {
        "schema_version": "1.0",
        "status": "VERIFIED_FIDELITY_V2_REVIEW_DRAFT",
        "figure_id": FIGURE_ID,
        "validation_scope": semantic["validation_scope"],
        "checks": {
            "major_region_count": len(verified_regions),
            "approved_raster_atom_count": 2,
            "whole_candidate_raster_count": 0,
            "generator_layer_group_count": 11,
            "generator_face_gradient_count": len(gradients),
            "native_plot_curve_count": len(curves),
            "cosmetic_plot_sample_dot_count": 0,
            "svg_explicit_arrowhead_count": len(arrows),
            "pptx_vector_equation_count": len(vector_media),
            "pptx_substantive_raster_count": len(substantive_rasters),
            "pptx_native_shape_count": slide_xml.count(b"<p:sp>"),
            "pptx_native_gradient_present": True,
            "pptx_alpha_present": True,
            "drawio_generator_layer_cell_count": 11,
            "drawio_plot_curve_cell_count": 2,
            "drawio_directed_topology_edge_count": ARROW_HEAD_COUNT,
            "pdf_page_count": 1,
            "equation_aspect_ratio_preserved": True,
            "visual_triptych_count": len(visual_report["regions"]),
        },
        "claims": {
            "svg": "editable native vector composition with two relative replaceable image atoms",
            "pptx": "editable native shapes, gradients, text, two independent picture shapes, and vector equations",
            "drawio": "editable structural view; pixel equivalence to the SVG/PPTX is not claimed",
            "pdf": "preview/export only",
            "scientific_correctness": "not automated; explicit final researcher approval remains required",
        },
        "final_visual_approval": None,
        "final_scientific_approval": None,
    }
    if write_report:
        (output_dir / "validation").mkdir(parents=True, exist_ok=True)
        write_json(output_dir / "validation" / "fidelity_v2_validation_report.json", report)
    return report


def _hex_colors(text: str) -> list[str]:
    import re

    return re.findall(r"#[0-9a-f]{6}", text.lower())


def _write_package_readme(output_dir: Path) -> None:
    write_text(output_dir / "README.md", """# Candidate C — fidelity v2 review package

Status: `AWAITING_FINAL_RESEARCHER_REVIEW`. Final visual and scientific approval remain `null`.

This package moves the editable outputs closer to the user-selected Candidate C PNG without flattening the full figure. It retains the hash-bound eight-region layout and exactly two independently replaceable raster atoms. The generator uses native editable gradients, both synthetic signal glyphs are single reference-fitted editable polylines, arrows use smaller explicit polygons, and equations are intrinsic-aspect colored LaTeX SVG objects.

## Review evidence

- `source/selected_candidate_map.json`: hash-bound visual direction and conversion policy.
- `source/semantic_figure.json`: canonical object geometry, topology, gradient paint, and curve-fit provenance.
- `validation/region_comparisons/*.png`: reference / PPTX render / amplified-difference triptychs for all eight regions.
- `validation/visual_fidelity_report.json`: diagnostic visual metrics that require human interpretation.
- `validation/fidelity_v2_validation_report.json`: programmatic structure, provenance, parse, and topology checks.

## Editable outputs

- `delivery/svg/master.svg`: vector master with relative links to two replaceable raster atoms.
- `delivery/pptx/figure.pptx`: native shapes, native gradients/alpha, editable polylines, text, and nine vector equation objects.
- `delivery/drawio/figure.drawio`: structural editing view with 11 generator layer cells, two curve cells, seven directed topology edges, and two image cells. Pixel equivalence is not claimed.
- `delivery/pdf/publication.pdf`: preview/export only; no editability claim.

The local curve fit is limited to two decorative synthetic signal glyphs in the selected ImageGen proposal. It is not a chart digitizer and does not recover scientific data. Automated validation does not judge scientific correctness or publication suitability; the researcher makes those decisions.
""")


def _write_delivery_manifest(output_dir: Path, report: Mapping[str, Any]) -> None:
    write_json(output_dir / "delivery" / "delivery_manifest.json", {
        "schema_version": "1.0",
        "figure_id": FIGURE_ID,
        "status": report["status"],
        "canonical_source": "source/semantic_figure.json",
        "selected_candidate_map": "source/selected_candidate_map.json",
        "asset_manifest": "source/asset_manifest.json",
        "validation_report": "validation/fidelity_v2_validation_report.json",
        "visual_fidelity_report": "validation/visual_fidelity_report.json",
        "formats": [
            {"format": "svg", "path": "delivery/svg/master.svg", "editability": "native vectors, gradients, equations, and two replaceable image atoms"},
            {"format": "pptx", "path": "delivery/pptx/figure.pptx", "editability": "native shapes, gradients, text, curves, and vector equations"},
            {"format": "drawio", "path": "delivery/drawio/figure.drawio", "editability": "native structural view; pixel equivalence not claimed"},
            {"format": "pdf", "path": "delivery/pdf/publication.pdf", "editability": "none claimed; preview/export only"},
        ],
        "final_visual_approval": None,
        "final_scientific_approval": None,
    })


def finalize_existing(
    output_dir: Path,
    *,
    pdftoppm: str | None,
    example_root: Path | None = None,
) -> dict[str, Any]:
    pdf_dir = output_dir / "delivery" / "pdf"
    publication = pdf_dir / "publication.pdf"
    if not publication.is_file():
        publication = native._adopt_converted_pdf(pdf_dir)
    pdftoppm_path = native._resolve_executable(pdftoppm, ("pdftoppm",))
    if not pdftoppm_path:
        raise RuntimeError("pdftoppm is required for preview rendering")
    preview = output_dir / "preview.png"
    if preview.exists():
        raise FileExistsError(preview)
    native._render_preview(publication, preview, pdftoppm_path)
    candidate = (example_root or output_dir.parent) / CANDIDATE_RELATIVE_PATH
    write_visual_qa(candidate, output_dir / "delivery" / "pptx" / "slide-01.png", output_dir)
    report = validate_package(output_dir, candidate_path=candidate)
    _write_delivery_manifest(output_dir, report)
    _write_package_readme(output_dir)
    return report


def build_package(
    example_root: Path,
    output_dir: Path,
    *,
    soffice: str | None,
    pdftoppm: str | None,
    defer_pdf: bool = False,
) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_dir}")
    _, approved_map = verify_reference_case_inputs(example_root)
    candidate = example_root / CANDIDATE_RELATIVE_PATH
    with Image.open(candidate) as image:
        if image.size != (CANVAS_WIDTH, CANVAS_HEIGHT):
            raise ValueError(f"candidate C must be {CANVAS_WIDTH}x{CANVAS_HEIGHT}; got {image.size}")
    source_dir = output_dir / "source"
    source_dir.mkdir(parents=True)
    selected_map = build_selected_candidate_map(example_root)
    validate_selected_candidate_map(
        selected_map,
        candidate_sha256=sha256_file(candidate),
        approved_map=approved_map,
    )
    write_json(source_dir / "selected_candidate_map.json", selected_map)
    references = native._write_reference_regions(candidate, source_dir)
    overlay = native._write_region_overlay(candidate, source_dir)
    write_json(source_dir / "reference_region_manifest.json", {
        "schema_version": "1.0",
        "candidate_sha256": selected_map["image_hash"],
        "policy": "reference_only_not_embedded",
        "regions": references,
        "region_overlay": overlay,
    })
    asset_manifest = fidelity._write_exact_raster_atoms(candidate, source_dir)
    fidelity._write_raster_atom_review_decision(source_dir, asset_manifest)
    equations = _render_equations(source_dir)
    semantic = build_semantic(example_root, equations, asset_manifest)
    semantic_path = source_dir / "semantic_figure.json"
    write_json(semantic_path, semantic)
    render_svg(semantic, source_dir / "math", output_dir / "delivery" / "svg" / "master.svg", source_dir)
    render_drawio(semantic, output_dir / "delivery" / "drawio" / "figure.drawio", source_dir)
    pptx_dir = output_dir / "delivery" / "pptx"
    pptx_dir.mkdir(parents=True)
    _run_pptx_export(semantic_path, source_dir / "math", source_dir, pptx_dir)
    if defer_pdf:
        return {
            "status": "STAGED_PENDING_PDF_PREVIEW",
            "output_dir": str(output_dir),
            "pptx": "delivery/pptx/figure.pptx",
            "final_visual_approval": None,
            "final_scientific_approval": None,
        }
    soffice_path = native._resolve_executable(
        soffice,
        ("soffice", "/Applications/LibreOffice.app/Contents/MacOS/soffice"),
    )
    if not soffice_path:
        raise RuntimeError("LibreOffice soffice is required for PDF preview export")
    native._export_pdf(pptx_dir / "figure.pptx", output_dir / "delivery" / "pdf", soffice_path)
    return finalize_existing(output_dir, pdftoppm=pdftoppm, example_root=example_root)


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
    parser.add_argument("--defer-pdf", action="store_true")
    parser.add_argument("--finalize-existing", action="store_true")
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    if args.finalize_existing:
        report = finalize_existing(
            output_dir,
            pdftoppm=args.pdftoppm,
            example_root=args.example_root.resolve(),
        )
    else:
        report = build_package(
            args.example_root.resolve(),
            output_dir,
            soffice=args.soffice,
            pdftoppm=args.pdftoppm,
            defer_pdf=args.defer_pdf,
        )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
