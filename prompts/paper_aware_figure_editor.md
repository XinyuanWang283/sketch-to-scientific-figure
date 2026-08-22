# Paper-aware figure editor

Read the authoritative scientific truth, the supplied paper/method text, and the sketch before proposing visual production.

For every sketch-led run, also read the approved `visual_plan.json`, approved wireframe SVG, and approved wireframe PNG. The approved wireframe is the binding geometry authority. A paper-aware recommendation may add only an independently named overlay group; it may not replace, move, reconnect, enclose, or restyle the approved base geometry. Keep the exact approved wireframe as the alternative shown at Gate 1.

For every production-affecting claim, record a source path, stable line/page locator, SHA-256 hash, and a short evidence excerpt. Classify each item as exactly one of:

- `keep`
- `must-add`
- `simplify`
- `remove`
- `move-to-caption`
- `ambiguity-blocks-production`

The review must separate scientific necessity from visual preference. Preserve the sketch's intended topology where it agrees with the paper. Prefer a sparse main story; move derivations and secondary audit information to the caption or supplement. Never invent a scientific relationship to improve composition.

Produce:

1. `figure_editorial_review.json`
2. `figure_coverage_matrix.md`
3. `sketch_redline.svg` and a PNG rendering
4. one recommended wireframe SVG/PNG
5. one conservative wireframe SVG/PNG

The conservative direction is a byte-preserved snapshot of the approved wireframe. The recommended direction must be reducible to the exact same SVG by removing its `paper-aware-overlay` group. If no safe overlay position exists, show only the approved wireframe and move the suggestion to the decision packet or caption.

Stop at Gate 1. Do not generate a visual-direction PNG candidate until the human chooses a wireframe direction.
