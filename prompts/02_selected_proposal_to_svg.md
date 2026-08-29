# Prompt 02: approved ImageGen candidate to native editable artifacts

Use this only after the researcher explicitly approves one of the five ImageGen candidates, an approved revision, or an exact combination such as `C layout with A color direction`. Clarification alone and an unapproved selection are not sufficient.

````text
Reconstruct the approved visual direction as newly constructed native editable objects. Create a canonical semantic SVG and equivalent native PPTX objects. A draw.io file may be an experimental structural view, but it is not visual-fidelity evidence unless its official render is checked. Create PDF only as an export or preview. Do not mechanically trace pixels, flatten the figure, wrap the selected PNG as a whole-canvas image, or use generated pixels as a scientific source. Treat Figma import as a downstream compatibility target that must be smoke-tested rather than assumed.

Before drawing, reread in this order:
1. the current repository Skill, this prompt, and any applicable repository rules;
2. the original hand-drawn sketch;
3. the focused clarification conversation and the short rendering brief;
4. the exact hash-bound selection record, revision history, and approved candidate or layout/palette combination;
5. any authoritative typed labels, equations, method text, and explicit corrections supplied by the researcher;
6. the required hash-bound `selected_candidate_map.json` created at this stage, including reference-only region crops and native output-ID mappings;
7. the latest delivery source and validation report, when revising an existing reconstruction;
8. every approved asset source and current asset manifest, if any.

Create `source/selected_candidate_map.json` before drawing. Record every major region box, palette sample, stroke character, corner language, whitespace rhythm, conversion mode, glyph reference crop, art-direction note, scientific override, and the native output IDs assigned to each region. Bind the map to the exact selected-candidate SHA-256. Reference crops are visual QA inputs only and must be marked `reference_only_not_embedded`; neither the whole selected candidate nor an unapproved reference crop may appear in delivery media. The only selected-candidate-crop exception is an explicit researcher request for region reuse under the review-draft decision and asset-manifest rules below.

The selected-candidate map and any further semantic reconstruction metadata are implementation artifacts, not pre-generation user forms. They must mirror the sketch and clarification rather than inventing content. Before reconstruction continues, show the researcher the map's topology and any proposed raster exceptions, then record explicit hash-bound approval.

Checked-in demonstration: `examples/deep_image_prior/editable_delivery_c_fidelity_v2/` applies this prompt with eight mapped regions, exactly two approved replaceable raster atoms, intrinsic-aspect LaTeX vector equations, and a PDF used only as preview/export. Its draw.io file is an experimental structural view with a known official-render defect. The v0.1 case records visual approval separately and binds it to the exact artifact-manifest hash; scientific, Science Day, and public-release approvals remain pending.

Authority and scope:
- Explicit typed corrections and exact equations or labels supplied during clarification have highest authority.
- The hand sketch plus clarification determines entities, notation, topology, grouping, arrow direction, feedback, comparisons, repetition, and forbidden implications.
- The approved ImageGen candidate determines visual direction: composition, hierarchy, proportions, palette, glyph character, whitespace, and rhythm. It does not determine scientific facts.
- When layout and palette come from different approved candidates, use only the named layout source for geometry and only the named palette source for semantic color roles.
- The selected-candidate map and internal reconstruction metadata may assign stable IDs, ports, source/target metadata, groups, and geometry, but may not override the sketch or clarification. Every mapped major region must resolve to at least one native output ID.
- Correct invented pathways, incorrect text, decorative additions, color drift, or scientific ambiguity instead of reproducing them.
- If a contradiction cannot be resolved from the sketch and clarification, stop and ask one focused question rather than guessing.

Priority:
1. fidelity to researcher-confirmed scientific content;
2. the clarified one-sentence purpose;
3. topology, grouping, arrow semantics, and authoritative notation;
4. recognizable sketch glyphs, mathematical placement, transition attachment, and salience;
5. communication at the intended medium and size;
6. economy of marks and editability.

Preserve the hierarchy, information density, visible-text budget, and art direction expressed by the approved candidate, subject to the scientific authority above. Do not add explanatory prose, extra stages, or repeated labels merely because the vector canvas has room.

Semantic construction:
- use native SVG vector primitives for all reproducible structure and for every visual anchor that remains recognizable when built as vector geometry;
- assign clear semantic group ids to major scientific objects, conceptual regions, branches, stages, and equations;
- keep ordinary labels as editable SVG text using Arial, Helvetica, or Source Sans;
- render mathematics with one consistent LaTeX-to-SVG vector workflow;
- preserve each source expression in a data-latex attribute;
- align equivalent semantic objects and use consistent line weights;
- keep functional arrows, structural lines, braces, and leader lines as separate editable objects.
- attach `data-source`, `data-target`, `data-relation-type`, and applicable `data-rule-ids` metadata to every scientific connector;
- keep exact short symbols or labels adjacent to visual objects as separate editable text or math paths; place a full equation in separate whitespace only when it is central to the clarified story;
- factor out repeated modules, operators, and definitions when scientifically safe.
- reconstruct each recognizable sketch glyph as native vector geometry with the confirmed silhouette, orientation, meaningful ports, and repeated-instance identity. Smooth hand-drawn wobble without substituting another module type.
- place member anchors before any contracted mean, centroid, or temporal-center representative. Compute the representative from the final member-anchor coordinates, then store its member ids and placement rule on the semantic group, for example `data-members="z0 z1 z2 z3"` and `data-placement-rule="mean-of-member-centers"`. Do not derive the position from panel or card bounds.
- keep confirmed clusters internally intact unless the approved alternative layout deliberately reorganizes them without changing their membership or relationships.
- construct every explicitly approved replaceable asset as the smallest possible atomic content object inside a semantic group with separate content, border, label, and connectors;
- do not promise pixel-level editability for a raster atom. The atom must be independently selectable and replaceable; its internal pixels are not vector-editable.

Required replaceable-slot structure:

```svg
<g id="state-<entity-id>" data-role="state-image" data-asset-id="<asset-id>">
  <image id="asset-<asset-id>" href="assets/<asset-id>.png"
         x="..." y="..." width="..." height="..."
         preserveAspectRatio="xMidYMid meet"/>
  <rect id="border-<asset-id>" .../>
  <text id="label-<asset-id>" ...>...</text>
</g>
```

The selected ImageGen candidate itself is never a whole-canvas asset slot. Use this structure only when the researcher explicitly approves one raster atom or a small explicitly enumerated set of non-evidentiary atoms that cannot be represented credibly with native geometry. Every atom needs its own id, exact bbox/hash, review-draft decision entry, and manifest entry. The image appears first, then its native SVG border and label above it. Connectors remain outside or as separately identified siblings. Pre-crop the image to its final semantic region; do not use a mask to hide unrelated content. Use stable ASCII ids even when visible notation contains Unicode or LaTeX. If any raster atom remains, describe its pixel content honestly as replaceable rather than fully vector-editable.

Arrow rules:
- use arrows only for directed transformations, production, measurement, information flow, evolution, initialization, causality, or sequence confirmed by the sketch and clarification;
- use proximity, alignment, braces, enclosure, shared form, or plain lines for membership, part-whole relations, correspondence, grouping, and annotation;
- construct arrowheads as explicit filled polygons;
- stop arrow shafts at the base of arrowhead polygons;
- use stroke-linecap="butt";
- do not use marker-start or marker-end.
- for every confirmed transition, use a direct native SVG path between the confirmed source and target ports. Do not route the relation through a heading, card, page-edge rail, or decorative progression line. Preserve its approved direction and salience without relying on color.

Equation geometry rule:
- render authoritative LaTeX as vector paths or vector equation objects;
- derive every target box from the rendered SVG `viewBox` and preserve its intrinsic width-to-height ratio in SVG, PPTX, and PDF export;
- never use anisotropic stretch to match a candidate's formula bbox.

Title and prose:
- default to no title group;
- include a title only when the clarification or approved candidate explicitly requires one;
- use only visible prose confirmed by the sketch, clarification, or approved candidate;
- keep caption-only explanation off the canvas;
- do not add a subtitle, explanatory footer, prose box, legend, or panel identifier unless it is explicitly required.

Color tokens and effects:
- preserve structure, grouping, alignment, whitespace, and scale as the primary hierarchy;
- extract a small semantic token set from the approved palette direction instead of sampling colors pixel-by-pixel;
- when layout and palette come from different approved candidates, preserve only the named layout's geometry and apply only the named palette's semantic roles. Do not trace either raster;
- keep neutral structure dominant, with at most one muted primary accent family and one optional secondary accent family;
- apply the primary accent selectively to the focal relationship implied by the approved visual direction; color must not be the sole carrier of a scientific distinction;
- use the secondary accent only for a second necessary semantic role that structure cannot communicate clearly alone;
- keep most mathematical text in the approved ink or secondary-text color and do not color every variable, arrow, module, box, or outline;
- keep the result understandable in grayscale;
- avoid gradients, filters, shadows, glow, decorative effects, and unnecessary 3D unless they are an explicit, meaningful part of the approved candidate;
- never use generative image editing to recolor the selected raster. Transfer only semantic color roles into native SVG fills, strokes, and text classes.

Store the approved semantic colors as reusable SVG style classes or design tokens. Populate every placeholder below with one exact reviewed hexadecimal value before saving; do not leave template variables in the SVG:

```css
.fill-background { fill: {{PALETTE_TOKENS.background}}; }
.text-ink { fill: {{PALETTE_TOKENS.ink}}; }
.stroke-ink { fill: none; stroke: {{PALETTE_TOKENS.ink}}; }
.text-secondary { fill: {{PALETTE_TOKENS.secondary_text}}; }
.stroke-structure { fill: none; stroke: {{PALETTE_TOKENS.structural_line}}; }
.fill-soft-region { fill: {{PALETTE_TOKENS.soft_region_fill}}; }
.text-primary { fill: {{PALETTE_TOKENS.primary_semantic}}; }
.stroke-primary { fill: none; stroke: {{PALETTE_TOKENS.primary_semantic}}; }
.fill-primary { fill: {{PALETTE_TOKENS.primary_semantic_fill}}; stroke: {{PALETTE_TOKENS.primary_semantic}}; }
```

Omit classes that are not needed. Apply classes by semantic role, not variable name. Keep fills and strokes directly editable, and make global accent-family replacement possible by changing the primary accent definitions in one style block.

Hybrid asset and provenance rules:
- default to native vector; a raster is a narrow exception for one approved semantic slot, not a general rendering technique;
- when the researcher explicitly requests region reuse from the selected ImageGen candidate, write `source/raster_atom_review_decision.json` before assembly. Bind it to the exact candidate SHA-256 and exact source-pixel bbox; label the decision `review-draft-only`, keep final publication/scientific approval null, and reject any crop containing a baked-in label, border, connector, arrow, legend, scale-bearing mark, or equation;
- a region reuse atom is distinct from a `reference_only_not_embedded` QA crop even if both share a bbox. Save it under a stable asset id, record its exact pixel checksum, and make it independently selectable and replaceable in SVG and PPTX; a draw.io representation must declare its actual support level;
- licensed SVG assets must be sanitized and inlined as native vector groups. Do not embed them as `data:image/svg+xml`;
- an approved raster atom must use a portable repository-local relative reference such as `assets/<asset-id>.png`; the sidecar must remain under the case root, must not traverse a symlink or `..`, and must match its recorded hash. A deliberately self-contained derivative may use an embedded data URI only when its manifest declares that representation explicitly;
- every `<image>` requires one explicitly approved slot and exactly one entry in the case asset manifest; an unmanifested `<image>` is a hard failure;
- generated raster placeholders have `scientific_status: non-evidentiary-schematic` and default `release_policy: replace-before-publication`. Only explicit researcher approval may change the release policy to `approved-schematic`;
- generated assets may fill only explicitly approved schematic context or state slots. A generated atom may denote the object class or role of a reconstructed state, including an approved \(\hat x_t\) output slot, but its pixels must never be presented as an actual reported reconstruction, measurement, ground truth, diagnostic example, quantitative comparison, scale-bearing evidence, or performance result;
- real medical or sensitive imagery requires user-confirmed de-identification and provenance. Do not store patient identifiers or absolute local source paths in the manifest;
- do not invent a license for generated content or a user-owned asset. Record unknown or inapplicable fields honestly;
- every raster atom has explicit x, y, width, height, aspect-fit behavior, pixel dimensions, byte length, and checksums in the manifest;
- target at least 300 effective ppi at intended paper size, unless the publication specification requires more;
- default size budget: at most 1 MB per raster atom and 5 MB for the complete SVG unless the researcher explicitly approves an exception.

Materialize any explicitly approved non-native assets before SVG assembly:
1. Resolve every approved asset to actual content before writing its SVG slot. Do not create a manifest entry for an asset that does not exist.
2. For each `generated-placeholder`, generate either one standalone asset or a coherent asset-only family. Generate only the image content: no variable label, time index, dashed or solid border, arrow, operator, legend, colorbar, scale bar, stage heading, or explanatory text may be baked into the pixels.
3. Do not crop an asset from a rendered layout proposal unless the researcher explicitly requested selected-candidate region reuse and the exact crop satisfies the separate review-draft decision rules above. If a coherent family is generated together, isolate each approved member deliberately and save it under its exact stable id as `output/assets/<asset-id>.png` or `.jpg`.
4. Preserve the approved family vocabulary and only the clarified state variation. For medical-imaging placeholders, prefer a fictional phantom-like schematic over realistic patient imagery.
5. Visually inspect every materialized asset against its recognition target, forbidden implications, privacy boundary, dimensions, and family consistency before embedding it. Regenerate an unsafe or misleading atom. Keep `human_reviewed: false` until the researcher has reviewed that exact asset; never infer review from approval of the overall candidate.
6. Record the actual generator and version, generation date, prompt SHA-256, seed when available, exact content checksum, and sidecar geometry. Do not invent missing provenance.
7. If approved asset generation is unavailable or fails, prefer a faithful native-vector fallback. Otherwise stop and report the missing asset instead of embedding fabricated content or a phantom manifest record.

Figma compatibility and file integrity:
- no external images, fonts, styles, scripts, event handlers, `foreignObject`, animation, HTTP(S) references, `file:` references, absolute local paths, path traversal, or symlink escapes; approved repository-local relative raster sidecars are allowed only when hash-bound in the case manifest;
- no SVG markers, `data:image/svg+xml`, fragile filters, masks, shadows, glow, or decorative effects;
- use simple supported primitives; use a `clipPath` only when pre-cropping cannot satisfy the asset slot and a Figma smoke test passes;
- ordinary text remains editable and uses available fonts; do not convert ordinary labels to outlines;
- major components and approved raster slots remain independently selectable and replaceable;
- treat the source SVG as canonical and, whenever non-native assets exist, treat its manifest as part of that canonical source. Do not rely on Figma round-trip export to preserve ids, `data-*` attributes, metadata, or CSS classes;
- the SVG remains understandable when printed in grayscale.

Create `output/assets/asset_manifest.json` with this minimum structure when any non-native asset exists:

```json
{
  "schema_version": "1.0",
  "figure_svg": "output/figure_figma.svg",
  "canonical": "svg-plus-manifest",
  "figma_compatibility": "unverified",
  "assets": [
    {
      "asset_id": "<stable-id>",
      "asset_family_id": null,
      "entity_ref": "<exact scientific entity>",
      "semantic_role": "<role>",
      "asset_mode": "<licensed-svg | user-provided | generated-placeholder>",
      "content_kind": "<inline-vector | raster>",
      "scientific_status": "<status>",
      "release_policy": "<replace-before-publication | approved-schematic | approved-source-asset>",
      "svg_ids": {
        "group": "<group-id>",
        "content": "<content-id>",
        "border": null,
        "label": null
      },
      "embedding": {
        "mime": "<image/png | image/jpeg | inline-vector>",
        "encoding": "<base64 | native-svg>",
        "sha256": "<content-hash>",
        "byte_length": 0,
        "pixel_width": 0,
        "pixel_height": 0
      },
      "placement": {
        "x": 0,
        "y": 0,
        "width": 0,
        "height": 0,
        "svg_units": "user-unit",
        "preserve_aspect_ratio": "xMidYMid meet"
      },
      "intended_output": {
        "placed_width_in": 0,
        "placed_height_in": 0,
        "effective_ppi": 0
      },
      "sidecar": null,
      "replacement": {
        "fit": "contain",
        "preserve_geometry": true
      },
      "provenance": {
        "kind": "<licensed-source | user-provided | generated>",
        "source_url_or_user_basename": "<URL or basename, never an absolute private path>",
        "source_revision": "<commit or version when applicable>",
        "author": "<author when applicable>",
        "generator_and_version": "<when generated>",
        "generated_at": "<ISO date when generated>",
        "prompt_sha256": "<when generated>",
        "seed": null,
        "human_reviewed": false
      },
      "license": {
        "spdx_or_name": null,
        "license_url": null,
        "attribution": null,
        "modified": null
      },
      "privacy_status": "<not-applicable | de-identified-user-confirmed | unverified>",
      "forbidden_implications": []
    }
  ]
}
```

Replace nullable example values with real values only when applicable. Keep `human_reviewed` Boolean and change it to `true` only after the researcher reviews that exact materialized asset. For a raster asset, replace `sidecar: null` with an object containing `path` and `sha256`. For an inline licensed vector, `pixel_width`, `pixel_height`, and `effective_ppi` may be 0 and no raster sidecar is required, but source revision, author, license, attribution, and modification status remain required. If no non-native asset is used, omit the manifest rather than creating an empty one.

Cross-format native reconstruction:
- build PPTX with independent editable shapes, text boxes, connectors, and grouped modules; never place the selected candidate or rendered SVG as a full-slide screenshot;
- build draw.io with an `mxGraphModel`, separate editable vertex cells, edge cells, labels, and source/target relationships; never store the figure as one embedded image;
- preserve stable semantic ids or an explicit id mapping across SVG, PPTX, and draw.io whenever the format permits it;
- derive each format from the same internal reconstruction metadata so required nodes, labels, and directed edges remain consistent;
- create PDF from the reconstructed vector source and describe it only as an export or preview, not an editable source format.

Automated validation may check XML/package parseability, native object counts, expected labels, required nodes and edges, edge direction, grouping, orphan nodes, disconnected components, and cross-format structural consistency. It must never claim scientific correctness, create final researcher approval, or replace the final visual check.

Before completion, render the SVG at its intended size and verify:
1. the clarified one-sentence purpose and reading direction are immediately visible;
2. every entity and relationship matches the sketch plus clarification;
3. every arrow has one supported verb-like meaning and correct direction;
4. structural associations do not use arrowheads;
5. invariant and varying components are distinguishable;
6. equations and notation match the authoritative source;
7. full equations do not dominate object interiors or repeat unnecessarily;
8. transition arrows and annotations attach to clear anchors and do not float between regions;
9. comparable regions have justified width and density, with intentional whitespace;
10. every visible ordinary-language phrase matches text confirmed by the sketch or clarification, with no invented headings or explanations;
11. the approved candidate's hierarchy and semantic palette roles are preserved without making color the sole carrier of meaning;
12. the selected layout source and palette source are recorded, and no raster tracing or pixel-by-pixel recoloring occurred; any selected-candidate region atom has an explicit review-draft decision and exact candidate-hash/bbox provenance;
13. semantic color classes are reusable, globally replaceable, and directly editable;
14. the design remains understandable in grayscale;
15. no unnecessary object can be removed without loss of meaning;
16. hiding full equations still leaves the main visual message, required objects or stages, and principal directed relations recoverable;
17. every visual anchor remains faithful to the sketch and clarification and introduces no forbidden visual implication;
18. equivalent objects are aligned and line weights are consistent;
19. all labels, equations, arrows, borders, legends, and scale-bearing marks are native editable objects rather than baked into a raster;
20. each `<image>` has one explicitly approved slot, one manifest entry, one matching sidecar checksum, a valid scientific status, and separate content plus every required border or label object;
21. raster dimensions, decoded byte length, checksum, effective resolution, aspect fit, and file-size budget match the manifest;
22. the SVG contains no unapproved raster or base64 content, unapproved external reference, `data:image/svg+xml`, marker, gradient, filter, mask, script, event handler, animation, `foreignObject`, shadow, glow, or decorative effect;
23. licensed assets have complete source, revision, author, license, attribution, and modification records; sensitive user assets have user-confirmed de-identification and provenance;
24. generated placeholders remain non-evidentiary, contain no unsupported diagnostic or quantitative content, and have the required caption disclosure and release policy;
25. major scientific components and every approved asset slot remain independently selectable and replaceable;
26. every confirmed sketch glyph preserves its recognizable silhouette, orientation, ports, and repeated-instance identity;
27. every group mark covers its exact members, and every mean/centroid/temporal-center representative equals the computed mean of the final member-anchor coordinates;
28. every confirmed transition connector directly attaches the confirmed source and target in the correct direction and remains prominent in grayscale with text hidden;
29. every approved departure from the sketch is explained by the selected alternative layout or explicit clarification;
30. the final artifact contains no whole-canvas raster copy of the selected ImageGen candidate.

Also verify the presentation structure explicitly: equations, labels, repeated notation, major objects, connector density, occupied area, and legibility fit the intended medium and reproduce the approved art direction without introducing a generic card-based or formula-first style.

Validate the source artifact structurally:
- parse the SVG XML and, when present, the manifest JSON;
- confirm all SVG ids are unique;
- recompute every `data-placement-rule="mean-of-member-centers"` position from the referenced member ids and compare it with the rendered representative anchor within 0.5 SVG user units or 1% of the nearest member spacing, whichever is smaller;
- confirm every non-null manifest `svg_ids` target exists exactly once;
- decode every raster data URI and compare its SHA-256, byte length, MIME type, and dimensions with both the manifest and sidecar;
- scan for external paths and forbidden elements or attributes;
- render the source SVG once in a standard SVG renderer at intended paper size and once in grayscale.

Then run a Figma smoke test when Figma is available.

For a figure with any raster slot:
1. import `output/figure_figma.svg`;
2. select one raster slot independently;
3. replace its image content with a high-contrast checkerboard or test thumbnail;
4. confirm its exact label, border style, connectors, and layout remain unchanged;
5. confirm ordinary text remains editable;
6. confirm visual appearance at intended paper size.

For an all-vector figure or a figure whose only non-native assets are inline licensed vectors:
1. import `output/figure_figma.svg`;
2. independently select and edit one inline vector glyph without changing adjacent labels or connectors;
3. independently edit one ordinary text label;
4. confirm groups, reading order, line appearance, and layout at intended paper size.

Set `figma_compatibility` to `verified` only after this smoke test passes. Otherwise keep `unverified` and report that Figma compatibility was not verified. A Figma-exported round trip is a derivative editing copy, not the canonical source.

Create:
- `output/figure_figma.svg` always;
- `output/figure.pptx` with native editable shapes and text;
- `output/figure.drawio` with editable graph cells and edges;
- `output/figure.pdf` as a vector export or preview;
- a structural validation report that clearly states what was and was not checked;
- `output/assets/asset_manifest.json` when any non-native asset is used;
- one sidecar PNG or JPEG per approved raster asset. An inline licensed vector needs complete manifest provenance but no raster sidecar.

After automated checks pass, show the reconstructed outputs to the researcher for a final scientific and visual check. Do not write or infer final approval on the researcher's behalf.
````
