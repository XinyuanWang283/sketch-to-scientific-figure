#!/usr/bin/env python3
"""Validate generic truth, blueprint, skeleton, and provenance artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Set, Tuple

from figure_artifacts import (
    basic_blueprint_errors,
    basic_truth_errors,
    json_schema_errors,
    load_json,
    sha256_file,
    truth_instance_index,
    write_json,
)


def load_all_rules(repository_root: Path, run_dir: Path) -> Dict[str, Mapping[str, Any]]:
    result: Dict[str, Mapping[str, Any]] = {}
    for path in [
        repository_root / "rules" / "common_rules.json",
        run_dir / "rules" / "validation_rules.json",
    ]:
        if not path.exists():
            continue
        for rule in load_json(path).get("rules", []):
            result[rule["rule_id"]] = rule
    return result


def run_schema_errors(run_dir: Path, repository_root: Path) -> List[str]:
    schema_dir = repository_root / "schemas"
    targets: List[Tuple[Path, Path]] = [
        (run_dir / "truth" / "scientific_truth.json", schema_dir / "scientific_truth.schema.json"),
        (run_dir / "rules" / "validation_rules.json", schema_dir / "validation_rules.schema.json"),
    ]
    targets.extend(
        (path, schema_dir / "candidate_blueprint.schema.json")
        for path in sorted((run_dir / "blueprints").glob("*.json"))
    )
    targets.extend(
        (path, schema_dir / "review_result.schema.json")
        for path in sorted((run_dir / "reviews").glob("*_review*.json"))
    )
    targets.extend(
        (path, schema_dir / "selected_candidate_map.schema.json")
        for path in sorted((run_dir / "selected").glob("*.json"))
    )
    targets.extend(
        (path, schema_dir / "svg_reconstruction_spec.schema.json")
        for path in sorted((run_dir / "svg").glob("*_reconstruction_spec.json"))
    )
    problems: List[str] = []
    for artifact, schema in targets:
        if not artifact.exists():
            continue
        for error in json_schema_errors(load_json(artifact), load_json(schema)):
            problems.append("%s: %s" % (artifact.relative_to(run_dir), error))
    return problems


def scene_object_index(scene: Mapping[str, Any]) -> Dict[str, Mapping[str, Any]]:
    return {item["id"]: item for item in scene.get("objects", [])}


def evaluate_rule(
    rule: Mapping[str, Any],
    truth: Mapping[str, Any],
    blueprints: Sequence[Mapping[str, Any]],
    scenes: Mapping[str, Mapping[str, Any]],
    source_root: Path,
    fingerprint_report: Mapping[str, Any],
) -> Tuple[bool, str]:
    predicate = rule.get("predicate_type")
    if predicate == "required_fields":
        errors = basic_truth_errors(truth)
        return not errors, "; ".join(errors) if errors else "required fields are present"
    if predicate == "source_hashes":
        problems = []
        for source in truth.get("provenance", {}).get("sources", []):
            path = source_root / source["path"]
            if not path.exists():
                problems.append("missing %s" % source["path"])
            elif sha256_file(path) != source["sha256"]:
                problems.append("hash mismatch %s" % source["path"])
        return not problems, "; ".join(problems) if problems else "source hashes match"
    if predicate == "unique_ids":
        errors = [error for error in basic_truth_errors(truth) if "duplicate" in error]
        return not errors, "; ".join(errors) if errors else "truth IDs are unique"
    if predicate == "reference_integrity":
        errors = basic_truth_errors(truth)
        return not errors, "; ".join(errors) if errors else "truth references resolve"
    if predicate == "truth_coverage":
        expected = set(truth_instance_index(truth))
        problems = []
        for blueprint in blueprints:
            actual = {ref for node in blueprint.get("nodes", []) for ref in node.get("instance_refs", [])}
            if actual != expected:
                problems.append("%s missing=%s extra=%s" % (blueprint.get("candidate_id"), sorted(expected - actual), sorted(actual - expected)))
        return not problems, "; ".join(problems) if problems else "every blueprint covers truth exactly once"
    if predicate == "fingerprint_diversity":
        passed = bool(fingerprint_report.get("overall_pass"))
        return passed, "pairwise fingerprint report overall_pass=%s" % passed
    if predicate == "orthogonal_connectors":
        problems = []
        for candidate_id, scene in scenes.items():
            for connector in scene.get("connectors", []):
                for start, end in zip(connector["points"], connector["points"][1:]):
                    if abs(start[0] - end[0]) > 1e-6 and abs(start[1] - end[1]) > 1e-6:
                        problems.append("%s:%s" % (candidate_id, connector["id"]))
        return not problems, "; ".join(problems) if problems else "connector shafts are axis-aligned"
    return True, "predicate is checked at a later artifact stage"


def validate(run_dir: Path, repository_root: Path, source_root: Path) -> Dict[str, Any]:
    truth_path = run_dir / "truth" / "scientific_truth.json"
    truth = load_json(truth_path)
    rules = load_all_rules(repository_root, run_dir)
    rule_ids: Set[str] = set(rules)
    blueprint_paths = sorted((run_dir / "blueprints").glob("*.json"))
    blueprints = [load_json(path) for path in blueprint_paths]

    structural_errors = basic_truth_errors(truth)
    truth_hash = sha256_file(truth_path)
    for path, blueprint in zip(blueprint_paths, blueprints):
        structural_errors.extend(basic_blueprint_errors(blueprint, truth, rule_ids))
        if blueprint.get("truth_ref", {}).get("sha256") != truth_hash:
            structural_errors.append("%s truth hash mismatch" % path.name)

    fingerprint_path = run_dir / "skeletons" / "fingerprint_report.json"
    fingerprint_report = load_json(fingerprint_path) if fingerprint_path.exists() else {"overall_pass": len(blueprints) <= 1}
    scenes: Dict[str, Mapping[str, Any]] = {}
    for blueprint in blueprints:
        path = run_dir / "skeletons" / (blueprint["candidate_id"] + "_skeleton.scene.json")
        if not path.exists():
            structural_errors.append("missing skeleton scene %s" % path.name)
            continue
        scene = load_json(path)
        scenes[blueprint["candidate_id"]] = scene
        expected = set(truth_instance_index(truth))
        actual = set(scene_object_index(scene))
        if expected != actual:
            structural_errors.append("%s scene coverage mismatch" % blueprint["candidate_id"])

    schema_problems = run_schema_errors(run_dir, repository_root)
    checks = [{
        "rule_id": "ARTIFACT_SCHEMA_VALIDITY",
        "severity": "blocker",
        "status": "fail" if schema_problems else "pass",
        "evidence": schema_problems or "repository schema contracts pass",
    }]
    for rule_id, rule in rules.items():
        if rule_id == "ARTIFACT_SCHEMA_VALIDITY":
            continue
        if not set(rule.get("applicable_stages", [])).intersection({"artifact", "blueprint", "skeleton"}):
            continue
        passed, evidence = evaluate_rule(rule, truth, blueprints, scenes, source_root, fingerprint_report)
        checks.append({
            "rule_id": rule_id,
            "severity": rule.get("severity", "error"),
            "status": "pass" if passed else "fail",
            "evidence": evidence,
        })
    if structural_errors:
        checks.insert(0, {"rule_id": "ARTIFACT_STRUCTURE", "severity": "blocker", "status": "fail", "evidence": structural_errors})

    failed_blockers = [check for check in checks if check["status"] == "fail" and check["severity"] == "blocker"]
    try:
        display_run_dir = str(run_dir.relative_to(repository_root))
    except ValueError:
        display_run_dir = run_dir.name
    report = {
        "schema_version": "1.0",
        "figure_id": truth.get("figure_id"),
        "run_dir": display_run_dir,
        "truth_sha256": truth_hash,
        "blueprint_count": len(blueprints),
        "scene_count": len(scenes),
        "checks": checks,
        "summary": {
            "passed": sum(check["status"] == "pass" for check in checks),
            "failed": sum(check["status"] == "fail" for check in checks),
            "blockers": len(failed_blockers),
            "overall": "pass" if not failed_blockers and not structural_errors else "fail",
        },
    }
    write_json(run_dir / "validation" / "artifact_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        report = validate(args.run_dir.resolve(), args.repository_root.resolve(), args.source_root.resolve())
    except (OSError, ValueError, KeyError) as exc:
        print("VALIDATION FAIL: %s" % exc, file=sys.stderr)
        return 1
    print(json.dumps(report["summary"], indent=2))
    return 0 if report["summary"]["overall"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
