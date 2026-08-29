#!/usr/bin/env python3
"""Portable enforcement tests for the publication-safe synthetic demo."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPOSITORY_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import run_synthetic_demo as demo  # noqa: E402


FULL_RUNTIME_READY, FULL_RUNTIME_MISSING = demo.full_runtime_prerequisites()
FULL_RUNTIME_SKIP = (
    "requires the documented native adapter runtime: %s"
    % ", ".join(FULL_RUNTIME_MISSING)
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def changed_record(source: Path, destination: Path, *keys: str, value: object) -> Path:
    record = read_json(source)
    target = record
    for key in keys[:-1]:
        target = target[key]
    target[keys[-1]] = value
    write_json(destination, record)
    return destination


def prepare_verified_boundary(run_dir: Path) -> tuple[dict, Path]:
    state = demo.build_demo(run_dir, mode="core")
    state["mode"] = "full"
    state["status"] = "IN_PROGRESS"
    state["stage"] = "adapters_built"
    report_path = run_dir / "validation" / "cross_format_report.json"
    write_json(
        report_path,
        {
            "schema_version": "1.0",
            "figure_id": "synthetic_restoration_demo",
            "status": "VERIFIED",
            "validation_scope": (
                "Programmable structure only; not scientific correctness or Gate 3 approval."
            ),
        },
    )
    return state, report_path


class SyntheticDemoGateTests(unittest.TestCase):
    def test_missing_and_bad_gate_1_stop_before_skeleton(self) -> None:
        with tempfile.TemporaryDirectory(prefix="synthetic-gate1-", dir="/tmp") as temporary:
            root = Path(temporary)
            cases = {
                "missing": root / "missing_gate_1.json",
                "bad": changed_record(
                    demo.DEFAULT_GATE_1,
                    root / "bad_gate_1.json",
                    "interpretation_sha256",
                    value="0" * 64,
                ),
            }
            for name, gate_record in cases.items():
                with self.subTest(name=name):
                    output = root / ("run_" + name)
                    with self.assertRaisesRegex(demo.DemoError, "Gate 1"):
                        demo.build_demo(
                            output,
                            mode="core",
                            gate_1_record=gate_record,
                        )
                    state = read_json(output / "demo_state.json")
                    self.assertEqual(state["stage"], "blocked_gate_1")
                    self.assertEqual(state["gates"]["gate_1"]["status"], "blocked")
                    self.assertFalse((output / "skeleton").exists())
                    self.assertFalse((output / "source").exists())
                    self.assertFalse((output / "delivery").exists())

    def test_missing_and_bad_gate_2_stop_before_exports(self) -> None:
        with tempfile.TemporaryDirectory(prefix="synthetic-gate2-", dir="/tmp") as temporary:
            root = Path(temporary)
            cases = {
                "missing": root / "missing_gate_2.json",
                "bad": changed_record(
                    demo.DEFAULT_GATE_2,
                    root / "bad_gate_2.json",
                    "topology_bindings",
                    "scene_sha256",
                    value="0" * 64,
                ),
            }
            for name, gate_record in cases.items():
                with self.subTest(name=name):
                    output = root / ("run_" + name)
                    with self.assertRaisesRegex(demo.DemoError, "Gate 2"):
                        demo.build_demo(
                            output,
                            mode="core",
                            gate_2_record=gate_record,
                        )
                    state = read_json(output / "demo_state.json")
                    self.assertEqual(state["stage"], "blocked_gate_2")
                    self.assertEqual(state["gates"]["gate_2"]["status"], "blocked")
                    for path in demo.SKELETON_FILES.values():
                        self.assertTrue((output / path).is_file())
                    self.assertFalse((output / "source").exists())
                    self.assertFalse((output / "delivery").exists())

    def test_programmable_validation_cannot_create_gate_3_approval(self) -> None:
        with tempfile.TemporaryDirectory(prefix="synthetic-gate3-boundary-", dir="/tmp") as temporary:
            output = Path(temporary) / "run"
            state, report_path = prepare_verified_boundary(output)
            with mock.patch.object(demo, "_assert_full_delivery_files"):
                state = demo._enter_awaiting_gate_3(output, state, report_path)
            self.assertEqual(state["stage"], "awaiting_gate_3")
            self.assertEqual(
                state["gates"]["gate_3"]["status"],
                "awaiting_explicit_researcher_or_operator_action",
            )
            self.assertFalse(
                (output / "approvals" / "gate_3_final_approval.json").exists()
            )
            self.assertFalse(
                state["gates"]["gate_3"]["created_by_automated_validation"]
            )

    def test_final_approval_is_a_separate_explicit_bound_record(self) -> None:
        with tempfile.TemporaryDirectory(prefix="synthetic-gate3-explicit-", dir="/tmp") as temporary:
            output = Path(temporary) / "run"
            state, report_path = prepare_verified_boundary(output)
            with mock.patch.object(demo, "_assert_full_delivery_files"):
                demo._enter_awaiting_gate_3(output, state, report_path)
                self.assertFalse(
                    (output / "approvals" / "gate_3_final_approval.json").exists()
                )
                final_state = demo.approve_final(output, "Unit Test Researcher")

            approval_path = output / "approvals" / "gate_3_final_approval.json"
            approval = read_json(approval_path)
            self.assertEqual(final_state["stage"], "complete")
            self.assertEqual(approval["decision"], "APPROVE_FINAL")
            self.assertEqual(approval["operator"], "Unit Test Researcher")
            self.assertEqual(
                approval["validation_report"]["sha256"],
                demo.sha256_file(report_path),
            )
            self.assertFalse(approval["created_by_automated_validation"])
            self.assertEqual(
                approval["scientific_acceptability_decided_by"],
                "researcher/operator",
            )
            self.assertIn(
                "not automated validation",
                approval["decision_statement"],
            )

    def test_added_artifact_after_validation_blocks_final_approval(self) -> None:
        with tempfile.TemporaryDirectory(prefix="synthetic-gate3-added-", dir="/tmp") as temporary:
            output = Path(temporary) / "run"
            state, report_path = prepare_verified_boundary(output)
            with mock.patch.object(demo, "_assert_full_delivery_files"):
                demo._enter_awaiting_gate_3(output, state, report_path)
                (output / "unvalidated-added-file.txt").write_text(
                    "not part of the VERIFIED snapshot\n",
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(demo.DemoError, "artifact set changed"):
                    demo.approve_final(output, "Unit Test Researcher")
            self.assertFalse(
                (output / "approvals" / "gate_3_final_approval.json").exists()
            )

    def test_gate_3_approval_path_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="synthetic-gate3-symlink-", dir="/tmp") as temporary:
            root = Path(temporary)
            output = root / "run"
            state, report_path = prepare_verified_boundary(output)
            outside_target = root / "outside-approval.json"
            approval_path = output / "approvals" / "gate_3_final_approval.json"
            with mock.patch.object(demo, "_assert_full_delivery_files"):
                demo._enter_awaiting_gate_3(output, state, report_path)
                approval_path.symlink_to(outside_target)
                with self.assertRaisesRegex(demo.DemoError, "symbolic link"):
                    demo.approve_final(output, "Unit Test Researcher")
            self.assertTrue(approval_path.is_symlink())
            self.assertFalse(outside_target.exists())

    def test_fresh_core_runs_have_identical_structure_and_hashes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="synthetic-repeat-", dir="/tmp") as temporary:
            root = Path(temporary)
            first = root / "first"
            second = root / "second"
            first_state = demo.build_demo(first, mode="core")
            second_state = demo.build_demo(second, mode="core")
            self.assertEqual(
                sorted(path.relative_to(first).as_posix() for path in first.rglob("*") if path.is_file()),
                sorted(path.relative_to(second).as_posix() for path in second.rglob("*") if path.is_file()),
            )
            self.assertEqual(first_state["artifact_hashes"], second_state["artifact_hashes"])
            self.assertNotIn(
                str(REPOSITORY_ROOT.resolve()),
                (first / "demo_state.json").read_text(encoding="utf-8"),
            )
            self.assertFalse((first / "approvals" / "gate_3_final_approval.json").exists())

    def test_existing_output_directory_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory(prefix="synthetic-existing-", dir="/tmp") as temporary:
            output = Path(temporary) / "run"
            output.mkdir()
            marker = output / "keep.txt"
            marker.write_text("unchanged\n", encoding="utf-8")
            with self.assertRaisesRegex(demo.DemoError, "refusing to overwrite"):
                demo.build_demo(output, mode="core")
            self.assertEqual(marker.read_text(encoding="utf-8"), "unchanged\n")
            self.assertEqual([marker], list(output.iterdir()))

    def test_output_inside_repository_is_rejected_before_creation(self) -> None:
        output = REPOSITORY_ROOT / "synthetic-demo-output-must-not-exist"
        self.assertFalse(output.exists())
        with self.assertRaisesRegex(demo.DemoError, "outside the repository"):
            demo.build_demo(output, mode="core")
        self.assertFalse(output.exists())

    @unittest.skipUnless(FULL_RUNTIME_READY, FULL_RUNTIME_SKIP)
    def test_full_mode_reaches_gate_3_with_native_formats(self) -> None:
        with tempfile.TemporaryDirectory(prefix="synthetic-full-", dir="/tmp") as temporary:
            output = Path(temporary) / "run"
            state = demo.build_demo(output, mode="full")
            self.assertEqual(state["stage"], "awaiting_gate_3")
            self.assertEqual(
                read_json(output / "validation" / "cross_format_report.json")["status"],
                "VERIFIED",
            )
            for path in demo.FULL_DELIVERY_FILES:
                self.assertTrue((output / path).is_file(), path.as_posix())
            self.assertFalse(
                (output / "approvals" / "gate_3_final_approval.json").exists()
            )


if __name__ == "__main__":
    unittest.main()
