#!/usr/bin/env python3
"""Replay the public synthetic example without AI, network, or credentials.

This command is deliberately separate from live sketch interpretation.  Gate 1
and Gate 2 consume checked-in deterministic fixture pre-approval records.  A
VERIFIED structural report can only move a full run to ``awaiting_gate_3``;
``--approve-final`` is the separate researcher/operator action that creates the
final scientific-acceptance record.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Any, Mapping, Sequence

# A normal CLI invocation must not leave Python cache files in the source tree.
sys.dont_write_bytecode = True

from build_fixture_semantic_source import build as build_semantic_source
from export_drawio import export as export_drawio
from export_pdf import export as export_pdf
from export_pptx import export as export_pptx
from export_svg import export as export_svg
from render_equations import render_manifest
from render_topology_skeleton import render as render_topology_skeleton
from validate_delivery import validate as validate_delivery
from workflow_v3 import semantic_integrity_errors


SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parent
EXAMPLE_ROOT = REPOSITORY_ROOT / "examples" / "synthetic_restoration"
DEMO_FIXTURE_ROOT = EXAMPLE_ROOT / "demo"

DEFAULT_GATE_1 = DEMO_FIXTURE_ROOT / "gate_1_preapproval.json"
DEFAULT_GATE_2 = DEMO_FIXTURE_ROOT / "gate_2_preapproval.json"
INTERPRETATION_SOURCE = DEMO_FIXTURE_ROOT / "reviewed_interpretation.json"

PUBLIC_INPUTS = {
    "synthetic_demo_sketch": EXAMPLE_ROOT / "sketch.svg",
    "scientific_truth": EXAMPLE_ROOT / "truth" / "scientific_truth.json",
    "topology_blueprint": EXAMPLE_ROOT / "blueprints" / "synthetic_restoration.json",
    "reviewed_semantic_svg": EXAMPLE_ROOT / "editable_figure.svg",
    "semantic_validation_spec": EXAMPLE_ROOT / "validation_spec.json",
}

INPUT_DESTINATIONS = {
    "synthetic_demo_sketch": Path("input/synthetic_demo_sketch.svg"),
    "scientific_truth": Path("input/scientific_truth.json"),
    "topology_blueprint": Path("input/topology_blueprint.json"),
    "reviewed_semantic_svg": Path("input/reviewed_semantic_fixture.svg"),
    "semantic_validation_spec": Path("input/semantic_validation_spec.json"),
}

SKELETON_FILES = {
    "scene_sha256": Path("skeleton/synthetic_restoration_skeleton.scene.json"),
    "svg_sha256": Path("skeleton/synthetic_restoration_skeleton.svg"),
    "png_sha256": Path("skeleton/synthetic_restoration_skeleton.png"),
}

FULL_DELIVERY_FILES = (
    Path("source/semantic_figure.json"),
    Path("source/equations.tex"),
    Path("delivery/svg/master.svg"),
    Path("delivery/figma/figure_figma.svg"),
    Path("delivery/pptx/figure.pptx"),
    Path("delivery/drawio/figure.drawio"),
    Path("delivery/drawio/figure_drawio_preview.pdf"),
    Path("delivery/pdf/publication.pdf"),
    Path("delivery/pdf/grayscale.pdf"),
    Path("delivery/delivery_manifest.json"),
    Path("validation/cross_format_report.json"),
    Path("validation/cross_format_preview.png"),
)

GATE_LABELS = {
    "synthetic",
    "publication-safe",
    "deterministic fixture pre-approval",
}
FIXED_GENERATION_LABEL = "deterministic fixture replay; runtime timestamp intentionally omitted"
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


class DemoError(RuntimeError):
    """Raised when the demo must stop without claiming completion."""


class FullRuntimeUnavailable(DemoError):
    """Raised when full adapters cannot run in the documented local runtime."""

    def __init__(self, missing: Sequence[str]) -> None:
        self.missing = list(missing)
        super().__init__(
            "full adapter runtime is incomplete: %s. See docs/runtime_requirements.md; "
            "install the declared Python dependencies and provide the documented local tools."
            % "; ".join(self.missing)
        )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path, label: str = "JSON record") -> Any:
    if not path.is_file():
        raise DemoError("%s is missing" % label)
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DemoError("%s is not parseable JSON" % label) from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _external_output(path: Path, *, must_exist: bool) -> Path:
    resolved = path.expanduser().resolve()
    if _inside(resolved, REPOSITORY_ROOT):
        raise DemoError("--output-dir must be outside the repository source tree")
    if must_exist:
        if not resolved.is_dir():
            raise DemoError("the requested demo run directory does not exist")
    elif resolved.exists():
        raise DemoError(
            "refusing to overwrite an existing path; choose a new --output-dir"
        )
    return resolved


def _run_file(run_dir: Path, relative_path: str | Path) -> Path:
    candidate = (run_dir / Path(relative_path)).resolve()
    if not _inside(candidate, run_dir):
        raise DemoError("demo state contains a path outside its run directory")
    return candidate


def _portable_string(value: str, run_dir: Path) -> str:
    root = str(run_dir.resolve())
    repository = str(REPOSITORY_ROOT.resolve())
    if value == root:
        return "."
    prefix = root + os.sep
    if value.startswith(prefix):
        return value[len(prefix) :].replace(os.sep, "/")
    if value == repository:
        return "<repository-root>"
    repository_prefix = repository + os.sep
    if value.startswith(repository_prefix):
        relative = value[len(repository_prefix) :].replace(os.sep, "/")
        return "<repository-root>/%s" % relative
    return (
        value.replace(prefix, "")
        .replace(root, ".")
        .replace(repository_prefix, "<repository-root>/")
        .replace(repository, "<repository-root>")
    )


def _portable_value(value: Any, run_dir: Path) -> Any:
    if isinstance(value, str):
        return _portable_string(value, run_dir)
    if isinstance(value, list):
        return [_portable_value(item, run_dir) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _portable_value(item, run_dir)
            for key, item in value.items()
        }
    return value


def _sanitize_portable_records(run_dir: Path) -> None:
    for path in sorted(run_dir.rglob("*.json")):
        if path.name == "demo_state.json":
            continue
        try:
            value = load_json(path, "generated JSON record")
        except DemoError:
            continue
        portable = _portable_value(value, run_dir)
        if portable != value:
            write_json(path, portable)
    root_bytes = str(run_dir.resolve()).encode("utf-8")
    repository_bytes = str(REPOSITORY_ROOT.resolve()).encode("utf-8")
    for path in sorted(run_dir.rglob("*.ndjson")):
        payload = path.read_bytes()
        portable = payload.replace(root_bytes + os.sep.encode("utf-8"), b"")
        portable = portable.replace(
            repository_bytes + os.sep.encode("utf-8"),
            b"<repository-root>/",
        )
        if portable != payload:
            path.write_bytes(portable)


def _artifact_hashes(run_dir: Path) -> dict[str, str]:
    records: dict[str, str] = {}
    for path in sorted(run_dir.rglob("*")):
        if path.is_symlink():
            relative = path.relative_to(run_dir).as_posix()
            raise DemoError("demo artifact inventory contains a symbolic link: %s" % relative)
        if not path.is_file() or path.name == "demo_state.json":
            continue
        relative = path.relative_to(run_dir).as_posix()
        records[relative] = sha256_file(path)
    return records


def _save_state(run_dir: Path, state: dict[str, Any]) -> None:
    state["artifact_hashes"] = _artifact_hashes(run_dir)
    write_json(run_dir / "demo_state.json", state)


def _event(state: dict[str, Any], name: str) -> None:
    events = state.setdefault("events", [])
    if name not in events:
        events.append(name)


def _initial_state(mode: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "demo_version": "1.0",
        "demo_kind": "publication-safe deterministic fixture replay",
        "mode": mode,
        "status": "IN_PROGRESS",
        "stage": "initialized",
        "input": {
            "name": "synthetic demo sketch",
            "interpretation": "reviewed deterministic fixture",
            "execution_mode": "fixture replay",
            "ai_execution": False,
        },
        "output_contract": {
            "location": "explicit external output directory",
            "existing_output_policy": "refuse; never overwrite an existing run",
            "core_mode": (
                "canonical semantic source and editable SVG only; explicitly INCOMPLETE"
            ),
            "full_mode_required_artifacts": [
                path.as_posix() for path in FULL_DELIVERY_FILES
            ],
            "gate_3_record": "approvals/gate_3_final_approval.json",
            "placeholder_formats_allowed": False,
        },
        "gates": {
            "gate_1": {
                "status": "not_reached",
                "authority": "checked-in deterministic fixture pre-approval",
                "in_run_human_action": False,
            },
            "gate_2": {
                "status": "not_reached",
                "authority": "checked-in deterministic fixture pre-approval",
                "in_run_human_action": False,
            },
            "gate_3": {
                "status": "not_reached",
                "authority": "separate explicit researcher/operator action",
                "created_by_automated_validation": False,
            },
        },
        "claims": {
            "live_ai_interpretation": False,
            "validation_name": "programmable structural checks",
            "programmable_checks_are_scientific_validation": False,
            "reproducibility_scope": (
                "Checked fixtures, topology, canonical semantic source, core SVG, record structure, "
                "and gate bindings are deterministic. Full adapter binaries may vary with the "
                "documented local runtime; their hashes remain audited per run."
            ),
        },
        "events": ["run_initialized"],
        "artifact_hashes": {},
    }


def _block(
    run_dir: Path,
    state: dict[str, Any],
    stage: str,
    error: DemoError,
    *,
    gate: str | None = None,
) -> None:
    state["status"] = "BLOCKED"
    state["stage"] = stage
    state["blocker"] = {
        "message": _portable_string(str(error), run_dir),
        "action": "Resolve the stated requirement, then start again in a new output directory.",
    }
    if gate is not None:
        state["gates"][gate]["status"] = "blocked"
    if isinstance(error, FullRuntimeUnavailable):
        state["blocker"]["missing_prerequisites"] = error.missing
    _event(state, stage)
    _sanitize_portable_records(run_dir)
    _save_state(run_dir, state)


def _require_sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise DemoError("%s must be a lowercase SHA-256 digest" % label)
    return value


def _public_source(path_value: Any, label: str) -> Path:
    if not isinstance(path_value, str) or not path_value:
        raise DemoError("reviewed interpretation has an invalid %s path" % label)
    source = (REPOSITORY_ROOT / path_value).resolve()
    if not _inside(source, REPOSITORY_ROOT) or not source.is_file():
        raise DemoError("reviewed interpretation %s source is unavailable" % label)
    return source


def _validate_interpretation() -> Mapping[str, Any]:
    value = load_json(INTERPRETATION_SOURCE, "reviewed deterministic fixture")
    if not isinstance(value, Mapping):
        raise DemoError("reviewed deterministic fixture must be a JSON object")
    if value.get("input_name") != "synthetic demo sketch":
        raise DemoError("reviewed interpretation has the wrong input name")
    if value.get("interpretation_name") != "reviewed deterministic fixture":
        raise DemoError("reviewed interpretation has the wrong fixture name")
    if value.get("execution_mode") != "fixture replay" or value.get("ai_execution") is not False:
        raise DemoError("reviewed interpretation must explicitly declare fixture replay with no AI execution")
    bindings = value.get("source_bindings")
    if not isinstance(bindings, Mapping) or set(bindings) != set(PUBLIC_INPUTS):
        raise DemoError("reviewed interpretation source bindings are incomplete")
    for name, expected_path in PUBLIC_INPUTS.items():
        binding = bindings.get(name)
        if not isinstance(binding, Mapping):
            raise DemoError("reviewed interpretation source binding is invalid: %s" % name)
        source = _public_source(binding.get("path"), name)
        if source != expected_path.resolve():
            raise DemoError("reviewed interpretation binds the wrong public source: %s" % name)
        expected_hash = _require_sha(binding.get("sha256"), "%s binding" % name)
        if sha256_file(source) != expected_hash:
            raise DemoError("reviewed interpretation source hash changed: %s" % name)
    return value


def _validate_gate_1(record_path: Path, run_dir: Path) -> Mapping[str, Any]:
    record = load_json(record_path, "Gate 1 deterministic fixture pre-approval")
    if not isinstance(record, Mapping):
        raise DemoError("Gate 1 record must be a JSON object")
    expected = {
        "schema_version": "1.0",
        "gate_id": "GATE_1",
        "record_type": "deterministic fixture pre-approval",
        "decision": "PREAPPROVE_REVIEWED_FIXTURE",
        "input_name": "synthetic demo sketch",
        "interpretation_name": "reviewed deterministic fixture",
        "authority": "checked-in publication-safe fixture record",
        "in_run_human_action": False,
        "scientific_validation": False,
    }
    for key, value in expected.items():
        if record.get(key) != value:
            raise DemoError("Gate 1 record has invalid %s" % key)
    labels = record.get("labels")
    if not isinstance(labels, list) or not all(isinstance(item, str) for item in labels):
        raise DemoError("Gate 1 record labels must be an array of strings")
    if set(labels) != GATE_LABELS:
        raise DemoError("Gate 1 record lacks the required publication-safe fixture labels")
    if sha256_file(record_path) != sha256_file(DEFAULT_GATE_1):
        raise DemoError("Gate 1 record must match the checked-in publication-safe pre-approval")
    interpretation_path = run_dir / "input" / "reviewed_deterministic_fixture.json"
    sketch_path = run_dir / "input" / "synthetic_demo_sketch.svg"
    if record.get("interpretation_sha256") != sha256_file(interpretation_path):
        raise DemoError("Gate 1 interpretation SHA-256 binding does not match")
    if record.get("input_sha256") != sha256_file(sketch_path):
        raise DemoError("Gate 1 synthetic demo sketch SHA-256 binding does not match")
    return record


def _validate_gate_2(
    record_path: Path,
    run_dir: Path,
    interpretation: Mapping[str, Any],
) -> Mapping[str, Any]:
    record = load_json(record_path, "Gate 2 deterministic fixture pre-approval")
    if not isinstance(record, Mapping):
        raise DemoError("Gate 2 record must be a JSON object")
    expected = {
        "schema_version": "1.0",
        "gate_id": "GATE_2",
        "record_type": "deterministic fixture pre-approval",
        "decision": "PREAPPROVE_TOPOLOGY_FIXTURE",
        "authority": "checked-in publication-safe fixture record",
        "in_run_human_action": False,
        "scientific_validation": False,
    }
    for key, value in expected.items():
        if record.get(key) != value:
            raise DemoError("Gate 2 record has invalid %s" % key)
    labels = record.get("labels")
    if not isinstance(labels, list) or not all(isinstance(item, str) for item in labels):
        raise DemoError("Gate 2 record labels must be an array of strings")
    if set(labels) != GATE_LABELS:
        raise DemoError("Gate 2 record lacks the required publication-safe fixture labels")
    if sha256_file(record_path) != sha256_file(DEFAULT_GATE_2):
        raise DemoError("Gate 2 record must match the checked-in publication-safe pre-approval")
    topology = record.get("topology_bindings")
    if not isinstance(topology, Mapping):
        raise DemoError("Gate 2 topology bindings are missing")
    for hash_name, relative_path in SKELETON_FILES.items():
        expected_hash = _require_sha(topology.get(hash_name), "Gate 2 %s" % hash_name)
        if sha256_file(run_dir / relative_path) != expected_hash:
            raise DemoError("Gate 2 topology SHA-256 binding does not match: %s" % hash_name)
    sources = record.get("source_bindings")
    if not isinstance(sources, Mapping):
        raise DemoError("Gate 2 source bindings are missing")
    source_checks = {
        "scientific_truth_sha256": run_dir / INPUT_DESTINATIONS["scientific_truth"],
        "topology_blueprint_sha256": run_dir / INPUT_DESTINATIONS["topology_blueprint"],
    }
    for name, path in source_checks.items():
        if sources.get(name) != sha256_file(path):
            raise DemoError("Gate 2 source SHA-256 binding does not match: %s" % name)
    expected_contract = interpretation.get("interpretation", {}).get("topology_contract")
    if record.get("semantic_topology_contract") != expected_contract:
        raise DemoError("Gate 2 semantic topology contract does not match Gate 1 interpretation")
    return record


def _copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise DemoError("refusing to overwrite an existing demo artifact")
    shutil.copyfile(source, destination)


def _copy_initial_inputs(run_dir: Path) -> None:
    _copy(
        PUBLIC_INPUTS["synthetic_demo_sketch"],
        run_dir / INPUT_DESTINATIONS["synthetic_demo_sketch"],
    )
    _copy(
        INTERPRETATION_SOURCE,
        run_dir / "input" / "reviewed_deterministic_fixture.json",
    )


def _copy_topology_inputs(run_dir: Path) -> None:
    for name in ("scientific_truth", "topology_blueprint"):
        _copy(PUBLIC_INPUTS[name], run_dir / INPUT_DESTINATIONS[name])


def _copy_semantic_inputs(run_dir: Path) -> None:
    for name in ("reviewed_semantic_svg", "semantic_validation_spec"):
        _copy(PUBLIC_INPUTS[name], run_dir / INPUT_DESTINATIONS[name])


def _portable_semantic_source(run_dir: Path) -> None:
    semantic_path = run_dir / "source" / "semantic_figure.json"
    semantic = load_json(semantic_path, "canonical semantic source")
    if not isinstance(semantic, dict):
        raise DemoError("canonical semantic source must be a JSON object")
    provenance = semantic.setdefault("provenance", {})
    provenance["generated_at"] = FIXED_GENERATION_LABEL
    provenance["truth_source"] = "input/scientific_truth.json"
    provenance["equation_manifest"] = "../math/equation_manifest.json"
    provenance["execution_mode"] = "fixture replay"
    provenance["ai_execution"] = False
    provenance["source_roles"] = {
        "semantic_svg": "reviewed deterministic fixture geometry",
        "approved_wireframe": "Gate 2 bound deterministic topology skeleton",
        "approved_png_direction": "not applicable; fixture replay used no generated candidate",
    }
    semantic = _portable_value(semantic, run_dir)
    errors = semantic_integrity_errors(semantic)
    if errors:
        raise DemoError("canonical semantic source failed validation: %s" % "; ".join(errors))
    write_json(semantic_path, semantic)


def _build_semantic_and_core_svg(run_dir: Path) -> None:
    semantic_svg = run_dir / INPUT_DESTINATIONS["reviewed_semantic_svg"]
    validation_spec = run_dir / INPUT_DESTINATIONS["semantic_validation_spec"]
    truth = run_dir / INPUT_DESTINATIONS["scientific_truth"]
    skeleton = run_dir / SKELETON_FILES["svg_sha256"]
    build_semantic_source(
        semantic_svg,
        validation_spec,
        run_dir,
        figure_id="synthetic_restoration_demo",
        truth_path=truth,
        wireframe_path=skeleton,
    )
    _portable_semantic_source(run_dir)
    _sanitize_portable_records(run_dir)
    semantic = run_dir / "source" / "semantic_figure.json"
    export_svg(semantic, run_dir / "master" / "master.svg", "svg")
    export_svg(semantic, run_dir / "delivery" / "svg" / "master.svg", "svg")
    _sanitize_portable_records(run_dir)


def full_runtime_prerequisites() -> tuple[bool, list[str]]:
    """Return documented full-runtime readiness without running an adapter."""

    missing: list[str] = []
    node_value = os.environ.get("RUNTIME_NODE") or "node"
    node = shutil.which(node_value) or (
        str(Path(node_value).resolve()) if Path(node_value).is_file() else None
    )
    if not node:
        missing.append("Node.js executable (RUNTIME_NODE or node on PATH)")
    module_root = os.environ.get("RUNTIME_NODE_MODULES")
    artifact_module = (
        Path(module_root) / "@oai" / "artifact-tool" / "dist" / "artifact_tool.mjs"
        if module_root
        else None
    )
    if artifact_module is None or not artifact_module.is_file():
        missing.append(
            "RUNTIME_NODE_MODULES containing @oai/artifact-tool/dist/artifact_tool.mjs"
        )
    latex_ready = shutil.which("latex") is not None and shutil.which("dvisvgm") is not None
    mathjax_ready = bool(
        node
        and module_root
        and (Path(module_root) / "mathjax-full" / "js" / "mathjax.js").is_file()
    )
    if not latex_ready and not mathjax_ready:
        missing.append("equation renderer (latex+dvisvgm or local mathjax-full)")
    for module in ("PIL", "reportlab", "pypdf"):
        if importlib.util.find_spec(module) is None:
            missing.append("Python module %s" % module)
    return not missing, missing


def _portable_pptx(path: Path, run_dir: Path) -> None:
    """Remove the run-directory path embedded in native PPTX notes."""

    temporary = path.with_suffix(".portable.tmp")
    root_bytes = str(run_dir.resolve()).encode("utf-8") + os.sep.encode("utf-8")
    with zipfile.ZipFile(path, "r") as source, zipfile.ZipFile(
        temporary, "w", compression=zipfile.ZIP_DEFLATED
    ) as target:
        for item in source.infolist():
            payload = source.read(item.filename).replace(root_bytes, b"")
            info = zipfile.ZipInfo(item.filename, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = item.external_attr
            info.create_system = item.create_system
            target.writestr(info, payload)
    temporary.replace(path)


def _require_adapter_status(report: Mapping[str, Any], name: str) -> None:
    if report.get("status") != "VERIFIED":
        reason = report.get("reason", "adapter did not return VERIFIED")
        raise DemoError("%s adapter blocked: %s" % (name, reason))


def _assert_full_delivery_files(run_dir: Path) -> None:
    missing = [path.as_posix() for path in FULL_DELIVERY_FILES if not (run_dir / path).is_file()]
    if missing:
        raise DemoError("full delivery is missing required native artifact(s): %s" % ", ".join(missing))


def _build_full_delivery(run_dir: Path) -> Path:
    ready, missing = full_runtime_prerequisites()
    if not ready:
        raise FullRuntimeUnavailable(missing)

    semantic = run_dir / "source" / "semantic_figure.json"
    equation_report = render_manifest(
        run_dir / "math" / "equation_manifest.json",
        run_dir / "math" / "rendered",
    )
    _require_adapter_status(equation_report, "equation rendering")

    export_svg(semantic, run_dir / "delivery" / "figma" / "figure_figma.svg", "figma")
    pptx_report = export_pptx(
        semantic,
        run_dir / "delivery" / "pptx",
        run_dir / "math" / "rendered",
    )
    _require_adapter_status(pptx_report, "PPTX")
    drawio_report = export_drawio(semantic, run_dir / "delivery" / "drawio")
    _require_adapter_status(drawio_report, "draw.io")
    pdf_report = export_pdf(semantic, run_dir / "delivery" / "pdf")
    _require_adapter_status(pdf_report, "PDF")

    pptx_path = run_dir / "delivery" / "pptx" / "figure.pptx"
    _portable_pptx(pptx_path, run_dir)
    pptx_export_report_path = run_dir / "delivery" / "pptx" / "pptx_export_report.json"
    pptx_export_report = load_json(pptx_export_report_path, "PPTX export report")
    if isinstance(pptx_export_report, dict):
        pptx_export_report["pptx_sha256"] = sha256_file(pptx_path)
        write_json(pptx_export_report_path, pptx_export_report)
    _sanitize_portable_records(run_dir)

    report = validate_delivery(run_dir)
    _sanitize_portable_records(run_dir)
    report_path = run_dir / "validation" / "cross_format_report.json"
    report = load_json(report_path, "cross-format structural validation report")
    if not isinstance(report, Mapping) or report.get("status") != "VERIFIED":
        raise DemoError(
            "programmable structural checks did not return VERIFIED; inspect "
            "validation/cross_format_report.json"
        )
    if report.get("validation_scope") != (
        "Programmable structure only; not scientific correctness or Gate 3 approval."
    ):
        raise DemoError("validation report does not preserve the scientific-approval boundary")
    _assert_full_delivery_files(run_dir)
    return report_path


def _enter_awaiting_gate_3(
    run_dir: Path,
    state: dict[str, Any],
    report_path: Path,
) -> dict[str, Any]:
    """Record VERIFIED structural checks without creating scientific approval."""

    _assert_full_delivery_files(run_dir)
    report = load_json(report_path, "cross-format structural validation report")
    if not isinstance(report, Mapping) or report.get("status") != "VERIFIED":
        raise DemoError("Gate 3 requires a VERIFIED cross-format structural report")
    approval_path = run_dir / "approvals" / "gate_3_final_approval.json"
    if approval_path.exists():
        raise DemoError("automated validation must not create the Gate 3 approval record")
    relative_report = report_path.resolve().relative_to(run_dir.resolve()).as_posix()
    state["status"] = "AWAITING_DECISION"
    state["stage"] = "awaiting_gate_3"
    state["gates"]["gate_3"] = {
        "status": "awaiting_explicit_researcher_or_operator_action",
        "authority": "separate explicit researcher/operator action",
        "created_by_automated_validation": False,
        "validation_report": {
            "path": relative_report,
            "sha256": sha256_file(report_path),
            "scope": "programmable structural checks; not scientific validation",
        },
    }
    _event(state, "programmable_structural_checks_verified")
    _event(state, "awaiting_gate_3")
    _save_state(run_dir, state)
    return state


def build_demo(
    output_dir: Path,
    *,
    mode: str = "full",
    gate_1_record: Path = DEFAULT_GATE_1,
    gate_2_record: Path = DEFAULT_GATE_2,
) -> dict[str, Any]:
    if mode not in {"core", "full"}:
        raise DemoError("mode must be core or full")
    run_dir = _external_output(output_dir, must_exist=False)
    run_dir.mkdir(parents=True)
    state = _initial_state(mode)
    _save_state(run_dir, state)

    try:
        interpretation = _validate_interpretation()
        _copy_initial_inputs(run_dir)
        _event(state, "reviewed_deterministic_fixture_emitted")
        _save_state(run_dir, state)
    except DemoError as error:
        _block(run_dir, state, "blocked_input_fixture", error)
        raise

    try:
        gate_1 = _validate_gate_1(gate_1_record, run_dir)
        _copy(gate_1_record, run_dir / "approvals" / "gate_1_preapproval.json")
        state["gates"]["gate_1"] = {
            "status": "accepted_checked_in_fixture_preapproval",
            "record": "approvals/gate_1_preapproval.json",
            "record_sha256": sha256_file(run_dir / "approvals" / "gate_1_preapproval.json"),
            "interpretation_sha256": gate_1["interpretation_sha256"],
            "authority": "checked-in deterministic fixture pre-approval",
            "in_run_human_action": False,
        }
        _event(state, "gate_1_fixture_preapproval_accepted")
        _save_state(run_dir, state)
    except DemoError as error:
        _block(run_dir, state, "blocked_gate_1", error, gate="gate_1")
        raise

    try:
        _copy_topology_inputs(run_dir)
        render_topology_skeleton(
            run_dir / INPUT_DESTINATIONS["scientific_truth"],
            run_dir / INPUT_DESTINATIONS["topology_blueprint"],
            run_dir / "skeleton",
        )
        state["stage"] = "skeleton_generated"
        _event(state, "deterministic_topology_skeleton_generated")
        _save_state(run_dir, state)
    except (OSError, ValueError, KeyError) as exc:
        error = DemoError("deterministic topology skeleton generation failed: %s" % exc)
        _block(run_dir, state, "blocked_skeleton", error)
        raise error from exc

    try:
        gate_2 = _validate_gate_2(gate_2_record, run_dir, interpretation)
        _copy(gate_2_record, run_dir / "approvals" / "gate_2_preapproval.json")
        state["gates"]["gate_2"] = {
            "status": "accepted_checked_in_fixture_preapproval",
            "record": "approvals/gate_2_preapproval.json",
            "record_sha256": sha256_file(run_dir / "approvals" / "gate_2_preapproval.json"),
            "topology_bindings": dict(gate_2["topology_bindings"]),
            "authority": "checked-in deterministic fixture pre-approval",
            "in_run_human_action": False,
        }
        _event(state, "gate_2_fixture_preapproval_accepted")
        _save_state(run_dir, state)
    except DemoError as error:
        _block(run_dir, state, "blocked_gate_2", error, gate="gate_2")
        raise

    try:
        _copy_semantic_inputs(run_dir)
        _build_semantic_and_core_svg(run_dir)
        state["stage"] = "semantic_source_built"
        _event(state, "canonical_semantic_source_built")
        _event(state, "editable_svg_built")
        _save_state(run_dir, state)
    except (DemoError, OSError, ValueError, KeyError) as exc:
        error = exc if isinstance(exc, DemoError) else DemoError(
            "canonical semantic source build failed: %s" % exc
        )
        _block(run_dir, state, "blocked_semantic_source", error)
        raise error from exc

    if mode == "core":
        state["status"] = "INCOMPLETE"
        state["stage"] = "incomplete_core_only"
        state["gates"]["gate_3"]["status"] = "not_reached_incomplete_core_only"
        state["limitations"] = {
            "reason": "Core-only mode intentionally omits the full adapter and cross-format validation chain.",
            "omitted_formats": [
                "native PPTX",
                "editable draw.io",
                "publication PDF",
                "grayscale PDF",
                "draw.io companion PDF",
                "cross-format preview",
            ],
            "placeholders_emitted": False,
            "final_approval_emitted": False,
        }
        _event(state, "core_only_stopped_incomplete")
        _sanitize_portable_records(run_dir)
        _save_state(run_dir, state)
        return state

    try:
        report_path = _build_full_delivery(run_dir)
        state["stage"] = "adapters_built"
        _event(state, "native_full_adapter_outputs_built")
        _save_state(run_dir, state)
        return _enter_awaiting_gate_3(run_dir, state, report_path)
    except DemoError as error:
        stage = (
            "blocked_full_runtime"
            if isinstance(error, FullRuntimeUnavailable)
            else "blocked_full_delivery"
        )
        state["gates"]["gate_3"]["status"] = "not_reached_full_delivery_blocked"
        _block(run_dir, state, stage, error)
        raise
    except (OSError, ValueError, KeyError) as exc:
        error = DemoError("full delivery build failed: %s" % exc)
        state["gates"]["gate_3"]["status"] = "not_reached_full_delivery_blocked"
        _block(run_dir, state, "blocked_full_delivery", error)
        raise error from exc


def _operator(value: str | None) -> str:
    if value is None or not value.strip():
        raise DemoError("--approve-final requires a non-empty --operator")
    operator = value.strip()
    if len(operator) > 120 or any(ord(character) < 32 for character in operator):
        raise DemoError("--operator must be printable and at most 120 characters")
    return operator


def _verify_artifact_hashes(run_dir: Path, state: Mapping[str, Any]) -> None:
    records = state.get("artifact_hashes")
    if not isinstance(records, Mapping):
        raise DemoError("demo state lacks artifact hash bindings")
    current = _artifact_hashes(run_dir)
    recorded_paths = {str(path) for path in records}
    current_paths = set(current)
    if current_paths != recorded_paths:
        added = sorted(current_paths - recorded_paths)
        missing = sorted(recorded_paths - current_paths)
        details = []
        if added:
            details.append("added: %s" % ", ".join(added))
        if missing:
            details.append("missing: %s" % ", ".join(missing))
        raise DemoError(
            "artifact set changed after validation (%s)" % "; ".join(details)
        )
    for relative, expected in records.items():
        path = _run_file(run_dir, str(relative))
        if current[str(relative)] != expected or not path.is_file():
            raise DemoError("artifact changed after validation: %s" % relative)


def approve_final(output_dir: Path, operator: str) -> dict[str, Any]:
    """Create Gate 3 only after an explicit researcher/operator invocation."""

    run_dir = _external_output(output_dir, must_exist=True)
    actor = _operator(operator)
    state = load_json(run_dir / "demo_state.json", "demo state")
    if not isinstance(state, dict):
        raise DemoError("demo state must be a JSON object")
    if state.get("mode") != "full" or state.get("stage") != "awaiting_gate_3":
        raise DemoError("final approval is allowed only for a full run awaiting Gate 3")
    gate_3 = state.get("gates", {}).get("gate_3", {})
    if gate_3.get("status") != "awaiting_explicit_researcher_or_operator_action":
        raise DemoError("demo state is not awaiting explicit Gate 3 action")
    _assert_full_delivery_files(run_dir)
    _verify_artifact_hashes(run_dir, state)

    binding = gate_3.get("validation_report")
    if not isinstance(binding, Mapping):
        raise DemoError("Gate 3 validation-report binding is missing")
    report_path = _run_file(run_dir, str(binding.get("path", "")))
    report_hash = _require_sha(binding.get("sha256"), "Gate 3 validation report")
    if not report_path.is_file() or sha256_file(report_path) != report_hash:
        raise DemoError("Gate 3 validation report changed after programmable checks")
    report = load_json(report_path, "cross-format structural validation report")
    if not isinstance(report, Mapping) or report.get("status") != "VERIFIED":
        raise DemoError("Gate 3 validation report is not VERIFIED")

    approval_candidate = run_dir / "approvals" / "gate_3_final_approval.json"
    if approval_candidate.is_symlink():
        raise DemoError("Gate 3 approval path must not be a symbolic link")
    approval_path = _run_file(
        run_dir,
        "approvals/gate_3_final_approval.json",
    )
    if approval_path.exists():
        raise DemoError("refusing to overwrite an existing Gate 3 approval record")
    approval = {
        "schema_version": "1.0",
        "gate_id": "GATE_3",
        "record_type": "explicit researcher/operator scientific-acceptability decision",
        "decision": "APPROVE_FINAL",
        "operator": actor,
        "validation_report": {
            "path": report_path.relative_to(run_dir).as_posix(),
            "sha256": report_hash,
            "status": "VERIFIED",
            "scope": "programmable structural checks; not scientific validation",
        },
        "decision_statement": (
            "The researcher/operator, not automated validation, decides scientific acceptability. "
            "VERIFIED means only that the programmable structural checks passed."
        ),
        "created_by_automated_validation": False,
        "scientific_acceptability_decided_by": "researcher/operator",
        "ai_execution": False,
    }
    write_json(approval_path, approval)
    state["status"] = "COMPLETE"
    state["stage"] = "complete"
    state["gates"]["gate_3"] = {
        "status": "approved_by_explicit_researcher_or_operator_action",
        "authority": "researcher/operator",
        "created_by_automated_validation": False,
        "record": "approvals/gate_3_final_approval.json",
        "record_sha256": sha256_file(approval_path),
        "validation_report": dict(binding),
    }
    _event(state, "gate_3_explicit_approval_recorded")
    _save_state(run_dir, state)
    return state


def _summary(state: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "status": state.get("status"),
        "stage": state.get("stage"),
        "mode": state.get("mode"),
        "gate_status": {
            name: details.get("status")
            for name, details in state.get("gates", {}).items()
        },
        "artifact_count": len(state.get("artifact_hashes", {})),
        "ai_execution": False,
        "validation": "programmable structural checks; not scientific validation",
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--mode", choices=("core", "full"), default="full")
    parser.add_argument("--gate-1-record", type=Path, default=DEFAULT_GATE_1)
    parser.add_argument("--gate-2-record", type=Path, default=DEFAULT_GATE_2)
    parser.add_argument("--approve-final", action="store_true")
    parser.add_argument("--operator")
    args = parser.parse_args(argv)
    try:
        if args.approve_final:
            state = approve_final(args.output_dir, args.operator)
        else:
            if args.operator is not None:
                raise DemoError("--operator is used only with --approve-final")
            state = build_demo(
                args.output_dir,
                mode=args.mode,
                gate_1_record=args.gate_1_record,
                gate_2_record=args.gate_2_record,
            )
    except DemoError as exc:
        print("SYNTHETIC DEMO BLOCKED: %s" % exc, file=sys.stderr)
        return 2
    print(json.dumps(_summary(state), indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
