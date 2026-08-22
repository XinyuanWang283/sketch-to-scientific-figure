# Semantic SVG reconstruction template

```text
Reconstruct a new semantic SVG; do not trace, auto-vectorize, wrap, or OCR the selected PNG.

AUTHORITIES
- scientific_truth.json: exact entities, instances, counts, notation, equations, relations, invariants, and forbidden implications;
- candidate_blueprint.json: semantic regions, ports, edges, topology, and geometry;
- selected_candidate_map.json: composition and art direction only;
- svg_reconstruction_spec.json + validation_rules.json: executable output contract.

REQUIRED OUTPUT
- parseable SVG XML with one unique stable ID per semantic object;
- semantic groups and live text;
- exact equation metadata from truth;
- explicit ports and independent connector paths;
- every connector annotated with data-source, data-target, data-relation-id, and data-rule-id;
- global reusable style tokens and congruent repeated geometry;
- no whole-canvas raster, tracing output, filters, shadows, or inferred text.

Recompute all means/centroids from the final displayed member-anchor coordinates. Rebuild exact labels, indices, formulas, connector endpoints, directions, and routing from truth/blueprint regardless of what appears in the PNG.

Run artifact and semantic-SVG validators. A validator pass does not replace final-size visual inspection or researcher sign-off.
```
