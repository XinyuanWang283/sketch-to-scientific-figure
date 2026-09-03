# sketch-to-scientific-figure technical reference

## Scope

Version 0.1 is a reusable, repository-scoped Codex workflow with approval records, case-specific region-aware reconstruction tools, and one verified reference case. It is not a universal sketch-to-editable-figure converter and provides no evidence of cross-sketch generalization.

The current workflow is:

```text
researcher sketch
→ focused Codex clarification
→ five separate built-in ImageGen calls
→ five active A–E candidates
→ one exact researcher-approved candidate
→ approved region map
→ case-specific native reconstruction
→ structural validation
→ separate researcher decisions
```

The live path uses the built-in image-generation capability only when the Codex environment exposes it. It requires no repository-managed or user-supplied `OPENAI_API_KEY`. Repository Python does not call ImageGen.

## Responsibility boundary

| Component | Responsibility |
|---|---|
| Codex / ImageGen | Ask material questions and propose visual candidates |
| Researcher | Correct scientific meaning and approve one exact candidate and region map |
| Reconstruction code | Build case-specific SVG, PPTX, draw.io, and PDF artifacts |
| Automated validation | Check hashes, files, paths, objects, and programmable topology constraints |
| Researcher | Decide visual quality, scientific correctness, Science Day use, and public release |

Automated validation never establishes scientific correctness or creates a human approval.

## Proposal contract

The initial active proposal set contains exactly five slots:

- A — Faithful
- B — Publication
- C — Presentation
- D — Alternative layout
- E — Visual variant

Each slot comes from a separate built-in ImageGen call using the same sketch and clarified brief plus one direction-specific suffix. “Separate” describes distinct generation calls; it is not a claim of statistical independence.

Each candidate record contains a mandatory repository-local `generation_event_id`, relative file path, SHA-256, slot, concise design note, timestamp, and provenance status. A native tool-call ID is optional and may be recorded only when the tool exposes it. Repository code verifies the records and files but does not independently prove the backend generator identity.

Events are append-only. A single-slot regeneration adds a superseding generation event and preserves the old event. A request to combine layout or style ideas is treated as a new generation brief, not as a reconstructable selection. Codex must first generate and register a new candidate image; the researcher then approves that exact file. A material change to the scientific brief or overall direction starts a new five-candidate run.

## Exact selection and region-map boundary

Editable reconstruction requires approval of one exact active candidate. The selection binds:

- case or run ID;
- slot and candidate ID;
- active generation event;
- candidate SHA-256;
- operator and timestamp;
- approval provenance.

The next authority is `source/selected_candidate_map.json`. It binds every major visual region to the selected-candidate hash and records source-pixel bounds, semantic role, conversion mode, scientific overrides, visual properties, and output object IDs.

Reference crops are inspection inputs and use `reference_only_not_embedded`. They do not become delivery media. A bounded candidate crop may become a raster atom only after a separate researcher decision approves the exact candidate hash and source-pixel box. Such an atom must contain no baked-in label, equation, border, arrow, connector, legend, or scale-bearing mark; it remains independently replaceable and is recorded in `source/asset_manifest.json`.

The region map and every raster exception require explicit approval before reconstruction. Hard-coded geometry must not silently bypass this stage.

## Reconstruction boundary

The reconstruction is case-specific. It creates new native objects from approved inputs rather than tracing or embedding the full candidate.

### Scientific authority

- The sketch, clarification, exact typed material, and researcher corrections control scientific meaning, labels, equations, topology, grouping, and directions.
- The approved candidate controls composition, hierarchy, palette, glyph character, whitespace, and rhythm.
- Reconstruction metadata controls stable IDs, ports, object groups, geometry, and cross-format mappings.

### Equations

Authoritative LaTeX is retained in `source/equations.tex` and bound to rendered objects through `source/equation_manifest.json`. When native semantic equation support is unavailable, equations may be stored as intrinsic-aspect vector objects. These objects are scalable and movable but are not semantically editable LaTeX. Anisotropic stretching is rejected.

### Gradients

Native SVG and PPTX gradients are allowed when they are part of the approved visual direction and remain editable. They may not be the only carrier of a scientific distinction. Unsupported filters, scripts, animation, remote resources, and fragile effects are excluded.

### Raster atoms

The permitted raster identities and count come from the approved asset manifest, not from a universal number. Each atom records its relative path, MIME type, dimensions, byte length, SHA-256, semantic role, scientific status, placement, and provenance. SVG sidecars remain below `delivery/svg/assets/`. Absolute references, path traversal, symlink escape, missing sidecars, unmanifested images, and whole-canvas candidate embedding are errors.

## Format support

| Format | v0.1 support boundary |
|---|---|
| SVG | Native/vector master, live text where supported, vector equation objects, and only approved relative raster sidecars |
| PPTX | Independent native shapes, text, curves, equation objects, connectors, and approved replaceable picture objects |
| draw.io | Editable graph cells, labels, and directed edges; visual rendering remains experimental for the reference case |
| PDF | Export or preview; no semantic-editability claim |

Figma compatibility is not claimed without a real import smoke test showing that representative objects can be edited independently.

## Validation and delivery registration

A machine-readable structural report binds the case ID, delivery revision, selected-candidate hash, approved region-map hash, artifact manifest, output hashes, individual checks, overall result, and validator identity or code revision.

Delivery registration fails closed when:

- the validation report is missing or failed;
- the report belongs to another case or revision;
- the candidate or region-map hash differs;
- an output hash differs from the artifact manifest;
- a required object, label, edge, or region mapping is missing;
- an unapproved raster or whole-canvas image appears;
- an absolute path, traversal, or symlink escape is detected.

Structural checks can cover parse validity, native object structure, required labels, nodes, groups, edge direction, disconnected components, orphans, raster containment, equation aspect ratio, and implemented cross-format consistency. The report must state which checks were actually run.

## Offline reference replay

[`scripts/replay_reference_case.py`](../scripts/replay_reference_case.py) is the deterministic offline entrypoint. It verifies the frozen input sketch, A–E candidate records, Candidate C selection, region-map approval, raster authorization, validation report, artifact manifest, exact output hashes, and visual approval before copying the reference evidence into a new external run.

```bash
python scripts/replay_reference_case.py replay \
  --output-dir /tmp/sketch-figure-reference-v0-1
python scripts/replay_reference_case.py validate \
  --run-dir /tmp/sketch-figure-reference-v0-1
python scripts/replay_reference_case.py status \
  --run-dir /tmp/sketch-figure-reference-v0-1
```

Replay performs zero ImageGen or remote calls. It does not simulate a new researcher interaction or create scientific, Science Day-use, or public-release approval. The local ledger is consistency-checked, not cryptographically tamper-proof without an external signed anchor.

## Verified Deep Image Prior case

The active case record is [`examples/deep_image_prior/reference_case_v0_1.json`](../examples/deep_image_prior/reference_case_v0_1.json). The canonical delivery is [`editable_delivery_c_fidelity_v2/`](../examples/deep_image_prior/editable_delivery_c_fidelity_v2/README.md).

For this case only, the evidence records:

- one original explanatory sketch and a focused clarification brief;
- five operator-attested ImageGen candidates with hashes and generation events;
- exact selection of Candidate C;
- an approved eight-region map;
- two approved, unresampled, replaceable synthetic raster atoms;
- native/vector reconstruction of the remaining structure;
- nine intrinsic-aspect LaTeX-derived vector equations;
- native SVG/PPTX gradients and two editable synthetic curves;
- a structurally editable but visually experimental draw.io artifact;
- a PDF preview/export;
- structural validation and a visual approval bound to the artifact-manifest hash.

The checked-in governance fields preserve the frozen pre-authorization snapshot. The annotated `v0.1.0` tag is a separate owner attestation bound to its exact release tree. Neither record generalizes to later changes or other cases.

## Repository resources

- [Current Skill](../.agents/skills/sketch-to-scientific-figure/SKILL.md)
- [Focused clarification prompt](../prompts/00_clarify_for_imagegen.md)
- [Five-candidate prompt](../prompts/01_sketch_to_five_proposals.md)
- [Editable reconstruction prompt](../prompts/02_selected_proposal_to_svg.md)
- [Reference-case evidence](../examples/deep_image_prior/reference_case_v0_1.md)
- [Asset provenance and licensing boundaries](../ASSETS.md)
- [Runtime requirements](runtime_requirements.md)

Historical V2/V3 contracts and complete superseded delivery packages remain available in the immutable `v0.1.0` release history. They are not current execution instructions.

## Known limitations

- Only one reference case has been verified.
- Built-in ImageGen availability depends on the Codex environment.
- ImageGen may change notation, omit elements, or produce misleading arrows; human review is mandatory.
- Reconstruction is case-specific and still requires engineering judgment.
- Visual similarity, object editability, topology consistency, and scientific correctness are separate properties.
- Raster atoms are replaceable but not internally vector-editable.
- draw.io visual fidelity is experimental for the reference case.
- PDF is not an editable source.
- No formal human user study, time-saving benchmark, universal fidelity threshold, cross-platform guarantee, or generalization claim is provided.
