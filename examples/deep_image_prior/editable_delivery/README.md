# Historical editable reconstruction: D layout + C visual style

**Review status:** `REJECTED_FOR_VISUAL_REVISION`. The researcher later chose candidate C alone, rejected its first native-only reconstruction for insufficient visual fidelity, and moved to a [high-fidelity hybrid review draft](../editable_delivery_c_hybrid/README.md). This directory is retained as decision history; the generated artifacts below have not been replaced.

The researcher explicitly approved this combination on 2026-08-27:

> Use D's layout with C's visual style

Candidate D supplies the spatial layout and comparison loop. Candidate C supplies the purple–blue–teal palette, dimensional encoder–decoder treatment, typography, and presentation hierarchy. The dual hash-bound decision is recorded in [`../candidate_selection.json`](../candidate_selection.json).

![Rendered preview of the native editable Deep Image Prior delivery](preview.png)

## Files

| Artifact | Role | Editable status |
|---|---|---|
| [`source/semantic_figure.json`](source/semantic_figure.json) | Canonical semantic source shared by all adapters | Yes; structured source |
| [`source/equations.tex`](source/equations.tex) | Authoritative LaTeX for all nine equation objects | Yes |
| [`delivery/svg/master.svg`](delivery/svg/master.svg) | Native vector master with groups, text, shapes, and connectors | Yes |
| [`delivery/figma/figure_figma.svg`](delivery/figma/figure_figma.svg) | Figma-ready SVG for manual import | Import-ready; Figma GUI import not yet verified |
| [`delivery/pptx/figure.pptx`](delivery/pptx/figure.pptx) | One-slide PowerPoint with independent native shapes and text | Yes |
| [`delivery/drawio/figure.drawio`](delivery/drawio/figure.drawio) | Native `mxGraphModel` with editable vertices and directed edges | Yes |
| [`delivery/pdf/publication.pdf`](delivery/pdf/publication.pdf) | Vector publication preview/export | No semantic-editability claim |
| [`validation/cross_format_report.json`](validation/cross_format_report.json) | Portable machine-readable structural validation evidence | Checks only programmable structure |
| [`validation/cross_format_preview.png`](validation/cross_format_preview.png) | Side-by-side adapter rendering comparison | Preview only |

The shared source contains 214 native shapes, 10 live text objects, 9 equation objects, and 8 directed semantic connectors. The checked-in validation report records `VERIFIED` for SVG, PPTX, draw.io, the color PDF, the grayscale PDF, and the draw.io companion PDF. The Figma-ready SVG is `IMPORT_READY_UNVERIFIED` because no Figma GUI import was performed.

## Scientific and approval boundary

The final topology is:

```text
z → Gθ → x̂ → A → ŷ
                    ↓
              comparison ← y
                    ↓
                  loss
                    └ - - optimize θ - - → Gθ
```

The predicted observation `ŷ`, rather than the operator box itself, enters the comparison. The loss feeds the parameter-optimization loop. Automated checks confirm file structure, native objects, labels, equations, and connector endpoints; they do not establish scientific correctness.

This historical reconstruction did not receive final scientific approval. Its visual direction was rejected, so it must not be presented as the active result.

## Rebuild the canonical source

From the repository root, use a new external directory so checked-in evidence is not overwritten:

```bash
python3 scripts/build_deep_image_prior_semantic.py \
  --output-dir /tmp/deep-image-prior-editable-source-01
```

The native adapters in [`../../../scripts/`](../../../scripts/) consume that source. See the [technical reference](../../../docs/technical_reference.md) for runtime requirements and adapter commands.
