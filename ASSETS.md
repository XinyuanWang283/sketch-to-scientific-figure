# Asset provenance and licensing boundaries

This file describes the public assets shipped with the repository. It is a provenance record, not legal advice, scientific validation, or a guarantee that generated imagery is free of third-party rights.

## Deep Image Prior reference case

| Asset group | Repository paths | Recorded origin | Use boundary |
|---|---|---|---|
| Input sketch | `examples/deep_image_prior/sketch.png` | Created by the repository author as an original explanatory sketch | Not copied or traced from a paper figure; contains no experimental data |
| ImageGen candidates | `examples/deep_image_prior/candidates/A-faithful.png` through `E-visual-variant.png` | Operator-attested outputs from five separate Codex built-in ImageGen calls | Visual proposals only; not measurements, results, or scientific evidence |
| Candidate comparison | `examples/deep_image_prior/candidate-comparison.png` | Deterministic local composition of the five saved candidate files | Derived convenience view, not a sixth generation call |
| Region references | `examples/deep_image_prior/editable_delivery_c_fidelity_v2/source/reference_regions/` and `source/region_overlay.png` | Crops and annotations derived from the hash-bound Candidate C file | Visual QA inputs; not delivery assets or scientific evidence |
| Approved raster atoms | `examples/deep_image_prior/editable_delivery_c_fidelity_v2/source/raster_atoms/` and `delivery/svg/assets/` | Exact, unresampled crops from Candidate C, bound by source-pixel boxes and SHA-256 values | Two replaceable synthetic visual atoms; not pixel-editable and not measured data |
| Equation objects | `examples/deep_image_prior/editable_delivery_c_fidelity_v2/source/equations.tex`, `source/equation_manifest.json`, and `source/math/` | Local rendering of the case's authoritative LaTeX source | Vector-path representations remain bound to the LaTeX source; they are not semantically editable LaTeX |
| Editable delivery | `examples/deep_image_prior/editable_delivery_c_fidelity_v2/delivery/` | Generated locally by the case-specific reconstruction tools from the approved records | SVG and PPTX contain native/vector objects; draw.io is a structural view; PDF is preview/export |
| Validation images | `examples/deep_image_prior/editable_delivery_c_fidelity_v2/validation/region_comparisons/` | Deterministic comparison views derived from Candidate C and rendered delivery artifacts | Diagnostic evidence for human review; not a fidelity benchmark or approval |

The scientific concept is attributed to Dmitry Ulyanov, Andrea Vedaldi, and Victor Lempitsky, [*Deep Image Prior*](https://arxiv.org/abs/1711.10925), CVPR 2018. This repository explains the concept in independently created artwork; it does not redistribute or reproduce the paper's figure artwork.

Exact candidate hashes, dimensions, generation-event records, and provenance status are stored in [`examples/deep_image_prior/candidate_manifest.json`](examples/deep_image_prior/candidate_manifest.json). The repository records the candidates as operator-attested Codex ImageGen outputs. It does not invent a native tool-call ID, model version, seed, or API record when none was exposed.

The candidate files were observed to contain Content Credentials when the reference evidence was assembled. The repository does not cryptographically validate those credentials and does not treat them as proof of backend identity or call isolation.

## Superseded previews

Compact preview images from rejected reconstruction attempts may remain in the current tree as decision-history evidence. They are not supported deliverables. Complete superseded packages remain available in the immutable `v0.1.0` release history.

## Source readings and external links

The repository links to papers, DOI pages, publishers, tools, and external documentation. A link does not import the linked work into this repository or grant a license to it. The current tree does not intentionally redistribute source-paper PDFs as reference assets.

## MIT License boundary

The repository is distributed under the [MIT License](LICENSE). That license applies to the repository material supplied by its copyright holder to the extent that the holder has the right to license it.

The MIT License does not by itself:

- transfer ownership of the underlying Deep Image Prior scientific concept;
- grant rights in third-party papers, linked works, trademarks, or external software;
- certify the legal status of model-generated imagery in every jurisdiction;
- establish that an output is scientifically correct, publication-ready, or suitable for a particular venue;
- replace a downstream user's responsibility to review asset rights, attribution, privacy, and publication policies.

No separate license or scientific-use guarantee is asserted for the ImageGen candidates beyond the repository-level license statement and the provenance records above. If a future case uses a user-provided, licensed, medical, or other third-party asset, its manifest must record the actual source, license or permission status, attribution, modification status, and privacy review without guessing missing values.

## Reporting a concern

If an asset appears to have incorrect provenance, attribution, privacy status, or release permission, do not reuse it. Report the exact repository path through the project's security or issue-reporting channel so the owner can review it before further distribution.
