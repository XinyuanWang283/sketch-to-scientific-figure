# Candidate C-only editable review draft

**Review status:** `REJECTED_FOR_INSUFFICIENT_VISUAL_FIDELITY`. The researcher found that this native-only reconstruction no longer looked close enough to candidate C. It is preserved unchanged as revision history; the active result is the [high-fidelity hybrid revision](../editable_delivery_c_hybrid/README.md).

The researcher had previously rejected the D-layout/C-style reconstruction and asked to try candidate C alone. The hash-bound candidate decision remains recorded in [`../candidate_selection_c_only.json`](../candidate_selection_c_only.json). The earlier D/C delivery remains available in [`../editable_delivery/`](../editable_delivery/README.md); neither historical artifact package was overwritten.

![Rendered preview of the candidate C-only editable review draft](preview.png)

## Files

| Artifact | Role | Editable status |
|---|---|---|
| [`source/semantic_figure.json`](source/semantic_figure.json) | Canonical semantic source shared by every adapter | Yes; structured source |
| [`source/equations.tex`](source/equations.tex) | Authoritative LaTeX for all nine equation objects | Yes |
| [`delivery/svg/master.svg`](delivery/svg/master.svg) | Native vector master with semantic IDs, shapes, equations, and connectors | Yes |
| [`delivery/figma/figure_figma.svg`](delivery/figma/figure_figma.svg) | Figma-ready SVG for manual import | Import-ready; Figma GUI import not verified |
| [`delivery/pptx/figure.pptx`](delivery/pptx/figure.pptx) | One-slide PowerPoint with independent native objects | Yes |
| [`delivery/drawio/figure.drawio`](delivery/drawio/figure.drawio) | Native `mxGraphModel` with editable cells and directed edges | Yes |
| [`delivery/pdf/publication.pdf`](delivery/pdf/publication.pdf) | Vector publication preview/export | No semantic-editability claim |
| [`validation/cross_format_report.json`](validation/cross_format_report.json) | Portable machine-readable structural checks | Programmable structure only |
| [`validation/cross_format_preview.png`](validation/cross_format_preview.png) | SVG, Figma-ready SVG, draw.io, and PPTX render comparison | Preview only |

The shared source contains 1,340 native shapes, one live text object, nine equation objects, and seven directed semantic connectors. The checked-in report records `VERIFIED` for SVG, PPTX, draw.io, the color PDF, the grayscale PDF, and the draw.io companion PDF. The Figma-ready SVG remains `IMPORT_READY_UNVERIFIED` because no Figma GUI import was performed.

## Visual direction and topology

Candidate C supplies both the composition and the visual language:

- one left-to-right scientific reading path;
- a purple encoder–decoder generator;
- a single observation panel containing predicted data, loss, and measured data;
- a low feedback loop returning the optimization signal to the generator;
- no title, subtitle, or explanatory captions competing with the diagram.

The preserved scientific topology is:

```text
z → Gθ → x̂ → A → ŷ
                    ↓
                  loss ← y
                    └ - - optimize θ - - → Gθ
```

Automated checks confirm file parsing, native objects, equations, directed endpoints, and cross-format structure. They do not establish scientific correctness or visual acceptance.

This package did not receive final scientific approval and is no longer the active review draft.

## Rebuild the canonical source

From the repository root, use a new external output directory:

```bash
python3 scripts/build_deep_image_prior_c_semantic.py \
  --output-dir /tmp/deep-image-prior-c-editable-01
```

The native adapters under [`../../../scripts/`](../../../scripts/) consume the generated canonical source. See the [technical reference](../../../docs/technical_reference.md) for adapter runtime requirements.
