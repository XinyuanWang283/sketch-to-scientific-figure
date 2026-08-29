#!/usr/bin/env python3
"""Focused checks for the candidate-C high-fidelity hybrid delivery."""

from __future__ import annotations

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
DELIVERY_ROOT = EXAMPLE_ROOT / "editable_delivery_c_hybrid"
SCRIPTS = REPOSITORY_ROOT / "scripts"
LOCAL_PATH_MARKERS = (
    "/" + "Users" + "/",
    "/" + "private" + "/" + "tmp" + "/",
)
sys.path.insert(0, str(SCRIPTS))

from build_deep_image_prior_c_hybrid import (  # noqa: E402
    APPROVED_RASTER_ATOMS,
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    EQUATIONS,
    build_spec,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class DeepImagePriorCHybridTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.spec_path = DELIVERY_ROOT / "source" / "hybrid_figure.json"
        cls.spec = json.loads(cls.spec_path.read_text(encoding="utf-8"))

    def test_spec_binds_candidate_c_and_an_explicit_hybrid_contract(self) -> None:
        expected = build_spec(EXAMPLE_ROOT)
        self.assertEqual(expected, self.spec)
        self.assertEqual(self.spec["canvas"], {
            "width": CANVAS_WIDTH,
            "height": CANVAS_HEIGHT,
            "background": "#FFFFFF",
        })
        self.assertEqual(len(self.spec["image_modules"]), 2)
        self.assertEqual(len(self.spec["network_layers"]), 11)
        self.assertEqual(len(self.spec["connectors"]), 7)
        self.assertEqual(len(self.spec["equation_objects"]), 9)
        self.assertFalse(self.spec["editability_contract"]["whole_canvas_raster"])
        self.assertEqual(self.spec["editability_contract"]["approved_raster_atom_count"], 2)
        self.assertEqual(self.spec["editability_contract"]["drawio_role"], "STRUCTURAL_EDITING_VIEW")
        self.assertEqual(self.spec["editability_contract"]["pdf_role"], "MIXED_MEDIA_PREVIEW_EXPORT")
        self.assertIsNone(self.spec["selection"]["final_scientific_approval"])
        self.assertEqual(
            self.spec["visual_reference"]["sha256"],
            sha256_file(EXAMPLE_ROOT / "candidates" / "C-presentation.png"),
        )

    def test_raster_atoms_are_exact_reproducible_crops_and_not_full_canvas(self) -> None:
        manifest = json.loads(
            (DELIVERY_ROOT / "source" / "asset_manifest.json").read_text(encoding="utf-8")
        )
        self.assertFalse(manifest["whole_canvas_raster"])
        self.assertEqual(len(manifest["approved_raster_atoms"]), 2)
        records = {item["id"]: item for item in manifest["approved_raster_atoms"]}
        with Image.open(EXAMPLE_ROOT / "candidates" / "C-presentation.png") as source:
            source = source.convert("RGB")
            for atom_id, policy in APPROVED_RASTER_ATOMS.items():
                asset_path = DELIVERY_ROOT / "source" / records[atom_id]["path"]
                with Image.open(asset_path) as checked:
                    expected = source.crop(tuple(policy["crop_box"]))
                    self.assertIsNone(ImageChops.difference(expected, checked.convert("RGB")).getbbox())
                    self.assertLess(checked.width * checked.height, CANVAS_WIDTH * CANVAS_HEIGHT * 0.30)
                self.assertEqual(records[atom_id]["sha256"], sha256_file(asset_path))
                self.assertFalse(records[atom_id]["scientific_data"])
                self.assertTrue(records[atom_id]["replaceable"])

    def test_latex_is_authoritative_and_all_nine_equations_are_vector_svg(self) -> None:
        manifest = json.loads(
            (DELIVERY_ROOT / "source" / "equation_manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["authoritative_tex"], "equations.tex")
        self.assertEqual(
            [item["latex_source"] for item in manifest["equations"]],
            [item["latex_source"] for item in EQUATIONS],
        )
        for item in manifest["equations"]:
            svg_path = DELIVERY_ROOT / "source" / "math" / f"{item['equation_id']}.svg"
            root = ET.parse(svg_path).getroot()
            self.assertEqual(root.get("data-latex"), item["latex_source"])
            self.assertEqual(root.get("data-equation-id"), item["equation_id"])
            self.assertFalse(any(element.tag.endswith("image") for element in root.iter()))
            self.assertTrue(any(element.tag.endswith("path") for element in root.iter()))
        equations_tex = (DELIVERY_ROOT / "source" / "equations.tex").read_text(encoding="utf-8")
        self.assertIn(r"\theta^{\ast}", equations_tex)
        self.assertIn(r"\operatorname*{arg\,min}_{\theta}", equations_tex)
        self.assertNotIn(r"\theta^\*", equations_tex)

    def test_svg_has_two_approved_png_atoms_and_nine_vector_equations(self) -> None:
        svg_path = DELIVERY_ROOT / "delivery" / "svg" / "master.svg"
        root = ET.parse(svg_path).getroot()
        images = [element for element in root.iter() if element.tag.endswith("image")]
        hrefs = [
            element.get("href")
            or element.get("{http://www.w3.org/1999/xlink}href")
            or ""
            for element in images
        ]
        self.assertEqual(sum(value.startswith("data:image/png;base64,") for value in hrefs), 2)
        self.assertEqual(sum(value.startswith("data:image/svg+xml;base64,") for value in hrefs), 9)
        self.assertFalse(any(value.startswith(("file:", "http:", "https:")) for value in hrefs))
        self.assertEqual(
            len([element for element in root.iter() if element.get("data-source")]),
            7,
        )

    def test_pptx_contains_only_two_raster_atoms_and_nine_vector_equations(self) -> None:
        pptx_path = DELIVERY_ROOT / "delivery" / "pptx" / "figure.pptx"
        with zipfile.ZipFile(pptx_path) as archive:
            media = [name for name in archive.namelist() if name.startswith("ppt/media/")]
            raster = [
                name
                for name in media
                if name.lower().endswith((".png", ".jpg", ".jpeg"))
                and archive.getinfo(name).file_size > 1000
            ]
            svg_fallbacks = [
                name
                for name in media
                if name.lower().endswith(".png")
                and archive.getinfo(name).file_size <= 1000
            ]
            vector = [name for name in media if name.lower().endswith(".svg")]
            notes = b"\n".join(
                archive.read(name)
                for name in archive.namelist()
                if name.startswith("ppt/notesSlides/") and name.endswith(".xml")
            )
            slide_xml = archive.read("ppt/slides/slide1.xml")
        self.assertEqual(len(raster), 2)
        self.assertEqual(len(svg_fallbacks), 9)
        self.assertEqual(len(vector), 9)
        for marker in LOCAL_PATH_MARKERS:
            self.assertNotIn(marker.encode("utf-8"), notes)
        self.assertIn(b"eq_objective", notes)
        self.assertIn(b"noise-raster-atom", slide_xml)
        self.assertIn(b"reconstruction-raster-atom", slide_xml)

    def test_drawio_is_an_honest_native_structural_view(self) -> None:
        path = DELIVERY_ROOT / "delivery" / "drawio" / "figure.drawio"
        tree = ET.parse(path)
        cells = tree.findall(".//mxCell")
        edges = [item for item in cells if item.get("edge") == "1"]
        placeholders = [
            item for item in cells
            if item.get("semanticType") == "replaceable-raster-placeholder"
        ]
        self.assertEqual(len(edges), 7)
        self.assertEqual(len(placeholders), 2)
        self.assertFalse(any("data:image" in (item.get("style") or "") for item in cells))
        report = json.loads(
            (DELIVERY_ROOT / "delivery" / "drawio" / "drawio_export_report.json").read_text(encoding="utf-8")
        )
        self.assertEqual(report["status"], "STRUCTURAL_EDITING_VIEW")
        self.assertFalse(report["high_fidelity_visual_master"])

    def test_pdf_and_portable_validation_report_keep_claims_honest(self) -> None:
        pdf_path = DELIVERY_ROOT / "delivery" / "pdf" / "publication.pdf"
        self.assertEqual(len(PdfReader(pdf_path).pages), 1)
        report_path = DELIVERY_ROOT / "validation" / "hybrid_validation_report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "VERIFIED_HYBRID_REVIEW_DRAFT")
        self.assertEqual(report["checks"]["approved_raster_atom_count"], 2)
        self.assertEqual(report["checks"]["svg_vector_equation_count"], 9)
        self.assertEqual(report["checks"]["pptx_vector_equation_count"], 9)
        self.assertEqual(report["claims"]["pdf"], "mixed-media preview/export; no semantic-editability claim")
        self.assertIsNone(report["final_scientific_approval"])
        serialized = "\n".join(
            path.read_text(encoding="utf-8")
            for path in DELIVERY_ROOT.rglob("*.json")
        )
        for marker in LOCAL_PATH_MARKERS:
            self.assertNotIn(marker, serialized)


if __name__ == "__main__":
    unittest.main()
