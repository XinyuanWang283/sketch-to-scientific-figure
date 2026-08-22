# GitHub workflow inspiration

Reviewed on 2026-08-13. These repositories informed the local workflow design. They are not dependencies, scientific authorities, venue specifications, or templates to copy wholesale.

## Transferable patterns

### Separate scientific intent, visual planning, generation, and critique

- [Google Research PaperVizAgent](https://github.com/google-research/papervizagent) uses Retriever, Planner, Stylist, Visualizer, and Critic stages. Its planner requests concrete element, connection, color, line, and icon descriptions rather than a formula transcription.
- The project's [diagram style guide](https://github.com/google-research/papervizagent/blob/main/style_guides/neurips2025_diagram_style_guide.md) recommends an actual thumbnail for image content rather than an empty square. This guide is project-authored, not an official NeurIPS specification.
- [NanaDraw](https://github.com/Shannon4Science/NanaDraw) separates Draft, Generation, and Assembly. Its Assembly sequence—Plan, Image, Blueprint, Components, Assembly—supports using a concept image to discover embodiment before producing structured editable output.

Local adoption: preserve the hard scientific contract, add a separate VISUAL EMBODIMENT BRIEF, generate layout hypotheses, review them, and reconstruct the selected structure.

### Assemble semantic components instead of flattening the figure

- [AutoFigure-Edit](https://github.com/ResearAI/AutoFigure-Edit) goes from raster generation through segmentation and a labeled SVG template to final assembly. Its raster icon components are movable but are not internally vector-editable.
- [Scientific Illustrator](https://github.com/icebird1998/scientific-illustrator) prioritizes native text, shapes, connectors, tables, and charts, permitting only the smallest image region that cannot be reproduced reliably with native objects.
- [Academic Figures](https://github.com/sai-tv/academic-figures) uses named SVG groups, live text, and labeled placeholders for downstream plot insertion.

Local adoption: keep labels, borders, arrows, operators, equations, and layout native. Permit only a contract-approved minimal raster atom, keep it independently replaceable, and never flatten a panel or whole figure.

### Separate semantics from style and reuse a domain vocabulary

- [Penrose](https://github.com/penrose/penrose) separates Domain, Substance, and Style so the same semantic structure can receive different visual representations.
- [DNAplotlib](https://github.com/VoigtLab/dnaplotlib) uses a stable, customizable domain-specific glyph vocabulary and produces publication-quality vector output.

Local adoption: SCIENTIFIC LOCKS define immutable truth; SKETCH SEMANTIC LOCKS preserve deliberate glyph and spatial identity; VISUAL EMBODIMENT BRIEF defines the remaining approved representation choices. Equivalent entities keep a stable visual family across candidates and stages.

### Track asset provenance and licensing

- [Bioicons](https://github.com/duerrsimon/bioicons) distributes editable scientific SVGs and requires users to track each icon's license and attribution.

Local adoption: every non-native asset receives a manifest entry. Licensed vectors require source, revision, author, license, attribution, and modification status. Generated placeholders require generator provenance, non-evidentiary status, forbidden implications, and a release policy.

## Explicit non-adoptions

- No external API, server, UI, segmentation model, asset manager, or repository download is added to this project.
- A raster draft never becomes scientific authority.
- A generated CT, MRI, microscopy, or other scientific thumbnail never becomes evidence merely because it looks realistic.
- Project style guides are inspiration, not journal mandates.
- Component-level replaceability is not misreported as pixel-level vector editability.
