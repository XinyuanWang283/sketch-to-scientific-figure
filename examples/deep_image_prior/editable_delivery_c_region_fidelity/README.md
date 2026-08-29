# Candidate C — region-first fidelity review package

Status: `AWAITING_FINAL_RESEARCHER_REVIEW`. Final scientific approval is `null`.

This is a **fidelity-first mixed-media editable composition**. The user selected Candidate C and the current request authorizes this segmented review draft; it does not authorize final publication approval.

## Region-first construction

1. `source/selected_candidate_map.json` binds Candidate C by SHA-256 and records eight major source-pixel regions.
2. `source/region_overlay.png` and `source/reference_regions/` expose the region review. They are `reference_only_not_embedded` QA assets.
3. `source/raster_atom_review_decision.json` records the user's narrow `APPROVED_FOR_REVIEW_DRAFT_ONLY` authorization before assembly; both final approval fields remain `null`.
4. `source/asset_manifest.json` authorizes exactly two exact-pixel raster atoms: noise content and reconstruction content.
5. Every other component is rebuilt as native shapes, text, plot paths, explicit arrows, or intrinsic-aspect vector LaTeX.

## Editability boundary

The two image atoms are **replaceable but not pixel-editable**. They are independent image objects, not a whole-slide screenshot. Generator layers, frames, plot curves, plot sample points, labels, connectors, and arrowheads remain separately editable. Equations are vector SVGs generated from the authoritative LaTeX in `source/equations.tex`.

## Outputs

- `delivery/svg/master.svg`: native composition plus two relative replaceable image-asset references.
- `delivery/pptx/figure.pptx`: more than 500 native shapes, two independent picture shapes, and nine vector equation objects.
- `delivery/drawio/figure.drawio`: native structural cells and seven directed edges plus two independent image cells.
- `delivery/pdf/publication.pdf`: **preview/export only**; no editability or scientific-correctness claim.
- `preview.png`: rendered PDF review preview.
- `delivery/pptx/slide-01.png`: independent PowerPoint authoring render.

## Approval boundary

Candidate C selection and this segmented review draft are visual decisions. `source/raster_atom_review_decision.json` authorizes only the two listed atoms for this review draft. The image atoms are synthetic visuals, not scientific evidence. Automated validation checks provenance, exact crops, file structure, topology, arrow construction, and equation aspect ratio. It does not validate scientific correctness. Final publication approval and final scientific approval are both `null` and require explicit researcher review.
