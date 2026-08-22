# Synthetic restoration example

This fictional, non-confidential example shows the repository's authority chain without using experimental data or an unpublished method.

| 1. Rough sketch | 2. Deterministic topology | 3. Editable semantic SVG |
|---|---|---|
| [Open sketch](sketch.svg) | [Open skeleton](skeletons/synthetic_restoration_skeleton.svg) | [Open final SVG](editable_figure.svg) |

The method note and sketch are hashed in [`scientific_truth.json`](truth/scientific_truth.json). The blueprint binds the three truth instances to regions, ports, and directed edges. The topology renderer then produces the SVG/PNG skeleton from that blueprint. The final SVG keeps groups, labels, equations, connectors, IDs, and style tokens editable.

## Reproduce the checked artifacts

From the repository root:

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

The example intentionally makes no claim about accuracy, image quality, clinical utility, or time saved.
