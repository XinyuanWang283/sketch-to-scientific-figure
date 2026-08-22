# Source-derived design principles

These notes synthesize the supplied readings into domain-independent principles for scientific overview and method diagrams.

## 1. Begin with the message, not the inventory

Doumont distinguishes a message from raw information: information states what is present, whereas a message tells a specific audience what to understand. Before drawing, write one complete sentence describing what the reader should understand after viewing the figure.

An overview figure should construct a mental model for the paper. It should communicate the general concept and experimental or computational logic rather than reproduce all data or implementation detail.

Practical rule: if the figure cannot be summarized by one sentence, its scope is probably too broad.

Sources: [Doumont, 2009](../references/README.md#doumont-2009); [Wong, overview figure](../references/README.md#wong-2011--overview-figure).

## 2. Use the sketch to expose and test the mental model

Drawing forces spatial and relational assumptions to become explicit. It can expose missing links, ambiguous groupings, and contradictions that remain hidden in prose. Early sketches should be fast and exploratory; visual polish is not required.

Practical rule: scientific text and equations may correct the sketch, but every scientifically valid glyph or spatial relation that the researcher marks as deliberate becomes a binding sketch-semantic lock. Rough line quality is disposable; semantic geometry is not.

Source: [Wong, pencil and paper](../references/README.md#wong-2012--pencil-and-paper).

## 3. Use the fewest marks that preserve sophistication

Simplification is not the removal of scientific meaning. It is the removal, merging, or deemphasis of elements that do not support the main message. The objective is the fewest possible marks without becoming simplistic.

Useful operations:

- merge steps that do not need separate visual attention;
- replace repeated label fragments with one shared header;
- show the minimum number of examples needed to establish a concept;
- collapse standard components into one labeled module;
- reserve detailed data plots and network internals for other figures;
- use whitespace instead of additional boxes to separate groups.

Sources: [Wong, simplify to clarify](../references/README.md#wong-2011--simplify-to-clarify); [Krzywinski, elements of visual style](../references/README.md#krzywinski-2013).

## 4. Make every arrow a verb

Arrows are most naturally interpreted as change, movement, direction, sequence, or causality. They should describe functional relationships between objects.

Use:

- arrows for transformations and directed information flow;
- plain lines for structural association;
- leader lines without arrowheads for labels;
- consistent arrow direction to create a natural reading path.

Do not reuse the same arrow style for unrelated meanings. Use arrows sparingly, leave whitespace around their endpoints, and keep arrowheads visible but subordinate to the scientific content.

Sources: [Wong, arrows](../references/README.md#wong-2011--arrows); [Wong, overview figure](../references/README.md#wong-2011--overview-figure).

## 5. Reveal hierarchy through layout

Layout determines the order in which the figure is read. Equal visual weight for every element removes hierarchy and makes the starting point unclear.

Use:

- alignment to a small number of invisible horizontal and vertical guides;
- proximity to group related objects;
- whitespace to separate conceptual regions;
- size or position to emphasize the main scientific relation;
- restraint for supporting objects;
- a stable left-to-right or top-to-bottom reading direction unless the science requires another order.

Source: [Wong, layout](../references/README.md#wong-2011--layout).

## 6. Use a consistent visual vocabulary

Objects with the same function should look alike. Different visual forms should indicate scientifically meaningful differences, not decoration. Use parallel visual construction for parallel scientific ideas.

First establish hierarchy through topology, locked sketch geometry, grouping, alignment, whitespace, and scale. Use restrained color only when it adds a necessary secondary semantic cue. A neutral-monochrome figure is valid; when color is used, it must not be the only carrier of meaning and must preserve grayscale readability.

Source: [Krzywinski, elements of visual style](../references/README.md#krzywinski-2013).

Project workflow extension: when color is necessary, derive the palette from the current subject and publication context rather than a reusable academic default. Treat an untested swatch mapping as provisional and keep structure studies neutral until it is approved in figure context. This anti-template palette check is a local workflow decision, not a claim attributed to the supplied scientific-visualization PDFs. Workflow inspiration: Anthropic, `frontend-design` Skill, <https://github.com/anthropics/claude-code/blob/main/plugins/frontend-design/skills/frontend-design/SKILL.md> (accessed 2026-08-07).

## 7. Match visual and verbal representations

Pictures are fast and intuitive but can be ambiguous. Variables, operator labels, and concise captions disambiguate abstract scientific concepts. Use visual and verbal representations as complementary, compatible encodings rather than as competing duplicates.

The visual object should show a scientific role, while notation identifies the exact quantity, operator, state, measurement, or module in the current paper.

For an image-valued state, the visual role normally requires recognizable image content, not only a framed variable. Keep the content, variable label, and semantic border as separate objects so a thumbnail can be replaced without changing identity or topology.

Source: [Doumont, 2009](../references/README.md#doumont-2009).

## 8. Revise and redraw

The first visual idea is a starting point. Evaluate each proposal against the message, remove noise, correct ambiguous symbols, and redraw. Use one focused proposal when the visual brief is resolved, three directed proposals for a compact comparison, or five proposals for broad controlled exploration; every count preserves the same scientific contract.

Source: [Krzywinski, elements of visual style](../references/README.md#krzywinski-2013).

## 9. Separate object identity from mathematical definition

A visual object normally needs a short symbol or label, not its complete defining equation. Repeating full definitions inside states or modules increases density without adding structure. Put a full equation in separate whitespace only when the equation itself carries the main message; otherwise keep the definition in the manuscript text or caption.

Practical rule: if the same expression appears inside several visual objects, factor it into one definition or remove it from the canvas.

## 10. Separate scientific semantics from visual embodiment

An object's scientific identity and its drawn appearance are coupled but not interchangeable. The scientific contract fixes the object, relation, and forbidden implications. Sketch-semantic locks preserve deliberate glyph and spatial identity. A separate visual embodiment brief chooses only the remaining approved glyph detail, image anchor, asset source, and styling that make the object recognizable.

This follows the useful separation illustrated by [Penrose](https://github.com/penrose/penrose), where domain and substance declarations are distinct from style rules. Our workflow applies the idea more conservatively: changing an embodiment may improve visual intuition, but it may not change the scientific graph.

Practical rule: hide full equations temporarily. The reader should still recognize the main object types and process from visual anchors, short labels, and topology. If the diagram collapses into anonymous boxes, the embodiment is too abstract.

## 11. Separate visual exploration, editable assembly, and critique

Current open-source academic-figure projects repeatedly separate creative generation from structural assembly and quality review:

- [PaperVizAgent](https://github.com/google-research/papervizagent) exposes distinct retrieval, planning, styling, visualization, and critic roles;
- [NanaDraw](https://github.com/Shannon4Science/NanaDraw) distinguishes fast visual generation from structured editable assembly and reusable asset work;
- [AutoFigure-Edit](https://github.com/ResearAI/AutoFigure-Edit) uses labeled placeholders and reconstructs editable SVG outputs from a visual draft;
- [Scientific Illustrator](https://github.com/icebird1998/scientific-illustrator) prioritizes native editable objects and explicit designer/drawer/reviewer/corrector gates.

The local workflow adopts the common lesson, not the projects' full implementations: candidate images may explore visual form, but an approved contract, a semantic reconstruction pass, and a separate review pass control the deliverable. Scientific correctness cannot be delegated to visual plausibility.

## 12. Prefer domain glyphs and record asset provenance

Reusable domain-specific glyphs can communicate faster than generic boxes. [Bioicons](https://github.com/duerrsimon/bioicons) demonstrates an editable SVG asset library with per-icon licensing and attribution requirements. [DNAplotlib](https://github.com/VoigtLab/dnaplotlib) demonstrates a programmable domain vocabulary in which standardized biological parts remain customizable and produce vector output.

Use this hierarchy: native vector glyph, then licensed SVG, then a minimal user-provided or generated raster atom. Record every non-native asset in an asset manifest. A generated CT thumbnail may occupy a replaceable reconstructed-state slot, but its pixels remain a schematic placeholder and must never be described as measured data, ground truth, the method's actual reconstruction result, or quantitative evidence.

Practical rule: labels, borders, arrows, operators, and stage semantics stay native and separate from the asset pixels. Replacing the asset must not require reconstructing the diagram.

GitHub repositories in Sections 10–12 were reviewed on 2026-08-13 as workflow inspiration; they are not dependencies or scientific authorities for the local method.

## Compact checklist

Before accepting a figure, ask:

1. What single sentence should the reader understand?
2. Can the reading order be found without reading every label?
3. Does every object support the message?
4. Does every arrow have one unambiguous verb-like meaning?
5. Are standard or repeated elements collapsed?
6. Are related objects grouped by alignment, proximity, or shared form?
7. Does the most relevant relation receive the strongest visual emphasis?
8. Is color necessary, and if used, is it carrying scientific meaning rather than decoration?
9. Are equations and labels precise but minimal?
10. Can anything be removed without loss of meaning?
11. Is every visible prose phrase included in the approved prose budget?
12. Has an unsolicited title, footer, or caption-like explanation entered the canvas?
13. Under `sketch-bound` mode, do the candidates test distinct approved flexibility zones without changing the locked backbone; under `topology-exploratory` mode, do they contain at least three distinct macro-topologies?
14. Are repeated equations or modules factored out where scientifically safe?
15. Does any color encode a stated semantic role and remain secondary to structure?
16. If a colored palette is locked, is its rationale specific enough that it would need to change for an unrelated method figure?
17. If COLOR_NECESSITY is not none, does one restrained signature accent use reinforce the primary scientific relationship without becoming decoration?
18. If full equations are hidden, are the main object types and process still recognizable from visual anchors, short labels, and topology?
19. Does every image-valued state contain an honest visual anchor rather than an anonymous formula box?
20. Is every generated image explicitly treated as a replaceable schematic placeholder rather than data or evidence?
21. Are image pixels independent from variable labels, semantic borders, arrows, and connector geometry?
22. Does the asset manifest record source or generation status, license when applicable, placeholder status, SVG object ID, replacement target, and forbidden implication?
23. Does every locked sketch glyph preserve its silhouette, orientation, ports, and repeated-instance identity?
24. Is every mean or centroid representative computed from its member anchors rather than a card, column, label, or partial group?
25. Does every locked transition connector attach directly to its source and target and remain prominent without color or prose?
