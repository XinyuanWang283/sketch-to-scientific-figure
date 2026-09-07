# Release and public-visibility checklist

The last recorded remote check (2026-09-04) found Release `v0.1.0` in a Private GitHub repository. Recheck current remote state before publication. Its tag and owner attestations bind only that exact release tree; they do not approve later local or `main` changes.

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

## Current publication candidate — pending

The 2026-09-07 review started from `0a6d69bec7c331ea81a61364141369dd1023dadd` plus uncommitted legacy cleanup. Historical checks above apply to `v0.1.0`, not to this candidate. Record the final candidate commit and its verification evidence when available; do not carry forward checked boxes from a different tree.

That review passed targeted tests and verified the four canonical main-output hashes, but full tests, replay, and the complete privacy scan were interrupted by file-read stalls. Git history inspection timed out, and dependency downloads and the GitHub API were unavailable. These are incomplete checks, not passing release evidence or a diagnosis of a code defect.

- [ ] Verify the final cleanup and all canonical fidelity-v2 file hashes without changing artifact bytes.
- [ ] Review the exact proposed file set and diff; exclude local prototypes, caches, build output, and unapproved assets.
- [ ] Run clean dependency installation, the full suite, and focused workflow tests on that final tree; record commands and results.
- [ ] Run frozen replay, validation, and status in a fresh external output directory.
- [ ] Complete personal-path, credential, cache, symlink, asset-provenance, Markdown-link, and reachable-history checks on that candidate.
- [ ] Obtain owner authorization for the exact local commit contents.
- [ ] Create the authorized commit or commits using the reviewed GitHub noreply identity; record their hashes.
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
