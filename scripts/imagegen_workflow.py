#!/usr/bin/env python3
"""Local evidence ledger for a Codex ImageGen-first figure workflow.

This module never invokes an image model.  It records operator-attested candidate
artifacts produced outside this process, binds every decision to file hashes, and
keeps final scientific approval separate from automated delivery validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from typing import Any, Mapping, Sequence

from PIL import Image


STATE_FILENAME = "imagegen_workflow_state.json"
STATE_HISTORY_DIRECTORY = "ledger/state_history"
CANDIDATE_APPROVAL_PATH = "approvals/candidate_selection.json"
REGION_MAP_PATH = "approvals/approved_region_map.json"
REGION_MAP_APPROVAL_PATH = "approvals/region_map_approval.json"
VISUAL_APPROVAL_PATH = "approvals/visual_delivery.json"
FINAL_APPROVAL_PATH = "approvals/final_delivery.json"
PROVENANCE_ASSURANCE = "operator_attested_not_independently_verified"
PDF_ROLE = "preview_export_not_editable_source"
VALIDATION_SCOPE = "passing_structural_report_and_artifact_manifest_hash_bound"
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
COMBINATION_REQUIRES_NEW_RUN = (
    "v0.1 cannot approve a mixed candidate for editable reconstruction. "
    "Create a new append-only proposal run that renders the requested combination "
    "into one A-E slot, then approve that exact hash-bound candidate."
)

CANDIDATE_DIRECTIONS: tuple[tuple[str, str, str], ...] = (
    ("A", "A-faithful", "faithful"),
    ("B", "B-publication", "publication"),
    ("C", "C-presentation", "presentation"),
    ("D", "D-alternative-layout", "alternative-layout"),
    ("E", "E-visual-variant", "visual-variant"),
)

STAGES = (
    "CLARIFICATION_COMPLETE",
    "CANDIDATES_REGISTERED",
    "CANDIDATE_APPROVED",
    "REGION_MAP_APPROVED",
    "DELIVERY_REGISTERED",
    "VISUAL_APPROVED",
    "FINAL_APPROVED",
)

DESIGN_NOTES = {
    "A": "Faithful cleanup of the clarified sketch.",
    "B": "Compact publication-oriented composition.",
    "C": "Presentation-oriented visual hierarchy.",
    "D": "Alternative layout exploration.",
    "E": "Distinct visual-style exploration.",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty human-readable string")
    return value.strip()


def require_approval_timestamp(value: Any, label: str) -> str:
    """Require a parseable, timezone-aware ISO-8601 approval timestamp."""
    raw = require_text(value, label)
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{label} must be a timezone-aware ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} must be a timezone-aware ISO-8601 timestamp")
    return raw


def require_approval_metadata(
    approval: Mapping[str, Any],
    label: str,
    *,
    allow_legacy_approval_basis: bool = False,
) -> tuple[str, str, str]:
    """Validate the human and provenance fields on an imported approval record."""
    operator = require_text(approval.get("operator"), f"{label} operator")
    approved_at = require_approval_timestamp(
        approval.get("approved_at"), f"{label} approved_at"
    )
    provenance_value = approval.get("provenance")
    if provenance_value is None and allow_legacy_approval_basis:
        # The frozen v0.1 region approval predates the current field name.  Its
        # non-empty approval_basis carries the same operator-attested provenance
        # without changing the immutable source record.
        provenance_value = approval.get("approval_basis")
    provenance = require_text(provenance_value, f"{label} provenance")
    return operator, approved_at, provenance


def require_existing_file(path: str | Path, label: str) -> Path:
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file():
        raise ValueError(f"{label} is missing or is not a regular file: {resolved}")
    try:
        if resolved.stat().st_size <= 0:
            raise ValueError(f"{label} is empty: {resolved}")
        with resolved.open("rb") as handle:
            handle.read(1)
    except OSError as exc:
        raise ValueError(f"{label} is not readable: {resolved}") from exc
    return resolved


def require_png(path: str | Path, label: str) -> Path:
    resolved = require_existing_file(path, label)
    if resolved.suffix.lower() != ".png":
        raise ValueError(f"{label} must use the .png extension: {resolved}")
    try:
        with Image.open(resolved) as image:
            if image.format != "PNG":
                raise ValueError(f"{label} is not a PNG image: {resolved}")
            image.verify()
    except (OSError, SyntaxError) as exc:
        raise ValueError(f"{label} is not a readable PNG image: {resolved}") from exc
    return resolved


def require_inside_run(run_dir: Path, path: str | Path, label: str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = run_dir / candidate
    resolved = candidate.expanduser().resolve()
    try:
        resolved.relative_to(run_dir.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} must be located inside run directory {run_dir.resolve()}") from exc
    return require_existing_file(resolved, label)


def relative_to_run(run_dir: Path, path: Path) -> str:
    return path.resolve().relative_to(run_dir.resolve()).as_posix()


def require_portable_relative_path(path: str | Path, label: str) -> str:
    """Reject host-specific or escaping paths before reading a shareable ledger."""
    raw = str(path)
    segments = raw.split("/")
    if (
        not raw
        or Path(raw).is_absolute()
        or PureWindowsPath(raw).is_absolute()
        or bool(PureWindowsPath(raw).drive)
        or raw.startswith("~")
        or raw.lower().startswith("file:")
        or "\\" in raw
        or any(segment in {"", ".", ".."} for segment in segments)
    ):
        raise ValueError(f"{label} path must be a portable run-relative path")
    return raw


def artifact_record(path: Path, *, relative_base: Path) -> dict[str, str]:
    displayed_path = relative_to_run(relative_base, path)
    require_portable_relative_path(displayed_path, "artifact")
    return {"path": displayed_path, "sha256": sha256_file(path)}


def copy_artifact_into_run(
    source: Path,
    run_dir: Path,
    relative_path: str,
    label: str,
) -> Path:
    """Create a byte-identical, fixed-name ledger copy without exposing the source path."""
    portable_path = require_portable_relative_path(relative_path, label)
    destination = run_dir.joinpath(*portable_path.split("/"))
    try:
        destination.parent.resolve(strict=False).relative_to(run_dir.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} destination must stay inside the run directory") from exc
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        destination.parent.resolve().relative_to(run_dir.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} destination must stay inside the run directory") from exc
    if destination.exists() or destination.is_symlink():
        raise ValueError(f"refusing to overwrite imported {label}: {portable_path}")
    try:
        with source.open("rb") as input_handle, destination.open("xb") as output_handle:
            shutil.copyfileobj(input_handle, output_handle)
            output_handle.flush()
            os.fsync(output_handle.fileno())
    except OSError as exc:
        if destination.is_file() and not destination.is_symlink():
            destination.unlink()
        raise ValueError(f"could not import {label} into the run directory") from exc
    if sha256_file(destination) != sha256_file(source):
        destination.unlink()
        raise ValueError(f"imported {label} does not match its source SHA-256")
    return destination


def state_path(run_dir: Path) -> Path:
    return run_dir.resolve() / STATE_FILENAME


def state_history_path(run_dir: Path, revision: int) -> Path:
    return run_dir.resolve() / STATE_HISTORY_DIRECTORY / f"{revision:04d}.json"


def write_json_exclusive(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise ValueError(f"refusing to overwrite existing record: {path}") from exc


def write_current_state(run_dir: Path, state: Mapping[str, Any], *, initialize: bool = False) -> None:
    assert_state_invariants(state, run_dir, verify_files=True)
    revision = state.get("revision")
    if not isinstance(revision, int) or revision < 1:
        raise ValueError("state revision must be a positive integer")
    snapshot = state_history_path(run_dir, revision)
    write_json_exclusive(snapshot, state)

    current = state_path(run_dir)
    if initialize:
        write_json_exclusive(current, state)
        return
    if not current.is_file():
        raise ValueError(f"existing run is missing {STATE_FILENAME}")
    pending = current.with_name(f".{STATE_FILENAME}.pending")
    write_json_exclusive(pending, state)
    pending.replace(current)


def read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is unreadable or invalid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must contain a JSON object: {path}")
    return value


def record_event(state: dict[str, Any], event: str, **details: Any) -> None:
    at = utc_now()
    state["updated_at"] = at
    state["history"].append({"at": at, "event": event, **details})


def advance_state(run_dir: Path, state: dict[str, Any], event: str, **details: Any) -> dict[str, Any]:
    state["revision"] += 1
    record_event(state, event, **details)
    write_current_state(run_dir, state)
    return state


def verify_record(record: Mapping[str, Any], label: str, *, run_dir: Path) -> Path:
    raw_path = record.get("path")
    expected = record.get("sha256")
    if not isinstance(raw_path, str) or not raw_path:
        raise ValueError(f"{label} has no artifact path")
    if not isinstance(expected, str) or SHA256_PATTERN.fullmatch(expected) is None:
        raise ValueError(f"{label} has an invalid SHA-256 binding")
    portable_path = require_portable_relative_path(raw_path, label)
    path = require_inside_run(run_dir, portable_path, label)
    if sha256_file(path) != expected:
        raise ValueError(f"{label} no longer matches its recorded SHA-256")
    return path


def _candidate_map(state: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    pool = state.get("candidate_pool", [])
    if not isinstance(pool, list):
        raise ValueError("candidate_pool must be an array")
    return {
        item["slot"]: item
        for item in pool
        if isinstance(item, Mapping) and isinstance(item.get("slot"), str)
    }


def assert_state_invariants(
    state: Mapping[str, Any], run_dir: Path, *, verify_files: bool
) -> None:
    if state.get("schema_version") != "1.1" or state.get("workflow") != "codex_imagegen_artifact_ledger":
        raise ValueError("unsupported or malformed ImageGen workflow state")
    stage = state.get("stage")
    if stage not in STAGES:
        raise ValueError(f"unsupported ImageGen workflow stage: {stage}")
    history = state.get("history")
    revision = state.get("revision")
    if not isinstance(history, list) or not history:
        raise ValueError("workflow history must be non-empty")
    if not isinstance(revision, int) or revision != len(history):
        raise ValueError("workflow revision must equal the append-only history length")
    events = [item.get("event") if isinstance(item, Mapping) else None for item in history]
    if events[0] != "clarification_recorded":
        raise ValueError("workflow history must begin with clarification_recorded")
    expected_length = STAGES.index(stage) + 1
    if len(events) != expected_length:
        raise ValueError("workflow stage does not match its append-only event sequence")
    fixed_events = {
        1: "five_candidates_registered",
        3: "region_map_explicitly_approved",
        4: "editable_delivery_registered_after_structural_validation",
        5: "visual_delivery_explicitly_approved",
        6: "final_delivery_explicitly_approved",
    }
    for index, expected_event in fixed_events.items():
        if index < len(events) and events[index] != expected_event:
            raise ValueError("workflow event sequence is inconsistent with its stage")
    if len(events) >= 3 and events[2] not in {
        "candidate_explicitly_approved",
        "candidate_combination_explicitly_approved",
    }:
        raise ValueError("workflow selection event is missing or invalid")
    clarification = state.get("clarification", {})
    if not isinstance(clarification, Mapping):
        raise ValueError("clarification record is missing")
    require_text(clarification.get("brief"), "clarification brief")

    sketch = state.get("sketch")
    if not isinstance(sketch, Mapping):
        raise ValueError("sketch binding is missing")
    if verify_files:
        verify_record(sketch, "source sketch", run_dir=run_dir)

    pool = state.get("candidate_pool")
    if not isinstance(pool, list):
        raise ValueError("candidate_pool must be an array")
    if stage == "CLARIFICATION_COMPLETE":
        if pool:
            raise ValueError("clarification-only state cannot contain candidates")
    else:
        if len(pool) != 5:
            raise ValueError("registered candidate pool must contain exactly five candidates")
        expected = {slot: (candidate_id, direction) for slot, candidate_id, direction in CANDIDATE_DIRECTIONS}
        slots: set[str] = set()
        generation_events: set[str] = set()
        native_tool_calls: set[str] = set()
        candidate_ids: set[str] = set()
        for item in pool:
            if not isinstance(item, Mapping):
                raise ValueError("each candidate record must be an object")
            slot = item.get("slot")
            candidate_id = item.get("candidate_id")
            direction = item.get("direction")
            if slot not in expected or expected[slot] != (candidate_id, direction):
                raise ValueError("candidate slot, ID, and direction do not match the fixed A-E pool")
            if slot in slots or candidate_id in candidate_ids:
                raise ValueError("candidate slots and IDs must be unique")
            slots.add(slot)
            candidate_ids.add(candidate_id)
            event_id = require_text(item.get("generation_event_id"), "generation event ID")
            if event_id in generation_events:
                raise ValueError("generation event IDs must be unique")
            generation_events.add(event_id)
            native_tool_call_id = item.get("native_tool_call_id")
            if native_tool_call_id is not None:
                native_tool_call_id = require_text(
                    native_tool_call_id, "native tool call ID"
                )
                if native_tool_call_id in native_tool_calls:
                    raise ValueError("native tool call IDs must be unique when recorded")
                native_tool_calls.add(native_tool_call_id)
            require_text(item.get("design_note"), "candidate design note")
            require_text(item.get("registered_at"), "candidate registration timestamp")
            if item.get("provenance_assurance") != PROVENANCE_ASSURANCE:
                raise ValueError("candidate provenance assurance is missing or overstated")
            if item.get("provenance_status") != "repository_registered_operator_attested":
                raise ValueError("candidate provenance status is missing or overstated")
            require_text(item.get("provenance_operator"), "candidate provenance operator")
            if verify_files:
                path = verify_record(item, f"candidate {slot}", run_dir=run_dir)
                require_png(path, f"candidate {slot}")
        if slots != {item[0] for item in CANDIDATE_DIRECTIONS}:
            raise ValueError("candidate pool must expose fixed slots A through E")
        packet = state.get("selection_packet")
        if not isinstance(packet, Mapping) or packet.get("status") not in {
            "awaiting_operator_selection", "resolved"
        }:
            raise ValueError("selection packet is missing or malformed")
        if packet.get("candidates") != pool:
            raise ValueError("selection packet must expose all five registered candidates")

    selected = state.get("selected_candidate")
    selected_combination = state.get("selected_combination")
    selection_approval = state.get("candidate_selection_approval")
    selection_required = stage in {
        "CANDIDATE_APPROVED",
        "REGION_MAP_APPROVED",
        "DELIVERY_REGISTERED",
        "VISUAL_APPROVED",
        "FINAL_APPROVED",
    }
    if selection_required:
        selection_count = sum(
            isinstance(item, Mapping) for item in (selected, selected_combination)
        )
        if selection_count != 1 or not isinstance(selection_approval, Mapping):
            raise ValueError("candidate approval is required before this stage")
        approval_path = verify_record(
            selection_approval, "candidate selection approval", run_dir=run_dir
        ) if verify_files else run_dir / str(selection_approval.get("path", ""))
        if isinstance(selected, Mapping):
            registered = _candidate_map(state).get(selected.get("slot"))
            if registered is None or any(
                selected.get(key) != registered.get(key)
                for key in ("slot", "candidate_id", "sha256")
            ):
                raise ValueError("selected candidate does not match the registered pool")
            if verify_files:
                approval = read_json(approval_path, "candidate selection approval")
                approval_selected = approval.get("selected_candidate")
                if not isinstance(approval_selected, Mapping):
                    approval_selected = approval
                if approval.get("decision") != "APPROVE_IMAGEGEN_CANDIDATE" or any(
                    approval_selected.get(key) != selected.get(key)
                    for key in ("slot", "candidate_id", "sha256")
                ):
                    raise ValueError(
                        "candidate selection approval is not bound to the selected candidate"
                    )
            packet = state.get("selection_packet")
            if not isinstance(packet, Mapping) or packet.get("selected_slot") != selected.get("slot"):
                raise ValueError("selection packet is not bound to the selected candidate")
        else:
            assert isinstance(selected_combination, Mapping)
            expected_slots: dict[str, Any] = {}
            for source_key, label in (
                ("layout_source", "layout source"),
                ("visual_style_source", "visual style source"),
            ):
                source = selected_combination.get(source_key)
                if not isinstance(source, Mapping):
                    raise ValueError(f"selected combination is missing its {label}")
                registered = _candidate_map(state).get(source.get("slot"))
                if registered is None or any(
                    source.get(key) != registered.get(key)
                    for key in ("slot", "candidate_id", "sha256")
                ):
                    raise ValueError(f"selected combination {label} does not match the registered pool")
                expected_slots[source_key] = source.get("slot")
            require_text(selected_combination.get("operator"), "selection operator")
            packet = state.get("selection_packet")
            if not isinstance(packet, Mapping) or packet.get("selected_slots") != expected_slots:
                raise ValueError("selection packet is not bound to the selected combination")
            if verify_files:
                approval = read_json(approval_path, "candidate selection approval")
                approval_is_bound = approval.get("decision") == "APPROVE_IMAGEGEN_COMBINATION"
                for source_key in ("layout_source", "visual_style_source"):
                    approval_source = approval.get(source_key)
                    selected_source = selected_combination.get(source_key)
                    if not isinstance(approval_source, Mapping) or not isinstance(
                        selected_source, Mapping
                    ) or any(
                        approval_source.get(key) != selected_source.get(key)
                        for key in ("slot", "candidate_id", "sha256")
                    ):
                        approval_is_bound = False
                if not approval_is_bound:
                    raise ValueError(
                        "candidate selection approval is not bound to the selected combination"
                    )
    elif (
        selected is not None
        or selected_combination is not None
        or selection_approval is not None
    ):
        raise ValueError("candidate selection cannot exist before explicit approval")

    approved_region_map = state.get("approved_region_map")
    region_required = stage in {
        "REGION_MAP_APPROVED",
        "DELIVERY_REGISTERED",
        "VISUAL_APPROVED",
        "FINAL_APPROVED",
    }
    if region_required:
        if not isinstance(approved_region_map, Mapping):
            raise ValueError("approved region-map binding is required before this stage")
        case_id = require_text(approved_region_map.get("case_id"), "region-map case ID")
        delivery_revision = require_text(
            approved_region_map.get("delivery_revision"), "region-map delivery revision"
        )
        require_text(approved_region_map.get("recipe_id"), "region-map reconstruction recipe")
        map_record = approved_region_map.get("region_map")
        approval_record = approved_region_map.get("approval_record")
        if not isinstance(map_record, Mapping) or not isinstance(approval_record, Mapping):
            raise ValueError("region map and its explicit approval record are required")
        if verify_files:
            verify_record(map_record, "approved region map", run_dir=run_dir)
            approval_path = verify_record(
                approval_record, "region-map approval", run_dir=run_dir
            )
            approval = read_json(approval_path, "region-map approval")
            require_approval_metadata(
                approval,
                "region-map approval",
            )
            if (
                approval.get("decision") != "APPROVE_REGION_MAP_FOR_RECONSTRUCTION"
                or approval.get("case_id") != case_id
                or approval.get("delivery_revision") != delivery_revision
                or approval.get("region_map_sha256") != map_record.get("sha256")
                or approval.get("recipe_id") != approved_region_map.get("recipe_id")
                or approval.get("scientific_approval_created") is not False
            ):
                raise ValueError("region-map approval is not bound to the approved case inputs")
            selected_binding = approval.get("selected_candidate")
            if not isinstance(selected_binding, Mapping):
                raise ValueError("region-map approval is missing its selected candidate")
            expected_selection = selected if isinstance(selected, Mapping) else None
            if expected_selection is None or any(
                selected_binding.get(key) != expected_selection.get(key)
                for key in ("slot", "candidate_id", "sha256")
            ):
                raise ValueError("region-map approval does not match the selected candidate")
    elif approved_region_map is not None:
        raise ValueError("region map cannot be approved before candidate selection")

    delivery = state.get("delivery")
    delivery_required = stage in {"DELIVERY_REGISTERED", "VISUAL_APPROVED", "FINAL_APPROVED"}
    if delivery_required:
        if not isinstance(delivery, Mapping):
            raise ValueError("editable delivery binding is required before this stage")
        if delivery.get("validation_scope") != VALIDATION_SCOPE:
            raise ValueError("delivery validation scope is missing or overstated")
        if delivery.get("pdf_role") != PDF_ROLE:
            raise ValueError("PDF must be labeled as a preview/export")
        if delivery.get("case_id") != approved_region_map.get("case_id") or delivery.get(
            "delivery_revision"
        ) != approved_region_map.get("delivery_revision"):
            raise ValueError("delivery case or revision does not match the approved region map")
        for key in (
            "svg",
            "pptx",
            "drawio",
            "pdf_preview",
            "validation_report",
            "artifact_manifest",
        ):
            record = delivery.get(key)
            if not isinstance(record, Mapping):
                raise ValueError(f"delivery is missing {key}")
            if verify_files:
                verify_record(record, f"delivery {key}", run_dir=run_dir)
    elif delivery is not None:
        raise ValueError("delivery cannot be registered before candidate approval")

    visual_approval = state.get("visual_approval")
    if stage in {"VISUAL_APPROVED", "FINAL_APPROVED"}:
        if not isinstance(visual_approval, Mapping):
            raise ValueError("explicit visual approval is required before this stage")
        if verify_files:
            visual_path = verify_record(
                visual_approval, "visual delivery approval", run_dir=run_dir
            )
            visual = read_json(visual_path, "visual delivery approval")
            require_approval_metadata(visual, "visual approval")
            if (
                visual.get("decision") != "APPROVE_VISUAL_DELIVERY"
                or visual.get("case_id") != delivery.get("case_id")
                or visual.get("delivery_revision") != delivery.get("delivery_revision")
                or visual.get("artifact_manifest_sha256")
                != delivery["artifact_manifest"]["sha256"]
                or visual.get("scientific_approval_created") is not False
                or visual.get("science_day_use_approval_created") is not False
                or visual.get("public_release_approval_created") is not False
            ):
                raise ValueError("visual approval is not bound to the registered artifact manifest")
    elif visual_approval is not None:
        raise ValueError("visual approval may only follow a registered delivery")

    for pending_key in ("science_day_use_approval", "public_release_approval"):
        if state.get(pending_key) is not None:
            raise ValueError(f"{pending_key} is unsupported in v0.1 and must remain pending")

    final_approval = state.get("final_delivery_approval")
    if stage == "FINAL_APPROVED":
        if not isinstance(final_approval, Mapping):
            raise ValueError("final approval record is required for FINAL_APPROVED")
        if verify_files:
            final_path = verify_record(final_approval, "final delivery approval", run_dir=run_dir)
            approval = read_json(final_path, "final delivery approval")
            if approval.get("decision") != "APPROVE_FINAL_DELIVERY" or approval.get(
                "approval_type"
            ) != "scientific_approval":
                raise ValueError("final delivery approval has the wrong explicit decision")
            if approval.get("delivery_hashes") != {
                key: delivery[key]["sha256"]
                for key in (
                    "svg",
                    "pptx",
                    "drawio",
                    "pdf_preview",
                    "validation_report",
                    "artifact_manifest",
                )
            }:
                raise ValueError("final delivery approval is not bound to registered delivery hashes")
            if isinstance(selected_combination, Mapping) and approval.get(
                "selected_combination"
            ) != selected_combination:
                raise ValueError(
                    "final delivery approval is not bound to the selected combination"
                )
    elif final_approval is not None:
        raise ValueError("final approval may only exist after an explicit operator action")

    # Bind append-only event details to the state that each event created.  The
    # ledger is a local consistency record, not a cryptographically signed log,
    # but a stale event must never disagree with the currently bound evidence.
    if len(history) >= 2:
        registered_event = history[1]
        if not isinstance(registered_event, Mapping) or registered_event.get("slots") != [
            item[0] for item in CANDIDATE_DIRECTIONS
        ] or registered_event.get("provenance_assurance") != PROVENANCE_ASSURANCE:
            raise ValueError("candidate registration event does not match the registered pool")
    if selection_required:
        selection_event = history[2]
        if not isinstance(selection_event, Mapping):
            raise ValueError("candidate selection event is malformed")
        if isinstance(selected, Mapping):
            expected_selection_event = {
                "event": "candidate_explicitly_approved",
                "slot": selected.get("slot"),
                "candidate_id": selected.get("candidate_id"),
                "operator": selected.get("operator"),
            }
        else:
            assert isinstance(selected_combination, Mapping)
            expected_selection_event = {
                "event": "candidate_combination_explicitly_approved",
                "layout_slot": selected_combination["layout_source"].get("slot"),
                "layout_candidate_id": selected_combination["layout_source"].get(
                    "candidate_id"
                ),
                "visual_style_slot": selected_combination["visual_style_source"].get(
                    "slot"
                ),
                "visual_style_candidate_id": selected_combination[
                    "visual_style_source"
                ].get("candidate_id"),
                "operator": selected_combination.get("operator"),
            }
        if any(selection_event.get(key) != value for key, value in expected_selection_event.items()):
            raise ValueError("candidate selection event does not match the approved selection")
    if region_required:
        region_event = history[3]
        if not isinstance(region_event, Mapping) or any(
            region_event.get(key) != value
            for key, value in {
                "event": "region_map_explicitly_approved",
                "case_id": approved_region_map.get("case_id"),
                "delivery_revision": approved_region_map.get("delivery_revision"),
            }.items()
        ):
            raise ValueError("region-map event does not match the approved region map")
    if delivery_required:
        delivery_event = history[4]
        if not isinstance(delivery_event, Mapping) or any(
            delivery_event.get(key) != value
            for key, value in {
                "event": "editable_delivery_registered_after_structural_validation",
                "validation_scope": delivery.get("validation_scope"),
                "pdf_role": delivery.get("pdf_role"),
            }.items()
        ):
            raise ValueError("delivery event does not match the registered delivery")
    if stage in {"VISUAL_APPROVED", "FINAL_APPROVED"}:
        visual_event = history[5]
        if not isinstance(visual_event, Mapping) or any(
            visual_event.get(key) != value
            for key, value in {
                "event": "visual_delivery_explicitly_approved",
                "artifact_manifest_sha256": delivery["artifact_manifest"]["sha256"],
            }.items()
        ):
            raise ValueError("visual-approval event does not match the registered manifest")


def load_state(run_dir: str | Path) -> tuple[Path, dict[str, Any]]:
    resolved_run = Path(run_dir).expanduser().resolve()
    current = state_path(resolved_run)
    if not current.is_file():
        raise ValueError(f"run does not contain {STATE_FILENAME}: {resolved_run}")
    state = read_json(current, "ImageGen workflow state")
    revision = state.get("revision")
    if not isinstance(revision, int) or revision < 1:
        raise ValueError("state revision is missing or invalid")
    snapshot = state_history_path(resolved_run, revision)
    if not snapshot.is_file() or read_json(snapshot, "immutable state snapshot") != state:
        raise ValueError("current state does not match its immutable revision snapshot")
    assert_state_invariants(state, resolved_run, verify_files=True)
    stable_keys = ("schema_version", "workflow", "run_id", "created_at", "sketch", "clarification")
    historical_states: list[dict[str, Any]] = []
    for snapshot_revision in range(1, revision + 1):
        historical_path = state_history_path(resolved_run, snapshot_revision)
        if not historical_path.is_file():
            raise ValueError("append-only state history contains a missing revision")
        historical = read_json(historical_path, "immutable state snapshot")
        assert_state_invariants(historical, resolved_run, verify_files=True)
        if historical.get("revision") != snapshot_revision or historical.get(
            "history"
        ) != state["history"][:snapshot_revision]:
            raise ValueError("append-only state history prefix was modified")
        if any(historical.get(key) != state.get(key) for key in stable_keys):
            raise ValueError("append-only state history changed immutable run metadata")
        historical_states.append(historical)

    # Once evidence enters the ledger, later revisions may refer to it but may
    # not rewrite it.  Stage/revision/history/updated_at are intentionally not
    # included because they are the append-only transition envelope itself.
    introduced_fields = {
        2: ("candidate_pool",),
        3: (
            "selection_packet",
            "selected_candidate",
            "selected_combination",
            "candidate_selection_approval",
        ),
        4: ("approved_region_map",),
        5: ("delivery",),
        6: ("visual_approval",),
        7: ("final_delivery_approval",),
    }
    for introduced_revision, fields in introduced_fields.items():
        if revision < introduced_revision:
            continue
        introduced = historical_states[introduced_revision - 1]
        for later in historical_states[introduced_revision:]:
            if any(later.get(field) != introduced.get(field) for field in fields):
                raise ValueError(
                    "append-only state history rewrote evidence from an earlier revision"
                )
    return resolved_run, state


def initialize_run(
    run_dir: str | Path, sketch: str | Path, clarification_brief: str
) -> dict[str, Any]:
    resolved_run = Path(run_dir).expanduser().resolve()
    if resolved_run.exists():
        raise ValueError(f"refusing to overwrite existing run directory: {resolved_run}")
    sketch_path = require_existing_file(sketch, "source sketch")
    brief = require_text(clarification_brief, "clarification brief")
    resolved_run.mkdir(parents=True)
    sketch_suffix = sketch_path.suffix.lower()
    if re.fullmatch(r"\.[a-z0-9]{1,10}", sketch_suffix) is None:
        sketch_suffix = ".bin"
    imported_sketch = copy_artifact_into_run(
        sketch_path,
        resolved_run,
        f"ledger/inputs/source_sketch{sketch_suffix}",
        "source sketch",
    )
    now = utc_now()
    state: dict[str, Any] = {
        "schema_version": "1.1",
        "workflow": "codex_imagegen_artifact_ledger",
        "run_id": resolved_run.name,
        "revision": 1,
        "stage": "CLARIFICATION_COMPLETE",
        "created_at": now,
        "updated_at": now,
        "sketch": artifact_record(imported_sketch, relative_base=resolved_run),
        "clarification": {
            "brief": brief,
            "purpose": "human-readable rendering brief after focused clarification",
        },
        "candidate_pool": [],
        "selection_packet": None,
        "selected_candidate": None,
        "selected_combination": None,
        "candidate_selection_approval": None,
        "approved_region_map": None,
        "delivery": None,
        "visual_approval": None,
        "final_delivery_approval": None,
        "science_day_use_approval": None,
        "public_release_approval": None,
        "history": [{"at": now, "event": "clarification_recorded"}],
    }
    write_current_state(resolved_run, state, initialize=True)
    return state


def register_candidates(
    run_dir: str | Path,
    candidate_paths: Sequence[str | Path],
    generation_event_ids: Sequence[str],
    operator: str,
    native_tool_call_ids: Sequence[str | None] | None = None,
) -> dict[str, Any]:
    resolved_run, state = load_state(run_dir)
    if state["stage"] != "CLARIFICATION_COMPLETE":
        raise ValueError("candidates can only be registered immediately after clarification")
    if len(candidate_paths) != 5:
        raise ValueError("exactly five PNG candidates are required")
    if len(generation_event_ids) != 5:
        raise ValueError("exactly five generation event IDs are required")
    provenance_operator = require_text(operator, "candidate provenance operator")
    events = [require_text(item, "generation event ID") for item in generation_event_ids]
    if len(set(events)) != 5:
        raise ValueError("five unique generation event IDs are required")
    native_ids = list(native_tool_call_ids or [None] * 5)
    if len(native_ids) != 5:
        raise ValueError("native tool call IDs must contain five optional entries")
    normalized_native_ids = [
        require_text(item, "native tool call ID") if item is not None else None
        for item in native_ids
    ]
    recorded_native_ids = [item for item in normalized_native_ids if item is not None]
    if len(recorded_native_ids) != len(set(recorded_native_ids)):
        raise ValueError("native tool call IDs must be unique when recorded")
    paths = [
        require_png(path, f"candidate {slot}")
        for (slot, _, _), path in zip(CANDIDATE_DIRECTIONS, candidate_paths)
    ]
    if len({str(path) for path in paths}) != 5:
        raise ValueError("five distinct PNG candidate files are required")

    imported_paths = [
        copy_artifact_into_run(
            path,
            resolved_run,
            f"ledger/candidates/{slot}.png",
            f"candidate {slot}",
        )
        for (slot, _, _), path in zip(CANDIDATE_DIRECTIONS, paths)
    ]

    pool: list[dict[str, str]] = []
    registered_at = utc_now()
    for (slot, candidate_id, direction), path, event_id, native_tool_call_id in zip(
        CANDIDATE_DIRECTIONS,
        imported_paths,
        events,
        normalized_native_ids,
        strict=True,
    ):
        record = {
            "slot": slot,
            "candidate_id": candidate_id,
            "direction": direction,
            **artifact_record(path, relative_base=resolved_run),
            "generation_event_id": event_id,
            "design_note": DESIGN_NOTES[slot],
            "registered_at": registered_at,
            "provenance_operator": provenance_operator,
            "provenance_assurance": PROVENANCE_ASSURANCE,
            "provenance_status": "repository_registered_operator_attested",
            "generator_context": (
                "Codex built-in ImageGen artifact from a separate generation call; "
                "operator attested"
            ),
        }
        if native_tool_call_id is not None:
            record["native_tool_call_id"] = native_tool_call_id
        pool.append(record)
    state["candidate_pool"] = pool
    state["selection_packet"] = {
        "status": "awaiting_operator_selection",
        "instructions": (
            "Select one exact hash-bound candidate. If a mixed layout/style direction is "
            "needed, create a new append-only proposal run that renders the combination "
            "into one A-E slot before approval."
        ),
        "candidates": deepcopy(pool),
    }
    state["stage"] = "CANDIDATES_REGISTERED"
    return advance_state(
        resolved_run,
        state,
        "five_candidates_registered",
        slots=[item["slot"] for item in pool],
        provenance_assurance=PROVENANCE_ASSURANCE,
    )


def select_candidate(
    run_dir: str | Path,
    slot: str,
    candidate_id: str,
    candidate_sha256: str,
    operator: str,
) -> dict[str, Any]:
    resolved_run, state = load_state(run_dir)
    if state["stage"] != "CANDIDATES_REGISTERED":
        raise ValueError("candidate selection requires a complete five-candidate pool")
    selected_slot = require_text(slot, "candidate slot").upper()
    selected_id = require_text(candidate_id, "candidate ID")
    selected_hash = require_text(candidate_sha256, "candidate SHA-256").lower()
    if SHA256_PATTERN.fullmatch(selected_hash) is None:
        raise ValueError("candidate SHA-256 must be a lowercase 64-character digest")
    selected_operator = require_text(operator, "selection operator")
    registered = _candidate_map(state).get(selected_slot)
    if registered is None:
        raise ValueError(f"candidate slot is not registered: {selected_slot}")
    if registered["candidate_id"] != selected_id:
        raise ValueError("candidate ID does not match the exact registered slot")
    if registered["sha256"] != selected_hash:
        raise ValueError("candidate SHA-256 does not match the registered artifact")

    approval_path = resolved_run / CANDIDATE_APPROVAL_PATH
    approval = {
        "schema_version": "1.1",
        "decision": "APPROVE_IMAGEGEN_CANDIDATE",
        "operator": selected_operator,
        "approved_at": utc_now(),
        "slot": selected_slot,
        "candidate_id": selected_id,
        "sha256": selected_hash,
        "generation_event_id": registered["generation_event_id"],
        "provenance_assurance": registered["provenance_assurance"],
    }
    if registered.get("native_tool_call_id") is not None:
        approval["native_tool_call_id"] = registered["native_tool_call_id"]
    write_json_exclusive(approval_path, approval)
    state["selected_candidate"] = {
        "slot": selected_slot,
        "candidate_id": selected_id,
        "sha256": selected_hash,
        "operator": selected_operator,
    }
    state["selected_combination"] = None
    state["candidate_selection_approval"] = artifact_record(
        approval_path, relative_base=resolved_run
    )
    state["selection_packet"]["status"] = "resolved"
    state["selection_packet"]["selected_slot"] = selected_slot
    state["stage"] = "CANDIDATE_APPROVED"
    return advance_state(
        resolved_run,
        state,
        "candidate_explicitly_approved",
        slot=selected_slot,
        candidate_id=selected_id,
        operator=selected_operator,
    )


def register_candidate_selection_approval(
    run_dir: str | Path, approval_record: str | Path
) -> dict[str, Any]:
    """Import a frozen explicit selection record without creating new approval evidence."""
    resolved_run, state = load_state(run_dir)
    if state["stage"] != "CANDIDATES_REGISTERED":
        raise ValueError("candidate selection requires a complete five-candidate pool")
    source = require_existing_file(approval_record, "candidate selection approval record")
    approval = read_json(source, "candidate selection approval record")
    selected = approval.get("selected_candidate")
    if (
        approval.get("decision") != "APPROVE_IMAGEGEN_CANDIDATE"
        or approval.get("status") != "approved_for_editable_reconstruction"
        or approval.get("editable_reconstruction_authorized") is not True
        or approval.get("final_scientific_approval") is not None
        or not isinstance(selected, Mapping)
    ):
        raise ValueError("candidate selection record is not an explicit reconstruction approval")
    slot = require_text(selected.get("slot"), "candidate slot").upper()
    registered = _candidate_map(state).get(slot)
    if registered is None or any(
        selected.get(key) != registered.get(key)
        for key in ("slot", "candidate_id", "sha256")
    ):
        raise ValueError("candidate selection record does not match the registered pool")
    imported = copy_artifact_into_run(
        source,
        resolved_run,
        CANDIDATE_APPROVAL_PATH,
        "candidate selection approval record",
    )
    raw_operator = approval.get("operator") or approval.get("approved_by")
    operator = (
        require_text(raw_operator, "imported selection operator")
        if raw_operator is not None
        else "unknown_not_recorded_in_frozen_selection"
    )
    state["selected_candidate"] = {
        "slot": slot,
        "candidate_id": registered["candidate_id"],
        "sha256": registered["sha256"],
        "operator": operator,
    }
    state["selected_combination"] = None
    state["candidate_selection_approval"] = artifact_record(
        imported, relative_base=resolved_run
    )
    state["selection_packet"]["status"] = "resolved"
    state["selection_packet"]["selected_slot"] = slot
    state["stage"] = "CANDIDATE_APPROVED"
    return advance_state(
        resolved_run,
        state,
        "candidate_explicitly_approved",
        slot=slot,
        candidate_id=registered["candidate_id"],
        operator=operator,
        imported_frozen_record=True,
    )


def select_combination(
    run_dir: str | Path,
    layout_slot: str,
    layout_candidate_id: str,
    layout_sha256: str,
    visual_style_slot: str,
    visual_style_candidate_id: str,
    visual_style_sha256: str,
    operator: str,
) -> dict[str, Any]:
    """Reject mixed-source approval; v0.1 reconstructs one exact candidate only."""
    _, state = load_state(run_dir)
    if state["stage"] != "CANDIDATES_REGISTERED":
        raise ValueError("combination selection requires a complete five-candidate pool")
    del (
        layout_slot,
        layout_candidate_id,
        layout_sha256,
        visual_style_slot,
        visual_style_candidate_id,
        visual_style_sha256,
        operator,
    )
    raise ValueError(COMBINATION_REQUIRES_NEW_RUN)


def _delivery_record(run_dir: Path, path: str | Path, label: str, extensions: set[str]) -> dict[str, str]:
    artifact = require_inside_run(run_dir, path, label)
    if artifact.suffix.lower() not in extensions:
        expected = ", ".join(sorted(extensions))
        raise ValueError(f"{label} must use one of these extensions: {expected}")
    return artifact_record(artifact, relative_base=run_dir)


def register_region_map_approval(
    run_dir: str | Path,
    *,
    region_map: str | Path,
    approval_record: str | Path,
) -> dict[str, Any]:
    """Import an explicit, hash-bound region-map approval after candidate selection."""
    resolved_run, state = load_state(run_dir)
    if state["stage"] != "CANDIDATE_APPROVED":
        raise ValueError("region-map approval requires an explicitly approved candidate")
    if not isinstance(state.get("selected_candidate"), Mapping):
        raise ValueError(COMBINATION_REQUIRES_NEW_RUN)
    source_map = require_existing_file(region_map, "approved region map")
    source_approval = require_existing_file(approval_record, "region-map approval record")
    approval = read_json(source_approval, "region-map approval record")
    operator, approved_at, provenance = require_approval_metadata(
        approval,
        "region-map approval",
    )
    selected = state["selected_candidate"]
    selected_binding = approval.get("selected_candidate")
    if approval.get("decision") != "APPROVE_REGION_MAP_FOR_RECONSTRUCTION":
        raise ValueError("region-map record must contain the explicit approval decision")
    if not isinstance(selected_binding, Mapping) or any(
        selected_binding.get(key) != selected.get(key)
        for key in ("slot", "candidate_id", "sha256")
    ):
        raise ValueError("region-map approval does not match the selected candidate")
    if approval.get("region_map_sha256") != sha256_file(source_map):
        raise ValueError("region-map approval SHA-256 does not match the supplied map")
    if approval.get("scientific_approval_created") is not False:
        raise ValueError("region-map approval must not create scientific approval")
    case_id = require_text(approval.get("case_id"), "region-map case ID")
    delivery_revision = require_text(
        approval.get("delivery_revision"), "region-map delivery revision"
    )
    recipe_id = require_text(approval.get("recipe_id"), "region-map reconstruction recipe")

    imported_map = copy_artifact_into_run(
        source_map, resolved_run, REGION_MAP_PATH, "approved region map"
    )
    imported_approval = copy_artifact_into_run(
        source_approval,
        resolved_run,
        REGION_MAP_APPROVAL_PATH,
        "region-map approval record",
    )
    state["approved_region_map"] = {
        "case_id": case_id,
        "delivery_revision": delivery_revision,
        "recipe_id": recipe_id,
        "region_map": artifact_record(imported_map, relative_base=resolved_run),
        "approval_record": artifact_record(imported_approval, relative_base=resolved_run),
    }
    state["stage"] = "REGION_MAP_APPROVED"
    return advance_state(
        resolved_run,
        state,
        "region_map_explicitly_approved",
        case_id=case_id,
        delivery_revision=delivery_revision,
        operator=operator,
        approved_at=approved_at,
        provenance=provenance,
    )


def _require_hash_mapping(
    value: Any,
    label: str,
    keys: Sequence[str],
    optional_keys: Sequence[str] = (),
) -> dict[str, str]:
    required = set(keys)
    allowed = required | set(optional_keys)
    if (
        not isinstance(value, Mapping)
        or not required.issubset(value)
        or not set(value).issubset(allowed)
    ):
        suffix = (
            f"; optional: {', '.join(optional_keys)}" if optional_keys else ""
        )
        raise ValueError(
            f"{label} must contain: {', '.join(keys)}{suffix}"
        )
    result: dict[str, str] = {}
    for key in value:
        digest = value.get(key)
        if not isinstance(digest, str) or SHA256_PATTERN.fullmatch(digest) is None:
            raise ValueError(f"{label} contains an invalid SHA-256 for {key}")
        result[key] = digest
    return result


def _verify_strong_delivery_evidence(
    run_dir: Path,
    state: Mapping[str, Any],
    records: Mapping[str, Mapping[str, str]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    validation_path = verify_record(
        records["validation_report"], "structural validation report", run_dir=run_dir
    )
    manifest_path = verify_record(
        records["artifact_manifest"], "artifact manifest", run_dir=run_dir
    )
    report = read_json(validation_path, "structural validation report")
    manifest = read_json(manifest_path, "artifact manifest")
    region = state.get("approved_region_map")
    selected = state.get("selected_candidate")
    selection_record = state.get("candidate_selection_approval")
    if not isinstance(region, Mapping) or not isinstance(selected, Mapping) or not isinstance(
        selection_record, Mapping
    ):
        raise ValueError("delivery evidence is missing approved input bindings")
    if (
        report.get("schema_version") != "1.0"
        or report.get("report_type") != "structural_delivery_validation"
        or report.get("status") != "PASSED"
        or report.get("overall_pass") is not True
        or report.get("scientific_correctness_checked") is not False
    ):
        raise ValueError("structural validation report is missing an explicit passing result")
    if report.get("case_id") != region.get("case_id") or report.get(
        "delivery_revision"
    ) != region.get("delivery_revision"):
        raise ValueError("validation report belongs to another case or delivery revision")
    validator = report.get("validator")
    if not isinstance(validator, Mapping):
        raise ValueError("validation report is missing validator identity")
    for key in ("name", "version", "code_sha256"):
        require_text(validator.get(key), f"validator {key}")
    if SHA256_PATTERN.fullmatch(str(validator.get("code_sha256"))) is None:
        raise ValueError("validator code_sha256 is invalid")
    checks = report.get("checks")
    if not isinstance(checks, Mapping) or not checks:
        raise ValueError("structural validation report contains an empty check set")
    for check_name, result in checks.items():
        if not isinstance(result, Mapping) or result.get("passed") is not True:
            raise ValueError(
                f"structural validation report contains a non-passing check: {check_name}"
            )
    input_hashes = _require_hash_mapping(
        report.get("input_hashes"),
        "validation input hashes",
        ("candidate_sha256", "candidate_selection_sha256", "region_map_sha256"),
        (
            "approved_raster_manifest_sha256",
            "raster_atom_review_decision_sha256",
        ),
    )
    expected_inputs = {
        "candidate_sha256": str(selected.get("sha256")),
        "candidate_selection_sha256": str(selection_record.get("sha256")),
        "region_map_sha256": str(region["region_map"].get("sha256")),
    }
    if any(input_hashes.get(key) != value for key, value in expected_inputs.items()):
        raise ValueError("validation report input hashes do not match approved inputs")
    optional_input_bindings = {
        "approved_raster_manifest_sha256": "approved_raster_atoms",
        "raster_atom_review_decision_sha256": "raster_atom_review_decision",
    }
    for input_key, manifest_key in optional_input_bindings.items():
        if input_key not in input_hashes:
            continue
        binding = manifest.get(manifest_key)
        if not isinstance(binding, Mapping):
            raise ValueError(
                f"artifact manifest is missing the optional {manifest_key} input binding"
            )
        verify_record(binding, f"artifact manifest {manifest_key}", run_dir=run_dir)
        if binding.get("sha256") != input_hashes[input_key]:
            raise ValueError(
                f"validation report {input_key} does not match the artifact manifest"
            )
    output_keys = ("svg", "pptx", "drawio", "pdf_preview")
    output_hashes = _require_hash_mapping(
        report.get("output_hashes"), "validation output hashes", output_keys
    )
    actual_outputs = {key: str(records[key].get("sha256")) for key in output_keys}
    if output_hashes != actual_outputs:
        raise ValueError("validation report output hashes do not match registered artifacts")

    if (
        manifest.get("schema_version") != "1.0"
        or manifest.get("manifest_type") != "editable_delivery_artifact_manifest"
        or manifest.get("case_id") != region.get("case_id")
        or manifest.get("delivery_revision") != region.get("delivery_revision")
        or manifest.get("scientific_correctness_checked") is not False
    ):
        raise ValueError(
            "artifact manifest has the wrong case, revision, or scientific-check boundary"
        )
    validation_binding = manifest.get("validation_report")
    if not isinstance(validation_binding, Mapping) or any(
        validation_binding.get(key) != records["validation_report"].get(key)
        for key in ("path", "sha256")
    ):
        raise ValueError("artifact manifest is not bound to the consumed validation report")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, Mapping) or set(artifacts) != set(output_keys):
        raise ValueError("artifact manifest must describe exactly the four delivery outputs")

    raster_binding_keys = (
        "approved_raster_atoms",
        "raster_atom_review_decision",
    )
    raster_input_keys = (
        "approved_raster_manifest_sha256",
        "raster_atom_review_decision_sha256",
    )
    present_bindings = {
        key for key in raster_binding_keys if isinstance(manifest.get(key), Mapping)
    }
    present_inputs = {key for key in raster_input_keys if key in input_hashes}
    if present_bindings not in (set(), set(raster_binding_keys)) or present_inputs not in (
        set(),
        set(raster_input_keys),
    ) or bool(present_bindings) != bool(present_inputs):
        raise ValueError(
            "raster authorization requires both manifest bindings and both validation input hashes"
        )

    expected_sidecars: dict[str, set[tuple[str, str]]] = {
        key: set() for key in output_keys
    }
    if present_bindings:
        asset_binding = manifest["approved_raster_atoms"]
        decision_binding = manifest["raster_atom_review_decision"]
        assert isinstance(asset_binding, Mapping) and isinstance(decision_binding, Mapping)
        asset_manifest_path = verify_record(
            asset_binding, "artifact manifest approved raster atoms", run_dir=run_dir
        )
        verify_record(
            decision_binding,
            "artifact manifest raster atom review decision",
            run_dir=run_dir,
        )
        asset_manifest = read_json(asset_manifest_path, "approved raster manifest")
        assets = asset_manifest.get("assets")
        if not isinstance(assets, list):
            raise ValueError("approved raster manifest assets must be an array")
        asset_binding_path = require_portable_relative_path(
            str(asset_binding.get("path")), "approved raster manifest"
        )
        source_parent = asset_binding_path.rsplit("/", 1)[0] if "/" in asset_binding_path else ""
        for index, raw_asset in enumerate(assets):
            if not isinstance(raw_asset, Mapping):
                raise ValueError(f"approved raster asset {index} must be an object")
            source_name = require_portable_relative_path(
                str(raw_asset.get("path")), f"approved raster asset {index}"
            )
            svg_name = require_portable_relative_path(
                str(raw_asset.get("delivery_svg_path")),
                f"approved raster asset {index} SVG delivery",
            )
            digest = raw_asset.get("sha256")
            if not isinstance(digest, str) or SHA256_PATTERN.fullmatch(digest) is None:
                raise ValueError(f"approved raster asset {index} has an invalid SHA-256")
            source_name = f"{source_parent}/{source_name}" if source_parent else source_name
            for name, label in ((source_name, "source"), (svg_name, "SVG delivery")):
                verify_record(
                    {"path": name, "sha256": digest},
                    f"approved raster asset {index} {label}",
                    run_dir=run_dir,
                )
            expected_sidecars["svg"].add((svg_name, digest))
            expected_sidecars["pptx"].add((source_name, digest))
            expected_sidecars["drawio"].add((source_name, digest))

    for key in output_keys:
        item = artifacts.get(key)
        if not isinstance(item, Mapping):
            raise ValueError(f"artifact manifest entry is missing for {key}")
        if item.get("sha256") != records[key].get("sha256") or item.get(
            "path"
        ) != records[key].get("path"):
            raise ValueError(f"artifact manifest does not match registered {key}")
        require_text(item.get("media_type"), f"{key} media type")
        require_text(item.get("editability"), f"{key} editability classification")
        require_text(item.get("structural_summary"), f"{key} structural summary")
        sidecars = item.get("approved_raster_sidecars")
        if not isinstance(sidecars, list):
            raise ValueError(f"artifact manifest {key} approved_raster_sidecars must be an array")
        observed_sidecars: list[tuple[str, str]] = []
        for index, sidecar in enumerate(sidecars):
            if not isinstance(sidecar, Mapping):
                raise ValueError(f"artifact manifest {key} raster sidecar {index} is invalid")
            verify_record(
                sidecar,
                f"artifact manifest {key} raster sidecar {index}",
                run_dir=run_dir,
            )
            observed_sidecars.append((str(sidecar.get("path")), str(sidecar.get("sha256"))))
        if len(observed_sidecars) != len(set(observed_sidecars)) or set(
            observed_sidecars
        ) != expected_sidecars[key]:
            raise ValueError(
                f"artifact manifest {key} raster sidecars do not exactly match "
                "the approved raster manifest"
            )
    return report, manifest


def register_delivery(
    run_dir: str | Path,
    *,
    svg: str | Path,
    pptx: str | Path,
    drawio: str | Path,
    pdf_preview: str | Path,
    validation_report: str | Path,
    artifact_manifest: str | Path,
) -> dict[str, Any]:
    resolved_run, state = load_state(run_dir)
    if state["stage"] != "REGION_MAP_APPROVED":
        raise ValueError(
            "editable delivery is blocked until candidate and region-map approvals are recorded"
        )
    region = state["approved_region_map"]
    delivery = {
        "registered_at": utc_now(),
        "case_id": region["case_id"],
        "delivery_revision": region["delivery_revision"],
        "validation_scope": VALIDATION_SCOPE,
        "scientific_correctness_checked": False,
        "pdf_role": PDF_ROLE,
        "svg": _delivery_record(resolved_run, svg, "editable SVG", {".svg"}),
        "pptx": _delivery_record(resolved_run, pptx, "editable PPTX", {".pptx"}),
        "drawio": _delivery_record(resolved_run, drawio, "editable draw.io", {".drawio"}),
        "pdf_preview": _delivery_record(resolved_run, pdf_preview, "PDF preview/export", {".pdf"}),
        "validation_report": _delivery_record(
            resolved_run, validation_report, "validation report", {".json"}
        ),
        "artifact_manifest": _delivery_record(
            resolved_run, artifact_manifest, "artifact manifest", {".json"}
        ),
    }
    _verify_strong_delivery_evidence(resolved_run, state, delivery)
    state["delivery"] = delivery
    state["stage"] = "DELIVERY_REGISTERED"
    return advance_state(
        resolved_run,
        state,
        "editable_delivery_registered_after_structural_validation",
        validation_scope=VALIDATION_SCOPE,
        pdf_role=PDF_ROLE,
    )


def register_visual_approval(
    run_dir: str | Path, approval_record: str | Path
) -> dict[str, Any]:
    """Import explicit visual approval without inferring scientific or release approval."""
    resolved_run, state = load_state(run_dir)
    if state["stage"] != "DELIVERY_REGISTERED":
        raise ValueError("visual approval requires a structurally registered delivery")
    source = require_existing_file(approval_record, "visual approval record")
    approval = read_json(source, "visual approval record")
    operator, approved_at, provenance = require_approval_metadata(
        approval, "visual approval"
    )
    delivery = state["delivery"]
    if (
        approval.get("decision") != "APPROVE_VISUAL_DELIVERY"
        or approval.get("case_id") != delivery.get("case_id")
        or approval.get("delivery_revision") != delivery.get("delivery_revision")
        or approval.get("artifact_manifest_sha256")
        != delivery["artifact_manifest"]["sha256"]
        or approval.get("scientific_approval_created") is not False
        or approval.get("science_day_use_approval_created") is not False
        or approval.get("public_release_approval_created") is not False
    ):
        raise ValueError("visual approval is not bound to this exact artifact manifest")
    imported = copy_artifact_into_run(
        source, resolved_run, VISUAL_APPROVAL_PATH, "visual approval record"
    )
    state["visual_approval"] = artifact_record(imported, relative_base=resolved_run)
    state["stage"] = "VISUAL_APPROVED"
    return advance_state(
        resolved_run,
        state,
        "visual_delivery_explicitly_approved",
        operator=operator,
        approved_at=approved_at,
        provenance=provenance,
        artifact_manifest_sha256=approval.get("artifact_manifest_sha256"),
    )


def approve_final_delivery(
    run_dir: str | Path, operator: str, approval_note: str
) -> dict[str, Any]:
    resolved_run, state = load_state(run_dir)
    if state["stage"] != "VISUAL_APPROVED":
        raise ValueError(
            "final scientific approval requires registered structural evidence and visual approval"
        )
    final_operator = require_text(operator, "final approval operator")
    note = require_text(approval_note, "final approval note")
    delivery = state["delivery"]
    delivery_hashes = {
        key: delivery[key]["sha256"]
        for key in (
            "svg",
            "pptx",
            "drawio",
            "pdf_preview",
            "validation_report",
            "artifact_manifest",
        )
    }
    approval_path = resolved_run / FINAL_APPROVAL_PATH
    approval = {
        "schema_version": "1.1",
        "decision": "APPROVE_FINAL_DELIVERY",
        "approval_type": "scientific_approval",
        "operator": final_operator,
        "approval_note": note,
        "approved_at": utc_now(),
        "selected_candidate": deepcopy(state["selected_candidate"]),
        "selected_combination": deepcopy(state.get("selected_combination")),
        "delivery_hashes": delivery_hashes,
        "automated_validation_created_this_approval": False,
        "scientific_acceptance_is_human_decision": True,
    }
    write_json_exclusive(approval_path, approval)
    state["final_delivery_approval"] = artifact_record(
        approval_path, relative_base=resolved_run
    )
    state["stage"] = "FINAL_APPROVED"
    return advance_state(
        resolved_run,
        state,
        "final_delivery_explicitly_approved",
        operator=final_operator,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Record a Codex ImageGen-first workflow locally. This command does not invoke "
            "ImageGen or any remote API."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    initialize = subparsers.add_parser("init", help="Create a run and record the clarified rendering brief")
    initialize.add_argument("--run-dir", type=Path, required=True)
    initialize.add_argument("--sketch", type=Path, required=True)
    initialize.add_argument("--clarification-brief", required=True)

    candidates = subparsers.add_parser(
        "register-candidates", help="Register the fixed A-E pool of exactly five PNGs"
    )
    candidates.add_argument("--run-dir", type=Path, required=True)
    candidates.add_argument("--operator", required=True, help="Operator attesting artifact provenance")
    for slot, _, direction in CANDIDATE_DIRECTIONS:
        lower = slot.lower()
        candidates.add_argument(f"--{lower}-png", type=Path, required=True, help=f"Slot {slot}: {direction}")
        candidates.add_argument(f"--{lower}-generation-event-id", required=True)
        candidates.add_argument(
            f"--{lower}-native-tool-call-id",
            help="Optional native tool-call ID; omit when the Codex tool did not expose one",
        )

    select = subparsers.add_parser("select-candidate", help="Explicitly approve one exact candidate")
    select.add_argument("--run-dir", type=Path, required=True)
    select.add_argument("--slot", choices=[item[0] for item in CANDIDATE_DIRECTIONS], required=True)
    select.add_argument("--candidate-id", required=True)
    select.add_argument("--sha256", required=True)
    select.add_argument("--operator", required=True)

    imported_selection = subparsers.add_parser(
        "register-selection",
        help="Import a frozen explicit candidate-selection approval record",
    )
    imported_selection.add_argument("--run-dir", type=Path, required=True)
    imported_selection.add_argument("--approval-record", type=Path, required=True)

    combination = subparsers.add_parser(
        "select-combination",
        help=(
            "Reject mixed-source approval in v0.1 and direct the operator to a new "
            "append-only proposal run"
        ),
    )
    combination.add_argument("--run-dir", type=Path, required=True)
    combination.add_argument(
        "--layout-slot", choices=[item[0] for item in CANDIDATE_DIRECTIONS], required=True
    )
    combination.add_argument("--layout-candidate-id", required=True)
    combination.add_argument("--layout-sha256", required=True)
    combination.add_argument(
        "--visual-style-slot",
        choices=[item[0] for item in CANDIDATE_DIRECTIONS],
        required=True,
    )
    combination.add_argument("--visual-style-candidate-id", required=True)
    combination.add_argument("--visual-style-sha256", required=True)
    combination.add_argument("--operator", required=True)

    region = subparsers.add_parser(
        "register-region-map",
        help="Register an explicit case/revision-bound region-map approval",
    )
    region.add_argument("--run-dir", type=Path, required=True)
    region.add_argument("--region-map", type=Path, required=True)
    region.add_argument("--approval-record", type=Path, required=True)

    delivery = subparsers.add_parser(
        "register-delivery",
        help="Bind editable outputs after passing structural validation and manifest checks",
    )
    delivery.add_argument("--run-dir", type=Path, required=True)
    delivery.add_argument("--svg", type=Path, required=True)
    delivery.add_argument("--pptx", type=Path, required=True)
    delivery.add_argument("--drawio", type=Path, required=True)
    delivery.add_argument("--pdf-preview", type=Path, required=True)
    delivery.add_argument("--validation-report", type=Path, required=True)
    delivery.add_argument("--artifact-manifest", type=Path, required=True)

    visual = subparsers.add_parser(
        "approve-visual",
        help="Register explicit hash-bound visual approval without scientific/release approval",
    )
    visual.add_argument("--run-dir", type=Path, required=True)
    visual.add_argument("--approval-record", type=Path, required=True)

    approve = subparsers.add_parser(
        "approve-delivery", help="Record the operator's separate final scientific approval"
    )
    approve.add_argument("--run-dir", type=Path, required=True)
    approve.add_argument("--operator", required=True)
    approve.add_argument("--approval-note", required=True)

    show = subparsers.add_parser("show", help="Verify and print the current ledger state")
    show.add_argument("--run-dir", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "init":
        state = initialize_run(args.run_dir, args.sketch, args.clarification_brief)
    elif args.command == "register-candidates":
        paths = [getattr(args, f"{slot.lower()}_png") for slot, _, _ in CANDIDATE_DIRECTIONS]
        event_ids = [
            getattr(args, f"{slot.lower()}_generation_event_id")
            for slot, _, _ in CANDIDATE_DIRECTIONS
        ]
        native_ids = [
            getattr(args, f"{slot.lower()}_native_tool_call_id")
            for slot, _, _ in CANDIDATE_DIRECTIONS
        ]
        state = register_candidates(
            args.run_dir,
            paths,
            event_ids,
            args.operator,
            native_tool_call_ids=native_ids,
        )
    elif args.command == "select-candidate":
        state = select_candidate(
            args.run_dir, args.slot, args.candidate_id, args.sha256, args.operator
        )
    elif args.command == "register-selection":
        state = register_candidate_selection_approval(
            args.run_dir, args.approval_record
        )
    elif args.command == "select-combination":
        state = select_combination(
            args.run_dir,
            args.layout_slot,
            args.layout_candidate_id,
            args.layout_sha256,
            args.visual_style_slot,
            args.visual_style_candidate_id,
            args.visual_style_sha256,
            args.operator,
        )
    elif args.command == "register-region-map":
        state = register_region_map_approval(
            args.run_dir,
            region_map=args.region_map,
            approval_record=args.approval_record,
        )
    elif args.command == "register-delivery":
        state = register_delivery(
            args.run_dir,
            svg=args.svg,
            pptx=args.pptx,
            drawio=args.drawio,
            pdf_preview=args.pdf_preview,
            validation_report=args.validation_report,
            artifact_manifest=args.artifact_manifest,
        )
    elif args.command == "approve-visual":
        state = register_visual_approval(args.run_dir, args.approval_record)
    elif args.command == "approve-delivery":
        state = approve_final_delivery(args.run_dir, args.operator, args.approval_note)
    else:
        _, state = load_state(args.run_dir)
    print(json.dumps(state, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(
            json.dumps(
                {"status": "FAILED", "error": str(exc)},
                sort_keys=True,
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        raise SystemExit(2) from None
