# V3 autopilot policy

The workflow runs in `autopilot_with_gates` mode. It performs deterministic, reversible work automatically and stops only at three named human decisions.

## Exactly three gates

1. **Gate 1 — Editorial story and wireframe.** The researcher chooses the scientific story and spatial plan after seeing paper-linked editorial evidence, a sketch redline, and one or two wireframes.
2. **Gate 2 — PNG visual direction.** After Gate 1 approval, the researcher selects or rejects the generated bitmap direction. No semantic delivery is built from an unapproved candidate.
3. **Gate 3 — Final scientific delivery.** The researcher approves the validated cross-format package.

No other normal step asks a question. Ambiguity that could change scientific truth is attached to the next defined gate; if production cannot safely proceed, it is classified as `ambiguity-blocks-production` at Gate 1.

For a sketch-led run, Gate 1 is initialized only after an approved Visual Plan binding is supplied. `visual_plan.json`, the approved wireframe SVG, and its approved PNG preview are snapshotted into the run. The exact approved wireframe remains one Gate 1 option. Paper-aware content may appear only in a separately identified overlay group whose removal restores the approved SVG; it cannot create a parallel card-based or generic wireframe.

## Delegated defaults

The workflow may choose deterministic filenames, standard canvas sizes, non-semantic spacing, preview layout, metadata wording, and platform-safe font fallbacks. It may not delegate scientific claims, equation meaning, topology, story selection, PNG candidate selection, or final acceptance.

Every gate uses a compact decision packet with at most three questions, at most three options per question, one explicit recommendation, and one resume command. The packet must state which low-impact defaults were delegated.

## Resume and exactly-once behavior

`run_state.json` is the authority for continuation. Re-running without `--resume` against an existing state is rejected. `execution_count` is fixed to `1`; a resume appends an event without incrementing that count. Each artifact is registered only after it exists and its hash can be computed.

## Failure boundaries

- No Image API or API key is used.
- The built-in image-generation tool remains the only PNG-generation route, and only after Gate 1 approval.
- A PNG never becomes the canonical editable source.
- No adapter may be labeled editable without format-specific structural evidence.
- Missing external connectors produce an honest unverified or blocked status, not a fabricated success.
