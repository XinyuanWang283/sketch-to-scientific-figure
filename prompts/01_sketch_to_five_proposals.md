# Prompt 01: compiled truth to 1, 3, or 5 PNG visual candidates

The filename is retained for compatibility. The approved proposal mode determines the count. `directed-three` is the normal comparison default; `exploratory-five` is exceptional.

## Step A: write machine-readable blueprints

Start from approved `scientific_truth.json`, not from a monolithic image prompt. Write one `candidate_blueprint.json` per candidate using the repository schema.

Each blueprint must include:

- stable semantic nodes, ports, edges, and truth instance references;
- required regions and normalized boxes;
- rule IDs for every in-scope invariant;
- allowed flexibility and deliberate omissions;
- a complexity budget;
- a layout fingerprint with `reading_axis`, `region_graph`, `dominant_region`, `stage_arrangement`, `repetition_strategy`, `audit_location`, `symmetry`, `connector_topology`, and `occupied_area_distribution`.

Candidate policy:

- `focused-one`: one best-fit blueprint; no diversity test.
- `directed-three`: normally sketch-faithful, mechanism-dominant, and compact editorial.
- `exploratory-five`: only when hierarchy or message remains genuinely unresolved and the researcher explicitly accepts the budget.

Role names do not establish diversity. Reject a pair when the four core fingerprint fields—region graph, reading axis, stage arrangement, and repetition strategy—are identical and fewer than three categorical fields differ. Occupied area cannot establish diversity by itself.

## Step B: render deterministic topology skeletons

Render `<candidate>_skeleton.svg` and `<candidate>_skeleton.png` from the same scene. The skeleton must encode:

- major regions and reading order;
- entity cardinality and grouping;
- stage order;
- rough placement;
- fan-out, fan-in, and meaningful transitions.

It must omit final palette, decoration, final glyph styling, production typography, production equations, and connector aesthetics.

Run artifact and skeleton validation before image generation. Fix the truth or blueprint when a count, ID, derived placement, port, edge, stage order, transition, or fingerprint fails. Do not append prose to compensate.

## Step C: compile the short image brief

Compile one approximately 350–500 English word brief from truth plus one blueprint. It contains only:

- purpose and audience;
- one visual message;
- reference-image roles;
- five to eight image-level blocking rule IDs and descriptions;
- candidate art direction;
- a small visible-text whitelist;
- forbidden visual implications;
- an explicit statement that production typography is not required.

Never interpolate the complete contract or all equations into the image prompt.

## Step D: generate independent candidates

Make exactly one built-in image-generation call per blueprint. Do not call the Image API, use an API key, generate a contact sheet, or seed a new candidate with a prior candidate.

Reference roles:

```text
Image 1: topology skeleton; authoritative for structure
Image 2: optional style reference; authoritative for style only
```

Do not attach two competing structural references. For a sketch-faithful candidate, compile the sketch into the topology skeleton or use the sketch instead of a separate skeleton.

Use the compiled brief. The candidate should reinterpret visual treatment while preserving the skeleton's macro-topology. Do not add titles, legends, footers, stages, modules, measurements, arrows, or explanatory text.

## Step E: pre-display macro-topology review

PNG image-level blockers are:

1. stage order and major stage count;
2. state count and view-per-image count;
3. shared versus independent entities where the contract distinguishes them;
4. fan-out and fan-in topology;
5. aggregation and transition relations follow the order declared by the truth;
6. shared generator identity and required stage transitions;
7. any forbidden scientific implication;
8. failure to follow the candidate's declared dominant region or region graph.

The following do not block a useful PNG when macro-topology is unambiguous:

- imperfect production indices or short symbolic labels;
- exact equations;
- exact centroid coordinates;
- exact ports, endpoints, and connector routing;
- final typography, kerning, line breaks, and semantic group IDs.

Record those items as `acceptable raster imperfection` or `must-fix in SVG`; do not start an open-ended raster repair loop.

## Repair budget

- One regeneration per blueprint for global composition, hierarchy, or blueprint mismatch.
- One local style edit per candidate for palette, saturation, one glyph appearance, one ornament, local whitespace, or unwanted decoration.
- Never use local raster edit for count, index, stage order, grouping, source/target, fan-in/fan-out, centroid, equation, connector rewiring, or backward multiplicity.
- If the same hard topology error appears twice, revise the blueprint/skeleton or reject the candidate.

Gate 2 receives only candidates that pass every image-level blocker. A candidate may still contain production details explicitly scheduled for deterministic SVG reconstruction.
