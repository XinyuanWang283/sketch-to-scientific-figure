#!/usr/bin/env python3
"""Tests for the additive, local-only ImageGen artifact ledger."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from PIL import Image


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPOSITORY_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import imagegen_workflow as workflow  # noqa: E402


class ImageGenWorkflowTests(unittest.TestCase):
    def make_png(self, path: Path, color: tuple[int, int, int]) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (32, 20), color).save(path, format="PNG")
        return path

    def initialize(self, root: Path) -> tuple[Path, Path]:
        sketch = self.make_png(root / "input" / "sketch.png", (255, 255, 255))
        run_dir = root / "run"
        state = workflow.initialize_run(
            run_dir,
            sketch,
            (
                "Preserve the confirmed left-to-right scientific topology and exact labels. "
                "Prepare five visually distinct directions for a landscape presentation figure."
            ),
        )
        self.assertEqual(state["stage"], "CLARIFICATION_COMPLETE")
        return run_dir, sketch

    def candidate_files(self, root: Path, count: int = 5) -> list[Path]:
        return [
            self.make_png(
                root / "generated" / f"candidate-{index + 1}.png",
                ((index + 1) * 30, 40, 120),
            )
            for index in range(count)
        ]

    def register_pool(self, root: Path, run_dir: Path) -> dict[str, object]:
        return workflow.register_candidates(
            run_dir,
            self.candidate_files(root),
            [f"codex-imagegen-call-{index + 1}" for index in range(5)],
            "test operator",
        )

    def select_publication(self, run_dir: Path, state: dict[str, object]) -> dict[str, object]:
        candidate = state["candidate_pool"][1]  # type: ignore[index]
        return workflow.select_candidate(
            run_dir,
            "B",
            "B-publication",
            candidate["sha256"],  # type: ignore[index]
            "researcher@example.test",
        )

    def select_d_layout_c_style(
        self, run_dir: Path, state: dict[str, object]
    ) -> dict[str, object]:
        presentation = state["candidate_pool"][2]  # type: ignore[index]
        alternative_layout = state["candidate_pool"][3]  # type: ignore[index]
        return workflow.select_combination(
            run_dir,
            "D",
            "D-alternative-layout",
            alternative_layout["sha256"],  # type: ignore[index]
            "C",
            "C-presentation",
            presentation["sha256"],  # type: ignore[index]
            "researcher@example.test",
        )

    def approve_region_map(
        self, root: Path, run_dir: Path, state: dict[str, object]
    ) -> dict[str, object]:
        region_map = root / "approved-region-map.json"
        region_map.write_text(
            json.dumps({"case_id": "test-case", "regions": [{"id": "main"}]}),
            encoding="utf-8",
        )
        selected = state["selected_candidate"]
        approval = root / "region-map-approval.json"
        approval.write_text(
            json.dumps(
                {
                    "decision": "APPROVE_REGION_MAP_FOR_RECONSTRUCTION",
                    "case_id": "test-case",
                    "delivery_revision": "test-revision",
                    "recipe_id": "test-recipe",
                    "selected_candidate": {
                        key: selected[key]  # type: ignore[index]
                        for key in ("slot", "candidate_id", "sha256")
                    },
                    "region_map_sha256": workflow.sha256_file(region_map),
                    "operator": "researcher@example.test",
                    "scientific_approval_created": False,
                }
            ),
            encoding="utf-8",
        )
        return workflow.register_region_map_approval(
            run_dir,
            region_map=region_map,
            approval_record=approval,
        )

    def delivery_files(self, run_dir: Path) -> dict[str, Path]:
        delivery = run_dir / "delivery"
        delivery.mkdir(parents=True, exist_ok=True)
        paths = {
            "svg": delivery / "figure.svg",
            "pptx": delivery / "figure.pptx",
            "drawio": delivery / "figure.drawio",
            "pdf_preview": delivery / "figure-preview.pdf",
            "validation_report": delivery / "validation-report.json",
            "artifact_manifest": delivery / "artifact-manifest.json",
        }
        paths["svg"].write_text(
            '<svg xmlns="http://www.w3.org/2000/svg"><text>synthetic</text></svg>\n',
            encoding="utf-8",
        )
        paths["pptx"].write_bytes(b"synthetic-pptx-test-evidence\n")
        paths["drawio"].write_text("<mxGraphModel/>\n", encoding="utf-8")
        paths["pdf_preview"].write_bytes(b"%PDF-1.4\nsynthetic-preview\n")
        _, state = workflow.load_state(run_dir)
        selected = state["selected_candidate"]
        selection_record = state["candidate_selection_approval"]
        region = state["approved_region_map"]
        output_keys = ("svg", "pptx", "drawio", "pdf_preview")
        output_hashes = {key: workflow.sha256_file(paths[key]) for key in output_keys}
        report = {
            "schema_version": "1.0",
            "report_type": "structural_delivery_validation",
            "status": "PASSED",
            "case_id": region["case_id"],  # type: ignore[index]
            "delivery_revision": region["delivery_revision"],  # type: ignore[index]
            "input_hashes": {
                "candidate_sha256": selected["sha256"],  # type: ignore[index]
                "candidate_selection_sha256": selection_record["sha256"],  # type: ignore[index]
                "region_map_sha256": region["region_map"]["sha256"],  # type: ignore[index]
            },
            "output_hashes": output_hashes,
            "checks": {
                "structure": {"passed": True},
                "approved_raster_atoms": {"passed": True},
            },
            "overall_pass": True,
            "scientific_correctness_checked": False,
            "validator": {
                "name": "synthetic-test-validator",
                "version": "1.0",
                "code_sha256": "a" * 64,
            },
        }
        paths["validation_report"].write_text(json.dumps(report), encoding="utf-8")
        manifest = {
            "schema_version": "1.0",
            "manifest_type": "editable_delivery_artifact_manifest",
            "case_id": region["case_id"],  # type: ignore[index]
            "delivery_revision": region["delivery_revision"],  # type: ignore[index]
            "scientific_correctness_checked": False,
            "validation_report": {
                "path": paths["validation_report"].relative_to(run_dir).as_posix(),
                "sha256": workflow.sha256_file(paths["validation_report"]),
            },
            "artifacts": {
                key: {
                    "path": paths[key].relative_to(run_dir).as_posix(),
                    "sha256": output_hashes[key],
                    "media_type": f"application/x-test-{key}",
                    "editability": "synthetic test classification",
                    "structural_summary": "Synthetic test artifact.",
                    "approved_raster_sidecars": [],
                }
                for key in output_keys
            },
        }
        paths["artifact_manifest"].write_text(json.dumps(manifest), encoding="utf-8")
        return paths

    def register_delivery(self, root: Path, run_dir: Path) -> dict[str, object]:
        _, state = workflow.load_state(run_dir)
        if state["stage"] == "CANDIDATE_APPROVED":
            self.approve_region_map(root, run_dir, state)
        paths = self.delivery_files(run_dir)
        return workflow.register_delivery(run_dir, **paths)

    def approve_visual(self, root: Path, run_dir: Path) -> dict[str, object]:
        _, state = workflow.load_state(run_dir)
        approval = root / "visual-approval.json"
        approval.write_text(
            json.dumps(
                {
                    "decision": "APPROVE_VISUAL_DELIVERY",
                    "case_id": state["delivery"]["case_id"],  # type: ignore[index]
                    "delivery_revision": state["delivery"]["delivery_revision"],  # type: ignore[index]
                    "artifact_manifest_sha256": state["delivery"]["artifact_manifest"]["sha256"],  # type: ignore[index]
                    "operator": "researcher@example.test",
                    "scientific_approval_created": False,
                    "science_day_use_approval_created": False,
                    "public_release_approval_created": False,
                }
            ),
            encoding="utf-8",
        )
        return workflow.register_visual_approval(run_dir, approval)

    def test_happy_path_records_five_stages_and_immutable_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="imagegen-ledger-happy-") as temporary:
            root = Path(temporary)
            run_dir, _ = self.initialize(root)
            state = self.register_pool(root, run_dir)
            self.assertEqual(state["stage"], "CANDIDATES_REGISTERED")

            state = self.select_publication(run_dir, state)
            self.assertEqual(state["stage"], "CANDIDATE_APPROVED")
            self.assertTrue((run_dir / workflow.CANDIDATE_APPROVAL_PATH).is_file())

            state = self.register_delivery(root, run_dir)
            self.assertEqual(state["stage"], "DELIVERY_REGISTERED")
            self.assertIsNone(state["final_delivery_approval"])

            state = self.approve_visual(root, run_dir)
            self.assertEqual(state["stage"], "VISUAL_APPROVED")

            state = workflow.approve_final_delivery(
                run_dir,
                "researcher@example.test",
                "I reviewed the editable delivery and approve its scientific presentation.",
            )
            self.assertEqual(state["stage"], "FINAL_APPROVED")
            self.assertEqual(state["revision"], 7)
            self.assertEqual(len(state["history"]), 7)
            self.assertEqual(
                len(list((run_dir / workflow.STATE_HISTORY_DIRECTORY).glob("*.json"))),
                7,
            )
            _, reloaded = workflow.load_state(run_dir)
            self.assertEqual(reloaded, state)

    def test_missing_or_empty_clarification_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="imagegen-ledger-clarification-") as temporary:
            root = Path(temporary)
            sketch = self.make_png(root / "sketch.png", (255, 255, 255))
            for index, brief in enumerate((None, "", "   \n")):
                with self.subTest(brief=brief):
                    with self.assertRaisesRegex(ValueError, "clarification brief.*non-empty"):
                        workflow.initialize_run(
                            root / f"run-{index}", sketch, brief  # type: ignore[arg-type]
                        )
                    self.assertFalse((root / f"run-{index}").exists())

    def test_initialize_refuses_to_overwrite_an_existing_run(self) -> None:
        with tempfile.TemporaryDirectory(prefix="imagegen-ledger-existing-") as temporary:
            root = Path(temporary)
            run_dir, sketch = self.initialize(root)
            with self.assertRaisesRegex(ValueError, "refusing to overwrite existing run"):
                workflow.initialize_run(run_dir, sketch, "A second clarification brief")

    def test_shareable_ledger_imports_sources_and_uses_only_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory(prefix="imagegen-ledger-relative-") as temporary:
            root = Path(temporary)
            run_dir, sketch = self.initialize(root)
            state = self.register_pool(root, run_dir)

            serialized = json.dumps(state, sort_keys=True)
            self.assertNotIn(str(root), serialized)
            self.assertEqual(state["sketch"]["path"], "ledger/inputs/source_sketch.png")
            self.assertEqual(
                [item["path"] for item in state["candidate_pool"]],
                [f"ledger/candidates/{slot}.png" for slot in "ABCDE"],
            )
            self.assertEqual(
                (run_dir / state["sketch"]["path"]).read_bytes(),
                sketch.read_bytes(),
            )
            self.assertTrue(all(
                (run_dir / item["path"]).is_file()
                for item in state["candidate_pool"]
            ))
            current_text = (run_dir / workflow.STATE_FILENAME).read_text(encoding="utf-8")
            history_text = "".join(
                item.read_text(encoding="utf-8")
                for item in sorted((run_dir / workflow.STATE_HISTORY_DIRECTORY).glob("*.json"))
            )
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(
                    workflow.main(["show", "--run-dir", str(run_dir)]),
                    0,
                )
            self.assertNotIn(str(root), current_text)
            self.assertNotIn(str(root), history_text)
            self.assertNotIn(str(root), output.getvalue())

    def test_imported_sources_survive_original_removal_and_run_relocation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="imagegen-ledger-portable-") as temporary:
            root = Path(temporary)
            run_dir, sketch = self.initialize(root)
            candidates = self.candidate_files(root)
            workflow.register_candidates(
                run_dir,
                candidates,
                [f"portable-call-{index + 1}" for index in range(5)],
                "test operator",
            )
            sketch.unlink()
            for candidate in candidates:
                candidate.unlink()
            relocated = root / "relocated-run"
            run_dir.rename(relocated)
            resolved, state = workflow.load_state(relocated)
            self.assertEqual(resolved, relocated.resolve())
            self.assertEqual(state["stage"], "CANDIDATES_REGISTERED")

    def test_tampered_run_local_candidate_fails_hash_verification(self) -> None:
        with tempfile.TemporaryDirectory(prefix="imagegen-ledger-tamper-") as temporary:
            root = Path(temporary)
            run_dir, _ = self.initialize(root)
            state = self.register_pool(root, run_dir)
            candidate_path = run_dir / state["candidate_pool"][0]["path"]
            candidate_path.write_bytes(candidate_path.read_bytes() + b"tampered")
            with self.assertRaisesRegex(ValueError, "no longer matches.*SHA-256"):
                workflow.load_state(run_dir)

    def test_shareable_ledger_rejects_posix_windows_and_unc_absolute_paths(self) -> None:
        absolute_paths = (
            "/private-machine/sketch.png",
            "../sketch.png",
            "X:\\private-machine\\sketch.png",
            "X:private-machine/sketch.png",
            "\\\\server\\share\\sketch.png",
            "./sketch.png",
            "ledger//sketch.png",
            "ledger\\sketch.png",
        )
        for index, absolute_path in enumerate(absolute_paths):
            with self.subTest(path=absolute_path):
                with tempfile.TemporaryDirectory(
                    prefix=f"imagegen-ledger-absolute-{index}-"
                ) as temporary:
                    root = Path(temporary)
                    run_dir, _ = self.initialize(root)
                    current = run_dir / workflow.STATE_FILENAME
                    snapshot = run_dir / workflow.STATE_HISTORY_DIRECTORY / "0001.json"
                    state = json.loads(current.read_text(encoding="utf-8"))
                    state["sketch"]["path"] = absolute_path
                    encoded = json.dumps(state, indent=2, sort_keys=True) + "\n"
                    current.write_text(encoded, encoding="utf-8")
                    snapshot.write_text(encoded, encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "portable run-relative path"):
                        workflow.load_state(run_dir)

    def test_outside_or_symlink_escape_is_rejected_before_file_read(self) -> None:
        with tempfile.TemporaryDirectory(prefix="imagegen-ledger-containment-") as temporary:
            root = Path(temporary)
            run_dir = root / "run"
            run_dir.mkdir()
            external = root / "external.svg"
            external.write_text("<svg/>\n", encoding="utf-8")
            escape = run_dir / "escape.svg"
            escape.symlink_to(external)
            with mock.patch.object(
                workflow,
                "require_existing_file",
                side_effect=AssertionError("outside file must not be read"),
            ):
                with self.assertRaisesRegex(ValueError, "must be located inside run directory"):
                    workflow.require_inside_run(run_dir, external, "external artifact")
                with self.assertRaisesRegex(ValueError, "must be located inside run directory"):
                    workflow.require_inside_run(run_dir, escape, "symlink artifact")

    def test_four_or_six_candidates_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="imagegen-ledger-count-") as temporary:
            root = Path(temporary)
            run_dir, _ = self.initialize(root)
            for count in (4, 6):
                with self.subTest(count=count):
                    with self.assertRaisesRegex(ValueError, "exactly five PNG candidates"):
                        workflow.register_candidates(
                            run_dir,
                            self.candidate_files(root / f"case-{count}", count),
                            [f"call-{index}" for index in range(count)],
                            "test operator",
                        )
            _, state = workflow.load_state(run_dir)
            self.assertEqual(state["stage"], "CLARIFICATION_COMPLETE")

    def test_duplicate_or_empty_generation_event_ids_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="imagegen-ledger-calls-") as temporary:
            root = Path(temporary)
            run_dir, _ = self.initialize(root)
            candidates = self.candidate_files(root)
            with self.assertRaisesRegex(ValueError, "unique generation event IDs"):
                workflow.register_candidates(
                    run_dir,
                    candidates,
                    ["call-a", "call-b", "call-c", "call-d", "call-a"],
                    "test operator",
                )
            with self.assertRaisesRegex(ValueError, "generation event ID.*non-empty"):
                workflow.register_candidates(
                    run_dir,
                    candidates,
                    ["call-a", "call-b", "", "call-d", "call-e"],
                    "test operator",
                )

    def test_non_png_candidate_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="imagegen-ledger-non-png-") as temporary:
            root = Path(temporary)
            run_dir, _ = self.initialize(root)
            candidates = self.candidate_files(root)
            jpeg = root / "generated" / "candidate-3.jpg"
            Image.new("RGB", (32, 20), (10, 20, 30)).save(jpeg, format="JPEG")
            candidates[2] = jpeg
            with self.assertRaisesRegex(ValueError, "must use the .png extension"):
                workflow.register_candidates(
                    run_dir,
                    candidates,
                    [f"call-{index}" for index in range(5)],
                    "test operator",
                )

    def test_selection_packet_exposes_all_five_fixed_directions(self) -> None:
        with tempfile.TemporaryDirectory(prefix="imagegen-ledger-packet-") as temporary:
            root = Path(temporary)
            run_dir, _ = self.initialize(root)
            state = self.register_pool(root, run_dir)
            packet = state["selection_packet"]
            candidates = packet["candidates"]  # type: ignore[index]
            self.assertEqual(len(candidates), 5)
            self.assertEqual([item["slot"] for item in candidates], list("ABCDE"))
            self.assertEqual(
                [item["direction"] for item in candidates],
                ["faithful", "publication", "presentation", "alternative-layout", "visual-variant"],
            )
            self.assertEqual(len({item["generation_event_id"] for item in candidates}), 5)
            self.assertTrue(all(item["sha256"] for item in candidates))
            self.assertTrue(all(
                item["provenance_assurance"] == workflow.PROVENANCE_ASSURANCE
                for item in candidates
            ))

    def test_selection_rejects_wrong_hash_and_wrong_exact_id(self) -> None:
        with tempfile.TemporaryDirectory(prefix="imagegen-ledger-selection-") as temporary:
            root = Path(temporary)
            run_dir, _ = self.initialize(root)
            state = self.register_pool(root, run_dir)
            candidate = state["candidate_pool"][1]  # type: ignore[index]
            with self.assertRaisesRegex(ValueError, "SHA-256 does not match"):
                workflow.select_candidate(
                    run_dir,
                    "B",
                    "B-publication",
                    "0" * 64,
                    "researcher@example.test",
                )
            with self.assertRaisesRegex(ValueError, "ID does not match"):
                workflow.select_candidate(
                    run_dir,
                    "B",
                    "A-faithful",
                    candidate["sha256"],  # type: ignore[index]
                    "researcher@example.test",
                )
            self.assertFalse((run_dir / workflow.CANDIDATE_APPROVAL_PATH).exists())

    def test_combination_selection_binds_layout_and_visual_style_separately(self) -> None:
        with tempfile.TemporaryDirectory(prefix="imagegen-ledger-combination-") as temporary:
            root = Path(temporary)
            run_dir, _ = self.initialize(root)
            state = self.register_pool(root, run_dir)

            state = self.select_d_layout_c_style(run_dir, state)

            self.assertEqual(state["stage"], "CANDIDATE_APPROVED")
            self.assertIsNone(state["selected_candidate"])
            combination = state["selected_combination"]
            self.assertEqual(combination["layout_source"]["slot"], "D")  # type: ignore[index]
            self.assertEqual(
                combination["layout_source"]["candidate_id"],  # type: ignore[index]
                "D-alternative-layout",
            )
            self.assertEqual(combination["visual_style_source"]["slot"], "C")  # type: ignore[index]
            self.assertEqual(
                combination["visual_style_source"]["candidate_id"],  # type: ignore[index]
                "C-presentation",
            )
            packet = state["selection_packet"]
            self.assertEqual(
                packet["selected_slots"],  # type: ignore[index]
                {"layout_source": "D", "visual_style_source": "C"},
            )

            approval_path = run_dir / workflow.CANDIDATE_APPROVAL_PATH
            approval = json.loads(approval_path.read_text(encoding="utf-8"))
            self.assertEqual(approval["decision"], "APPROVE_IMAGEGEN_COMBINATION")
            self.assertEqual(approval["layout_source"]["sha256"], combination["layout_source"]["sha256"])  # type: ignore[index]
            self.assertEqual(
                approval["visual_style_source"]["sha256"],
                combination["visual_style_source"]["sha256"],  # type: ignore[index]
            )

            region_map = root / "combination-region-map.json"
            region_map.write_text("{}\n", encoding="utf-8")
            region_approval = root / "combination-region-approval.json"
            region_approval.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "supports one exact selected candidate"):
                workflow.register_region_map_approval(
                    run_dir,
                    region_map=region_map,
                    approval_record=region_approval,
                )

    def test_combination_selection_rejects_mismatched_source_bindings(self) -> None:
        with tempfile.TemporaryDirectory(prefix="imagegen-ledger-combination-invalid-") as temporary:
            root = Path(temporary)
            run_dir, _ = self.initialize(root)
            state = self.register_pool(root, run_dir)
            presentation = state["candidate_pool"][2]  # type: ignore[index]
            alternative_layout = state["candidate_pool"][3]  # type: ignore[index]

            with self.assertRaisesRegex(ValueError, "layout source SHA-256 does not match"):
                workflow.select_combination(
                    run_dir,
                    "D",
                    "D-alternative-layout",
                    "0" * 64,
                    "C",
                    "C-presentation",
                    presentation["sha256"],  # type: ignore[index]
                    "researcher@example.test",
                )
            with self.assertRaisesRegex(ValueError, "visual style source ID does not match"):
                workflow.select_combination(
                    run_dir,
                    "D",
                    "D-alternative-layout",
                    alternative_layout["sha256"],  # type: ignore[index]
                    "C",
                    "D-alternative-layout",
                    presentation["sha256"],  # type: ignore[index]
                    "researcher@example.test",
                )
            self.assertFalse((run_dir / workflow.CANDIDATE_APPROVAL_PATH).exists())
            _, reloaded = workflow.load_state(run_dir)
            self.assertEqual(reloaded["stage"], "CANDIDATES_REGISTERED")

    def test_delivery_is_blocked_before_candidate_approval(self) -> None:
        with tempfile.TemporaryDirectory(prefix="imagegen-ledger-delivery-block-") as temporary:
            root = Path(temporary)
            run_dir, _ = self.initialize(root)
            self.register_pool(root, run_dir)
            placeholder = run_dir / "not-created"
            paths = {
                "svg": placeholder.with_suffix(".svg"),
                "pptx": placeholder.with_suffix(".pptx"),
                "drawio": placeholder.with_suffix(".drawio"),
                "pdf_preview": placeholder.with_suffix(".pdf"),
                "validation_report": placeholder.with_suffix(".json"),
                "artifact_manifest": run_dir / "not-created-manifest.json",
            }
            with self.assertRaisesRegex(ValueError, "blocked until candidate and region-map approvals"):
                workflow.register_delivery(run_dir, **paths)
            _, state = workflow.load_state(run_dir)
            self.assertIsNone(state["delivery"])

    def test_final_approval_is_a_separate_operator_action(self) -> None:
        with tempfile.TemporaryDirectory(prefix="imagegen-ledger-final-separate-") as temporary:
            root = Path(temporary)
            run_dir, _ = self.initialize(root)
            state = self.register_pool(root, run_dir)
            self.select_publication(run_dir, state)
            state = self.register_delivery(root, run_dir)

            self.assertEqual(state["stage"], "DELIVERY_REGISTERED")
            self.assertIsNone(state["final_delivery_approval"])
            self.assertFalse((run_dir / workflow.FINAL_APPROVAL_PATH).exists())
            validation_path = run_dir / state["delivery"]["validation_report"]["path"]  # type: ignore[index]
            validation = json.loads(validation_path.read_text(encoding="utf-8"))
            self.assertFalse(validation["scientific_correctness_checked"])

            with self.assertRaisesRegex(ValueError, "requires registered structural evidence and visual approval"):
                workflow.approve_final_delivery(
                    run_dir,
                    "researcher@example.test",
                    "This must not bypass visual approval.",
                )
            self.approve_visual(root, run_dir)
            state = workflow.approve_final_delivery(
                run_dir,
                "researcher@example.test",
                "I explicitly approve this delivery after scientific review.",
            )
            approval_path = run_dir / workflow.FINAL_APPROVAL_PATH
            approval = json.loads(approval_path.read_text(encoding="utf-8"))
            self.assertEqual(state["stage"], "FINAL_APPROVED")
            self.assertEqual(approval["decision"], "APPROVE_FINAL_DELIVERY")
            self.assertFalse(approval["automated_validation_created_this_approval"])
            self.assertTrue(approval["scientific_acceptance_is_human_decision"])

    def test_delivery_registration_fails_closed_on_failed_or_missing_validation(self) -> None:
        for mode in ("failed", "missing"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory(
                prefix=f"imagegen-ledger-validation-{mode}-"
            ) as temporary:
                root = Path(temporary)
                run_dir, _ = self.initialize(root)
                state = self.register_pool(root, run_dir)
                state = self.select_publication(run_dir, state)
                self.approve_region_map(root, run_dir, state)
                paths = self.delivery_files(run_dir)
                if mode == "failed":
                    report = json.loads(paths["validation_report"].read_text(encoding="utf-8"))
                    report["checks"]["structure"]["passed"] = False
                    paths["validation_report"].write_text(json.dumps(report), encoding="utf-8")
                    expected = "non-passing check"
                else:
                    paths["validation_report"].unlink()
                    expected = "missing or is not a regular file"
                with self.assertRaisesRegex(ValueError, expected):
                    workflow.register_delivery(run_dir, **paths)
                _, reloaded = workflow.load_state(run_dir)
                self.assertEqual(reloaded["stage"], "REGION_MAP_APPROVED")
                self.assertIsNone(reloaded["delivery"])

    def test_delivery_manifest_cannot_claim_scientific_correctness(self) -> None:
        with tempfile.TemporaryDirectory(prefix="imagegen-ledger-manifest-science-") as temporary:
            root = Path(temporary)
            run_dir, _ = self.initialize(root)
            state = self.register_pool(root, run_dir)
            state = self.select_publication(run_dir, state)
            self.approve_region_map(root, run_dir, state)
            paths = self.delivery_files(run_dir)
            manifest = json.loads(paths["artifact_manifest"].read_text(encoding="utf-8"))
            manifest["scientific_correctness_checked"] = True
            paths["artifact_manifest"].write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "scientific-check boundary"):
                workflow.register_delivery(run_dir, **paths)

    def test_delivery_manifest_cannot_omit_approved_raster_sidecars(self) -> None:
        with tempfile.TemporaryDirectory(prefix="imagegen-ledger-raster-sidecars-") as temporary:
            root = Path(temporary)
            run_dir, _ = self.initialize(root)
            state = self.register_pool(root, run_dir)
            state = self.select_publication(run_dir, state)
            self.approve_region_map(root, run_dir, state)
            paths = self.delivery_files(run_dir)

            source_asset = run_dir / "source" / "raster_atoms" / "atom.png"
            svg_asset = run_dir / "delivery" / "svg" / "assets" / "atom.png"
            source_asset.parent.mkdir(parents=True)
            svg_asset.parent.mkdir(parents=True)
            source_asset.write_bytes(b"approved-raster-atom")
            svg_asset.write_bytes(source_asset.read_bytes())
            digest = workflow.sha256_file(source_asset)
            asset_manifest = run_dir / "source" / "asset_manifest.json"
            asset_manifest.write_text(
                json.dumps(
                    {
                        "assets": [
                            {
                                "path": "raster_atoms/atom.png",
                                "delivery_svg_path": "delivery/svg/assets/atom.png",
                                "sha256": digest,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            review = run_dir / "source" / "raster_atom_review_decision.json"
            review.write_text(json.dumps({"status": "APPROVED"}), encoding="utf-8")

            report = json.loads(paths["validation_report"].read_text(encoding="utf-8"))
            report["input_hashes"].update(
                {
                    "approved_raster_manifest_sha256": workflow.sha256_file(asset_manifest),
                    "raster_atom_review_decision_sha256": workflow.sha256_file(review),
                }
            )
            paths["validation_report"].write_text(json.dumps(report), encoding="utf-8")
            manifest = json.loads(paths["artifact_manifest"].read_text(encoding="utf-8"))
            manifest["validation_report"]["sha256"] = workflow.sha256_file(
                paths["validation_report"]
            )
            manifest["approved_raster_atoms"] = {
                "path": "source/asset_manifest.json",
                "sha256": workflow.sha256_file(asset_manifest),
            }
            manifest["raster_atom_review_decision"] = {
                "path": "source/raster_atom_review_decision.json",
                "sha256": workflow.sha256_file(review),
            }
            paths["artifact_manifest"].write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "do not exactly match"):
                workflow.register_delivery(run_dir, **paths)

    def test_region_map_hash_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="imagegen-ledger-region-hash-") as temporary:
            root = Path(temporary)
            run_dir, _ = self.initialize(root)
            state = self.register_pool(root, run_dir)
            state = self.select_publication(run_dir, state)
            region_map = root / "region-map.json"
            region_map.write_text("{}\n", encoding="utf-8")
            approval = root / "region-approval.json"
            approval.write_text(
                json.dumps(
                    {
                        "decision": "APPROVE_REGION_MAP_FOR_RECONSTRUCTION",
                        "case_id": "test-case",
                        "delivery_revision": "test-revision",
                        "recipe_id": "test-recipe",
                        "selected_candidate": {
                            key: state["selected_candidate"][key]  # type: ignore[index]
                            for key in ("slot", "candidate_id", "sha256")
                        },
                        "region_map_sha256": "0" * 64,
                        "scientific_approval_created": False,
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "SHA-256 does not match"):
                workflow.register_region_map_approval(
                    run_dir,
                    region_map=region_map,
                    approval_record=approval,
                )

    def test_delivery_artifacts_must_be_inside_the_run(self) -> None:
        with tempfile.TemporaryDirectory(prefix="imagegen-ledger-scoped-delivery-") as temporary:
            root = Path(temporary)
            run_dir, _ = self.initialize(root)
            state = self.register_pool(root, run_dir)
            state = self.select_publication(run_dir, state)
            self.approve_region_map(root, run_dir, state)
            paths = self.delivery_files(run_dir)
            external_svg = root / "outside.svg"
            external_svg.write_text("<svg/>\n", encoding="utf-8")
            paths["svg"] = external_svg
            with self.assertRaisesRegex(ValueError, "must be located inside run directory"):
                workflow.register_delivery(run_dir, **paths)

    def test_schema_is_valid_json_and_encodes_exact_five_pool(self) -> None:
        schema_path = REPOSITORY_ROOT / "schemas" / "imagegen_workflow_state.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        exact_pool = schema["definitions"]["exact_five_candidate_pool"]
        self.assertEqual(schema["properties"]["schema_version"]["const"], "1.1")
        self.assertEqual(exact_pool["minItems"], 5)
        self.assertEqual(exact_pool["maxItems"], 5)
        self.assertEqual(len(exact_pool["allOf"]), 5)
        self.assertIn("FINAL_APPROVED", schema["properties"]["stage"]["enum"])
        self.assertIn("REGION_MAP_APPROVED", schema["properties"]["stage"]["enum"])
        self.assertIn("VISUAL_APPROVED", schema["properties"]["stage"]["enum"])
        self.assertIn("generation_event_id", schema["definitions"]["candidate"]["required"])
        self.assertNotIn("native_tool_call_id", schema["definitions"]["candidate"]["required"])
        self.assertIn("artifact_manifest", schema["definitions"]["delivery"]["required"])
        self.assertIn("selected_combination", schema["properties"])
        self.assertIn("selected_combination", schema["required"])
        combination = schema["definitions"]["selected_combination"]
        self.assertEqual(
            set(combination["required"]),
            {"layout_source", "visual_style_source", "operator"},
        )
        self.assertIn("pattern", schema["definitions"]["relative_path"])

    def test_cli_exposes_hash_bound_combination_selection(self) -> None:
        args = workflow.build_parser().parse_args([
            "select-combination",
            "--run-dir", "/tmp/example-run",
            "--layout-slot", "D",
            "--layout-candidate-id", "D-alternative-layout",
            "--layout-sha256", "1" * 64,
            "--visual-style-slot", "C",
            "--visual-style-candidate-id", "C-presentation",
            "--visual-style-sha256", "2" * 64,
            "--operator", "researcher@example.test",
        ])
        self.assertEqual(args.command, "select-combination")
        self.assertEqual(args.layout_slot, "D")
        self.assertEqual(args.visual_style_slot, "C")

    def test_selection_event_rejects_rewritten_approved_candidate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="imagegen-ledger-rewritten-selection-") as temporary:
            root = Path(temporary)
            run_dir, _ = self.initialize(root)
            state = self.register_pool(root, run_dir)
            state = self.select_publication(run_dir, state)
            candidate_a = state["candidate_pool"][0]  # type: ignore[index]
            approval_path = run_dir / workflow.CANDIDATE_APPROVAL_PATH
            approval = json.loads(approval_path.read_text(encoding="utf-8"))
            approval.update(
                slot=candidate_a["slot"],
                candidate_id=candidate_a["candidate_id"],
                sha256=candidate_a["sha256"],
                generation_event_id=candidate_a["generation_event_id"],
            )
            approval_path.write_text(json.dumps(approval), encoding="utf-8")
            state["selected_candidate"].update(  # type: ignore[union-attr]
                slot=candidate_a["slot"],
                candidate_id=candidate_a["candidate_id"],
                sha256=candidate_a["sha256"],
            )
            state["selection_packet"]["selected_slot"] = "A"  # type: ignore[index]
            state["candidate_selection_approval"]["sha256"] = workflow.sha256_file(  # type: ignore[index]
                approval_path
            )
            encoded = json.dumps(state, indent=2, sort_keys=True) + "\n"
            (run_dir / workflow.STATE_FILENAME).write_text(encoded, encoding="utf-8")
            workflow.state_history_path(run_dir, 3).write_text(encoded, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "selection event"):
                workflow.load_state(run_dir)

    def test_later_snapshots_cannot_rewrite_registered_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="imagegen-ledger-evidence-freeze-") as temporary:
            root = Path(temporary)
            run_dir, _ = self.initialize(root)
            state = self.register_pool(root, run_dir)
            state = self.select_publication(run_dir, state)
            state["candidate_pool"][0]["design_note"] = "rewritten provenance"  # type: ignore[index]
            state["selection_packet"]["candidates"][0]["design_note"] = (  # type: ignore[index]
                "rewritten provenance"
            )
            encoded = json.dumps(state, indent=2, sort_keys=True) + "\n"
            (run_dir / workflow.STATE_FILENAME).write_text(encoded, encoding="utf-8")
            workflow.state_history_path(run_dir, 3).write_text(encoded, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "rewrote evidence"):
                workflow.load_state(run_dir)

    def test_later_snapshot_cannot_replace_approval_record_binding(self) -> None:
        with tempfile.TemporaryDirectory(prefix="imagegen-ledger-approval-freeze-") as temporary:
            root = Path(temporary)
            run_dir, _ = self.initialize(root)
            state = self.register_pool(root, run_dir)
            state = self.select_publication(run_dir, state)
            state = self.approve_region_map(root, run_dir, state)
            original = run_dir / workflow.CANDIDATE_APPROVAL_PATH
            replacement = run_dir / "ledger/approvals/copied-selection.json"
            replacement.parent.mkdir(parents=True, exist_ok=True)
            replacement.write_bytes(original.read_bytes())
            state["candidate_selection_approval"] = {  # type: ignore[assignment]
                "path": replacement.relative_to(run_dir).as_posix(),
                "sha256": workflow.sha256_file(replacement),
            }
            encoded = json.dumps(state, indent=2, sort_keys=True) + "\n"
            (run_dir / workflow.STATE_FILENAME).write_text(encoded, encoding="utf-8")
            workflow.state_history_path(run_dir, 4).write_text(encoded, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "rewrote evidence"):
                workflow.load_state(run_dir)


if __name__ == "__main__":
    unittest.main()
