#!/usr/bin/env python3
"""Compile stage-specific figure artifacts from truth, rules, and blueprints."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping

from figure_artifacts import (
    basic_blueprint_errors,
    basic_truth_errors,
    canonical_json_sha256,
    compare_fingerprints,
    load_json,
    sha256_file,
    word_count,
    write_json,
)


def load_rules(repository_root: Path, run_dir: Path) -> Dict[str, Mapping[str, Any]]:
    paths = [
        repository_root / "rules" / "common_rules.json",
        run_dir / "rules" / "validation_rules.json",
    ]
    result: Dict[str, Mapping[str, Any]] = {}
    for path in paths:
        if not path.exists():
            continue
        payload = load_json(path)
        for rule in payload.get("rules", []):
            rule_id = rule["rule_id"]
            if rule_id in result and result[rule_id] != rule:
                raise ValueError("conflicting definitions for rule %s" % rule_id)
            result[rule_id] = rule
    return result


def blocking_rules(
    blueprint: Mapping[str, Any], rules: Mapping[str, Mapping[str, Any]]
) -> List[Mapping[str, Any]]:
    selected: List[Mapping[str, Any]] = []
    for rule_id in blueprint.get("in_scope_rule_ids", []):
        rule = rules[rule_id]
        if rule.get("png_classification") == "image-level blocking":
            selected.append(rule)
    return selected[:8]


def build_generation_brief(
    truth: Mapping[str, Any],
    blueprint: Mapping[str, Any],
    rules: Mapping[str, Mapping[str, Any]],
) -> str:
    rule_lines = "\n".join(
        "- [%s] %s" % (rule["rule_id"], rule["description"])
        for rule in blocking_rules(blueprint, rules)
    ) or "- No additional case-specific image-level blocking rules are registered. Preserve the blueprint exactly."
    forbidden = truth.get("forbidden_implications", [])
    forbidden_lines = "\n".join(
        "- %s" % item["description"] for item in forbidden[:6]
    )
    whitelist = ", ".join(
        '"%s"' % item for item in blueprint.get("visible_text_whitelist", [])
    )
    fingerprint = blueprint["layout_fingerprint"]
    art = blueprint.get("art_direction", {})
    depiction = blueprint.get("depiction_policy", {})
    text = f"""# Built-in image-generation brief: {blueprint['candidate_id']}

Use case: scientific-educational
Asset type: landscape main-paper scientific method figure; PNG visual candidate
Audience: {truth['message']['audience']}
Primary visual message: {truth['message']['visual_message']}

AUTHORITY AND PURPOSE
Create one visual hypothesis for composition, hierarchy, palette, glyphs, whitespace, and rhythm. Image 1 is a deterministic topology skeleton and is authoritative for regions, reading order, grouping, declared multiplicity, and connector direction. The scientific truth file remains authoritative for entities, relations, equations, counts, and forbidden implications. The later semantic reconstruction remains authoritative for exact text, notation, ports, connector endpoints, and editable object identity. Do not infer new science from the roughness, omissions, or visual style of the sketch or skeleton.

LAYOUT
Use a {fingerprint['reading_axis']} reading axis and region graph {json.dumps(fingerprint['region_graph'], ensure_ascii=False)}. Dominant region: {fingerprint['dominant_region']}. Arrangement: {fingerprint['stage_arrangement']}. Repetition strategy: {fingerprint['repetition_strategy']}. Audit location: {fingerprint['audit_location']}. Respect the skeleton's region boxes, relative emphasis, object groupings, and directed relations. Preserve generous outer margins and enough whitespace around connectors that their endpoints remain visually unambiguous.

DEPICTION POLICY
Mode: {depiction.get('depiction_mode', 'literal_instances')}. Visible scope: {depiction.get('visible_scope', 'all contracted instances')}. Semantic scope: {depiction.get('semantic_scope', 'the complete scientific contract')}. If the blueprint uses a representative template or multiplicity badge, show that choice explicitly and avoid implying that omitted repetitions do not exist. Never merge independent entities merely to reduce visual density. Never duplicate a shared entity merely to improve symmetry.

BLOCKING VISUAL INVARIANTS
{rule_lines}

ART DIRECTION
Use a flat academic-editorial treatment on a clean light background. Composition: {art.get('composition', 'structure-first')}. Shapes: {art.get('shape_language', 'simple domain-aware scientific glyphs')}. Color: {art.get('color', 'restrained and grayscale-safe')}. Whitespace: {art.get('whitespace', 'generous and intentional')}. Connectors: {art.get('connectors', 'quiet and directional')}. Establish hierarchy through position, grouping, and scale before adding color. Avoid generic dashboard cards unless the scientific contract explicitly calls for modular panels.

TEXT BOUNDARY
Visible text is optional and limited to: {whitelist}. Do not typeset full equations, prose, title, legend, footer, row headings, or production indices. Exact notation is rebuilt from truth. Production typography is not required in this PNG.

FORBIDDEN VISUAL IMPLICATIONS
{forbidden_lines}

OUTPUT AND RESTRAINT
Generate one independent candidate, not a contact sheet. Add no scientific object, arrow, causal relation, result, performance cue, or data-like image that is absent from the supplied contract. Avoid gradients, shadows, glow, 3D, decorative circuitry, rainbow variables, clinical imagery, and evidence-like reconstructions. Keep required content inside the canvas. Treat any image-valued object as a clearly schematic placeholder. Exact production details will be rebuilt as native semantic objects after human selection.
"""
    count = word_count(text)
    if count < 350 or count > 500:
        raise ValueError(
            "compiled generation brief must be 350-500 words; got %d for %s"
            % (count, blueprint["candidate_id"])
        )
    return text


def build_review_template(
    truth_hash: str,
    blueprint_hash: str,
    prompt_hash: str,
    blueprint: Mapping[str, Any],
    rules: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    human_checks = []
    for rule_id in blueprint.get("in_scope_rule_ids", []):
        rule = rules[rule_id]
        if "png_human" in rule.get("applicable_stages", []):
            human_checks.append(
                {
                    "rule_id": rule_id,
                    "classification": rule.get("png_classification"),
                    "status": "pending",
                    "notes": "",
                }
            )
    return {
        "schema_version": "1.0",
        "candidate_id": blueprint["candidate_id"],
        "truth_hash": truth_hash,
        "blueprint_hash": blueprint_hash,
        "prompt_hash": prompt_hash,
        "image_hash": "pending",
        "machine_checks": [],
        "human_checks": human_checks,
        "blocking_failures": [],
        "acceptable_raster_imperfections": [],
        "svg_reconstruction_fixes": [
            "replace all generated text and equations from scientific truth",
            "rebuild all connectors from source/target metadata",
            "recompute centroids and exact geometry",
        ],
        "repair_budget_used": {"regenerations": 0, "local_style_edits": 0},
        "decision": "pending",
        "decision_reason": "",
    }


def build_selected_map_template(blueprint: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": "1.0",
        "candidate_id": blueprint["candidate_id"],
        "image_hash": "pending",
        "major_region_bboxes": {
            region["id"]: region["bbox"] for region in blueprint.get("regions", [])
        },
        "palette_samples": {},
        "stroke_character": "pending human selection",
        "corner_language": "pending human selection",
        "whitespace_rhythm": [],
        "glyph_reference_crops": [],
        "art_direction_notes": "Populate only after Gate 2 macro-layout selection.",
        "scientific_overrides": [
            "ignore_all_generated_text",
            "ignore_all_generated_equations",
            "ignore_generated_indices",
            "ignore_generated_connector_endpoints",
            "ignore_generated_arrow_directions",
            "ignore_generated_centroids",
        ],
    }


def build_svg_spec(
    truth: Mapping[str, Any],
    truth_hash: str,
    blueprint: Mapping[str, Any],
    blueprint_hash: str,
) -> Dict[str, Any]:
    profile = truth.get("information_profiles", {}).get("main_paper_story_first", {})
    counts: Dict[str, Dict[str, int]] = {}
    for instance in truth.get("instances", []):
        stage = str(instance.get("stage", "global"))
        entity_type = str(instance.get("type", "entity"))
        counts.setdefault(stage, {}).setdefault(entity_type, 0)
        counts[stage][entity_type] += 1
    inventory: Dict[str, int] = {}
    for instance in truth.get("instances", []):
        inventory[instance["type"]] = inventory.get(instance["type"], 0) + 1
    depiction_policy = blueprint.get("depiction_policy", {})
    relation_counts: Dict[str, int] = {}
    for relation in truth.get("relations", []):
        relation_type = str(relation.get("type", "relation"))
        relation_counts[relation_type] = relation_counts.get(relation_type, 0) + 1
    stage_ids = [str(stage.get("id")) for stage in truth.get("stages", []) if stage.get("id")]
    if not stage_ids:
        stage_ids = sorted(counts)
    return {
        "schema_version": "1.0",
        "truth_ref": {"path": "truth/scientific_truth.json", "sha256": truth_hash},
        "blueprint_ref": {
            "path": "blueprints/%s.json" % blueprint["candidate_id"],
            "sha256": blueprint_hash,
        },
        "selected_candidate_map_ref": {
            "path": "selected/%s_selected_candidate_map.template.json"
            % blueprint["candidate_id"],
            "status": "pending_gate_2",
        },
        "native_object_inventory": [
            {"entity_type": key, "expected_count": value}
            for key, value in sorted(inventory.items())
        ],
        "semantic_group_inventory": [
            {"id": "stage-%s" % stage_id, "role": "stage"}
            for stage_id in stage_ids
        ],
        "exact_text": profile.get("exact_text", []),
        "exact_equations": [
            equation["latex"]
            for equation in truth.get("equations", [])
            if equation["id"] in profile.get("displayed_equation_ids", [])
        ],
        "ports": blueprint.get("ports", []),
        "connectors": blueprint.get("edges", []),
        "depiction_policy": depiction_policy,
        "geometry_policy": {
            "semantic_topology_from": "candidate blueprint",
            "exact_counts_from": "scientific truth",
            "style_from": "selected candidate map only",
            "centroid_tolerance_normalized": 0.005,
            "orthogonal_connectors": blueprint.get("connector_style", "orthogonal") == "orthogonal",
            "minimum_font_size_pt": profile.get("minimum_font_size_pt", 7.5),
            "entity_counts_by_stage": counts,
            "relation_counts": relation_counts,
            "congruent_entity_types": blueprint.get("congruent_entity_types", []),
        },
        "style_tokens": {
            "background": "pending_gate_2",
            "ink": "pending_gate_2",
            "muted": "pending_gate_2",
            "cool": "pending_gate_2",
            "accent": "pending_gate_2",
            "surface": "pending_gate_2",
            "surface2": "pending_gate_2",
        },
        "raster_asset_policy": {
            "allowed": False,
            "whole_canvas_raster_forbidden": True,
            "exceptions_require_manifest": True,
        },
        "editability_requirements": {
            "stable_ids": True,
            "semantic_groups": True,
            "live_text": True,
            "independent_connectors": True,
            "source_target_metadata": True,
            "global_style_tokens": True,
        },
        "validation_rule_ids": blueprint.get("in_scope_rule_ids", []),
        "status": "prepared; finalize after Gate 2",
    }


def compile_run(run_dir: Path, repository_root: Path) -> Dict[str, Any]:
    truth_path = run_dir / "truth" / "scientific_truth.json"
    truth = load_json(truth_path)
    truth_errors = basic_truth_errors(truth)
    if truth_errors:
        raise ValueError("invalid scientific truth:\n- " + "\n- ".join(truth_errors))
    truth_hash = sha256_file(truth_path)

    rules = load_rules(repository_root, run_dir)
    if not rules:
        raise ValueError("no validation rules found")
    write_json(
        run_dir / "rules" / "validation_rules.json",
        {
            "schema_version": "1.0",
            "source_registry": [
                "rules/common_rules.json",
            ],
            "rules": list(rules.values()),
        },
    )

    blueprint_paths = sorted((run_dir / "blueprints").glob("*.json"))
    if not blueprint_paths:
        raise ValueError("no candidate blueprints found")
    blueprints: List[Mapping[str, Any]] = []
    for path in blueprint_paths:
        blueprint = load_json(path)
        errors = basic_blueprint_errors(blueprint, truth, set(rules))
        if blueprint.get("truth_ref", {}).get("sha256") != truth_hash:
            errors.append("truth_ref.sha256 does not match scientific_truth.json")
        if errors:
            raise ValueError("invalid blueprint %s:\n- %s" % (path, "\n- ".join(errors)))
        blueprints.append(blueprint)

    fingerprint_report: Dict[str, Any] = {
        "schema_version": "1.0",
        "candidates": [
            {
                "candidate_id": blueprint["candidate_id"],
                "layout_fingerprint": blueprint["layout_fingerprint"],
            }
            for blueprint in blueprints
        ],
        "pairs": [],
    }
    for left_index, left in enumerate(blueprints):
        for right in blueprints[left_index + 1 :]:
            comparison = compare_fingerprints(
                left["layout_fingerprint"], right["layout_fingerprint"]
            )
            comparison["left"] = left["candidate_id"]
            comparison["right"] = right["candidate_id"]
            fingerprint_report["pairs"].append(comparison)
    fingerprint_report["overall_pass"] = all(
        pair["sufficiently_different"] for pair in fingerprint_report["pairs"]
    )
    write_json(run_dir / "skeletons" / "fingerprint_report.json", fingerprint_report)
    if not fingerprint_report["overall_pass"]:
        raise ValueError("blueprint fingerprint diversity failed")

    manifest_entries = []
    compiled = []
    for path, blueprint in zip(blueprint_paths, blueprints):
        blueprint_hash = sha256_file(path)
        brief = build_generation_brief(truth, blueprint, rules)
        prompt_path = run_dir / "generation" / (blueprint["candidate_id"] + "_prompt.md")
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(brief, encoding="utf-8")
        prompt_hash = sha256_file(prompt_path)

        review = build_review_template(
            truth_hash, blueprint_hash, prompt_hash, blueprint, rules
        )
        write_json(
            run_dir / "reviews" / (blueprint["candidate_id"] + "_review.template.json"),
            review,
        )
        write_json(
            run_dir
            / "selected"
            / (blueprint["candidate_id"] + "_selected_candidate_map.template.json"),
            build_selected_map_template(blueprint),
        )
        write_json(
            run_dir / "svg" / (blueprint["candidate_id"] + "_reconstruction_spec.json"),
            build_svg_spec(truth, truth_hash, blueprint, blueprint_hash),
        )
        manifest_entries.append(
            {
                "candidate_id": blueprint["candidate_id"],
                "workflow": "compiled_skeleton_v2",
                "status": "prepared",
                "prompt_path": str(prompt_path.relative_to(run_dir)),
                "prompt_sha256": prompt_hash,
                "prompt_word_count": word_count(brief),
                "reference_roles": [
                    {
                        "image": "skeletons/%s_skeleton.png" % blueprint["candidate_id"],
                        "role": "topology_skeleton",
                        "authority": "structure",
                    }
                ],
                "generation_call_completed": False,
                "output_path": None,
            }
        )
        compiled.append(
            {
                "candidate_id": blueprint["candidate_id"],
                "blueprint_sha256": blueprint_hash,
                "prompt_sha256": prompt_hash,
                "prompt_word_count": word_count(brief),
            }
        )

    write_json(
        run_dir / "generation" / "generation_manifest.json",
        {
            "schema_version": "1.0",
            "execution_mode": "built-in_chat_image_generation_only",
            "image_api_forbidden": True,
            "independent_calls_required": True,
            "entries": manifest_entries,
        },
    )
    summary = {
        "schema_version": "1.0",
        "figure_id": truth["figure_id"],
        "truth_sha256": truth_hash,
        "rule_count": len(rules),
        "candidate_count": len(blueprints),
        "fingerprint_diversity_pass": fingerprint_report["overall_pass"],
        "compiled": compiled,
    }
    write_json(run_dir / "validation" / "compile_report.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    args = parser.parse_args()
    try:
        summary = compile_run(args.run_dir.resolve(), args.repository_root.resolve())
    except (OSError, ValueError, KeyError) as exc:
        print("COMPILE FAIL: %s" % exc, file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
