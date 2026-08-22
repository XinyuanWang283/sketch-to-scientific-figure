#!/usr/bin/env python3
"""Export publication and grayscale vector PDFs directly from semantic JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from figure_artifacts import load_json, sha256_file, write_json
from workflow_v3 import render_semantic_pdf, semantic_integrity_errors


def export(semantic_path: Path, output_dir: Path) -> Dict[str, Any]:
    semantic = load_json(semantic_path)
    errors = semantic_integrity_errors(semantic)
    if errors:
        raise ValueError("invalid semantic source:\n%s" % "\n".join(errors))
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for name, grayscale in [("publication.pdf", False), ("grayscale.pdf", True)]:
        pdf_path = output_dir / name
        result = render_semantic_pdf(semantic, pdf_path, grayscale=grayscale)
        if pdf_path.exists():
            result["bytes"] = pdf_path.stat().st_size
        outputs.append({"path": str(pdf_path.resolve()), "grayscale": grayscale, **result})
    report = {
        "status": "VERIFIED" if all(item["status"] == "VERIFIED" for item in outputs) else "BLOCKED",
        "canonical_source": str(semantic_path.resolve()), "canonical_source_sha256": sha256_file(semantic_path),
        "outputs": outputs, "semantic_editability": False, "equation_source_editability": False,
        "vector_policy": "PDF is a vector publication deliverable; canonical semantic JSON and equations.tex remain the editable sources.",
        "whole_canvas_raster": False,
    }
    write_json(output_dir / "pdf_export_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--semantic", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    report = export(args.semantic, args.output_dir)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
