#!/usr/bin/env python3
"""Resumable V3 autopilot orchestrator with exactly three human gates."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import json
import re
import shlex
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

from build_figure_editorial_review import (
    build_outputs as build_editorial_outputs,
    resolve_approved_wireframe_preview,
    validate_visual_plan_binding,
)
from build_fixture_semantic_source import build as build_fixture_source
from export_drawio import export as export_drawio
from export_pdf import export as export_pdf
from export_pptx import export as export_pptx
from export_svg import export as export_svg
from figure_artifacts import load_json, sha256_file, write_json
from render_equations import render_manifest
from validate_delivery import validate as validate_delivery
from workflow_v3 import require_valid, utc_now


SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parent
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
CANDIDATE_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
OPERATOR_ATTESTED_CANDIDATE = "operator_attested_candidate"
EXPECTED_DELIVERY_FORMATS = (
    ("svg", "delivery/svg/master.svg"),
    ("figma-ready-svg", "delivery/figma/figure_figma.svg"),
    ("pptx", "delivery/pptx/figure.pptx"),
    ("drawio", "delivery/drawio/figure.drawio"),
    ("publication-pdf", "delivery/pdf/publication.pdf"),
    ("grayscale-pdf", "delivery/pdf/grayscale.pdf"),
    ("drawio-companion-pdf", "delivery/drawio/figure_drawio_preview.pdf"),
)


def relative(path: Path, base: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except ValueError:
        return str(path.resolve())


def require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError("%s must be a lowercase SHA-256 hex digest" % label)
    return value


def scoped_file(run_dir: Path, value: str | Path, label: str) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = run_dir / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(run_dir.resolve())
    except ValueError as exc:
        raise ValueError("%s must resolve inside run directory %s" % (label, run_dir.resolve())) from exc
    if not resolved.is_file():
        raise ValueError("%s is missing or is not a regular file: %s" % (label, resolved))
    return resolved


def file_record(run_dir: Path, path: Path) -> Dict[str, str]:
    return {"path": relative(path, run_dir), "sha256": sha256_file(path)}


def verify_file_record(run_dir: Path, record_value: Mapping[str, Any], label: str) -> Path:
    try:
        path = scoped_file(run_dir, record_value["path"], label)
    except (KeyError, TypeError, ValueError) as exc:
        invariant_error(str(exc))
    if sha256_file(path) != record_value.get("sha256"):
        invariant_error("%s hash changed" % label)
    return path


@contextmanager
def workflow_lock(run_dir: Path):
    """Serialize cooperating workflow processes across validation and state commits."""
    lock_path = run_dir / ".workflow.lock"
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def resume_command(*parts: Any) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def invariant_error(message: str) -> None:
    raise ValueError(
        "run_state security invariant failed: %s. "
        "This legacy or inconsistent sketch state cannot be resumed safely; restart in a new run directory."
        % message
    )


def run_state_mode(state: Mapping[str, Any]) -> str:
    values = list(state.get("gate_status", {}).values())
    if values and all(value == "not_applicable_fixture" for value in values):
        return "fixture"
    if any(value == "not_applicable_fixture" for value in values):
        invariant_error("fixture and sketch gate statuses are mixed")
    return "sketch"


def assert_state_invariants(state: Mapping[str, Any], run_dir: Path) -> None:
    current = state.get("state")
    gates = state.get("gate_status", {})
    provenance = state.get("provenance", {})
    if run_state_mode(state) == "fixture":
        if current not in {"INITIALIZED", "SEMANTIC_BUILD", "DELIVERY_BUILD", "FIXTURE_COMPLETE", "FAILED"}:
            invariant_error("fixture run uses unsupported state %s" % current)
        if provenance.get("image_generation_calls") != 0:
            invariant_error("fixture run must not record image-generation calls")
        if current != "FAILED" and state.get("decision_packet", {}).get("gate_id") != "NONE":
            invariant_error("fixture run cannot expose a human gate packet")
        return
    expected = {
        "INITIALIZED": ("not_reached", "not_reached", "not_reached"),
        "EDITORIAL_REVIEW": ("not_reached", "not_reached", "not_reached"),
        "GATE_1_EDITORIAL_STORY_WIREFRAME": ("awaiting_human", "not_reached", "not_reached"),
        "PNG_DIRECTION": ("approved", "not_reached", "not_reached"),
        "GATE_2_PNG_VISUAL_DIRECTION": ("approved", "awaiting_human", "not_reached"),
        "SEMANTIC_BUILD": ("approved", "approved", "not_reached"),
        "DELIVERY_BUILD": ("approved", "approved", "not_reached"),
        "GATE_3_FINAL_SCIENTIFIC_DELIVERY": ("approved", "approved", "awaiting_human"),
        "COMPLETE": ("approved", "approved", "approved"),
    }
    if current == "FAILED":
        return
    actual = (gates.get("gate_1"), gates.get("gate_2"), gates.get("gate_3"))
    if current not in expected or actual != expected[current]:
        invariant_error("state %s has inconsistent gate statuses %s" % (current, actual))
    expected_packet = {
        "GATE_1_EDITORIAL_STORY_WIREFRAME": "GATE_1",
        "GATE_2_PNG_VISUAL_DIRECTION": "GATE_2",
        "GATE_3_FINAL_SCIENTIFIC_DELIVERY": "GATE_3",
    }.get(current, "NONE")
    decision_packet = state.get("decision_packet", {})
    if decision_packet.get("gate_id") != expected_packet:
        invariant_error("state %s has the wrong decision packet" % current)
    expected_packet_status = "not_applicable" if expected_packet == "NONE" else "awaiting_human"
    if decision_packet.get("status") != expected_packet_status:
        invariant_error("state %s has the wrong decision packet status" % current)

    required: set[str] = set()
    if current not in {"INITIALIZED", "EDITORIAL_REVIEW"}:
        required.add("visual_plan_binding")
    if current in {"PNG_DIRECTION", "GATE_2_PNG_VISUAL_DIRECTION", "SEMANTIC_BUILD", "DELIVERY_BUILD", "GATE_3_FINAL_SCIENTIFIC_DELIVERY", "COMPLETE"}:
        required.add("gate_1_approval")
    if current in {"GATE_2_PNG_VISUAL_DIRECTION", "SEMANTIC_BUILD", "DELIVERY_BUILD", "GATE_3_FINAL_SCIENTIFIC_DELIVERY", "COMPLETE"}:
        required.add("registered_candidates")
    if current in {"SEMANTIC_BUILD", "DELIVERY_BUILD", "GATE_3_FINAL_SCIENTIFIC_DELIVERY", "COMPLETE"}:
        required.add("selected_candidate")
    if current in {"GATE_3_FINAL_SCIENTIFIC_DELIVERY", "COMPLETE"}:
        required.add("delivery_validation")
    missing = sorted(required - set(provenance))
    if missing:
        invariant_error("state %s lacks %s" % (current, ", ".join(missing)))
    if "visual_plan_binding" in required:
        binding = provenance["visual_plan_binding"]
        for path_key, hash_key, label in (
            ("visual_plan_path", "visual_plan_sha256", "approved Visual Plan"),
            ("approved_wireframe_svg_path", "approved_wireframe_svg_sha256", "approved wireframe SVG"),
            ("approved_wireframe_png_path", "approved_wireframe_png_sha256", "approved wireframe preview"),
        ):
            verify_file_record(
                run_dir, {"path": binding.get(path_key), "sha256": binding.get(hash_key)}, label
            )
    if "gate_1_approval" in required:
        approval = provenance["gate_1_approval"]
        plan = provenance["visual_plan_binding"]
        if approval.get("visual_plan_sha256") != plan.get("visual_plan_sha256"):
            invariant_error("Gate 1 approval is not bound to the Visual Plan hash")
        for key, label in (
            ("scientific_interpretation", "Gate 1 scientific interpretation"),
            ("interpretation", "Gate 1 visual interpretation"),
            ("preview", "Gate 1 visual interpretation preview"),
        ):
            if not isinstance(approval.get(key), Mapping):
                invariant_error("Gate 1 approval lacks %s" % key)
            verify_file_record(run_dir, approval[key], label)
    records = provenance.get("registered_candidates", [])
    if not isinstance(records, list):
        invariant_error("registered_candidates must be an array")
    candidates = {item.get("candidate_id"): item for item in records if isinstance(item, Mapping)}
    calls = {item.get("generation_call_id") for item in records if isinstance(item, Mapping)}
    if len(candidates) != len(records) or provenance.get("image_generation_calls") != len(calls):
        invariant_error("registered candidate IDs/call counts are inconsistent")
    approval = provenance.get("gate_1_approval", {})
    for candidate in records:
        verify_file_record(run_dir, candidate, "registered candidate")
        if candidate.get("gate_1_visual_plan_sha256") != approval.get("visual_plan_sha256") or candidate.get("gate_1_interpretation_sha256") != approval.get("interpretation", {}).get("sha256"):
            invariant_error("registered candidate is not bound to Gate 1")
        if candidate.get("provenance_assurance") != "operator_attested_not_independently_verified":
            invariant_error("candidate provenance assurance is missing or overstated")
    if current == "GATE_2_PNG_VISUAL_DIRECTION":
        pool = provenance.get("gate_2_selection_pool")
        if not isinstance(pool, list) or not pool or any(item not in candidates for item in pool):
            invariant_error("Gate 2 selection pool contains an unregistered candidate")
    if "selected_candidate" in required:
        selected = provenance["selected_candidate"]
        registered = candidates.get(selected.get("candidate_id"))
        if registered is None or selected.get("sha256") != registered.get("sha256"):
            invariant_error("Gate 2 selected candidate does not match its registration")
    if "delivery_validation" in required:
        delivery = provenance["delivery_validation"]
        needed = {
            "canonical_source", "equations_source", "manifest", "validation_report", "preview",
            "format_artifacts", "gate_1_scientific_interpretation_sha256",
            "gate_1_visual_interpretation_sha256", "gate_2_candidate_id", "gate_2_candidate_sha256",
        }
        if not isinstance(delivery, Mapping) or not needed.issubset(delivery):
            invariant_error("validated delivery binding is incomplete")
        if {item.get("format") for item in delivery["format_artifacts"]} != {item[0] for item in EXPECTED_DELIVERY_FORMATS}:
            invariant_error("validated delivery format set is inconsistent")
        if (
            delivery.get("gate_1_scientific_interpretation_sha256")
            != provenance["gate_1_approval"]["scientific_interpretation"]["sha256"]
            or delivery.get("gate_1_visual_interpretation_sha256")
            != provenance["gate_1_approval"]["interpretation"]["sha256"]
            or delivery.get("gate_2_candidate_id") != provenance["selected_candidate"]["candidate_id"]
            or delivery.get("gate_2_candidate_sha256") != provenance["selected_candidate"]["sha256"]
        ):
            invariant_error("validated delivery is not bound to Gate 1 and Gate 2 approvals")
        delivery_records = [
            delivery[key] for key in (
                "canonical_source", "equations_source", "manifest", "validation_report", "preview"
            )
        ]
        delivery_records.extend(delivery["format_artifacts"])
        for item in delivery_records:
            verify_file_record(run_dir, item, "validated delivery artifact")


def decision_none() -> Dict[str, Any]:
    return {
        "gate_id": "NONE", "status": "not_applicable", "summary": "No human decision is pending.",
        "questions": [], "recommendation": "Continue deterministic workflow steps.", "resume_command": "",
    }


def initial_state(run_dir: Path, repository_root: Path, input_paths: Sequence[Path], mode: str) -> Dict[str, Any]:
    now = utc_now()
    return {
        "schema_version": "1.1", "run_id": run_dir.name, "workflow_version": "3.1", "execution_count": 1,
        "interaction_mode": "autopilot_with_gates", "state": "INITIALIZED",
        "gate_status": {
            "gate_1": "not_applicable_fixture" if mode == "fixture" else "not_reached",
            "gate_2": "not_applicable_fixture" if mode == "fixture" else "not_reached",
            "gate_3": "not_applicable_fixture" if mode == "fixture" else "not_reached",
        },
        "completed_artifacts": [],
        "delegated_defaults": {
            "allow_low_impact_defaults": True,
            "decisions": [
                {"field": "filenames", "value": "deterministic V3 layout"},
                {"field": "canvas_and_preview", "value": "canonical pixel coordinate system and 2×2 validation preview"},
                {"field": "font_fallback", "value": "Arial/Cambria Math where the platform cannot preserve source font"},
                {"field": "metadata_wording", "value": "stable semantic IDs, hashes, and LaTeX source"},
            ],
        },
        "decision_packet": decision_none(),
        "provenance": {
            "created_at": now, "updated_at": now, "repository_root": str(repository_root.resolve()),
            "input_hashes": {relative(path, repository_root.parent): sha256_file(path) for path in input_paths if path.exists()},
            "image_generation_calls": 0,
        },
        "history": [{"at": now, "event": "run_initialized", "mode": mode, "execution_count": 1}],
    }


def save_state(run_dir: Path, state: Mapping[str, Any]) -> None:
    require_valid(state, "run_state.schema.json")
    assert_state_invariants(state, run_dir)
    pending_path = run_dir / "run_state.json.pending"
    write_json(pending_path, state)
    pending_path.replace(run_dir / "run_state.json")


def add_artifact(state: Dict[str, Any], run_dir: Path, path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)
    value = relative(path, run_dir)
    if value not in state["completed_artifacts"]:
        state["completed_artifacts"].append(value)


def record(state: Dict[str, Any], event: str, **details: Any) -> None:
    now = utc_now()
    state["provenance"]["updated_at"] = now
    state["history"].append({"at": now, "event": event, **details})


def gate1_packet(run_dir: Path, script_path: Path, visual_mode: str) -> Dict[str, Any]:
    resume_base = ["python", script_path.resolve(), "--mode", "sketch", "--run-dir", run_dir.resolve(), "--resume", "--decision"]
    faithful = visual_mode == "faithful_redraw"
    return {
        "gate_id": "GATE_1", "status": "awaiting_human",
        "summary": (
            "Review editorial/figure_editorial_review.json for scientific meaning, labels, relations, and omissions; "
            "then approve one plan-locked visual interpretation or request revision."
        ),
        "questions": [{
            "id": "scientific_meaning_and_wireframe", "question": (
                "Is the structured scientific interpretation acceptable, and which locked wireframe should production use?"
            ),
            "options": [
                {"id": "APPROVE_CONSERVATIVE", "label": "Exact approved Visual Plan", "impact": "Preserves the approved wireframe SVG and PNG byte-for-byte; supporting detail remains in the review/caption."},
                {"id": "APPROVE_RECOMMENDED", "label": "Plan-locked paper-aware overlay", "impact": "Keeps the identical geometry and adds one removable message cue."},
                {"id": "REVISE_GATE_1", "label": "Request revision", "impact": "Keeps production stopped so meaning, labels, relations, omissions, or wireframe can be corrected."}
            ],
        }],
        "recommendation": (
            "APPROVE_CONSERVATIVE: faithful_redraw keeps the researcher-approved geometry as the production authority."
            if faithful else
            "APPROVE_RECOMMENDED: the optional paper-aware cue is isolated from the approved geometry."
        ),
        "resume_command": resume_command(*resume_base, "APPROVE_CONSERVATIVE" if faithful else "APPROVE_RECOMMENDED"),
        "delegated_defaults": ["filenames", "spacing", "canvas size", "font fallback", "preview arrangement"],
    }


def gate2_packet(
    run_dir: Path, script_path: Path, candidates: Sequence[Mapping[str, Any]]
) -> Dict[str, Any]:
    options = []
    for candidate in candidates[:2]:
        options.append({
            "id": candidate["candidate_id"],
            "decision": "APPROVE_PNG",
            "label": Path(candidate["path"]).name,
            "candidate_path": candidate["path"],
            "candidate_sha256": candidate["sha256"],
            "impact": "Approve this exact registered visual direction; scientific structure remains governed by truth and semantic source.",
        })
    options.append({"id": "REJECT_PNG", "label": "Reject directions", "impact": "Return to the same Gate 2 with a bounded repair brief."})
    recommended = candidates[0]
    return {
        "gate_id": "GATE_2", "status": "awaiting_human", "summary": "Select or reject the PNG visual direction.",
        "questions": [{
            "id": "png_direction", "question": "Which generated direction should become the semantic source reference?",
            "options": options,
        }],
        "recommendation": "Approve only a candidate that passes the blocking topology checks; cosmetic SVG corrections remain downstream.",
        "resume_command": resume_command(
            "python", script_path.resolve(), "--mode", "sketch", "--run-dir", run_dir.resolve(),
            "--resume", "--decision", "APPROVE_PNG", "--selected-candidate",
            recommended["candidate_id"], "--selected-candidate-sha256", recommended["sha256"],
        ),
    }


def gate3_packet(run_dir: Path, script_path: Path) -> Dict[str, Any]:
    return {
        "gate_id": "GATE_3", "status": "awaiting_human", "summary": "Approve or reject the structurally checked delivery package.",
        "questions": [{
            "id": "final_delivery", "question": "Is the structurally checked package scientifically acceptable for its intended use?",
            "options": [
                {"id": "APPROVE_FINAL", "label": "Approve delivery", "impact": "Marks the V3 run complete."},
                {"id": "REVISE_DELIVERY", "label": "Request corrections", "impact": "Keeps the run at Gate 3 and records the requested correction."}
            ],
        }],
        "recommendation": "Approve only when scientific invariants pass and each format's editability claim is supported by its validation report.",
        "resume_command": resume_command(
            "python", script_path.resolve(), "--mode", "sketch", "--run-dir", run_dir.resolve(),
            "--resume", "--decision", "APPROVE_FINAL",
        ),
    }


def validate_initial_sketch_inputs(args: argparse.Namespace) -> None:
    paper_sources = list(getattr(args, "paper_source", []) or [])
    required = {
        "--truth": getattr(args, "truth", None),
        "--paper-source": paper_sources[0] if paper_sources else None,
        "--sketch": getattr(args, "sketch", None),
        "--visual-plan": getattr(args, "visual_plan", None),
        "--approved-wireframe": getattr(args, "approved_wireframe", None),
    }
    missing = [flag for flag, path in required.items() if path is None]
    if missing:
        raise ValueError(
            "sketch mode is missing required input(s): %s; no run state was created"
            % ", ".join(missing)
        )
    input_files = [required["--truth"], required["--sketch"], required["--visual-plan"], required["--approved-wireframe"], *paper_sources]
    for path in input_files:
        if not Path(path).is_file():
            raise ValueError("required sketch input is missing or not a regular file: %s" % Path(path))
    if getattr(args, "approved_wireframe_png", None) is None:
        args.approved_wireframe_png = resolve_approved_wireframe_preview(args.visual_plan)
    if not args.approved_wireframe_png.is_file():
        raise ValueError(
            "approved wireframe PNG is missing or not a regular file: %s"
            % args.approved_wireframe_png
        )
    validate_visual_plan_binding(
        args.visual_plan, args.approved_wireframe, args.approved_wireframe_png
    )


def register_png_candidates(
    args: argparse.Namespace, state: Dict[str, Any]
) -> List[Dict[str, Any]]:
    sources = list(getattr(args, "register_png", None) or [])
    hashes = list(getattr(args, "candidate_sha256", None) or [])
    call_ids = list(getattr(args, "generation_call_id", None) or [])
    if not sources:
        raise ValueError(
            "PNG_DIRECTION requires --register-png, --candidate-sha256, and "
            "--generation-call-id for an operator-staged candidate"
        )
    if len(sources) > 2 or len(hashes) != len(sources) or len(call_ids) != len(sources):
        raise ValueError(
            "provide one --candidate-sha256 and --generation-call-id per --register-png "
            "(at most two candidates)"
        )
    candidate_root = (args.run_dir / "generation/candidates").resolve()
    approval = state["provenance"]["gate_1_approval"]
    existing = {
        item["candidate_id"]: item
        for item in state["provenance"].get("registered_candidates", [])
    }
    records: List[Dict[str, Any]] = []
    for value, expected_value, call_id in zip(sources, hashes, call_ids):
        source = scoped_file(args.run_dir, value, "--register-png")
        if source.parent != candidate_root:
            raise ValueError(
                "--register-png must already be inside this run's generation/candidates "
                "directory; the workflow binds exact bytes but does not independently prove their generator"
            )
        candidate_id = source.stem
        if CANDIDATE_ID_PATTERN.fullmatch(candidate_id) is None or candidate_id in existing:
            raise ValueError("candidate filename stem must be a new safe candidate_id")
        if not isinstance(call_id, str) or CANDIDATE_ID_PATTERN.fullmatch(call_id) is None:
            raise ValueError("--generation-call-id must match %s" % CANDIDATE_ID_PATTERN.pattern)
        expected_hash = require_sha256(expected_value, "--candidate-sha256")
        if sha256_file(source) != expected_hash:
            raise ValueError("--candidate-sha256 does not match %s" % source)
        try:
            from PIL import Image
            with Image.open(source) as image:
                image.verify()
                image_format = image.format
        except Exception as exc:
            raise ValueError("registered candidate is not a readable PNG: %s" % source) from exc
        if image_format != "PNG":
            raise ValueError("registered candidate must be PNG encoded: %s" % source)
        record_value = {
            "candidate_id": candidate_id,
            "path": relative(source, args.run_dir),
            "sha256": expected_hash,
            "generator": OPERATOR_ATTESTED_CANDIDATE,
            "generation_call_id": call_id,
            "provenance_assurance": "operator_attested_not_independently_verified",
            "gate_1_visual_plan_sha256": approval["visual_plan_sha256"],
            "gate_1_interpretation_sha256": approval["interpretation"]["sha256"],
        }
        records.append(record_value)
        existing[candidate_id] = record_value
    all_records = list(state["provenance"].get("registered_candidates", [])) + records
    state["provenance"]["registered_candidates"] = all_records
    state["provenance"]["image_generation_calls"] = len({
        item["generation_call_id"] for item in all_records
    })
    state["provenance"]["gate_2_selection_pool"] = [
        item["candidate_id"] for item in records
    ]
    return records


def collect_delivery_evidence(
    run_dir: Path, registered_values: Sequence[Path], state: Mapping[str, Any]
) -> tuple[Dict[str, Any], List[Path]]:
    registered = [
        scoped_file(run_dir, value, "--register-delivery path")
        for value in registered_values
    ]
    semantic = scoped_file(run_dir, "source/semantic_figure.json", "canonical semantic source")
    equations = scoped_file(run_dir, "source/equations.tex", "LaTeX equations source")
    manifest_path = scoped_file(run_dir, "delivery/delivery_manifest.json", "delivery manifest")
    report_path = scoped_file(run_dir, "validation/cross_format_report.json", "validation report")
    if set(registered) != {manifest_path, report_path}:
        raise ValueError(
            "--register-delivery must contain exactly this run's delivery manifest and validation report"
        )

    approval = state["provenance"]["gate_1_approval"]
    selected = state["provenance"]["selected_candidate"]
    semantic_data = load_json(semantic)
    source_hashes = semantic_data.get("provenance", {}).get("source_hashes", {})
    required_source_hashes = {
        "gate_1_scientific_interpretation": approval["scientific_interpretation"]["sha256"],
        "approved_wireframe": approval["interpretation"]["sha256"],
        "approved_png_direction": selected["sha256"],
    }
    mismatched_sources = sorted(
        key for key, expected in required_source_hashes.items()
        if source_hashes.get(key) != expected
    )
    if mismatched_sources:
        raise ValueError(
            "canonical semantic source is not bound to Gate 1/Gate 2 hashes: %s"
            % ", ".join(mismatched_sources)
        )

    fresh = validate_delivery(run_dir)
    if fresh.get("status") != "VERIFIED":
        raise ValueError("fresh cross-format validation must return VERIFIED before Gate 3")
    manifest = load_json(manifest_path)
    report = load_json(report_path)
    require_valid(manifest, "delivery_manifest.schema.json")
    if report.get("status") != "VERIFIED":
        raise ValueError("written cross-format validation report is not VERIFIED")
    figure_id = semantic_data.get("figure_id")
    if not figure_id or manifest.get("figure_id") != figure_id or report.get("figure_id") != figure_id:
        raise ValueError("semantic source, manifest, and report figure_id values must match")
    if scoped_file(run_dir, manifest["canonical_source"], "manifest canonical source") != semantic:
        raise ValueError("manifest canonical_source must be this run's semantic source")
    if scoped_file(run_dir, report["canonical_source"], "report canonical source") != semantic:
        raise ValueError("report canonical_source must be this run's semantic source")
    if scoped_file(run_dir, manifest["validation_report"], "manifest validation report") != report_path:
        raise ValueError("manifest validation_report must be this run's report")

    formats = {
        item.get("format"): item
        for item in manifest.get("formats", [])
        if isinstance(item, Mapping)
    }
    if set(formats) != {item[0] for item in EXPECTED_DELIVERY_FORMATS}:
        raise ValueError("delivery manifest does not contain the exact required adapter formats")
    artifacts: List[Dict[str, Any]] = []
    evidence = [semantic, equations]
    fresh_checks = {
        item.get("format"): item
        for item in fresh.get("checks", [])
        if isinstance(item, Mapping)
    }
    semantic_check = fresh_checks.get("semantic-source", {})
    semantic_hash = sha256_file(semantic)
    if semantic_check.get("sha256") != semantic_hash:
        raise ValueError("canonical semantic source changed after fresh validation")
    for name, relative_path in EXPECTED_DELIVERY_FORMATS:
        path = scoped_file(run_dir, relative_path, "%s delivery artifact" % name)
        item = formats[name]
        if scoped_file(run_dir, item.get("path", ""), "%s manifest path" % name) != path:
            raise ValueError("%s manifest path is not the expected in-run artifact" % name)
        fresh_check = fresh_checks.get(name, {})
        current_hash = sha256_file(path)
        if fresh_check.get("sha256") != current_hash:
            raise ValueError("%s bytes do not match the fresh validation evidence" % name)
        if item.get("status") != fresh_check.get("status"):
            raise ValueError("%s manifest status does not match fresh validation" % name)
        artifacts.append({
            "format": name,
            "path": relative(path, run_dir),
            "sha256": current_hash,
        })
        evidence.append(path)
    preview_data = fresh.get("preview", {})
    preview = scoped_file(run_dir, "validation/cross_format_preview.png", "validation preview")
    if preview_data.get("status") != "VERIFIED":
        raise ValueError("fresh cross-format preview is not VERIFIED")
    if scoped_file(run_dir, preview_data.get("path", ""), "reported preview") != preview:
        raise ValueError("fresh validator reported the wrong preview path")
    preview_hash = sha256_file(preview)
    if preview_data.get("sha256") != preview_hash:
        raise ValueError("preview bytes do not match the fresh validation evidence")
    evidence.extend([manifest_path, report_path, preview])
    binding = {
        "canonical_source": {"path": relative(semantic, run_dir), "sha256": semantic_hash},
        "equations_source": file_record(run_dir, equations),
        "manifest": file_record(run_dir, manifest_path),
        "validation_report": file_record(run_dir, report_path),
        "preview": {"path": relative(preview, run_dir), "sha256": preview_hash},
        "format_artifacts": artifacts,
        "gate_1_scientific_interpretation_sha256": approval["scientific_interpretation"]["sha256"],
        "gate_1_visual_interpretation_sha256": approval["interpretation"]["sha256"],
        "gate_2_candidate_id": selected["candidate_id"],
        "gate_2_candidate_sha256": selected["sha256"],
    }
    return binding, evidence


def run_fixture(args: argparse.Namespace, state: Dict[str, Any]) -> Dict[str, Any]:
    run_dir = args.run_dir
    state["state"] = "SEMANTIC_BUILD"
    record(state, "fixture_semantic_build_started")
    save_state(run_dir, state)
    fixture_svg = args.fixture_svg or REPOSITORY_ROOT / "tests/fixtures/generic_semantic_pass.svg"
    fixture_spec = args.fixture_spec or REPOSITORY_ROOT / "tests/fixtures/generic_svg_fixture_spec.json"
    build_fixture_source(fixture_svg, fixture_spec, run_dir)
    for path in [run_dir / "source/semantic_figure.json", run_dir / "source/equations.tex", run_dir / "math/equations.tex", run_dir / "math/equation_manifest.json"]:
        add_artifact(state, run_dir, path)
    render_report = render_manifest(run_dir / "math/equation_manifest.json", run_dir / "math/rendered")
    if render_report["status"] != "VERIFIED":
        raise RuntimeError("fixture equation rendering failed")
    for equation in render_report["equations"]:
        add_artifact(state, run_dir, Path(equation["path"]))
    state["state"] = "DELIVERY_BUILD"
    record(state, "fixture_delivery_build_started")
    save_state(run_dir, state)
    semantic = run_dir / "source/semantic_figure.json"
    export_svg(semantic, run_dir / "master/master.svg", "svg")
    export_svg(semantic, run_dir / "delivery/svg/master.svg", "svg")
    export_svg(semantic, run_dir / "delivery/figma/figure_figma.svg", "figma")
    pptx_report = export_pptx(semantic, run_dir / "delivery/pptx", run_dir / "math/rendered")
    drawio_report = export_drawio(semantic, run_dir / "delivery/drawio")
    pdf_report = export_pdf(semantic, run_dir / "delivery/pdf")
    if pptx_report["status"] != "VERIFIED" or drawio_report["status"] != "VERIFIED" or pdf_report["status"] != "VERIFIED":
        raise RuntimeError("one or more fixture adapters failed")
    validation = validate_delivery(run_dir)
    if validation["status"] != "VERIFIED":
        raise RuntimeError("fixture cross-format validation failed")
    for path in [
        run_dir / "master/master.svg", run_dir / "delivery/svg/master.svg", run_dir / "delivery/figma/figure_figma.svg",
        run_dir / "delivery/pptx/figure.pptx", run_dir / "delivery/drawio/figure.drawio",
        run_dir / "delivery/drawio/figure_drawio.svg", run_dir / "delivery/drawio/figure_drawio_preview.pdf",
        run_dir / "delivery/pdf/publication.pdf", run_dir / "delivery/pdf/grayscale.pdf",
        run_dir / "delivery/delivery_manifest.json", run_dir / "validation/cross_format_report.json",
        run_dir / "validation/cross_format_preview.png",
    ]:
        add_artifact(state, run_dir, path)
    state["state"] = "FIXTURE_COMPLETE"
    state["decision_packet"] = decision_none()
    record(state, "fixture_complete", image_generation_calls=0)
    save_state(run_dir, state)
    return state


def run_sketch_initial(args: argparse.Namespace, state: Dict[str, Any]) -> Dict[str, Any]:
    visual_plan = getattr(args, "visual_plan", None)
    approved_wireframe = getattr(args, "approved_wireframe", None)
    approved_wireframe_png = getattr(args, "approved_wireframe_png", None)
    state["state"] = "EDITORIAL_REVIEW"
    record(state, "editorial_review_started")
    report = build_editorial_outputs(
        args.truth,
        args.paper_source,
        args.sketch,
        args.run_dir / "editorial",
        visual_plan,
        approved_wireframe,
        approved_wireframe_png,
    )
    if report["status"] != "VERIFIED":
        raise RuntimeError("editorial artifact rendering failed")
    for item in report["artifacts"]:
        add_artifact(state, args.run_dir, Path(item["path"]))
    add_artifact(state, args.run_dir, args.run_dir / "editorial/editorial_build_report.json")
    state["provenance"]["visual_plan_binding"] = {
        **report["visual_plan_binding"],
        "visual_plan_path": "visual_plan/visual_plan.json",
        "approved_wireframe_svg_path": "visual_plan/approved_wireframe.svg",
        "approved_wireframe_png_path": "visual_plan/approved_wireframe.png",
    }
    state["state"] = "GATE_1_EDITORIAL_STORY_WIREFRAME"
    state["gate_status"]["gate_1"] = "awaiting_human"
    state["decision_packet"] = gate1_packet(
        args.run_dir,
        Path(__file__),
        report["visual_plan_binding"]["visual_mode"],
    )
    write_json(args.run_dir / "gate_1_decision_packet.json", state["decision_packet"])
    add_artifact(state, args.run_dir, args.run_dir / "gate_1_decision_packet.json")
    record(state, "gate_1_reached", image_generation_calls=0)
    save_state(args.run_dir, state)
    return state


def resume_sketch(args: argparse.Namespace, state: Dict[str, Any]) -> Dict[str, Any]:
    current = state["state"]
    decision = args.decision
    if current == "GATE_1_EDITORIAL_STORY_WIREFRAME":
        binding = state["provenance"]["visual_plan_binding"]
        plan_snapshot = scoped_file(args.run_dir, binding["visual_plan_path"], "approved Visual Plan")
        if sha256_file(plan_snapshot) != binding["visual_plan_sha256"]:
            raise ValueError("approved Visual Plan bytes changed before Gate 1 decision")
        if decision not in {"APPROVE_RECOMMENDED", "APPROVE_CONSERVATIVE", "REVISE_GATE_1"}:
            raise ValueError("Gate 1 requires APPROVE_RECOMMENDED, APPROVE_CONSERVATIVE, or REVISE_GATE_1")
        if decision == "REVISE_GATE_1":
            record(state, "gate_1_revision_requested")
            save_state(args.run_dir, state)
            return state
        stem = "recommended" if decision == "APPROVE_RECOMMENDED" else "conservative"
        interpretation = scoped_file(
            args.run_dir, "editorial/wireframe_%s.svg" % stem, "selected Gate 1 interpretation"
        )
        preview = scoped_file(
            args.run_dir, "editorial/wireframe_%s.png" % stem, "selected Gate 1 interpretation preview"
        )
        scientific_interpretation = scoped_file(
            args.run_dir, "editorial/figure_editorial_review.json", "Gate 1 scientific interpretation"
        )
        state["provenance"]["gate_1_approval"] = {
            "decision": decision,
            "visual_plan_sha256": binding["visual_plan_sha256"],
            "scientific_interpretation": file_record(args.run_dir, scientific_interpretation),
            "interpretation": file_record(args.run_dir, interpretation),
            "preview": file_record(args.run_dir, preview),
        }
        state["gate_status"]["gate_1"] = "approved"
        state["state"] = "PNG_DIRECTION"
        state["decision_packet"] = decision_none()
        record(
            state,
            "gate_1_approved",
            decision=decision,
            visual_plan_sha256=binding["visual_plan_sha256"],
            scientific_interpretation_sha256=state["provenance"]["gate_1_approval"]["scientific_interpretation"]["sha256"],
            interpretation_sha256=state["provenance"]["gate_1_approval"]["interpretation"]["sha256"],
        )
        save_state(args.run_dir, state)
        return state
    if current == "PNG_DIRECTION":
        candidates = register_png_candidates(args, state)
        for candidate in candidates:
            add_artifact(state, args.run_dir, scoped_file(args.run_dir, candidate["path"], "registered candidate"))
        state["state"] = "GATE_2_PNG_VISUAL_DIRECTION"
        state["gate_status"]["gate_2"] = "awaiting_human"
        state["decision_packet"] = gate2_packet(args.run_dir, Path(__file__), candidates)
        write_json(args.run_dir / "gate_2_decision_packet.json", state["decision_packet"])
        add_artifact(state, args.run_dir, args.run_dir / "gate_2_decision_packet.json")
        record(
            state,
            "gate_2_reached",
            candidates=[
                {"candidate_id": item["candidate_id"], "path": item["path"], "sha256": item["sha256"]}
                for item in candidates
            ],
        )
        save_state(args.run_dir, state)
        return state
    if current == "GATE_2_PNG_VISUAL_DIRECTION":
        if decision not in {"APPROVE_PNG", "REJECT_PNG"}:
            raise ValueError("Gate 2 requires APPROVE_PNG or REJECT_PNG")
        if decision == "REJECT_PNG":
            state["state"] = "PNG_DIRECTION"
            state["gate_status"]["gate_2"] = "not_reached"
            state["decision_packet"] = decision_none()
            record(state, "gate_2_rejected")
        else:
            selected_value = getattr(args, "selected_candidate", None)
            selected_hash = getattr(args, "selected_candidate_sha256", None)
            if not selected_value or not selected_hash:
                raise ValueError(
                    "APPROVE_PNG requires --selected-candidate and --selected-candidate-sha256; "
                    "generic approval or --yes/force cannot select Gate 2"
                )
            registered = {
                item["candidate_id"]: item
                for item in state["provenance"].get("registered_candidates", [])
            }
            matches = [
                item for item in registered.values()
                if selected_value in {item["candidate_id"], item["path"], Path(item["path"]).name}
            ]
            if len(matches) != 1:
                raise ValueError("--selected-candidate must identify exactly one registered Gate 2 candidate")
            selected = matches[0]
            pool = state["provenance"].get("gate_2_selection_pool", [])
            if selected["candidate_id"] not in pool:
                raise ValueError("--selected-candidate is not in the current Gate 2 decision packet")
            if require_sha256(selected_hash, "--selected-candidate-sha256") != selected["sha256"]:
                raise ValueError("--selected-candidate-sha256 does not match the registered candidate")
            selected_path = scoped_file(args.run_dir, selected["path"], "selected Gate 2 candidate")
            if sha256_file(selected_path) != selected["sha256"]:
                raise ValueError("selected Gate 2 candidate bytes changed after registration")
            state["provenance"]["selected_candidate"] = dict(selected)
            state["gate_status"]["gate_2"] = "approved"
            state["state"] = "SEMANTIC_BUILD"
            state["decision_packet"] = decision_none()
            record(
                state,
                "gate_2_approved",
                candidate_id=selected["candidate_id"],
                candidate_sha256=selected["sha256"],
            )
        save_state(args.run_dir, state)
        return state
    if current in {"SEMANTIC_BUILD", "DELIVERY_BUILD"}:
        registered_delivery = list(getattr(args, "register_delivery", None) or [])
        if not registered_delivery:
            raise ValueError(
                "semantic/delivery build resume requires --register-delivery for this run's "
                "delivery manifest and VERIFIED cross-format report"
            )
        delivery_binding, evidence_paths = collect_delivery_evidence(
            args.run_dir, registered_delivery, state
        )
        state["provenance"]["delivery_validation"] = delivery_binding
        for path in evidence_paths:
            add_artifact(state, args.run_dir, path)
        state["state"] = "GATE_3_FINAL_SCIENTIFIC_DELIVERY"
        state["gate_status"]["gate_3"] = "awaiting_human"
        state["decision_packet"] = gate3_packet(args.run_dir, Path(__file__))
        write_json(args.run_dir / "gate_3_decision_packet.json", state["decision_packet"])
        add_artifact(state, args.run_dir, args.run_dir / "gate_3_decision_packet.json")
        record(
            state,
            "gate_3_reached",
            validation_report_sha256=delivery_binding["validation_report"]["sha256"],
            delivery_manifest_sha256=delivery_binding["manifest"]["sha256"],
        )
        save_state(args.run_dir, state)
        return state
    if current == "GATE_3_FINAL_SCIENTIFIC_DELIVERY":
        if decision not in {"APPROVE_FINAL", "REVISE_DELIVERY"}:
            raise ValueError("Gate 3 requires APPROVE_FINAL or REVISE_DELIVERY")
        if decision == "APPROVE_FINAL":
            state["gate_status"]["gate_3"] = "approved"
            state["state"] = "COMPLETE"
            state["decision_packet"] = decision_none()
            record(state, "workflow_complete")
        else:
            state["state"] = "DELIVERY_BUILD"
            state["gate_status"]["gate_3"] = "not_reached"
            state["decision_packet"] = decision_none()
            state["provenance"].pop("delivery_validation", None)
            record(state, "gate_3_revision_requested")
        save_state(args.run_dir, state)
        return state
    if current in {"INITIALIZED", "EDITORIAL_REVIEW"}:
        raise ValueError(
            "pre-Gate-1 sketch state cannot be resumed safely; restart in a new run directory "
            "with all required sketch inputs"
        )
    raise ValueError("cannot resume state %s" % current)


def _run_locked(args: argparse.Namespace) -> Dict[str, Any]:
    args.run_dir = args.run_dir.resolve()
    state_path = args.run_dir / "run_state.json"
    if args.resume:
        if not state_path.exists():
            raise FileNotFoundError("--resume requested but run_state.json does not exist")
        state = load_json(state_path)
        try:
            require_valid(state, "run_state.schema.json")
        except ValueError as exc:
            raise ValueError(
                "persisted run_state is incompatible with enforced gate bindings; "
                "restart in a new run directory. Details: %s" % exc
            ) from exc
        assert_state_invariants(state, args.run_dir)
        if run_state_mode(state) != args.mode:
            raise ValueError(
                "--mode %s does not match the persisted %s run state"
                % (args.mode, run_state_mode(state))
            )
        if state["execution_count"] != 1:
            raise ValueError("execution_count must remain exactly 1")
        record(state, "run_resumed", prior_state=state["state"])
        if args.mode == "fixture":
            if state["state"] == "FIXTURE_COMPLETE" and args.decision != "REVALIDATE":
                return state
            return run_fixture(args, state)
        return resume_sketch(args, state)
    if state_path.exists():
        raise FileExistsError("run already exists; use --resume. Exactly-once initialization prevents overwrite: %s" % state_path)
    if args.mode == "sketch":
        validate_initial_sketch_inputs(args)
    args.run_dir.mkdir(parents=True, exist_ok=True)
    inputs: List[Path] = []
    if args.mode == "fixture":
        inputs = [
            args.fixture_svg or REPOSITORY_ROOT / "tests/fixtures/generic_semantic_pass.svg",
            args.fixture_spec or REPOSITORY_ROOT / "tests/fixtures/generic_svg_fixture_spec.json",
        ]
    else:
        inputs = [
            path for path in [
                args.truth,
                args.sketch,
                *args.paper_source,
                getattr(args, "visual_plan", None),
                getattr(args, "approved_wireframe", None),
                getattr(args, "approved_wireframe_png", None),
            ] if path
        ]
    state = initial_state(args.run_dir, REPOSITORY_ROOT, inputs, args.mode)
    if args.mode == "fixture":
        save_state(args.run_dir, state)
        return run_fixture(args, state)
    return run_sketch_initial(args, state)


def run(args: argparse.Namespace) -> Dict[str, Any]:
    args.run_dir = args.run_dir.resolve()
    if CANDIDATE_ID_PATTERN.fullmatch(args.run_dir.name) is None:
        raise ValueError("run directory name must match %s" % CANDIDATE_ID_PATTERN.pattern)
    if args.resume:
        if not args.run_dir.is_dir():
            raise FileNotFoundError("--resume run directory does not exist: %s" % args.run_dir)
    else:
        if args.mode == "sketch":
            validate_initial_sketch_inputs(args)
        args.run_dir.mkdir(parents=True, exist_ok=True)
    with workflow_lock(args.run_dir):
        return _run_locked(args)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["fixture", "sketch"], required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--decision")
    parser.add_argument("--truth", type=Path)
    parser.add_argument("--paper-source", action="append", type=Path, default=[])
    parser.add_argument("--sketch", type=Path)
    parser.add_argument("--visual-plan", type=Path)
    parser.add_argument("--approved-wireframe", type=Path)
    parser.add_argument("--approved-wireframe-png", type=Path)
    parser.add_argument("--fixture-svg", type=Path)
    parser.add_argument("--fixture-spec", type=Path)
    parser.add_argument("--register-png", action="append", type=Path)
    parser.add_argument("--candidate-sha256", action="append")
    parser.add_argument("--generation-call-id", action="append")
    parser.add_argument("--selected-candidate")
    parser.add_argument("--selected-candidate-sha256")
    parser.add_argument("--register-delivery", action="append", type=Path)
    args = parser.parse_args()
    state = run(args)
    print(json.dumps(state, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
