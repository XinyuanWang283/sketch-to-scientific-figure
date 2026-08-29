#!/usr/bin/env python3
"""Offline validation and replay for the frozen Deep Image Prior v0.1 case.

This module is deliberately case-specific.  It never calls ImageGen, a network,
or a remote service.  Replay only imports already-frozen, hash-bound artifacts
into a new external ledger run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Any, Mapping, Sequence

import imagegen_workflow
from build_deep_image_prior_c_fidelity_v2 import validate_package


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXAMPLE_ROOT = REPOSITORY_ROOT / "examples" / "deep_image_prior"
REFERENCE_CASE_FILENAME = "reference_case_v0_1.json"
ARTIFACT_MANIFEST_FILENAME = "reference_case_v0_1_artifact_manifest.json"
STRUCTURAL_VALIDATION_FILENAME = "reference_case_v0_1_validation_report.json"
REPLAY_START_HERE_FILENAME = "START_HERE.md"
CASE_ID = "deep-image-prior-synthetic-v0.1"
DELIVERY_REVISION = "fidelity-v2"
RECIPE_ID = "deep-image-prior-c-fidelity-v2"
BUILDER_RELATIVE_PATH = "scripts/build_deep_image_prior_c_fidelity_v2.py"
CANDIDATE_PROVENANCE_STATUS = "repository_registered_operator_attested"
SELECTED_SLOT = "C"
SELECTED_CANDIDATE_ID = "C-presentation"
VALIDATOR_NAME = "build_deep_image_prior_c_fidelity_v2.validate_package"
VALIDATOR_VERSION = "1.1"
VALIDATOR_STATUS = "VERIFIED_FIDELITY_V2_REVIEW_DRAFT"
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
EXPECTED_CANDIDATES = {
    "A": "A-faithful",
    "B": "B-publication",
    "C": SELECTED_CANDIDATE_ID,
    "D": "D-alternative-layout",
    "E": "E-visual-variant",
}
ARTIFACT_KEYS = ("svg", "pptx", "drawio", "pdf_preview")
EXPECTED_ARTIFACT_PATHS = {
    "svg": "delivery/svg/master.svg",
    "pptx": "delivery/pptx/figure.pptx",
    "drawio": "delivery/drawio/figure.drawio",
    "pdf_preview": "delivery/pdf/publication.pdf",
}
APPROVAL_KEYS = ("visual", "scientific", "science_day_use", "public_release")
IMPORTED_VALIDATOR_PATH = Path(validate_package.__code__.co_filename).resolve()


@dataclass(frozen=True)
class ReferenceCase:
    example_root: Path
    case: dict[str, Any]
    artifact_manifest: dict[str, Any]
    region_map_approval: dict[str, Any]
    visual_approval: dict[str, Any]
    paths: dict[str, Path]
    output_hashes: dict[str, str]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def _require_false(value: Any, label: str) -> None:
    if value is not False:
        raise ValueError(f"{label} must be false")


def _portable_relative_path(value: Any, label: str) -> str:
    raw = _require_text(value, label)
    parts = raw.split("/")
    windows = PureWindowsPath(raw)
    if (
        Path(raw).is_absolute()
        or windows.is_absolute()
        or bool(windows.drive)
        or raw.startswith("~")
        or raw.lower().startswith("file:")
        or "\\" in raw
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise ValueError(f"{label} must be a portable relative path without traversal")
    return raw


def _reject_symlink_components(base: Path, relative: str, label: str) -> Path:
    candidate = base
    for part in relative.split("/"):
        candidate = candidate / part
        if candidate.is_symlink():
            raise ValueError(f"{label} must not traverse a symbolic link")
    return candidate


def _resolve_inside(base: Path, value: Any, label: str, *, directory: bool = False) -> Path:
    relative = _portable_relative_path(value, label)
    candidate = _reject_symlink_components(base, relative, label)
    try:
        resolved_base = base.resolve(strict=True)
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(resolved_base)
    except (OSError, ValueError) as exc:
        raise ValueError(f"{label} is missing or escapes its allowed root") from exc
    if directory:
        if not resolved.is_dir():
            raise ValueError(f"{label} must resolve to a directory")
    elif not resolved.is_file():
        raise ValueError(f"{label} must resolve to a regular file")
    return resolved


def _require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _record(value: Any, label: str) -> dict[str, Any]:
    record = _require_object(value, label)
    _portable_relative_path(record.get("path"), f"{label}.path")
    _require_sha256(record.get("sha256"), f"{label}.sha256")
    return record


def _resolve_record(base: Path, value: Any, label: str) -> Path:
    record = _record(value, label)
    path = _resolve_inside(base, record["path"], f"{label}.path")
    actual = sha256_file(path)
    if actual != record["sha256"]:
        raise ValueError(f"{label} SHA-256 mismatch: expected {record['sha256']}, got {actual}")
    return path


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is unreadable or invalid JSON: {path}") from exc
    return _require_object(value, label)


def _check_identity(value: Mapping[str, Any], label: str) -> None:
    if value.get("case_id") != CASE_ID:
        raise ValueError(f"{label}.case_id must be {CASE_ID}")
    if value.get("delivery_revision") != DELIVERY_REVISION:
        raise ValueError(f"{label}.delivery_revision must be {DELIVERY_REVISION}")


def _check_selected(value: Mapping[str, Any], label: str, expected_sha256: str) -> None:
    if value.get("slot") != SELECTED_SLOT or value.get("candidate_id") != SELECTED_CANDIDATE_ID:
        raise ValueError(f"{label} must select exact Candidate C ({SELECTED_CANDIDATE_ID})")
    if value.get("sha256") != expected_sha256:
        raise ValueError(f"{label} is not bound to the registered Candidate C SHA-256")


def _check_reference_candidates(
    example_root: Path, case: Mapping[str, Any], paths: dict[str, Path]
) -> dict[str, Mapping[str, Any]]:
    candidates = case.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != 5:
        raise ValueError("reference_case.candidates must contain exactly five events")
    by_slot: dict[str, Mapping[str, Any]] = {}
    event_ids: set[str] = set()
    for index, raw in enumerate(candidates):
        item = _require_object(raw, f"reference_case.candidates[{index}]")
        slot = _require_text(item.get("slot"), f"candidate[{index}].slot").upper()
        if slot not in EXPECTED_CANDIDATES or slot in by_slot:
            raise ValueError("candidate events must expose unique fixed slots A through E")
        if item.get("candidate_id") != EXPECTED_CANDIDATES[slot]:
            raise ValueError(f"candidate {slot} has the wrong fixed candidate_id")
        event_id = _require_text(
            item.get("generation_event_id"), f"candidate {slot}.generation_event_id"
        )
        if event_id in event_ids:
            raise ValueError("five unique generation_event_id values are required")
        event_ids.add(event_id)
        for key in ("design_note", "registered_at"):
            _require_text(item.get(key), f"candidate {slot}.{key}")
        if item.get("provenance_status") != CANDIDATE_PROVENANCE_STATUS:
            raise ValueError(
                f"candidate {slot}.provenance_status must be "
                f"{CANDIDATE_PROVENANCE_STATUS}"
            )
        native_id = item.get("native_tool_call_id")
        if native_id is not None:
            _require_text(native_id, f"candidate {slot}.native_tool_call_id")
        path = _resolve_record(example_root, item, f"candidate {slot}")
        paths[f"candidate_{slot}"] = path
        by_slot[slot] = item
    if set(by_slot) != set(EXPECTED_CANDIDATES):
        raise ValueError("candidate events must expose exactly slots A through E")
    return by_slot


def _check_candidate_manifest(
    manifest: Mapping[str, Any], candidates: Mapping[str, Mapping[str, Any]]
) -> None:
    entries = manifest.get("candidates")
    if not isinstance(entries, list) or len(entries) != 5:
        raise ValueError("candidate manifest must contain exactly five candidates")
    seen: set[str] = set()
    for index, raw in enumerate(entries):
        item = _require_object(raw, f"candidate_manifest.candidates[{index}]")
        slot = _require_text(item.get("slot"), f"candidate manifest slot {index}").upper()
        if slot not in candidates or slot in seen:
            raise ValueError("candidate manifest must expose unique slots A through E")
        seen.add(slot)
        expected = candidates[slot]
        if item.get("path") != expected.get("path") or item.get("sha256") != expected.get("sha256"):
            raise ValueError(f"candidate manifest binding differs for slot {slot}")
    if seen != set(EXPECTED_CANDIDATES):
        raise ValueError("candidate manifest must expose exactly slots A through E")


def _check_artifact_manifest(
    example_root: Path,
    manifest: Mapping[str, Any],
    paths: dict[str, Path],
) -> tuple[dict[str, str], Path]:
    if manifest.get("schema_version") != "1.0":
        raise ValueError("artifact manifest schema_version must be 1.0")
    if manifest.get("manifest_type") != "editable_delivery_artifact_manifest":
        raise ValueError("artifact manifest has the wrong manifest_type")
    _check_identity(manifest, "artifact_manifest")
    if manifest.get("canonical_root") != "editable_delivery_c_fidelity_v2":
        raise ValueError("artifact_manifest.canonical_root must be editable_delivery_c_fidelity_v2")
    _require_false(
        manifest.get("scientific_correctness_checked"),
        "artifact_manifest.scientific_correctness_checked",
    )
    package_root = _resolve_inside(
        example_root, manifest.get("canonical_root"), "artifact_manifest.canonical_root", directory=True
    )
    paths["package_root"] = package_root
    validation_path = _resolve_record(
        example_root,
        manifest.get("validation_report"),
        "artifact_manifest.validation_report",
    )
    paths["structural_validation_report"] = validation_path
    if validation_path.name != STRUCTURAL_VALIDATION_FILENAME:
        raise ValueError(
            f"artifact manifest validation report must be named {STRUCTURAL_VALIDATION_FILENAME}"
        )
    for manifest_key, expected_path, paths_key in (
        ("approved_raster_atoms", "source/asset_manifest.json", "approved_raster_manifest"),
        (
            "raster_atom_review_decision",
            "source/raster_atom_review_decision.json",
            "raster_atom_review_decision",
        ),
    ):
        binding = _record(manifest.get(manifest_key), f"artifact_manifest.{manifest_key}")
        if binding["path"] != expected_path:
            raise ValueError(
                f"artifact_manifest.{manifest_key}.path must be {expected_path}"
            )
        paths[paths_key] = _resolve_record(
            package_root, binding, f"artifact_manifest.{manifest_key}"
        )

    raster_manifest = _load_json(
        paths["approved_raster_manifest"], "approved raster manifest"
    )
    raster_assets = raster_manifest.get("assets")
    if not isinstance(raster_assets, list):
        raise ValueError("approved raster manifest assets must be an array")
    expected_sidecars: dict[str, set[tuple[str, str]]] = {
        key: set() for key in ARTIFACT_KEYS
    }
    for index, raw_asset in enumerate(raster_assets):
        asset = _require_object(raw_asset, f"approved raster asset {index}")
        source_relative = "source/" + _portable_relative_path(
            asset.get("path"), f"approved raster asset {index}.path"
        )
        svg_relative = _portable_relative_path(
            asset.get("delivery_svg_path"),
            f"approved raster asset {index}.delivery_svg_path",
        )
        digest = _require_sha256(
            asset.get("sha256"), f"approved raster asset {index}.sha256"
        )
        for relative, label in (
            (source_relative, "source"),
            (svg_relative, "SVG delivery"),
        ):
            _resolve_record(
                package_root,
                {"path": relative, "sha256": digest},
                f"approved raster asset {index} {label}",
            )
        expected_sidecars["svg"].add((svg_relative, digest))
        expected_sidecars["pptx"].add((source_relative, digest))
        expected_sidecars["drawio"].add((source_relative, digest))
    artifacts = _require_object(manifest.get("artifacts"), "artifact_manifest.artifacts")
    if set(artifacts) != set(ARTIFACT_KEYS):
        raise ValueError("artifact manifest must contain exactly svg, pptx, drawio, and pdf_preview")
    hashes: dict[str, str] = {}
    for key in ARTIFACT_KEYS:
        item = _record(artifacts[key], f"artifact_manifest.artifacts.{key}")
        if item["path"] != EXPECTED_ARTIFACT_PATHS[key]:
            raise ValueError(
                f"artifact {key}.path must be {EXPECTED_ARTIFACT_PATHS[key]}"
            )
        for metadata in ("media_type", "editability", "structural_summary"):
            _require_text(item.get(metadata), f"artifact {key}.{metadata}")
        sidecars = item.get("approved_raster_sidecars")
        if not isinstance(sidecars, list):
            raise ValueError(f"artifact {key}.approved_raster_sidecars must be an array")
        path = _resolve_record(package_root, item, f"artifact {key}")
        paths[f"artifact_{key}"] = path
        hashes[key] = item["sha256"]
        observed_sidecars: list[tuple[str, str]] = []
        for index, sidecar in enumerate(sidecars):
            record = _record(
                sidecar, f"artifact {key}.approved_raster_sidecars[{index}]"
            )
            _resolve_record(
                package_root,
                record,
                f"artifact {key}.approved_raster_sidecars[{index}]",
            )
            observed_sidecars.append((record["path"], record["sha256"]))
        if len(observed_sidecars) != len(set(observed_sidecars)) or set(
            observed_sidecars
        ) != expected_sidecars[key]:
            raise ValueError(
                f"artifact {key}.approved_raster_sidecars must exactly match "
                "the approved raster manifest"
            )
    return hashes, package_root


def inspect_reference_case(example_root: str | Path) -> ReferenceCase:
    root = Path(example_root).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f"example root must be a directory: {root}")
    case_path = _resolve_inside(root, REFERENCE_CASE_FILENAME, "reference case")
    case = _load_json(case_path, "reference case")
    if case.get("schema_version") != "1.0":
        raise ValueError("reference case schema_version must be 1.0")
    _check_identity(case, "reference_case")
    paths: dict[str, Path] = {"reference_case": case_path}
    paths["input_sketch"] = _resolve_record(root, case.get("input_sketch"), "input_sketch")
    paths["clarification"] = _resolve_record(root, case.get("clarification"), "clarification")
    if not paths["clarification"].read_text(encoding="utf-8").strip():
        raise ValueError("clarification file must contain a non-empty human-readable brief")

    candidates = _check_reference_candidates(root, case, paths)
    candidate_manifest_path = _resolve_record(
        root, case.get("candidate_manifest"), "candidate_manifest"
    )
    paths["candidate_manifest"] = candidate_manifest_path
    _check_candidate_manifest(
        _load_json(candidate_manifest_path, "candidate manifest"), candidates
    )

    selection = _require_object(case.get("selection"), "reference_case.selection")
    _check_selected(selection, "reference_case.selection", candidates["C"]["sha256"])
    paths["candidate_selection"] = _resolve_record(
        root, selection.get("record"), "selection.record"
    )
    selection_record = _load_json(paths["candidate_selection"], "candidate selection")
    if (
        selection_record.get("decision") != "APPROVE_IMAGEGEN_CANDIDATE"
        or selection_record.get("status") != "approved_for_editable_reconstruction"
        or selection_record.get("editable_reconstruction_authorized") is not True
        or selection_record.get("final_scientific_approval") is not None
    ):
        raise ValueError("candidate selection record is not an explicit reconstruction approval")
    selection_binding = selection_record.get("selected_candidate", selection_record)
    _check_selected(
        _require_object(selection_binding, "candidate selection binding"),
        "candidate selection binding",
        candidates["C"]["sha256"],
    )

    approved_region = _require_object(
        case.get("approved_region_map"), "reference_case.approved_region_map"
    )
    paths["region_map"] = _resolve_record(root, approved_region, "approved_region_map")
    paths["region_map_approval"] = _resolve_record(
        root, approved_region.get("approval_record"), "approved_region_map.approval_record"
    )
    region_approval = _load_json(paths["region_map_approval"], "region map approval")
    _check_identity(region_approval, "region map approval")
    if region_approval.get("decision") != "APPROVE_REGION_MAP_FOR_RECONSTRUCTION":
        raise ValueError("region map approval has the wrong decision")
    if region_approval.get("region_map_sha256") != approved_region.get("sha256"):
        raise ValueError("region map approval is not bound to the approved region map")
    _check_selected(
        _require_object(region_approval.get("selected_candidate"), "region approval candidate"),
        "region approval candidate",
        candidates["C"]["sha256"],
    )
    if region_approval.get("recipe_id") != RECIPE_ID:
        raise ValueError(f"region map approval recipe_id must be {RECIPE_ID}")
    _require_text(region_approval.get("operator"), "region map approval.operator")
    _require_text(region_approval.get("approved_at"), "region map approval.approved_at")
    _require_false(
        region_approval.get("scientific_approval_created"),
        "region map approval.scientific_approval_created",
    )

    reconstruction = _require_object(case.get("reconstruction"), "reference_case.reconstruction")
    if reconstruction.get("recipe_id") != RECIPE_ID:
        raise ValueError(f"reference reconstruction recipe_id must be {RECIPE_ID}")
    builder_relative = _portable_relative_path(
        reconstruction.get("builder_path"), "reference_case.reconstruction.builder_path"
    )
    if builder_relative != BUILDER_RELATIVE_PATH:
        raise ValueError(
            f"reference_case.reconstruction.builder_path must be {BUILDER_RELATIVE_PATH}"
        )
    paths["validator_code"] = _resolve_inside(
        REPOSITORY_ROOT, builder_relative, "reference_case.reconstruction.builder_path"
    )
    if paths["validator_code"] != IMPORTED_VALIDATOR_PATH:
        raise ValueError("the bound validator code is not the validator implementation in use")

    approved_rasters = _record(
        case.get("approved_raster_atoms"), "reference_case.approved_raster_atoms"
    )
    if approved_rasters["path"] != (
        "editable_delivery_c_fidelity_v2/source/asset_manifest.json"
    ):
        raise ValueError("reference approved-raster manifest must use the canonical fidelity-v2 path")
    paths["approved_raster_manifest"] = _resolve_record(
        root, approved_rasters, "reference_case.approved_raster_atoms"
    )
    review_binding = _record(
        approved_rasters.get("review_decision"),
        "reference_case.approved_raster_atoms.review_decision",
    )
    if review_binding["path"] != (
        "editable_delivery_c_fidelity_v2/source/raster_atom_review_decision.json"
    ):
        raise ValueError("reference raster review decision must use the canonical fidelity-v2 path")
    paths["raster_atom_review_decision"] = _resolve_record(
        root,
        review_binding,
        "reference_case.approved_raster_atoms.review_decision",
    )

    artifact_manifest_path = _resolve_record(
        root, case.get("artifact_manifest"), "artifact_manifest"
    )
    if artifact_manifest_path.name != ARTIFACT_MANIFEST_FILENAME:
        raise ValueError(f"artifact manifest must be named {ARTIFACT_MANIFEST_FILENAME}")
    paths["artifact_manifest"] = artifact_manifest_path
    artifact_manifest = _load_json(artifact_manifest_path, "artifact manifest")
    output_hashes, _ = _check_artifact_manifest(root, artifact_manifest, paths)

    case_validation_binding = _record(
        case.get("validation_evidence"), "validation_evidence"
    )
    manifest_validation_binding = _record(
        artifact_manifest.get("validation_report"),
        "artifact_manifest.validation_report",
    )
    if case_validation_binding != manifest_validation_binding:
        raise ValueError(
            "reference_case.validation_evidence must exactly match "
            "artifact_manifest.validation_report"
        )
    case_validation = _resolve_record(
        root, case_validation_binding, "validation_evidence"
    )
    if case_validation != paths["structural_validation_report"]:
        raise ValueError("reference-case validation evidence resolves to another file")
    paths["case_validation_evidence"] = case_validation

    approvals = _require_object(case.get("approvals"), "reference_case.approvals")
    if set(approvals) != set(APPROVAL_KEYS):
        raise ValueError("reference approvals must separate visual, scientific, science_day_use, and public_release")
    visual = _require_object(approvals["visual"], "reference_case.approvals.visual")
    if visual.get("status") != "APPROVED":
        raise ValueError("the frozen reference case requires an APPROVED visual record")
    paths["visual_approval"] = _resolve_record(root, visual, "visual approval")
    visual_approval = _load_json(paths["visual_approval"], "visual approval")
    _check_identity(visual_approval, "visual approval")
    if visual_approval.get("decision") != "APPROVE_VISUAL_DELIVERY":
        raise ValueError("visual approval has the wrong decision")
    if visual_approval.get("artifact_manifest_sha256") != case["artifact_manifest"]["sha256"]:
        raise ValueError("visual approval is not bound to the artifact manifest")
    if visual_approval.get("canonical_artifact_hashes") != output_hashes:
        raise ValueError(
            "visual approval canonical_artifact_hashes do not match the artifact manifest"
        )
    _require_text(visual_approval.get("operator"), "visual approval.operator")
    _require_text(visual_approval.get("approved_at"), "visual approval.approved_at")
    _require_text(visual_approval.get("provenance"), "visual approval.provenance")
    limitations = visual_approval.get("known_limitations")
    if not isinstance(limitations, list) or not limitations or not all(
        isinstance(item, str) and item.strip() for item in limitations
    ):
        raise ValueError("visual approval.known_limitations must be a non-empty string array")
    for key in (
        "scientific_approval_created",
        "science_day_use_approval_created",
        "public_release_approval_created",
    ):
        _require_false(visual_approval.get(key), f"visual approval.{key}")
    for key in APPROVAL_KEYS[1:]:
        if approvals[key] != {"status": "PENDING"}:
            raise ValueError(
                f"reference_case.approvals.{key} is unsupported in v0.1 and must remain PENDING"
            )

    return ReferenceCase(
        example_root=root,
        case=case,
        artifact_manifest=artifact_manifest,
        region_map_approval=region_approval,
        visual_approval=visual_approval,
        paths=paths,
        output_hashes=output_hashes,
    )


def _encoded_json(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def build_validation_report(
    reference: ReferenceCase,
    package_root: Path | None = None,
    *,
    candidate_path: Path | None = None,
    verify_precomputed: bool = True,
) -> dict[str, Any]:
    root = package_root or reference.paths["package_root"]
    selected_path = candidate_path or reference.paths["candidate_C"]
    package_report = validate_package(root, candidate_path=selected_path, write_report=False)
    package_pass = package_report.get("status") == VALIDATOR_STATUS
    if not package_pass:
        raise ValueError(
            f"fidelity-v2 validator returned unexpected status: {package_report.get('status')!r}"
        )
    output_hashes: dict[str, str] = {}
    for key in ARTIFACT_KEYS:
        relative = reference.artifact_manifest["artifacts"][key]["path"]
        replayed = _resolve_inside(root, relative, f"validated output {key}")
        actual = sha256_file(replayed)
        expected = reference.output_hashes[key]
        if actual != expected:
            raise ValueError(f"validated output {key} SHA-256 mismatch")
        output_hashes[key] = actual
    checks = {
        "reference_case_integrity": {"passed": True},
        "artifact_manifest_integrity": {"passed": True},
        "fidelity_v2_package": {
            "passed": True,
            "status": package_report["status"],
            "validator_checks": package_report.get("checks", {}),
        },
    }
    case = reference.case
    report = {
        "schema_version": "1.0",
        "report_type": "structural_delivery_validation",
        "status": "PASSED",
        "case_id": CASE_ID,
        "delivery_revision": DELIVERY_REVISION,
        "input_hashes": {
            "candidate_sha256": case["selection"]["sha256"],
            "candidate_selection_sha256": case["selection"]["record"]["sha256"],
            "region_map_sha256": case["approved_region_map"]["sha256"],
            "approved_raster_manifest_sha256": sha256_file(
                reference.paths["approved_raster_manifest"]
            ),
            "raster_atom_review_decision_sha256": sha256_file(
                reference.paths["raster_atom_review_decision"]
            ),
        },
        "output_hashes": output_hashes,
        "checks": checks,
        "overall_pass": True,
        "scientific_correctness_checked": False,
        "validator": {
            "name": VALIDATOR_NAME,
            "version": VALIDATOR_VERSION,
            "code_sha256": sha256_file(reference.paths["validator_code"]),
        },
    }
    if verify_precomputed:
        frozen_path = reference.paths["structural_validation_report"]
        frozen = _load_json(frozen_path, "precomputed structural validation report")
        if frozen != report:
            raise ValueError("recomputed structural validation report differs from the frozen report")
        if frozen_path.read_bytes() != _encoded_json(report):
            raise ValueError("frozen structural validation report is not deterministically encoded")
    return report


def build_status(reference: ReferenceCase) -> dict[str, Any]:
    approvals = reference.case["approvals"]
    return {
        "schema_version": "1.0",
        "report_type": "reference_case_status",
        "case_id": CASE_ID,
        "delivery_revision": DELIVERY_REVISION,
        "case_integrity": {"status": "VALID", "overall_pass": True},
        "approvals": {
            "visual": {
                "status": approvals["visual"]["status"],
                "decision": reference.visual_approval["decision"],
                "scientific_approval_created": False,
            },
            "scientific": dict(approvals["scientific"]),
            "science_day_use": dict(approvals["science_day_use"]),
            "public_release": dict(approvals["public_release"]),
        },
    }


def _write_json_exclusive(path: Path, value: Mapping[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise ValueError(f"refusing to overwrite existing output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise ValueError(f"refusing to overwrite existing output: {path}") from exc


def _write_text_exclusive(path: Path, value: str) -> None:
    if path.exists() or path.is_symlink():
        raise ValueError(f"refusing to overwrite existing output: {path}")
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise ValueError(f"refusing to overwrite existing output: {path}") from exc


def _require_external_output(path: Path, example_root: Path, label: str) -> Path:
    resolved = path.expanduser().resolve(strict=False)
    try:
        resolved.relative_to(example_root.resolve(strict=True))
    except ValueError:
        return resolved
    raise ValueError(f"{label} must be outside the canonical example root")


def _copy_tree_contents_exclusive(source: Path, destination: Path) -> None:
    if not destination.is_dir() or destination.is_symlink():
        raise ValueError(f"replay run root is missing or unsafe: {destination}")
    for item in sorted(source.rglob("*"), key=lambda value: value.as_posix()):
        relative = item.relative_to(source)
        _portable_relative_path(relative.as_posix(), "frozen package member")
        if item.is_symlink():
            raise ValueError(f"frozen package must not contain symbolic links: {relative.as_posix()}")
        target = destination / relative
        if target.exists() or target.is_symlink():
            raise ValueError(f"refusing to overwrite replay package member: {relative.as_posix()}")
        if item.is_dir():
            target.mkdir()
        elif item.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            with item.open("rb") as input_handle, target.open("xb") as output_handle:
                shutil.copyfileobj(input_handle, output_handle)
        else:
            raise ValueError(f"frozen package contains a non-regular entry: {relative.as_posix()}")


def replay_reference_case(example_root: str | Path, output_dir: str | Path) -> dict[str, Any]:
    reference = inspect_reference_case(example_root)
    run_dir = _require_external_output(Path(output_dir), reference.example_root, "replay output-dir")
    if run_dir.exists() or run_dir.is_symlink():
        raise ValueError(f"refusing to overwrite existing replay output-dir: {run_dir}")

    case = reference.case
    operator = reference.region_map_approval["operator"]
    state = imagegen_workflow.initialize_run(
        run_dir,
        reference.paths["input_sketch"],
        reference.paths["clarification"].read_text(encoding="utf-8"),
    )
    ordered = [next(item for item in case["candidates"] if item["slot"] == slot) for slot in EXPECTED_CANDIDATES]
    native_ids = [item.get("native_tool_call_id") for item in ordered]
    state = imagegen_workflow.register_candidates(
        run_dir,
        [reference.paths[f"candidate_{item['slot']}"] for item in ordered],
        [item["generation_event_id"] for item in ordered],
        operator,
        native_tool_call_ids=native_ids if any(native_ids) else None,
    )
    state = imagegen_workflow.register_candidate_selection_approval(
        run_dir,
        reference.paths["candidate_selection"],
    )
    state = imagegen_workflow.register_region_map_approval(
        run_dir,
        region_map=reference.paths["region_map"],
        approval_record=reference.paths["region_map_approval"],
    )

    _copy_tree_contents_exclusive(reference.paths["package_root"], run_dir)
    candidate_record = next(item for item in state["candidate_pool"] if item["slot"] == SELECTED_SLOT)
    replay_candidate = _resolve_inside(run_dir, candidate_record["path"], "replayed Candidate C")
    if sha256_file(replay_candidate) != case["selection"]["sha256"]:
        raise ValueError("replayed Candidate C no longer matches the frozen selection")
    report = build_validation_report(
        reference,
        run_dir,
        verify_precomputed=True,
    )
    report_relative = reference.artifact_manifest["validation_report"]["path"]
    report_path = run_dir / report_relative
    if report_path.exists() or report_path.is_symlink():
        raise ValueError(f"refusing to overwrite replay validation report: {report_relative}")
    shutil.copyfile(reference.paths["structural_validation_report"], report_path)
    manifest_copy = run_dir / ARTIFACT_MANIFEST_FILENAME
    shutil.copyfile(reference.paths["artifact_manifest"], manifest_copy)

    state = imagegen_workflow.register_delivery(
        run_dir,
        svg=run_dir / reference.artifact_manifest["artifacts"]["svg"]["path"],
        pptx=run_dir / reference.artifact_manifest["artifacts"]["pptx"]["path"],
        drawio=run_dir / reference.artifact_manifest["artifacts"]["drawio"]["path"],
        pdf_preview=run_dir / reference.artifact_manifest["artifacts"]["pdf_preview"]["path"],
        validation_report=report_path,
        artifact_manifest=manifest_copy,
    )
    state = imagegen_workflow.register_visual_approval(
        run_dir, reference.paths["visual_approval"]
    )
    status = build_status(reference)
    readiness = {
        "schema_version": "1.0",
        "report_type": "reference_case_replay_readiness",
        "case_id": CASE_ID,
        "delivery_revision": DELIVERY_REVISION,
        "offline_replay": True,
        "imagegen_or_remote_calls": 0,
        "canonical_modified": False,
        "workflow_stage": state.get("stage"),
        "workflow_revision": state.get("revision"),
        "structural_validation": {
            "status": report["status"],
            "overall_pass": report["overall_pass"],
            "path": report_relative,
        },
        "case_integrity": status["case_integrity"],
        "approvals": status["approvals"],
        "ready_for_scientific_use": status["approvals"]["scientific"].get("status") == "APPROVED",
        "ready_for_science_day_use": status["approvals"]["science_day_use"].get("status") == "APPROVED",
        "ready_for_public_release": status["approvals"]["public_release"].get("status") == "APPROVED",
        "start_here": REPLAY_START_HERE_FILENAME,
    }
    _write_json_exclusive(run_dir / "reference_case_v0_1_readiness.json", readiness)
    _write_text_exclusive(
        run_dir / REPLAY_START_HERE_FILENAME,
        """# Offline v0.1 reference-case replay

This directory is a replay of frozen, hash-bound evidence. It made zero
ImageGen or remote calls.

Start with `reference_case_v0_1_readiness.json`. The replay imported a
separate visual approval bound to the exact artifact-manifest hash, so the
ledger stage is `VISUAL_APPROVED`. Scientific approval, Science Day use, and
public release remain separate `PENDING` decisions.

The copied package's `README.md` and package-internal review fields describe
the reconstruction output before case-level approval; their visual/scientific
approval fields remain null by design. They do not override the imported
case-level visual approval. Automated validation checks programmable
constraints only and does not establish scientific correctness.
""",
    )
    return readiness


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate or replay the frozen v0.1 reference case without ImageGen or network access."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "status"):
        command = subparsers.add_parser(name)
        command.add_argument("--example-root", type=Path, default=DEFAULT_EXAMPLE_ROOT)
        if name == "validate":
            command.add_argument("--report", type=Path)
    replay = subparsers.add_parser("replay")
    replay.add_argument("--example-root", type=Path, default=DEFAULT_EXAMPLE_ROOT)
    replay.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "replay":
            result = replay_reference_case(args.example_root, args.output_dir)
        else:
            reference = inspect_reference_case(args.example_root)
            if args.command == "status":
                result = build_status(reference)
            else:
                result = build_validation_report(reference)
                if args.report is not None:
                    report_path = _require_external_output(
                        args.report, reference.example_root, "validation report"
                    )
                    _write_json_exclusive(report_path, result)
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        print(
            json.dumps(
                {"status": "FAILED", "overall_pass": False, "error": str(exc)},
                sort_keys=True,
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
