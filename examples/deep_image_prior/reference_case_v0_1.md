# v0.1 reference case: Deep Image Prior

## Scope

Version 0.1 is a reusable **Codex workflow plus one verified reference case**. It is not a universal sketch-to-vector converter, and it does not claim that arbitrary generated artwork can be recovered as semantically correct editable objects.

The reusable part is the decision sequence: resolve material ambiguity, make five separate generation calls, let the researcher choose or revise, bind the chosen source by hash, map its regions, and reconstruct the approved direction with explicit format-specific editability boundaries. The checked-in Deep Image Prior materials are one publication-safe demonstration of that sequence.

The canonical review package for this case is [`editable_delivery_c_fidelity_v2/`](editable_delivery_c_fidelity_v2/README.md). Earlier deliveries remain recorded in [`selection_history.json`](selection_history.json), with their full historical packages preserved by the immutable [`v0.1.0` tag](https://github.com/XinyuanWang283/sketch-to-scientific-figure/tree/v0.1.0/examples/deep_image_prior); they are not active directories on `main`.

## Two execution paths

### 1. Live Codex path

The live product path is interactive and intentionally non-deterministic:

```text
hand sketch and exact scientific material
→ focused questions about outcome-changing ambiguity
→ five separate Codex built-in ImageGen calls
→ A Faithful / B Publication / C Presentation / D Alternative layout / E Visual variant
→ researcher approval of one exact candidate, rejection, or request for a new revision
→ any requested revision is rendered and registered as a new candidate
→ explicit hash-bound approval of one exact visual direction
→ case-specific, hash-bound region map
→ native/mixed-media reconstruction and review
```

All five candidates receive the same sketch and clarified brief, with one direction-specific suffix per call. They are five separate ImageGen outputs, not a generated five-panel sheet. ImageGen proposes visual directions; it does not determine equations, topology, scientific correctness, editability, or approval. Repository Python records artifacts and hashes but does not rerun or impersonate Codex built-in ImageGen.

The live path can produce different pixels on another run. Its scientific content therefore remains controlled by the sketch, exact typed material, and researcher corrections—not by generated labels, equations, or arrows.

### 2. Offline frozen replay

The offline path replays the checked-in reference case. It **does not rerun ImageGen**, regenerate A–E, or prove which backend produced the recorded candidates. It is the deterministic primary path for a Science Day demonstration because it avoids network and generation variance while preserving the recorded decision and artifact evidence.

From the repository root, write only to a new directory outside the repository:

```bash
python scripts/replay_reference_case.py replay \
  --output-dir /tmp/sketch-figure-reference-v0-1

python scripts/replay_reference_case.py validate \
  --run-dir /tmp/sketch-figure-reference-v0-1

python scripts/replay_reference_case.py status \
  --run-dir /tmp/sketch-figure-reference-v0-1
```

Use a different new output directory for every replay. The optional live Science Day branch may show focused clarification and fresh A–E generation, but it is non-deterministic and must stop if the researcher has not approved an exact direction. Continue the presentation with the frozen reference case rather than presenting an unapproved live branch as complete.

## Responsibility boundary

| Party | Responsible for | Not responsible for |
|---|---|---|
| Researcher | Authoritative meaning, corrections, selection or revision, and explicit visual/scientific acceptance | Delegating scientific accountability to an image, validator, or status label |
| Codex | Focused clarification, five-call orchestration, provenance records, region mapping, reconstruction, and an honest review packet | Inventing scientific facts or approving on the researcher's behalf |
| Built-in ImageGen | Five A–E visual proposals from separate calls using the same sketch and brief | Exact scientific text, topology, editability, selection, or final approval |
| Repository code | Frozen replay, hash and structure checks, deterministic reconstruction/export, and status reporting | Rerunning ImageGen, verifying backend identity, judging scientific correctness, or creating human approval |

## Verified reference case

The authoritative index is [`reference_case_v0_1.json`](reference_case_v0_1.json). The input is an original synthetic sketch of the Deep Image Prior principle, accompanied by a short [`clarification_brief.md`](clarification_brief.md). Five separately recorded candidates and their hashes are listed in [`candidate_manifest.json`](candidate_manifest.json). The active direction is Candidate C, bound to SHA-256 `c888a5fd0d2c4380717c8e38c1f9ec08d764ef31ef770983ead278a26c8cb26c` by the selection and [region-map approval](approvals/fidelity_v2_region_map_approval.json).

The decision history matters. A D-layout/C-style reconstruction was rejected. A native-only C reconstruction lost too much of the selected visual character. A later hybrid retained two image regions but had equation-aspect and missing-region-map defects. [`selection_history.json`](selection_history.json) preserves those decisions, while the complete frozen legacy packages remain available at the immutable [`v0.1.0` tag](https://github.com/XinyuanWang283/sketch-to-scientific-figure/tree/v0.1.0/examples/deep_image_prior), not in active delivery directories on `main`. The canonical v0.1 result is the later fidelity-v2 review package, which starts from an eight-region map and preserves two narrowly authorized, independently replaceable synthetic image atoms.

The [machine-readable validation report](reference_case_v0_1_validation_report.json) and [artifact manifest](reference_case_v0_1_artifact_manifest.json) bind the approved inputs to the exact delivery outputs. Their input hashes include both the raster-asset manifest and its explicit review-draft authorization; a rejected, weakened, missing, or mismatched raster decision fails closed. Programmatic validation reports `VERIFIED_FIDELITY_V2_REVIEW_DRAFT`. This means the checked scope—candidate and crop provenance, the eight-region/two-raster boundary, equation aspect ratio, native/vector structure, parsing, and directed topology—passed. It does not mean the figure is scientifically correct, publication-ready, or universally reproducible from other sketches. Visual acceptance is a separate human record described below.

## Canonical artifacts and precise editability

| Artifact | v0.1 claim |
|---|---|
| [`source/semantic_figure.json`](editable_delivery_c_fidelity_v2/source/semantic_figure.json) and [`source/equations.tex`](editable_delivery_c_fidelity_v2/source/equations.tex) | Canonical object/topology source and authoritative equation source for this case |
| [`delivery/svg/master.svg`](editable_delivery_c_fidelity_v2/delivery/svg/master.svg) | Editable vector composition with live structural objects, vector equations, and exactly two relative, replaceable raster sidecars; those two image contents are not pixel-editable |
| [`delivery/pptx/figure.pptx`](editable_delivery_c_fidelity_v2/delivery/pptx/figure.pptx) | Independent native shapes, gradients, text, editable synthetic curves, vector equation objects, and two replaceable picture objects; it is not a flattened slide image |
| [`delivery/drawio/figure.drawio`](editable_delivery_c_fidelity_v2/delivery/drawio/figure.drawio) | **Experimental structural view** with editable cells and seven directed topology edges. The official draw.io CLI renders its major colored regions as black blocks and displays all nine equation values as raw LaTeX. It is not the visual master or visual-fidelity evidence |
| [`delivery/pdf/publication.pdf`](editable_delivery_c_fidelity_v2/delivery/pdf/publication.pdf) | Preview/export only; no semantic or object-level editability claim |

The SVG uses relative raster sidecars under `delivery/svg/assets/`. Relative links are intentional for a portable package: keep `master.svg` and its `assets/` directory together. The two exact-pixel crops are synthetic visual atoms, are independently replaceable, and are explicitly not scientific evidence.

Correcting the draw.io rendering defect requires a new delivery revision. The frozen fidelity-v2 artifact is evidence for the v0.1 structural path and is not modified in place.

## Approval state

Candidate selection and the region map are bound to the exact Candidate C hash. The v0.1 [visual decision record](approvals/fidelity_v2_visual_approval.json) is stored separately as `APPROVE_VISUAL_DELIVERY` and binds the exact frozen artifact-manifest SHA-256, so a later rebuild cannot inherit that approval silently. Its scope includes the documented draw.io limitation; it does not approve scientific meaning or public/event use.

A fresh offline replay reports `workflow_revision: 6` because this is the replay ledger's six-event counter: clarification, five-candidate registration, Candidate C approval, region-map approval, delivery registration, and visual approval. Sequence `8` in [`selection_history.json`](selection_history.json) is the checked-in evidence lineage, while `delivery_revision: fidelity-v2` is the artifact-family identifier. These values belong to different namespaces and are not competing version numbers.

The generated fidelity-v2 package reports describe the pre-case packaging state and remain frozen with their earlier nullable final-approval fields. Those `null` values do not override or conflict with the separate, hash-bound reference-case visual decision; that record is the authoritative visual approval for v0.1 replay.

The checked-in record preserves the pre-authorization snapshot state:

- scientific approval is `PENDING` in replay state;
- Science Day use approval is `PENDING` in replay state;
- public-release approval is `PENDING` in replay state;
- structural validation must not be presented as any of those approvals.

The annotated `v0.1.0` tag is a separate, later attestation bound to the exact release commit, Git tree, snapshot digests, artifact manifest, validation report, visual approval, and canonical artifact hashes. It records project-owner approval for scientific content, Science Day use, and public release of that exact release tree without rewriting the frozen replay ledger.

## Rebuild boundary

The frozen replay is the primary reproducible demonstration. A maintainer who intentionally needs a fresh fidelity-v2 reconstruction may run the case-specific builder, but must first complete the [native-runtime preflight](../../docs/runtime_requirements.md#fidelity-v2-rebuild-preflight) and write to a new directory outside the repository:

```bash
python scripts/build_deep_image_prior_c_fidelity_v2.py \
  --soffice "$SOFFICE_BIN" \
  --pdftoppm "$PDFTOPPM_BIN" \
  --output-dir /tmp/sketch-figure-fidelity-v2-rebuild-01
```

The builder refuses to overwrite an existing output directory. A complete rebuild also depends on the documented native PDF/preview runtime. Rebuilding does not grant visual, scientific, Science Day, or public-release approval.

For the event narrative, use the deterministic frozen replay as the primary path and treat fresh built-in ImageGen calls as an optional, explicitly non-deterministic branch. See the [Science Day runbook](../../docs/science-day-demo.md) for timing and fallback guidance.
