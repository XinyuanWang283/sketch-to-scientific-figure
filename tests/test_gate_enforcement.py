#!/usr/bin/env python3
"""Regression tests for fail-closed workflow gate enforcement."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPOSITORY_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import run_workflow as workflow  # noqa: E402
from build_fixture_semantic_source import build as build_semantic_source  # noqa: E402
from figure_artifacts import sha256_file, write_json  # noqa: E402
from workflow_v3 import validate_schema  # noqa: E402


def args(run_dir: Path, **overrides: object) -> SimpleNamespace:
    values = {
        "mode": "sketch", "run_dir": run_dir, "resume": True, "decision": None,
        "truth": None, "paper_source": [], "sketch": None, "visual_plan": None,
        "approved_wireframe": None, "approved_wireframe_png": None,
        "fixture_svg": None, "fixture_spec": None, "register_png": None,
        "candidate_sha256": None, "generation_call_id": None,
        "selected_candidate": None, "selected_candidate_sha256": None,
        "register_delivery": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def png(path: Path) -> None:
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (24, 16), "white").save(path)


def awaiting_packet(gate_id: str) -> dict[str, object]:
    return {
        "gate_id": gate_id, "status": "awaiting_human", "summary": "test gate",
        "questions": [], "recommendation": "review", "resume_command": "test",
    }


def make_gate_1_state(run_dir: Path) -> dict[str, object]:
    plan_dir = run_dir / "visual_plan"
    editorial = run_dir / "editorial"
    plan_dir.mkdir(parents=True)
    editorial.mkdir(parents=True)
    plan = plan_dir / "visual_plan.json"
    wireframe = plan_dir / "approved_wireframe.svg"
    preview = plan_dir / "approved_wireframe.png"
    wireframe.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>\n', encoding="utf-8")
    png(preview)
    plan.write_text(json.dumps({
        "schema_version": "1.0", "case_id": "gate-test", "visual_mode": "guided_redesign",
        "status": "approved", "spatial_locks": ["left to right"], "allowed_changes": [],
        "forbidden_visual_grammars": ["dashboard"], "text_policy": {},
        "wireframe_artifacts": {"wireframe_svg": wireframe.name, "wireframe_png": preview.name},
        "approval_gate": {
            "image_generation_authorized": True, "approved_wireframe_revision": 1,
            "approved_wireframe_sha256": sha256_file(preview),
        },
    }), encoding="utf-8")
    for stem in ("conservative", "recommended"):
        (editorial / ("wireframe_%s.svg" % stem)).write_text(
            '<svg xmlns="http://www.w3.org/2000/svg"/>\n', encoding="utf-8"
        )
        png(editorial / ("wireframe_%s.png" % stem))
    write_json(editorial / "figure_editorial_review.json", {
        "figure_id": "gate-test", "scientific_meaning": "synthetic test interpretation",
    })
    state = workflow.initial_state(run_dir, REPOSITORY_ROOT, [], "sketch")
    state["state"] = "GATE_1_EDITORIAL_STORY_WIREFRAME"
    state["gate_status"]["gate_1"] = "awaiting_human"
    state["decision_packet"] = awaiting_packet("GATE_1")
    state["provenance"]["visual_plan_binding"] = {
        "visual_mode": "guided_redesign", "visual_plan_status": "approved",
        "visual_plan_path": "visual_plan/visual_plan.json",
        "visual_plan_sha256": sha256_file(plan),
        "approved_wireframe_svg_path": "visual_plan/approved_wireframe.svg",
        "approved_wireframe_svg_sha256": sha256_file(wireframe),
        "approved_wireframe_png_path": "visual_plan/approved_wireframe.png",
        "approved_wireframe_png_sha256": sha256_file(preview),
    }
    workflow.save_state(run_dir, state)
    return state


def advance_to_gate_2(run_dir: Path) -> tuple[dict[str, object], Path]:
    make_gate_1_state(run_dir)
    state = workflow.run(args(run_dir, decision="APPROVE_CONSERVATIVE"))
    candidate = run_dir / "generation/candidates/candidate-a.png"
    png(candidate)
    candidate_hash = sha256_file(candidate)
    state = workflow.run(args(
        run_dir, register_png=[candidate], candidate_sha256=[candidate_hash],
        generation_call_id=["image-call-1"],
    ))
    return state, candidate


def advance_to_semantic_build(run_dir: Path) -> tuple[dict[str, object], Path]:
    _, candidate = advance_to_gate_2(run_dir)
    state = workflow.run(args(
        run_dir, decision="APPROVE_PNG", selected_candidate="candidate-a",
        selected_candidate_sha256=sha256_file(candidate),
    ))
    return state, candidate


def make_delivery(
    run_dir: Path, *, preserve_semantic: bool = False
) -> tuple[Path, Path, dict[str, object]]:
    semantic = run_dir / "source/semantic_figure.json"
    equations = run_dir / "source/equations.tex"
    semantic.parent.mkdir(parents=True, exist_ok=True)
    state = json.loads((run_dir / "run_state.json").read_text(encoding="utf-8"))
    approval = state["provenance"]["gate_1_approval"]
    selected = state["provenance"]["selected_candidate"]
    if not preserve_semantic:
        write_json(semantic, {
            "figure_id": "gate-test",
            "provenance": {"source_hashes": {
                "gate_1_scientific_interpretation": approval["scientific_interpretation"]["sha256"],
                "approved_wireframe": approval["interpretation"]["sha256"],
                "approved_png_direction": selected["sha256"],
            }},
        })
        equations.write_text("% equations\n", encoding="utf-8")
    figure_id = json.loads(semantic.read_text(encoding="utf-8"))["figure_id"]
    formats = []
    for name, relative_path in workflow.EXPECTED_DELIVERY_FORMATS:
        path = run_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((name + "\n").encode("utf-8"))
        formats.append({
            "format": name, "path": str(path.resolve()), "status": "VERIFIED",
            "semantic_editability": name in {"svg", "figma-ready-svg", "pptx", "drawio"},
            "equation_source_editability": name in {"svg", "figma-ready-svg", "pptx", "drawio"},
            "verification": "validation/cross_format_report.json",
        })
    preview = run_dir / "validation/cross_format_preview.png"
    png(preview)
    report_path = run_dir / "validation/cross_format_report.json"
    manifest_path = run_dir / "delivery/delivery_manifest.json"
    report = {
        "schema_version": "1.0", "figure_id": figure_id, "status": "VERIFIED",
        "canonical_source": str(semantic.resolve()),
        "checks": [
            {"format": "semantic-source", "status": "VERIFIED", "path": str(semantic.resolve()), "sha256": sha256_file(semantic)},
            *[
                {"format": item["format"], "status": item["status"], "path": item["path"], "sha256": sha256_file(Path(item["path"]))}
                for item in formats
            ],
        ],
        "preview": {"status": "VERIFIED", "path": str(preview.resolve()), "sha256": sha256_file(preview)},
    }
    write_json(report_path, report)
    write_json(manifest_path, {
        "schema_version": "1.0", "figure_id": figure_id,
        "canonical_source": str(semantic.resolve()), "formats": formats,
        "validation_report": str(report_path.resolve()),
    })
    return manifest_path, report_path, report


class GateEnforcementTests(unittest.TestCase):
    def test_positive_gate_1_and_gate_2_transitions_bind_hashes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gate-positive-") as temporary:
            run_dir = Path(temporary) / "run"
            make_gate_1_state(run_dir)
            state = workflow.run(args(run_dir, decision="APPROVE_CONSERVATIVE"))
            self.assertEqual(state["state"], "PNG_DIRECTION")
            self.assertIn("gate_1_approval", state["provenance"])

            candidate = run_dir / "generation/candidates/candidate-a.png"
            png(candidate)
            state = workflow.run(args(
                run_dir, register_png=[candidate], candidate_sha256=[sha256_file(candidate)],
                generation_call_id=["image-call-1"],
            ))
            self.assertEqual(state["state"], "GATE_2_PNG_VISUAL_DIRECTION")
            self.assertEqual(state["provenance"]["image_generation_calls"], 1)
            self.assertEqual(
                state["provenance"]["registered_candidates"][0]["provenance_assurance"],
                "operator_attested_not_independently_verified",
            )

            state = workflow.run(args(
                run_dir, decision="APPROVE_PNG", selected_candidate="candidate-a",
                selected_candidate_sha256=sha256_file(candidate),
            ))
            self.assertEqual(state["state"], "SEMANTIC_BUILD")
            self.assertEqual(state["provenance"]["selected_candidate"]["sha256"], sha256_file(candidate))

    def test_missing_gate_1_blocks_candidate_registration(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gate1-missing-") as temporary:
            run_dir = Path(temporary) / "run"
            run_dir.mkdir()
            state = workflow.initial_state(run_dir, REPOSITORY_ROOT, [], "sketch")
            state["state"] = "PNG_DIRECTION"
            state["gate_status"]["gate_1"] = "approved"
            write_json(run_dir / "run_state.json", state)
            with self.assertRaisesRegex(ValueError, "incompatible|security invariant"):
                workflow.run(args(run_dir))
            self.assertFalse((run_dir / "generation").exists())
            self.assertEqual(json.loads((run_dir / "run_state.json").read_text())["provenance"]["image_generation_calls"], 0)

    def test_gate_1_approved_files_are_rechecked_on_every_resume(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gate1-evidence-loss-") as temporary:
            run_dir = Path(temporary) / "run"
            make_gate_1_state(run_dir)
            workflow.run(args(run_dir, decision="APPROVE_CONSERVATIVE"))
            (run_dir / "editorial/figure_editorial_review.json").unlink()
            with self.assertRaisesRegex(ValueError, "scientific interpretation|security invariant"):
                workflow.run(args(run_dir))

    def test_external_or_wrong_candidate_cannot_pass_gate_2(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gate2-wrong-") as temporary:
            root = Path(temporary)
            run_dir = root / "run"
            make_gate_1_state(run_dir)
            workflow.run(args(run_dir, decision="APPROVE_CONSERVATIVE"))
            external = root / "arbitrary.png"
            png(external)
            with self.assertRaisesRegex(ValueError, "inside run directory|generation/candidates"):
                workflow.run(args(
                    run_dir, register_png=[external], candidate_sha256=[sha256_file(external)],
                    generation_call_id=["image-call-1"],
                ))

            _, candidate = advance_to_gate_2(root / "second-run")
            second = root / "second-run"
            with self.assertRaisesRegex(ValueError, "exactly one registered"):
                workflow.run(args(
                    second, decision="APPROVE_PNG", selected_candidate="not-registered",
                    selected_candidate_sha256=sha256_file(candidate),
                ))
            with self.assertRaisesRegex(ValueError, "does not match"):
                workflow.run(args(
                    second, decision="APPROVE_PNG", selected_candidate="candidate-a",
                    selected_candidate_sha256="0" * 64,
                ))
            self.assertEqual(json.loads((second / "run_state.json").read_text())["state"], "GATE_2_PNG_VISUAL_DIRECTION")

    def test_arbitrary_delivery_cannot_reach_gate_3(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gate3-arbitrary-") as temporary:
            run_dir = Path(temporary) / "run"
            advance_to_semantic_build(run_dir)
            dummy = run_dir / "dummy.txt"
            dummy.write_text("not a delivery", encoding="utf-8")
            with mock.patch.object(workflow, "validate_delivery", return_value={"status": "BLOCKED"}):
                with self.assertRaisesRegex(ValueError, "canonical semantic source|delivery manifest"):
                    workflow.run(args(run_dir, register_delivery=[dummy]))
            self.assertEqual(json.loads((run_dir / "run_state.json").read_text())["state"], "SEMANTIC_BUILD")

    def test_fake_verified_report_is_rejected_by_fresh_validation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gate3-fake-report-") as temporary:
            run_dir = Path(temporary) / "run"
            advance_to_semantic_build(run_dir)
            manifest, report, _ = make_delivery(run_dir)
            with mock.patch.object(
                workflow, "validate_delivery", return_value={"status": "BLOCKED"}
            ) as validator:
                with self.assertRaisesRegex(ValueError, "fresh cross-format validation"):
                    workflow.run(args(run_dir, register_delivery=[manifest, report]))
            validator.assert_called_once_with(run_dir.resolve())
            self.assertEqual(json.loads((run_dir / "run_state.json").read_text())["gate_status"]["gate_3"], "not_reached")

    def test_delivery_must_bind_gate_1_and_selected_gate_2_candidate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gate-delivery-binding-") as temporary:
            run_dir = Path(temporary) / "run"
            advance_to_semantic_build(run_dir)
            manifest, report_path, report = make_delivery(run_dir)
            semantic_path = run_dir / "source/semantic_figure.json"
            semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
            semantic["provenance"]["source_hashes"]["approved_png_direction"] = "0" * 64
            write_json(semantic_path, semantic)
            with mock.patch.object(workflow, "validate_delivery", return_value=report) as validator:
                with self.assertRaisesRegex(ValueError, "not bound to Gate 1/Gate 2"):
                    workflow.run(args(run_dir, register_delivery=[manifest, report_path]))
            validator.assert_not_called()

    def test_real_semantic_builder_emits_gate_approval_bindings(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gate-builder-contract-") as temporary:
            run_dir = Path(temporary) / "run"
            state, candidate = advance_to_semantic_build(run_dir)
            approval = state["provenance"]["gate_1_approval"]
            scientific_interpretation = run_dir / approval["scientific_interpretation"]["path"]
            approved_wireframe = run_dir / approval["interpretation"]["path"]
            build_semantic_source(
                REPOSITORY_ROOT / "tests/fixtures/generic_semantic_pass.svg",
                REPOSITORY_ROOT / "tests/fixtures/generic_svg_fixture_spec.json",
                run_dir,
                truth_path=scientific_interpretation,
                scientific_interpretation_path=scientific_interpretation,
                wireframe_path=approved_wireframe,
                candidate_path=candidate,
            )
            semantic = json.loads(
                (run_dir / "source/semantic_figure.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                semantic["provenance"]["source_hashes"],
                {
                    "semantic_svg": sha256_file(
                        REPOSITORY_ROOT / "tests/fixtures/generic_semantic_pass.svg"
                    ),
                    "reconstruction_spec": sha256_file(
                        REPOSITORY_ROOT / "tests/fixtures/generic_svg_fixture_spec.json"
                    ),
                    "scientific_truth": approval["scientific_interpretation"]["sha256"],
                    "gate_1_scientific_interpretation": approval["scientific_interpretation"]["sha256"],
                    "approved_wireframe": approval["interpretation"]["sha256"],
                    "approved_png_direction": state["provenance"]["selected_candidate"]["sha256"],
                },
            )
            manifest, report_path, report = make_delivery(
                run_dir, preserve_semantic=True
            )
            with mock.patch.object(workflow, "validate_delivery", return_value=report):
                state = workflow.run(
                    args(run_dir, register_delivery=[manifest, report_path])
                )
            self.assertEqual(state["state"], "GATE_3_FINAL_SCIENTIFIC_DELIVERY")

    def test_fresh_hash_mutation_is_not_rebound_or_committed(self) -> None:
        target_paths = (
            "source/semantic_figure.json",
            "delivery/svg/master.svg",
            "validation/cross_format_preview.png",
        )
        for target_path in target_paths:
            with self.subTest(target=target_path), tempfile.TemporaryDirectory(
                prefix="gate3-hash-race-"
            ) as temporary:
                run_dir = Path(temporary) / "run"
                advance_to_semantic_build(run_dir)
                manifest, report_path, report = make_delivery(run_dir)
                target = (run_dir / target_path).resolve()
                original_sha256 = workflow.sha256_file
                mutated = False

                def mutate_after_first_hash(path: Path) -> str:
                    nonlocal mutated
                    digest = original_sha256(path)
                    if Path(path).resolve() == target and not mutated:
                        target.write_bytes(b"changed after fresh validation\n")
                        mutated = True
                    return digest

                with mock.patch.object(
                    workflow, "validate_delivery", return_value=report
                ), mock.patch.object(
                    workflow, "sha256_file", side_effect=mutate_after_first_hash
                ):
                    with self.assertRaisesRegex(
                        ValueError, "validated delivery artifact hash changed"
                    ):
                        workflow.run(
                            args(run_dir, register_delivery=[manifest, report_path])
                        )
                self.assertTrue(mutated)
                persisted = json.loads(
                    (run_dir / "run_state.json").read_text(encoding="utf-8")
                )
                self.assertEqual(persisted["state"], "SEMANTIC_BUILD")
                self.assertEqual(persisted["gate_status"]["gate_3"], "not_reached")

    def test_validation_stops_at_gate_3_until_explicit_final_approval(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gate3-positive-") as temporary:
            run_dir = Path(temporary) / "run"
            advance_to_semantic_build(run_dir)
            manifest, report_path, report = make_delivery(run_dir)
            with mock.patch.object(workflow, "validate_delivery", return_value=report):
                state = workflow.run(args(run_dir, register_delivery=[manifest, report_path]))
                self.assertEqual(state["state"], "GATE_3_FINAL_SCIENTIFIC_DELIVERY")
                self.assertEqual(state["gate_status"]["gate_3"], "awaiting_human")
                state = workflow.run(args(run_dir, decision="APPROVE_FINAL"))
            self.assertEqual(state["state"], "COMPLETE")
            self.assertEqual(state["gate_status"]["gate_3"], "approved")

    def test_gate_3_revision_returns_to_delivery_build(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gate3-revision-") as temporary:
            run_dir = Path(temporary) / "run"
            advance_to_semantic_build(run_dir)
            manifest, report_path, report = make_delivery(run_dir)
            with mock.patch.object(workflow, "validate_delivery", return_value=report):
                workflow.run(args(run_dir, register_delivery=[manifest, report_path]))
            state = workflow.run(args(run_dir, decision="REVISE_DELIVERY"))
            self.assertEqual(state["state"], "DELIVERY_BUILD")
            self.assertEqual(state["gate_status"]["gate_3"], "not_reached")
            self.assertNotIn("delivery_validation", state["provenance"])

    def test_inconsistent_complete_state_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="complete-inconsistent-") as temporary:
            run_dir = Path(temporary) / "run"
            run_dir.mkdir()
            state = workflow.initial_state(run_dir, REPOSITORY_ROOT, [], "sketch")
            state["state"] = "COMPLETE"
            write_json(run_dir / "run_state.json", state)
            with self.assertRaisesRegex(ValueError, "incompatible|inconsistent gate statuses"):
                workflow.run(args(run_dir))
            self.assertTrue(validate_schema(state, "run_state.schema.json"))

    def test_missing_initial_inputs_leave_no_run_state(self) -> None:
        with tempfile.TemporaryDirectory(prefix="missing-inputs-") as temporary:
            run_dir = Path(temporary) / "run"
            with self.assertRaisesRegex(ValueError, "--visual-plan"):
                workflow.run(args(run_dir, resume=False))
            self.assertFalse((run_dir / "run_state.json").exists())
            self.assertFalse(run_dir.exists())

    def test_draft_visual_plan_fails_schema(self) -> None:
        draft = {
            "schema_version": "1.0", "case_id": "draft", "visual_mode": "guided_redesign",
            "status": "draft", "spatial_locks": ["one"], "allowed_changes": [],
            "forbidden_visual_grammars": ["dashboard"], "text_policy": {},
            "wireframe_artifacts": {"wireframe_svg": "a.svg", "wireframe_png": "a.png"},
            "approval_gate": {
                "image_generation_authorized": True, "approved_wireframe_revision": 1,
                "approved_wireframe_sha256": "0" * 64,
            },
        }
        self.assertTrue(validate_schema(draft, "visual_plan.schema.json"))


if __name__ == "__main__":
    unittest.main()
