# V3 autopilot policy (legacy adapter)

> **Scope:** this policy applies only to the retained V3 contract-driven runner. It does not govern the default ImageGen-first workflow described in the [README](../README.md). Default users clarify ambiguity conversationally, receive exactly five active candidates from separate calls, and approve a visual direction before editable reconstruction; they do not complete the V3 Gate 1 wireframe process.

The workflow runs in `autopilot_with_gates` mode. It performs deterministic, reversible work automatically and stops only at three named human decisions.

## Exactly three gates

1. **Gate 1 — Editorial story and wireframe.** The researcher chooses the scientific story and spatial plan after seeing paper-linked editorial evidence, a sketch redline, and one or two wireframes.
2. **Gate 2 — Registered PNG visual direction.** After Gate 1 approval, the researcher selects or rejects a registered bitmap direction. No semantic delivery is built from an unapproved candidate.
3. **Gate 3 — Final scientific delivery.** After reviewing the structurally checked cross-format package, the researcher decides scientific acceptability.

No other normal step asks a question. Ambiguity that could change scientific truth is attached to the next defined gate; if production cannot safely proceed, it is classified as `ambiguity-blocks-production` at Gate 1.

For a sketch-led run, Gate 1 is initialized only after an approved Visual Plan binding is supplied. `visual_plan.json`, the approved wireframe SVG, and its approved PNG preview are snapshotted into the run. The exact approved wireframe remains one Gate 1 option. Paper-aware content may appear only in a separately identified overlay group whose removal restores the approved SVG; it cannot create a parallel card-based or generic wireframe.

## Delegated defaults

The workflow may choose deterministic filenames, standard canvas sizes, non-semantic spacing, preview layout, metadata wording, and platform-safe font fallbacks. It may not delegate scientific claims, equation meaning, topology, story selection, PNG candidate selection, or final acceptance.

Every gate uses a compact decision packet with at most three questions, at most three options per question, one explicit recommendation, and one resume command. The packet must state which low-impact defaults were delegated.

## Resume and exactly-once behavior

`run_state.json` is the authority for continuation. Re-running without `--resume` against an existing state is rejected. `execution_count` is fixed to `1`; a resume appends an event without incrementing that count. Each artifact is registered only after it exists and its hash can be computed.

## Failure boundaries

- No Image API or API key is used.
- The repository does not invoke or independently verify a PNG generator. It accepts only explicitly registered in-run candidates with exact hashes, operator-supplied call IDs, and Gate 1 bindings; provenance remains operator-attested and not independently verified.
- A PNG never becomes the canonical editable source.
- No adapter may be labeled editable without format-specific structural evidence.
- Missing external connectors produce an honest unverified or blocked status, not a fabricated success.

The publication-safe synthetic replay does not simulate live human decisions. Its checked-in Gate 1/2 fixture records are deterministic pre-approvals with `in_run_human_action: false` and `scientific_validation: false`; only a successful full replay can reach Gate 3, where it waits for a separate explicit researcher/operator action.
