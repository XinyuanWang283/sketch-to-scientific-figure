#!/usr/bin/env python3
"""Build source-linked editorial artifacts before visual production."""

from __future__ import annotations

import argparse
import json
import shutil
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence, Tuple

from figure_artifacts import load_json, sha256_file, write_json
from workflow_v3 import (
    esc,
    render_svg_to_png,
    require_valid,
    save_validated_json,
    svg_document,
    utc_now,
    write_text,
)


OVERLAY_START = "  <!-- PAPER_AWARE_OVERLAY_START -->\n"
OVERLAY_END = "  <!-- PAPER_AWARE_OVERLAY_END -->\n"


def locate(path: Path, needle: str) -> Tuple[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    lowered = needle.lower()
    for index, line in enumerate(lines, start=1):
        if lowered in line.lower():
            return "line %d" % index, line.strip()
    for index, line in enumerate(lines, start=1):
        if line.strip():
            return "line %d" % index, line.strip()
    return "file-level", path.name


def evidence(path: Path, needle: str) -> Dict[str, str]:
    locator, evidence_text = locate(path, needle)
    return {
        "source_path": str(path.resolve()),
        "locator": locator,
        "source_hash": sha256_file(path),
        "evidence_text": evidence_text,
    }


def resolve_approved_wireframe_preview(
    visual_plan_path: Path,
    approved_wireframe_png: Path | None = None,
) -> Path:
    if approved_wireframe_png is not None:
        return approved_wireframe_png.resolve()
    visual_plan = load_json(visual_plan_path)
    configured = visual_plan.get("wireframe_artifacts", {}).get("wireframe_png")
    if not configured:
        raise ValueError("visual plan does not identify wireframe_artifacts.wireframe_png")
    candidate = Path(configured)
    if not candidate.is_absolute():
        candidate = visual_plan_path.resolve().parent / candidate
    return candidate.resolve()


def validate_visual_plan_binding(
    visual_plan_path: Path,
    approved_wireframe_path: Path,
    approved_wireframe_png: Path,
) -> Dict[str, Any]:
    for path in (visual_plan_path, approved_wireframe_path, approved_wireframe_png):
        if not path.exists():
            raise FileNotFoundError(path)
    visual_plan = load_json(visual_plan_path)
    require_valid(visual_plan, "visual_plan.schema.json")
    if not visual_plan["approval_gate"].get("image_generation_authorized"):
        raise ValueError("visual plan has not been approved for image generation")
    svg_text = approved_wireframe_path.read_text(encoding="utf-8")
    lowered = svg_text.lower()
    if "<script" in lowered or "<foreignobject" in lowered:
        raise ValueError("approved wireframe contains a forbidden active SVG element")
    root = ET.fromstring(svg_text)
    if root.tag.rsplit("}", 1)[-1] != "svg":
        raise ValueError("approved wireframe is not an SVG document")
    configured_svg = Path(visual_plan["wireframe_artifacts"]["wireframe_svg"])
    if not configured_svg.is_absolute():
        configured_svg = visual_plan_path.resolve().parent / configured_svg
    if not configured_svg.exists():
        raise FileNotFoundError(configured_svg)
    if sha256_file(configured_svg) != sha256_file(approved_wireframe_path):
        raise ValueError("approved wireframe SVG does not match visual_plan.json")
    actual_preview_hash = sha256_file(approved_wireframe_png)
    expected_preview_hash = visual_plan["approval_gate"].get("approved_wireframe_sha256")
    if expected_preview_hash and expected_preview_hash != actual_preview_hash:
        raise ValueError("approved wireframe PNG hash does not match visual plan approval")
    return {
        "visual_mode": visual_plan["visual_mode"],
        "visual_plan_sha256": sha256_file(visual_plan_path),
        "approved_wireframe_svg_sha256": sha256_file(approved_wireframe_path),
        "approved_wireframe_png_sha256": actual_preview_hash,
        "approved_wireframe_revision": visual_plan["approval_gate"].get("approved_wireframe_revision"),
        "spatial_locks": list(visual_plan["spatial_locks"]),
        "forbidden_visual_grammars": list(visual_plan["forbidden_visual_grammars"]),
        "geometry_policy": "approved-wireframe-is-binding; additions are overlay-only",
    }


def build_review(
    truth_path: Path,
    paper_paths: Sequence[Path],
    sketch_path: Path,
    visual_plan_path: Path,
    approved_wireframe_path: Path,
    approved_wireframe_png: Path,
) -> Dict[str, Any]:
    truth = load_json(truth_path)
    visual_plan = load_json(visual_plan_path)
    primary_source = paper_paths[0]
    supporting_source = paper_paths[1] if len(paper_paths) > 1 else primary_source
    message = truth.get("message", {})
    one_sentence = message.get("one_sentence", "Show the approved scientific process.")
    visual_message = message.get("visual_message", one_sentence)
    first_lock = visual_plan["spatial_locks"][0]

    source_inventory = []
    for path, role in [
        (truth_path, "scientific_truth"),
        (sketch_path, "original_sketch"),
        (visual_plan_path, "approved_visual_plan"),
        (approved_wireframe_path, "approved_wireframe_svg"),
        (approved_wireframe_png, "approved_wireframe_preview"),
    ]:
        source_inventory.append({"path": str(path.resolve()), "role": role, "sha256": sha256_file(path)})
    for index, path in enumerate(paper_paths):
        source_inventory.append({"path": str(path.resolve()), "role": "paper_source_%d" % (index + 1), "sha256": sha256_file(path)})

    items = [
        {
            "item_id": "core-message",
            "classification": "keep",
            "claim": one_sentence,
            "visual_action": "Make this the dominant reading path and remove objects that do not support it.",
            "evidence": [evidence(truth_path, one_sentence)],
            "production_impact": "required",
        },
        {
            "item_id": "sketch-semantics",
            "classification": "keep",
            "claim": "Approved sketch geometry is binding within its recorded scope.",
            "visual_action": "Preserve the approved spatial locks while cleaning alignment, spacing, and line quality.",
            "evidence": [evidence(visual_plan_path, first_lock)],
            "production_impact": "required",
        },
        {
            "item_id": "source-traceability",
            "classification": "must-add",
            "claim": "Every visible scientific relation must be traceable to an authoritative source.",
            "visual_action": "Keep stable semantic IDs and source-linked relation metadata in the editable reconstruction.",
            "evidence": [evidence(truth_path, "provenance")],
            "production_impact": "required",
        },
        {
            "item_id": "detail-density",
            "classification": "simplify",
            "claim": "Supporting method detail must remain subordinate to the primary visual message.",
            "visual_action": "Collapse repeated or standard components when their multiplicity is documented elsewhere.",
            "evidence": [evidence(primary_source, "")],
            "production_impact": "optional",
        },
        {
            "item_id": "equation-density",
            "classification": "move-to-caption",
            "claim": "Equations that do not carry the primary message belong in the caption or editable source.",
            "visual_action": "Keep only message-critical notation on the main canvas and preserve full LaTeX metadata.",
            "evidence": [evidence(supporting_source, "")],
            "production_impact": "optional",
        },
        {
            "item_id": "unsupported-claims",
            "classification": "remove",
            "claim": "The figure must not introduce implications that are absent from the scientific contract.",
            "visual_action": "Remove decorative or causal cues that imply unsupported scientific relationships.",
            "evidence": [evidence(truth_path, "forbidden_implications")],
            "production_impact": "prohibited",
        },
    ]
    geometry_hash = sha256_file(approved_wireframe_path)
    return {
        "schema_version": "1.0",
        "figure_id": truth.get("figure_id", "scientific-figure"),
        "editorial_thesis": visual_message,
        "source_inventory": source_inventory,
        "items": items,
        "ambiguities": truth.get("unresolved_ambiguities", []),
        "recommended_wireframe": {
            "id": "plan-locked-paper-aware-overlay",
            "description": "Approved geometry plus one removable message cue.",
            "recommended": visual_plan.get("visual_mode") != "faithful_redraw",
            "geometry_source_sha256": geometry_hash,
            "overlay_only": True,
        },
        "conservative_wireframe": {
            "id": "exact-approved-visual-plan",
            "description": "Byte-preserved approved wireframe with no overlay.",
            "recommended": visual_plan.get("visual_mode") == "faithful_redraw",
            "geometry_source_sha256": geometry_hash,
            "overlay_only": False,
        },
        "visual_plan_binding": {
            "visual_mode": visual_plan["visual_mode"],
            "spatial_locks": visual_plan["spatial_locks"],
            "forbidden_visual_grammars": visual_plan["forbidden_visual_grammars"],
            "approved_wireframe_svg_sha256": geometry_hash,
            "approved_wireframe_png_sha256": sha256_file(approved_wireframe_png),
        },
        "generated_at": utc_now(),
    }


def coverage_markdown(review: Mapping[str, Any]) -> str:
    lines = [
        "# Figure coverage matrix",
        "",
        "| ID | Classification | Scientific claim | Visual action | Evidence |",
        "|---|---|---|---|---|",
    ]
    for item in review["items"]:
        refs = "; ".join("`%s` %s" % (Path(ref["source_path"]).name, ref["locator"]) for ref in item["evidence"])
        lines.append("| %s | %s | %s | %s | %s |" % (
            item["item_id"],
            item["classification"],
            item["claim"].replace("|", "\\|"),
            item["visual_action"].replace("|", "\\|"),
            refs,
        ))
    binding = review.get("visual_plan_binding", {})
    lines += [
        "",
        "## Visual Plan binding",
        "",
        "- Visual mode: `%s`." % binding.get("visual_mode", "unknown"),
        "- Approved geometry SHA-256: `%s`." % binding.get("approved_wireframe_svg_sha256", "unknown"),
        "- The recommended direction may add only the named overlay group.",
        "",
    ]
    return "\n".join(lines)


def redline_svg(sketch_filename: str, width: int, height: int) -> str:
    margin = max(16, int(min(width, height) * 0.035))
    body = f'''
<image href="{esc(sketch_filename)}" x="0" y="0" width="{width}" height="{height}" preserveAspectRatio="xMidYMid meet" opacity="0.78"/>
<g font-family="Arial, Helvetica, sans-serif" font-weight="700">
  <rect x="{margin}" y="{margin}" width="{width - 2 * margin}" height="{height - 2 * margin}" rx="18" fill="none" stroke="#2563EB" stroke-width="6"/>
  <rect x="{margin * 2}" y="{margin * 2}" width="{min(430, width - 4 * margin)}" height="56" rx="12" fill="#DBEAFE" stroke="#2563EB" stroke-width="2"/>
  <text x="{margin * 2 + 18}" y="{margin * 2 + 37}" font-size="22" fill="#1D4ED8">KEEP · approved sketch semantics</text>
  <rect x="{margin * 2}" y="{height - margin * 2 - 56}" width="{min(480, width - 4 * margin)}" height="56" rx="12" fill="#DCFCE7" stroke="#16A34A" stroke-width="2"/>
  <text x="{margin * 2 + 18}" y="{height - margin * 2 - 19}" font-size="20" fill="#166534">CHECK · every relation against sources</text>
</g>'''
    return svg_document(width, height, body, {"artifact": "source-linked-sketch-redline", "source": sketch_filename})


def svg_size(svg_text: str) -> Tuple[float, float]:
    root = ET.fromstring(svg_text)
    viewbox = [float(value) for value in root.get("viewBox", "0 0 1200 675").split()]
    return viewbox[2], viewbox[3]


def paper_aware_overlay(svg_text: str, message: str) -> Tuple[str, Tuple[float, float]]:
    width, height = svg_size(svg_text)
    short_message = textwrap.shorten(message, width=76, placeholder="…")
    overlay = (
        OVERLAY_START
        + '  <g id="paper-aware-overlay" data-overlay-only="true" '
        + 'font-family="Helvetica, Arial, sans-serif">\n'
        + '    <rect x="%.1f" y="%.1f" width="%.1f" height="34" rx="8" fill="#FFF7ED" stroke="#FDBA74"/>\n'
        % (width * 0.12, height - 52, width * 0.76)
        + '    <text x="%.1f" y="%.1f" text-anchor="middle" font-size="14" font-weight="600" fill="#9A3412">%s</text>\n'
        % (width / 2, height - 30, esc(short_message))
        + "  </g>\n"
        + OVERLAY_END
    )
    closing = svg_text.rfind("</svg>")
    if closing < 0:
        raise ValueError("approved wireframe SVG has no closing </svg> tag")
    return svg_text[:closing] + overlay + svg_text[closing:], (width, height)


def render_overlay_preview(base_png: Path, output_png: Path, message: str) -> Dict[str, Any]:
    from PIL import Image, ImageDraw, ImageFont

    image = Image.open(base_png).convert("RGB")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    for candidate in [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]:
        if Path(candidate).exists():
            font = ImageFont.truetype(candidate, max(12, int(image.height * 0.025)))
            break
    short_message = textwrap.shorten(message, width=76, placeholder="…")
    bbox = draw.textbbox((0, 0), short_message, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    padding = 12
    x = max(12, (image.width - text_width) / 2)
    y = image.height - text_height - padding * 2 - 12
    draw.rounded_rectangle(
        (x - padding, y - padding, x + text_width + padding, y + text_height + padding),
        radius=8,
        fill="#FFF7ED",
        outline="#FDBA74",
    )
    draw.text((x, y), short_message, font=font, fill="#9A3412")
    output_png.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_png)
    return {"status": "VERIFIED", "path": str(output_png.resolve()), "sha256": sha256_file(output_png), "renderer": "approved-preview-plus-overlay"}


def build_outputs(
    truth: Path,
    paper_sources: Sequence[Path],
    sketch: Path,
    output_dir: Path,
    visual_plan: Path,
    approved_wireframe: Path,
    approved_wireframe_png: Path | None = None,
) -> Dict[str, Any]:
    from PIL import Image

    output_dir.mkdir(parents=True, exist_ok=True)
    approved_preview = resolve_approved_wireframe_preview(visual_plan, approved_wireframe_png)
    binding = validate_visual_plan_binding(visual_plan, approved_wireframe, approved_preview)
    snapshot_dir = output_dir.parent / "visual_plan"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    plan_snapshot = snapshot_dir / "visual_plan.json"
    wireframe_snapshot = snapshot_dir / "approved_wireframe.svg"
    preview_snapshot = snapshot_dir / "approved_wireframe.png"
    for source, destination in [
        (visual_plan, plan_snapshot),
        (approved_wireframe, wireframe_snapshot),
        (approved_preview, preview_snapshot),
    ]:
        if source.resolve() != destination.resolve():
            shutil.copyfile(source, destination)
    source_sketch = output_dir / "source_sketch.png"
    if source_sketch.resolve() != sketch.resolve():
        shutil.copyfile(sketch, source_sketch)

    review = build_review(truth, paper_sources, sketch, plan_snapshot, wireframe_snapshot, preview_snapshot)
    review_path = output_dir / "figure_editorial_review.json"
    save_validated_json(review_path, review, "figure_editorial_review.schema.json")
    coverage_path = output_dir / "figure_coverage_matrix.md"
    write_text(coverage_path, coverage_markdown(review))
    assets = [review_path, coverage_path, source_sketch, plan_snapshot, wireframe_snapshot, preview_snapshot]

    with Image.open(source_sketch) as image:
        sketch_width, sketch_height = image.size
    redline_path = output_dir / "sketch_redline.svg"
    redline_png = redline_path.with_suffix(".png")
    write_text(redline_path, redline_svg(source_sketch.name, sketch_width, sketch_height))
    renders = [render_svg_to_png(redline_path, redline_png, sketch_width, sketch_height)]
    assets.extend([redline_path, redline_png])

    conservative_svg = output_dir / "wireframe_conservative.svg"
    conservative_png = output_dir / "wireframe_conservative.png"
    shutil.copyfile(wireframe_snapshot, conservative_svg)
    shutil.copyfile(preview_snapshot, conservative_png)
    renders.append({"status": "VERIFIED", "path": str(conservative_png.resolve()), "sha256": sha256_file(conservative_png), "renderer": "approved-wireframe-preview-copy"})
    assets.extend([conservative_svg, conservative_png])

    message = review["editorial_thesis"]
    recommended_text, _ = paper_aware_overlay(wireframe_snapshot.read_text(encoding="utf-8"), message)
    recommended_svg = output_dir / "wireframe_recommended.svg"
    recommended_png = output_dir / "wireframe_recommended.png"
    write_text(recommended_svg, recommended_text)
    renders.append(render_overlay_preview(preview_snapshot, recommended_png, message))
    assets.extend([recommended_svg, recommended_png])

    result = {
        "status": "VERIFIED" if all(item["status"] == "VERIFIED" for item in renders) else "GENERATED_UNVERIFIED",
        "output_dir": str(output_dir.resolve()),
        "artifacts": [{"path": str(path.resolve()), "sha256": sha256_file(path)} for path in assets if path.exists()],
        "render_checks": renders,
        "visual_plan_binding": binding,
        "image_generation_calls": 0,
    }
    write_json(output_dir / "editorial_build_report.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--truth", required=True, type=Path)
    parser.add_argument("--paper-source", required=True, action="append", type=Path)
    parser.add_argument("--sketch", required=True, type=Path)
    parser.add_argument("--visual-plan", required=True, type=Path)
    parser.add_argument("--approved-wireframe", required=True, type=Path)
    parser.add_argument("--approved-wireframe-png", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    report = build_outputs(
        args.truth,
        args.paper_source,
        args.sketch,
        args.output_dir,
        args.visual_plan,
        args.approved_wireframe,
        args.approved_wireframe_png,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
