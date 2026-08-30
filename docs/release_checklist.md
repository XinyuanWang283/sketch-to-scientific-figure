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
- [x] Record repository-owner acceptance of the exact proposed release-candidate file set.
- [x] Record scientific approval for the exact reference-case artifact manifest in the annotated `v0.1.0` tag attestation.
- [x] Record Science Day-use approval for the exact frozen case in the annotated `v0.1.0` tag attestation.
- [x] Record public-release approval for the exact release tree in the annotated `v0.1.0` tag attestation.
- [x] Use the verified GitHub noreply identity for author and committer metadata throughout local `main` history.
- [x] Push the accepted file set and confirm that remote Actions pass for the exact `main` commit and `v0.1.0` tag while GitHub visibility remains **Private**.

## P1 — strongly recommended

- [x] Add an original publication-safe sketch with five separately generated ImageGen proposals, hash-bound selection and region-map records, validation-backed delivery registration, and a separate visual approval.
- [x] Preserve the frozen Deep Image Prior v0.1 reference case, including its hash-bound manifest, validation report, and separate visual approval.
- [ ] Obtain one colleague's dry-run feedback using only the README.
- [ ] Add a repository description and topic tags on GitHub.
- [ ] Add a small social preview image.
- [x] Create the first release tag only after the release contents are frozen.

## First-push boundary

Release `v0.1.0` is committed, tagged, and published inside the still-Private repository. For every later `main` change, review the exact diff, wait for Actions on the new commit, and keep any visibility change as a separate explicit owner action.

## Science Day evidence

Use the [Science Day demo guide](science-day-demo.md) for the original Deep Image Prior sketch, five separately generated proposals, preserved decision history, and the canonical [`editable_delivery_c_fidelity_v2/`](../examples/deep_image_prior/editable_delivery_c_fidelity_v2/README.md) reference case. Earlier revisions remain legacy evidence. Fidelity v2 binds eight source regions to the selected Candidate C hash, keeps exactly two bounded synthetic raster atoms, and rebuilds the remaining scientific structure with native/vector objects and aspect-preserving LaTeX-derived equations. Its draw.io file is an experimental structural view with a known official-render defect, and its PDF is a preview/export. Structural validation and a hash-bound visual approval exist. The annotated `v0.1.0` tag separately records owner approval for scientific content, Science Day use, and public release of the exact release tree. The primary offline replay executes no AI. Neither path is human research, a scientific-correctness result, or a time-saving benchmark.
