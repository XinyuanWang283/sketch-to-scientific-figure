# Science Day demo: sketch, five choices, editable reconstruction

This 3–5 minute runbook presents the current product story:

> hand-drawn sketch → focused clarification → five separate Codex ImageGen calls → researcher choice → approved region map → editable reconstruction → structural checks → separate researcher decisions

Use the deterministic offline frozen replay as the primary stage path. It reuses the recorded A–E outputs and does not rerun ImageGen. A fresh live Codex branch is optional and explicitly non-deterministic; stop it at selection unless the researcher approves one exact direction.

The demo does not claim a measured time saving, benchmark result, scientific validation, production readiness, or a human user study. The five image candidates are visual proposals. The researcher remains responsible for scientific meaning and final acceptance.

## Current evidence boundary

The public Deep Image Prior example reaches the editable-delivery review point. Its canonical v0.1 pointer is [`editable_delivery_c_fidelity_v2/`](../examples/deep_image_prior/editable_delivery_c_fidelity_v2/README.md), and the workflow/case boundary is documented in the [v0.1 reference case](../examples/deep_image_prior/reference_case_v0_1.md). It contains the original sketch, clarification record, five separate operator-attested built-in ImageGen outputs, hashes, a locally assembled comparison sheet, preserved decision history, an approved eight-region map, and mixed-media editable outputs. Repository code does not independently prove generator backend identity or call isolation.

The active stage story begins with the researcher's exact, hash-bound selection of Candidate C. Superseded attempts are retained only as compact history capsules and do not need stage time. Fidelity v2 maps eight Candidate C regions, uses exactly two bounded visual atoms, and rebuilds the remaining scientific structure as native/vector objects. Structural checks pass, and a separate human visual approval is bound to the frozen artifact-manifest hash. The annotated `v0.1.0` tag separately records project-owner approval for scientific content, Science Day use, and public release of the exact release tree.

## What the audience should remember

1. A sketch is a fast way to communicate an initial scientific figure idea.
2. Codex asks only questions whose answers materially change the meaning or result.
3. Built-in ImageGen makes five visual proposals through separate calls; it does not decide which one is correct.
4. The researcher approves one exact candidate, rejects the set, or asks for a newly rendered revision.
5. The selected candidate is mapped into reviewable regions and explicitly approved before reconstruction, rather than being silently flattened into the final figure.
6. Only an explicitly approved direction proceeds to reconstruction; editability claims are stated per object and format, and PDF is an export/preview.
7. Automated checks inspect programmable structure; visual, scientific, event-use, and public-release decisions remain separate human decisions even when their release approvals have been recorded.

## Prepare before the event

Run setup from the repository root with Python 3.11 or newer:

```bash
python3 --version
python3 -m venv /tmp/sketch-figure-science-day-venv-01
source /tmp/sketch-figure-science-day-venv-01/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/replay_reference_case.py replay \
  --output-dir /tmp/sketch-figure-science-day-preflight-01
python scripts/replay_reference_case.py validate \
  --run-dir /tmp/sketch-figure-science-day-preflight-01
python scripts/replay_reference_case.py status \
  --run-dir /tmp/sketch-figure-science-day-preflight-01
```

Installation may need network access if declared packages are not cached. Complete it before the event. The presentation path itself needs no user-supplied API key and should not depend on venue Wi-Fi.

Open these files before going on stage:

- [`examples/deep_image_prior/sketch.png`](../examples/deep_image_prior/sketch.png)
- [`examples/deep_image_prior/clarification_brief.md`](../examples/deep_image_prior/clarification_brief.md)
- [`examples/deep_image_prior/candidate-comparison.png`](../examples/deep_image_prior/candidate-comparison.png)
- [`examples/deep_image_prior/candidate_manifest.json`](../examples/deep_image_prior/candidate_manifest.json)
- [`examples/deep_image_prior/selection_history.json`](../examples/deep_image_prior/selection_history.json)
- [`examples/deep_image_prior/candidate_selection_c_only.json`](../examples/deep_image_prior/candidate_selection_c_only.json)
- [`examples/deep_image_prior/reference_case_v0_1.json`](../examples/deep_image_prior/reference_case_v0_1.json)
- [`examples/deep_image_prior/reference_case_v0_1_artifact_manifest.json`](../examples/deep_image_prior/reference_case_v0_1_artifact_manifest.json)
- [`examples/deep_image_prior/reference_case_v0_1_validation_report.json`](../examples/deep_image_prior/reference_case_v0_1_validation_report.json)
- [`examples/deep_image_prior/approvals/fidelity_v2_region_map_approval.json`](../examples/deep_image_prior/approvals/fidelity_v2_region_map_approval.json)
- [`examples/deep_image_prior/approvals/fidelity_v2_visual_approval.json`](../examples/deep_image_prior/approvals/fidelity_v2_visual_approval.json)
- [`examples/deep_image_prior/editable_delivery_c_fidelity_v2/source/region_overlay.png`](../examples/deep_image_prior/editable_delivery_c_fidelity_v2/source/region_overlay.png)
- [`examples/deep_image_prior/editable_delivery_c_fidelity_v2/preview.png`](../examples/deep_image_prior/editable_delivery_c_fidelity_v2/preview.png)
- [`examples/deep_image_prior/editable_delivery_c_fidelity_v2/source/equations.tex`](../examples/deep_image_prior/editable_delivery_c_fidelity_v2/source/equations.tex)
- [`examples/deep_image_prior/editable_delivery_c_fidelity_v2/delivery/svg/master.svg`](../examples/deep_image_prior/editable_delivery_c_fidelity_v2/delivery/svg/master.svg)
- [`examples/deep_image_prior/editable_delivery_c_fidelity_v2/delivery/pptx/figure.pptx`](../examples/deep_image_prior/editable_delivery_c_fidelity_v2/delivery/pptx/figure.pptx)
- [`examples/deep_image_prior/editable_delivery_c_fidelity_v2/delivery/drawio/figure.drawio`](../examples/deep_image_prior/editable_delivery_c_fidelity_v2/delivery/drawio/figure.drawio)
- [`examples/deep_image_prior/editable_delivery_c_fidelity_v2/delivery/pdf/publication.pdf`](../examples/deep_image_prior/editable_delivery_c_fidelity_v2/delivery/pdf/publication.pdf)

The five candidate originals are separate files under [`examples/deep_image_prior/candidates/`](../examples/deep_image_prior/candidates/). Do not describe the comparison sheet as an ImageGen result; local code assembled it only after the five originals existed.

## Recommended 3–5 minute timeline

| Time | Show | Say |
|---|---|---|
| 0:00–0:30 | Original Deep Image Prior sketch | “Sketches are fast, but rebuilding the same idea cleanly in several editable formats is repetitive.” |
| 0:30–1:00 | Short clarification brief | “Codex resolves only outcome-changing ambiguity: what the feedback means, what is compared, and which notation must be exact.” |
| 1:00–1:45 | A–E comparison sheet | “These came from five separate built-in ImageGen calls using the same sketch and confirmed relationships.” |
| 1:45–2:20 | Decision history and eight-region overlay | “Candidate C remains hash-bound. Before rebuilding it, Codex records each major region and how it will become a native object or an approved replaceable atom.” |
| 2:20–3:25 | Run frozen replay; inspect SVG/PPTX, structural draw.io, and PDF preview | “Only the noise and synthetic mountain remain as replaceable image atoms. Network layers, plots, arrows, labels, and nine aspect-preserving LaTeX equations are native or vector objects in SVG/PPTX.” |
| 3:25–4:15 | Machine-readable structural report and artifact manifest | “Code checked hashes, parsing, the two-raster boundary, equation aspect ratios, and directed topology. It cannot certify scientific correctness.” |
| 4:15–5:00 | Hash-bound visual approval and tag-level owner approvals | “This exact frozen manifest has visual approval. Automated validation did not approve the science or release; the project owner separately recorded scientific-content, Science Day-use, and public-release approvals in the immutable `v0.1.0` tag.” |

If a fresh live sketch has not reached an approved choice during the event, stop that live branch at selection and continue with the checked-in Candidate C fidelity-v2 case. Say explicitly that the checked-in package is frozen evidence rather than a live ImageGen result.

## Live talking points

### 1. Show the input

The sketch is original to the repository author and was not copied or traced from a paper figure. It illustrates the Deep Image Prior principle without experimental data, quantitative results, or an unpublished method.

Point out the intended structure:

- latent input \(z\);
- generator \(G_\theta\);
- reconstructed image \(\hat{x}=G_\theta(z)\);
- forward operator \(A\);
- predicted observation \(\hat{y}\);
- comparison with measured \(y\);
- feedback through \(\theta^*=\arg\min_\theta\lVert A G_\theta(z)-y\rVert_2^2\).

### 2. Show the clarification

Clarification is a short conversation, not a user-facing structured-interpretation form. This example resolved the feedback-loop meaning, comparison, image content, and intended wide Science Day/GitHub format.

Codex normally asks 1–3 questions per round and usually no more than two rounds. It should not ask the researcher to repeat information already visible in the sketch or present in the conversation.

### 3. Show five proposals from separate calls

| Slot | Direction | Purpose |
|---|---|---|
| A | Faithful | Preserve the sketch's recognizable layout while polishing it |
| B | Publication | Use a restrained, compact paper-figure treatment |
| C | Presentation | Increase hierarchy and distance legibility |
| D | Alternative layout | Reorganize composition without changing confirmed relationships |
| E | Visual variant | Explore a different palette and graphical language |

Do not claim that generated labels, equations, or arrows are authoritative. The sketch plus the researcher's clarification remains the source for exact content.

### 4. Make the researcher decision visible

Show the active decision sequence used for this example:

```text
Choose candidate C only for the new editable review draft.
Keep C as the reference; map its regions first, then use the fidelity-first editable reconstruction.
Approve the eight-region map and the two explicit raster exceptions.
```

For a future revision request, use wording such as:

```text
Revise D: keep the central loss loop, but use A's restrained color direction.
```

That instruction is not itself an approved composite. Render it as a new candidate in a new append-only proposal run, register its file and hash, show it to the researcher, and then ask for approval. Editable reconstruction begins only after explicit approval of one exact rendered candidate.

### 5. Explain the editable reconstruction

For the canonical fidelity-v2 case, Codex used C for both composition and graphical character, recorded and approved eight source regions before drawing, and used the sketch plus clarification for exact labels, equations, direction, and grouping. Rejected reconstructions remain available as history and are not presented as the active result.

Required outputs are:

- SVG with native/vector structure, embedded vector equations, and exactly two bounded raster atoms;
- PPTX with independent frames, network layers, plots, labels, connectors, and SVG equations plus two replaceable raster pictures;
- draw.io with native graph cells and source/target edges as an experimental topology-focused view; its official CLI render currently shows black major regions and raw-LaTeX equations, so do not use it as visual-fidelity evidence;
- PDF described only as export/preview.

Candidate C is not embedded as the whole canvas. The checked-in package has two exact-pixel, replaceable raster modules, nine aspect-preserving LaTeX-derived vector equation objects, and seven directed connectors. The two image atoms are not pixel-editable or scientific evidence. The authoritative formula source is `source/equations.tex`; formula content should be edited there and regenerated.

### 6. Separate checks from judgment

Automated validation may check parseability, hashes, expected labels, native object evidence, IDs, directed edges, grouping, approved raster boundaries, and implemented cross-format consistency. It does not establish scientific correctness, visual quality, Science Day suitability, public-release readiness, or final approval.

End with:

> Codex reduces the mechanical translation and export work. The researcher still controls meaning, visual direction, and final acceptance.

## Primary offline replay

The primary demo is the frozen Deep Image Prior reference case. It executes no ImageGen or network calls and writes only to a new directory outside the repository:

```bash
python scripts/replay_reference_case.py replay \
  --output-dir /tmp/sketch-figure-science-day-reference-01
python scripts/replay_reference_case.py validate \
  --run-dir /tmp/sketch-figure-science-day-reference-01
python scripts/replay_reference_case.py status \
  --run-dir /tmp/sketch-figure-science-day-reference-01
```

Expected summary:

```text
"offline_replay": true
"imagegen_or_remote_calls": 0
"workflow_stage": "VISUAL_APPROVED"
"ready_for_scientific_use": false
"ready_for_science_day_use": false
"ready_for_public_release": false
```

Open:

- `/tmp/sketch-figure-science-day-reference-01/reference_case_v0_1_readiness.json`
- `/tmp/sketch-figure-science-day-reference-01/imagegen_workflow_state.json`
- `/tmp/sketch-figure-science-day-reference-01/delivery/svg/master.svg`
- `/tmp/sketch-figure-science-day-reference-01/delivery/pptx/figure.pptx`
- `/tmp/sketch-figure-science-day-reference-01/delivery/pdf/publication.pdf`

The three `false` values above are the frozen replay ledger's pre-authorization state; replay deliberately does not synthesize later governance decisions. The annotated `v0.1.0` tag is the separate hash-bound record of the owner's scientific-content, Science Day-use, and public-release approvals.

Say: “This is a frozen replay of five recorded proposals and one approved Candidate C delivery. It did not rerun ImageGen. Automated validation did not approve the science; the project owner separately approved the exact tagged case for scientific content, Science Day use, and release.”

An optional rebuild is useful only when the native runtime has already passed the explicit preflight in [runtime requirements](runtime_requirements.md#fidelity-v2-rebuild-preflight). It must use a new external output directory and does not inherit the frozen visual approval:

```bash
python scripts/build_deep_image_prior_c_fidelity_v2.py \
  --soffice "$SOFFICE_BIN" \
  --pdftoppm "$PDFTOPPM_BIN" \
  --output-dir /tmp/sketch-figure-science-day-rebuild-01
```

If that rebuild cannot complete, return to the frozen replay. Do not improvise a replacement artifact or alter the canonical directory on stage.

## Optional live ImageGen extension

Only use this after the deterministic 3–5 minute path if time and the Codex environment permit it. Attach a fresh publication-safe sketch, show focused clarification, and request A–E through five separate built-in ImageGen calls. Explain that the pixels are non-deterministic. Stop at the selection decision unless the researcher approves one exact direction; do not present a newly generated candidate as an editable or validated figure.

## Failure and no-network plan

| Situation | Use | Honest statement |
|---|---|---|
| No venue network | Primary frozen replay | “The candidates were generated beforehand in five separate Codex calls; this replay and its checks are local.” |
| Built-in ImageGen unavailable | Present the recorded candidates and manifest | “This is a pre-generated proposal set, not live generation.” |
| A new live sketch has no approved choice | Stop that branch at the decision point; return to the frozen fidelity-v2 replay | “This live sketch is blocked until the researcher chooses; the following case was prepared and structurally checked earlier.” |
| Native adapter runtime unavailable | Skip rebuild; use frozen outputs and the machine-readable report | “These files were generated and checked beforehand; I am replaying their evidence, not rebuilding them here.” |
| Candidate has a wrong label or arrow | Revise or regenerate that slot | “Image generation does not establish scientific authority.” |
| Validation fails | Preserve the report and do not present delivery as verified | “The programmable check found a blocking issue.” |

## Reset and cleanup

Repository source files are not modified during the stage demo. For every offline retry, use a new external output directory, for example change `-01` to `-02`; the runner refuses to overwrite an existing run.

After the event, inspect the exact `/tmp/sketch-figure-science-day-*` directories before removing them. No repository cleanup command, Git reset, or remote write is required.

## Responsibility summary

| Layer | Does | Does not do |
|---|---|---|
| Codex clarification | Resolves material ambiguity and produces a short prose brief | Require the researcher to approve JSON |
| Built-in ImageGen | Produces five visual directions through separate calls | Decide science, editability, or approval |
| Reconstruction code | Builds native objects and repeatable exports after selection | Infer scientific correctness |
| Automated validation | Checks programmable file and structure properties | Create final scientific approval |
| Researcher | Corrects ambiguity, selects/revises a direction, and accepts or rejects the final figure | Delegate accountability to an AI image or status label |
