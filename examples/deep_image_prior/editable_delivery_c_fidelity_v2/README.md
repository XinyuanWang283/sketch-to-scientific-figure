# Candidate C — fidelity v2 review package

Status: `AWAITING_FINAL_RESEARCHER_REVIEW`. Final visual and scientific approval remain `null`.

This package moves the editable outputs closer to the user-selected Candidate C PNG without flattening the full figure. It retains the hash-bound eight-region layout and exactly two independently replaceable raster atoms. The generator uses native editable gradients, both synthetic signal glyphs are single reference-fitted editable polylines, arrows use smaller explicit polygons, and equations are intrinsic-aspect colored LaTeX SVG objects.

## Review evidence

- `source/selected_candidate_map.json`: hash-bound visual direction and conversion policy.
- `source/semantic_figure.json`: canonical object geometry, topology, gradient paint, and curve-fit provenance.
- `validation/region_comparisons/*.png`: reference / PPTX render / amplified-difference triptychs for all eight regions.
- `validation/visual_fidelity_report.json`: diagnostic visual metrics that require human interpretation.
- `validation/fidelity_v2_validation_report.json`: programmatic structure, provenance, parse, and topology checks.

## Editable outputs

- `delivery/svg/master.svg`: vector master with relative links to two replaceable raster atoms.
- `delivery/pptx/figure.pptx`: native shapes, native gradients/alpha, editable polylines, text, and nine vector equation objects.
- `delivery/drawio/figure.drawio`: structural editing view with 11 generator layer cells, two curve cells, seven directed topology edges, and two image cells. Pixel equivalence is not claimed.
- `delivery/pdf/publication.pdf`: preview/export only; no editability claim.

The local curve fit is limited to two decorative synthetic signal glyphs in the selected ImageGen proposal. It is not a chart digitizer and does not recover scientific data. Automated validation does not judge scientific correctness or publication suitability; the researcher makes those decisions.
