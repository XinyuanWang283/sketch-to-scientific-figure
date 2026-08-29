#!/usr/bin/env python3
"""Assemble five separately generated candidate PNGs into a labeled comparison sheet."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageDraw, ImageFont


LABELS = ("A — Faithful", "B — Publication", "C — Presentation", "D — Alternative layout", "E — Visual variant")


def _font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("Arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def build_sheet(inputs: Sequence[Path], output: Path) -> Path:
    """Create a 2×3 contact sheet without changing the five originals."""
    if len(inputs) != 5:
        raise ValueError("exactly five candidate PNGs are required")
    if output.exists():
        raise FileExistsError("refusing to overwrite comparison sheet: %s" % output)

    images: list[Image.Image] = []
    for path in inputs:
        if not path.is_file() or path.suffix.lower() != ".png":
            raise ValueError("candidate must be an existing PNG: %s" % path)
        with Image.open(path) as source:
            source.verify()
        with Image.open(path) as source:
            images.append(source.convert("RGB"))

    cell_width = 900
    cell_height = 590
    label_height = 54
    margin = 28
    sheet = Image.new("RGB", (cell_width * 3, cell_height * 2), "white")
    draw = ImageDraw.Draw(sheet)
    font = _font(30)

    positions = ((0, 0), (1, 0), (0, 1), (1, 1), (2, 1))
    for image, label, (column, row) in zip(images, LABELS, positions):
        available = (cell_width - 2 * margin, cell_height - label_height - 2 * margin)
        image.thumbnail(available, Image.Resampling.LANCZOS)
        left = column * cell_width + (cell_width - image.width) // 2
        top = row * cell_height + label_height + (cell_height - label_height - image.height) // 2
        sheet.paste(image, (left, top))
        draw.text(
            (column * cell_width + margin, row * cell_height + 14),
            label,
            fill="#0f2747",
            font=font,
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, format="PNG", optimize=True)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build_sheet(args.input, args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
