# Public release checklist

Do not make the repository public until every P0 item is resolved.

## P0 — required before first public push

- [x] Choose an open-source license and add the exact `LICENSE` text: MIT.
- [x] Exclude unpublished project example documents, images, and delivery outputs.
- [x] Confirm that the author name and citation metadata in `CITATION.cff` are correct.
- [x] Run the core unit tests from a clean environment.
- [x] Run the personal-path, credential, cache, and broken-link scans recorded in the preparation report.
- [ ] Review the repository while the GitHub visibility remains **Private**.

## P1 — strongly recommended

- [x] Add a fictional, non-confidential end-to-end example with an editable SVG and deterministic topology artifacts.
- [ ] Obtain one colleague's dry-run feedback using only the README.
- [ ] Add a repository description and topic tags on GitHub.
- [ ] Add a small social preview image.
- [ ] Create the first release tag only after the public contents are frozen.

## First-push boundary

The local preparation process does not initialize, commit, or push this directory. After the P0 review, copy or move the approved contents into the intended Git worktree, inspect `git status`, commit, and push explicitly. Keep the remote private until the pushed tree has been reviewed on GitHub.

## Science Day evidence

No unpublished project example is included. The repository does not yet establish a time-saving percentage. For a defensible claim, record active human time for at least a small set of comparable figures and state how the baseline was measured.
