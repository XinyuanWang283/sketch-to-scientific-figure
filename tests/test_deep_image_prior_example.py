#!/usr/bin/env python3
"""Integrity checks for the public five-candidate Deep Image Prior example."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from PIL import Image


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_ROOT = REPOSITORY_ROOT / "examples" / "deep_image_prior"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class DeepImagePriorExampleTests(unittest.TestCase):
    def test_manifest_binds_exactly_five_separate_candidate_events(self) -> None:
        manifest = json.loads(
            (EXAMPLE_ROOT / "candidate_manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            manifest["status"],
            "visual_approved_scientific_and_release_decisions_pending",
        )
        self.assertEqual(manifest["generation"]["mode"], "codex_builtin_imagegen")
        self.assertFalse(manifest["generation"]["user_api_key_required"])
        self.assertEqual(manifest["generation"]["separate_generation_calls"], 5)
        self.assertTrue(manifest["generation"]["generation_event_ids_are_repository_local"])
        self.assertFalse(manifest["generation"]["native_tool_call_ids_recorded"])
        self.assertFalse(
            manifest["generation"]["content_credentials_cryptographically_validated_by_repository"]
        )
        self.assertFalse(manifest["generation"]["backend_model_identity_independently_verified"])
        self.assertFalse(manifest["generation"]["comparison_sheet_generated_by_imagegen"])

        expected = [
            ("A", "faithful"),
            ("B", "publication"),
            ("C", "presentation"),
            ("D", "alternative-layout"),
            ("E", "visual-variant"),
        ]
        candidates = manifest["candidates"]
        self.assertEqual(
            [(item["slot"], item["direction"]) for item in candidates], expected
        )
        self.assertEqual(len({item["generation_event_id"] for item in candidates}), 5)
        self.assertTrue(all("native_tool_call_id" not in item for item in candidates))
        self.assertEqual(len({item["sha256"] for item in candidates}), 5)

        for candidate in candidates:
            path = EXAMPLE_ROOT / candidate["path"]
            self.assertTrue(path.is_file(), path)
            self.assertEqual(sha256_file(path), candidate["sha256"])
            with Image.open(path) as image:
                self.assertEqual(image.format, "PNG")
                self.assertEqual(image.size, (candidate["width"], candidate["height"]))

    def test_input_comparison_sheet_and_active_c_only_selection_are_bound(self) -> None:
        manifest = json.loads(
            (EXAMPLE_ROOT / "candidate_manifest.json").read_text(encoding="utf-8")
        )
        sketch = EXAMPLE_ROOT / manifest["input"]["path"]
        comparison = EXAMPLE_ROOT / manifest["comparison_sheet"]["path"]
        self.assertEqual(sha256_file(sketch), manifest["input"]["sha256"])
        self.assertEqual(sha256_file(comparison), manifest["comparison_sheet"]["sha256"])
        self.assertTrue(
            manifest["comparison_sheet"]["created_after_five_separate_generation_events"]
        )
        self.assertFalse(manifest["comparison_sheet"]["generated_by_imagegen"])

        selection = manifest["selection"]
        self.assertEqual(selection["status"], "approved_for_editable_reconstruction")
        self.assertEqual(selection["selection_type"], "single_candidate")
        self.assertEqual(selection["selected_candidate"]["slot"], "C")
        self.assertEqual(selection["supersedes"]["review_outcome"], "REJECTED_FOR_VISUAL_REVISION")
        self.assertIsNone(selection["final_scientific_approval"])

        approval_path = EXAMPLE_ROOT / selection["approval_record"]
        approval = json.loads(approval_path.read_text(encoding="utf-8"))
        self.assertEqual(approval["decision"], "APPROVE_IMAGEGEN_CANDIDATE")
        self.assertEqual(approval["selection_type"], "single_candidate")
        self.assertEqual(
            approval["selected_candidate"]["sha256"],
            selection["selected_candidate"]["sha256"],
        )
        self.assertEqual(
            sha256_file(EXAMPLE_ROOT / approval["selected_candidate"]["path"]),
            approval["selected_candidate"]["sha256"],
        )
        self.assertTrue(approval["editable_reconstruction_authorized"])
        self.assertEqual(approval["supersedes"]["review_outcome"], "REJECTED_FOR_VISUAL_REVISION")
        self.assertIsNone(approval["final_scientific_approval"])

        history = json.loads(
            (EXAMPLE_ROOT / selection["selection_history"]).read_text(encoding="utf-8")
        )
        self.assertEqual(history["active_selection_record"], selection["approval_record"])
        self.assertEqual(history["active_delivery_revision"], "editable_delivery_c_fidelity_v2/")
        self.assertEqual(len(history["history"]), 8)
        self.assertEqual(history["history"][0]["review_outcome"], "REJECTED_FOR_VISUAL_REVISION")
        self.assertEqual(
            history["history"][1]["review_outcome"],
            "REJECTED_FOR_INSUFFICIENT_VISUAL_FIDELITY",
        )
        self.assertEqual(
            history["history"][2]["review_outcome"],
            "REJECTED_FOR_REGION_WORKFLOW_AND_EXPORT_DEFECTS",
        )
        self.assertEqual(
            history["history"][3]["review_outcome"],
            "PRESERVED_AS_MAXIMUM_EDITABILITY_OPTION",
        )
        self.assertEqual(
            history["history"][4]["review_outcome"],
            "AWAITING_FINAL_RESEARCHER_REVIEW",
        )
        self.assertEqual(
            history["history"][5]["review_outcome"],
            "VISUAL_APPROVED_SCIENTIFIC_AND_RELEASE_DECISIONS_PENDING",
        )
        self.assertEqual(
            history["history"][6]["review_outcome"],
            "VISUAL_APPROVED_WITH_RASTER_AUTHORIZATION_BOUND_SCIENTIFIC_AND_RELEASE_DECISIONS_PENDING",
        )
        self.assertEqual(
            history["history"][7]["review_outcome"],
            "VISUAL_APPROVED_WITH_VALIDATOR_IDENTITY_AND_MANIFEST_SEMANTICS_BOUND_SCIENTIFIC_AND_RELEASE_DECISIONS_PENDING",
        )
        for item in history["history"]:
            record = EXAMPLE_ROOT / item["selection_record"]
            self.assertEqual(sha256_file(record), item["selection_record_sha256"])
            for path_key, hash_key in (
                ("reference_case_record", "reference_case_record_sha256"),
                ("artifact_manifest", "artifact_manifest_sha256"),
                ("structural_validation_report", "structural_validation_report_sha256"),
                ("visual_approval_record", "visual_approval_record_sha256"),
            ):
                if path_key in item:
                    self.assertEqual(
                        sha256_file(EXAMPLE_ROOT / item[path_key]),
                        item[hash_key],
                    )

        template = json.loads(
            (EXAMPLE_ROOT / "candidate_selection.template.json").read_text(encoding="utf-8")
        )
        self.assertEqual(template["status"], "template_not_approved")
        self.assertIsNone(template["selection_type"])
        self.assertIsNone(template["single_selection"])
        self.assertIsNone(template["combination"]["layout_source"])
        self.assertIsNone(template["combination"]["visual_style_source"])
        self.assertFalse(template["editable_reconstruction_authorized"])
        self.assertIsNone(template["decision"])
        self.assertIsNone(template["final_scientific_approval"])


if __name__ == "__main__":
    unittest.main()
