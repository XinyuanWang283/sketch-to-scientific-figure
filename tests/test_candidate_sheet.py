#!/usr/bin/env python3
"""Tests for the non-generative five-candidate comparison sheet builder."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from build_candidate_sheet import build_sheet  # noqa: E402


class CandidateSheetTests(unittest.TestCase):
    def test_builds_sheet_from_exactly_five_pngs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="candidate-sheet-") as temporary:
            root = Path(temporary)
            inputs = []
            for index in range(5):
                path = root / ("candidate-%d.png" % index)
                Image.new("RGB", (320, 180), (20 * index, 80, 140)).save(path)
                inputs.append(path)
            output = build_sheet(inputs, root / "comparison.png")
            with Image.open(output) as sheet:
                self.assertEqual(sheet.size, (2700, 1180))

    def test_rejects_wrong_count_and_existing_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="candidate-sheet-fail-") as temporary:
            root = Path(temporary)
            inputs = []
            for index in range(5):
                path = root / ("candidate-%d.png" % index)
                Image.new("RGB", (32, 18), "white").save(path)
                inputs.append(path)
            with self.assertRaisesRegex(ValueError, "exactly five"):
                build_sheet(inputs[:4], root / "comparison.png")
            output = root / "existing.png"
            output.write_bytes(b"existing")
            with self.assertRaises(FileExistsError):
                build_sheet(inputs, output)


if __name__ == "__main__":
    unittest.main()
