# Candidate C — region-first native review revision

Status: `AWAITING_FINAL_RESEARCHER_REVIEW`. Final scientific approval is `null`.

The earlier `editable_delivery_c_segmented_native` directory has status `INCOMPLETE_SUPERSEDED_BUILD`. This package supersedes it; use this directory for review.

## What “region-first” means

1. `source/selected_candidate_map.json` binds the exact Candidate C SHA-256 and records eight source-pixel regions.
2. `source/region_overlay.png` and `source/reference_regions/*.png` make the decomposition inspectable. They are marked `reference_only_not_embedded`.
3. `source/semantic_figure.json` maps each region to stable native output IDs.
4. SVG, PPTX, and draw.io are reconstructed from native shapes, paths, text, connectors, and vector equations. Candidate C and its crops are not embedded.

## Specific corrections in this revision

- Every arrow uses a separate small filled triangle; SVG markers are not used, and each butt-capped shaft stops at the triangle base.
- Every LaTeX SVG keeps its intrinsic `viewBox` aspect ratio. The bottom objective is about 600 × 90 source pixels; the reconstruction equation is about 233 × 51.
- The noise field is a deterministic editable stipple/short-stroke field.
- The network, synthetic landscape, and signal plots are native vector regions.

## Editable outputs

- `delivery/svg/master.svg`: all-native vector review master.
- `delivery/pptx/figure.pptx`: independent native shapes/text plus vector equation objects.
- `delivery/drawio/figure.drawio`: native structural cells and directed edges.
- `delivery/pdf/publication.pdf`: preview/export only; no editability or scientific-correctness claim.

## Trade-off

All-native reconstruction preserves editability but intentionally represents the Candidate C mountain as a stylized vector landscape rather than a photographic crop. Automated validation checks format, topology, raster absence, arrow construction, and equation aspect ratios; it does not approve scientific meaning or visual quality.
