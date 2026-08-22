# Prompt 00: extract the runtime scientific contract

Use this before any layout or image generation. The output is specific to the user's current paper and must not inherit variables, stages, modalities, or panel structures from examples.

```text
You are a scientific figure editor. Convert the attached hand sketch and current scientific materials into an authoritative runtime scientific contract. Do not design or generate a figure yet. After Gate 1 approval, serialize the approved content as `scientific_truth.json` with stable IDs and source hashes; the full prose contract is not an image-generation prompt.

Current inputs may include:
- hand sketch;
- method description;
- authoritative equations;
- paper draft or excerpt;
- optional reference figure.

Source authority:
1. Authoritative equations and explicit method statements define scientific meaning.
2. The hand sketch does not override scientific meaning, but it is the source of intended visual topology, grouping, glyph identity, relative placement, and direction. Every scientifically valid feature recorded under SKETCH SEMANTIC LOCKS becomes binding visual authority.
3. An optional reference figure may inform a factual convention only when the user identifies it as authoritative. It is never a default style template.
4. If sources conflict, report the conflict. Do not silently choose or import a resolution from an example.

Priority:
1. Scientific correctness.
2. The one-sentence message.
3. Correct entities, topology, grouping, and arrow semantics.
4. Minimal visual complexity and visible prose.

Return exactly the following sections.

INTAKE_MODE
Choose exactly one:
- `direct`: the user supplied a sufficiently complete specification and only unresolved scientific or sketch-semantic conflicts require clarification;
- `guided`: an `INTERVIEW_STATE` and synthesized guided brief were produced with Prompt 00a.

If guided, preserve the decision value and provenance (`inferred`, `user-confirmed`, or `user-delegated`) from the interview. Do not reinterpret a discovery answer as Gate 1 approval.

FIGURE_ROLE
Choose the intended reading context: `main-paper`, `appendix-or-audit`, `slide-or-poster`, `graphical-abstract`, or another explicit role. Record target aspect ratio or column width when known. This controls hierarchy and density, not scientific truth.

PROPOSAL_MODE
Choose exactly one:
- `focused-one`: one best-fit synthesis; use when topology is fixed and only visual treatment is open;
- `directed-three`: three nonduplicate, purposefully contrasted proposals; this is the default when comparison is useful;
- `exploratory-five`: five declared narrative tracks for broad information-design or palette exploration.

PROPOSAL_COUNT
Write the matching integer: `1`, `3`, or `5`. `focused-one` must map to 1, `directed-three` to 3, and `exploratory-five` to 5. Proposal mode and `FIDELITY_MODE` are independent. `controlled-mixed` and `per-candidate-exploration` are five-track programs and therefore require `exploratory-five`.

DETAIL_MODE
Choose exactly one:
- `story-first`: prioritize the three-second method narrative and move exact repeated verification into a compact audit inset or caption when scientifically safe; recommended for a main-paper figure;
- `balanced`: keep the primary narrative dominant while showing moderate branch-level verification in the main body;
- `audit-complete`: display every required correspondence prominently, accepting the resulting density; normally reserved for appendix, audit, or explicit researcher request.

AUDIENCE
What background may be assumed?

ONE-SENTENCE MESSAGE
What should the reader understand after viewing the figure? Write one complete sentence.

VISUAL MESSAGE
What should a reader recognize from the objects and relationships within about three seconds, before reading any full equation? Write one concrete sentence. This is a perceptual target, not a new scientific claim.

HIERARCHY_MAP
Assign every required item to exactly one presentation layer:
- `HERO`: the relation or object family that must be noticed first and carries the VISUAL MESSAGE;
- `MAIN-BODY`: entities and flow needed to decode the method;
- `AUDIT-INSET`: exact indexed correspondence, repeated verification, or dense detail that must remain visible but subordinate;
- `CAPTION`: definitions, qualifications, provenance, and equations not needed for visual decoding.

Do not delete science when moving detail between layers. If an exact relation must remain individually visible, an indexed compact matrix, strip set, or audit inset may preserve it without making it the hero.

COMPLEXITY_BUDGET
Set explicit, reviewable limits for the intended output size:
- `hero_groups`: the maximum or exact number of visually dominant groups;
- `support_repetition`: the approved explicit, indexed-compact, exemplar, stack, or audit strategy for repeated support objects;
- `audit_regions`: the maximum or exact number of subordinate verification regions;
- `displayed_equations`: the maximum number of full equations on the canvas;
- `ordinary_prose`: the maximum number of ordinary phrases, consistent with VISIBLE_PROSE_BUDGET;
- `connector_policy`: factoring, routing, maximum long routes or elbows, and the intended-paper-size pass condition; this never overrides a connector-routing lock;
- `visual_anchor_families`: the maximum or exact number of coherent thumbnail/domain-glyph families.

ART_DIRECTION_BRIEF
Describe the visual character that should make this figure belong to the current method and publication context. Include composition character and whitespace policy; shape/glyph language; fill strategy and card policy; connector character; domain anchors; reference-derived traits that may be borrowed without copying a figure; and explicit anti-style constraints.

Do not reduce this section to generic words such as “clean” or “professional.” Do not ask the user for low-impact micro-decisions when the materials support a defensible synthesis.

SCIENTIFIC ENTITIES
What objects, variables, operators, states, measurements, or modules are necessary? For each, give:
- id;
- exact label or notation from the current inputs;
- scientific role;
- minimal visual role;
- conceptual region, branch, stage, or condition when applicable.

FUNCTIONAL RELATIONSHIPS
Which relationships are directed transformations, information flow, motion, sequence, or causality? Express each as:
source -> verb or operator -> target.
Do not list membership, annotation, or correspondence here.

STRUCTURAL ASSOCIATIONS
Which relationships express grouping, membership, correspondence, shared context, or annotation and therefore should not use arrowheads? State the preferred encoding: proximity, alignment, brace, enclosure, shared form, or plain leader line.

EQUATIONS
Which equations and notation are authoritative? Reproduce them exactly and state which entities or relationships they govern.

EQUATION ROLE
For every authoritative equation, assign one role:
- PRIMARY: the equation itself carries part of the ONE-SENTENCE MESSAGE and should appear as a separate typeset object;
- SUPPORTING: the visual story should remain understandable without it, while the equation provides exact definition or verification;
- CAPTION: scientifically relevant but not needed on the canvas.
Do not let a repeated formula substitute for a recognizable scientific object.

INFORMATION PROFILES
Record both profiles without changing scientific truth:
- `main_paper_story_first`: one dominant method story, only the repetition required for comprehension, and at most two displayed equation blocks;
- `appendix_audit_complete`: all authoritative equation groups and more explicit indices.

Do not require production equations in the PNG candidate. Equation display policy controls deterministic SVG reconstruction and caption/method placement.

CONCEPTUAL REGIONS
What panels or conceptual groups are scientifically necessary? Do not create panels merely to organize the page.

SKETCH INVARIANTS
Which topology, grouping, order, relative placement, and arrow directions from the sketch must be preserved? Identify any sketch element overridden by authoritative science.

FIDELITY_MODE
Choose exactly one:
- `sketch-bound`: default when the supplied sketch contains a deliberate pipeline, architecture glyph, stage arrangement, or spatial story. All candidates keep the locked macro-backbone and vary only inside approved flexibility zones.
- `topology-exploratory`: use only when the researcher explicitly requests broad rearrangement or confirms that the sketch's macro-layout is disposable. Every semantic lock whose scope includes a candidate remains binding for that candidate.
- `controlled-mixed`: use when the researcher explicitly requests a deliberately mixed set containing both method-first narrative exploration and a sketch-faithful spatial interpretation. Every `all-candidates` lock remains binding; `sketch-faithful-candidate` locks apply to the faithful track, and named-candidate locks apply exactly to their named tracks. A lock outside a candidate's scope is not relaxed; it is intentionally inapplicable there.

Do not infer `topology-exploratory` merely because the researcher requests flexibility, polish, or multiple candidates.

SKETCH SEMANTIC LOCKS
Record every scientifically valid hand-drawn feature whose replacement or movement would change the entity's visual identity, mathematical placement, relation, or priority. For each lock, give:
- lock_id;
- scope: `all-candidates`, `sketch-faithful-candidate`, or exact named candidate ids;
- source_region in the sketch;
- entity_or_relation from the contract;
- lock_type: `glyph-silhouette`, `glyph-ports`, `relative-placement`, `group-membership`, `group-centroid`, `stage-transition`, `connector-routing`, `salience-hierarchy`, or `reading-order`;
- must_preserve as an observable property;
- allowed_cleanup;
- forbidden_deviation;
- verification rule;
- scientific_override: `none` or the exact authoritative correction.

When a representative is scientifically defined as a mean, centroid, or temporal center, lock its displayed position to the mean of its member-anchor positions. On a straight path, compute the representative path coordinate from the members; do not center it using a surrounding card, column, label region, or partial group.

When the researcher specifies connector geometry, record it as a scoped `connector-routing` lock. For example, `orthogonal-only` means every arrow shaft and connector segment is horizontal or vertical and every turn is a 90-degree elbow; a triangular arrowhead may terminate such a segment, but no diagonal shaft is allowed.

FLEXIBILITY ZONES
List the layout, spacing, compression, scale, or presentation decisions that may change without violating SKETCH SEMANTIC LOCKS. Moving a locked cluster as one unit may be allowed; rearranging its members is not automatically allowed.

CANDIDATE EXPLORATION PROGRAM
Use this section only for `PROPOSAL_MODE: exploratory-five` with `FIDELITY_MODE: controlled-mixed`; otherwise write `not applicable`. Define exactly five candidate tracks before generation:
1. `method-first narrative discovery`: explore the clearest scientifically valid macro-story for the method;
2. `sketch-faithful spatial cleanup`: preserve the sketch's broader spatial composition as well as every universal lock;
3–5. three different declared information-design emphases chosen from the current method, such as temporal progression, constraint multiplicity, shared-versus-changing structure, comparison, or compact paper-size communication.

For each track, record: candidate id, exploration goal, narrative question, required lock scopes, allowed macro-layout freedom, and the decision that makes it non-duplicate.

PROPOSAL PROGRAM
Record one blueprint responsibility per approved proposal:
- for `focused-one`, one best-fit synthesis tied directly to HIERARCHY_MAP and ART_DIRECTION_BRIEF;
- for `directed-three`, three nonduplicate questions, normally `best-fit method narrative`, `sketch-faithful cleanup`, and `compact journal-size representation`, unless the interview approved a more relevant trio;
- for `exploratory-five`, reference the five-track CANDIDATE EXPLORATION PROGRAM or define five tracks compatible with the active fidelity mode.

For every proposal record: candidate id, narrative question, required lock scopes, hierarchy/detail allocation, allowed freedom, art-direction decision, and nonduplicate decision. A one-proposal program has no set-diversity requirement.

INVARIANT COMPONENTS
Which components remain the same across stages, branches, conditions, time points, scales, or comparisons?

VARYING COMPONENTS
Which components actually change, and along which dimension or condition?

FORBIDDEN IMPLICATIONS
What scientifically incorrect entities, pathways, targets, supervision signals, causal claims, correspondences, stages, or physical meanings must not be introduced?

SCIENTIFIC LOCKS
Summarize the facts that no layout or visual embodiment may change: required entities, counts or cardinalities, directed and structural relations, stage or panel order, shared versus varying components, exact notation, the scope of every approved SKETCH SEMANTIC LOCK, and the most important FORBIDDEN IMPLICATIONS. Derive this list only from the sections above; do not add facts.

VISUAL EMBODIMENT BRIEF
Map scientific entities to recognizable visual anchors while keeping SCIENTIFIC LOCKS immutable. Include every entity whose role would be clearer as an image, domain glyph, trace, strip, geometry, material object, or other visual representation. An image-valued state should not default to an empty frame or a math-only box when a recognizable thumbnail can clarify its role.

For each visual anchor, give:
- entity_id and exact_label;
- visual_class: `thumbnail`, `domain-glyph`, `schematic-shape`, `trace-or-strip`, `notation`, or `equation`;
- recognition_target: what the reader should identify without reading the label;
- preferred_asset_mode: `native-vector`, `licensed-svg`, `generated-placeholder`, or `user-provided`;
- invariant_content_anchor: what must remain visually consistent across repeated instances, stages, or candidates;
- allowed_stylization: what may vary without changing scientific meaning;
- forbidden_visual_implications: data, anatomy, averaging, causality, performance, diagnosis, scale, or other meanings the glyph must not suggest;
- label_and_frame_semantics: which variable labels, status borders, stage styles, or annotations must remain separate from the asset pixels;
- replaceable: true or false.

Every anchor must add decoding value. Do not add generic clip art merely to make the figure look richer. Visual flexibility may alter only approved embodiment details, abstraction, local composition, and restrained styling inside FLEXIBILITY ZONES; it may not alter SCIENTIFIC LOCKS or any SKETCH SEMANTIC LOCK whose scope includes the candidate. Every `all-candidates` lock always applies.

ASSET POLICY
Choose the least complex representation that preserves recognition, in this order:
1. native SVG primitives and editable text;
2. project-owned or licensed SVG with recorded source and license;
3. the smallest necessary user-provided or generated raster atom.

Return this schema:

ASSET_POLICY:
  mode: hybrid-vector-first
  generated_placeholders_allowed: <true only when the user approved them or explicitly requested illustrative generation; otherwise false>
  approved_non_native_assets:
    - asset_id: <stable id, or none>
      asset_family_id: <shared visual family id, or none>
      entity_id: <scientific entity>
      asset_mode: <licensed-svg | generated-placeholder | user-provided>
      source_or_generator: <path, URL, built-in image generation, or pending>
      license_or_ownership: <license, user-owned, project-generated placeholder, or pending>
      scientific_status: <non-evidentiary-schematic | measured-data | reported-result | other exact status>
      release_policy: <replace-before-publication | approved-schematic | approved-source-asset>
      privacy_status: <not-applicable | de-identified-user-confirmed | unverified>
      replaceable: true
      replacement_notes: <what may be swapped without changing labels, borders, arrows, or layout>
  raster_scope: minimal-atomic-only
  whole_figure_raster_forbidden: true
  provenance_manifest_required: <true when approved_non_native_assets is not empty; otherwise false>
  publication_disclosure: <caption or methods disclosure needed, or none>

Generated or generic medical imagery may be used only as a clearly schematic placeholder. It must use `release_policy: replace-before-publication` unless the researcher explicitly approves it as a retained schematic. It may denote the object class or role of a reconstructed state, but its pixels must not be presented as acquired data, ground truth, the method's actual reported reconstruction, quantitative evidence, or a clinical finding. Real medical imagery requires user-confirmed de-identification and provenance. Use `pending` only for unresolved source, license, or attribution fields; use `privacy_status: unverified` and an honest unresolved scientific status when those are unknown. Do not invent clearance.

OPEN AMBIGUITIES
List unresolved questions. Mark each as either:
- TOPOLOGY-CHANGING: the answer could change an entity, connection, direction, grouping, correspondence, stage, branch, or panel;
- SKETCH-SEMANTIC-CHANGING: the answer could change whether a deliberate glyph, port, mathematical position, transition route, or salience relation is locked;
- NON-TOPOLOGICAL: wording, spacing, typography, or another aesthetic detail.
Do not invent a resolution.

TITLE_POLICY
Default: none.
Use a title only when the user explicitly requests one. Panel identifiers are allowed only when CONCEPTUAL REGIONS requires genuine panels.

VISIBLE_PROSE_BUDGET
List every non-mathematical phrase allowed on the canvas. This is an exact allowlist, not a suggestion. Prefer short module names and essential panel labels. If none are required, write: none. Generic inferred row headings, category captions, legends, and explanatory phrases are forbidden unless their exact wording appears here. Any extra ordinary-language phrase in a rendered candidate is a pre-display rejection error rather than a repair deferred to SVG reconstruction.

VISIBLE_TEXT_BUDGET
Constrain all visible text, including mathematical labels and repetition that VISIBLE_PROSE_BUDGET does not count. Return:
- `ordinary_prose_allowlist`: the exact phrases copied into VISIBLE_PROSE_BUDGET;
- `stage_or_panel_labels`: every permitted short stage or panel label;
- `notation_labels`: every permitted mathematical symbol, recording whether indexed instances must appear individually or may use a shared header, range, matrix, or ellipsis;
- `displayed_equations`: every full equation allowed as a separate typeset object;
- `forbidden_inferred_text`: headings, legends, explanations, or duplicate labels that must not be invented.

An allowlisted phrase may still violate COMPLEXITY_BUDGET through repetition. Do not solve an overcrowded figure by shrinking every label.

COLOR_MODE
Choose one: `neutral-structure`, `subject-derived-restrained`, `researcher-specified`, or `per-candidate-exploration`.

Default to `neutral-structure` when color does not encode a necessary scientific distinction, the sketch is intentionally black and white, or the proposed role mapping has not been tested in figure context. A monochrome or near-monochrome paper figure is valid. Use `subject-derived-restrained` only when current materials provide a defensible semantic role for color. Use `researcher-specified` only when the researcher has approved the role mapping, not merely supplied a swatch sheet.

Use `per-candidate-exploration` only when the researcher explicitly requests five differently colored candidate settings and `PROPOSAL_MODE` is `exploratory-five`. Define five restrained filled palette directions before generation; keep the semantic role vocabulary invariant across candidates even when the hue families differ. Color remains a secondary cue after topology, grouping, alignment, whitespace, scale, and SKETCH SEMANTIC LOCKS. Do not choose colors from a domain stereotype or a fashionable default.

PALETTE_STATUS
Choose exactly one:
- `locked`: the researcher has approved the palette in the intended figure context and its semantic role mapping;
- `provisional`: the swatches or mapping remain an unapproved hypothesis. Layout candidates must use neutral structure-study styling, and palette approval joins the existing layout-selection gate before SVG reconstruction.
- `exploration-approved`: the researcher has approved comparing five declared filled palette directions, but has not selected the final palette. Each candidate uses its assigned tokens from first generation; the selected or hybrid palette becomes `locked` at the existing layout-selection/repair gate.

Supplying colors, a screenshot, or a palette sheet does not by itself make the mapping `locked`.

COLOR_NECESSITY
State which contracted distinction becomes faster or safer to decode because of color. If structure communicates every necessary distinction, write: `none; neutral structure is sufficient`.

PALETTE_RATIONALE
For a colored mode, explain why the palette belongs to the current figure. Identify its subject basis, semantic logic, publication context, one signature accent use tied to the ONE-SENTENCE MESSAGE, and one generic palette default deliberately avoided. If the same rationale would fit an unrelated method figure unchanged, revise it. For `neutral-structure`, explain why color would add no necessary distinction or remains premature.

PALETTE_TOKENS
Specify 4–7 named working color tokens plus the background as hexadecimal values. Tokens must describe reusable roles, not individual variables. Include only the tokens the figure needs. The default paper background is pure white. These are the active tokens used in layout studies: when PALETTE_STATUS is `provisional`, they must be neutral structure-study tokens with no active accent. Record any unapproved colored candidate under `provisional_candidate` instead of applying it.

When `COLOR_MODE` is `per-candidate-exploration`, provide five complete candidate token sets under `PALETTE_PROGRAM` instead of one shared active set. Any shared `PALETTE_TOKENS` remain inactive until Gate 2 locks the selected or hybrid palette. Every candidate set must include visible but restrained fills, neutral readable ink, and the same semantic role names. The five directions must differ materially in hue family or tonal strategy, not merely in saturation. Temporary versus final, grouping, direction, and other scientific distinctions must remain recoverable without color.

COLOR_ROLES
Describe roles rather than variable names. Examples may include observed versus inferred, fixed versus optimized, physical operator versus learned component, current stage versus shared context, or highlighted path versus supporting structure. These are examples only.

Return this schema:

COLOR_MODE: <neutral-structure | subject-derived-restrained | researcher-specified | per-candidate-exploration>
PALETTE_STATUS: <locked | provisional | exploration-approved>
COLOR_NECESSITY: <one contracted decoding role, or none; neutral structure is sufficient>
PALETTE_RATIONALE:
  subject_basis: <specific evidence from the current subject or supplied materials>
  semantic_logic: <why the colors fit the scientific roles>
  publication_context: <paper, slide, poster, or other stated medium>
  signature_accent_use: <one restrained emphasis tied to the primary scientific relationship, or none>
  avoided_generic_default: <a plausible but generic palette choice rejected for this figure>
  provisional_candidate: <unapproved swatches and proposed role mapping, or none>
PALETTE_TOKENS:
  background: "#FFFFFF"
  ink: <hex>
  secondary_text: <hex>
  structural_line: <hex>
  soft_region_fill: <hex or none>
  primary_semantic: <hex or none>
  primary_semantic_fill: <hex or none>
  optional_secondary: <hex or none>
COLOR_ROLES:
  primary_accent_role: <one scientific role mapped to primary_semantic, or none>
  optional_secondary_role: <second necessary role mapped to optional_secondary, or none>
  neutral_roles: <supporting roles mapped to ink, secondary_text, structural_line, or soft_region_fill>
COLOR_BUDGET:
  neutral_dominant: true
  primary_accent_families_max: 1
  secondary_accent_families_max: 1
  accent_used_selectively: true
PALETTE_PROGRAM:
  mode: <shared | per-candidate>
  filled_candidates_required: <true only for per-candidate-exploration; otherwise false>
  semantic_role_mapping_invariant: true
  candidate_palettes:
    - candidate_id: <1-5; omit this list for shared mode>
      direction: <distinct restrained color/tonal idea>
      rationale: <why this is useful to compare for the current figure>
      tokens: <complete 4-7 role-token set plus white background>
      filled_roles: <which regions or objects receive soft fill>

Use a secondary role only when two genuinely different semantic roles cannot be communicated clearly by structure alone. Do not assign colors to individual variable names. Do not treat percentage ranges as pixel quotas; the qualitative budget and scientific role mapping govern color use. Do not force a primary accent when `COLOR_NECESSITY` is none.

CAPTION_ONLY_CONTENT
Which explanations belong in the manuscript caption rather than on the canvas? Include method explanation, generalization notes, dataset or training details, long definitions, border-style explanations, tutorial instructions, and required schematic-placeholder or asset-provenance disclosure unless they are necessary to decode topology.

After producing the contract:
- If any OPEN AMBIGUITY is TOPOLOGY-CHANGING or SKETCH-SEMANTIC-CHANGING, stop and ask only the minimum targeted clarification questions needed to resolve it. Do not generate layout proposals.
- Under `INTAKE_MODE: direct`, do not ask about low-impact decoration when ambiguities are only NON-TOPOLOGICAL. Under `INTAKE_MODE: guided`, Prompt 00a may ask one unresolved high-impact visual decision when it would change the primary narrative, information hierarchy, visual embodiment, publication-scale readability, or proposal strategy. Do not ask about font choice, corner radius, exact spacing, or hexadecimal color unless the researcher made it a decision.
- When the contract is complete, present the entire synthesized scientific and visual contract as Gate 1. Do not generate proposals before the researcher approves this snapshot.
- After Gate 1, compile the approved snapshot into `scientific_truth.json`, `candidate_blueprint.json`, short generation briefs, SVG reconstruction specs, and validation rule references. Use stable IDs and SHA-256 source hashes. Never interpolate this full contract directly into image generation.
- Treat generated-placeholder permission, unresolved asset ownership, and privacy status as asset-policy decisions. They do not change topology, but an unapproved or unverified asset may not be promoted to publication-ready evidence.
```
