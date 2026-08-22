#!/usr/bin/env python3
"""Render stable equation SVGs from the authoritative LaTeX manifest."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import copy
from pathlib import Path
from typing import Any, Dict, Mapping

from figure_artifacts import load_json, sha256_bytes, sha256_file, write_json
from workflow_v3 import require_valid, write_text


TEX_TEMPLATE = r"""\documentclass[12pt]{article}
\usepackage[active,tightpage]{preview}
\usepackage{amsmath,amssymb,bm}
\PreviewEnvironment{equation*}
\setlength\PreviewBorder{2pt}
\begin{document}
\begin{equation*}
%s
\end{equation*}
\end{document}
"""


def annotate_svg(path: Path, equation: Mapping[str, Any], engine: str) -> None:
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    root = ET.parse(path).getroot()
    root.set("id", "equation-%s" % equation["equation_id"])
    root.set("data-equation-id", equation["equation_id"])
    root.set("data-latex", equation["latex_source"])
    root.set("data-render-engine", engine)
    viewbox = [float(value) for value in root.get("viewBox", "0 0 1 1").split()]
    definitions = {
        item.get("id"): item
        for item in root.findall(".//{http://www.w3.org/2000/svg}defs/{http://www.w3.org/2000/svg}path")
        if item.get("id")
    }
    for use in list(root.findall(".//{http://www.w3.org/2000/svg}use")):
        href = use.get("{http://www.w3.org/1999/xlink}href") or use.get("href", "")
        source = definitions.get(href.lstrip("#"))
        if source is None:
            continue
        replacement = ET.Element("{http://www.w3.org/2000/svg}g", {
            "transform": "translate(%s,%s)" % (use.get("x", "0"), use.get("y", "0")),
            "data-glyph-ref": href.lstrip("#"),
        })
        glyph = copy.deepcopy(source)
        glyph.attrib.pop("id", None)
        replacement.append(glyph)
        parent = next(candidate for candidate in root.iter() if use in list(candidate))
        index = list(parent).index(use)
        parent.remove(use)
        parent.insert(index, replacement)
    page_group = next((item for item in root.findall(".//{http://www.w3.org/2000/svg}g") if item.get("id") == "page1"), None)
    if page_group is not None:
        existing = page_group.get("transform", "")
        page_group.set("transform", "translate(%s,%s) %s" % (-viewbox[0], -viewbox[1], existing))
        root.set("viewBox", "0 0 %s %s" % (viewbox[2], viewbox[3]))
    metadata = ET.Element("{http://www.w3.org/2000/svg}metadata")
    metadata.text = json.dumps({
        "equation_id": equation["equation_id"], "latex_source": equation["latex_source"],
        "checksum": equation["checksum"], "render_engine": engine,
    }, ensure_ascii=False)
    root.insert(0, metadata)
    ET.ElementTree(root).write(path, encoding="unicode", xml_declaration=True)


def render_latex(equation: Mapping[str, Any], output_path: Path) -> Dict[str, Any]:
    latex = shutil.which("latex")
    dvisvgm = shutil.which("dvisvgm")
    if not latex or not dvisvgm:
        return {"status": "BLOCKED", "reason": "latex or dvisvgm unavailable"}
    with tempfile.TemporaryDirectory(prefix="figure-equation-") as temporary:
        temp = Path(temporary)
        tex_path = temp / "equation.tex"
        write_text(tex_path, TEX_TEMPLATE % equation["latex_source"])
        compile_result = subprocess.run(
            [latex, "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
            cwd=temp, capture_output=True, text=True, timeout=60,
        )
        if compile_result.returncode != 0:
            return {"status": "BLOCKED", "reason": "latex failed", "stderr": compile_result.stdout[-2000:]}
        convert_result = subprocess.run(
            [dvisvgm, "--no-fonts", "--exact-bbox", "--output=%s" % output_path.resolve(), str(temp / "equation.dvi")],
            capture_output=True, text=True, timeout=60,
        )
        if convert_result.returncode != 0 or not output_path.exists():
            return {"status": "BLOCKED", "reason": "dvisvgm failed", "stderr": convert_result.stderr[-2000:]}
    annotate_svg(output_path, equation, "latex+dvisvgm")
    return {"status": "VERIFIED", "engine": "latex+dvisvgm"}


def render_mathjax(equation: Mapping[str, Any], output_path: Path) -> Dict[str, Any]:
    node = shutil.which("node")
    modules = os.environ.get("RUNTIME_NODE_MODULES") or os.environ.get("NODE_PATH")
    if not node or not modules:
        return {"status": "BLOCKED", "reason": "local MathJax runtime unavailable"}
    script = r"""
const {mathjax} = require('mathjax-full/js/mathjax.js');
const {TeX} = require('mathjax-full/js/input/tex.js');
const {SVG} = require('mathjax-full/js/output/svg.js');
const {liteAdaptor} = require('mathjax-full/js/adaptors/liteAdaptor.js');
const {RegisterHTMLHandler} = require('mathjax-full/js/handlers/html.js');
const {AllPackages} = require('mathjax-full/js/input/tex/AllPackages.js');
const fs = require('fs');
const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);
const html = mathjax.document('', {InputJax: new TeX({packages: AllPackages}), OutputJax: new SVG({fontCache: 'none'})});
const node = html.convert(process.argv[2], {display: true});
fs.writeFileSync(process.argv[3], adaptor.outerHTML(node));
"""
    with tempfile.TemporaryDirectory(prefix="figure-mathjax-") as temporary:
        js_path = Path(temporary) / "render.js"
        write_text(js_path, script)
        env = dict(os.environ)
        env["NODE_PATH"] = modules
        result = subprocess.run(
            [node, str(js_path), equation["latex_source"], str(output_path.resolve())],
            capture_output=True, text=True, env=env, timeout=60,
        )
    if result.returncode != 0 or not output_path.exists():
        return {"status": "BLOCKED", "reason": "MathJax fallback failed", "stderr": result.stderr[-2000:]}
    annotate_svg(output_path, equation, "mathjax-svg")
    return {"status": "VERIFIED", "engine": "mathjax-svg"}


def render_manifest(manifest_path: Path, output_dir: Path) -> Dict[str, Any]:
    manifest = load_json(manifest_path)
    require_valid(manifest, "equation_manifest.schema.json")
    authoritative = (manifest_path.parent / manifest["authoritative_tex"]).resolve()
    if not authoritative.exists():
        raise FileNotFoundError(authoritative)
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for equation in manifest["equations"]:
        expected = sha256_bytes(equation["latex_source"].encode("utf-8"))
        if equation["checksum"] != expected:
            raise ValueError("equation checksum mismatch: %s" % equation["equation_id"])
        output_path = output_dir / (equation["equation_id"] + ".svg")
        result = render_latex(equation, output_path)
        if result["status"] != "VERIFIED":
            result = render_mathjax(equation, output_path)
        record = {"equation_id": equation["equation_id"], "path": str(output_path.resolve()), **result}
        if output_path.exists():
            record["sha256"] = sha256_file(output_path)
        results.append(record)
    report = {
        "status": "VERIFIED" if all(item["status"] == "VERIFIED" for item in results) else "BLOCKED",
        "manifest": str(manifest_path.resolve()), "authoritative_tex": str(authoritative), "equations": results,
    }
    write_json(output_dir / "equation_render_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    report = render_manifest(args.manifest, args.output_dir)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
