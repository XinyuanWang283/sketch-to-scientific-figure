from __future__ import annotations

import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import replay_reference_case as replay  # noqa: E402


def write_json(path: Path, value: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def record(root: Path, path: Path) -> dict[str, str]:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": replay.sha256_file(path),
    }


class Fixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.package = root / "editable_delivery_c_fidelity_v2"
        self.builder_path = "scripts/build_deep_image_prior_c_fidelity_v2.py"
        self._build()

    def _build(self) -> None:
        sketch = self.root / "sketch.png"
        sketch.write_bytes(b"offline sketch")
        clarification = self.root / "clarification_brief.md"
        clarification.write_text("Preserve the fixed scientific topology.\n", encoding="utf-8")

        candidates: list[dict[str, object]] = []
        manifest_candidates: list[dict[str, str]] = []
        for index, (slot, candidate_id) in enumerate(replay.EXPECTED_CANDIDATES.items()):
            path = self.root / "candidates" / f"{candidate_id}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(f"candidate-{slot}".encode())
            binding = record(self.root, path)
            candidates.append(
                {
                    "slot": slot,
                    "candidate_id": candidate_id,
                    **binding,
                    "generation_event_id": f"offline-event-{slot}",
                    "design_note": f"Fixed direction {slot}",
                    "registered_at": f"2026-08-2{index}T00:00:00+00:00",
                    "provenance_status": replay.CANDIDATE_PROVENANCE_STATUS,
                }
            )
            manifest_candidates.append({"slot": slot, **binding})
        candidate_manifest_path = write_json(
            self.root / "candidate_manifest.json", {"candidates": manifest_candidates}
        )

        candidate_c = next(item for item in candidates if item["slot"] == "C")
        selection_path = write_json(
            self.root / "candidate_selection_c_only.json",
            {
                "decision": "APPROVE_IMAGEGEN_CANDIDATE",
                "status": "approved_for_editable_reconstruction",
                "editable_reconstruction_authorized": True,
                "final_scientific_approval": None,
                "selected_candidate": {
                    "slot": "C",
                    "candidate_id": "C-presentation",
                    "sha256": candidate_c["sha256"],
                },
            },
        )
        region_map_path = write_json(
            self.package / "source" / "selected_candidate_map.json",
            {"candidate_id": "C-presentation", "image_hash": candidate_c["sha256"]},
        )
        region_approval_path = write_json(
            self.root / "reference_case_v0_1_region_map_approval.json",
            {
                "schema_version": "1.0",
                "decision": "APPROVE_REGION_MAP_FOR_RECONSTRUCTION",
                "case_id": replay.CASE_ID,
                "delivery_revision": replay.DELIVERY_REVISION,
                "selected_candidate": {
                    "slot": "C",
                    "candidate_id": "C-presentation",
                    "sha256": candidate_c["sha256"],
                },
                "region_map_sha256": replay.sha256_file(region_map_path),
                "recipe_id": replay.RECIPE_ID,
                "operator": "fixture operator",
                "approved_at": "2026-08-29T00:00:00+00:00",
                "scientific_approval_created": False,
            },
        )
        source_raster = self.package / "source" / "raster_atoms" / "atom.png"
        delivery_raster = self.package / "delivery" / "svg" / "assets" / "atom.png"
        source_raster.parent.mkdir(parents=True, exist_ok=True)
        delivery_raster.parent.mkdir(parents=True, exist_ok=True)
        source_raster.write_bytes(b"approved-raster-atom")
        delivery_raster.write_bytes(source_raster.read_bytes())
        raster_digest = replay.sha256_file(source_raster)
        raster_asset_manifest_path = write_json(
            self.package / "source" / "asset_manifest.json",
            {
                "schema_version": "1.0",
                "assets": [
                    {
                        "path": "raster_atoms/atom.png",
                        "delivery_svg_path": "delivery/svg/assets/atom.png",
                        "sha256": raster_digest,
                    }
                ],
            },
        )
        raster_review_path = write_json(
            self.package / "source" / "raster_atom_review_decision.json",
            {
                "schema_version": "1.0",
                "status": "APPROVED_FOR_REVIEW_DRAFT_ONLY",
            },
        )

        artifact_paths = {
            "svg": self.package / "delivery" / "svg" / "master.svg",
            "pptx": self.package / "delivery" / "pptx" / "figure.pptx",
            "drawio": self.package / "delivery" / "drawio" / "figure.drawio",
            "pdf_preview": self.package / "delivery" / "pdf" / "publication.pdf",
        }
        for key, path in artifact_paths.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(f"frozen-{key}".encode())
        validation_path = write_json(
            self.package / "validation" / "fidelity_v2_validation_report.json",
            {"status": replay.VALIDATOR_STATUS},
        )
        output_hashes = {
            key: replay.sha256_file(path) for key, path in artifact_paths.items()
        }
        strong_report_path = write_json(
            self.root / "reference_case_v0_1_validation_report.json",
            {
                "schema_version": "1.0",
                "report_type": "structural_delivery_validation",
                "status": "PASSED",
                "case_id": replay.CASE_ID,
                "delivery_revision": replay.DELIVERY_REVISION,
                "input_hashes": {
                    "candidate_sha256": candidate_c["sha256"],
                    "candidate_selection_sha256": replay.sha256_file(selection_path),
                    "region_map_sha256": replay.sha256_file(region_map_path),
                    "approved_raster_manifest_sha256": replay.sha256_file(
                        raster_asset_manifest_path
                    ),
                    "raster_atom_review_decision_sha256": replay.sha256_file(
                        raster_review_path
                    ),
                },
                "output_hashes": output_hashes,
                "checks": {
                    "reference_case_integrity": {"passed": True},
                    "artifact_manifest_integrity": {"passed": True},
                    "fidelity_v2_package": {
                        "passed": True,
                        "status": replay.VALIDATOR_STATUS,
                        "validator_checks": {"fixture_check": True},
                    },
                },
                "overall_pass": True,
                "scientific_correctness_checked": False,
                "validator": {
                    "name": replay.VALIDATOR_NAME,
                    "version": replay.VALIDATOR_VERSION,
                    "code_sha256": replay.sha256_file(ROOT / self.builder_path),
                },
            },
        )
        artifact_manifest: dict[str, object] = {
            "schema_version": "1.0",
            "manifest_type": "editable_delivery_artifact_manifest",
            "case_id": replay.CASE_ID,
            "delivery_revision": replay.DELIVERY_REVISION,
            "canonical_root": self.package.name,
            "scientific_correctness_checked": False,
            "validation_report": record(self.root, strong_report_path),
            "approved_raster_atoms": record(self.package, raster_asset_manifest_path),
            "raster_atom_review_decision": record(self.package, raster_review_path),
            "artifacts": {},
        }
        artifact_items = artifact_manifest["artifacts"]
        assert isinstance(artifact_items, dict)
        for key, path in artifact_paths.items():
            if key == "svg":
                sidecars = [record(self.package, delivery_raster)]
            elif key in {"pptx", "drawio"}:
                sidecars = [record(self.package, source_raster)]
            else:
                sidecars = []
            artifact_items[key] = {
                **record(self.package, path),
                "media_type": "application/octet-stream",
                "editability": "fixture editability declaration",
                "structural_summary": "fixture structural summary",
                "approved_raster_sidecars": sidecars,
            }
        artifact_manifest_path = write_json(
            self.root / replay.ARTIFACT_MANIFEST_FILENAME, artifact_manifest
        )
        visual_approval_path = write_json(
            self.root / "reference_case_v0_1_visual_approval.json",
            {
                "schema_version": "1.0",
                "decision": "APPROVE_VISUAL_DELIVERY",
                "case_id": replay.CASE_ID,
                "delivery_revision": replay.DELIVERY_REVISION,
                "artifact_manifest_sha256": replay.sha256_file(artifact_manifest_path),
                "canonical_artifact_hashes": output_hashes,
                "operator": "fixture operator",
                "approved_at": "2026-08-29T00:00:00+00:00",
                "provenance": "offline frozen reference artifacts",
                "known_limitations": ["Scientific correctness remains pending."],
                "scientific_approval_created": False,
                "science_day_use_approval_created": False,
                "public_release_approval_created": False,
            },
        )
        self.case: dict[str, object] = {
            "schema_version": "1.0",
            "case_id": replay.CASE_ID,
            "delivery_revision": replay.DELIVERY_REVISION,
            "input_sketch": record(self.root, sketch),
            "clarification": record(self.root, clarification),
            "candidate_manifest": record(self.root, candidate_manifest_path),
            "candidates": candidates,
            "selection": {
                "record": record(self.root, selection_path),
                "slot": "C",
                "candidate_id": "C-presentation",
                "sha256": candidate_c["sha256"],
            },
            "approved_region_map": {
                **record(self.root, region_map_path),
                "approval_record": record(self.root, region_approval_path),
            },
            "reconstruction": {
                "recipe_id": replay.RECIPE_ID,
                "builder_path": self.builder_path,
            },
            "approved_raster_atoms": {
                **record(self.root, raster_asset_manifest_path),
                "review_decision": record(self.root, raster_review_path),
            },
            "artifact_manifest": record(self.root, artifact_manifest_path),
            "validation_evidence": record(self.root, strong_report_path),
            "approvals": {
                "visual": {**record(self.root, visual_approval_path), "status": "APPROVED"},
                "scientific": {"status": "PENDING"},
                "science_day_use": {"status": "PENDING"},
                "public_release": {"status": "PENDING"},
            },
        }
        self.write_case()

    def write_case(self) -> None:
        write_json(self.root / replay.REFERENCE_CASE_FILENAME, self.case)

    def refresh_manifest_and_visual_hashes(self) -> None:
        manifest_path = self.root / replay.ARTIFACT_MANIFEST_FILENAME
        visual_path = self.root / "reference_case_v0_1_visual_approval.json"
        visual = json.loads(visual_path.read_text(encoding="utf-8"))
        visual["artifact_manifest_sha256"] = replay.sha256_file(manifest_path)
        write_json(visual_path, visual)
        artifact_binding = self.case["artifact_manifest"]
        approvals = self.case["approvals"]
        assert isinstance(artifact_binding, dict) and isinstance(approvals, dict)
        artifact_binding["sha256"] = replay.sha256_file(manifest_path)
        visual_binding = approvals["visual"]
        assert isinstance(visual_binding, dict)
        visual_binding["sha256"] = replay.sha256_file(visual_path)
        self.write_case()

    def refresh_validation_chain(self) -> None:
        report_path = self.root / replay.STRUCTURAL_VALIDATION_FILENAME
        manifest_path = self.root / replay.ARTIFACT_MANIFEST_FILENAME
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["validation_report"]["sha256"] = replay.sha256_file(report_path)
        write_json(manifest_path, manifest)
        validation_binding = self.case["validation_evidence"]
        assert isinstance(validation_binding, dict)
        validation_binding["sha256"] = replay.sha256_file(report_path)
        self.refresh_manifest_and_visual_hashes()


def passing_package_report(*args: object, **kwargs: object) -> dict[str, object]:
    return {
        "status": replay.VALIDATOR_STATUS,
        "checks": {"fixture_check": True},
    }


class FakeWorkflow:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.state: dict[str, object] = {}

    def initialize_run(self, run_dir: Path, sketch: Path, brief: str) -> dict[str, object]:
        self.calls.append("init")
        run_dir.mkdir()
        self.state = {"stage": "CLARIFICATION_COMPLETE", "revision": 1, "candidate_pool": []}
        return self.state

    def register_candidates(
        self,
        run_dir: Path,
        paths: list[Path],
        generation_event_ids: list[str],
        operator: str,
        native_tool_call_ids: list[str | None] | None = None,
    ) -> dict[str, object]:
        self.calls.append("candidates")
        pool = []
        for slot, source in zip(replay.EXPECTED_CANDIDATES, paths):
            destination = run_dir / "ledger" / "candidates" / f"{slot}.png"
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            pool.append({"slot": slot, "path": destination.relative_to(run_dir).as_posix()})
        self.state = {"stage": "CANDIDATES_REGISTERED", "revision": 2, "candidate_pool": pool}
        return self.state

    def select_candidate(self, *args: object, **kwargs: object) -> dict[str, object]:
        self.calls.append("select-C")
        self.state.update(stage="CANDIDATE_APPROVED", revision=3)
        return self.state

    def register_candidate_selection_approval(
        self, *args: object, **kwargs: object
    ) -> dict[str, object]:
        return self.select_candidate(*args, **kwargs)

    def register_region_map_approval(self, *args: object, **kwargs: object) -> dict[str, object]:
        self.calls.append("region-map")
        self.state.update(stage="REGION_MAP_APPROVED", revision=4)
        return self.state

    def register_delivery(self, *args: object, **kwargs: object) -> dict[str, object]:
        self.calls.append("delivery")
        self.state.update(stage="DELIVERY_REGISTERED", revision=5)
        return self.state

    def register_visual_approval(self, *args: object, **kwargs: object) -> dict[str, object]:
        self.calls.append("visual")
        self.state.update(stage="VISUAL_APPROVED", revision=6)
        return self.state


class ReferenceCaseReplayTests(unittest.TestCase):
    def make_fixture(self, parent: Path) -> Fixture:
        root = parent / "example"
        root.mkdir(parents=True)
        return Fixture(root)

    def test_validate_emits_strong_machine_report_without_writing_canonical(self) -> None:
        with tempfile.TemporaryDirectory(prefix="reference-replay-valid-") as temporary:
            fixture = self.make_fixture(Path(temporary))
            before = sorted(path.relative_to(fixture.root) for path in fixture.root.rglob("*"))
            with mock.patch.object(replay, "validate_package", side_effect=passing_package_report):
                reference = replay.inspect_reference_case(fixture.root)
                report = replay.build_validation_report(reference)
            after = sorted(path.relative_to(fixture.root) for path in fixture.root.rglob("*"))
            self.assertEqual(before, after)
            self.assertTrue(report["overall_pass"])
            self.assertFalse(report["scientific_correctness_checked"])
            self.assertEqual(report["report_type"], "structural_delivery_validation")
            self.assertEqual(set(report["output_hashes"]), set(replay.ARTIFACT_KEYS))
            self.assertEqual(report["validator"]["name"], replay.VALIDATOR_NAME)
            self.assertRegex(report["validator"]["code_sha256"], r"^[a-f0-9]{64}$")

    def test_replay_uses_offline_ledger_sequence_and_preserves_pending_gates(self) -> None:
        with tempfile.TemporaryDirectory(prefix="reference-replay-run-") as temporary:
            parent = Path(temporary)
            fixture = self.make_fixture(parent)
            output = parent / "external-run"
            fake = FakeWorkflow()
            with (
                mock.patch.object(replay, "validate_package", side_effect=passing_package_report),
                mock.patch.object(replay.imagegen_workflow, "initialize_run", fake.initialize_run),
                mock.patch.object(replay.imagegen_workflow, "register_candidates", fake.register_candidates),
                mock.patch.object(
                    replay.imagegen_workflow,
                    "register_candidate_selection_approval",
                    fake.register_candidate_selection_approval,
                    create=True,
                ),
                mock.patch.object(
                    replay.imagegen_workflow,
                    "register_region_map_approval",
                    fake.register_region_map_approval,
                    create=True,
                ),
                mock.patch.object(replay.imagegen_workflow, "register_delivery", fake.register_delivery),
                mock.patch.object(
                    replay.imagegen_workflow,
                    "register_visual_approval",
                    fake.register_visual_approval,
                    create=True,
                ),
            ):
                readiness = replay.replay_reference_case(fixture.root, output)
            self.assertEqual(
                fake.calls,
                ["init", "candidates", "select-C", "region-map", "delivery", "visual"],
            )
            self.assertEqual(readiness["imagegen_or_remote_calls"], 0)
            self.assertFalse(readiness["canonical_modified"])
            self.assertFalse(readiness["ready_for_scientific_use"])
            self.assertFalse(readiness["ready_for_science_day_use"])
            self.assertFalse(readiness["ready_for_public_release"])
            self.assertTrue((output / "reference_case_v0_1_readiness.json").is_file())
            self.assertTrue((output / replay.REPLAY_START_HERE_FILENAME).is_file())
            self.assertTrue(
                (output / "reference_case_v0_1_validation_report.json").is_file()
            )
            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                replay.replay_reference_case(fixture.root, output)

    def test_malformed_artifact_manifest_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="reference-replay-manifest-") as temporary:
            fixture = self.make_fixture(Path(temporary))
            path = fixture.root / replay.ARTIFACT_MANIFEST_FILENAME
            manifest = json.loads(path.read_text(encoding="utf-8"))
            del manifest["artifacts"]["pdf_preview"]
            write_json(path, manifest)
            fixture.refresh_manifest_and_visual_hashes()
            with self.assertRaisesRegex(ValueError, "must contain exactly"):
                replay.inspect_reference_case(fixture.root)

    def test_unsafe_and_symlink_paths_are_rejected_before_read(self) -> None:
        with tempfile.TemporaryDirectory(prefix="reference-replay-unsafe-") as temporary:
            parent = Path(temporary)
            fixture = self.make_fixture(parent)
            candidates = fixture.case["candidates"]
            assert isinstance(candidates, list) and isinstance(candidates[0], dict)
            candidates[0]["path"] = "../outside.png"
            fixture.write_case()
            with self.assertRaisesRegex(ValueError, "portable relative path"):
                replay.inspect_reference_case(fixture.root)

            fixture = self.make_fixture(parent / "second")
            candidate = fixture.root / "candidates" / "A-faithful.png"
            external = parent / "external.png"
            external.write_bytes(b"candidate-A")
            candidate.unlink()
            candidate.symlink_to(external)
            with self.assertRaisesRegex(ValueError, "symbolic link"):
                replay.inspect_reference_case(fixture.root)

    def test_hash_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="reference-replay-hash-") as temporary:
            fixture = self.make_fixture(Path(temporary))
            (fixture.root / "candidates" / "C-presentation.png").write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                replay.inspect_reference_case(fixture.root)

    def test_status_keeps_all_four_approvals_separate_and_pending(self) -> None:
        with tempfile.TemporaryDirectory(prefix="reference-replay-status-") as temporary:
            fixture = self.make_fixture(Path(temporary))
            output = io.StringIO()
            with redirect_stdout(output):
                code = replay.main(["status", "--example-root", str(fixture.root)])
            self.assertEqual(code, 0)
            status = json.loads(output.getvalue())
            self.assertEqual(status["case_integrity"]["status"], "VALID")
            self.assertEqual(status["approvals"]["visual"]["status"], "APPROVED")
            self.assertEqual(status["approvals"]["scientific"]["status"], "PENDING")
            self.assertEqual(status["approvals"]["science_day_use"]["status"], "PENDING")
            self.assertEqual(status["approvals"]["public_release"]["status"], "PENDING")

    def test_bare_human_approval_statuses_fail_closed(self) -> None:
        for approval_key in ("scientific", "science_day_use", "public_release"):
            with self.subTest(approval_key=approval_key), tempfile.TemporaryDirectory(
                prefix=f"reference-replay-approval-{approval_key}-"
            ) as temporary:
                fixture = self.make_fixture(Path(temporary))
                approvals = fixture.case["approvals"]
                assert isinstance(approvals, dict)
                approvals[approval_key] = {"status": "APPROVED"}
                fixture.write_case()
                with self.assertRaisesRegex(ValueError, "must remain PENDING"):
                    replay.inspect_reference_case(fixture.root)

    def test_raster_authorization_bindings_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="reference-replay-raster-binding-") as temporary:
            fixture = self.make_fixture(Path(temporary))
            approved = fixture.case["approved_raster_atoms"]
            assert isinstance(approved, dict)
            approved["sha256"] = "0" * 64
            fixture.write_case()
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                replay.inspect_reference_case(fixture.root)

    def test_validation_evidence_must_match_consumed_structural_report(self) -> None:
        with tempfile.TemporaryDirectory(prefix="reference-replay-validation-binding-") as temporary:
            fixture = self.make_fixture(Path(temporary))
            clarification = fixture.root / "clarification_brief.md"
            fixture.case["validation_evidence"] = record(fixture.root, clarification)
            fixture.write_case()
            with self.assertRaisesRegex(ValueError, "must exactly match"):
                replay.inspect_reference_case(fixture.root)

    def test_validator_identity_cannot_be_coherently_rebound(self) -> None:
        with tempfile.TemporaryDirectory(prefix="reference-replay-validator-identity-") as temporary:
            fixture = self.make_fixture(Path(temporary))
            reconstruction = fixture.case["reconstruction"]
            assert isinstance(reconstruction, dict)
            reconstruction["builder_path"] = "README.md"
            report_path = fixture.root / replay.STRUCTURAL_VALIDATION_FILENAME
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["validator"]["code_sha256"] = replay.sha256_file(ROOT / "README.md")
            write_json(report_path, report)
            fixture.refresh_validation_chain()
            with self.assertRaisesRegex(ValueError, "builder_path must be"):
                replay.inspect_reference_case(fixture.root)

    def test_manifest_semantics_and_sidecar_set_fail_closed(self) -> None:
        mutations = (
            ("scientific", lambda manifest: manifest.__setitem__("scientific_correctness_checked", True)),
            (
                "sidecars",
                lambda manifest: [
                    item.__setitem__("approved_raster_sidecars", [])
                    for item in manifest["artifacts"].values()
                ],
            ),
        )
        for label, mutate in mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory(
                prefix=f"reference-replay-manifest-{label}-"
            ) as temporary:
                fixture = self.make_fixture(Path(temporary))
                manifest_path = fixture.root / replay.ARTIFACT_MANIFEST_FILENAME
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                mutate(manifest)
                write_json(manifest_path, manifest)
                fixture.refresh_manifest_and_visual_hashes()
                expected = "must be false" if label == "scientific" else "exactly match"
                with self.assertRaisesRegex(ValueError, expected):
                    replay.inspect_reference_case(fixture.root)

    def test_candidate_provenance_overclaim_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="reference-replay-provenance-") as temporary:
            fixture = self.make_fixture(Path(temporary))
            candidates = fixture.case["candidates"]
            assert isinstance(candidates, list) and isinstance(candidates[0], dict)
            candidates[0]["provenance_status"] = "cryptographically_verified_backend"
            fixture.write_case()
            with self.assertRaisesRegex(ValueError, "provenance_status must be"):
                replay.inspect_reference_case(fixture.root)

    def test_visual_approval_output_hash_claim_must_match_manifest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="reference-replay-visual-hashes-") as temporary:
            fixture = self.make_fixture(Path(temporary))
            visual_path = fixture.root / "reference_case_v0_1_visual_approval.json"
            visual = json.loads(visual_path.read_text(encoding="utf-8"))
            visual["canonical_artifact_hashes"]["svg"] = "0" * 64
            write_json(visual_path, visual)
            approvals = fixture.case["approvals"]
            assert isinstance(approvals, dict) and isinstance(approvals["visual"], dict)
            approvals["visual"]["sha256"] = replay.sha256_file(visual_path)
            fixture.write_case()
            with self.assertRaisesRegex(ValueError, "do not match"):
                replay.inspect_reference_case(fixture.root)


if __name__ == "__main__":
    unittest.main()
