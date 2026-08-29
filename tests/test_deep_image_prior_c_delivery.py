#!/usr/bin/env python3
"""Structural tests for the active candidate C-only editable delivery."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_ROOT = REPOSITORY_ROOT / "examples" / "deep_image_prior"
DELIVERY_ROOT = EXAMPLE_ROOT / "editable_delivery_c"
SCRIPTS = REPOSITORY_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_deep_image_prior_c_semantic import build_semantic  # noqa: E402
from validate_delivery import check_drawio, check_pdf, check_pptx, check_svg  # noqa: E402


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class DeepImagePriorCDeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.semantic_path = DELIVERY_ROOT / "source" / "semantic_figure.json"
        cls.semantic = json.loads(cls.semantic_path.read_text(encoding="utf-8"))

    def test_semantic_source_binds_candidate_c_and_expected_topology(self) -> None:
        semantic = self.semantic
        self.assertEqual(semantic["figure_id"], "deep-image-prior-C-presentation")
        self.assertEqual(semantic["canvas"]["width"], 1600)
        self.assertEqual(semantic["canvas"]["height"], 900)
        self.assertEqual({item["type"] for item in semantic["shapes"]}, {"rect", "ellipse"})
        self.assertEqual(len(semantic["shapes"]), 1340)
        self.assertEqual(len(semantic["text_objects"]), 1)
        self.assertEqual(len(semantic["equation_objects"]), 9)
        self.assertEqual(len(semantic["connectors"]), 7)
        self.assertEqual(semantic["ports"], [])
        entity_types = {
            item["id"]: item["entity_type"]
            for item in semantic["entities"]
        }
        for shape in semantic["shapes"]:
            self.assertEqual(entity_types[shape["id"]], shape["entity_type"])

        hashes = semantic["provenance"]["source_hashes"]
        self.assertEqual(hashes["input_sketch"], sha256_file(EXAMPLE_ROOT / "sketch.png"))
        self.assertEqual(
            hashes["candidate_C"],
            sha256_file(EXAMPLE_ROOT / "candidates" / "C-presentation.png"),
        )
        self.assertEqual(
            hashes["selection_approval"],
            sha256_file(EXAMPLE_ROOT / "candidate_selection_c_only.json"),
        )
        self.assertEqual(semantic["provenance"]["selection"], "candidate C for both layout and visual style")
        self.assertIsNone(semantic["provenance"]["final_scientific_approval"])

        actual_edges = {
            item["id"]: (item["source_id"], item["target_id"])
            for item in semantic["connectors"]
        }
        self.assertEqual(actual_edges, {
            "flow-z-generator": ("noise-frame", "generator-frame"),
            "flow-generator-reconstruction": ("generator-frame", "reconstruction-background"),
            "flow-reconstruction-operator": ("reconstruction-background", "operator-frame"),
            "flow-operator-predicted": ("operator-frame", "predicted-frame"),
            "flow-predicted-loss": ("predicted-frame", "comparison-node"),
            "flow-observed-loss": ("observed-frame", "comparison-node"),
            "feedback-optimize-generator": ("comparison-node", "generator-frame"),
        })

    def test_builder_reproduces_checked_in_canonical_source(self) -> None:
        rebuilt = build_semantic(
            EXAMPLE_ROOT,
            EXAMPLE_ROOT / "candidate_selection_c_only.json",
        )
        self.assertEqual(rebuilt, self.semantic)

    def test_builder_needs_no_rejected_d_candidate_or_selection(self) -> None:
        with tempfile.TemporaryDirectory(prefix="deep-image-prior-c-only-") as temporary:
            clean_root = Path(temporary)
            (clean_root / "candidates").mkdir()
            shutil.copyfile(EXAMPLE_ROOT / "sketch.png", clean_root / "sketch.png")
            shutil.copyfile(
                EXAMPLE_ROOT / "candidates" / "C-presentation.png",
                clean_root / "candidates" / "C-presentation.png",
            )
            shutil.copyfile(
                EXAMPLE_ROOT / "candidate_selection_c_only.json",
                clean_root / "candidate_selection_c_only.json",
            )
            rebuilt = build_semantic(
                clean_root,
                clean_root / "candidate_selection_c_only.json",
            )
            self.assertEqual(rebuilt["provenance"]["selection"], "candidate C for both layout and visual style")
            self.assertFalse((clean_root / "candidate_selection.json").exists())
            self.assertFalse((clean_root / "candidates" / "D-alternative-layout.png").exists())

    def test_svg_pptx_drawio_and_pdf_have_native_verified_structure(self) -> None:
        checks = [
            check_svg(DELIVERY_ROOT / "delivery" / "svg" / "master.svg", self.semantic, "svg"),
            check_pptx(DELIVERY_ROOT / "delivery" / "pptx" / "figure.pptx", self.semantic),
            check_drawio(DELIVERY_ROOT / "delivery" / "drawio" / "figure.drawio", self.semantic),
            check_pdf(
                DELIVERY_ROOT / "delivery" / "pdf" / "publication.pdf",
                "publication-pdf",
                self.semantic,
            ),
        ]
        self.assertEqual([item["status"] for item in checks], ["VERIFIED"] * 4)
        svg, pptx, drawio, pdf = checks
        self.assertEqual(svg["raster_element_count"], 0)
        self.assertEqual(svg["external_or_embedded_image_refs"], [])
        self.assertEqual(pptx["raster_picture_ids"], [])
        self.assertEqual(pptx["whole_canvas_picture_ids"], [])
        self.assertEqual(pptx["native_connector_count"], 7)
        self.assertEqual(drawio["picture_standin_cells"], [])
        self.assertEqual(drawio["native_edge_count"], 7)
        self.assertTrue(drawio["endpoint_integrity"])
        self.assertEqual(pdf["page_count"], 1)
        self.assertEqual(pdf["embedded_image_count"], 0)
        self.assertTrue(pdf["vector_evidence"])
        self.assertFalse(pdf["scientific_validation"])

    def test_portable_validation_report_matches_checked_in_artifacts(self) -> None:
        report_path = DELIVERY_ROOT / "validation" / "cross_format_report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "VERIFIED")
        self.assertEqual(report["canonical_source"], "source/semantic_figure.json")
        self.assertEqual(report["checks"][0]["sha256"], sha256_file(self.semantic_path))
        self.assertEqual(
            report["validation_scope"],
            "Programmable structure only; not scientific correctness or Gate 3 approval.",
        )
        self.assertTrue((DELIVERY_ROOT / report["preview"]["path"]).is_file())
        serialized = report_path.read_text(encoding="utf-8")
        self.assertNotIn("/" + "Users" + "/", serialized)
        self.assertNotIn("/" + "private" + "/" + "tmp" + "/", serialized)
        self.assertNotIn("C:" + "\\" + "Users" + "\\", serialized)

    def test_powerpoint_notes_do_not_publish_local_paths(self) -> None:
        pptx_path = DELIVERY_ROOT / "delivery" / "pptx" / "figure.pptx"
        with zipfile.ZipFile(pptx_path) as archive:
            notes = b"\n".join(
                archive.read(name)
                for name in archive.namelist()
                if name.startswith("ppt/notesSlides/") and name.endswith(".xml")
            )
        self.assertNotIn(b"/" + b"Users" + b"/", notes)
        self.assertNotIn(b"/" + b"private" + b"/" + b"tmp" + b"/", notes)
        self.assertIn(b"source/semantic_figure.json", notes)


if __name__ == "__main__":
    unittest.main()
