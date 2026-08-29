from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from PIL import Image, ImageChops
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from build_deep_image_prior_c_fidelity_v2 import (  # noqa: E402
    APPROVED_RASTER_ATOMS,
    ARROW_HEAD_COUNT,
    build_selected_candidate_map,
    sha256_file,
    validate_package,
)


EXAMPLE_ROOT = ROOT / "examples" / "deep_image_prior"
DELIVERY_ROOT = EXAMPLE_ROOT / "editable_delivery_c_fidelity_v2"


class DeepImagePriorCFidelityV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.candidate_path = EXAMPLE_ROOT / "candidates" / "C-presentation.png"
        cls.source_dir = DELIVERY_ROOT / "source"
        cls.semantic = json.loads((cls.source_dir / "semantic_figure.json").read_text(encoding="utf-8"))
        cls.selected_map = json.loads((cls.source_dir / "selected_candidate_map.json").read_text(encoding="utf-8"))
        cls.assets = json.loads((cls.source_dir / "asset_manifest.json").read_text(encoding="utf-8"))
        cls.equations = json.loads((cls.source_dir / "equation_manifest.json").read_text(encoding="utf-8"))

    def test_selected_map_is_hash_bound_and_limits_local_fitting_to_synthetic_glyphs(self) -> None:
        self.assertEqual(self.selected_map, build_selected_candidate_map(EXAMPLE_ROOT))
        self.assertEqual(self.selected_map["image_hash"], sha256_file(self.candidate_path))
        policy = self.selected_map["reference_fit_policy"]
        self.assertEqual(policy["scope"], "two decorative synthetic signal glyphs only")
        self.assertFalse(policy["scientific_data"])
        self.assertFalse(policy["whole_image_tracing"])
        self.assertIsNone(policy["final_visual_approval"])
        self.assertIsNone(policy["final_scientific_approval"])

    def test_two_raster_atoms_are_exact_unresampled_replaceable_crops(self) -> None:
        self.assertEqual(len(self.assets["assets"]), 2)
        with Image.open(self.candidate_path) as candidate:
            for asset in self.assets["assets"]:
                self.assertIn(asset["id"], APPROVED_RASTER_ATOMS)
                self.assertTrue(asset["exact_pixel_crop"])
                self.assertFalse(asset["resampled"])
                self.assertTrue(asset["replaceable"])
                self.assertFalse(asset["pixel_editable"])
                self.assertFalse(asset["scientific_evidence"])
                left, top, right, bottom = asset["bbox"]
                expected = candidate.crop((left, top, right, bottom)).convert("RGBA")
                with Image.open(self.source_dir / asset["path"]) as actual:
                    self.assertIsNone(ImageChops.difference(expected, actual.convert("RGBA")).getbbox())

    def test_generator_has_eleven_native_gradient_faces_and_no_generator_raster(self) -> None:
        network = self.semantic["regions"]["generator-network"]
        self.assertEqual(len(self.semantic["network_layer_groups"]), 11)
        self.assertEqual(len(network), 33)
        faces = [item for item in network if item["id"].endswith("-face")]
        self.assertEqual(len(faces), 11)
        for face in faces:
            fill = face["fill"]
            self.assertEqual(fill["type"], "gradient")
            self.assertEqual(fill["gradientKind"], "linear")
            self.assertGreaterEqual(len(fill["stops"]), 2)
        generator_ids = {item["id"] for item in self.semantic["image_modules"]}
        self.assertNotIn("generator-network", generator_ids)

    def test_plots_are_two_reference_fitted_polylines_without_cosmetic_dots(self) -> None:
        shapes = [item for group in self.semantic["regions"].values() for item in group]
        self.assertFalse(any("-sample-" in item["id"] for item in shapes))
        curves = [item for item in shapes if item["id"].endswith("-curve")]
        self.assertEqual({item["id"] for item in curves}, {"predicted-plot-curve", "observed-plot-curve"})
        for curve in curves:
            self.assertEqual(curve["type"], "polyline")
            self.assertGreaterEqual(len(curve["points"]), 30)
            self.assertLessEqual(len(curve["points"]), 50)
            fit = curve["reference_fit"]
            self.assertGreaterEqual(fit["coverage"], 0.98)
            self.assertLessEqual(fit["median_vertical_error_px"], 1.5)
            self.assertLessEqual(fit["max_vertical_error_px"], 4)
            self.assertFalse(fit["scientific_data"])
            self.assertTrue(fit["human_review_required"])

    def test_svg_uses_gradients_small_explicit_arrows_and_only_two_relative_images(self) -> None:
        svg_path = DELIVERY_ROOT / "delivery" / "svg" / "master.svg"
        root = ET.parse(svg_path).getroot()
        text = svg_path.read_text(encoding="utf-8")
        self.assertGreaterEqual(text.count("<linearGradient"), 14)
        for forbidden in ("marker-end", "<marker", "<filter", "<radialGradient", "<mask"):
            self.assertNotIn(forbidden, text)
        images = [node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "image"]
        self.assertEqual(len(images), 2)
        self.assertEqual(
            {node.get("href") for node in images},
            {"assets/noise-content.png", "assets/reconstruction-content.png"},
        )
        arrows = [node for node in root.iter() if (node.get("id") or "").endswith("-arrowhead")]
        self.assertEqual(len(arrows), ARROW_HEAD_COUNT)
        for arrow in arrows:
            points = [tuple(map(float, item.split(","))) for item in arrow.get("points", "").split()]
            extent = max(
                max(point[0] for point in points) - min(point[0] for point in points),
                max(point[1] for point in points) - min(point[1] for point in points),
            )
            self.assertGreaterEqual(extent, 12.0)
            self.assertLessEqual(extent, 14.5)

    def test_colored_latex_equations_are_raster_free_and_not_stretched(self) -> None:
        self.assertEqual(len(self.equations["equations"]), 9)
        by_id = {item["equation_id"]: item for item in self.equations["equations"]}
        for item in by_id.values():
            intrinsic = item["intrinsic_viewbox"]
            target = item["target_position"]
            intrinsic_ratio = intrinsic[2] / intrinsic[3]
            target_ratio = target["width"] / target["height"]
            self.assertAlmostEqual(target_ratio, intrinsic_ratio, delta=intrinsic_ratio * 0.005)
            root = ET.parse(self.source_dir / "math" / f"{item['equation_id']}.svg").getroot()
            self.assertTrue(any(node.tag.endswith("path") for node in root.iter()))
            self.assertFalse(any(node.tag.endswith("image") for node in root.iter()))
        objective = (self.source_dir / "math" / "eq_objective.svg").read_text(encoding="utf-8").lower()
        reconstruction = (self.source_dir / "math" / "eq_reconstruction.svg").read_text(encoding="utf-8").lower()
        self.assertIn("#5a258c", objective)
        self.assertIn("#0d2f6e", objective)
        self.assertIn("#0b6262", reconstruction)
        self.assertIn("#5a258c", reconstruction)
        self.assertIn("#0d2f6e", reconstruction)
        generator = by_id["eq_generator"]["target_position"]
        self.assertLessEqual(generator["height"], 44.0)

    def test_pptx_contains_native_gradients_alpha_curves_and_expected_media(self) -> None:
        pptx_path = DELIVERY_ROOT / "delivery" / "pptx" / "figure.pptx"
        approved_hashes = {item["sha256"] for item in self.assets["assets"]}
        with zipfile.ZipFile(pptx_path) as archive:
            media = [name for name in archive.namelist() if name.startswith("ppt/media/")]
            vector = [name for name in media if name.lower().endswith(".svg")]
            rasters = [
                name for name in media
                if name.lower().endswith((".png", ".jpg", ".jpeg"))
                and archive.getinfo(name).file_size > 4096
            ]
            raster_hashes = {hashlib.sha256(archive.read(name)).hexdigest() for name in rasters}
            slide_xml = archive.read("ppt/slides/slide1.xml")
        self.assertEqual(len(vector), 9)
        self.assertEqual(len(rasters), 2)
        self.assertEqual(raster_hashes, approved_hashes)
        self.assertIn(b"<a:gradFill", slide_xml)
        self.assertIn(b"<a:alpha", slide_xml)
        self.assertIn(b"<a:custGeom", slide_xml)
        self.assertLess(
            slide_xml.index(b"measurement-panel-fill"),
            slide_xml.index(b"flow-predicted-loss-shaft"),
        )
        self.assertLess(
            slide_xml.index(b"measurement-panel-fill"),
            slide_xml.index(b"flow-observed-loss-shaft"),
        )
        self.assertGreaterEqual(
            slide_xml.count(b"<p:sp>"),
            self.semantic["editability_contract"]["native_region_shape_minimum"],
        )

    def test_drawio_exposes_layers_curves_and_only_seven_topology_edges(self) -> None:
        tree = ET.parse(DELIVERY_ROOT / "delivery" / "drawio" / "figure.drawio")
        cells = tree.findall(".//mxCell")
        self.assertEqual(len([item for item in cells if item.get("semanticType") == "editable-generator-layer"]), 11)
        self.assertEqual(
            len([item for item in cells if item.get("semanticType") == "editable-reference-fitted-synthetic-curve"]),
            2,
        )
        self.assertEqual(len([item for item in cells if item.get("relationType")]), 7)
        self.assertEqual(len([item for item in cells if item.get("semanticType") == "replaceable-raster-atom"]), 2)

    def test_pdf_and_region_qa_are_explicitly_review_only(self) -> None:
        self.assertEqual(len(PdfReader(DELIVERY_ROOT / "delivery" / "pdf" / "publication.pdf").pages), 1)
        visual = json.loads((DELIVERY_ROOT / "validation" / "visual_fidelity_report.json").read_text(encoding="utf-8"))
        self.assertEqual(visual["status"], "MEASURED_FOR_HUMAN_VISUAL_REVIEW")
        self.assertEqual(len(visual["regions"]), 8)
        self.assertIsNone(visual["final_visual_approval"])
        self.assertIsNone(visual["final_scientific_approval"])
        for item in visual["regions"].values():
            self.assertTrue(item["human_review_required"])
            self.assertTrue((DELIVERY_ROOT / "validation" / item["comparison"]).is_file())

    def test_portable_json_and_validation_do_not_claim_scientific_approval(self) -> None:
        report = json.loads((DELIVERY_ROOT / "validation" / "fidelity_v2_validation_report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "VERIFIED_FIDELITY_V2_REVIEW_DRAFT")
        self.assertIsNone(report["final_visual_approval"])
        self.assertIsNone(report["final_scientific_approval"])
        serialized = "\n".join(path.read_text(encoding="utf-8") for path in DELIVERY_ROOT.rglob("*.json"))
        for marker in (
            "/" + "Users/",
            "/" + "private/",
            "/" + "home/",
            "file" + "://",
        ):
            self.assertNotIn(marker, serialized)

    def test_validation_accepts_explicit_candidate_path_for_external_output_roots(self) -> None:
        report = validate_package(
            DELIVERY_ROOT,
            candidate_path=self.candidate_path,
            write_report=False,
        )
        self.assertEqual(report["status"], "VERIFIED_FIDELITY_V2_REVIEW_DRAFT")

    def test_validation_rejects_weakened_raster_authorization(self) -> None:
        mutations = {
            "status": lambda value: value.__setitem__("status", "REJECTED"),
            "authorized_atoms": lambda value: value.__setitem__("authorized_atoms", []),
            "bbox": lambda value: value["authorized_atoms"][0].__setitem__(
                "bbox", [0, 0, 1, 1]
            ),
            "asset_path": lambda value: value["authorized_atoms"][0].__setitem__(
                "asset_path", "raster_atoms/other.png"
            ),
            "constraint": lambda value: value["constraints"].__setitem__(
                "synthetic_visual_only", False
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory(
                prefix=f"c-fidelity-v2-raster-{label}-"
            ) as temporary:
                clone = Path(temporary) / "delivery"
                shutil.copytree(DELIVERY_ROOT, clone)
                decision_path = clone / "source/raster_atom_review_decision.json"
                decision = json.loads(decision_path.read_text(encoding="utf-8"))
                mutate(decision)
                decision_path.write_text(json.dumps(decision), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "review decision"):
                    validate_package(
                        clone,
                        candidate_path=self.candidate_path,
                        write_report=False,
                    )

    def test_validation_rejects_missing_or_escaping_declared_artifacts(self) -> None:
        with tempfile.TemporaryDirectory(prefix="c-fidelity-v2-validation-") as temporary:
            clone = Path(temporary) / "delivery"
            shutil.copytree(DELIVERY_ROOT, clone)
            for relative in (
                Path("delivery/svg/assets/noise-content.png"),
                Path("source/math/eq_z.svg"),
                Path("validation/region_comparisons/generator_network.png"),
            ):
                victim = clone / relative
                victim.unlink()
                with self.subTest(relative=relative):
                    with self.assertRaises(ValueError):
                        validate_package(
                            clone,
                            candidate_path=self.candidate_path,
                            write_report=False,
                        )
                shutil.copy2(DELIVERY_ROOT / relative, victim)

            escaping_atom = clone / "source/raster_atoms/noise-content.png"
            escaping_atom.unlink()
            escaping_atom.symlink_to(self.candidate_path)
            with self.assertRaisesRegex(ValueError, "escapes its package directory"):
                validate_package(
                    clone,
                    candidate_path=self.candidate_path,
                    write_report=False,
                )

            escaping_atom.unlink()
            shutil.copy2(
                DELIVERY_ROOT / "source/raster_atoms/noise-content.png",
                escaping_atom,
            )
            pptx_path = clone / "delivery/pptx/figure.pptx"
            with zipfile.ZipFile(pptx_path, "a") as archive:
                archive.writestr(
                    "ppt/media/extra-approved-copy.png",
                    (DELIVERY_ROOT / "source/raster_atoms/noise-content.png").read_bytes(),
                )
            with self.assertRaisesRegex(ValueError, "PPTX media boundary"):
                validate_package(
                    clone,
                    candidate_path=self.candidate_path,
                    write_report=False,
                )

            shutil.copy2(DELIVERY_ROOT / "delivery/pptx/figure.pptx", pptx_path)
            visual_path = clone / "validation/visual_fidelity_report.json"
            visual = json.loads(visual_path.read_text(encoding="utf-8"))
            visual["reference_sha256"] = "0" * 64
            visual_path.write_text(json.dumps(visual), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "visual QA reference hash"):
                validate_package(
                    clone,
                    candidate_path=self.candidate_path,
                    write_report=False,
                )

            shutil.copy2(DELIVERY_ROOT / "validation/visual_fidelity_report.json", visual_path)
            outside_json = Path(temporary) / "outside.json"
            outside_json.write_text("{}", encoding="utf-8")
            (clone / "unexpected.json").symlink_to(outside_json)
            with self.assertRaisesRegex(ValueError, "escapes its package directory"):
                validate_package(
                    clone,
                    candidate_path=self.candidate_path,
                    write_report=False,
                )


if __name__ == "__main__":
    unittest.main()
