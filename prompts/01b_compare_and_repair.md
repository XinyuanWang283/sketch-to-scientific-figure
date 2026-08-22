# Prompt 01b: PNG macro-topology review and bounded repair

Compare the candidate against `scientific_truth.json`, its blueprint, topology skeleton, rule registry, and compiled generation brief. The PNG is a visual hypothesis, not scientific authority.

## Rule classification

For every applicable rule ID, record exactly one PNG classification:

- `image-level blocking`;
- `acceptable raster imperfection`;
- `must-fix in SVG`;
- `caption-only`.

Do not create independent prose versions of a rule. Reference the registry's `rule_id`.

## Five-question human review

1. Are the required stages present and in the correct order?
2. Are required shared and independent entities visually distinguishable where the contract needs that distinction?
3. Do fan-out, fan-in, aggregation, and transition relations occur in the contracted order without adding a global relation that the truth does not define?
4. Does the candidate introduce any forbidden implication?
5. When equations are ignored, can the visual message be stated in a few seconds?

A failure in questions 1–4 is blocking only when it requires overturning the macro-layout: wrong stages/order, missing required entities, reversed or missing primary relations, a false independence implication, or major-region/dominant-hierarchy surgery. Exact repetition counts, indices, ports, endpoints, routing, derived placement, borders, formulas, and repeated micro-topology are deterministic SVG corrections.

## Decision model

Write `review_result.json` with hashes for truth, blueprint, prompt, and image; machine and human checks; blocking failures; acceptable raster imperfections; deterministic SVG fixes; repair budget; decision; and reason.

Allowed decisions:

```text
accept_for_svg
accept_for_svg_with_deterministic_structural_corrections
regenerate_from_same_blueprint
revise_blueprint
switch_candidate
local_style_edit
reject
```

Choose `accept_for_svg_with_deterministic_structural_corrections` when the PNG has useful composition/art direction and passes every image-level blocker but needs exact repeated counts, indices, ports, endpoints/routing, derived placement, borders, formulas, or repeated micro-topology rebuilt. List every correction under `svg_reconstruction_fixes`.

## Repair routing

Regenerate once for a global composition mismatch, hierarchy failure, blueprint mismatch, or wrong dominant region.

Use one local style edit only for palette, saturation, one glyph, one decorative element, local whitespace, or removal of an unwanted title/ornament.

Do not locally edit raster counts, indices, stage order, grouping, source/target, fan-out/fan-in, centroid, equation, connector wiring, or backward multiplicity. Route deterministic micro-structural errors to SVG; revise the blueprint/skeleton or reject only when the macro-layout itself must change.

## Candidate selection

For one candidate, recommend accept, bounded repair, or regenerate. For multiple candidates, review layout and palette separately. The layout winner and palette direction may differ; combine them only through the selected-candidate map and SVG style tokens.

At Gate 2 the researcher chooses:

1. one macro-layout;
2. one palette direction;
3. no more than three local issues that materially affect understanding.

After selection, create `selected_candidate_map.json`. Record major region boxes, palette samples, stroke character, corner language, whitespace rhythm, glyph crops, and art-direction notes. List generated text, equations, indices, centroids, and all connectors under scientific overrides as non-authoritative.
