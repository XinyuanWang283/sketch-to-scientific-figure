# Public release checklist

Do not make the repository public until every P0 item is resolved.

## P0 — required before first public push

- [x] Choose an open-source license and add the exact `LICENSE` text: MIT.
- [x] Exclude unpublished project example documents, images, and delivery outputs.
- [x] Confirm that the author name and citation metadata in `CITATION.cff` are correct.
- [x] Run the core unit tests from a clean environment.
- [x] Run the personal-path, credential, cache, and broken-link scans recorded in the preparation report.
- [x] Review the pushed repository while the GitHub visibility remains **Private**.

## P1 — strongly recommended

- [x] Add a fictional, non-confidential end-to-end example with an editable SVG and deterministic topology artifacts.
- [ ] Obtain one colleague's dry-run feedback using only the README.
- [ ] Add a repository description and topic tags on GitHub.
- [ ] Add a small social preview image.
- [ ] Create the first release tag only after the public contents are frozen.

## First-push boundary

The verified public-ready tree has been pushed to the private `main` branch. Before changing visibility to Public, confirm the latest Actions run is green, inspect the rendered README and safe example on GitHub, and make the visibility change as a separate explicit action.

## Science Day evidence

No unpublished project example is included. The repository does not yet establish a time-saving percentage. For a defensible claim, record active human time for at least a small set of comparable figures and state how the baseline was measured.
