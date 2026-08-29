# Clarified rendering brief

This is a synthetic, publication-safe demonstration of the Deep Image Prior principle. The hand-drawn sketch was created by the repository author and was not copied or traced from a published figure.

## Scientific relationships to preserve

- Fixed random noise `z` enters an untrained encoder-decoder generator `G_θ`.
- The generator produces the reconstructed image `x̂ = G_{θ*}(z)`.
- A forward operator `A` maps the reconstruction to a predicted measurement `ŷ`.
- The predicted measurement `ŷ` is compared with the observed measurement `y` using an L2 data-consistency loss.
- The feedback path optimizes `θ` for the current observation; it is not a supervised training-data loop.
- The optimization equation is `θ* = arg min_θ ||A G_θ(z) − y||²₂`.

## Visual decisions inferred from the conversation

- Use a synthetic grayscale mountain image for `x̂`.
- Use a wide landscape canvas suitable for GitHub and a Science Day presentation.
- Preserve the exact variable labels, arrow direction, comparison, and feedback meaning across every candidate.
- Do not add a training dataset, ground-truth image, performance numbers, paper branding, or extra scientific modules.
- Generate five visual directions through separate calls. The researcher chooses or revises a candidate before editable reconstruction starts.

This prose brief is a rendering aid, not a structured scientific interpretation or an approval record.
