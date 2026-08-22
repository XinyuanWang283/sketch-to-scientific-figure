# Prompt 02: selected layout to semantic SVG

Use this only after Gate 2: the researcher approves or repairs the sole scientifically safe proposal, or selects one from a multi-proposal set, and approves the repair directive.

````text
Reconstruct the selected layout as a newly constructed vector-editable semantic SVG from `scientific_truth`, the selected `candidate_blueprint`, `selected_candidate_map`, and `svg_reconstruction_spec`. Do not mechanically trace pixels, flatten the figure, or use the PNG as a scientific source. Treat Figma import as a downstream compatibility target that must be smoke-tested rather than assumed.

Before drawing, reread in this order:
1. the approved SCIENTIFIC CONTRACT;
2. `scientific_truth.json` and its source hashes;
3. the selected candidate blueprint and approved REPAIR DIRECTIVE;
4. `selected_candidate_map.json` and `svg_reconstruction_spec.json`;
5. the original hand sketch and authoritative equations/method text;
6. every approved asset source and current asset manifest, if any.

Confirm that the approved REPAIR DIRECTIVE names `selected_layout_candidate` and `selected_palette_candidate` independently. The latter may be `shared` only when per-candidate palette exploration was inactive. If the contract entered this step with `PALETTE_STATUS: provisional` or `exploration-approved`, the directive must resolve it to one exact `locked` token set before any SVG styling begins.

Authority and scope:
- The scientific contract and authoritative equations determine entities, notation, topology, grouping, arrows, invariants, variations, figure role, detail mode, hierarchy, complexity and text budgets, title, prose, and color policy.
- The hand sketch remains binding visual authority for every approved SKETCH SEMANTIC LOCK whose scope includes the selected layout candidate unless the contract records an exact scientific correction. Every `all-candidates` lock applies.
- The candidate blueprint controls semantic topology and geometry. The selected-candidate map transfers only composition, hierarchy, proportions, palette, glyph character, whitespace, and rhythm from the PNG inside FLEXIBILITY ZONES. The PNG cannot override SCIENTIFIC LOCKS, any in-scope SKETCH SEMANTIC LOCK, stable IDs, ports, source/target metadata, exact counts, or computed spatial rules.
- The blueprint depiction policy controls visible repetition. For `representative_template`, reconstruct only the declared representative and preserve the complete semantic multiplicity in metadata and caption support. For `literal_instances`, validate each stage- and type-specific count independently rather than collapsing them into a global total.
- Correct invented pathways, incorrect text, decorative additions, color drift, or scientific ambiguity instead of reproducing them.
- SCIENTIFIC LOCKS and every in-scope SKETCH SEMANTIC LOCK remain immutable. VISUAL EMBODIMENT BRIEF controls how approved entities are made recognizable; ASSET POLICY controls which non-native atoms may be used.

Priority:
1. scientific correctness;
2. ONE-SENTENCE MESSAGE;
3. topology, grouping, arrow semantics, and authoritative notation;
4. locked sketch glyphs, mathematical placement, stage-transition attachment, and salience;
5. communication at intended paper size;
6. economy of marks and editability.

Preserve the approved `HIERARCHY_MAP`, `COMPLEXITY_BUDGET`, `ART_DIRECTION_BRIEF`, and `VISIBLE_TEXT_BUDGET`. Do not promote an audit inset into the hero, reintroduce caption-only content, or increase label/connector repetition merely because the SVG canvas has room.

Semantic construction:
- use native SVG vector primitives for all reproducible structure and for every visual anchor that remains recognizable when built as vector geometry;
- assign clear semantic group ids to major scientific objects, conceptual regions, branches, stages, and equations;
- keep ordinary labels as editable SVG text using Arial, Helvetica, or Source Sans;
- render mathematics with one consistent LaTeX-to-SVG vector workflow;
- preserve each source expression in a data-latex attribute;
- align equivalent semantic objects and use consistent line weights;
- keep functional arrows, structural lines, braces, and leader lines as separate editable objects.
- attach `data-source`, `data-target`, `data-relation-type`, and applicable `data-rule-ids` metadata to every scientific connector;
- keep exact short symbols or labels adjacent to visual objects as separate editable text or math paths; place a full equation in separate whitespace only when its EQUATION ROLE is PRIMARY;
- factor out repeated modules, operators, and definitions when scientifically safe.
- reconstruct every in-scope locked sketch glyph as native vector geometry with its approved silhouette, orientation, meaningful ports, and repeated-instance identity. Smooth hand-drawn wobble without substituting another module type.
- place member anchors before any contracted mean, centroid, or temporal-center representative. Compute the representative from the final member-anchor coordinates, then store its member ids and placement rule on the semantic group, for example `data-members="z0 z1 z2 z3"` and `data-placement-rule="mean-of-member-centers"`. Do not derive the position from panel or card bounds.
- keep in-scope locked clusters internally intact. Translate or uniformly scale a cluster only when FLEXIBILITY ZONES permits it.
- construct every approved replaceable asset as the smallest possible atomic content object inside a semantic group with separate content, border, label, and connectors;
- do not promise pixel-level editability for a raster atom. The atom must be independently selectable and replaceable; its internal pixels are not vector-editable.

Required replaceable-slot structure:

```svg
<g id="state-<entity-id>" data-role="state-image" data-asset-id="<asset-id>">
  <image id="asset-<asset-id>" href="data:image/png;base64,..."
         x="..." y="..." width="..." height="..."
         preserveAspectRatio="xMidYMid meet"/>
  <rect id="border-<asset-id>" .../>
  <text id="label-<asset-id>" ...>...</text>
</g>
```

Use this structure only when the contract approves a raster asset. The image appears first, then its native SVG border and label above it. Connectors remain outside or as separately identified siblings. Pre-crop the image to its final semantic region; do not use a mask to hide unrelated content. Use stable ASCII ids even when visible notation contains Unicode or LaTeX.

Arrow rules:
- use arrows only for directed transformations, production, measurement, information flow, evolution, initialization, causality, or sequence explicitly present in the contract;
- use proximity, alignment, braces, enclosure, shared form, or plain lines for membership, part-whole relations, correspondence, grouping, and annotation;
- construct arrowheads as explicit filled polygons;
- stop arrow shafts at the base of arrowhead polygons;
- use stroke-linecap="butt";
- do not use marker-start or marker-end.
- for every locked transition, use a direct native SVG path between the contracted source and target ports. Do not route the relation through a heading, card, page-edge rail, or decorative progression line. Preserve its approved direction and salience without relying on color.

Title and prose:
- default to no title group;
- include a title only if TITLE_POLICY explicitly requests one;
- use only phrases in VISIBLE_PROSE_BUDGET;
- keep CAPTION_ONLY_CONTENT off the canvas;
- do not add a subtitle, schedule title, explanatory footer, prose box, legend, or panel identifier unless the contract requires it.

Color tokens and effects:
- use the approved structure-first COLOR_MODE; topology, locked sketch geometry, grouping, alignment, whitespace, and scale remain the primary hierarchy;
- obey COLOR_MODE, PALETTE_STATUS, COLOR_NECESSITY, PALETTE_RATIONALE, PALETTE_TOKENS, COLOR_ROLES, and COLOR_BUDGET;
- do not begin SVG reconstruction while PALETTE_STATUS remains `provisional` or `exploration-approved`; resolve it inside the approved selection/repair directive without creating another workflow gate;
- when layout and palette come from different candidates, preserve only the selected layout's approved geometry and apply only the selected palette's semantic tokens and fill strategy. Do not trace geometry from the palette source or copy colors pixel-by-pixel from a raster;
- use the exact approved PALETTE_TOKENS rather than substituting a generic academic palette;
- keep neutral structure dominant, with at most one muted primary accent family and one optional secondary accent family;
- apply the primary accent selectively to the approved signature_accent_use when COLOR_NECESSITY names one; a final locked palette selected from an explicit per-candidate exploration may instead use restrained fills for the approved editorial hierarchy, but color must not become the sole carrier of a scientific distinction;
- use the secondary accent only for a second necessary semantic role that structure cannot communicate clearly alone;
- keep most mathematical text in the approved ink or secondary-text color and do not color every variable, arrow, module, box, or outline;
- if COLOR_NECESSITY is none, remain neutral unless the final locked token set came from an explicitly approved per-candidate exploration; in that case preserve its approved restrained fill strategy and grayscale-independent science rather than discarding the selected palette;
- do not drift toward generic gray-blue, cream-and-terracotta, bright teal-plus-orange, saturated-navy, fashionable pastel, rainbow, colorful-card, or Canva-like styling without an explicit current-subject rationale;
- no gradients, filters, shadows, glow, off-white background, decorative effects, or unnecessary 3D.
- never use generative image editing to recolor the selected layout raster. Transfer only the approved semantic token mapping into native SVG fills, strokes, and text classes.

Store the approved semantic colors as reusable SVG style classes or design tokens. Populate every placeholder below with the exact approved hexadecimal value before saving; do not leave template variables in the SVG and do not replace the runtime palette with the emergency gray-blue fallback:

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

Omit classes whose approved token is `none`. Create optional secondary classes only when `optional_secondary_role` is not `none`. Apply classes by semantic role, not variable name. Keep fills and strokes directly editable, and make global accent-family replacement possible by changing the primary accent definitions in one style block.

Hybrid asset and provenance rules:
- default to native vector; a raster is a narrow exception for one approved semantic slot, not a general rendering technique;
- licensed SVG assets must be sanitized and inlined as native vector groups. Do not embed them as `data:image/svg+xml`;
- an approved raster atom must be embedded as `data:image/png;base64` or `data:image/jpeg;base64` so the canonical SVG is self-contained, and the identical decoded asset must also be written as a sidecar under `output/assets/`;
- every `<image>` requires exactly one approved contract slot and exactly one entry in `output/assets/asset_manifest.json`; an unmanifested `<image>` is a hard failure;
- generated raster placeholders have `scientific_status: non-evidentiary-schematic` and default `release_policy: replace-before-publication`. Only explicit researcher approval may change the release policy to `approved-schematic`;
- generated assets may fill only schematic context or state slots approved by the contract. A generated atom may denote the object class or role of a reconstructed state, including an approved \(\hat x_t\) output slot, but its pixels must never be presented as the method's actual reported reconstruction, measurement, ground truth, diagnostic example, quantitative comparison, scale-bearing evidence, or performance result;
- real medical or sensitive imagery requires user-confirmed de-identification and provenance. Do not store patient identifiers or absolute local source paths in the manifest;
- do not invent a license for generated content or a user-owned asset. Record unknown or inapplicable fields honestly;
- every raster atom has explicit x, y, width, height, aspect-fit behavior, pixel dimensions, byte length, and checksums in the manifest;
- target at least 300 effective ppi at intended paper size, unless the publication specification requires more;
- default size budget: at most 1 MB per raster atom and 5 MB for the complete SVG unless the approved contract records an exception.

Materialize approved assets before SVG assembly:
1. Resolve every `approved_non_native_assets` entry to actual content before writing its SVG slot. Do not create a manifest entry for an asset that does not exist.
2. For each `generated-placeholder`, generate either one standalone asset or a coherent asset-only family. Generate only the image content: no variable label, time index, dashed or solid border, arrow, operator, legend, colorbar, scale bar, stage heading, or explanatory text may be baked into the pixels.
3. Do not crop an asset from a rendered layout proposal. If a coherent family is generated together, isolate each approved member deliberately and save it under its exact stable id as `output/assets/<asset-id>.png` or `.jpg`.
4. Preserve the approved family vocabulary and only the contracted state variation. For medical-imaging placeholders, prefer a phantom-like schematic over realistic patient imagery.
5. Visually inspect every materialized asset against its recognition target, forbidden implications, privacy boundary, dimensions, and family consistency before embedding it. Regenerate an unsafe or misleading atom. Keep `human_reviewed: false` until the researcher has reviewed that exact asset; never infer review from approval of the general asset policy.
6. Record the actual generator and version, generation date, prompt SHA-256, seed when available, exact content checksum, and sidecar geometry. Do not invent missing provenance.
7. If approved generation is unavailable or fails, use an approved native-vector fallback when the VISUAL EMBODIMENT BRIEF permits it. Otherwise stop and report the missing asset instead of embedding fabricated content or a phantom manifest record.

Figma compatibility and file integrity:
- no external images, fonts, styles, scripts, event handlers, `foreignObject`, animation, HTTP(S) references, `file:` references, or absolute local paths;
- no SVG markers, `data:image/svg+xml`, fragile filters, masks, shadows, glow, or decorative effects;
- use simple supported primitives; use a `clipPath` only when pre-cropping cannot satisfy the asset slot and a Figma smoke test passes;
- ordinary text remains editable and uses available fonts; do not convert ordinary labels to outlines;
- major components and approved raster slots remain independently selectable and replaceable;
- treat the source SVG as canonical and, whenever non-native assets exist, treat its manifest as part of that canonical source. Do not rely on Figma round-trip export to preserve ids, `data-*` attributes, metadata, or CSS classes;
- the SVG remains understandable when printed in grayscale; it may remain neutral when COLOR_NECESSITY is none.

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

Before completion, render the SVG at intended paper size and verify:
1. the ONE-SENTENCE MESSAGE and reading direction are immediately visible;
2. every entity and relationship matches the contract;
3. every arrow has one supported verb-like meaning and correct direction;
4. structural associations do not use arrowheads;
5. invariant and varying components are distinguishable;
6. equations and notation match the authoritative source;
7. full equations do not dominate object interiors or repeat unnecessarily;
8. transition arrows and annotations attach to clear anchors and do not float between regions;
9. comparable regions have justified width and density, with intentional whitespace;
10. a transcription of every visible ordinary-language phrase matches the exact VISIBLE_PROSE_BUDGET allowlist, with no inferred headings or explanations;
11. TITLE_POLICY, COLOR_MODE, final `PALETTE_STATUS: locked`, COLOR_NECESSITY, PALETTE_RATIONALE, PALETTE_TOKENS, COLOR_ROLES, and COLOR_BUDGET are obeyed;
12. the REPAIR DIRECTIVE's selected layout source and palette source are recorded, the signature accent use reinforces the primary scientific relationship, and no generic palette substitution or raster recoloring occurred;
13. semantic color classes are reusable, globally replaceable, and directly editable;
14. the design remains understandable in grayscale and remains neutral only when permitted by COLOR_MODE and COLOR_NECESSITY;
15. no unnecessary object can be removed without loss of meaning;
16. hiding full equations still leaves the VISUAL MESSAGE, entity classes, required counts or stages, and principal directed relations recoverable;
17. every visual anchor obeys VISUAL EMBODIMENT BRIEF and introduces no forbidden visual implication;
18. equivalent objects are aligned and line weights are consistent;
19. all labels, equations, arrows, borders, legends, and scale-bearing marks are native editable objects rather than baked into a raster;
20. each `<image>` has one approved slot, one manifest entry, one matching sidecar checksum, a valid scientific status, and separate content plus every contract-required border or label object;
21. raster dimensions, decoded byte length, checksum, effective resolution, aspect fit, and file-size budget match the manifest;
22. the SVG contains no unapproved raster or base64 content, external reference, `data:image/svg+xml`, marker, gradient, filter, mask, script, event handler, animation, `foreignObject`, shadow, glow, or decorative effect;
23. licensed assets have complete source, revision, author, license, attribution, and modification records; sensitive user assets have user-confirmed de-identification and provenance;
24. generated placeholders remain non-evidentiary, contain no unsupported diagnostic or quantitative content, and have the required caption disclosure and release policy;
25. major scientific components and every approved asset slot remain independently selectable and replaceable;
26. every in-scope locked sketch glyph preserves its approved silhouette, orientation, ports, and repeated-instance identity;
27. every group mark covers its exact members, and every mean/centroid/temporal-center representative equals the computed mean of the final member-anchor coordinates;
28. every in-scope locked transition connector directly attaches the contracted source and target in the correct direction and remains prominent in grayscale with text hidden;
29. all movement or compression stays inside FLEXIBILITY ZONES and every approved deviation in the repair directive is accounted for;
30. every SKETCH SEMANTIC LOCK whose scope includes the selected layout candidate passes, including every `all-candidates` lock.

Also verify the presentation contract explicitly: every item remains in its approved HERO, MAIN-BODY, AUDIT-INSET, or CAPTION layer; total equations, labels, and repeated notation obey VISIBLE_TEXT_BUDGET; major objects, repetition strategy, connector factoring, elbow count, occupied area, and paper-size legibility obey COMPLEXITY_BUDGET; and the result realizes ART_DIRECTION_BRIEF without introducing a generic card-based or formula-first style.

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
- `output/assets/asset_manifest.json` when any non-native asset is used;
- one sidecar PNG or JPEG per approved raster asset. An inline licensed vector needs complete manifest provenance but no raster sidecar.
````
