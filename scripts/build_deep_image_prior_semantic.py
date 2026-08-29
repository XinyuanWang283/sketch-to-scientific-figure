#!/usr/bin/env python3
"""Build the native semantic source for the approved Deep Image Prior example.

The researcher approved candidate D as the layout reference and candidate C as
the visual-style reference.  This builder converts that decision into a
deterministic, raster-free semantic source consumed by all delivery adapters.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

from figure_artifacts import write_json
from workflow_v3 import semantic_integrity_errors, write_text


CANVAS_WIDTH = 1600
CANVAS_HEIGHT = 900
EXAMPLE_ID = "deep-image-prior-D-layout-C-style"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_semantic(
    example_root: Path | None,
    selection_path: Path | None,
) -> dict[str, Any]:
    shapes: list[dict[str, Any]] = []
    texts: list[dict[str, Any]] = []
    equations: list[dict[str, Any]] = []
    connectors: list[dict[str, Any]] = []
    entities: list[dict[str, Any]] = []
    group_members: dict[str, list[str]] = {
        "input-noise": [],
        "generator": [],
        "reconstruction": [],
        "forward-operator": [],
        "predicted-measurement": [],
        "observed-measurement": [],
        "data-consistency": [],
        "optimization": [],
        "figure-context": [],
    }

    def remember(identifier: str, group_id: str | None) -> None:
        if group_id:
            group_members[group_id].append(identifier)

    def rect(
        identifier: str,
        x: float,
        y: float,
        width: float,
        height: float,
        *,
        fill: str,
        stroke: str,
        stroke_width: float = 2.2,
        rx: float = 8,
        group_id: str | None = None,
        entity_type: str = "shape",
        stage: str = "global",
        dash: str | None = None,
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
        shapes.append(item)
        entities.append({"id": identifier, "entity_type": entity_type, "stage": stage})
        remember(identifier, group_id)

    def ellipse(
        identifier: str,
        cx: float,
        cy: float,
        rx: float,
        ry: float,
        *,
        fill: str,
        stroke: str,
        stroke_width: float = 2.2,
        group_id: str | None = None,
        entity_type: str = "shape",
        stage: str = "global",
    ) -> None:
        shapes.append({
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
        })
        entities.append({"id": identifier, "entity_type": entity_type, "stage": stage})
        remember(identifier, group_id)

    def text(
        identifier: str,
        value: str,
        x: float,
        y: float,
        *,
        font_size: float = 20,
        font_weight: int = 400,
        fill_token: str = "ink",
        anchor: str = "middle",
        group_id: str | None = None,
    ) -> None:
        texts.append({
            "id": identifier,
            "text": value,
            "x": x,
            "y": y,
            "font_size": font_size,
            "font_weight": font_weight,
            "font_family": "Aptos, Arial, Helvetica, sans-serif",
            "fill_token": fill_token,
            "text_anchor": anchor,
            "group_id": group_id,
        })
        remember(identifier, group_id)

    def equation(
        identifier: str,
        equation_id: str,
        latex_source: str,
        fallback_text: str,
        x: float,
        y: float,
        *,
        width: float,
        height: float,
        font_size: float,
        anchor: str = "middle",
        group_id: str | None = None,
    ) -> None:
        equations.append({
            "id": identifier,
            "equation_id": equation_id,
            "latex_source": latex_source,
            "fallback_text": fallback_text,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "font_size": font_size,
            "font_family": "STIX Two Text, Cambria Math, serif",
            "font_style": "italic",
            "text_anchor": anchor,
            "group_id": group_id,
        })
        remember(identifier, group_id)

    def connector(
        identifier: str,
        source_id: str,
        target_id: str,
        points: list[list[float]],
        *,
        relation_type: str,
        stroke_token: str = "ink",
        dash: bool = False,
    ) -> None:
        connectors.append({
            "id": identifier,
            "source_id": source_id,
            "target_id": target_id,
            "relation_type": relation_type,
            "direction": "forward",
            "points": points,
            "arrow": "end",
            "stroke_token": stroke_token,
            "dash": dash,
        })

    # Figure context.
    text("title", "Deep Image Prior", 52, 64, font_size=29, font_weight=700, fill_token="purple", anchor="start", group_id="figure-context")
    text(
        "subtitle",
        "Optimize an untrained generator for one observed measurement",
        52,
        102,
        font_size=19,
        fill_token="muted",
        anchor="start",
        group_id="figure-context",
    )

    # Fixed random input z: every dot is a native vector object.
    rect(
        "noise-frame", 60, 210, 170, 170,
        fill="#F8FAFF", stroke="#17356B", stroke_width=3.0, rx=12,
        group_id="input-noise", entity_type="input", stage="input",
    )
    dot_palette = ("#17356B", "#6C4FD3", "#3F6FAE", "#8FA7C9")
    for row in range(9):
        for column in range(9):
            offset_x = ((row * 7 + column * 11) % 5) - 2
            offset_y = ((row * 13 + column * 3) % 5) - 2
            radius = 2.1 + ((row * 5 + column * 7) % 4) * 0.45
            color = dot_palette[(row * 3 + column * 5) % len(dot_palette)]
            ellipse(
                f"noise-dot-{row + 1:02d}-{column + 1:02d}",
                78 + column * 17 + offset_x,
                228 + row * 17 + offset_y,
                radius,
                radius,
                fill=color,
                stroke=color,
                stroke_width=0.6,
                group_id="input-noise",
                entity_type="noise-sample",
                stage="input",
            )
    equation("eq-z", "eq_z", r"z", "z", 145, 190, width=80, height=48, font_size=42, group_id="input-noise")
    text("noise-caption", "fixed random input", 145, 413, font_size=18, fill_token="muted", group_id="input-noise")

    # C-style dimensional encoder-decoder, placed according to D's layout.
    rect(
        "generator-frame", 320, 145, 430, 310,
        fill="#F7F3FF", stroke="#6C4FD3", stroke_width=3.2, rx=18,
        group_id="generator", entity_type="model", stage="generation",
    )
    equation("eq-generator", "eq_generator", r"G_{\theta}", "Gθ", 535, 202, width=150, height=55, font_size=43, group_id="generator")

    encoder_specs = [
        (370, 226, 30, 150, "#7057C8"),
        (414, 242, 28, 118, "#8069D2"),
        (456, 258, 26, 86, "#927DDB"),
        (495, 272, 24, 58, "#A794E4"),
    ]
    decoder_specs = [
        (551, 272, 24, 58, "#A794E4"),
        (588, 258, 26, 86, "#927DDB"),
        (628, 242, 28, 118, "#8069D2"),
        (670, 226, 30, 150, "#7057C8"),
    ]
    for side, specifications in (("enc", encoder_specs), ("dec", decoder_specs)):
        for index, (x, y, width, height, color) in enumerate(specifications, start=1):
            rect(
                f"{side}-block-{index}-back", x + 8, y - 7, width, height,
                fill="#D9D0F3", stroke="#A693DF", stroke_width=1.2, rx=4,
                group_id="generator", entity_type="network-layer", stage="generation",
            )
            rect(
                f"{side}-block-{index}-front", x, y, width, height,
                fill=color, stroke="#5741B5", stroke_width=1.8, rx=4,
                group_id="generator", entity_type="network-layer", stage="generation",
            )
    rect(
        "bottleneck-back", 535, 279, 18, 52,
        fill="#D9D0F3", stroke="#A693DF", stroke_width=1.2, rx=4,
        group_id="generator", entity_type="network-layer", stage="generation",
    )
    rect(
        "bottleneck-front", 527, 286, 18, 52,
        fill="#5C43B5", stroke="#49328F", stroke_width=1.8, rx=4,
        group_id="generator", entity_type="network-layer", stage="generation",
    )
    for index, x in enumerate((520, 562), start=1):
        for dot_index in range(3):
            ellipse(
                f"latent-link-{index}-{dot_index + 1}",
                x + dot_index * (14 if index == 1 else -14),
                312,
                2.7,
                2.7,
                fill="#6C4FD3",
                stroke="#6C4FD3",
                stroke_width=0.5,
                group_id="generator",
                entity_type="latent-link",
                stage="generation",
            )
    text("generator-caption", "untrained encoder–decoder", 535, 425, font_size=19, fill_token="purple", group_id="generator")

    # Native, abstract reconstruction glyph: a layered mountain skyline made of editable bars.
    rect(
        "reconstruction-background", 825, 210, 190, 170,
        fill="#EEF4FA", stroke="#16868A", stroke_width=3.0, rx=12,
        group_id="reconstruction", entity_type="reconstruction", stage="reconstruction",
    )
    mountain_heights = [18, 24, 32, 44, 62, 82, 108, 132, 112, 94, 78, 66, 58, 76, 96, 116, 98, 82, 70, 60, 52, 45, 38, 32]
    for index, height in enumerate(mountain_heights):
        x = 836 + index * 7
        fill = "#60718D" if index < 12 else "#445873"
        rect(
            f"mountain-column-{index + 1:02d}", x, 366 - height, 7.5, height,
            fill=fill, stroke=fill, stroke_width=0.5, rx=0,
            group_id="reconstruction", entity_type="reconstruction-glyph", stage="reconstruction",
        )
    foreground_heights = [10, 14, 20, 28, 36, 48, 58, 70, 65, 54, 45, 38, 32, 28, 36, 48, 58, 64, 56, 46, 38, 30, 24, 18]
    for index, height in enumerate(foreground_heights):
        x = 836 + index * 7
        rect(
            f"foreground-column-{index + 1:02d}", x, 366 - height, 7.5, height,
            fill="#263B55", stroke="#263B55", stroke_width=0.5, rx=0,
            group_id="reconstruction", entity_type="reconstruction-glyph", stage="reconstruction",
        )
    equation("eq-xhat", "eq_xhat", r"\hat{x}", "x̂", 920, 190, width=90, height=52, font_size=44, group_id="reconstruction")
    text("reconstruction-caption", "current reconstruction", 920, 413, font_size=18, fill_token="teal", group_id="reconstruction")

    # Forward operator A.
    rect(
        "operator-frame", 1090, 245, 100, 100,
        fill="#FFF7E8", stroke="#C78312", stroke_width=3.0, rx=16,
        group_id="forward-operator", entity_type="forward-operator", stage="measurement",
    )
    equation("eq-operator", "eq_operator", r"A", "A", 1140, 316, width=80, height=58, font_size=48, group_id="forward-operator")
    text("operator-caption", "forward operator", 1140, 378, font_size=17, fill_token="gold", group_id="forward-operator")

    def add_measurement_plot(
        prefix: str,
        frame_y: float,
        values: list[float],
        *,
        group_id: str,
        entity_type: str,
    ) -> None:
        rect(
            f"{prefix}-frame", 1285, frame_y, 250, 150,
            fill="#FFFFFF", stroke="#17356B", stroke_width=3.0, rx=12,
            group_id=group_id, entity_type=entity_type, stage="measurement",
        )
        for index in range(1, 5):
            rect(
                f"{prefix}-grid-v-{index}", 1285 + index * 50, frame_y + 14, 1.2, 122,
                fill="#D9E3F0", stroke="#D9E3F0", stroke_width=0.4, rx=0,
                group_id=group_id, entity_type="plot-grid", stage="measurement",
            )
        for index in range(1, 3):
            rect(
                f"{prefix}-grid-h-{index}", 1298, frame_y + index * 50, 224, 1.2,
                fill="#D9E3F0", stroke="#D9E3F0", stroke_width=0.4, rx=0,
                group_id=group_id, entity_type="plot-grid", stage="measurement",
            )
        for index, value in enumerate(values):
            ellipse(
                f"{prefix}-sample-{index + 1:02d}",
                1300 + index * 11.5,
                frame_y + value,
                3.7,
                3.7,
                fill="#17356B",
                stroke="#17356B",
                stroke_width=0.6,
                group_id=group_id,
                entity_type="measurement-sample",
                stage="measurement",
            )

    predicted_values = [88, 82, 72, 54, 34, 24, 30, 50, 78, 96, 94, 82, 68, 64, 72, 86, 98, 92, 74, 64]
    observed_values = [91, 84, 70, 51, 31, 27, 36, 57, 82, 93, 88, 75, 62, 66, 79, 91, 94, 84, 69, 60]
    add_measurement_plot("predicted", 195, predicted_values, group_id="predicted-measurement", entity_type="predicted-measurement")
    equation("eq-yhat", "eq_yhat", r"\hat{y}", "ŷ", 1410, 176, width=90, height=52, font_size=43, group_id="predicted-measurement")
    text("predicted-caption", "predicted measurement", 1410, 378, font_size=18, fill_token="muted", group_id="predicted-measurement")

    add_measurement_plot("observed", 520, observed_values, group_id="observed-measurement", entity_type="observed-measurement")
    equation("eq-y", "eq_y", r"y", "y", 1410, 502, width=70, height=48, font_size=42, group_id="observed-measurement")
    text("observed-caption", "observed measurement", 1410, 704, font_size=18, fill_token="muted", group_id="observed-measurement")

    # Explicit data-consistency comparison and optimization feedback.
    ellipse(
        "comparison-node", 1155, 575, 33, 33,
        fill="#FFFFFF", stroke="#17356B", stroke_width=3.0,
        group_id="data-consistency", entity_type="comparison", stage="optimization",
    )
    rect(
        "comparison-minus-bar", 1144, 573, 22, 3.5,
        fill="#17356B", stroke="#17356B", stroke_width=0.6, rx=1,
        group_id="data-consistency", entity_type="comparison-symbol", stage="optimization",
    )
    rect(
        "loss-box", 1090, 660, 130, 72,
        fill="#F5F0FF", stroke="#6C4FD3", stroke_width=3.0, rx=14,
        group_id="data-consistency", entity_type="loss", stage="optimization",
    )
    equation("eq-loss", "eq_loss", r"\lVert\cdot\rVert_2^2", "‖·‖²₂", 1155, 709, width=110, height=44, font_size=34, group_id="data-consistency")
    text("loss-caption", "data-consistency loss", 1155, 758, font_size=17, fill_token="purple", group_id="data-consistency")
    text("feedback-caption", "optimize θ", 845, 778, font_size=19, font_weight=600, fill_token="purple", group_id="optimization")

    # D-layout topology, with a corrected unambiguous predicted/observed comparison.
    connector("flow-z-generator", "noise-frame", "generator-frame", [[230, 295], [320, 295]], relation_type="generator-input")
    connector("flow-generator-reconstruction", "generator-frame", "reconstruction-background", [[750, 295], [825, 295]], relation_type="reconstruction")
    connector("flow-reconstruction-operator", "reconstruction-background", "operator-frame", [[1015, 295], [1090, 295]], relation_type="forward-model-input")
    connector("flow-operator-predicted", "operator-frame", "predicted-frame", [[1190, 295], [1285, 295]], relation_type="predicted-measurement")
    connector(
        "flow-predicted-comparison", "predicted-frame", "comparison-node",
        [[1285, 345], [1245, 445], [1155, 445], [1155, 542]],
        relation_type="comparison-input",
    )
    connector(
        "flow-observed-comparison", "observed-frame", "comparison-node",
        [[1285, 595], [1188, 595]],
        relation_type="comparison-input",
    )
    connector("flow-comparison-loss", "comparison-node", "loss-box", [[1155, 608], [1155, 660]], relation_type="loss-evaluation")
    connector(
        "feedback-optimize-generator", "loss-box", "generator-frame",
        [[1090, 696], [1030, 696], [1030, 790], [535, 790], [535, 455]],
        relation_type="parameter-optimization", stroke_token="warm", dash=True,
    )

    equation(
        "eq-objective", "eq_objective",
        r"\theta^\* = \operatorname*{arg\,min}_{\theta}\lVert A G_{\theta}(z)-y\rVert_2^2",
        "θ* = arg minθ ‖A Gθ(z) − y‖²₂",
        55, 852, width=760, height=55, font_size=31, anchor="start", group_id="optimization",
    )
    equation(
        "eq-reconstruction", "eq_reconstruction",
        r"\hat{x}=G_{\theta^\*}(z)",
        "x̂ = Gθ*(z)",
        1015, 852, width=360, height=55, font_size=31, group_id="optimization",
    )

    groups = [
        {"id": identifier, "role": identifier.replace("-", " "), "member_ids": members}
        for identifier, members in group_members.items()
    ]
    z_order = [
        *(item["id"] for item in groups),
        *(item["id"] for item in shapes),
        *(item["id"] for item in connectors),
        *(item["id"] for item in texts),
        *(item["id"] for item in equations),
    ]
    semantic = {
        "schema_version": "1.0",
        "figure_id": EXAMPLE_ID,
        "canvas": {
            "width": CANVAS_WIDTH,
            "height": CANVAS_HEIGHT,
            "physical_width_mm": 338.67,
            "physical_height_mm": 190.5,
            "background": "#FCFBFF",
        },
        "entities": entities,
        "groups": groups,
        "shapes": shapes,
        "text_objects": texts,
        "equation_objects": equations,
        "ports": [],
        "connectors": connectors,
        "z_order": z_order,
        "style_tokens": {
            "colors": {
                "background": "#FCFBFF",
                "ink": "#14213D",
                "muted": "#5C6680",
                "warm": "#6C4FD3",
                "purple": "#6C4FD3",
                "teal": "#16868A",
                "gold": "#B86F05",
                "cool": "#16868A",
                "accent": "#C78312",
                "surface": "#F7F3FF",
                "surface2": "#EEF4FA",
                "white": "#FFFFFF"
            },
            "stroke_width": 2.4,
            "font_family": "Aptos, Arial, Helvetica, sans-serif",
        },
        "platform_overrides": {
            "pptx": {"all_objects_native": True, "whole_canvas_raster": False},
            "drawio": {"all_nodes_and_edges_native": True, "whole_canvas_raster": False},
            "pdf": {"role": "preview_export_not_editable_source"},
        },
        "provenance": {},
    }
    if (example_root is None) != (selection_path is None):
        raise ValueError("example_root and selection_path must both be supplied or both be omitted")
    if example_root is None:
        semantic["provenance"] = {
            "truth_source": "unbound Deep Image Prior semantic scaffold",
            "equation_manifest": "source/equations.tex",
            "generated_at": "2026-08-27T00:00:00Z",
            "source_hashes": {},
            "selection": "none; scaffold only",
            "editable_reconstruction_authorized": False,
            "final_scientific_approval": None,
        }
    else:
        assert selection_path is not None
        semantic["provenance"] = {
            "truth_source": "../../clarification_brief.md",
            "equation_manifest": "source/equations.tex",
            "generated_at": "2026-08-27T00:00:00Z",
            "source_hashes": {
                "input_sketch": sha256_file(example_root / "sketch.png"),
                "layout_reference_D": sha256_file(example_root / "candidates" / "D-alternative-layout.png"),
                "visual_style_reference_C": sha256_file(example_root / "candidates" / "C-presentation.png"),
                "selection_approval": sha256_file(selection_path),
            },
            "selection": "D layout with C visual style",
            "editable_reconstruction_authorized": True,
            "final_scientific_approval": None,
        }
    errors = semantic_integrity_errors(semantic)
    if errors:
        raise ValueError("invalid generated semantic source:\n%s" % "\n".join(errors))
    return semantic


def build_semantic_scaffold() -> dict[str, Any]:
    """Return neutral native objects without reading any candidate or approval file."""

    return build_semantic(None, None)


def equation_source(semantic: dict[str, Any]) -> str:
    blocks = []
    for item in semantic["equation_objects"]:
        blocks.append("%% equation-id: %s\n\\[\n%s\n\\]" % (item["equation_id"], item["latex_source"]))
    return "\n\n".join(blocks) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--example-root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "examples" / "deep_image_prior",
    )
    args = parser.parse_args()
    example_root = args.example_root.resolve()
    selection_path = example_root / "candidate_selection.json"
    semantic = build_semantic(example_root, selection_path)
    source_dir = args.output_dir.resolve() / "source"
    write_json(source_dir / "semantic_figure.json", semantic)
    write_text(source_dir / "equations.tex", equation_source(semantic))
    print("wrote %s" % (source_dir / "semantic_figure.json"))
    print("wrote %s" % (source_dir / "equations.tex"))
    print("shapes=%d texts=%d equations=%d connectors=%d" % (
        len(semantic["shapes"]),
        len(semantic["text_objects"]),
        len(semantic["equation_objects"]),
        len(semantic["connectors"]),
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
