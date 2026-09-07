# Release and public-visibility checklist

The 2026-09-08 remote check confirmed that the repository remains **Private** and commit `410a067cdedf5115569c646e582f1bff03d9f85a` passed [GitHub Actions](https://github.com/XinyuanWang283/sketch-to-scientific-figure/actions/runs/34166188147). Release `v0.1.0` and its tag are preserved. The tag's owner attestations bind only that exact release tree; they do not approve later local or `main` changes.

## Verified remote facts — 2026-09-04

- [x] Repository visibility is **Private**.
- [x] GitHub description is set.
- [x] Ten focused repository topics are set.
- [x] Default branch is `main`.
- [x] GitHub Release `v0.1.0 — Verified Science Day reference workflow` exists.

## Frozen v0.1.0 record

- [x] MIT `LICENSE` and `CITATION.cff` are present.
- [x] The release is limited to the publication-safe Deep Image Prior reference case; uncleared domain-specific material is excluded.
- [x] The input sketch is recorded as original explanatory artwork rather than a copy of a paper figure.
- [x] Five separately generated A–E candidates, hashes, generation events, and the exact Candidate C selection are recorded.
- [x] The approved region map, artifact manifest, structural report, and visual approval are hash-bound.
- [x] PDF/PPTX creator metadata was reviewed and classified as a generic exporter label rather than personal identity.
- [x] Third-party GitHub Actions are pinned to verified immutable full commit SHAs.
- [x] The release tree passed clean-environment tests, privacy checks, and remote GitHub Actions.
- [x] The annotated `v0.1.0` tag separately records owner approval for scientific content, Science Day use, and public release of that exact tree.
- [x] Author and committer history uses the reviewed GitHub noreply identity.

## Verification record — 2026-09-08

The latest pushed commit above has passing remote CI. Subsequent local documentation edits simplify the reader path and remove obsolete design notes; their local checks must not be described as remote CI results for an unpushed tree.

The earlier installation/network and history-read interruptions were resolved during the final check on 2026-09-07: a clean Python 3.12 environment installed the declared requirements without conflicts, and a fresh read-only mirror with the same eight reachable commits allowed all 398 unique historical file versions to be scanned. The defined credential, restricted-marker and private-path patterns had no matches; author and committer emails used noreply addresses. That scan describes its reviewed history, not a guarantee about future changes.

On 2026-09-08, the local suite reported 114 passed, one optional bundled-runtime test skipped, and zero failed. Frozen replay, validation and status passed; all 53 canonical files were unchanged. The suite includes relative-link, public-path, cache, symlink-containment and evidence-binding checks. The skipped adapter test does not establish a fresh native-runtime rebuild. These are software checks, not a human user study or scientific validation.

## Remaining publication steps

Apply the checklist to the final candidate, including edits made after the recorded checks. A historical pass does not automatically check a new tree.

- [ ] Verify the final cleanup and all canonical fidelity-v2 file hashes without changing artifact bytes.
- [ ] Review the exact proposed file set and diff; exclude local prototypes, caches, build output, and unapproved assets.
- [ ] Run clean dependency installation, the full suite, and focused workflow tests on that final tree; record commands and results.
- [ ] Run frozen replay, validation, and status in a fresh external output directory.
- [ ] Complete personal-path, credential, cache, symlink, asset-provenance, Markdown-link, and reachable-history checks on that candidate.
- [ ] Obtain owner authorization for the exact local commit contents.
- [ ] Commit any remaining approved local changes using the reviewed GitHub noreply identity; record their hashes.
- [ ] Push the reviewed local commits only under separate authorization.
- [ ] Confirm remote Actions pass for that exact pushed commit; record the run URL and commit hash.
- [ ] Perform the final privacy and canonical-hash check after remote CI.
- [ ] Change repository visibility only under a separate explicit owner instruction.

## Optional repository improvements

- [x] Add a repository description and topic tags on GitHub.
- [x] Keep an original publication-safe sketch, five candidates, and the frozen fidelity-v2 evidence.
- [ ] Obtain one colleague's README-only dry-run feedback.
- [ ] Add a small social preview image if the repository will be made public.

## Reference-case evidence

Review the [reference-case record](../examples/deep_image_prior/reference_case_v0_1.md) and canonical [`editable_delivery_c_fidelity_v2/`](../examples/deep_image_prior/editable_delivery_c_fidelity_v2/README.md) case. Fidelity v2 binds eight source regions to Candidate C, retains two approved synthetic raster atoms, and rebuilds the remaining structure with native/vector objects and intrinsic-aspect LaTeX-derived equations. draw.io is an experimental structural view; PDF is preview/export. The offline replay executes no ImageGen or remote call.

Distinguish structural validation from scientific correctness. Do not describe this case as a human study, time-saving benchmark, universal converter, or evidence of cross-sketch performance. Historical event-use approvals remain provenance records, not the product's purpose or a requirement to prepare a talk.
