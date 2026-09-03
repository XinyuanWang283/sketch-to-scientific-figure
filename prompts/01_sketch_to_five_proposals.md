# Prompt 01: sketch to five ImageGen candidates from separate calls

Use this prompt after focused conversational clarification is complete and a short natural-language rendering brief has been shown to the researcher. A machine-readable `scientific_truth.json`, deterministic topology skeleton, approved wireframe, and pre-generation approval gate are not required for this default path.

## Shared inputs

Use the same inputs for all five candidates:

1. the original hand-drawn sketch;
2. the complete prior conversation relevant to the figure;
3. the short clarified rendering brief;
4. one direction-specific suffix from A–E below.

The clarified brief must identify:

- the intended scientific story and reading direction;
- exact visible labels, symbols, and equations that must remain unchanged;
- confirmed nodes, arrows, feedback loops, comparisons, grouping, branching, and ordering;
- the intended image content for ambiguous state or result panels;
- the target medium and aspect ratio;
- forbidden implications and any sensitive or unpublished boundaries.

Treat these items as invariants across all five candidates. Candidate diversity may change composition, hierarchy, color, local graphical language, and presentation emphasis. It may not change scientific relationships, equations, labels, direction, grouping, or meaning.

## Generate five separate originals

Make exactly five separate calls to the Codex App built-in ImageGen capability. Use one call per slot and save five original outputs before making any comparison view.

For each call, create a mandatory repository-local `generation_event_id`. Record a native tool-call ID only if the tool exposes one; never invent it. Do not claim statistical independence. The initial active proposal set contains exactly A–E. If one slot is regenerated, append a new event that supersedes that slot's earlier event and preserve the earlier record.

Do not:

- call the OpenAI Image API;
- request or read an API key;
- use a repository script or CLI as an ImageGen fallback;
- generate all five candidates in one contact-sheet call;
- pass candidate A, B, C, D, or E as a reference for another slot;
- silently produce fewer than five candidates.

When the environment exposes no machine-verifiable generator metadata, record provenance honestly as an operator-attested Codex ImageGen output. Do not invent model versions, seeds, or API records.

### A — Faithful

Add this suffix to the shared brief:

> Preserve the hand-drawn sketch's recognizable macro-layout, object order, arrow routing, feedback placement, and visual grammar. Polish spacing, alignment, line quality, typography, and restrained color without redesigning the scientific composition.

### B — Publication

Add this suffix to the shared brief:

> Create a restrained, compact paper-figure direction with strong grayscale readability, economical marks, disciplined whitespace, and minimal decoration. Preserve every confirmed scientific invariant exactly.

### C — Presentation

Add this suffix to the shared brief:

> Create a presentation-ready direction with clearer distance legibility, stronger hierarchy, and a memorable focal relationship. Keep the scientific content precise and avoid decorative complexity that competes with the mechanism.

### D — Alternative layout

Add this suffix to the shared brief:

> Reorganize the macro-layout into a credible alternative composition while preserving the exact confirmed nodes, labels, equations, directions, feedback, comparisons, grouping, and causal or process meaning. Do not add or remove scientific relationships.

### E — Visual variant

Add this suffix to the shared brief:

> Preserve the confirmed scientific content and topology while exploring a distinct but professional palette, glyph vocabulary, stroke character, and whitespace rhythm. The visual language should be clearly different from A–D without becoming ornamental or misleading.

## Quality screen and slot regeneration

Inspect each original before presenting it. A candidate fails materially when it has any of these problems:

1. a required stage, object, comparison, branch, or feedback relation is absent;
2. an arrow, causal relation, or process direction is reversed or invented;
3. a required label or equation is missing, unreadable, or meaningfully changed;
4. the depicted state or result content contradicts the clarified brief;
5. it introduces a forbidden implication, unsupported result, measurement, or scientific claim;
6. it is visibly corrupted, clipped, illegible, or unusable at the intended aspect ratio;
7. its designated A–E direction is not meaningfully represented.

Regenerate only the failed slot, again from the original sketch, shared brief, and that slot's suffix. Never repair topology by editing another candidate or using a prior candidate as reference. Repeat until the user can be shown exactly five materially valid originals. Minor kerning, micro-alignment, and object-level details that can be rebuilt unambiguously as native objects may be noted for reconstruction, but must not conceal a scientific error.

## Present choices and preserve explicit approval

Show all five separate originals labeled A–E outside the generated image content. A comparison sheet may be assembled locally only after all five originals exist; it is a convenience view, not a sixth ImageGen output.

Accept natural-language decisions such as:

- `Choose C.`
- `Revise C: emphasize the feedback loop.`
- `Use C's layout with A's color direction.`
- `Regenerate all five.`

`Choose C` may approve the registered Candidate C directly. A revision or combination request is different: render it as a new candidate in a new append-only proposal run, show that exact image, and obtain explicit approval of its file hash before reconstruction. Do not treat an instruction such as “use C's layout with A's colors” as an approved composite that has no rendered candidate file. Selection is not approval while requested changes remain pending.

The approved candidate supplies visual direction only. Exact mathematics, text, and topology continue to come from the original sketch plus the researcher's clarification.
