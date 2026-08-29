#!/usr/bin/env python3
"""Build a native C-only Deep Image Prior review draft.

The previous D-layout/C-style delivery remains reproducible through
``build_deep_image_prior_semantic.py``.  This builder creates a separate draft
that uses candidate C as both composition and visual-style authority while
keeping exact scientific labels and topology under deterministic control.
"""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path
from typing import Any

from build_deep_image_prior_semantic import (
    build_semantic_scaffold,
    equation_source,
    sha256_file,
)
from figure_artifacts import write_json
from workflow_v3 import semantic_integrity_errors, write_text


CANVAS_WIDTH = 1600
CANVAS_HEIGHT = 900
EXAMPLE_ID = "deep-image-prior-C-presentation"


def _shape_map(semantic: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in semantic["shapes"]}


def _equation_map(semantic: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in semantic["equation_objects"]}


def _remove_shapes(
    semantic: dict[str, Any],
    *,
    exact_ids: set[str],
    prefixes: tuple[str, ...],
) -> None:
    removed = {
        item["id"]
        for item in semantic["shapes"]
        if item["id"] in exact_ids or item["id"].startswith(prefixes)
    }
    semantic["shapes"] = [
        item for item in semantic["shapes"] if item["id"] not in removed
    ]
    semantic["entities"] = [
        item for item in semantic["entities"] if item["id"] not in removed
    ]


def _add_rect(
    semantic: dict[str, Any],
    identifier: str,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    fill: str,
    stroke: str,
    stroke_width: float = 2.0,
    rx: float = 0,
    group_id: str,
    entity_type: str,
    stage: str,
    dash: str | None = None,
    prepend: bool = False,
) -> None:
    item: dict[str, Any] = {
        "id": identifier,
        "type": "rect",
        "entity_type": entity_type,
        "group_id": group_id,
        "style_role": "surface",
        "fill_token": "literal",
        "stroke_token": "literal",
        "fill": fill,
        "stroke": stroke,
        "stroke_width": stroke_width,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "rx": rx,
    }
    if dash:
        item["dash"] = dash
    if prepend:
        semantic["shapes"].insert(0, item)
    else:
        semantic["shapes"].append(item)
    semantic["entities"].append(
        {"id": identifier, "entity_type": entity_type, "stage": stage}
    )


def _add_ellipse(
    semantic: dict[str, Any],
    identifier: str,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    *,
    fill: str,
    stroke: str,
    stroke_width: float,
    group_id: str,
    entity_type: str,
    stage: str,
) -> None:
    semantic["shapes"].append(
        {
            "id": identifier,
            "type": "ellipse",
            "entity_type": entity_type,
            "group_id": group_id,
            "style_role": "surface",
            "fill_token": "literal",
            "stroke_token": "literal",
            "fill": fill,
            "stroke": stroke,
            "stroke_width": stroke_width,
            "cx": cx,
            "cy": cy,
            "rx": rx,
            "ry": ry,
        }
    )
    semantic["entities"].append(
        {"id": identifier, "entity_type": entity_type, "stage": stage}
    )


def _add_dense_noise(semantic: dict[str, Any]) -> None:
    palette = ("#111827", "#35405D", "#677084", "#9AA1AE")
    generator = random.Random(20260827)
    # A fixed local seed keeps the scatter reproducible without reading as a grid.
    for index in range(300):
        x = generator.uniform(56, 239)
        y = generator.uniform(221, 409)
        radius = generator.uniform(0.75, 1.85)
        color = generator.choice(palette)
        _add_ellipse(
            semantic,
            f"noise-dot-c-{index + 1:03d}",
            x,
            y,
            radius,
            radius,
            fill=color,
            stroke=color,
            stroke_width=0.2,
            group_id="input-noise",
            entity_type="noise-sample",
            stage="input",
        )


def _add_generator_layers(semantic: dict[str, Any]) -> None:
    center_y = 326.0
    encoder = [
        (379, 27, 174, "#59538D"),
        (417, 27, 146, "#68639A"),
        (455, 26, 114, "#7E78AB"),
        (492, 24, 80, "#9992C1"),
    ]
    decoder = [
        (568, 24, 80, "#9992C1"),
        (604, 26, 114, "#7E78AB"),
        (641, 27, 146, "#68639A"),
        (679, 27, 174, "#59538D"),
    ]
    for side, layers in (("encoder", encoder), ("decoder", decoder)):
        for index, (x, width, height, color) in enumerate(layers, start=1):
            y = center_y - height / 2
            _add_rect(
                semantic,
                f"c-{side}-{index}-back",
                x + 8,
                y - 6,
                width,
                height,
                fill="#C7C3DD",
                stroke="#7771A5",
                stroke_width=1.2,
                rx=3,
                group_id="generator",
                entity_type="network-layer",
                stage="generation",
            )
            _add_rect(
                semantic,
                f"c-{side}-{index}-front",
                x,
                y,
                width,
                height,
                fill=color,
                stroke="#4C467E",
                stroke_width=1.6,
                rx=3,
                group_id="generator",
                entity_type="network-layer",
                stage="generation",
            )
    _add_rect(
        semantic,
        "c-bottleneck-back",
        541,
        296,
        18,
        60,
        fill="#C7C3DD",
        stroke="#7771A5",
        stroke_width=1.2,
        rx=3,
        group_id="generator",
        entity_type="network-layer",
        stage="generation",
    )
    _add_rect(
        semantic,
        "c-bottleneck-front",
        533,
        302,
        18,
        60,
        fill="#504A84",
        stroke="#3F396C",
        stroke_width=1.6,
        rx=3,
        group_id="generator",
        entity_type="network-layer",
        stage="generation",
    )


def _add_smooth_mountain(semantic: dict[str, Any]) -> None:
    count = 181
    x_start = 806.0
    base_y = 421.0
    step = 198.0 / (count - 1)
    column_width = step + 0.55
    for index in range(count):
        t = index / (count - 1)
        back_height = (
            18
            + 63 * math.exp(-((t - 0.24) / 0.16) ** 2)
            + 151 * math.exp(-((t - 0.52) / 0.18) ** 2)
            + 56 * math.exp(-((t - 0.80) / 0.18) ** 2)
        )
        front_height = (
            13
            + 54 * math.exp(-((t - 0.32) / 0.22) ** 2)
            + 74 * math.exp(-((t - 0.70) / 0.21) ** 2)
            + 8 * math.sin(t * math.pi * 5.0) ** 2
        )
        x = x_start + index * step
        _add_rect(
            semantic,
            f"c-mountain-back-{index + 1:03d}",
            x,
            base_y - back_height,
            column_width,
            back_height,
            fill="#737987",
            stroke="#737987",
            stroke_width=0.0,
            group_id="reconstruction",
            entity_type="reconstruction-glyph",
            stage="reconstruction",
        )
        _add_rect(
            semantic,
            f"c-mountain-front-{index + 1:03d}",
            x,
            base_y - front_height,
            column_width,
            front_height,
            fill="#303846",
            stroke="#303846",
            stroke_width=0.0,
            group_id="reconstruction",
            entity_type="reconstruction-glyph",
            stage="reconstruction",
        )


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
    return [(item - minimum) / span for item in raw]


def _add_measurement_plot(
    semantic: dict[str, Any], prefix: str, frame_y: float, *, observed: bool
) -> None:
    for index in range(1, 5):
        _add_rect(
            semantic,
            f"c-{prefix}-grid-v-{index}",
            1306 + index * 47,
            frame_y + 12,
            1.0,
            102,
            fill="#D8E1EC",
            stroke="#D8E1EC",
            stroke_width=0.2,
            group_id=f"{prefix}-measurement",
            entity_type="plot-grid",
            stage="measurement",
        )
    for index in range(1, 3):
        _add_rect(
            semantic,
            f"c-{prefix}-grid-h-{index}",
            1318,
            frame_y + index * 42,
            211,
            1.0,
            fill="#D8E1EC",
            stroke="#D8E1EC",
            stroke_width=0.2,
            group_id=f"{prefix}-measurement",
            entity_type="plot-grid",
            stage="measurement",
        )
    # Closely overlapping native points approximate a continuous editable curve
    # in every export without embedding a raster or relying on a path object.
    values = _signal_values(320, observed)
    for index, value in enumerate(values):
        _add_ellipse(
            semantic,
            f"c-{prefix}-curve-{index + 1:03d}",
            1318 + index * (211 / 319),
            frame_y + 108 - value * 88,
            1.45,
            1.45,
            fill="#0E2061",
            stroke="#0E2061",
            stroke_width=0.2,
            group_id=f"{prefix}-measurement",
            entity_type="measurement-curve",
            stage="measurement",
        )


def _connector(
    identifier: str,
    source_id: str,
    target_id: str,
    points: list[list[float]],
    *,
    relation_type: str,
    stroke_token: str = "ink",
    dash: bool = False,
) -> dict[str, Any]:
    return {
        "id": identifier,
        "source_id": source_id,
        "target_id": target_id,
        "relation_type": relation_type,
        "direction": "forward",
        "points": points,
        "arrow": "end",
        "stroke_token": stroke_token,
        "dash": dash,
    }


def build_semantic(example_root: Path, selection_path: Path) -> dict[str, Any]:
    semantic = build_semantic_scaffold()

    _remove_shapes(
        semantic,
        exact_ids={"comparison-minus-bar", "loss-box"},
        prefixes=(
            "noise-dot-",
            "enc-block-",
            "dec-block-",
            "bottleneck-",
            "latent-link-",
            "mountain-column-",
            "foreground-column-",
            "predicted-grid-",
            "observed-grid-",
            "predicted-sample-",
            "observed-sample-",
        ),
    )
    semantic["text_objects"] = [
        item for item in semantic["text_objects"] if item["id"] == "feedback-caption"
    ]

    shapes = _shape_map(semantic)
    shapes["noise-frame"].update(
        x=40, y=205, width=215, height=220, rx=16,
        fill="#FFFFFF", stroke="#0E2061", stroke_width=3.0,
    )
    shapes["generator-frame"].update(
        x=350, y=183, width=370, height=283, rx=20,
        fill="#F7F3FB", stroke="#57218C", stroke_width=3.2,
    )
    shapes["reconstruction-background"].update(
        x=795, y=210, width=218, height=225, rx=15,
        fill="#ECEFF3", stroke="#125460", stroke_width=3.2,
    )
    shapes["operator-frame"].update(
        x=1088, y=260, width=112, height=110, rx=18,
        fill="#FFF8ED", stroke="#C37107", stroke_width=3.0,
    )
    shapes["predicted-frame"].update(
        x=1306, y=174, width=235, height=126, rx=13,
        fill="#FFFFFF", stroke="#0E2061", stroke_width=3.0,
    )
    shapes["observed-frame"].update(
        x=1306, y=495, width=235, height=126, rx=13,
        fill="#FFFFFF", stroke="#0E2061", stroke_width=3.0,
    )
    shapes["comparison-node"].update(
        cx=1423, cy=397, rx=56, ry=56,
        fill="#FFFFFF", stroke="#0E2061", stroke_width=3.0,
        entity_type="loss",
    )
    entities = {item["id"]: item for item in semantic["entities"]}
    entities["comparison-node"]["entity_type"] = "loss"

    _add_rect(
        semantic,
        "measurement-panel",
        1277,
        96,
        293,
        596,
        fill="#EFF5FB",
        stroke="#648EC4",
        stroke_width=3.0,
        rx=26,
        group_id="data-consistency",
        entity_type="measurement-panel",
        stage="measurement",
        dash="10 8",
        prepend=True,
    )
    _add_dense_noise(semantic)
    _add_generator_layers(semantic)
    _add_smooth_mountain(semantic)
    _add_measurement_plot(semantic, "predicted", 174, observed=False)
    _add_measurement_plot(semantic, "observed", 495, observed=True)

    equations = _equation_map(semantic)
    equations["eq-z"].update(x=147, y=185, width=90, height=54, font_size=48)
    equations["eq-generator"].update(x=535, y=229, width=150, height=58, font_size=46)
    equations["eq-xhat"].update(x=904, y=188, width=100, height=56, font_size=48)
    equations["eq-operator"].update(x=1144, y=333, width=80, height=62, font_size=50)
    equations["eq-yhat"].update(x=1423, y=150, width=90, height=54, font_size=46)
    equations["eq-y"].update(x=1423, y=668, width=70, height=52, font_size=46)
    equations["eq-loss"].update(x=1423, y=411, width=112, height=48, font_size=34)
    equations["eq-objective"].update(
        x=300, y=826, width=760, height=62, font_size=35, text_anchor="start"
    )
    equations["eq-reconstruction"].update(
        x=1170, y=826, width=360, height=62, font_size=35
    )

    feedback = semantic["text_objects"][0]
    feedback.update(
        text="optimize θ",
        x=880,
        y=721,
        font_size=20,
        font_weight=600,
        fill_token="purple",
        text_anchor="middle",
    )

    semantic["connectors"] = [
        _connector(
            "flow-z-generator", "noise-frame", "generator-frame",
            [[255, 315], [350, 315]], relation_type="generator-input",
        ),
        _connector(
            "flow-generator-reconstruction", "generator-frame", "reconstruction-background",
            [[720, 315], [795, 315]], relation_type="reconstruction",
        ),
        _connector(
            "flow-reconstruction-operator", "reconstruction-background", "operator-frame",
            [[1013, 315], [1088, 315]], relation_type="forward-model-input",
        ),
        _connector(
            "flow-operator-predicted", "operator-frame", "predicted-frame",
            [[1200, 315], [1277, 315], [1277, 237], [1306, 237]],
            relation_type="predicted-measurement",
        ),
        _connector(
            "flow-predicted-loss", "predicted-frame", "comparison-node",
            [[1423, 300], [1423, 341]], relation_type="comparison-input",
        ),
        _connector(
            "flow-observed-loss", "observed-frame", "comparison-node",
            [[1423, 495], [1423, 453]], relation_type="comparison-input",
        ),
        _connector(
            "feedback-optimize-generator", "comparison-node", "generator-frame",
            [[1383, 437], [1245, 437], [1245, 704], [535, 704], [535, 466]],
            relation_type="parameter-optimization", stroke_token="warm", dash=True,
        ),
    ]

    semantic["figure_id"] = EXAMPLE_ID
    semantic["canvas"].update(
        width=CANVAS_WIDTH,
        height=CANVAS_HEIGHT,
        physical_width_mm=338.67,
        physical_height_mm=190.5,
        background="#FBFBFC",
    )
    semantic["style_tokens"]["colors"].update(
        background="#FBFBFC",
        ink="#0E2061",
        muted="#5F627A",
        warm="#57218C",
        purple="#57218C",
        teal="#125460",
        gold="#C37107",
        cool="#125460",
        accent="#C37107",
        surface="#F7F3FB",
        surface2="#EFF5FB",
        white="#FFFFFF",
    )
    semantic["style_tokens"]["stroke_width"] = 3.2
    semantic["platform_overrides"]["pptx"]["rounded_rects"] = True
    semantic["provenance"] = {
        "truth_source": "../../clarification_brief.md",
        "equation_manifest": "source/equations.tex",
        "generated_at": "2026-08-27T00:00:00Z",
        "source_hashes": {
            "input_sketch": sha256_file(example_root / "sketch.png"),
            "candidate_C": sha256_file(example_root / "candidates" / "C-presentation.png"),
            "selection_approval": sha256_file(selection_path),
        },
        "selection": "candidate C for both layout and visual style",
        "supersedes_selection": "candidate_selection.json",
        "editable_reconstruction_authorized": True,
        "final_scientific_approval": None,
    }

    grouped_objects = [
        *semantic["shapes"],
        *semantic["text_objects"],
        *semantic["equation_objects"],
    ]
    for group in semantic["groups"]:
        group["member_ids"] = [
            item["id"]
            for item in grouped_objects
            if item.get("group_id") == group["id"]
        ]
    semantic["z_order"] = [
        *(item["id"] for item in semantic["groups"]),
        *(item["id"] for item in semantic["shapes"]),
        *(item["id"] for item in semantic["connectors"]),
        *(item["id"] for item in semantic["text_objects"]),
        *(item["id"] for item in semantic["equation_objects"]),
    ]

    errors = semantic_integrity_errors(semantic)
    if errors:
        raise ValueError("invalid C-only semantic source:\n%s" % "\n".join(errors))
    return semantic


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--example-root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "examples" / "deep_image_prior",
    )
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    if output_dir.exists():
        raise ValueError("refusing to overwrite an existing C-only output directory: %s" % output_dir)
    example_root = args.example_root.resolve()
    selection_path = example_root / "candidate_selection_c_only.json"
    semantic = build_semantic(example_root, selection_path)
    source_dir = output_dir / "source"
    write_json(source_dir / "semantic_figure.json", semantic)
    write_text(source_dir / "equations.tex", equation_source(semantic))
    print("wrote %s" % (source_dir / "semantic_figure.json"))
    print("wrote %s" % (source_dir / "equations.tex"))
    print(
        "shapes=%d texts=%d equations=%d connectors=%d"
        % (
            len(semantic["shapes"]),
            len(semantic["text_objects"]),
            len(semantic["equation_objects"]),
            len(semantic["connectors"]),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
