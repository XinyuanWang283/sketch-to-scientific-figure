# Synthetic restoration example

> **Offline adapter fixture, not the default ImageGen user path.** For the current sketch-to-five-candidates example, see the [Deep Image Prior example](../deep_image_prior/README.md).

This fictional, non-confidential fixture shows the retained deterministic authority chain without using experimental data or an unpublished method. It is useful for native-object and validation regression tests after candidate approval, but it does not execute or simulate five Codex ImageGen calls.

| 1. Rough sketch | 2. Deterministic topology | 3. Editable semantic SVG |
|---|---|---|
| [Open sketch](sketch.svg) | [Open skeleton](skeletons/synthetic_restoration_skeleton.svg) | [Open final SVG](editable_figure.svg) |

The method note and sketch are hashed in [`scientific_truth.json`](truth/scientific_truth.json). The blueprint binds the three truth instances to regions, ports, and directed edges. The topology renderer then produces the SVG/PNG skeleton from that blueprint. The checked-in semantic SVG keeps groups, labels, equations, connectors, IDs, and style tokens editable.

## Run the publication-safe replay

From the repository root with Python 3.11 or newer, install the declared dependencies and choose a new output directory outside the repository:

```bash
python -m pip install -r requirements.txt
python scripts/run_synthetic_demo.py \
  --mode core \
  --output-dir /tmp/synthetic-restoration-core-01
```

This command uses no AI, network, API key, or credentials. It replays [`reviewed_interpretation.json`](demo/reviewed_interpretation.json) and the checked-in Gate 1/2 pre-approval records, verifies their hashes, builds the topology and canonical semantic source, emits editable SVG, and stops with `INCOMPLETE`. Those pre-approvals demonstrate deterministic gate enforcement; they are not live human decisions and are not scientific validation.

Full mode uses the documented native adapter runtime:

```bash
python scripts/run_synthetic_demo.py \
  --mode full \
  --output-dir /tmp/synthetic-restoration-full-01
```

A successful full run produces SVG, native PPTX, native draw.io, Figma-ready SVG, PDF exports, and a cross-format report, then stops at Gate 3 with `AWAITING_DECISION`. Figma-ready SVG remains `IMPORT_READY_UNVERIFIED`; PDF reports use `semantic_editability=false`. `VERIFIED` describes programmable structural checks, not scientific correctness. See the [Science Day demo guide](../../docs/science-day-demo.md) for the artifact walkthrough, fallback, and explicit final-approval boundary.

## Validate the checked-in artifacts

These lower-level commands operate on the checked-in example. Run them from the repository root only when you intend to verify or regenerate those paths:

```bash
python3 scripts/compile_figure_artifacts.py --run-dir examples/synthetic_restoration
python3 scripts/render_topology_skeleton.py \
  --truth examples/synthetic_restoration/truth/scientific_truth.json \
  --blueprint examples/synthetic_restoration/blueprints/synthetic_restoration.json \
  --output-dir examples/synthetic_restoration/skeletons
python3 scripts/validate_figure_artifacts.py \
  --run-dir examples/synthetic_restoration \
  --source-root .
python3 scripts/validate_semantic_svg.py \
  --svg examples/synthetic_restoration/editable_figure.svg \
  --spec examples/synthetic_restoration/validation_spec.json
```

The example intentionally makes no claim about accuracy, image quality, clinical utility, human performance, publication readiness, or time saved. It contains no generated visual-direction candidate, so it also makes no generator-provenance claim.
