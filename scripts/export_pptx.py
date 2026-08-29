#!/usr/bin/env python3
"""Python CLI wrapper for the mandated @oai/artifact-tool PPTX adapter."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any, Dict, Mapping

from figure_artifacts import load_json, sha256_file, write_json


SCRIPT_DIR = Path(__file__).resolve().parent
PML = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
AML = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}


def _repair_connector_references(pptx_path: Path, semantic: Mapping[str, Any]) -> Dict[str, Any]:
    """Bind artifact-tool connector references to the exported OOXML object IDs."""
    with zipfile.ZipFile(pptx_path) as archive:
        infos = archive.infolist()
        payloads = {info.filename: archive.read(info.filename) for info in infos}
    slide_name = "ppt/slides/slide1.xml"
    if slide_name not in payloads:
        raise ValueError("artifact-tool PPTX is missing slide1.xml")
    slide = ET.fromstring(payloads[slide_name])
    name_to_id: Dict[str, str] = {}
    for element in slide.findall(".//p:sp", PML):
        properties = element.find(".//p:cNvPr", PML)
        if properties is not None and properties.get("name") and properties.get("id"):
            name = str(properties.get("name"))
            if name in name_to_id:
                raise ValueError("duplicate PPTX object name: %s" % name)
            name_to_id[name] = str(properties.get("id"))
    connector_map: Dict[str, ET.Element] = {}
    for connector in slide.findall(".//p:cxnSp", PML):
        properties = connector.find(".//p:cNvPr", PML)
        if properties is not None and properties.get("name"):
            connector_map[str(properties.get("name"))] = connector

    repaired = 0
    bindings = []
    for item in semantic.get("connectors", []):
        identifier = str(item.get("id", ""))
        source = str(item.get("source_id", ""))
        target = str(item.get("target_id", ""))
        connector = connector_map.get(identifier)
        if connector is None or source not in name_to_id or target not in name_to_id:
            raise ValueError("cannot bind PPTX connector %s to %s -> %s" % (identifier, source, target))
        start = connector.find(".//a:stCxn", AML)
        end = connector.find(".//a:endCxn", AML)
        if start is None or end is None:
            raise ValueError("PPTX connector %s has no OOXML endpoint references" % identifier)
        expected_start, expected_end = name_to_id[source], name_to_id[target]
        if start.get("id") != expected_start or end.get("id") != expected_end:
            start.set("id", expected_start)
            end.set("id", expected_end)
            repaired += 1
        bindings.append({
            "connector_id": identifier, "source_object_id": expected_start, "target_object_id": expected_end,
        })

    payloads[slide_name] = ET.tostring(slide, encoding="utf-8", xml_declaration=True)
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix="pptx-connector-repair-", suffix=".pptx", dir=pptx_path.parent, delete=False
        ) as temporary:
            temporary_name = temporary.name
        with zipfile.ZipFile(temporary_name, "w") as output:
            for info in infos:
                output.writestr(info, payloads[info.filename])
        os.replace(temporary_name, pptx_path)
        temporary_name = None
    finally:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)
    return {"repaired_connector_count": repaired, "connector_bindings": bindings}


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
        try:
            semantic = load_json(semantic_path)
            repair = _repair_connector_references(Path(report["output"]), semantic)
            report.update({
                "status": "VERIFIED", "semantic_editability": True, "equation_source_editability": True,
                "canonical_source_sha256": sha256_file(semantic_path), "pptx_sha256": sha256_file(Path(report["output"])),
                "verification": "@oai/artifact-tool authored native objects; connector OOXML references were rebound to exported object IDs. Cross-format validation is still required.",
                **repair,
            })
        except (KeyError, OSError, ValueError, ET.ParseError, zipfile.BadZipFile) as error:
            report.update({
                "status": "BLOCKED", "reason": "PPTX connector binding repair failed", "error": str(error),
                "semantic_editability": False, "equation_source_editability": False,
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
