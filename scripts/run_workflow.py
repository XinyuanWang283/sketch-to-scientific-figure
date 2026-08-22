#!/usr/bin/env python3
"""Resumable V3 autopilot orchestrator with exactly three human gates."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from build_figure_editorial_review import (
    build_outputs as build_editorial_outputs,
    resolve_approved_wireframe_preview,
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


def relative(path: Path, base: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except ValueError:
        return str(path.resolve())


def decision_none() -> Dict[str, Any]:
    return {
        "gate_id": "NONE", "status": "not_applicable", "summary": "No human decision is pending.",
        "questions": [], "recommendation": "Continue deterministic workflow steps.", "resume_command": "",
    }


def initial_state(run_dir: Path, repository_root: Path, input_paths: Sequence[Path], mode: str) -> Dict[str, Any]:
    now = utc_now()
    return {
        "schema_version": "1.0", "run_id": run_dir.name, "workflow_version": "3.0", "execution_count": 1,
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
    write_json(run_dir / "run_state.json", state)


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
    resume_base = "python %s --mode sketch --run-dir %s --resume --decision" % (script_path.resolve(), run_dir.resolve())
    faithful = visual_mode == "faithful_redraw"
    return {
        "gate_id": "GATE_1", "status": "awaiting_human",
        "summary": "Choose between the exact approved Visual Plan and the same geometry with one removable paper-aware overlay.",
        "questions": [{
            "id": "wireframe_direction", "question": "Which Gate 1 direction should production use?",
            "options": [
                {"id": "APPROVE_CONSERVATIVE", "label": "Exact approved Visual Plan", "impact": "Preserves the approved wireframe SVG and PNG byte-for-byte; supporting detail remains in the review/caption."},
                {"id": "APPROVE_RECOMMENDED", "label": "Plan-locked paper-aware overlay", "impact": "Keeps the identical geometry and adds one removable message cue."},
                {"id": "REVISE_GATE_1", "label": "Request revision", "impact": "Keeps production stopped before PNG generation."}
            ],
        }],
        "recommendation": (
            "APPROVE_CONSERVATIVE: faithful_redraw keeps the researcher-approved geometry as the production authority."
            if faithful else
            "APPROVE_RECOMMENDED: the optional paper-aware cue is isolated from the approved geometry."
        ),
        "resume_command": resume_base + (" APPROVE_CONSERVATIVE" if faithful else " APPROVE_RECOMMENDED"),
        "delegated_defaults": ["filenames", "spacing", "canvas size", "font fallback", "preview arrangement"],
    }


def gate2_packet(run_dir: Path, script_path: Path, candidates: Sequence[str]) -> Dict[str, Any]:
    return {
        "gate_id": "GATE_2", "status": "awaiting_human", "summary": "Select or reject the PNG visual direction.",
        "questions": [{
            "id": "png_direction", "question": "Which generated direction should become the semantic source reference?",
            "options": [{"id": "APPROVE_PNG", "label": Path(path).name, "impact": "Approve this visual direction; scientific structure remains governed by truth and semantic source."} for path in candidates[:2]] +
                       [{"id": "REJECT_PNG", "label": "Reject directions", "impact": "Return to the same Gate 2 with a bounded repair brief."}],
        }],
        "recommendation": "Approve only a candidate that passes the blocking topology checks; cosmetic SVG corrections remain downstream.",
        "resume_command": "python %s --mode sketch --run-dir %s --resume --decision APPROVE_PNG" % (script_path.resolve(), run_dir.resolve()),
    }


def gate3_packet(run_dir: Path, script_path: Path) -> Dict[str, Any]:
    return {
        "gate_id": "GATE_3", "status": "awaiting_human", "summary": "Approve or reject the validated scientific delivery package.",
        "questions": [{
            "id": "final_delivery", "question": "Approve the validated final scientific delivery?",
            "options": [
                {"id": "APPROVE_FINAL", "label": "Approve delivery", "impact": "Marks the V3 run complete."},
                {"id": "REVISE_DELIVERY", "label": "Request corrections", "impact": "Keeps the run at Gate 3 and records the requested correction."}
            ],
        }],
        "recommendation": "Approve only when scientific invariants pass and each format's editability claim is supported by its validation report.",
        "resume_command": "python %s --mode sketch --run-dir %s --resume --decision APPROVE_FINAL" % (script_path.resolve(), run_dir.resolve()),
    }


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
        run_dir / "delivery/drawio/figure_drawio.svg", run_dir / "delivery/drawio/figure_drawio_editable.pdf",
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
    primary_paper_source = args.paper_source[0] if args.paper_source else None
    required = [args.truth, primary_paper_source, args.sketch, visual_plan, approved_wireframe]
    if any(path is None for path in required):
        raise ValueError(
            "sketch mode requires --truth, at least one --paper-source, --sketch, "
            "--visual-plan, and --approved-wireframe"
        )
    state["state"] = "EDITORIAL_REVIEW"
    record(state, "editorial_review_started")
    save_state(args.run_dir, state)
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
    state["provenance"]["visual_plan_binding"] = report["visual_plan_binding"]
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
        if decision not in {"APPROVE_RECOMMENDED", "APPROVE_CONSERVATIVE", "REVISE_GATE_1"}:
            raise ValueError("Gate 1 requires APPROVE_RECOMMENDED, APPROVE_CONSERVATIVE, or REVISE_GATE_1")
        if decision == "REVISE_GATE_1":
            record(state, "gate_1_revision_requested")
            save_state(args.run_dir, state)
            return state
        state["gate_status"]["gate_1"] = "approved"
        state["state"] = "PNG_DIRECTION"
        state["decision_packet"] = decision_none()
        record(state, "gate_1_approved", decision=decision)
        save_state(args.run_dir, state)
        return state
    if current == "PNG_DIRECTION":
        if not args.register_png:
            raise ValueError("PNG_DIRECTION resume requires --register-png for a candidate created by the built-in image-generation tool")
        candidates = []
        candidate_dir = args.run_dir / "generation/candidates"
        candidate_dir.mkdir(parents=True, exist_ok=True)
        for source in args.register_png:
            destination = candidate_dir / source.name
            if source.resolve() != destination.resolve():
                shutil.copyfile(source, destination)
            candidates.append(relative(destination, args.run_dir))
            add_artifact(state, args.run_dir, destination)
        state["provenance"]["image_generation_calls"] += 1
        state["state"] = "GATE_2_PNG_VISUAL_DIRECTION"
        state["gate_status"]["gate_2"] = "awaiting_human"
        state["decision_packet"] = gate2_packet(args.run_dir, Path(__file__), candidates)
        write_json(args.run_dir / "gate_2_decision_packet.json", state["decision_packet"])
        add_artifact(state, args.run_dir, args.run_dir / "gate_2_decision_packet.json")
        record(state, "gate_2_reached", candidates=candidates)
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
            state["gate_status"]["gate_2"] = "approved"
            state["state"] = "SEMANTIC_BUILD"
            state["decision_packet"] = decision_none()
            record(state, "gate_2_approved")
        save_state(args.run_dir, state)
        return state
    if current in {"SEMANTIC_BUILD", "DELIVERY_BUILD"}:
        if not args.register_delivery:
            raise ValueError("semantic/delivery build resume requires --register-delivery after adapters and validation complete")
        for path in args.register_delivery:
            add_artifact(state, args.run_dir, path)
        state["state"] = "GATE_3_FINAL_SCIENTIFIC_DELIVERY"
        state["gate_status"]["gate_3"] = "awaiting_human"
        state["decision_packet"] = gate3_packet(args.run_dir, Path(__file__))
        write_json(args.run_dir / "gate_3_decision_packet.json", state["decision_packet"])
        add_artifact(state, args.run_dir, args.run_dir / "gate_3_decision_packet.json")
        record(state, "gate_3_reached")
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
            record(state, "gate_3_revision_requested")
        save_state(args.run_dir, state)
        return state
    raise ValueError("cannot resume state %s" % current)


def run(args: argparse.Namespace) -> Dict[str, Any]:
    args.run_dir = args.run_dir.resolve()
    state_path = args.run_dir / "run_state.json"
    if args.resume:
        if not state_path.exists():
            raise FileNotFoundError("--resume requested but run_state.json does not exist")
        state = load_json(state_path)
        require_valid(state, "run_state.schema.json")
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
    args.run_dir.mkdir(parents=True, exist_ok=True)
    inputs: List[Path] = []
    if args.mode == "fixture":
        inputs = [
            args.fixture_svg or REPOSITORY_ROOT / "tests/fixtures/generic_semantic_pass.svg",
            args.fixture_spec or REPOSITORY_ROOT / "tests/fixtures/generic_svg_fixture_spec.json",
        ]
    else:
        if getattr(args, "visual_plan", None) and not getattr(args, "approved_wireframe_png", None):
            args.approved_wireframe_png = resolve_approved_wireframe_preview(args.visual_plan)
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
    save_state(args.run_dir, state)
    return run_fixture(args, state) if args.mode == "fixture" else run_sketch_initial(args, state)


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
    parser.add_argument("--register-delivery", action="append", type=Path)
    args = parser.parse_args()
    state = run(args)
    print(json.dumps(state, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
