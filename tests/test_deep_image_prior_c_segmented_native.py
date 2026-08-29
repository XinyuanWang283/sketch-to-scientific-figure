#!/usr/bin/env python3
"""Regression checks for the Candidate-C region-first native revision."""

from __future__ import annotations

import hashlib
import json
import sys
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from pypdf import PdfReader


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_ROOT = REPOSITORY_ROOT / "examples" / "deep_image_prior"
DELIVERY_ROOT = EXAMPLE_ROOT / "editable_delivery_c_region_native"
SCRIPTS = REPOSITORY_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_deep_image_prior_c_segmented_native import (  # noqa: E402
    ARROW_HEAD_COUNT,
    build_selected_candidate_map,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class DeepImagePriorCSegmentedNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.map_path = DELIVERY_ROOT / "source" / "selected_candidate_map.json"
        cls.semantic_path = DELIVERY_ROOT / "source" / "semantic_figure.json"
        cls.map = json.loads(cls.map_path.read_text(encoding="utf-8"))
        cls.semantic = json.loads(cls.semantic_path.read_text(encoding="utf-8"))

    def test_region_map_is_hash_bound_and_every_region_maps_to_native_ids(self) -> None:
        expected = build_selected_candidate_map(EXAMPLE_ROOT)
        self.assertEqual(expected, self.map)
        self.assertEqual(
            self.map["image_hash"],
            sha256_file(EXAMPLE_ROOT / "candidates" / "C-presentation.png"),
        )
        required = {
            "candidate_id", "image_hash", "major_region_bboxes", "palette_samples",
            "stroke_character", "corner_language", "whitespace_rhythm",
            "glyph_reference_crops", "art_direction_notes", "scientific_overrides",
        }
        self.assertTrue(required.issubset(self.map))
        mapped = self.map["region_output_ids"]
        self.assertEqual(set(mapped), set(self.map["major_region_bboxes"]))
        self.assertTrue(all(ids for ids in mapped.values()))
        semantic_ids = set(self.semantic["object_ids"])
        for ids in mapped.values():
            self.assertTrue(set(ids).issubset(semantic_ids))
        self.assertTrue(all(item["use"] == "reference_only_not_embedded" for item in self.map["glyph_reference_crops"]))
        self.assertEqual(self.map["bbox_format"], "xywh_source_pixels")
        self.assertEqual(self.map["region_overlay"]["use"], "reference_only_not_embedded")
        self.assertTrue((DELIVERY_ROOT / "source" / self.map["region_overlay"]["path"]).is_file())

    def test_current_workflow_contract_keeps_region_first_map_mandatory(self) -> None:
        skill = (REPOSITORY_ROOT / ".agents" / "skills" / "sketch-to-scientific-figure" / "SKILL.md").read_text(encoding="utf-8")
        prompt = (REPOSITORY_ROOT / "prompts" / "02_selected_proposal_to_svg.md").read_text(encoding="utf-8")
        for contract in (skill, prompt):
            self.assertIn("selected_candidate_map.json", contract)
            self.assertIn("reference_only_not_embedded", contract)

    def test_network_geometry_stays_inside_generator_frame(self) -> None:
        frame = next(item for item in self.semantic["frames"] if item["id"] == "generator-frame")["position"]
        left, top = frame["left"], frame["top"]
        right, bottom = left + frame["width"], top + frame["height"]
        network = self.semantic["regions"]["generator-network"]
        points = [point for shape in network for point in shape["points"]]
        self.assertGreaterEqual(min(point[0] for point in points), left)
        self.assertLessEqual(max(point[0] for point in points), right)
        self.assertGreaterEqual(min(point[1] for point in points), top)
        self.assertLessEqual(max(point[1] for point in points), bottom)
        self.assertLessEqual(max(point[0] for point in points), 742)

    def test_noise_is_dense_native_geometry_and_main_panel_arrow_is_horizontal(self) -> None:
        noise = self.semantic["regions"]["noise-field"]
        self.assertEqual(sum(item["id"].startswith("noise-dot-") for item in noise), 1300)
        self.assertEqual(sum(item["id"].startswith("noise-stroke-") for item in noise), 450)
        noise_frame = next(item for item in self.semantic["frames"] if item["id"] == "noise-frame")
        self.assertEqual(noise_frame["fill"], "#F7F8FA")
        main_panel_arrow = next(
            item for item in self.semantic["connectors"] if item["id"] == "flow-operator-predicted"
        )
        self.assertEqual(main_panel_arrow["target_id"], "measurement-panel")
        self.assertEqual(len(main_panel_arrow["shaft_points"]), 2)
        self.assertEqual(main_panel_arrow["shaft_points"][0][1], main_panel_arrow["shaft_points"][1][1])

    def test_semantic_portable_source_paths_resolve_and_match_hashes(self) -> None:
        reference = (self.semantic_path.parent / self.semantic["visual_reference"]["path"]).resolve()
        selection = (self.semantic_path.parent / self.semantic["selection"]["path"]).resolve()
        self.assertEqual(reference, EXAMPLE_ROOT / "candidates" / "C-presentation.png")
        self.assertEqual(selection, EXAMPLE_ROOT / "candidate_selection_c_only.json")
        self.assertEqual(sha256_file(reference), self.semantic["visual_reference"]["sha256"])
        self.assertEqual(sha256_file(selection), self.semantic["selection"]["sha256"])

    def test_svg_is_native_and_uses_small_explicit_arrowheads(self) -> None:
        svg_path = DELIVERY_ROOT / "delivery" / "svg" / "master.svg"
        root = ET.parse(svg_path).getroot()
        tags = [element.tag.rsplit("}", 1)[-1] for element in root.iter()]
        self.assertNotIn("image", tags)
        self.assertNotIn("marker", tags)
        svg_text = svg_path.read_text(encoding="utf-8")
        for forbidden in ("marker-end", "<filter", "<linearGradient", "<radialGradient", "<mask", "data:image"):
            self.assertNotIn(forbidden, svg_text)
        arrows = [element for element in root.iter() if (element.get("id") or "").endswith("-arrowhead")]
        self.assertEqual(len(arrows), ARROW_HEAD_COUNT)
        for arrow in arrows:
            points = [tuple(map(float, item.split(","))) for item in arrow.get("points", "").split()]
            self.assertEqual(len(points), 3)
            xs = [point[0] for point in points]
            ys = [point[1] for point in points]
            self.assertLessEqual(max(max(xs) - min(xs), max(ys) - min(ys)), 18.01)
        shafts = [element for element in root.iter() if (element.get("id") or "").endswith("-shaft")]
        self.assertEqual(len(shafts), ARROW_HEAD_COUNT)
        self.assertTrue(all(item.get("stroke-linecap") == "butt" for item in shafts))

    def test_equation_boxes_preserve_rendered_intrinsic_aspect_ratio(self) -> None:
        manifest = json.loads(
            (DELIVERY_ROOT / "source" / "equation_manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(manifest["equations"]), 9)
        for item in manifest["equations"]:
            intrinsic = item["intrinsic_viewbox"]
            target = item["target_position"]
            intrinsic_ratio = intrinsic[2] / intrinsic[3]
            target_ratio = target["width"] / target["height"]
            self.assertAlmostEqual(target_ratio, intrinsic_ratio, delta=intrinsic_ratio * 0.005)
            equation_svg = DELIVERY_ROOT / "source" / "math" / f"{item['equation_id']}.svg"
            root = ET.parse(equation_svg).getroot()
            self.assertEqual(root.get("data-latex"), item["latex_source"])
            self.assertTrue(any(node.tag.endswith("path") for node in root.iter()))
            self.assertFalse(any(node.tag.endswith("image") for node in root.iter()))
        by_id = {item["equation_id"]: item for item in manifest["equations"]}
        self.assertAlmostEqual(by_id["eq_objective"]["target_position"]["width"], 600, delta=0.1)
        self.assertAlmostEqual(by_id["eq_objective"]["target_position"]["height"], 90, delta=0.2)
        self.assertAlmostEqual(by_id["eq_reconstruction"]["target_position"]["width"], 233, delta=1.0)
        self.assertAlmostEqual(by_id["eq_reconstruction"]["target_position"]["height"], 51, delta=0.1)
        master = ET.parse(DELIVERY_ROOT / "delivery" / "svg" / "master.svg").getroot()
        for item in manifest["equations"]:
            nested = next(node for node in master.iter() if node.get("id") == item["id"])
            self.assertTrue(any(node.tag.endswith("path") for node in nested.iter()))

    def test_pptx_has_native_objects_and_no_candidate_or_crop_raster(self) -> None:
        pptx_path = DELIVERY_ROOT / "delivery" / "pptx" / "figure.pptx"
        forbidden_hashes = {
            sha256_file(EXAMPLE_ROOT / "candidates" / "C-presentation.png"),
            sha256_file(DELIVERY_ROOT / "source" / "region_overlay.png"),
            *(sha256_file(path) for path in (DELIVERY_ROOT / "source" / "reference_regions").glob("*.png")),
        }
        with zipfile.ZipFile(pptx_path) as archive:
            media_names = [name for name in archive.namelist() if name.startswith("ppt/media/")]
            media_hashes = {hashlib.sha256(archive.read(name)).hexdigest() for name in media_names}
            raster = [name for name in media_names if name.lower().endswith((".png", ".jpg", ".jpeg"))]
            vector = [name for name in media_names if name.lower().endswith(".svg")]
            raster_sizes = [archive.getinfo(name).file_size for name in raster]
            slide_xml = archive.read("ppt/slides/slide1.xml")
        self.assertTrue(forbidden_hashes.isdisjoint(media_hashes))
        self.assertTrue(all(archive_size <= 4096 for archive_size in raster_sizes))
        self.assertEqual(len(vector), 9)
        self.assertGreater(slide_xml.count(b"<p:sp>"), 500)
        self.assertIn(b"optimize", slide_xml)

    def test_drawio_pdf_preview_and_validation_boundary(self) -> None:
        drawio_path = DELIVERY_ROOT / "delivery" / "drawio" / "figure.drawio"
        tree = ET.parse(drawio_path)
        cells = tree.findall(".//mxCell")
        edges = [cell for cell in cells if cell.get("edge") == "1"]
        nodes = [cell for cell in cells if cell.get("vertex") == "1"]
        self.assertEqual(len(edges), ARROW_HEAD_COUNT)
        self.assertGreaterEqual(len(nodes), 9)
        self.assertFalse(any("image=" in (cell.get("style") or "") for cell in cells))
        pdf = PdfReader(DELIVERY_ROOT / "delivery" / "pdf" / "publication.pdf")
        self.assertEqual(len(pdf.pages), 1)
        self.assertEqual(len(pdf.pages[0].get("/Resources", {}).get("/XObject", {})), 0)
        self.assertTrue((DELIVERY_ROOT / "preview.png").is_file())
        report = json.loads(
            (DELIVERY_ROOT / "validation" / "segmented_native_validation_report.json").read_text(encoding="utf-8")
        )
        self.assertEqual(report["status"], "VERIFIED_NATIVE_REVIEW_DRAFT")
        self.assertEqual(report["checks"]["embedded_candidate_raster_count"], 0)
        self.assertEqual(report["claims"]["pdf"], "preview/export only; no editability or scientific-correctness claim")
        self.assertIsNone(report["final_scientific_approval"])
        readme = (DELIVERY_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("reference_only_not_embedded", readme)
        self.assertIn("preview/export only", readme)
        self.assertIn("Final scientific approval is `null`", readme)
        self.assertIn("INCOMPLETE_SUPERSEDED_BUILD", readme)


if __name__ == "__main__":
    unittest.main()
