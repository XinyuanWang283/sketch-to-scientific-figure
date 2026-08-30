# sketch-to-scientific-figure technical reference

A repository-scoped Skill with this default user-visible workflow:

> hand-drawn sketch → focused conversational clarification → five separate Codex built-in ImageGen calls → explicit researcher selection or revision → approved selected-candidate region map → editable SVG/PPTX reconstruction + experimental structural draw.io view → PDF export/preview → structural validation → separate researcher decisions

Version 0.1 is a reusable Codex workflow plus one verified reference case, not a universal sketch converter. The live Codex path uses built-in ImageGen when the environment provides it and needs no repository-managed or user-supplied `OPENAI_API_KEY`. Repository Python does not call ImageGen. Each candidate has a mandatory repository-local `generation_event_id`; a native tool-call ID is optional and must never be invented.

The stable offline path is [`scripts/replay_reference_case.py`](../scripts/replay_reference_case.py). It verifies the frozen A–E records, exact Candidate C selection, approved region map, raster-authorization records, validation report, output manifest, and visual approval before replaying the evidence into a new external run. It does not rerun ImageGen. [`scripts/imagegen_workflow.py`](../scripts/imagegen_workflow.py) provides an append-only local consistency ledger, binds transition details to state, preserves introduced evidence across later snapshots, and refuses delivery registration unless a passing machine-readable structural report and matching artifact manifest bind the approved inputs and exact outputs. The local ledger is consistency-checked, not cryptographically tamper-proof without an external signed anchor.

The active case record is [`examples/deep_image_prior/reference_case_v0_1.json`](../examples/deep_image_prior/reference_case_v0_1.json), and the canonical delivery is [`editable_delivery_c_fidelity_v2/`](../examples/deep_image_prior/editable_delivery_c_fidelity_v2/README.md). Its draw.io artifact is only an experimental structural view because the official CLI currently renders major colored regions as black and displays equations as raw LaTeX. The PDF is a preview/export. Visual approval is hash-bound. The checked-in governance fields preserve the pre-authorization snapshot state; the annotated `v0.1.0` tag separately binds project-owner scientific-content, Science Day-use, and public-release approvals to the exact release tree.

The remainder of this document describes the retained V3 adapter architecture:

> scientific truth → paper-aware editorial review → Gate 1 wireframe → registered PNG direction → Gate 2 selection → canonical semantic source + LaTeX → SVG/Figma-ready SVG/PPTX/draw.io/PDF adapters → structural validation → Gate 3 sign-off

V3 is a legacy regression/advanced path, not the default Quick Start. Its deterministic native-object adapters remain relevant after a candidate is approved.

The retained V3 components were designed for several method-diagram families, but v0.1 does not claim cross-sketch or cross-domain performance from that design intent.

## Legacy V3 autopilot

V3 adds a resumable `run_state.json` state machine and stops only at three formal human decisions:

1. **Gate 1 — Editorial story and wireframe:** paper-linked one-sentence message, add/keep/simplify/remove advice, redlined sketch, and recommended/conservative wireframes.
2. **Gate 2 — Registered PNG visual direction:** the researcher/operator selects or rejects registered candidates after reviewing sketch fidelity, macro-layout, palette, and material differences.
3. **Gate 3 — Final scientific delivery:** final-size and grayscale previews, formulas, SVG validation, cross-format compatibility, and the complete package.

All deterministic work between gates runs automatically. Discovery, lint, adapter checks, and low-impact styling defaults do not create extra gates. A compact gate packet contains at most three high-impact questions, recommends one option, records delegated defaults, and supplies the exact resume action.

The delivery source of truth is `source/semantic_figure.json` plus `source/equations.tex`. `master.svg` and every other format are generated views. The SVG, Figma-ready SVG, PPTX, draw.io, and PDF adapters read the semantic source independently. Complex equations retain stable IDs and authoritative LaTeX; no adapter uses PNG as the equation source. PDF files are exports/previews with `semantic_editability=false`, and the Figma-ready SVG remains `IMPORT_READY_UNVERIFIED` until an actual import is checked.

Entrypoints:

```text
python3 scripts/run_workflow.py
python3 scripts/build_figure_editorial_review.py
python3 scripts/build_fixture_semantic_source.py
python3 scripts/render_equations.py
python3 scripts/validate_delivery.py
```

Despite its compatibility filename, `build_fixture_semantic_source.py` is the shared ID-rich SVG-to-canonical-source converter. Sketch-led runs can bind `--truth`, `--wireframe`, and `--candidate`; the PNG is recorded as art-direction provenance only and is never embedded or traced. Paper SVG/PDF outputs use a 180 mm physical width while Figma-ready SVG, PPTX, and draw.io retain the canonical pixel coordinate system.

Current candidate registration verifies location inside the run, PNG readability, SHA-256, a mandatory operator-supplied repository-local generation event ID, and any applicable approval bindings. A native tool-call ID is recorded only when exposed. The record uses `provenance_assurance: operator_attested_not_independently_verified`; the repository does not call or independently prove the identity of a candidate generator.

For a sketch-led run, bind the approved Visual Plan explicitly:

```text
python3 scripts/run_workflow.py \
  --mode sketch \
  --run-dir <new-run-directory> \
  --truth <scientific_truth.json> \
  --paper-source <typed_method.md> \
  --sketch <source_sketch.png> \
  --visual-plan <visual_plan.json> \
  --approved-wireframe <approved_wireframe.svg>
```

`--approved-wireframe-png` is optional when `visual_plan.json` identifies a sibling preview. The recorded approval hash must match that PNG. The run snapshots all three Visual Plan artifacts, copies the exact approved direction for Gate 1, and permits the paper-aware alternative to add only a removable `paper-aware-overlay` group.

## What the Skill does

The current paper materials supply authoritative scientific meaning: entities, variables, operators, equations, invariant and varying components, and forbidden interpretations. The hand sketch initially supplies provisional visual topology, grouping, glyph identity, relative placement, and arrow direction. Once a scientifically valid feature is recorded under `SKETCH SEMANTIC LOCKS`, it becomes binding visual authority for its contracted scope: `all-candidates` means universal, `sketch-faithful-candidate` applies to the faithful role, and named candidate IDs apply only to those candidates. Visual cleanup may refine a scoped lock, but an in-scope candidate may not replace or silently move it.

The Skill compiles those inputs into deliberately separated runtime artifacts:

- `scientific_truth.json`, which fixes meaning, stable IDs, counts, relations, notation, invariants, source hashes, and forbidden implications;
- candidate blueprints, which bind truth instances to regions, ports, edges, rule IDs, and reviewable layout fingerprints;
- deterministic SVG/PNG topology skeletons generated from the blueprints;
- short 350–500 word image briefs containing only the visual message, reference roles, blocking visual rules, art direction, and text whitelist;
- a selected-candidate map that transfers composition and art direction without promoting generated text or connectors to truth;
- an SVG reconstruction spec and validator rule set.

For example, an image-valued state such as `x_0` should normally contain a recognizable image anchor rather than an empty box with only a formula. The anchor may be a native vector glyph, a licensed SVG asset, or—when explicitly approved—a minimal user-provided or generated raster atom. A generated CT image is allowed only as a replaceable schematic placeholder. It may stand for the role of a reconstructed state, but its pixels are never presented as measured data, ground truth, the method's actual reported reconstruction, or quantitative evidence.

After scientific-truth confirmation, the Skill produces the approved number of deterministic blueprints: `focused-one` generates 1, `directed-three` generates 3, and `exploratory-five` generates 5. `directed-three` is the normal comparison default. Every multi-candidate set must pass fingerprint lint before image generation. Role names, palette changes, and box styling do not establish layout diversity.

When an operator uses an external image-generation capability, each candidate should receive one topology skeleton as structural authority and, optionally, one style-only reference. The registered PNG may influence only composition, hierarchy, palette, glyph appearance, whitespace, rhythm, and general art direction. Exact text, authoritative equation source, approved format-specific fallback text, indices, counts, ports, centroids, source/target, arrow direction, and routing are rebuilt from truth and blueprint data.

Color exploration is separately selectable. The ordinary default remains neutral structure with a provisional palette when color roles are unapproved. `COLOR_MODE: per-candidate-exploration` and `PALETTE_STATUS: exploration-approved` are specialized `exploratory-five` rules: a `PALETTE_PROGRAM` assigns the five proposals five materially different, restrained fill systems from their first generation. They are not generated once and recolored later. At Gate 2, the researcher may choose the layout and palette sources independently; one exact `locked` token set is then applied through semantic SVG/Figma tokens without repainting a raster.

After the researcher completes that selection, the Skill reconstructs the result as a vector-editable semantic SVG with any approved raster atoms independently replaceable. Labels, borders, arrows, and connectors remain native SVG objects even when one approved raster atom is used inside an image slot. Every external or generated asset is recorded in an asset manifest for later replacement or attribution.

Before reconstruction, the current default path must materialize a hash-bound selected-candidate map. Its ordinary region boxes and glyph crops are `reference_only_not_embedded` inputs for object-by-object reconstruction and visual QA. Each mapped region records its conversion mode and output IDs, so hard-coded approximation cannot silently bypass the decomposition step. A candidate region may become a delivery atom only after an explicit region-reuse request is recorded in a separate review-draft decision bound to the exact candidate hash and pixel bbox. Such an atom must exclude baked-in labels, borders, arrows, equations, legends, and scale-bearing marks; remain independently replaceable; carry an asset-manifest entry; and keep final publication/scientific approval pending.

The checked-in example at [`examples/deep_image_prior/editable_delivery_c_fidelity_v2/`](../examples/deep_image_prior/editable_delivery_c_fidelity_v2/README.md) demonstrates this boundary with eight approved mapped regions, exactly two unresampled replaceable raster atoms, nine LaTeX-sourced vector equations whose intrinsic aspect ratios are preserved, native arrows and topology, and a PDF that is only a preview/export. The reference-case record binds a separate visual approval; the annotated `v0.1.0` tag carries the later owner approval attestation for the exact release tree.

## Intake and proposal modes

Choose one intake path:

- `INTAKE_MODE: direct` — use when the supplied sketch, method text, equations, figure role, and constraints are already complete. The Skill synthesizes the contract immediately and asks only about unresolved high-impact ambiguity.
- `INTAKE_MODE: guided` — use when the visual brief should be discovered collaboratively. The Skill reads all supplied material first, infers known answers, and asks exactly one short highest-impact question per turn. It recommends a default and skips font, spacing, corner-radius, or color questions unless they change the result. A normal run needs about 3–6 questions, but stops as soon as the brief is information-complete.

Guided intake records `discovery_status` as `pre-reading`, `active`, or `sufficient`, and records each answer as `inferred`, `user-confirmed`, `user-delegated`, or `unresolved`. When a run directory exists, it writes `<run-directory>/interview_state.yaml` after pre-reading and after every answer; otherwise the state remains task-resident. Resuming starts from that state rather than repeating settled questions. Gate 1 freezes an immutable approved snapshot; a later contract-level change creates a new revision and returns that revision to Gate 1 instead of overwriting the approved record.

Discovery questions are not approval gates. The workflow has three V3 gates: editorial story/wireframe, PNG macro-layout/palette selection, and final scientific-delivery sign-off after executable validation.

Choose one proposal program:

| `PROPOSAL_MODE` | `PROPOSAL_COUNT` | Use when |
|---|---:|---|
| `focused-one` | 1 | topology is fixed and only visual treatment is open |
| `directed-three` | 3 | normal default: sketch-faithful, mechanism-dominant, and compact editorial |
| `exploratory-five` | 5 | message/hierarchy remains genuinely unresolved and five fingerprints pass lint |

## Main-paper storytelling controls

The synthesized brief records six controls before proposal generation:

- `FIGURE_ROLE` is `main-paper`, `appendix-or-audit`, `slide-or-poster`, `graphical-abstract`, or an explicit other role; record medium and approximate reading scale with it.
- `DETAIL_MODE` is exactly `story-first`, `balanced`, or `audit-complete`. A main-paper method figure normally uses `story-first`.
- `HIERARCHY_MAP` assigns contracted content to exactly `HERO`, `MAIN-BODY`, `AUDIT-INSET`, or `CAPTION` instead of giving every scientific fact equal visual weight.
- `COMPLEXITY_BUDGET` records limits or policies for `hero_groups`, `support_repetition`, `audit_regions`, `displayed_equations`, `ordinary_prose`, `connector_policy`, and `visual_anchor_families` at intended paper size.
- `ART_DIRECTION_BRIEF` is an object-level brief covering composition/dominant path, domain anchors, silhouettes/ports, whitespace/grouping, connector language, fill/color role, status encoding, and explicit anti-patterns.
- `VISIBLE_TEXT_BUDGET` records `ordinary_prose_allowlist`, `stage_or_panel_labels`, `notation_labels`, `displayed_equations`, and `forbidden_inferred_text`. Its prose allowlist maps to `VISIBLE_PROSE_BUDGET`; repeated notation still counts toward visual density.

For a main-paper method figure, put the one-sentence message in `HERO`, keep only necessary decoding objects in `MAIN-BODY`, and move exhaustive branch correspondence or validator-oriented evidence into one compact `AUDIT-INSET` when scientifically safe. This story-first split preserves auditability without turning the main illustration into a wiring diagram.

## Subscription-only boundary

This repository can be used with the image and coding capabilities available inside a ChatGPT or Codex subscription, but its CLI does not invoke those services or verify their identity.

- no OpenAI API calls;
- no API key request;
- no Web App, Streamlit, database, or server;
- no account or project backend;
- no API key or hosted project backend is required. Local Python checks and the full delivery adapters use the dependencies listed in [runtime requirements](runtime_requirements.md).

The Skill is invoked from a Codex workspace with `$sketch-to-scientific-figure` or `@sketch-to-scientific-figure`.

## Usage

1. Open this repository in Codex.
2. Upload a hand-drawn scientific sketch.
3. Upload or paste the scientific method description, authoritative equations, and any relevant paper excerpt. A reference figure is optional.
4. Invoke the Skill.
5. Choose `INTAKE_MODE: direct` or `guided`. In guided intake, answer one high-impact question at a time; already supplied facts are inferred and skipped.
6. Review paper-grounded editorial advice, redline, and 1–2 wireframes at Gate 1.
7. After approval, use `directed-three` by default; use 1 or 5 only under the stated policy.
8. Compile and validate fingerprints, short briefs, and deterministic topology skeletons before generation.
9. Optionally create one independent PNG per blueprint outside the repository CLI, place each file inside the run's `generation/candidates` directory, and register its exact hash and call ID. Treat generator provenance as operator-attested, not independently verified.
10. Select or reject a registered macro-layout and palette at Gate 2 after image-level blocking review; stop repairing delivery details in raster.
11. Build `semantic_figure.json` and `equations.tex`, then run the independent delivery adapters; never trace or wrap the PNG.
12. Run cross-format validators plus final-size, grayscale, and formula-hidden checks, then obtain Gate 3 sign-off.

The three V3 gates remain human decisions. Automated lint and validators are checkpoints, not approvals. A `VERIFIED` cross-format report covers programmable structure only; it is not scientific validation, visual-quality approval, or publication readiness.

Example invocation:

```text
$sketch-to-scientific-figure

INTAKE_MODE: guided
Read the attached sketch and method materials first. Infer what is already
known, then ask exactly one highest-impact unresolved question per turn.
Recommend a default with each question. Discovery is not an approval gate.

PROPOSAL_MODE: directed-three
PROPOSAL_COUNT: 3
FIGURE_ROLE: main-paper; method figure at two-column publication scale
DETAIL_MODE: story-first

Synthesize a HIERARCHY_MAP, COMPLEXITY_BUDGET, ART_DIRECTION_BRIEF,
VISIBLE_TEXT_BUDGET, exact VISIBLE_PROSE_BUDGET, and separate
VISUAL EMBODIMENT BRIEF. Keep the main story in HERO/MAIN-BODY and move
safe verification detail to AUDIT-INSET or CAPTION.

At Gate 1, ask me to approve the paper-aware editorial story and one shown
wireframe. At Gate 2, ask me to select or reject a registered PNG macro-layout
and palette after reviewing it against the approved constraints. Reconstruct every delivery format from the canonical semantic and
LaTeX sources, then request Gate 3 sign-off only after executable validation.
```

For a complete prewritten brief, replace `guided` with `direct`. When three alternatives would help, use `directed-three` with count 3. For an explicitly approved five-way mixed exploration, use:

```text
PROPOSAL_MODE: exploratory-five
PROPOSAL_COUNT: 5
FIDELITY_MODE: controlled-mixed
Use a CANDIDATE EXPLORATION PROGRAM with exactly five roles:
1) method-first free narrative,
2) sketch-faithful spatial layout,
3–5) three different method-specific information-design emphases.
All five still obey every SCIENTIFIC LOCK and every `all-candidates`
SKETCH SEMANTIC LOCK. The sketch-faithful track additionally obeys every
`sketch-faithful-candidate` lock, and named-candidate locks apply only to
their exact named ids.

COLOR_MODE: per-candidate-exploration
PALETTE_STATUS: exploration-approved
Define a PALETTE_PROGRAM that gives the five candidates different
restrained paper-style fill systems
from their first generation. Do not generatively recolor accepted rasters.
At Gate 2, let me choose the layout candidate and palette candidate
independently, then combine them deterministically with SVG color tokens.
```

## Default figure policy

- `TITLE_POLICY: none` unless the user explicitly requests a title.
- `INTAKE_MODE: guided` asks one inferred, high-impact question per turn; `direct` synthesizes a complete supplied brief immediately. Neither path adds an approval gate.
- `PROPOSAL_MODE` and `PROPOSAL_COUNT` must match: `focused-one`/1, `directed-three`/3, or `exploratory-five`/5. `directed-three` is the normal comparison default.
- Main-paper work normally uses `DETAIL_MODE: story-first`. Its `HIERARCHY_MAP` uses `HERO + MAIN-BODY + AUDIT-INSET + CAPTION`; together with `COMPLEXITY_BUDGET` and `VISIBLE_TEXT_BUDGET`, this prevents audit detail, repeated notation, and connector wiring from flattening the primary story.
- Scientific truth comes from current equations and explicit method text. A scientifically valid glyph or spatial relation becomes binding only after it is recorded under `SKETCH SEMANTIC LOCKS`.
- `FIDELITY_MODE: sketch-bound` is the default when the sketch contains a deliberate pipeline, architecture glyph, stage arrangement, or spatial story. A request for polish or flexibility does not unlock those relations.
- `FIDELITY_MODE: controlled-mixed` is an `exploratory-five`-only option. Its `CANDIDATE EXPLORATION PROGRAM` assigns exactly five roles: one method-first narrative, one sketch-faithful layout, and three method-specific information-design emphases. “Free” means freedom in unlocked macro-organization, never freedom from in-scope scientific or sketch-semantic locks.
- `FLEXIBILITY ZONES` name the only layout, spacing, compression, scale, or presentation decisions that may vary. A locked cluster may move as one unit only when the contract permits it; its members may not be rearranged silently.
- A mean, centroid, or temporal-center representative is placed at the arithmetic mean of its displayed member-anchor positions, never at the center of a card, label column, or partial group.
- A researcher-specified connector style is recorded as a scoped `connector-routing` lock. For example, `orthogonal-only` means horizontal/vertical shafts with 90-degree elbows and no diagonal arrows.
- A contracted transition attaches directly to its declared source and target ports. It must remain directed, continuous, and prominent without relying on color.
- Structure, grouping, alignment, whitespace, and topology establish the primary hierarchy; color is a secondary semantic cue.
- `COLOR_MODE: neutral-structure` is the default when color adds no necessary scientific distinction or its role mapping remains unapproved.
- `PALETTE_STATUS` is `locked` only after the researcher approves the palette and its semantic role mapping in figure context; a swatch sheet alone is `provisional`.
- A locked palette uses 4–7 named working tokens plus the background. For a provisional palette, the active `PALETTE_TOKENS` are neutral structure-study tokens with no accent; any unapproved colored mapping appears only as `PALETTE_RATIONALE.provisional_candidate` until the existing selection/repair gate locks or replaces it.
- `COLOR_MODE: per-candidate-exploration` with `PALETTE_STATUS: exploration-approved` is also `exploratory-five`-only. Its `PALETTE_PROGRAM` assigns each proposal a distinct restrained fill system at first generation, with its own token set but invariant semantic-role vocabulary. This mode never authorizes a post-hoc generative recolor.
- When a locked colored mode uses an accent, one restrained signature use reinforces the ONE-SENTENCE MESSAGE. If `COLOR_NECESSITY` is none, remain neutral by default; a final locked palette selected from an explicit `per-candidate-exploration` may retain its approved editorial fills, but color cannot become the sole carrier of scientific meaning.
- Write 1, 3, or 5 macro-layout blueprints before rendering according to `PROPOSAL_MODE`. Each records reading direction, hierarchy, major regions, central relationship, repetition compression, visual anchors, text/complexity budgets, art direction, and deliberate omissions.
- Each blueprint also records how the approved scientific entities are visually embodied. Image-valued states use a recognizable anchor plus a separate notation label; they are not empty formula boxes by default.
- Diversity review applies only when count is greater than one. Use the machine-readable layout fingerprint; five named roles never substitute for fingerprint diversity.
- Duplicate proposals are regenerated before display. Color, typography, separators, or box styling alone never create meaningful diversity.
- Allow at most one regeneration per blueprint and one local style edit per candidate. Never repair count, index, stage order, grouping, source/target, fan-in/fan-out, centroid, equation, connector rewiring, or backward multiplicity in raster. Revise the blueprint/skeleton or reject instead.
- Asset preference is `native vector → licensed SVG → minimal generated or user-provided raster atom`. Raster use is an explicit exception, not the default rendering strategy.
- A generated visual atom is a schematic placeholder only. Its SVG group, variable label, border state, and connector geometry remain independent so the atom can be replaced without rebuilding the diagram.
- An asset manifest records each non-native asset's ID, role, source or generation status, license when applicable, placeholder status, and replacement target.
- Each proposal and the final SVG must pass a formula-hidden comprehension test: if full equations are temporarily hidden, the main object types and process should still be recognizable from visual anchors, short labels, and topology.
- `ART_DIRECTION_BRIEF` may open bounded visual choices, but it cannot change scientific truth, in-scope locks, or evidentiary status.
- `VISIBLE_TEXT_BUDGET` limits total labels, repeated notation, equations, and prose; `VISIBLE_PROSE_BUDGET` remains the exact ordinary-language allowlist.
- `VISIBLE_PROSE_BUDGET` is an exact allowlist. Any inferred heading, row caption, legend, or explanation absent from it is a pre-display rejection error.
- Explanations that are not required to decode the diagram belong in the manuscript caption.
- Do not use generative image editing merely to recolor a candidate that already passed image-level blocking and sketch-fidelity review. Apply color deterministically during semantic SVG reconstruction, or regenerate from the approved blueprint and repeat review.
- At Gate 2, layout and palette selections may come from different candidates. Transfer only the selected palette's approved semantic token mapping onto the selected layout through SVG classes or equivalent Figma styles; do not composite or repaint raster candidates, and keep the canonical SVG token map synchronized.
- The final SVG uses semantic color classes or design tokens and remains understandable when printed in grayscale. It may remain neutral when `COLOR_NECESSITY` is none.

Neutral structure-study tokens:

```text
background:       #FFFFFF
ink:              #252525
secondary-text:   #7C7C7C
structural-line:  #D9D9D6
soft-region-fill: #F2F1ED
primary-semantic: none
optional-secondary: none
```

Use these tokens for neutral structure studies when color has no necessary role or a colored mapping remains provisional. They are not a project identity. The former 70–85% neutral, 10–25% primary, and 5% secondary ranges are rough review diagnostics, not generation targets or pixel quotas.

## Repository contents

- `.agents/skills/sketch-to-scientific-figure/SKILL.md`: repository-scoped Skill entrypoint and execution order.
- `prompts/00_scientific_figure_brief.md`: runtime scientific-contract extraction.
- `prompts/00a_guided_interview.md`: one-question-at-a-time guided discovery, resumable interview state, and proposal-mode recommendation.
- `prompts/01_sketch_to_five_proposals.md`: proposal-mode-aware structure classification and independent layout studies.
- `prompts/01b_compare_and_repair.md`: scientific, communication, and visual-restraint review.
- `prompts/02_selected_proposal_to_svg.md`: semantic SVG reconstruction and validation.
- `prompts/templates/`: compiled image-generation, bounded style-edit, and semantic-SVG reconstruction templates.
- `schemas/`: machine-readable contracts for truth, blueprints, rules, reviews, candidate selection, and SVG reconstruction.
- `schemas/run_state.schema.json`: resumable V3 state and exactly-three-gate contract.
- `schemas/figure_editorial_review.schema.json`: source-linked editorial classifications and recommendations.
- `schemas/equation_manifest.schema.json`: stable equation IDs, authoritative LaTeX, and rendered-object provenance.
- `schemas/semantic_figure.schema.json`: canonical object/geometry/topology source for all adapters.
- `schemas/delivery_manifest.schema.json`: format-by-format paths, validation, and honest editability status.
- `scripts/`: compiler, skeleton renderer, artifact/SVG validators, V3 runner, equation renderer, independent export adapters, and cross-format validator.
- `rules/`: common and optional run-specific rule registries with stable IDs.
- `docs/architecture_v2.md`: canonical artifact flow and authority boundaries.
- `docs/architecture_v3.md`: paper-aware/editorial, canonical-source, equation, adapter, and state-machine architecture.
- `docs/autopilot_policy.md`: exactly-three-gate policy, compact decision packets, resume behavior, and delegated defaults.
- `docs/repair_policy.md`: image-level classifications and bounded raster-repair policy.
- `docs/regression_protocol.md`: honest old-vs-new comparison and verdict thresholds.
- `notes/visual_grammar.md`: generic sketch-aware, structure-first color and layout grammar.
- `notes/sketch_fidelity_and_spatial_locks.md`: binding glyph, derived-placement, transition, prose, fidelity-mode, and flexibility-zone rules.
- `notes/visual_grounding_and_assets.md`: visual-anchor, replaceable-image, provenance, and hybrid-SVG rules.
- `notes/github_workflow_inspiration.md`: audited GitHub inspiration and the practices deliberately not adopted.
- `notes/project_method.md`: separation among the generic core, hard scientific contract, visual embodiment brief, and examples.
- `notes/source_derived_principles.md`: design principles synthesized from the supplied readings.
- `examples/`: the frozen Deep Image Prior v0.1 reference case, its preserved decision history, and hash-bound delivery evidence. Examples are not default scientific authority and must not be loaded unless directly relevant.
- `references/`: source readings retained for provenance.

## Priority order

1. scientific correctness;
2. one clear message;
3. correct topology, grouping, and arrow semantics;
4. binding sketch glyphs, mathematical placement, and transition attachment;
5. recognizable scientific objects without false evidentiary claims;
6. readable hierarchy at intended paper size;
7. economy of marks and downstream editability.

This is a scientific information-editing workflow, not a graphical-abstract generator. Visual flexibility is permitted only inside the approved `FLEXIBILITY ZONES` and embodiment brief; it cannot override the scientific contract or any `SKETCH SEMANTIC LOCK` whose scope includes the current candidate.
