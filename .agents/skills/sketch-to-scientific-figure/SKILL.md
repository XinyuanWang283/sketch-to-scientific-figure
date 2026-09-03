---
name: sketch-to-scientific-figure
description: Use when a researcher wants Codex to clarify a hand-drawn scientific sketch, make five separate built-in ImageGen calls, and reconstruct one explicitly approved candidate as editable scientific figure files.
---

# Sketch to Scientific Figure

## Product boundary

> Codex proposes; reconstruction tools transform; automated checks inspect programmable constraints; the researcher decides.

Version 0.1 is a reusable Codex workflow plus one verified reference case. It is not a universal sketch converter and does not guarantee reconstruction quality for an arbitrary sketch.

The current workflow is:

```text
hand-drawn sketch + prior conversation
→ focused clarification
→ five active A–E candidates from five separate built-in ImageGen calls
→ researcher approves one exact candidate
→ researcher-approved region map
→ case-specific editable SVG/PPTX reconstruction
→ experimental structural draw.io + PDF preview/export
→ automated structural validation
→ separate researcher decisions
```

Clarification is a short conversation, not a structured-interpretation form or approval gate. ImageGen candidates are visual proposals, not scientific evidence. Automated validation does not prove scientific correctness and never creates human approval.

## Current execution contract

### 1. Inspect before asking

Read `../../../prompts/00_clarify_for_imagegen.md`. Inspect the sketch and relevant prior conversation before asking anything. Ask only questions whose answers materially change scientific meaning or visual direction, normally 1–3 questions per round and no more than two rounds.

Prioritize exact notation, arrow direction, feedback or comparison meaning, ambiguous image content, intended medium, and restricted-content boundaries. Use safe defaults for cosmetic details. When the material ambiguities are resolved, show one compact natural-language rendering brief; do not require the researcher to review JSON.

### 2. Generate five candidates through five separate calls

Read `../../../prompts/01_sketch_to_five_proposals.md`. Make one built-in ImageGen call for each initial slot:

- **A — Faithful:** polish the recognizable sketch layout.
- **B — Publication:** use restrained paper-figure composition.
- **C — Presentation:** strengthen hierarchy and distance legibility.
- **D — Alternative layout:** change composition without changing confirmed science.
- **E — Visual variant:** change palette and graphical language without changing confirmed science.

Each call receives the same sketch and clarified brief plus only its direction suffix. Do not claim statistical independence, use one candidate as another candidate's reference, or ask ImageGen to create the contact sheet. Assemble a comparison sheet locally only after five original files exist.

Each event needs a repository-local `generation_event_id`, file path, SHA-256, slot, design note, timestamp, and honest provenance status. Record a native tool-call ID only when the tool exposes one; never invent it. Preserve every event append-only.

The initial active proposal set has exactly A–E. A single-slot revision creates a new ImageGen output and appends a superseding event for that slot. A request that combines ideas across candidates is a new visual brief, not an approved combination: generate and show a new candidate in a new run or a clearly superseding slot event before selection. If the scientific brief or overall direction changes materially, start a new five-candidate proposal run. Never reconstruct an unrendered verbal combination.

### 3. Record one exact approved candidate

Show A–E with short direction labels. The researcher may select one, request a revision, reject the set, or use two candidates to describe a new generation request. Editable reconstruction begins only after the researcher approves one exact candidate file.

Bind selection to the candidate slot, candidate ID, SHA-256, active generation event, operator, timestamp, and approval provenance. Selection and approval remain distinct while any requested revision is pending.

### 4. Map regions before reconstruction

Read `../../../prompts/02_selected_proposal_to_svg.md`, the exact selection record, and the latest source and validation report for the case. Create a hash-bound `source/selected_candidate_map.json` before drawing. It records each major region, source-pixel box, conversion mode, scientific overrides, visual properties, and native output IDs.

Use:

- the sketch, clarification, and explicit corrections for scientific meaning, exact text, equations, and topology;
- the approved candidate for composition, hierarchy, palette, glyph character, whitespace, and rhythm;
- reconstruction metadata for stable IDs, ports, groups, and cross-format mappings.

Codex may draft the region map, but reconstruction must not continue until the researcher explicitly approves its topology and any proposed raster exceptions in a separate hash-bound record.

Reference crops are QA inputs marked `reference_only_not_embedded`. Never embed the candidate as a whole canvas. A bounded crop may become an independently replaceable raster atom only when the researcher explicitly approves that exact candidate hash and source-pixel box, the crop contains no baked-in scientific label, equation, border, arrow, legend, or scale-bearing mark, and the asset manifest records its provenance and checksum.

### 5. Reconstruct supported formats

Create newly constructed native objects rather than tracing pixels:

- SVG: native geometry, live text where appropriate, vector equation objects, semantic IDs, and relative sidecars for approved raster atoms.
- PPTX: independent shapes, text, curves, equation objects, and replaceable picture shapes where explicitly approved.
- draw.io: editable graph cells and directed edges; describe it as an experimental structural view until an official render is checked.
- PDF: export or preview only.

Retain authoritative LaTeX source. A vector-path equation is visually scalable but is not semantically editable LaTeX. Native gradients are allowed when they are part of the approved visual direction and remain editable; gradients are not a scientific encoding by themselves.

### 6. Validate, then return control

Validate candidate and region-map hashes, path containment, manifest bindings, parseability, native object structure, required labels, required directed relationships, region-to-output coverage, raster-atom authorization, and cross-format consistency where implemented. Reject absolute paths, path traversal, symlink escape, unapproved raster content, whole-canvas candidate images, and delivery registration without a passing machine-readable validation report.

Report exactly what was checked. Do not call structural checks scientific validation. Final visual, scientific, Science Day-use, and public-release decisions remain explicit human actions bound to the artifacts they cover.

## Hard boundaries

- Use only the Codex App built-in image-generation capability for the live path. Do not request an API key, call the OpenAI Image API, or pretend repository Python invokes ImageGen.
- Built-in ImageGen availability depends on the Codex environment. The offline reference replay does not call ImageGen, a network service, or an external model.
- Do not invent measurements, results, claims, patient imagery, experimental evidence, provenance, model names, seeds, or tool-call IDs.
- Do not expose unpublished, identifiable, proprietary, or otherwise restricted content without explicit researcher authorization.
- Do not mechanically trace or flatten the approved candidate.
- Do not describe the PDF as editable or the draw.io artifact as visually faithful without corresponding evidence.
- Do not describe automated validation as scientific correctness, visual approval, or publication approval.

## Verified reference case

`examples/deep_image_prior/editable_delivery_c_fidelity_v2/` is the frozen Candidate C reference package. It binds an eight-region map to the selected candidate hash, uses exactly two approved replaceable synthetic raster atoms, and reconstructs the remaining structure with native/vector objects, editable gradients, reference-fitted synthetic curves, and intrinsic-aspect LaTeX-derived equations. Its draw.io output is structurally editable but visually experimental; its PDF is preview/export only.

The offline replay is `../../../scripts/replay_reference_case.py`. It verifies and copies frozen evidence; it does not rerun ImageGen or grant new approvals. The checked-in governance records preserve their original snapshot state. Release-level owner attestations, when applicable, are separate records bound to a particular Git tree.

## Resources

- `../../../prompts/00_clarify_for_imagegen.md` — focused clarification and rendering brief.
- `../../../prompts/01_sketch_to_five_proposals.md` — five A–E candidates from separate built-in ImageGen calls.
- `../../../prompts/02_selected_proposal_to_svg.md` — exact-candidate region mapping, native reconstruction, and validation.
- `../../../docs/technical_reference.md` — current architecture, evidence, and support boundaries.
- `../../../ASSETS.md` — asset provenance and licensing boundaries.

Historical V2/V3 contracts are preserved in the immutable `v0.1.0` release history. They are not instructions for the current Skill and must not be loaded unless the researcher explicitly requests historical inspection.
