#!/usr/bin/env python3
"""Regression checks for the Candidate-C region-first fidelity review package."""

from __future__ import annotations

import base64
import hashlib
import json
import sys
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from PIL import Image, ImageChops
from pypdf import PdfReader


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_ROOT = REPOSITORY_ROOT / "examples" / "deep_image_prior"
DELIVERY_ROOT = EXAMPLE_ROOT / "editable_delivery_c_region_fidelity"
SCRIPTS = REPOSITORY_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_deep_image_prior_c_region_fidelity import (  # noqa: E402
    APPROVED_RASTER_ATOMS,
    ARROW_HEAD_COUNT,
    build_selected_candidate_map,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class DeepImagePriorCRegionFidelityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.candidate_path = EXAMPLE_ROOT / "candidates" / "C-presentation.png"
        cls.map_path = DELIVERY_ROOT / "source" / "selected_candidate_map.json"
        cls.semantic_path = DELIVERY_ROOT / "source" / "semantic_figure.json"
        cls.asset_manifest_path = DELIVERY_ROOT / "source" / "asset_manifest.json"
        cls.review_decision_path = DELIVERY_ROOT / "source" / "raster_atom_review_decision.json"
        cls.region_map = json.loads(cls.map_path.read_text(encoding="utf-8"))
        cls.semantic = json.loads(cls.semantic_path.read_text(encoding="utf-8"))
        cls.assets = json.loads(cls.asset_manifest_path.read_text(encoding="utf-8"))
        cls.review_decision = json.loads(cls.review_decision_path.read_text(encoding="utf-8"))

    def test_selected_map_is_hash_bound_and_has_eight_conversion_records(self) -> None:
        self.assertEqual(self.region_map, build_selected_candidate_map(EXAMPLE_ROOT))
        self.assertEqual(self.region_map["image_hash"], sha256_file(self.candidate_path))
        self.assertEqual(self.region_map["bbox_format"], "xywh_source_pixels")
        self.assertEqual(len(self.region_map["major_region_bboxes"]), 8)
        conversions = self.region_map["region_conversions"]
        self.assertEqual(set(conversions), set(self.region_map["major_region_bboxes"]))
        self.assertTrue(all(item["native_output_ids"] for item in conversions.values()))
        semantic_ids = set(self.semantic["object_ids"])
        for item in conversions.values():
            self.assertTrue(set(item["native_output_ids"]).issubset(semantic_ids))
        self.assertEqual(
            conversions["noise_input"]["conversion_mode"],
            "exact_replaceable_raster_atom",
        )
        self.assertEqual(
            conversions["reconstruction_landscape"]["conversion_mode"],
            "exact_replaceable_raster_atom",
        )
        self.assertTrue(
            all(item["use"] == "reference_only_not_embedded" for item in self.region_map["glyph_reference_crops"])
        )
        self.assertEqual(self.region_map["region_overlay"]["use"], "reference_only_not_embedded")
        self.assertTrue((DELIVERY_ROOT / "source" / self.region_map["region_overlay"]["path"]).is_file())

    def test_two_approved_atoms_are_exact_unresampled_source_pixel_crops(self) -> None:
        self.assertEqual(self.assets["candidate_sha256"], sha256_file(self.candidate_path))
        self.assertEqual(self.assets["bbox_format"], "xyxy_source_pixels")
        self.assertEqual(len(self.assets["assets"]), 2)
        with Image.open(self.candidate_path) as candidate:
            for asset in self.assets["assets"]:
                expected_contract = APPROVED_RASTER_ATOMS[asset["id"]]
                self.assertEqual(asset["bbox"], expected_contract["bbox"])
                left, top, right, bottom = asset["bbox"]
                self.assertEqual(asset["dimensions"], [right - left, bottom - top])
                self.assertTrue(asset["exact_pixel_crop"])
                self.assertFalse(asset["resampled"])
                self.assertTrue(asset["replaceable"])
                self.assertFalse(asset["pixel_editable"])
                self.assertTrue(asset["publication_safe"])
                self.assertEqual(asset["scientific_status"], "synthetic_visual_only")
                self.assertEqual(asset["release_policy"], "final_human_review_required")
                path = DELIVERY_ROOT / "source" / asset["path"]
                self.assertEqual(asset["sha256"], sha256_file(path))
                with Image.open(path) as actual:
                    self.assertEqual(actual.size, (right - left, bottom - top))
                    expected = candidate.crop((left, top, right, bottom)).convert("RGBA")
                    self.assertIsNone(ImageChops.difference(expected, actual.convert("RGBA")).getbbox())

    def test_raster_atom_review_decision_is_narrow_hash_bound_and_not_final_approval(self) -> None:
        decision = self.review_decision
        self.assertEqual(decision["status"], "APPROVED_FOR_REVIEW_DRAFT_ONLY")
        self.assertEqual(decision["scope"], "review-draft-only")
        self.assertEqual(decision["candidate"]["id"], "C-presentation")
        self.assertEqual(decision["candidate"]["path"], "../../candidates/C-presentation.png")
        self.assertEqual(decision["candidate"]["sha256"], sha256_file(self.candidate_path))
        self.assertEqual(decision["approval_basis"]["type"], "explicit_user_request")
        self.assertIn("region-first fidelity review draft", decision["approval_basis"]["description"])
        expected = {
            atom_id: contract["bbox"] for atom_id, contract in APPROVED_RASTER_ATOMS.items()
        }
        self.assertEqual(
            {item["atom_id"]: item["bbox"] for item in decision["authorized_atoms"]},
            expected,
        )
        manifest_assets = {item["id"]: item["sha256"] for item in self.assets["assets"]}
        self.assertEqual(
            {item["atom_id"]: item["asset_sha256"] for item in decision["authorized_atoms"]},
            manifest_assets,
        )
        self.assertEqual(self.assets["review_decision"]["path"], "raster_atom_review_decision.json")
        self.assertEqual(self.assets["review_decision"]["status"], decision["status"])
        constraints = decision["constraints"]
        self.assertTrue(constraints["synthetic_visual_only"])
        self.assertFalse(constraints["scientific_evidence"])
        self.assertTrue(constraints["independently_replaceable"])
        self.assertFalse(constraints["pixel_editable"])
        self.assertIsNone(decision["final_publication_approval"])
        self.assertIsNone(decision["final_scientific_approval"])

    def test_svg_has_only_two_replaceable_atoms_and_explicit_small_arrows(self) -> None:
        svg_path = DELIVERY_ROOT / "delivery" / "svg" / "master.svg"
        root = ET.parse(svg_path).getroot()
        images = [node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "image"]
        self.assertEqual(len(images), 2)
        hrefs = [node.get("href") or node.get("{http://www.w3.org/1999/xlink}href") for node in images]
        self.assertEqual(set(hrefs), {"assets/noise-content.png", "assets/reconstruction-content.png"})
        self.assertTrue(all(not href.startswith("data:") for href in hrefs))
        self.assertTrue(all(node.get("data-replaceable") == "true" for node in images))
        text = svg_path.read_text(encoding="utf-8")
        for forbidden in ("marker-end", "<marker", "<filter", "<linearGradient", "<radialGradient", "<mask"):
            self.assertNotIn(forbidden, text)
        arrows = [node for node in root.iter() if (node.get("id") or "").endswith("-arrowhead")]
        shafts = [node for node in root.iter() if (node.get("id") or "").endswith("-shaft")]
        self.assertEqual(len(arrows), ARROW_HEAD_COUNT)
        self.assertEqual(len(shafts), ARROW_HEAD_COUNT)
        self.assertTrue(all(node.get("stroke-linecap") == "butt" for node in shafts))
        for arrow in arrows:
            points = [tuple(map(float, value.split(","))) for value in arrow.get("points", "").split()]
            extent = max(
                max(point[0] for point in points) - min(point[0] for point in points),
                max(point[1] for point in points) - min(point[1] for point in points),
            )
            self.assertGreaterEqual(extent, 16.9)
            self.assertLessEqual(extent, 20.01)

    def test_candidate_c_macro_anchors_and_network_bounds_are_preserved(self) -> None:
        generator_frame = next(item for item in self.semantic["frames"] if item["id"] == "generator-frame")
        position = generator_frame["position"]
        network = self.semantic["regions"]["generator-network"]
        self.assertEqual(len(self.semantic["network_layer_groups"]), 11)
        self.assertEqual(len(network), 33)
        points = [point for shape in network for point in shape["points"]]
        self.assertGreaterEqual(min(point[0] for point in points), position["left"])
        self.assertLessEqual(max(point[0] for point in points), position["left"] + position["width"])
        self.assertLessEqual(max(point[0] for point in points), 742)
        main_flow = next(item for item in self.semantic["connectors"] if item["id"] == "flow-operator-predicted")
        self.assertEqual(len(main_flow["shaft_points"]), 2)
        self.assertEqual(main_flow["shaft_points"][0][1], main_flow["shaft_points"][1][1])
        feedback = next(item for item in self.semantic["connectors"] if item["id"] == "feedback-optimize-generator")
        self.assertEqual(feedback["shaft_points"][:4], [[1434.0, 417.0], [1335.0, 417.0], [1335.0, 668.0], [568.0, 668.0]])

    def test_nine_vector_equations_preserve_intrinsic_aspect_ratio(self) -> None:
        manifest = json.loads((DELIVERY_ROOT / "source" / "equation_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["equations"]), 9)
        for item in manifest["equations"]:
            intrinsic = item["intrinsic_viewbox"]
            target = item["target_position"]
            intrinsic_ratio = intrinsic[2] / intrinsic[3]
            target_ratio = target["width"] / target["height"]
            self.assertAlmostEqual(target_ratio, intrinsic_ratio, delta=intrinsic_ratio * 0.005)
            root = ET.parse(DELIVERY_ROOT / "source" / "math" / f"{item['equation_id']}.svg").getroot()
            self.assertTrue(any(node.tag.endswith("path") for node in root.iter()))
            self.assertFalse(any(node.tag.endswith("image") for node in root.iter()))
        by_id = {item["equation_id"]: item for item in manifest["equations"]}
        self.assertAlmostEqual(by_id["eq_objective"]["target_position"]["width"], 600, delta=0.1)
        self.assertAlmostEqual(by_id["eq_objective"]["target_position"]["height"], 90, delta=0.2)
        self.assertAlmostEqual(by_id["eq_reconstruction"]["target_position"]["width"], 233, delta=1.0)
        self.assertAlmostEqual(by_id["eq_reconstruction"]["target_position"]["height"], 51, delta=0.1)

    def test_pptx_contains_two_picture_atoms_nine_equations_and_many_native_shapes(self) -> None:
        pptx_path = DELIVERY_ROOT / "delivery" / "pptx" / "figure.pptx"
        forbidden_hashes = {
            sha256_file(self.candidate_path),
            sha256_file(DELIVERY_ROOT / "source" / "region_overlay.png"),
            *(sha256_file(path) for path in (DELIVERY_ROOT / "source" / "reference_regions").glob("*.png")),
        }
        approved_hashes = {asset["sha256"] for asset in self.assets["assets"]}
        with zipfile.ZipFile(pptx_path) as archive:
            media_names = [name for name in archive.namelist() if name.startswith("ppt/media/")]
            media_hashes = {hashlib.sha256(archive.read(name)).hexdigest() for name in media_names}
            substantive_rasters = [
                name for name in media_names
                if name.lower().endswith((".png", ".jpg", ".jpeg")) and archive.getinfo(name).file_size > 4096
            ]
            substantive_hashes = {
                hashlib.sha256(archive.read(name)).hexdigest() for name in substantive_rasters
            }
            vector = [name for name in media_names if name.lower().endswith(".svg")]
            slide_xml = archive.read("ppt/slides/slide1.xml")
        self.assertTrue(forbidden_hashes.isdisjoint(media_hashes))
        self.assertEqual(substantive_hashes, approved_hashes)
        self.assertEqual(len(substantive_rasters), 2)
        self.assertEqual(len(vector), 9)
        self.assertGreaterEqual(slide_xml.count(b"<p:sp>"), 500)
        self.assertEqual(slide_xml.count(b"<p:pic>"), 11)
        self.assertIn(b"noise-raster-atom", slide_xml)
        self.assertIn(b"reconstruction-raster-atom", slide_xml)

    def test_drawio_has_two_independent_image_cells_and_seven_edges(self) -> None:
        tree = ET.parse(DELIVERY_ROOT / "delivery" / "drawio" / "figure.drawio")
        cells = tree.findall(".//mxCell")
        image_cells = [cell for cell in cells if cell.get("semanticType") == "replaceable-raster-atom"]
        self.assertEqual(len(image_cells), 2)
        self.assertEqual(len([cell for cell in cells if cell.get("edge") == "1"]), ARROW_HEAD_COUNT)
        for cell in image_cells:
            style = cell.get("style") or ""
            self.assertIn("shape=image", style)
            encoded = style.split("image=data:image/png;base64,", 1)[1].split(";", 1)[0]
            self.assertIn(hashlib.sha256(base64.b64decode(encoded)).hexdigest(), {item["sha256"] for item in self.assets["assets"]})

    def test_pdf_preview_validation_and_approval_boundary(self) -> None:
        pdf = PdfReader(DELIVERY_ROOT / "delivery" / "pdf" / "publication.pdf")
        self.assertEqual(len(pdf.pages), 1)
        report = json.loads(
            (DELIVERY_ROOT / "validation" / "region_fidelity_validation_report.json").read_text(encoding="utf-8")
        )
        self.assertEqual(report["status"], "VERIFIED_FIDELITY_MIXED_MEDIA_REVIEW_DRAFT")
        self.assertEqual(report["checks"]["approved_raster_atom_count"], 2)
        self.assertEqual(report["checks"]["raster_atom_review_decision_status"], "APPROVED_FOR_REVIEW_DRAFT_ONLY")
        self.assertEqual(report["checks"]["raster_atom_review_decision_scope"], "review-draft-only")
        self.assertEqual(
            report["artifacts"]["raster_atom_review_decision"]["sha256"],
            sha256_file(self.review_decision_path),
        )
        self.assertGreaterEqual(report["checks"]["pptx_native_shape_count"], 500)
        self.assertIsNone(report["final_scientific_approval"])
        self.assertTrue((DELIVERY_ROOT / "preview.png").is_file())
        self.assertTrue((DELIVERY_ROOT / "delivery" / "pptx" / "slide-01.png").is_file())
        readme = (DELIVERY_ROOT / "README.md").read_text(encoding="utf-8")
        for phrase in (
            "fidelity-first mixed-media editable composition",
            "replaceable but not pixel-editable",
            "preview/export only",
            "Final scientific approval is `null`",
            "segmented review draft",
            "source/raster_atom_review_decision.json",
        ):
            self.assertIn(phrase, readme)

    def test_portability_and_workspace_cleanliness(self) -> None:
        json_text = "\n".join(path.read_text(encoding="utf-8") for path in DELIVERY_ROOT.rglob("*.json"))
        path_markers = (
            "/" + "Users" + "/",
            "/" + "private" + "/" + "tmp" + "/",
            "/" + "home" + "/",
            "file" + "://",
        )
        for marker in path_markers:
            self.assertNotIn(marker, json_text)
        forbidden_names = {".DS_Store", ".pytest_cache", ".mypy_cache", ".ruff_cache", "__pycache__", "figure.pdf"}
        self.assertFalse([path for path in DELIVERY_ROOT.rglob("*") if path.name in forbidden_names])
        self.assertIsNone(self.semantic["selection"]["final_scientific_approval"])
        self.assertEqual(len(self.semantic["image_modules"]), 2)


if __name__ == "__main__":
    unittest.main()
