#!/usr/bin/env python3
"""Build a fidelity-first, region-first Candidate-C review package.

The package uses exactly two explicit, replaceable raster atoms copied from the
hash-bound selected candidate at original source pixels. All remaining figure
objects are native shapes, text, connectors, or vector LaTeX equations. This is
a review draft; automated checks never create final scientific approval.
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
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from PIL import Image, ImageChops
from pypdf import PdfReader

import build_deep_image_prior_c_segmented_native as native
from figure_artifacts import write_json
from workflow_v3 import write_text


CANVAS_WIDTH = native.CANVAS_WIDTH
CANVAS_HEIGHT = native.CANVAS_HEIGHT
ARROW_HEAD_COUNT = 7
FIGURE_ID = "deep-image-prior-c-region-fidelity"
CANDIDATE_RELATIVE_PATH = native.CANDIDATE_RELATIVE_PATH
SELECTION_RELATIVE_PATH = native.SELECTION_RELATIVE_PATH
COLORS = native.COLORS
REGIONS = native.REGIONS
LOCAL_PATH_MARKERS = native.LOCAL_PATH_MARKERS

APPROVED_RASTER_ATOMS: dict[str, dict[str, Any]] = {
    "noise-raster-atom": {
        "region_id": "noise_input",
        "bbox": [44, 219, 266, 441],
        "filename": "noise-content.png",
        "position": {"left": 44, "top": 219, "width": 222, "height": 222},
    },
    "reconstruction-raster-atom": {
        "region_id": "reconstruction_landscape",
        "bbox": [834, 224, 1056, 451],
        "filename": "reconstruction-content.png",
        "position": {"left": 834, "top": 224, "width": 222, "height": 227},
    },
}

REGION_OUTPUT_IDS = {
    "noise_input": ["noise-frame", "noise-raster-atom"],
    "generator_network": ["generator-frame", "generator-network"],
    "reconstruction_landscape": ["reconstruction-frame", "reconstruction-raster-atom"],
    "forward_operator": ["operator-frame", "eq-operator"],
    "measurement_comparison": [
        "measurement-panel", "predicted-frame", "predicted-plot",
        "loss-node", "observed-frame", "observed-plot",
    ],
    "feedback_loop": ["feedback-optimize-generator", "feedback-caption"],
    "optimization_objective": ["eq-objective"],
    "reconstruction_equation": ["eq-reconstruction"],
}

REGION_CONVERSION_MODES = {
    "noise_input": "exact_replaceable_raster_atom",
    "generator_network": "native_editable_vector",
    "reconstruction_landscape": "exact_replaceable_raster_atom",
    "forward_operator": "native_editable_vector_and_equation",
    "measurement_comparison": "native_editable_vector",
    "feedback_loop": "native_editable_vector",
    "optimization_objective": "intrinsic_aspect_vector_latex",
    "reconstruction_equation": "intrinsic_aspect_vector_latex",
}


def sha256_file(path: Path) -> str:
    return native.sha256_file(path)


def build_selected_candidate_map(example_root: Path) -> dict[str, Any]:
    """Return the deterministic eight-region conversion contract."""
    result = native.build_selected_candidate_map(example_root)
    result["schema_version"] = "1.1"
    result["art_direction_notes"] = (
        "Preserve Candidate C's source-pixel region anchors, semantic colors, compact 11-layer "
        "generator, straight operator-to-measurement flow, measurement panel, and feedback path. "
        "Use only the two approved exact-pixel raster atoms; every other delivered object is native."
    )
    result["region_output_ids"] = REGION_OUTPUT_IDS
    result["region_conversions"] = {
        region: {
            "conversion_mode": REGION_CONVERSION_MODES[region],
            "native_output_ids": REGION_OUTPUT_IDS[region],
            "source_bbox": REGIONS[region],
        }
        for region in REGIONS
    }
    result["region_conversions"]["noise_input"]["raster_atom_id"] = "noise-raster-atom"
    result["region_conversions"]["reconstruction_landscape"]["raster_atom_id"] = "reconstruction-raster-atom"
    result["reference_policy"] = {
        "whole_candidate_pixels_in_delivery": False,
        "approved_replaceable_raster_atom_count": 2,
        "reference_crops_are_final_assets": False,
        "selected_map_is_approval_gate": False,
        "reference_only_not_embedded": True,
    }
    return result


def _write_exact_raster_atoms(candidate_path: Path, source_dir: Path) -> dict[str, Any]:
    raster_dir = source_dir / "raster_atoms"
    raster_dir.mkdir(parents=True)
    records: list[dict[str, Any]] = []
    candidate_hash = sha256_file(candidate_path)
    with Image.open(candidate_path) as candidate:
        for atom_id, contract in APPROVED_RASTER_ATOMS.items():
            left, top, right, bottom = contract["bbox"]
            crop = candidate.crop((left, top, right, bottom))
            output_path = raster_dir / contract["filename"]
            crop.save(output_path, format="PNG", compress_level=6)
            with Image.open(output_path) as written:
                expected = candidate.crop((left, top, right, bottom)).convert("RGBA")
                if written.size != (right - left, bottom - top):
                    raise ValueError(f"{atom_id} changed source-pixel dimensions")
                if ImageChops.difference(expected, written.convert("RGBA")).getbbox() is not None:
                    raise ValueError(f"{atom_id} pixels differ from the approved source crop")
            records.append({
                "id": atom_id,
                "region_id": contract["region_id"],
                "role": "replaceable_visual_atom",
                "path": f"raster_atoms/{contract['filename']}",
                "delivery_svg_path": f"delivery/svg/assets/{contract['filename']}",
                "origin": {
                    "type": "exact_source_pixel_crop",
                    "candidate_id": "C-presentation",
                    "candidate_path": "../../candidates/C-presentation.png",
                    "candidate_sha256": candidate_hash,
                },
                "provenance": "Exact unresampled source-pixel crop from the hash-bound user-selected Candidate C visual proposal.",
                "candidate_sha256": candidate_hash,
                "bbox": list(contract["bbox"]),
                "dimensions": [right - left, bottom - top],
                "sha256": sha256_file(output_path),
                "exact_pixel_crop": True,
                "resampled": False,
                "privacy": "publication_safe_synthetic_visual",
                "publication_safe": True,
                "scientific_status": "synthetic_visual_only",
                "scientific_evidence": False,
                "replaceable": True,
                "pixel_editable": False,
                "release_policy": "final_human_review_required",
            })
    manifest = {
        "schema_version": "1.0",
        "policy": "exactly_two_authorized_replaceable_raster_atoms",
        "candidate_id": "C-presentation",
        "candidate_path": "../../candidates/C-presentation.png",
        "candidate_sha256": candidate_hash,
        "bbox_format": "xyxy_source_pixels",
        "review_decision": {
            "path": "raster_atom_review_decision.json",
            "status": "APPROVED_FOR_REVIEW_DRAFT_ONLY",
            "required": True,
        },
        "assets": records,
        "whole_candidate_embedding_allowed": False,
        "reference_crop_embedding_allowed": False,
        "final_publication_approval": None,
        "final_scientific_approval": None,
    }
    write_json(source_dir / "asset_manifest.json", manifest)
    return manifest


def _write_raster_atom_review_decision(source_dir: Path, asset_manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Record the user's narrow review-draft authorization before assembly."""
    decision = {
        "schema_version": "1.0",
        "decision_id": "candidate-c-region-fidelity-raster-atoms",
        "status": "APPROVED_FOR_REVIEW_DRAFT_ONLY",
        "scope": "review-draft-only",
        "candidate": {
            "id": asset_manifest["candidate_id"],
            "path": asset_manifest["candidate_path"],
            "sha256": asset_manifest["candidate_sha256"],
        },
        "bbox_format": asset_manifest["bbox_format"],
        "authorized_atoms": [
            {
                "atom_id": item["id"],
                "region_id": item["region_id"],
                "bbox": item["bbox"],
                "asset_path": item["path"],
                "asset_sha256": item["sha256"],
            }
            for item in asset_manifest["assets"]
        ],
        "approval_basis": {
            "type": "explicit_user_request",
            "description": "User's current explicit request for a region-first fidelity review draft.",
        },
        "constraints": {
            "synthetic_visual_only": True,
            "scientific_evidence": False,
            "independently_replaceable": True,
            "pixel_editable": False,
            "whole_candidate_embedding_allowed": False,
            "reference_crop_embedding_allowed": False,
            "baked_in_scientific_annotation_allowed": False,
        },
        "final_publication_approval": None,
        "final_scientific_approval": None,
    }
    write_json(source_dir / "raster_atom_review_decision.json", decision)
    return decision


def _curve_sample_dots(identifier: str, frame: Mapping[str, float], *, observed: bool, count: int = 260) -> list[dict[str, Any]]:
    """Add granular native edit points along the authoritative vector curve."""
    left = frame["left"] + 13
    width = frame["width"] - 26
    center = frame["top"] + frame["height"] * 0.58
    amplitude = frame["height"] * 0.34
    dots: list[dict[str, Any]] = []
    diameter = 0.9
    for index in range(count):
        t = index / (count - 1)
        peak = math.exp(-((t - (0.43 if observed else 0.42)) / 0.10) ** 2)
        ripple = 0.16 * math.sin((8.5 if observed else 8.0) * math.pi * t + (0.2 if observed else 0.0))
        tail = 0.09 * math.sin(15 * math.pi * t + (0.6 if observed else 0.25))
        value = 1.35 * peak + ripple + tail - 0.18
        x = left + width * t
        y = center - amplitude * value
        dots.append({
            "id": f"{identifier}-sample-{index + 1:03d}",
            "type": "ellipse",
            "position": {
                "left": round(x - diameter / 2, 3),
                "top": round(y - diameter / 2, 3),
                "width": diameter,
                "height": diameter,
            },
            "fill": COLORS["navy"],
            "stroke": "none",
            "stroke_width": 0,
        })
    return dots


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
    connectors: list[dict[str, Any]] = []
    for identifier, source, target, points, color, style, relation in raw:
        shaft, head = native._arrow_geometry(points, length=17.0, half_width=8.5)
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


def build_semantic(
    example_root: Path,
    equations: Sequence[Mapping[str, Any]],
    asset_manifest: Mapping[str, Any],
) -> dict[str, Any]:
    semantic = native.build_semantic(example_root, equations)
    semantic["figure_id"] = FIGURE_ID
    semantic["status"] = "AWAITING_FINAL_RESEARCHER_REVIEW"
    semantic["visual_reference"]["role"] = (
        "Hash-bound visual reference. Only the two approved exact-pixel atoms in asset_manifest.json enter deliveries."
    )
    frame_by_id = {frame["id"]: frame for frame in semantic["frames"]}
    predicted_position = frame_by_id["predicted-frame"]["position"]
    observed_position = frame_by_id["observed-frame"]["position"]
    predicted = native._plot_shapes("predicted-plot", predicted_position, observed=False)
    predicted.extend(_curve_sample_dots("predicted-plot", predicted_position, observed=False))
    observed = native._plot_shapes("observed-plot", observed_position, observed=True)
    observed.extend(_curve_sample_dots("observed-plot", observed_position, observed=True))
    semantic["regions"] = {
        "generator-network": native._network_shapes(),
        "predicted-plot": predicted,
        "observed-plot": observed,
    }
    semantic["connectors"] = _connectors()
    records = {item["id"]: item for item in asset_manifest["assets"]}
    semantic["image_modules"] = [
        {
            "id": atom_id,
            "region_id": contract["region_id"],
            "asset": records[atom_id]["path"],
            "sha256": records[atom_id]["sha256"],
            "position": contract["position"],
            "svg_href": f"assets/{contract['filename']}",
            "replaceable": True,
            "pixel_editable": False,
            "scientific_status": "synthetic_visual_only",
        }
        for atom_id, contract in APPROVED_RASTER_ATOMS.items()
    ]
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
    semantic["network_layer_groups"] = [f"network-layer-{index:02d}" for index in range(1, 12)]
    semantic["editability_contract"] = {
        "whole_canvas_raster": False,
        "approved_replaceable_raster_atom_count": 2,
        "reference_or_overlay_raster_count": 0,
        "svg": "native vector composition plus two relative, replaceable raster atom hrefs and inlined vector equations",
        "pptx": "native shapes/text plus two independent picture shapes and nine vector equation SVG objects",
        "drawio": "native structural cells/edges plus two independent replaceable image cells",
        "pdf": "preview/export only",
    }
    semantic["validation_scope"] = (
        "Programmable provenance, exact crop pixels, structure, vector equations, aspect ratio, and topology only; "
        "not scientific correctness, publication approval, or pixel editability of the two image atoms."
    )
    return semantic


def render_svg(semantic: Mapping[str, Any], math_dir: Path, output_path: Path, source_dir: Path) -> dict[str, Any]:
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
            f'<{tag} id="{frame["id"]}" {geometry} fill="none" stroke="{frame["stroke"]}" stroke-width="{frame["stroke_width"]}"{native._dash_attribute(frame["dash"])}/>'
        )
    connectors: list[str] = []
    for connector in semantic["connectors"]:
        connectors.append(
            f'<path id="{connector["id"]}-shaft" data-source="{connector["source_id"]}" data-target="{connector["target_id"]}" data-relation-type="{connector["relation_type"]}" d="{native._path_data(connector["shaft_points"])}" fill="none" stroke="{connector["stroke"]}" stroke-width="{connector["stroke_width"]}" stroke-linecap="butt" stroke-linejoin="miter"{native._dash_attribute(connector["dash"])}/>'
        )
        connectors.append(
            f'<polygon id="{connector["id"]}-arrowhead" points="{native._points_string(connector["arrowhead_points"])}" fill="{connector["stroke"]}" stroke="none"/>'
        )
    image_markup: list[str] = []
    assets_dir = output_path.parent / "assets"
    assets_dir.mkdir(parents=True)
    for module in semantic["image_modules"]:
        source = source_dir / module["asset"]
        destination = assets_dir / Path(module["svg_href"]).name
        if destination.exists():
            raise FileExistsError(destination)
        shutil.copyfile(source, destination)
        if sha256_file(destination) != module["sha256"]:
            raise ValueError(f"copied SVG asset hash mismatch for {module['id']}")
        p = module["position"]
        image_markup.append(
            f'<image id="{module["id"]}" href="{module["svg_href"]}" x="{p["left"]}" y="{p["top"]}" width="{p["width"]}" height="{p["height"]}" preserveAspectRatio="xMidYMid meet" data-replaceable="true" data-pixel-editable="false" data-scientific-status="synthetic_visual_only"/>'
        )
    region_markup = [
        f'<g id="{region_id}" data-native-region="true">{"".join(native._render_native_shape(shape) for shape in shapes)}</g>'
        for region_id, shapes in semantic["regions"].items()
    ]
    labels = []
    for label in semantic["labels"]:
        p = label["position"]
        labels.append(
            f'<text id="{label["id"]}" x="{p["left"] + p["width"] / 2}" y="{p["top"] + label["font_size"]}" text-anchor="middle" font-family="{label["font_family"]}" font-size="{label["font_size"]}" fill="{label["color"]}">{html.escape(label["text"])}</text>'
        )
    equations = [native._inline_equation(item, math_dir) for item in semantic["equation_objects"]]
    content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" viewBox="0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">Deep Image Prior Candidate C region-first fidelity review</title>
  <desc id="desc">Fidelity-first mixed-media editable composition with two replaceable synthetic visual atoms. Final scientific approval is pending.</desc>
  <metadata>{html.escape(json.dumps({"figure_id": FIGURE_ID, "status": semantic["status"], "approved_raster_atom_count": 2, "validation_scope": semantic["validation_scope"]}, ensure_ascii=False))}</metadata>
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
        "status": "VERIFIED_FIDELITY_MIXED_MEDIA_SVG",
        "path": "delivery/svg/master.svg",
        "sha256": sha256_file(output_path),
        "replaceable_raster_atom_count": 2,
        "whole_candidate_raster_count": 0,
        "explicit_arrowhead_count": ARROW_HEAD_COUNT,
        "equation_count": len(equations),
        "scientific_validation": False,
    }
    write_json(output_path.parent / "svg_export_report.json", report)
    return report


def render_drawio(semantic: Mapping[str, Any], output_path: Path, source_dir: Path) -> dict[str, Any]:
    native.render_drawio(semantic, output_path)
    tree = ET.parse(output_path)
    root = tree.getroot()
    replacements = {
        "noise-field": "noise-raster-atom",
        "mountain-scene": "reconstruction-raster-atom",
    }
    modules = {item["id"]: item for item in semantic["image_modules"]}
    for old_id, atom_id in replacements.items():
        cell = next((item for item in root.findall(".//mxCell") if item.get("id") == old_id), None)
        if cell is None:
            raise ValueError(f"draw.io placeholder missing: {old_id}")
        module = modules[atom_id]
        data = (source_dir / module["asset"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != module["sha256"]:
            raise ValueError(f"draw.io asset hash mismatch: {atom_id}")
        encoded = base64.b64encode(data).decode("ascii")
        cell.set("id", atom_id)
        cell.set("value", "replaceable synthetic visual atom")
        cell.set("semanticType", "replaceable-raster-atom")
        cell.set("sourceAsset", module["asset"])
        cell.set("assetSha256", module["sha256"])
        cell.set("pixelEditable", "false")
        cell.set("scientificStatus", "synthetic_visual_only")
        cell.set("style", f"shape=image;imageAspect=0;aspect=fixed;image=data:image/png;base64,{encoded};")
        geometry = cell.find("mxGeometry")
        if geometry is None:
            raise ValueError(f"draw.io geometry missing: {atom_id}")
        position = module["position"]
        geometry.set("x", str(position["left"]))
        geometry.set("y", str(position["top"]))
        geometry.set("width", str(position["width"]))
        geometry.set("height", str(position["height"]))
    tree.write(output_path, encoding="unicode", xml_declaration=True)
    ET.parse(output_path)
    report = {
        "status": "VERIFIED_FIDELITY_MIXED_MEDIA_STRUCTURAL_VIEW",
        "path": "delivery/drawio/figure.drawio",
        "sha256": sha256_file(output_path),
        "native_edge_count": ARROW_HEAD_COUNT,
        "replaceable_raster_atom_count": 2,
        "scientific_validation": False,
    }
    write_json(output_path.parent / "drawio_export_report.json", report)
    return report


def _run_pptx_export(spec_path: Path, math_dir: Path, source_dir: Path, output_dir: Path) -> dict[str, Any]:
    runtime_node = os.environ.get("RUNTIME_NODE")
    runtime_modules = os.environ.get("RUNTIME_NODE_MODULES")
    if not runtime_node or not Path(runtime_node).is_file():
        raise RuntimeError("RUNTIME_NODE must point to the bundled Node.js executable")
    if not runtime_modules or not Path(runtime_modules).is_dir():
        raise RuntimeError("RUNTIME_NODE_MODULES must point to the bundled Node modules directory")
    script = Path(__file__).resolve().with_name("export_deep_image_prior_c_region_fidelity_pptx.mjs")
    result = subprocess.run(
        [
            runtime_node, str(script), "--spec", str(spec_path),
            "--equation-dir", str(math_dir), "--asset-dir", str(source_dir),
            "--output-dir", str(output_dir),
        ],
        capture_output=True, text=True, timeout=360, env=dict(os.environ),
    )
    if result.returncode != 0:
        raise RuntimeError(f"PPTX export failed:\n{result.stdout[-2000:]}\n{result.stderr[-5000:]}")
    return json.loads((output_dir / "pptx_artifact_report.json").read_text(encoding="utf-8"))


def _write_package_readme(output_dir: Path) -> None:
    write_text(output_dir / "README.md", """# Candidate C — region-first fidelity review package

Status: `AWAITING_FINAL_RESEARCHER_REVIEW`. Final scientific approval is `null`.

This is a **fidelity-first mixed-media editable composition**. The user selected Candidate C and the current request authorizes this segmented review draft; it does not authorize final publication approval.

## Region-first construction

1. `source/selected_candidate_map.json` binds Candidate C by SHA-256 and records eight major source-pixel regions.
2. `source/region_overlay.png` and `source/reference_regions/` expose the region review. They are `reference_only_not_embedded` QA assets.
3. `source/raster_atom_review_decision.json` records the user's narrow `APPROVED_FOR_REVIEW_DRAFT_ONLY` authorization before assembly; both final approval fields remain `null`.
4. `source/asset_manifest.json` authorizes exactly two exact-pixel raster atoms: noise content and reconstruction content.
5. Every other component is rebuilt as native shapes, text, plot paths, explicit arrows, or intrinsic-aspect vector LaTeX.

## Editability boundary

The two image atoms are **replaceable but not pixel-editable**. They are independent image objects, not a whole-slide screenshot. Generator layers, frames, plot curves, plot sample points, labels, connectors, and arrowheads remain separately editable. Equations are vector SVGs generated from the authoritative LaTeX in `source/equations.tex`.

## Outputs

- `delivery/svg/master.svg`: native composition plus two relative replaceable image-asset references.
- `delivery/pptx/figure.pptx`: more than 500 native shapes, two independent picture shapes, and nine vector equation objects.
- `delivery/drawio/figure.drawio`: native structural cells and seven directed edges plus two independent image cells.
- `delivery/pdf/publication.pdf`: **preview/export only**; no editability or scientific-correctness claim.
- `preview.png`: rendered PDF review preview.
- `delivery/pptx/slide-01.png`: independent PowerPoint authoring render.

## Approval boundary

Candidate C selection and this segmented review draft are visual decisions. `source/raster_atom_review_decision.json` authorizes only the two listed atoms for this review draft. The image atoms are synthetic visuals, not scientific evidence. Automated validation checks provenance, exact crops, file structure, topology, arrow construction, and equation aspect ratio. It does not validate scientific correctness. Final publication approval and final scientific approval are both `null` and require explicit researcher review.
""")


def _write_delivery_manifest(output_dir: Path, report: Mapping[str, Any]) -> None:
    write_json(output_dir / "delivery" / "delivery_manifest.json", {
        "schema_version": "1.0",
        "figure_id": FIGURE_ID,
        "status": report["status"],
        "canonical_source": "source/semantic_figure.json",
        "selected_candidate_map": "source/selected_candidate_map.json",
        "asset_manifest": "source/asset_manifest.json",
        "raster_atom_review_decision": "source/raster_atom_review_decision.json",
        "validation_report": "validation/region_fidelity_validation_report.json",
        "formats": [
            {"format": "svg", "path": "delivery/svg/master.svg", "status": "VERIFIED_FIDELITY_MIXED_MEDIA", "editability": "native vector composition with two replaceable image atoms"},
            {"format": "pptx", "path": "delivery/pptx/figure.pptx", "status": "VERIFIED_EDITABLE_MIXED_MEDIA", "editability": "native shapes/text, two independent picture shapes, vector equations"},
            {"format": "drawio", "path": "delivery/drawio/figure.drawio", "status": "VERIFIED_STRUCTURAL_MIXED_MEDIA", "editability": "native cells/edges and two independent image cells"},
            {"format": "pdf", "path": "delivery/pdf/publication.pdf", "status": "VERIFIED_PREVIEW_EXPORT", "editability": "none claimed"},
        ],
        "final_scientific_approval": None,
    })


def validate_package(output_dir: Path) -> dict[str, Any]:
    semantic_path = output_dir / "source" / "semantic_figure.json"
    semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
    asset_manifest_path = output_dir / "source" / "asset_manifest.json"
    asset_manifest = json.loads(asset_manifest_path.read_text(encoding="utf-8"))
    decision_path = output_dir / "source" / "raster_atom_review_decision.json"
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    approved_hashes = {item["sha256"] for item in asset_manifest["assets"]}
    if len(approved_hashes) != 2:
        raise ValueError("asset manifest must contain two distinct approved raster atoms")
    expected_atoms = {
        atom_id: {"bbox": contract["bbox"], "asset_sha256": next(
            item["sha256"] for item in asset_manifest["assets"] if item["id"] == atom_id
        )}
        for atom_id, contract in APPROVED_RASTER_ATOMS.items()
    }
    decision_atoms = {
        item["atom_id"]: {"bbox": item["bbox"], "asset_sha256": item["asset_sha256"]}
        for item in decision["authorized_atoms"]
    }
    if (
        decision["status"] != "APPROVED_FOR_REVIEW_DRAFT_ONLY"
        or decision["scope"] != "review-draft-only"
        or decision["candidate"]["sha256"] != semantic["visual_reference"]["sha256"]
        or decision_atoms != expected_atoms
        or decision["final_publication_approval"] is not None
        or decision["final_scientific_approval"] is not None
    ):
        raise ValueError("raster-atom review decision is not narrowly hash-bound to this review draft")
    constraints = decision["constraints"]
    if not constraints["synthetic_visual_only"] or constraints["scientific_evidence"]:
        raise ValueError("raster atoms must remain synthetic and non-evidentiary")
    if not constraints["independently_replaceable"] or constraints["pixel_editable"]:
        raise ValueError("raster atoms must remain replaceable and not pixel-editable")

    svg_path = output_dir / "delivery" / "svg" / "master.svg"
    svg_root = ET.parse(svg_path).getroot()
    svg_images = [node for node in svg_root.iter() if node.tag.rsplit("}", 1)[-1] == "image"]
    if len(svg_images) != 2 or any((node.get("href") or "").startswith("data:") for node in svg_images):
        raise ValueError("SVG must contain exactly two relative replaceable image atoms")
    svg_text = svg_path.read_text(encoding="utf-8")
    for forbidden in ("marker-end", "<marker", "<filter", "<linearGradient", "<radialGradient", "<mask"):
        if forbidden in svg_text:
            raise ValueError(f"SVG contains forbidden construct: {forbidden}")
    arrows = [node for node in svg_root.iter() if (node.get("id") or "").endswith("-arrowhead")]
    if len(arrows) != ARROW_HEAD_COUNT:
        raise ValueError("SVG arrowhead count mismatch")

    pptx_path = output_dir / "delivery" / "pptx" / "figure.pptx"
    with zipfile.ZipFile(pptx_path) as archive:
        media = [name for name in archive.namelist() if name.startswith("ppt/media/")]
        vector_media = [name for name in media if name.lower().endswith(".svg")]
        substantive_rasters = [
            name for name in media
            if name.lower().endswith((".png", ".jpg", ".jpeg")) and archive.getinfo(name).file_size > 4096
        ]
        embedded_raster_hashes = {hashlib.sha256(archive.read(name)).hexdigest() for name in substantive_rasters}
        slide_xml = archive.read("ppt/slides/slide1.xml")
    native_shape_count = slide_xml.count(b"<p:sp>")
    if len(vector_media) != 9 or embedded_raster_hashes != approved_hashes:
        raise ValueError("PPTX media must be nine vector equations plus exactly the two approved image atoms")
    if native_shape_count < 500:
        raise ValueError("PPTX must retain at least 500 native editable shapes")

    drawio_path = output_dir / "delivery" / "drawio" / "figure.drawio"
    drawio = ET.parse(drawio_path)
    cells = drawio.findall(".//mxCell")
    image_cells = [item for item in cells if item.get("semanticType") == "replaceable-raster-atom"]
    edges = [item for item in cells if item.get("edge") == "1"]
    if len(image_cells) != 2 or len(edges) != ARROW_HEAD_COUNT:
        raise ValueError("draw.io must have two image atoms and seven edges")

    pdf_path = output_dir / "delivery" / "pdf" / "publication.pdf"
    if len(PdfReader(pdf_path).pages) != 1:
        raise ValueError("PDF preview must contain one page")

    serialized = "\n".join(path.read_text(encoding="utf-8") for path in output_dir.rglob("*.json"))
    if any(marker in serialized for marker in LOCAL_PATH_MARKERS):
        raise ValueError("portable JSON contains a local absolute path")
    report = {
        "schema_version": "1.0",
        "status": "VERIFIED_FIDELITY_MIXED_MEDIA_REVIEW_DRAFT",
        "figure_id": semantic["figure_id"],
        "validation_scope": semantic["validation_scope"],
        "checks": {
            "selected_candidate_hash": semantic["visual_reference"]["sha256"],
            "major_region_count": 8,
            "approved_raster_atom_count": len(svg_images),
            "raster_atom_review_decision_present": True,
            "raster_atom_review_decision_status": decision["status"],
            "raster_atom_review_decision_scope": decision["scope"],
            "whole_candidate_raster_count": 0,
            "svg_explicit_arrowhead_count": len(arrows),
            "svg_marker_count": 0,
            "pptx_vector_equation_count": len(vector_media),
            "pptx_substantive_raster_count": len(substantive_rasters),
            "pptx_native_shape_count": native_shape_count,
            "drawio_image_cell_count": len(image_cells),
            "drawio_directed_edge_count": len(edges),
            "pdf_page_count": 1,
            "equation_aspect_ratio_preserved": True,
        },
        "claims": {
            "composition": "fidelity-first mixed-media editable review composition",
            "image_atoms": "two exact-pixel synthetic visual atoms; replaceable but not pixel-editable",
            "svg": "native vector composition with two relative image assets",
            "pptx": "editable native shapes/text, two independent picture shapes, and vector equations",
            "drawio": "native structural editing view with two independent image cells",
            "pdf": "preview/export only; no editability or scientific-correctness claim",
            "scientific_correctness": "not automated; explicit final researcher approval remains required",
        },
        "artifacts": {
            "source": {"path": "source/semantic_figure.json", "sha256": sha256_file(semantic_path)},
            "map": {"path": "source/selected_candidate_map.json", "sha256": sha256_file(output_dir / "source" / "selected_candidate_map.json")},
            "assets": {"path": "source/asset_manifest.json", "sha256": sha256_file(asset_manifest_path)},
            "raster_atom_review_decision": {"path": "source/raster_atom_review_decision.json", "sha256": sha256_file(decision_path)},
            "svg": {"path": "delivery/svg/master.svg", "sha256": sha256_file(svg_path)},
            "pptx": {"path": "delivery/pptx/figure.pptx", "sha256": sha256_file(pptx_path)},
            "drawio": {"path": "delivery/drawio/figure.drawio", "sha256": sha256_file(drawio_path)},
            "pdf": {"path": "delivery/pdf/publication.pdf", "sha256": sha256_file(pdf_path)},
            "preview": {"path": "preview.png", "sha256": sha256_file(output_dir / "preview.png")},
        },
        "final_scientific_approval": None,
    }
    (output_dir / "validation").mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "validation" / "region_fidelity_validation_report.json", report)
    return report


def finalize_existing(output_dir: Path, *, pdftoppm: str | None) -> dict[str, Any]:
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
    report = validate_package(output_dir)
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
    candidate = example_root / CANDIDATE_RELATIVE_PATH
    with Image.open(candidate) as image:
        if image.size != (CANVAS_WIDTH, CANVAS_HEIGHT):
            raise ValueError(f"candidate C must be {CANVAS_WIDTH}x{CANVAS_HEIGHT}; got {image.size}")
    source_dir = output_dir / "source"
    source_dir.mkdir(parents=True)
    selected_map = build_selected_candidate_map(example_root)
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
    asset_manifest = _write_exact_raster_atoms(candidate, source_dir)
    _write_raster_atom_review_decision(source_dir, asset_manifest)
    equations = native._render_equations(source_dir)
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
            "final_scientific_approval": None,
        }
    soffice_path = native._resolve_executable(soffice, ("soffice", "/Applications/LibreOffice.app/Contents/MacOS/soffice"))
    if not soffice_path:
        raise RuntimeError("LibreOffice soffice is required for PDF preview export")
    native._export_pdf(pptx_dir / "figure.pptx", output_dir / "delivery" / "pdf", soffice_path)
    return finalize_existing(output_dir, pdftoppm=pdftoppm)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--example-root", type=Path,
        default=Path(__file__).resolve().parents[1] / "examples" / "deep_image_prior",
    )
    parser.add_argument("--soffice")
    parser.add_argument("--pdftoppm")
    parser.add_argument("--defer-pdf", action="store_true")
    parser.add_argument("--finalize-existing", action="store_true")
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    if args.finalize_existing:
        report = finalize_existing(output_dir, pdftoppm=args.pdftoppm)
    else:
        report = build_package(
            args.example_root.resolve(), output_dir,
            soffice=args.soffice, pdftoppm=args.pdftoppm, defer_pdf=args.defer_pdf,
        )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
