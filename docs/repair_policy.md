# Raster repair policy

## Acceptance rule

A PNG may advance to semantic SVG when it provides useful art direction and passes every `image-level blocking` rule. Blocking is reserved for macro-layout failures: wrong stages or order, missing required entities, reversed or missing primary relations, false evidence-like imagery, or major-region and dominant-hierarchy surgery. It does not need production-correct text, equations, indices, derived placement, ports, borders, connector endpoints, routing, or repeated micro-topology.

The depiction mode is declared per figure. `literal_instances` shows every contracted instance. `representative_template` and `multiplicity_badge` may compress repetition only when the truth and caption preserve the full semantic scope. Compression must never merge independent entities, duplicate a shared entity, or imply that omitted repetitions do not exist.

Each rule must receive exactly one classification in `review_result.json`:

- `image-level blocking`: macro science must already be visually correct;
- `acceptable raster imperfection`: unreliable in PNG but harmless because it will not be copied;
- `must-fix in SVG`: rebuilt deterministically from truth/blueprint;
- `caption-only`: evidence or explanation intentionally outside the canvas.

## Allowed repair budget

- At most one regeneration per blueprint for global hierarchy or composition failure.
- At most one local style edit per candidate for palette, saturation, one glyph, one decoration, local whitespace, or unwanted ornament.
- A second occurrence of the same topology failure requires blueprint/skeleton revision or candidate rejection.

## Forbidden raster repairs

Never use local generative editing to repair count, index, stage order, grouping, source/target, fan-out/fan-in, derived placement, equation, connector rewiring, or relation multiplicity. Reconstruct deterministic micro-structure in semantic SVG according to its rule classification. Revise the blueprint/skeleton only when the macro-layout must be overturned.

Do not recolor an already accepted PNG to create another candidate. Palette transfer is deterministic through SVG tokens.

## Selected-candidate transfer

The selected-candidate map may transfer major region boxes, palette samples, stroke character, corner language, whitespace rhythm, glyph appearance, and bounded art-direction notes. It must explicitly mark generated text, formulas, indices, counts, centroids, connectors, and endpoints as non-authoritative.

Human selection is required before filling the selected-candidate map. Do not silently choose a winner from validator output or aesthetic scoring.
