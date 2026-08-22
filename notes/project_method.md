# Project method and boundaries

## Positioning

This repository provides one durable job:

> Turn authoritative scientific sources and a hand-drawn sketch into machine-readable truth, deterministic topology skeletons, controlled PNG visual proposals, and one validated semantic SVG.

The workflow supports technical method diagrams across domains. It does not contain a default modality, method, variable set, stage schedule, panel structure, or visual template.

## Intake modes and confirmation boundary

The workflow has two intake paths:

- `INTAKE_MODE: direct` synthesizes a complete supplied specification and asks only when an unresolved high-impact ambiguity remains.
- `INTAKE_MODE: guided` reads every supplied source first, infers known fields, and asks exactly one short highest-impact question per turn with a recommended default. A normal run needs about 3–6 questions, but stops by information sufficiency rather than question count. Low-impact font, spacing, corner-radius, and hexadecimal-color choices are inferred unless the researcher explicitly wants to direct them.

Guided intake persists `discovery_status: pre-reading | active | sufficient` and per-field resolution as `inferred | user-confirmed | user-delegated | unresolved`. It writes `<run-directory>/interview_state.yaml` after pre-reading and after every answer when a run directory exists; otherwise state is task-resident. Resume reads this state first and asks only the next unresolved high-impact question. Confirmation 1 freezes an immutable truth snapshot. A later truth-level change creates a new revision and returns that revision to confirmation 1 rather than overwriting the approved snapshot.

Discovery questions are not approvals. Three confirmations remain: scientific truth before generation, PNG macro-layout/palette before reconstruction, and final scientific sign-off after executable validation and final-size review.

## Four strictly separated layers

### 1. Generic Skill core

The repository-scoped Skill and generic prompts define how to:

- read a hand sketch as a provisional topology source;
- read method text, equations, and paper excerpts as scientific authority;
- promote scientifically valid hand-drawn glyphs and spatial relations into binding `SKETCH SEMANTIC LOCKS`;
- separate locked sketch geometry from explicit `FLEXIBILITY ZONES`;
- identify entities, functional relationships, and structural associations;
- distinguish invariant from varying components;
- decide whether a relation needs an arrow;
- separate scientific identity from its visual embodiment;
- classify the scientific structure;
- propose 1, 3, or 5 controlled layouts according to one valid proposal-mode/count pair;
- budget visible prose and color;
- review candidates with a formula-hidden comprehension test;
- reconstruct a semantic SVG while keeping any approved image atom replaceable.

The core must not encode paper-specific variables, stages, operators, schedules, modalities, or panel arrangements.

### 2. Hard runtime scientific contract

Every run extracts a new contract from the user's current sketch and scientific materials. Current equations and explicit method statements are the authority for scientific truth. The sketch is provisional until a glyph or spatial relation is checked against that truth; every approved feature recorded under `SKETCH SEMANTIC LOCKS` then becomes binding visual authority within its scope. The exact scope tokens are `all-candidates` for a universal lock, `sketch-faithful-candidate` for a faithful-role-only lock, or explicit named candidate IDs.

The same contract records `FIDELITY_MODE`, `FLEXIBILITY ZONES`, entities, notation, directed and structural relationships, invariants, forbidden implications, `FIGURE_ROLE`, `DETAIL_MODE`, `HIERARCHY_MAP`, `COMPLEXITY_BUDGET`, `ART_DIRECTION_BRIEF`, `VISIBLE_TEXT_BUDGET`, title policy, color and palette state, asset policy, `PROPOSAL_MODE`, `PROPOSAL_COUNT`, and any applicable exploration program. Visual generation cannot change scientific truth, substitute an in-scope locked glyph, move a contracted representative, detach a stage transition, or turn a schematic into evidence.

Default to `FIDELITY_MODE: sketch-bound` when the sketch contains a deliberate pipeline, architecture glyph, stage arrangement, or spatial story. In that mode every candidate keeps the locked macro-backbone. Use `topology-exploratory` only when the researcher explicitly approves broad macro-topology search.

`FIDELITY_MODE: controlled-mixed` is a specialized `exploratory-five` option. Its `CANDIDATE EXPLORATION PROGRAM` assigns exactly five roles: one method-first narrative, one sketch-faithful spatial layout, and three different information-design emphases derived from the current method. The method-first candidate may reorganize unlocked macro-regions, but it is not exempt from in-scope scientific or sketch-semantic locks. Permission to polish, explore, or add visual flexibility never unlocks in-scope semantic geometry.

When a representative is scientifically defined as a mean, centroid, or temporal center, compute its displayed location from the arithmetic mean of its displayed member-anchor positions. Do not use a card, label column, or partial group as the placement reference. A contracted stage transition must attach directly to its declared source and target ports, preserve direction, and remain prominent without relying on color. When the researcher specifies connector geometry, record it as a scoped `connector-routing` lock; `orthogonal-only` permits horizontal/vertical shafts and 90-degree elbows but no diagonal arrow shafts.

The communication fields have fixed responsibilities:

- `FIGURE_ROLE` is exactly `main-paper`, `appendix-or-audit`, `slide-or-poster`, `graphical-abstract`, or an explicit other role, plus medium and approximate reading scale.
- `DETAIL_MODE` is exactly `story-first`, `balanced`, or `audit-complete`. Main-paper method figures normally use `story-first`.
- `HIERARCHY_MAP` partitions all contracted content into `HERO`, `MAIN-BODY`, `AUDIT-INSET`, or `CAPTION` and states their salience order without relying on color.
- `COMPLEXITY_BUDGET` records count-aware policies for `hero_groups`, `support_repetition`, `audit_regions`, `displayed_equations`, `ordinary_prose`, `connector_policy`, and `visual_anchor_families`.
- `ART_DIRECTION_BRIEF` is object-level, not a list of adjectives. It covers composition/dominant path, domain anchors, silhouettes/ports, whitespace/grouping, connector language, fill/color role, temporary/final status, and anti-patterns.
- `VISIBLE_TEXT_BUDGET` records `ordinary_prose_allowlist`, `stage_or_panel_labels`, `notation_labels`, `displayed_equations`, and `forbidden_inferred_text`. Its prose list maps to `VISIBLE_PROSE_BUDGET`; mathematical repetition still counts toward density.

Moving exact correspondence into `AUDIT-INSET` or definitions into `CAPTION` changes salience, not science. It may not delete a required entity, merge distinct measurements, change counts, or imply an unsupported summary operation. When required detail exceeds the main-field budget, use the audit layer instead of shrinking every object into a wiring field.

### 3. Runtime `VISUAL EMBODIMENT BRIEF`

The embodiment brief is derived only after the scientific identities are fixed. It specifies how an approved entity becomes recognizable without redefining it. For each entity that benefits from visual grounding, it records:

- the one-second recognition goal;
- the domain-relevant visual anchor;
- the asset mode and source status;
- appearance invariants across stages or repeated instances;
- forbidden evidentiary or causal implications;
- the stable replacement target used during manual editing.

An image-valued state should normally be constructed as `visual content + independent variable label + independent semantic border`, not as an empty formula box. A generated CT thumbnail is permitted only as a `generated-placeholder`: it may help the reader recognize the role of a reconstructed image state, but its pixels cannot be called acquired data, ground truth, the method's actual reconstruction result, or quantitative evidence.

After direct synthesis or guided discovery becomes sufficient, Gate 1 presents the contract, sketch locks, flexibility zones, communication fields, palette status, text budget, embodiment brief, and proposal program together. Guided answers may be `inferred`, `user-confirmed`, `user-delegated`, or `unresolved`; these resolution states record provenance and are not approvals. Gate 1 is the first formal approval.

### 4. Examples

Specific examples live only in `examples/`. They demonstrate how the generic workflow was applied to one paper. They are not default templates, are not loaded automatically, and cannot contribute scientific rules to an unrelated run.

## Proposal modes

`PROPOSAL_MODE` and `PROPOSAL_COUNT` are one exact pair and are independent of `FIDELITY_MODE`:

| Mode | Count | Program |
|---|---:|---|
| `focused-one` | 1 | one best-fit synthesis when topology is fixed |
| `directed-three` | 3 | normal default: sketch-faithful cleanup, mechanism-dominant narrative, and compact publication-scale representation |
| `exploratory-five` | 5 | method-first, sketch-faithful, and three method-specific information-design emphases |

Guided intake recommends `directed-three` by default unless topology is fixed enough for `focused-one`. `controlled-mixed` and `per-candidate-exploration` remain valid only for `exploratory-five`. The five-track palette program assigns different first-generation tokens with one invariant semantic-role vocabulary; it never authorizes generative recoloring.

Each proposal is generated independently, not as a contact sheet. Proposals share the scientific contract, applicable locks, canvas, reading scale, recognition goals, asset roles, `VISIBLE_TEXT_BUDGET`, and `COMPLEXITY_BUDGET`. Proposal-specific differences must be approved choices in hierarchy, reading direction, grouping, compression, whitespace, abstraction, or art direction; styling alone does not create a distinct hypothesis.

Before rendering, write one blueprint per proposal. It records:

- primary reading direction and `HIERARCHY_MAP`;
- location of the hero relationship and supporting/audit regions;
- repeated-element compression and invariant-versus-changing encoding;
- visual-anchor placement, reuse, and replaceable asset slots;
- compliance with `COMPLEXITY_BUDGET`, `VISIBLE_TEXT_BUDGET`, and `ART_DIRECTION_BRIEF`;
- handling of every in-scope sketch lock and approved deviation;
- deliberate `CAPTION` content.

Set-level duplicate review runs only when count is greater than one. `directed-three` must test its three declared decisions; `exploratory-five` must fulfill five distinct narrative responsibilities. Color, typography, separators, or box shape alone never rescue a duplicate.

For main-paper `story-first`, `HERO` and `MAIN-BODY` carry the method story while exact repeated correspondence remains inspectable in one compact `AUDIT-INSET`. The generic core never requires three rows, fixed columns, repeated modules at one position, or full expansion of every observation in the main field. Such requirements can come only from the runtime contract.

Use at most one regeneration per blueprint for global composition or hierarchy failure and one local style edit per candidate. Never repair count, index, stage order, grouping, source/target, fan-in/fan-out, centroid, equation, connector rewiring, or backward multiplicity through local raster editing. Revise the blueprint/skeleton or reject the candidate; rebuild exact production details during deterministic semantic SVG reconstruction.

## Visual embodiment and hybrid assets

Visual flexibility is controlled, not decorative. The main object types and scientific process should remain intelligible when full equations are temporarily hidden and only visual anchors, short labels, and topology remain. This formula-hidden comprehension test does not require photorealism; it requires a small number of recognizable, scientifically honest anchors.

Use this asset hierarchy:

1. native SVG primitives and reusable semantic glyphs;
2. licensed SVG assets whose source and license are recorded;
3. a minimal generated or user-provided raster atom when vector abstraction would not communicate the object efficiently.

A raster atom is an exception inside an otherwise editable figure. Keep the atom in a stable semantic group and keep its label, border, arrows, operators, stage indicators, and connector geometry as separate native SVG objects. Replacing the atom must not require redrawing the diagram.

Every non-native asset requires a manifest entry with at least: asset ID, scientific role, source or generation status, license when applicable, placeholder flag, SVG object ID, replacement target, and forbidden implication. User-provided scientific images retain the status provided by the researcher. AI-generated images always remain schematic placeholders regardless of visual realism.

This separation is informed by several open-source patterns without copying any one system wholesale: Penrose separates semantic declarations from styling; PaperVizAgent separates planning, styling, visualization, and critique; NanaDraw distinguishes quick generation from structured editable assembly and includes reusable assets; AutoFigure-Edit uses labeled placeholders and editable SVG reconstruction; Scientific Illustrator prioritizes native editable objects and explicit review gates. The resulting local rule is stricter for scientific evidence: generated atoms may improve recognition but cannot supply facts.

## Structure-first color policy

Establish the primary hierarchy with topology, locked sketch geometry, grouping, alignment, whitespace, and scale. Use color only as a secondary semantic cue. Default to `COLOR_MODE: neutral-structure` when color adds no necessary scientific distinction or the role mapping has not been approved in the current figure.

- record `PALETTE_STATUS: locked` only after the researcher approves the palette and semantic role mapping in figure context; a supplied swatch sheet alone remains `provisional`;
- for a locked palette, derive 4–7 named working tokens plus the background from the current subject, scientific roles, audience, publication context, supplied conventions, and known researcher preferences;
- for a provisional palette, make the active `PALETTE_TOKENS` neutral structure-study tokens with no accent and record any unapproved colored mapping only as `PALETTE_RATIONALE.provisional_candidate`;
- use `COLOR_MODE: per-candidate-exploration` only with `PROPOSAL_MODE: exploratory-five` when the researcher approves palette exploration before generation, and pair it with `PALETTE_STATUS: exploration-approved`;
- in that exploration mode, define a `PALETTE_PROGRAM` that assigns each first-generation candidate its own restrained, paper-appropriate 4–7 role tokens plus background; palette hypotheses must differ materially in hue family or tonal strategy while keeping the semantic role vocabulary invariant;
- record the subject basis, semantic logic, publication context, signature accent use, and generic default deliberately avoided;
- keep neutral structure dominant;
- use at most one muted primary accent family and one optional secondary accent family;
- keep most mathematical text in the approved ink or secondary-text color;
- the secondary accent requires a second necessary semantic role that structure alone cannot express clearly.

When no necessary semantic color role is supplied and exploration is not explicitly approved, use neutral styling rather than inventing an accent. Do not color every object, variable, arrow, module, or box. For a locked colored palette, if the same rationale could be applied unchanged to an unrelated method figure, revise it before generation. Numeric coverage ranges are review heuristics only, not pixel quotas. No palette hypothesis may alter hierarchy so strongly that it obscures a universal scientific or sketch-semantic lock.

Do not use generative image editing merely to recolor a raster candidate that has passed scientific and sketch-fidelity review. The redraw can mutate notation, glyphs, borders, or topology. Per-candidate palette differences must be present in the first generation. Later changes are applied deterministically through semantic SVG tokens; alternatively regenerate from the approved blueprint and repeat the complete review.

## Prose and reconstruction boundary

`VISIBLE_TEXT_BUDGET` governs the complete canvas text plan, including repeated notation and equations. Its `ordinary_prose_allowlist` maps to the exact `VISIBLE_PROSE_BUDGET`; transcribe every ordinary-language phrase and reject any inferred heading, row caption, legend, or explanation absent from it before display. Review total text against `COMPLEXITY_BUDGET`, not only prose correctness.

At Gate 2, `focused-one` is accepted or locally repaired; multi-proposal modes select one safe layout. In `exploratory-five` palette exploration, layout and palette sources may be selected independently. The repair directive resolves the final palette to one exact `PALETTE_STATUS: locked` token set before reconstruction. Semantic SVG reconstruction maps those tokens onto the selected layout's object classes; it does not composite two rasters or generatively repaint the layout.

SVG reconstruction must recompute contracted derived positions from final member-anchor coordinates and attach every locked transition path directly to its contracted source and target. Labels, equations, borders, connectors, and reproducible glyphs remain native editable SVG objects. Figma is a downstream editing target; compatibility remains `unverified` until the applicable all-vector or raster-slot import/edit/replace smoke test passes.

## Human decisions

Two approvals remain mandatory:

1. Gate 1 approves the complete scientific contract, locks and flexibility zones, `FIGURE_ROLE`, `DETAIL_MODE`, `HIERARCHY_MAP`, `COMPLEXITY_BUDGET`, `ART_DIRECTION_BRIEF`, `VISIBLE_TEXT_BUDGET`, visual embodiment, palette state, and proposal program before generation;
2. Gate 2 accepts or selects one scientifically safe layout, selects an exploration-approved palette when applicable, and approves the combined repair directive before SVG reconstruction.

Guided questions, `user-confirmed` discovery answers, and local Gate 2 repairs do not create extra gates. Palette selection stays inside Gate 2 rather than creating a third gate.

## Subscription-only execution boundary

The project runs through built-in ChatGPT/Codex capabilities and remains repository-scoped.

- no OpenAI API or API key;
- no Web App, Streamlit, account system, database, backend, or server;
- no image-generation dependency added to the repository; subscription-native image generation may be used only for an approved replaceable placeholder;
- no paper-specific automation hidden in the generic Skill.

The repository contains instructions, prompts, notes, examples, and source readings. It is not an application scaffold.
