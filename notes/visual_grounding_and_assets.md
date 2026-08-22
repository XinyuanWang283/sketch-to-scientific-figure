# Visual grounding and hybrid asset rules

Load this note when a scientific entity is easier to understand as an image, domain glyph, geometry, trace, strip, material object, or other content-bearing visual anchor. The runtime scientific contract remains authoritative.

## Three-layer contract

Keep these layers separate:

- **Scientific locks** state what is true: entities, counts, topology, direction, grouping, stages, invariant and varying components, exact notation, and forbidden implications.
- **Sketch semantic locks** preserve the scientifically valid glyph silhouette, ports, spatial center, transition path, or salience that the researcher encoded in the hand sketch.
- **Visual embodiment** states how approved truths become recognizable: thumbnails, domain glyphs, traces, strips, geometric cues, schematic shapes, labels, and presentation states.

Visual embodiment may vary inside the approved `allowed_stylization` and FLEXIBILITY ZONES. It may not add or change a scientific claim or replace a locked sketch feature.

## Visual-anchor test

For each entity, decide whether a content-bearing anchor improves comprehension.

Use one when it helps the reader identify the entity class before reading notation, for example:

- an image state shown by a schematic image thumbnail;
- a sampled signal shown by a short trace or strip;
- a view-dependent acquisition shown by a minimal geometry or angle glyph;
- a spatial domain shown by a quiet two-dimensional region;
- a material or apparatus shown by a restrained domain-specific silhouette.

Stay with notation or a simple module when the entity is abstract, when a glyph would be speculative, or when the visual adds no decoding value.

Never add an icon only because an empty area looks plain. Every visual anchor must answer: what scientific distinction becomes faster or safer to decode because this object is present?

## Image-state construction

Treat an image state as a semantic composite:

```text
image content + exact variable label + status border + connectors
```

Keep these parts independent. Image content conveys the object class; notation identifies the exact quantity; the border conveys temporary/final or another contracted state; connectors convey supported functional relationships.

For repeated image states:

- use one coherent content family, crop, orientation, tonal range, and visual scale;
- vary only the dimension named in `VARYING COMPONENTS`;
- do not imply improvement with unsupported sharpening, denoising, contrast gain, or added detail;
- do not imply averaging with blur, ghosting, or superposition unless the method averages images;
- keep labels and border styles outside the pixels.

## Asset modes

Use the first adequate mode:

1. `native-vector` — constructed from ordinary SVG primitives and live text;
2. `licensed-svg` — project-owned or third-party vector with source, revision, author, license, attribution, and modification records;
3. `user-provided` — a minimal raster atom with ownership, scientific status, privacy confirmation when relevant, and checksum;
4. `generated-placeholder` — a minimal schematic raster atom with generator provenance, explicit non-evidentiary status, and a publication release policy.

A licensed SVG is sanitized and inlined as vector geometry. Do not embed it as an SVG image data URI. A raster asset is embedded in the canonical source SVG for portability and kept as an identical sidecar for replacement and integrity checks.

## Generated-placeholder boundary

A generated placeholder can help a reader recognize an image-valued or contextual state. It is not scientific evidence.

Required status:

```text
scientific_status: non-evidentiary-schematic
release_policy: replace-before-publication
```

The researcher may explicitly change the release policy to `approved-schematic` after review. A generated atom may denote the object class or role of a reconstructed state, including an approved \(\hat x_t\) slot, but never silently promote its pixels to acquired data, ground truth, the method's actual reported reconstruction, a diagnostic example, or a quantitative result.

Generated medical imagery must be phantom-like or clearly illustrative. It must not contain patient identity, unsupported lesions, diagnostic claims, or a realistic clinical presentation that could be mistaken for data. Real sensitive imagery requires user-confirmed de-identification and provenance.

## Generated asset materialization

After layout selection and before SVG assembly, resolve every approved generated placeholder to an actual standalone asset or a coherent asset-only family. The generated pixels contain image content only; variable labels, borders, arrows, operators, legends, colorbars, scale bars, and stage text remain native SVG objects. Do not crop these atoms from a rendered layout proposal.

Save one exact PNG or JPEG sidecar per approved asset id, visually inspect every atom against its recognition target and forbidden implications, and regenerate anything misleading. Record the real generator/version, date, prompt hash, optional seed, checksum, dimensions, and placement. General approval of generated placeholders is not review of the actual pixels, so keep `human_reviewed: false` until the researcher sees that exact asset. If generation fails, use a contract-permitted native-vector fallback or report the missing asset; never invent content or provenance.

## Measurement fidelity

Match the glyph to the contracted unit:

- a single view is not automatically a full sinogram;
- a detector readout is not automatically a dataset;
- a sample set is not automatically a matrix;
- predicted and measured quantities must remain distinct when the contract distinguishes them;
- multiple views must not be averaged, merged, discarded, or duplicated unless the method says so.

When a forward operator depends on view, pair the exact operator label with a minimal view-angle or acquisition glyph only if the glyph clarifies that dependence.

## SVG editability contract

Keep the source SVG canonical and, when non-native assets are present, treat its manifest as part of that canonical source. A raster atom is replaceable, not internally vector-editable.

For each approved raster slot:

- one semantic `<g>` group;
- one `<image>` content object;
- one independent border object;
- one independent exact label;
- independent connectors;
- one sidecar PNG or JPEG;
- one manifest entry with stable ids, checksums, dimensions, provenance, scientific status, privacy status, license fields, and replacement geometry.

Do not put equations, labels, arrows, borders, legends, colorbars, scale bars, or an entire panel inside a raster atom. Do not use `<symbol>/<use>` for independently replaceable raster slots.

## Formula-hidden comprehension test

Ignore every full equation and inspect only the visual anchors, short labels, grouping, and connections. Keep short labels when they distinguish predicted from measured quantities or preserve indexed correspondence. The reader should still recover:

- the VISUAL MESSAGE;
- the major entity classes;
- required counts, stages, or branches;
- the principal reading direction;
- the main functional relations;
- invariant versus varying structure.

Failure means the visual embodiment is too weak or the layout is carrying mathematics instead of scientific storytelling. Repair the anchor or topology before adding prose.

## Final checks

- Every non-native asset is approved and manifested.
- Every raster data URI matches its sidecar checksum, byte length, MIME type, and pixel dimensions.
- Every asset obeys its forbidden visual implications.
- No private absolute path or patient identifier enters the SVG or manifest.
- When a raster slot exists, labels, borders, and connectors remain unchanged when a test thumbnail replaces its content.
- The figure remains readable at intended paper size and in grayscale.
- Figma compatibility is called `verified` only after the applicable Prompt 02 smoke test passes: raster-slot replacement when a raster exists, or independent vector and live-text editing for an all-vector figure.

Figma import is a derivative editing path. The source SVG, plus the manifest when present, remains canonical because an editor round trip may not preserve ids, classes, `data-*` attributes, or metadata.
