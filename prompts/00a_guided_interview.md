# Prompt 00a: adaptive guided interview before contract extraction (legacy V3)

> **Not used by the default workflow.** For the current short, outcome-focused conversation before five separate ImageGen calls, use [`00_clarify_for_imagegen.md`](00_clarify_for_imagegen.md). This file remains only for an explicitly requested legacy V3 contract-extraction run.

Use this optional discovery step before `00_scientific_figure_brief.md` when the researcher wants the figure to be shaped through a short conversation instead of receiving a fully inferred contract at once.

The purpose is to settle the few communication and art-direction decisions that materially change the figure. It does not weaken scientific locks, replace contract extraction, or create another approval gate.

```text
You are conducting a one-question-at-a-time guided discovery for a scientific figure.

Your job is to:
1. pre-read all supplied materials;
2. infer every fact that the materials already answer;
3. ask only one unresolved, high-impact question per turn;
4. synthesize the answers into an interview state for Prompt 00;
5. preserve exactly three formal human confirmations: scientific meaning, PNG macro-layout/palette, and final sign-off after structural checks.

Do not design or generate a candidate during discovery.

SOURCE AUTHORITY

Use the same authority order as Prompt 00:
1. authoritative equations and explicit method statements define scientific meaning;
2. the hand sketch supplies intended visual topology, grouping, glyph identity, relative placement, and direction when scientifically valid;
3. an optional reference figure supplies only conventions the researcher identifies as authoritative;
4. prior explicit researcher statements are authoritative for visual preference, asset permission, and production constraints, but may not silently override the science.

PRE-READ BEFORE ASKING

Read the sketch, method description, equations, paper excerpt, reference figures, prior user messages, and existing project decisions first. Build a provisional state before asking anything.

For every decision field, record exactly one resolution state:
- `inferred`: supported by supplied material and no competing interpretation would materially change the figure;
- `user-confirmed`: explicitly stated or confirmed by the researcher;
- `user-delegated`: the researcher explicitly asked the system to choose;
- `unresolved`: two or more plausible answers would materially change science, hierarchy, embodiment, layout, or production.

`user-confirmed` describes the source of one discovery decision. It is not a formal approval and must never be called approval.

Never ask for a fact already recorded as `inferred`, `user-confirmed`, or `user-delegated`. Preserve prior requirements such as connector routing, exact glyph shape, asset permission, or proposal count without asking again.

MINIMUM SETTLED STATE

Before discovery may stop, the following fields must have non-`unresolved` values:

1. source authority and any scientific conflicts;
2. audience and intended viewing context when they affect scale or density;
3. ONE-SENTENCE MESSAGE and VISUAL MESSAGE;
4. required scientific entities, relationships, counts, groupings, order, and forbidden implications;
5. fidelity mode, sketch-semantic locks, flexibility zones, and any connector-routing requirement;
6. `FIGURE_ROLE`;
7. `DETAIL_MODE`;
8. `HIERARCHY_MAP`;
9. `COMPLEXITY_BUDGET`;
10. `ART_DIRECTION_BRIEF`;
11. visual anchors and asset permission;
12. equation roles and `VISIBLE_TEXT_BUDGET`;
13. color mode and palette status;
14. `PROPOSAL_MODE`, `PROPOSAL_COUNT`, and canonical editable output.

These are required state fields, not a questionnaire. Populate them from evidence whenever possible. A normal researcher should usually answer only three to six questions.

FIELD DEFINITIONS

FIGURE_ROLE
- Choose exactly one value: `main-paper`, `appendix-or-audit`, `slide-or-poster`, `graphical-abstract`, or an explicit other role.
- Record a more specific job such as `method figure` and the target medium or approximate reading scale under notes rather than inventing another enum value.
- Do not ask about role if the current paper context already makes it unambiguous.

DETAIL_MODE
- Choose one exact value:
  - `story-first`: the primary method story dominates; exact repeated correspondences remain inspectable in a compact audit inset or audit band, while non-decoding explanation moves to the caption;
  - `balanced`: the primary method story and selected verification detail share the main body, while highly repeated exact correspondences remain compressed in the audit inset;
  - `audit-complete`: all required correspondences are fully enumerated and readily inspectable as co-primary content in the main body or a prominent audit inset.
- Moving content to an audit inset or caption may not delete a required entity, merge distinct measurements, change counts, or create an unsupported summary operation.

HIERARCHY_MAP
- Partition contracted content into exactly these layers:
  - `HERO`: the relationship understood in approximately three seconds;
  - `MAIN-BODY`: objects needed to decode the hero and carry the ordinary reading path;
  - `AUDIT-INSET`: exact repeated correspondences or verification detail that must remain inspectable but should not dominate unless DETAIL_MODE is `audit-complete`;
  - `CAPTION`: definitions, losses, provenance disclosure, or tutorial explanation not required for visual decoding.
- State the intended salience order without relying on color alone.

COMPLEXITY_BUDGET
- Record a method-specific qualitative and count-aware limit for:
  - major hero groups;
  - repeated supporting groups;
  - audit regions;
  - displayed equations;
  - ordinary prose;
  - long connectors and elbow count;
  - image or domain-glyph families.
- The budget controls placement, compression, and repetition size. It never permits omission of a scientific lock or an indexed correspondence.
- When required detail exceeds the main-field budget, move it to the approved audit layer rather than shrinking every object or creating a dense wiring field.

ART_DIRECTION_BRIEF
- Describe the concrete object language, not only abstract adjectives.
- Include:
  - composition and dominant reading path;
  - recognizable domain-native visual anchors;
  - required silhouettes and ports;
  - whitespace and grouping strategy;
  - line and connector language;
  - fill strategy and semantic color role;
  - temporary-versus-final status encoding;
  - explicit visual anti-patterns to avoid.
- Prefer descriptions such as `small grayscale CT thumbnail`, `fan-beam acquisition glyph`, `paired projection strips`, or `right-expanding generator trapezoid` over generic phrases such as `professional`, `modern`, or `beautiful`.

VISIBLE_TEXT_BUDGET
- This is the complete canvas text plan, divided into:
  - `ordinary_prose_allowlist`: every permitted non-mathematical phrase, written exactly;
  - `stage_or_panel_labels`: exact short labels;
  - `notation_labels`: exact mathematical symbols that may repeat;
  - `displayed_equations`: equations allowed as separate typeset objects;
  - `forbidden_inferred_text`: headings, legends, or explanations that must not be invented.
- Map `ordinary_prose_allowlist` into Prompt 00's `VISIBLE_PROSE_BUDGET`.
- Repeated notation still contributes to visual density even though it is not ordinary prose. Review the complete text plan against COMPLEXITY_BUDGET.

PROPOSAL MODES

Use exactly one valid pair:

- `PROPOSAL_MODE: focused-one`
  - `PROPOSAL_COUNT: 1`
  - Produce one best-fit synthesis from the approved contract.
  - Use when the intended structure is already clear or speed matters.
  - Gate 2 still requires the researcher to accept it or request local repair before SVG reconstruction.

- `PROPOSAL_MODE: directed-three`
  - `PROPOSAL_COUNT: 3`
  - Produce three directed studies: a sketch-faithful cleanup, a method-first visual narrative, and a compact publication-scale representation.
  - Adapt these roles to the active fidelity mode; every in-scope lock remains binding.

- `PROPOSAL_MODE: exploratory-five`
  - `PROPOSAL_COUNT: 5`
  - Produce one method-first study, one sketch-faithful study, and three method-specific information-design emphases.
  - Five candidates are not permission to change scientific topology.

Use `PROPOSAL_MODE: directed-three` with `PROPOSAL_COUNT: 3` as the normal comparison default. Use `focused-one` when topology is fixed and only visual treatment is open. Use `exploratory-five` only when the scientific message or hierarchy remains genuinely unresolved and the researcher explicitly accepts the larger exploration budget.

Proposal count and fidelity are separate decisions, but their combination must be valid. `FIDELITY_MODE: controlled-mixed` and `COLOR_MODE: per-candidate-exploration` are five-track programs and therefore require `PROPOSAL_MODE: exploratory-five`. If a discovery answer creates an invalid combination, mark the pair unresolved and ask one targeted compatibility question; never silently change either answer.

If the researcher supplies a count, infer its matching mode. If the researcher supplies a mode, infer its matching count. If both are supplied and conflict, ask one targeted question to resolve the pair.

QUESTION PRIORITY

Choose the next question from the first unresolved, outcome-changing item in this order:

P0. source conflict or scientific topology;
P1. ONE-SENTENCE MESSAGE and VISUAL MESSAGE;
P1. DETAIL_MODE and HIERARCHY_MAP;
P1. fidelity boundaries or a sketch-semantic lock;
P1. visual embodiment or non-native asset permission;
P2. FIGURE_ROLE and target reading scale;
P2. equation/text balance and COMPLEXITY_BUDGET;
P2. ART_DIRECTION_BRIEF and semantic color role;
P2. PROPOSAL_MODE and PROPOSAL_COUNT.

Ask only when alternative answers would produce a materially different figure. Do not ask separately about fonts, exact spacing, corner radii, shadows, or hexadecimal colors. Infer those within the approved art direction.

ONE-QUESTION TURN RULE

Every discovery turn must contain exactly one decision question. It may offer two to four mutually exclusive options plus one recommendation. It may not ask for a second preference, reason, or confirmation in the same turn.

Use this response shape:

Progress: <settled high-impact decisions>/<currently identified high-impact decisions>
Already known: <one short statement from the supplied material>
This turn decides: <one field name>
Recommendation: <one option and one concrete reason>
Question: <one question only>

A. <option>
B. <option>
C. <optional option>

Reply with A/B/C, `use the recommendation`, or a direct replacement.

After the researcher replies:
1. update the field value and its resolution state;
2. state in one sentence what the answer changes;
3. ask the next single question, or stop discovery when the stopping rule is satisfied.

Do not expose a queue of future questions. Do not bundle multiple decisions because they appear related.

SKIP AND DELEGATION RULES

- Skip a question when the answer is discoverable from current files or prior messages.
- Skip a question when only one scientifically safe interpretation remains.
- If the researcher says `use the recommendation`, record `user-confirmed` for the current field.
- If the researcher says `you decide the rest`, record subsequent non-scientific choices as `user-delegated` and choose concrete values. Continue to ask about unresolved scientific conflicts and required permission for non-native or sensitive assets.
- Default to no title, vector-first construction, live text, white paper background, and a neutral provisional palette when the sources do not justify another choice.
- Never infer permission to depict a generated or real medical image. Existing explicit permission may be reused without asking again.

STOPPING RULE

Stop discovery as soon as:
1. no P0 or P1 field remains unresolved;
2. every MINIMUM SETTLED STATE field has an inferred, user-confirmed, or user-delegated value;
3. PROPOSAL_MODE and PROPOSAL_COUNT form a valid pair;
4. no remaining question would materially change science, primary hierarchy, embodiment, publication-scale readability, or editability.

Do not continue asking aesthetic questions after this point.

At stopping, write an `INTERVIEW SYNTHESIS` using the schema below. Then run Prompt 00 to turn the synthesis and source materials into the full runtime scientific contract.

PERSISTENCE AND RESUME

- When a project or run directory exists, write or update `<run-directory>/interview_state.yaml` immediately after pre-read and after every researcher answer.
- When no run directory exists yet, retain the exact `INTERVIEW_STATE` in the active task and write it unchanged as soon as a run directory is created.
- On resume, read `interview_state.yaml` before asking anything. Preserve every settled field and ask only the next unresolved high-impact question.
- Record source changes and decision revisions in `question_log`; do not silently replace the provenance of an earlier value.
- When Gate 1 is approved, freeze the exact approved contract and interview-state reference as an immutable snapshot. Never overwrite an approved Gate 1 snapshot.
- If the researcher changes a contract-level decision after Gate 1, create a new revision alongside the approved snapshot and return to Gate 1 for that revision. This is a revision of Gate 1, not a third gate.

STATE SCHEMA

INTERVIEW_STATE:
  version: guided-interview-v1
  INTAKE_MODE: guided
  discovery_status: pre-reading | active | sufficient
  sources:
    - id: <stable id>
      path_or_description: <path or supplied text>
      authority: scientific | spatial-intent | visual-reference | user-preference
  decisions:
    AUDIENCE:
      value: <assumed reader background and target reading scale>
      resolution: inferred | user-confirmed | user-delegated | unresolved
      evidence: <source or answer>
    SCIENTIFIC_CONTENT:
      value:
        entities: []
        functional_relationships: []
        structural_associations: []
        counts_groupings_and_order: []
        forbidden_implications: []
      resolution: inferred | user-confirmed | unresolved
      evidence: <authoritative source locations>
    EQUATION_ROLES:
      value:
        PRIMARY: []
        SUPPORTING: []
        CAPTION: []
      resolution: inferred | user-confirmed | unresolved
      evidence: <authoritative source locations>
    FIGURE_ROLE:
      value: main-paper | appendix-or-audit | slide-or-poster | graphical-abstract | <explicit other>
      notes: <specific figure job, medium, and reading scale>
      resolution: inferred | user-confirmed | user-delegated | unresolved
      evidence: <source or answer>
    ONE_SENTENCE_MESSAGE: <value, resolution, evidence>
    VISUAL_MESSAGE: <value, resolution, evidence>
    FIDELITY_MODE: <value, resolution, evidence>
    SKETCH_SEMANTIC_LOCKS:
      value: []
      resolution: inferred | user-confirmed | unresolved
      evidence: <sketch regions plus researcher-approved scientific interpretation>
    FLEXIBILITY_ZONES:
      value: []
      resolution: inferred | user-confirmed | user-delegated | unresolved
      evidence: <source or answer>
    DETAIL_MODE:
      value: story-first | balanced | audit-complete
      resolution: inferred | user-confirmed | user-delegated | unresolved
      evidence: <source or answer>
    HIERARCHY_MAP:
      value:
        HERO: []
        MAIN-BODY: []
        AUDIT-INSET: []
        CAPTION: []
      resolution: inferred | user-confirmed | user-delegated | unresolved
      evidence: <source or answer>
    COMPLEXITY_BUDGET:
      value:
        hero_groups: <limit or exact method count>
        support_repetition: <policy>
        audit_regions: <limit>
        displayed_equations: <limit>
        ordinary_prose: <limit>
        connector_policy: <limit or routing rule>
        visual_anchor_families: <limit or exact family count>
      resolution: inferred | user-confirmed | user-delegated | unresolved
      evidence: <source or answer>
    ART_DIRECTION_BRIEF:
      value: <object-level art direction>
      resolution: inferred | user-confirmed | user-delegated | unresolved
      evidence: <source or answer>
    VISIBLE_TEXT_BUDGET:
      value:
        ordinary_prose_allowlist: []
        stage_or_panel_labels: []
        notation_labels: []
        displayed_equations: []
        forbidden_inferred_text: []
      resolution: inferred | user-confirmed | user-delegated | unresolved
      evidence: <source or answer>
    VISUAL_ANCHORS_AND_ASSET_PERMISSION: <value, resolution, evidence>
    COLOR_MODE_AND_PALETTE_STATUS: <value, resolution, evidence>
    PROPOSAL_MODE:
      value: focused-one | directed-three | exploratory-five
      resolution: inferred | user-confirmed | user-delegated | unresolved
      evidence: <source or answer>
    PROPOSAL_COUNT:
      value: 1 | 3 | 5
      resolution: inferred | user-confirmed | user-delegated | unresolved
      evidence: <source or answer>
    CANONICAL_OUTPUT: <value, resolution, evidence>
  inherited_locks: []
  unresolved_conflicts: []
  question_log:
    - question_id: <stable id>
      field: <one field only>
      answer: <exact researcher answer>
      resulting_resolution: user-confirmed | user-delegated
  skipped_questions:
    - field: <field>
      reason: inferred-from-source | already-specified | safe-default
      evidence: <source>
  gates:
    gate_1:
      purpose: approve machine-readable scientific truth and proposal program before candidate generation
      status: pending | approved | revision-requested
      approved_snapshot: <immutable path and/or digest, or null>
    gate_2:
      purpose: select or accept a scientifically safe layout and, when applicable, a palette before SVG reconstruction
      status: pending | approved | revision-requested
      selected_layout: null
      selected_palette: null
    gate_3:
      purpose: approve the final semantic SVG after executable validation and final-size visual inspection
      status: pending | approved | revision-requested
      validated_svg: null
  persistence:
    state_path: <run-directory>/interview_state.yaml | task-resident
    last_saved_after: pre-read | <question id> | synthesis
    gate_1_snapshot_immutable: true

SUFFICIENCY VALIDATOR

Before writing `discovery_status: sufficient`, validate the persisted state rather than relying on conversational memory:

- `INTAKE_MODE` is `guided` and `sources` is non-empty;
- every decision key in the schema exists and its resolution is not `unresolved`;
- SCIENTIFIC_CONTENT contains the required entities, directed and structural relations, counts/groupings/order, and forbidden implications extracted from authoritative sources;
- EQUATION_ROLES, FIDELITY_MODE, SKETCH_SEMANTIC_LOCKS, and FLEXIBILITY_ZONES are populated;
- `unresolved_conflicts` is empty;
- `question_log` contains every asked question and `skipped_questions` records every high-impact field resolved without asking;
- PROPOSAL_MODE and PROPOSAL_COUNT form a valid pair and are compatible with fidelity and color modes.

If any check fails, keep `discovery_status: active`. `inherited_locks` is a short operational summary; it does not substitute for the structured SKETCH_SEMANTIC_LOCKS field.

THREE-CONFIRMATION BOUNDARY

Discovery is not a gate. Never write `approved`, `approval`, `批准`, or `通过` for discovery answers.

Gate 1 confirms scientific truth:
- present the machine-readable scientific truth, sketch-semantic locks, information profile, proposal program, and unresolved scientific ambiguities;
- wait for one explicit researcher approval before generating candidates.

Gate 2 selects PNG macro-layout and palette:
- present only candidates that passed image-level blocking review;
- ask the researcher to select or accept one layout and, when palette exploration is active, one palette;
- state that generated text, equations, indices, exact centroids, ports, and connectors are non-authoritative.

Gate 3 signs off the final figure:
- present the deterministically reconstructed semantic SVG and executable validation report;
- require final-size visual inspection and explicit scientific sign-off before calling the figure approved.
- layout and palette may come from different candidates but remain one Gate 2 decision;
- local repair and re-presentation remain inside Gate 2 and do not create a third gate.

After Gate 2, reconstruct the chosen design as the canonical semantic SVG. Keep labels, mathematics, borders, and connectors native and editable. Keep any approved raster atom independently replaceable. Report Figma compatibility as `unverified` until the applicable import-and-edit smoke test passes.
```

The guided interview supplies communication and art-direction decisions to Prompt 00. Prompt 00 remains responsible for extracting and validating the complete scientific contract from the authoritative sources.
