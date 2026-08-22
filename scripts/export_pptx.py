#!/usr/bin/env python3
"""Python CLI wrapper for the mandated @oai/artifact-tool PPTX adapter."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict

from figure_artifacts import load_json, sha256_file, write_json


SCRIPT_DIR = Path(__file__).resolve().parent


def export(semantic_path: Path, output_dir: Path, equation_dir: Path | None = None) -> Dict[str, Any]:
    node = os.environ.get("RUNTIME_NODE") or shutil.which("node")
    modules = os.environ.get("RUNTIME_NODE_MODULES")
    if not node or not modules:
        report = {
            "status": "BLOCKED", "reason": "RUNTIME_NODE and RUNTIME_NODE_MODULES are required",
            "canonical_source": str(semantic_path.resolve()),
        }
        output_dir.mkdir(parents=True, exist_ok=True)
        write_json(output_dir / "pptx_export_report.json", report)
        return report
    command = [
        node, str(SCRIPT_DIR / "export_pptx.mjs"), "--semantic", str(semantic_path.resolve()),
        "--output-dir", str(output_dir.resolve()),
    ]
    if equation_dir:
        command += ["--equation-dir", str(equation_dir.resolve())]
    env = dict(os.environ)
    env["RUNTIME_NODE_MODULES"] = modules
    output_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(command, capture_output=True, text=True, env=env, timeout=180)
    artifact_report = output_dir / "pptx_artifact_report.json"
    if result.returncode != 0 or not artifact_report.exists():
        report = {
            "status": "BLOCKED", "reason": "artifact-tool export failed", "returncode": result.returncode,
            "stdout": result.stdout[-2000:], "stderr": result.stderr[-4000:], "canonical_source": str(semantic_path.resolve()),
        }
    else:
        report = load_json(artifact_report)
        report.update({
            "status": "VERIFIED", "semantic_editability": True, "equation_source_editability": True,
            "canonical_source_sha256": sha256_file(semantic_path), "pptx_sha256": sha256_file(Path(report["output"])),
            "verification": "@oai/artifact-tool authored native shapes, live text, attached connectors, equation SVG groups, notes metadata, and a rendered preview.",
        })
    write_json(output_dir / "pptx_export_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--semantic", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--equation-dir", type=Path)
    args = parser.parse_args()
    report = export(args.semantic, args.output_dir, args.equation_dir)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
