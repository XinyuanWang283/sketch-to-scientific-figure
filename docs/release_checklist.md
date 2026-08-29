# Public release checklist

Do not make the repository public until every P0 item is resolved.

## P0 — required before public visibility

- [x] Choose an open-source license and add the exact `LICENSE` text: MIT.
- [x] Limit v0.1 to publication-safe synthetic/reference cases; uncleared domain-specific case studies are excluded.
- [x] Confirm that the author name and citation metadata in `CITATION.cff` are correct.
- [x] Review PDF/PPTX creator metadata; it is a generic exporter label rather than personal identity, so artifact sanitization is not required.
- [x] Pin third-party GitHub Actions to verified immutable full commit SHAs.
- [x] Run the core unit tests from a clean environment.
- [x] Run the personal-path, credential, cache, and broken-link scans recorded in the preparation report.
- [ ] Record repository-owner acceptance of the exact proposed release-candidate file set.
- [ ] Record scientific approval for the exact reference-case artifact manifest, or explicitly decide that the public repository may ship with scientific approval pending.
- [ ] Record Science Day-use approval for the exact frozen case before presenting it at the event.
- [ ] Record public-release approval after reviewing this local tree and all remaining blockers.
- [x] Use the verified GitHub noreply identity for author and committer metadata throughout local `main` history.
- [ ] Push the accepted file set, then confirm that remote Actions pass for that exact commit while GitHub visibility remains **Private**.

## P1 — strongly recommended

- [x] Add an original publication-safe sketch with five separately generated ImageGen proposals, hash-bound selection and region-map records, validation-backed delivery registration, and a separate visual approval.
- [x] Add a fictional, non-confidential end-to-end example with an editable SVG and deterministic topology artifacts.
- [ ] Obtain one colleague's dry-run feedback using only the README.
- [ ] Add a repository description and topic tags on GitHub.
- [ ] Add a small social preview image.
- [ ] Create the first release tag only after the public contents are frozen.

## First-push boundary

The current release-candidate changes exist only in the local working tree; they have not been pushed. After an explicit local review and push, confirm that Actions passed for that exact commit, inspect the rendered README and safe example while the repository is still Private, resolve every unchecked P0 item above, and make any visibility change as a separate explicit action.

## Science Day evidence

Use the [Science Day demo guide](science-day-demo.md) for the original Deep Image Prior sketch, five separately generated proposals, preserved decision history, and the canonical [`editable_delivery_c_fidelity_v2/`](../examples/deep_image_prior/editable_delivery_c_fidelity_v2/README.md) reference case. Earlier revisions remain legacy evidence. Fidelity v2 binds eight source regions to the selected Candidate C hash, keeps exactly two bounded synthetic raster atoms, and rebuilds the remaining scientific structure with native/vector objects and aspect-preserving LaTeX-derived equations. Its draw.io file is an experimental structural view with a known official-render defect, and its PDF is a preview/export. Structural validation and a hash-bound visual approval exist; scientific approval, Science Day use, and public release remain pending. The primary offline replay executes no AI. Neither path is human research, a scientific-correctness result, or a time-saving benchmark.
