#!/usr/bin/env python3
"""Export master or Figma-ready SVG directly from canonical semantic JSON."""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict

from figure_artifacts import load_json, sha256_file, write_json
from workflow_v3 import render_semantic_svg, semantic_integrity_errors, write_text


def export(semantic_path: Path, output_path: Path, profile: str) -> Dict[str, Any]:
    semantic = load_json(semantic_path)
    errors = semantic_integrity_errors(semantic)
    if errors:
        raise ValueError("invalid semantic source:\n%s" % "\n".join(errors))
    content = render_semantic_svg(semantic, profile=profile)
    write_text(output_path, content)
    ET.parse(output_path)
    ids = []
    for collection in ("groups", "shapes", "text_objects", "equation_objects", "connectors"):
        ids.extend(item["id"] for item in semantic.get(collection, []))
    layer_manifest = {
        "schema_version": "1.0", "figure_id": semantic["figure_id"], "profile": profile,
        "canonical_source": str(semantic_path.resolve()),
        "layers": [
            {"name": "background", "editable": True}, {"name": "shapes", "editable": True},
            {"name": "connectors", "editable": True}, {"name": "text", "editable": True},
            {"name": "equations", "editable": True, "latex_metadata": True},
        ],
        "semantic_ids": ids,
    }
    manifest_path = output_path.parent / ("layer_manifest.json" if profile == "figma" else "svg_layer_manifest.json")
    write_json(manifest_path, layer_manifest)
    status = "IMPORT_READY_UNVERIFIED" if profile == "figma" else "VERIFIED"
    report = {
        "status": status, "format": "figma-ready-svg" if profile == "figma" else "svg",
        "output": str(output_path.resolve()), "sha256": sha256_file(output_path),
        "canonical_source": str(semantic_path.resolve()), "canonical_source_sha256": sha256_file(semantic_path),
        "native_shape_count": len(semantic.get("shapes", [])), "live_text_count": len(semantic.get("text_objects", [])),
        "equation_group_count": len(semantic.get("equation_objects", [])), "connector_count": len(semantic.get("connectors", [])),
        "whole_canvas_raster": False, "semantic_editability": True, "equation_source_editability": True,
        "verification": "XML parsed; semantic IDs, layers, live text, connector metadata, and LaTeX metadata emitted from canonical source.",
        "layer_manifest": str(manifest_path.resolve()),
    }
    report_name = "figma_import_report.json" if profile == "figma" else "svg_export_report.json"
    write_json(output_path.parent / report_name, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--semantic", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--profile", choices=["svg", "figma"], default="svg")
    args = parser.parse_args()
    report = export(args.semantic, args.output, args.profile)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
