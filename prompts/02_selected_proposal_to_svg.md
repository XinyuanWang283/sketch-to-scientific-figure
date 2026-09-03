# Prompt 02: one approved ImageGen candidate to editable artifacts

Use this prompt only after the researcher has explicitly approved one exact candidate file from the active A–E set. Bind that approval to the candidate slot, candidate ID, generation event, SHA-256, operator, timestamp, and provenance.

A revision request or a request such as “use C's layout with A's colors” is not an approved reconstruction input. First generate a new image, register it as a superseding slot event or in a new proposal run, show it to the researcher, and obtain approval for those exact bytes.

```text
Reconstruct the approved visual direction as newly constructed, case-specific native objects. Do not trace pixels, flatten the figure, wrap the selected PNG as a whole-canvas image, or treat generated pixels as scientific evidence.

Before drawing, read:
1. the current repository Skill and applicable repository rules;
2. the original sketch and focused clarification conversation;
3. the exact hash-bound candidate selection and generation-event history;
4. authoritative typed labels, equations, method text, and researcher corrections;
5. the latest source, manifest, and validation records when revising a delivery.

## Authority

Use the sources for different purposes:

- The sketch, clarification, and explicit corrections determine scientific meaning, exact notation, topology, grouping, arrow direction, comparisons, repetition, and forbidden implications.
- The one approved candidate determines visual direction: composition, hierarchy, proportions, palette, glyph character, whitespace, and rhythm.
- Reconstruction metadata assigns stable IDs, ports, groups, geometry, and cross-format mappings without changing the approved science.

If these sources conflict, scientific meaning and explicit researcher corrections win. If a material contradiction remains unresolved, stop and ask one focused question.

## Region map and approval

Create `source/selected_candidate_map.json` before building delivery artifacts. Bind it to the exact selected-candidate SHA-256 and record, for every major region:

- a stable region ID and source-pixel bounding box;
- semantic role and required content;
- visual properties taken from the approved candidate;
- conversion mode: native vector, vector equation, editable curve, reference-only crop, or approved raster atom;
- scientific overrides for generated text, equations, arrows, and connectors;
- the native output IDs expected in each supported format.

Every visible major region must map to one or more output IDs. Reference crops are QA inputs only and must be marked `reference_only_not_embedded`.

Show the map's topology and every proposed raster exception to the researcher. Record a separate approval containing the case ID, map SHA-256, selected-candidate SHA-256, operator, timestamp, and approval provenance. Do not continue without that exact approval.

## Native reconstruction

Construct structure with native objects:

- use SVG primitives and semantic groups for reproducible geometry;
- keep ordinary labels as live text when format support permits;
- retain authoritative LaTeX in `source/equations.tex` and bind each equation object through `source/equation_manifest.json`;
- render complex equations as intrinsic-aspect vector objects when native semantic equation support is unavailable;
- never stretch an equation anisotropically;
- keep borders, labels, arrows, connectors, curves, equations, and image slots independently selectable;
- attach stable source, target, and relation metadata to directed connectors;
- use arrowheads only for confirmed directed relationships;
- preserve meaning without relying on color alone.

A LaTeX-derived vector-path equation is scalable and visually editable as an object, but it is not semantically editable LaTeX. State that boundary explicitly.

Native SVG or PPTX gradients are allowed when they are part of the approved visual direction, remain editable, and do not carry an otherwise invisible scientific distinction. Avoid unsupported filters, masks, shadows, glow, scripts, animation, event handlers, `foreignObject`, and remote resources.

## Raster exceptions

Default to native vector reconstruction. A raster crop is allowed only when all of these conditions hold:

1. the researcher explicitly approved reuse of that exact region;
2. the decision is bound to the selected-candidate hash and exact source-pixel box;
3. the crop contains no baked-in label, equation, border, arrow, connector, legend, or scale-bearing mark;
4. it is the smallest credible content atom and remains independently replaceable;
5. its path, MIME type, dimensions, byte length, SHA-256, semantic role, scientific status, and provenance are recorded in `source/asset_manifest.json`;
6. the allowed identities and count come from that approved manifest, not from a universal numeric rule.

Store SVG sidecars below `delivery/svg/assets/` and use repository-relative paths. Reject absolute paths, `..` traversal, symlink escapes, missing files, hash mismatches, and unmanifested `<image>` elements. Do not use the complete selected candidate as an asset. Do not describe a raster atom as pixel-editable or as measured evidence.

## Output structure

Use the case's existing layout when revising it. For a new case, use this compact structure unless repository rules specify an equivalent:

source/
  selected_candidate_map.json
  semantic_figure.json
  equations.tex
  equation_manifest.json
  asset_manifest.json              # only when non-native assets exist
delivery/
  delivery_manifest.json
  svg/master.svg
  svg/assets/                      # only approved relative sidecars
  pptx/figure.pptx
  drawio/figure.drawio
  pdf/publication.pdf
validation/
  structural_validation_report.json

Format claims:

- SVG: native/vector master with live text where supported and only manifest-approved raster atoms.
- PPTX: independent shapes, text, curves, equation objects, connectors, and approved replaceable picture shapes; never one slide screenshot.
- draw.io: editable graph cells, labels, and directed edges. Treat visual fidelity as experimental until an official render is inspected.
- PDF: export or preview only.

Do not claim Figma compatibility unless a real import smoke test confirms that one group, one label, and one connector or image slot can be edited independently.

## Validation and registration

Before registering a delivery, produce a machine-readable structural report bound to the case ID, delivery revision, selected-candidate hash, approved region-map hash, output manifest, output hashes, check results, overall result, and validator version or code revision.

At minimum check:

- selection, map, approval, and manifest bindings;
- path containment and symlink safety;
- SVG XML, PPTX package, draw.io XML, and PDF parseability;
- native object structure and absence of a whole-canvas candidate image;
- required labels, nodes, groups, directed edges, and edge directions;
- region-to-output-ID coverage;
- raster identity, count, dimensions, paths, and hashes against the approved asset manifest;
- equation source binding and intrinsic aspect ratio;
- cross-format structural consistency where implemented.

Validation must fail closed. Do not register a delivery when the report is missing, belongs to another case or revision, has mismatched hashes, or reports failure. Do not weaken validation to make a delivery pass.

Automated checks may establish file validity and programmable structural consistency. They do not establish visual quality, scientific correctness, Science Day suitability, or permission to publish.

## Final researcher decisions

After validation, render the supported artifacts at their intended size and show the researcher:

- the approved candidate beside the reconstruction;
- region-level comparisons where useful;
- the editable-object boundary for each format;
- every retained raster atom;
- the structural validation report and its limitations.

Record visual, scientific-content, Science Day-use, and public-release decisions separately, with exact artifact or Git-tree bindings appropriate to each decision. Never infer one decision from another and never create any of them from automated validation.
```

## Verified example

The frozen example at `examples/deep_image_prior/editable_delivery_c_fidelity_v2/` demonstrates this prompt with one exact Candidate C selection, an eight-region approved map, native gradients, nine intrinsic-aspect LaTeX-derived vector equations, and two approved replaceable synthetic raster atoms. It is evidence for that case only, not a universal reconstruction benchmark.
