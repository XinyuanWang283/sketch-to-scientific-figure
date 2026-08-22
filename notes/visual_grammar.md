# Generic visual grammar for scientific method figures

Use a small and stable visual vocabulary. Forms encode scientific roles; they do not decorate individual objects.

## Sketch semantic geometry before visual style

Authoritative equations and method text define the science. Once a scientifically valid hand-drawn glyph or spatial relation is recorded under `SKETCH SEMANTIC LOCKS`, the sketch becomes binding visual authority for that feature.

Cleanup is not reinterpretation. It may smooth a line, regularize stroke weight, align equivalent instances, translate a locked cluster, or scale it proportionally when permitted. It may not replace a locked silhouette, swap meaningful ports, rearrange members inside a locked cluster, move a mathematical representative away from its contracted position, or detach a stage transition from the states it connects.

Read `notes/sketch_fidelity_and_spatial_locks.md` for the lock schema, derived-placement rule, transition rule, flexibility boundary, and pre-display checks.

## Structure-first color policy

Topology, locked sketch geometry, grouping, alignment, whitespace, and scale establish the primary hierarchy. Color provides an optional secondary semantic cue. A monochrome or near-monochrome figure is valid when color does not encode a necessary contracted distinction; color must never be added merely to make the figure attractive.

Use the same palette and semantic color-role mapping across the approved proposal set by default so candidates are compared by layout rather than color. When `PROPOSAL_MODE: exploratory-five` and the researcher explicitly approves `COLOR_MODE: per-candidate-exploration`, keep one invariant semantic role vocabulary but assign five materially different restrained palette directions and filled-role strategies before generation.

Do not use color differences as a substitute for proposal diversity. `focused-one` has no set-diversity requirement; `directed-three` compares three declared narrative decisions; `exploratory-five` compares five declared tracks. Enforce structural difference only within the active FIDELITY_MODE and lock scopes. In per-candidate color exploration, evaluate palette diversity separately.

Before proposing layouts, first decide whether color is necessary. If not, use `COLOR_MODE: neutral-structure`. If it is, derive one palette from evidence in the current brief: the subject's actual materials, instruments, phenomena, audience, publication medium, supplied visual conventions, or known researcher preferences. Do not infer a stereotyped color merely from a domain name.

A supplied swatch sheet is inspiration until the researcher approves its role mapping in figure context. Use `PALETTE_STATUS: provisional` for an untested mapping, keep the active tokens and layout studies neutral, and record any colored idea only as a provisional candidate. Do not use generative image editing to recolor a scientifically accepted raster candidate; defer the palette to semantic SVG styling or regenerate from the approved blueprint and repeat scientific review.

When the researcher explicitly requests five differently colored, filled candidates under `exploratory-five`, use `PALETTE_STATUS: exploration-approved`. Define five complete token sets first, give every candidate visible soft fills from its initial generation call, preserve readable neutral ink and grayscale-independent science, and keep equivalent semantic roles named consistently across the set. The selection gate may choose layout and palette from different candidates; combine them later through SVG tokens, not raster recoloring.

The approved palette plan contains:

- a subject basis grounded in the current inputs;
- a semantic logic that maps scientific roles to named tokens;
- a publication context;
- one signature accent use tied to the primary scientific relationship when COLOR_NECESSITY is not none;
- one plausible generic default that was considered and rejected;
- 4–7 named working color tokens plus the background, expressed as hexadecimal values.

For a locked colored palette, if the same rationale and accent family could be reused unchanged for an unrelated method figure, revise the palette before generation. Distinctiveness must come from relevance, not novelty for its own sake.

Qualitative color budget:

- neutral structure remains dominant;
- use at most one muted primary accent family;
- use at most one optional secondary accent family;
- use accents selectively rather than coloring every available object;
- most mathematical text remains in the approved ink or secondary-text color;
- use the secondary accent only when the contract contains two genuinely different semantic roles that structure alone cannot communicate clearly.

The former 70–85% neutral, 10–25% primary, and 5% secondary ranges may be used as a rough review diagnostic, not as a generation target or pixel-level compliance quota.

Neutral structure-study tokens:

```text
charcoal:       #252525
secondary-gray: #7C7C7C
light-gray:     #D9D9D6
soft-fill:      #F2F1ED
optional-primary-accent: #667F8A
optional-primary-fill:   #E7ECEE
```

Use the neutral ink, grays, and soft fill for provisional or neutral structure studies. Omit the optional accent unless COLOR_NECESSITY names a contracted role. A locked colored palette may instead draw from a restrained mineral, botanical, instrument, material, or phenomenon-derived family, provided print contrast and semantic clarity remain adequate. Never combine several fashionable families by default.

Valid semantic roles can include observed versus inferred, fixed versus optimized, physical operator versus learned component, current stage versus shared context, or highlighted path versus supporting structure. These are examples only, not mandatory categories. Colors describe roles, not specific variable names.

If no semantic color role is supplied or COLOR_NECESSITY is none, remain neutral rather than inventing an accent.

Explicitly avoid:

- bright teal plus orange combinations;
- saturated navy headings;
- rainbow pipelines;
- decorative color coding;
- gradients, glow, and shadow effects;
- colorful cards;
- Canva-like palettes;
- an unplanned different palette for each proposal outside `per-candidate-exploration`;
- coloring every variable, arrow, module, box, or outline.

## Arrows and structural relations

Read every arrow as a sentence with a verb. Use an arrow only when the contract supports one of these meanings:

- transforms into;
- produces;
- measures;
- passes information to;
- evolves into;
- initializes;
- causes;
- follows in sequence.

Do not use arrowheads for:

- belongs to;
- is part of;
- is labeled by;
- corresponds to;
- is grouped with;
- is an example of.

Show those structural associations with proximity, alignment, braces, enclosure, shared visual form, or a plain leader line. Do not add branching, feedback, or equation arrows unless the scientific contract explicitly contains that directed relationship.

## Shape vocabulary

| Scientific role | Preferred representation | Avoid |
|---|---|---|
| State or image | recognizable content-bearing thumbnail in a thin semantic frame, or a short stack | empty frame with only a variable, device mockup, thick frame, decorative card |
| Measurement | trace, strip, matrix, sample set, or domain-specific minimal mark | generic database icon |
| Operator or module | the approved sketch-locked silhouette when one exists; otherwise a compact labeled module or domain-grounded operational glyph on a directed path | substituting a locked glyph; an uncontracted default trapezoid, unrelated gear, glossy block |
| Domain or manifold | quiet two-dimensional region | decorative 3D surface |
| Repeated state | 2–4 exemplars plus an ellipsis | drawing every instance without need |
| Functional relation | thin arrow with one verb-like meaning | arrow for ownership or annotation |
| Structural association | alignment, proximity, brace, enclosure, or plain line | causal arrowhead |
| Annotation | short label and optional plain leader line | paragraph inside the figure |
| Equation | separate typeset object aligned to the diagram | decorative arrow into the equation |

Use rounded rectangles only when their geometry communicates a consistent module category. Do not surround every object with a card. Avoid decorative icons and 3D perspective unless the science requires spatial depth.

## Visual embodiment: make the scientific role recognizable

Separate three layers:

1. **Scientific identity** — the exact variable, operator, state, measurement, or module defined by the contract.
2. **Visual anchor** — the thumbnail, domain glyph, geometry, trace, strip, or schematic shape that makes the role quickly recognizable.
3. **Presentation state** — border style, stage or condition, temporary/final status, emphasis, and placement.

The scientific contract controls identity. The approved VISUAL EMBODIMENT BRIEF controls the anchor. Borders, labels, and layout control presentation state. Do not bake all three into one flattened image.

An image-valued state normally needs recognizable internal content. Pair that content with exact notation as separate, complementary encodings:

- the visual anchor answers “what kind of thing is this?”;
- the label answers “which exact scientific quantity is this?”;
- the border or surrounding structure answers “what status or stage does it have?”

Choose visual anchors with the following hierarchy:

1. native vector glyph that remains recognizable at paper size;
2. project-owned or appropriately licensed SVG glyph;
3. the smallest necessary user-provided or generated raster atom when complex imagery carries essential recognition.

Use generic notation-only treatment when the entity is genuinely abstract or when a pictorial glyph would imply unsupported physical meaning. Do not force every variable into an icon.

For repeated anchors:

- preserve one stable visual vocabulary and content family;
- vary only the dimension named in VARYING COMPONENTS;
- use shared masters or construction logic for invariant geometry;
- keep exact labels, borders, and connectors independent for every instance;
- do not imply progress by sharpening, denoising, adding detail, or increasing realism unless that change is part of the scientific claim.

For averaged, pooled, shared, or compressed representations, distinguish the operation precisely. A shared object is not automatically an average object, and several measurements do not automatically form a complete dataset. Use grouping and connection counts to communicate sharing before inventing appearance changes.

When the method defines a representative as a mean, centroid, or temporal center, place its visual anchor at the arithmetic mean of its displayed member-anchor positions. On a straight path this is the corresponding mean path coordinate, even when it lies between two beads. Do not center it from a panel, card, column, label, brace width, or partial group.

Every icon or thumbnail must pass one question: what scientific distinction becomes faster or safer to decode because this object is present? If the answer is only “the figure looks richer,” remove it.

## Replaceable image atoms

When ASSET POLICY approves a non-native thumbnail:

- crop it to the smallest semantic region needed for recognition;
- keep labels, equations, arrows, border styles, legends, colorbars, and scale bars out of the pixels;
- give content, border, and label separate semantic object ids in the final SVG;
- for a raster atom, keep an identical sidecar and a provenance manifest; for an inline licensed SVG, keep source, revision, license, attribution, and modification status in the manifest without inventing a raster sidecar;
- mark generated content as schematic and non-evidentiary;
- never flatten a panel or whole figure to avoid reconstructing editable structure.

Generated medical or biological imagery may denote the object class or role of a contracted reconstructed state, but its pixels must not be presented as a patient study, acquired observation, ground truth, the method's actual reported reconstruction, diagnostic example, or quantitative result. Real sensitive imagery requires user-confirmed de-identification and provenance. Record uncertainty instead of inventing a license, source, or privacy clearance.

## Information density

Information hierarchy is a contract decision, not a last-stage cleanup. Use the approved `HIERARCHY MAP`:

- `HERO` carries the three-second message and receives the strongest position, scale, and whitespace;
- `MAIN-BODY` contains the minimum flow needed to decode the method;
- `AUDIT-INSET` preserves dense indexed verification without becoming the main visual mass;
- `CAPTION` carries long definitions, qualifications, provenance, and equations that do not need to be seen for visual decoding.

For a main-paper `story-first` figure, do not render every scientifically valid detail at equal weight. Moving an exact repeated relation into an indexed inset is allowed only when correspondence remains individually recoverable. Never merge, average, or discard measurements to make the page quieter.

Apply `VISIBLE_TEXT_BUDGET` to ordinary prose, mathematical labels, equations, and repeated indices together. Apply `COMPLEXITY BUDGET` to major objects, repeated-detail strategy, connector factoring, elbow count, occupancy, and downscaled legibility. Correct notation can still be visually excessive.

- A visual object normally combines one content-bearing visual anchor with a short separate symbol or label, not its complete defining equation.
- Do not repeat definitions such as `output = model(input)` inside every output object.
- Put a full equation in separate whitespace only when the equation itself is part of the one-sentence message.
- Keep repeated definitions in manuscript text or caption.
- Do not include a generic footer sentence such as “Illustrated for…” unless the user explicitly requests it.
- Do not add explanatory callout boxes when grouping, notation, and short labels communicate the same relation.
- Factor out repeated modules or operators when doing so preserves scientific meaning.
- Compress repeated observations into exemplars, stacks, shared headers, or ellipses when the contract permits it.
- After hiding full equations, the visual anchors, short labels, and topology should still communicate the VISUAL MESSAGE. If they do not, revise the embodiment before adding more prose.

## Typography

- Ordinary labels use Arial, Helvetica, or Source Sans.
- Mathematics uses one consistent LaTeX font and neutral color.
- Use at most two principal text sizes.
- Avoid large bold headings and repeated prose-plus-notation labels.
- Default `TITLE_POLICY` is `none`.
- Panel identifiers such as `(a)` and `(b)` appear only when the scientific contract requires actual panels.

## Visible-prose budget

Before generating layouts, list every allowed non-mathematical phrase under `VISIBLE_PROSE_BUDGET`. Do not add ordinary text that is absent from that list.

Treat this as a pre-display hard allowlist. Transcribe all visible ordinary-language text from each candidate. An inferred row caption, category heading, legend, or explanatory phrase that is not listed requires regeneration; it is not a harmless note to delete during final SVG reconstruction.

Prefer, in order:

1. mathematical notation;
2. short module names;
3. essential panel labels;
4. a few short relational phrases when notation alone is ambiguous.

Method explanation, generalization claims, dataset description, training details, long definitions, border-style explanations, and tutorial instructions normally belong in `CAPTION_ONLY_CONTENT` rather than on the canvas.

## Layout and hierarchy

- Use a hidden alignment grid.
- Align equivalent objects across panels, stages, branches, or conditions.
- Maintain one obvious reading direction.
- Minimize arrow crossings and endpoint ambiguity.
- Do not allow transition arrows or annotations to float ambiguously between regions; attach them to clear anchors or a progression spine.
- Use whitespace before adding boxes or divider lines.
- Do not give all objects equal visual weight.
- Make the relation carrying the one-sentence message dominant through position, scale, alignment, and whitespace.
- Keep invariant and varying components visually distinguishable through structure, with semantic color as a secondary cue rather than the sole cue.
- Align stages through a clear spine, shared grid, or repeated anchor when stages exist in the runtime contract.
- For a locked stage transition, attach the connector directly to its contracted source and target, not to a header rail, page margin, or decorative schedule line.
- Avoid one region becoming dramatically wider or denser than comparable regions without scientific justification.
- Treat unexplained empty areas as a layout defect rather than automatically filling them with decoration.
- Evaluate the figure at intended paper size, not only when zoomed in.

Use visual strength in this order:

1. the relationship carrying the one-sentence message;
2. required scientific entities;
3. supporting context;
4. labels and secondary notation.
