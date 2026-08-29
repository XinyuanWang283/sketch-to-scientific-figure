# Architecture v2: truth-to-structurally-checked figure (legacy adapter)

> **Legacy reference, not the default user journey.** The current workflow starts with focused conversational clarification and exactly five active candidates from separate Codex built-in ImageGen calls; see the [README](../README.md) and [repository skill](../.agents/skills/sketch-to-scientific-figure/SKILL.md). This document describes the retained V2 deterministic compiler and validation architecture used for regression evidence after candidate approval or when explicitly requested.

## Decision

The canonical pipeline is:

```text
authoritative sources
  -> scientific_truth.json
  -> candidate_blueprint.json + validation_rules.json
  -> deterministic skeleton SVG/PNG + fingerprint lint
  -> optional externally created PNG candidate per blueprint
  -> exact-byte registration + review_result.json + human macro-layout/palette choice
  -> selected_candidate_map.json + svg_reconstruction_spec.json
  -> deterministic semantic SVG
  -> executable validation + human final sign-off
```

Candidate PNGs are disposable visual proposals. Scientific truth, blueprint topology, rules, reconstruction metadata, and semantic SVG remain canonical. The repository registers candidate bytes, SHA-256 values, operator-supplied call IDs, and Gate 1 bindings; it records generator provenance as operator-attested and not independently verified.

## Authority by stage

| Decision | Authority |
|---|---|
| entities, instances, counts, notation, equations, relations | `scientific_truth.json` |
| regions, semantic placement, ports, topology, rough geometry, depiction policy | candidate blueprint |
| structural reference supplied to image generation | deterministic skeleton |
| composition, hierarchy, palette, glyph appearance, whitespace | selected PNG, through selected-candidate map only |
| exact text, indices, centroids, ports, connector endpoints | truth + blueprint + reconstruction spec |
| pass/fail status | rule registry + executable validators |

The selected PNG never overrides truth or blueprint data. Whole-canvas tracing, raster wrapping, OCR recovery, and inferred connector reconstruction are prohibited.

## Artifact contracts

Schemas live under `schemas/`. The six P0 schemas cover scientific truth, candidate blueprint, validation rules, PNG review, selected-candidate map, and SVG reconstruction spec. All cross-stage references use stable IDs. A rule is defined once and referenced by the same `rule_id` in truth, blueprint, generation brief where visually necessary, review, SVG spec, and validator output.

The compiler rejects missing IDs, dangling truth/rule references, invalid proposal-mode counts, briefs outside 350–500 words, and insufficient multi-candidate fingerprints. Each current blueprint declares `literal_instances`, `representative_template`, or `multiplicity_badge`, including visible versus semantic scope and whether exact visible counts are required in PNG or SVG. The skeleton renderer expands semantic instance groups deterministically and calculates means/centroids from every displayed member anchor, but skeleton micro-repetition is not a PNG requirement under representative depiction.

## Candidate program

`directed-three` is the ordinary comparison default. Its three roles answer different questions:

1. sketch-faithful: can the sketch's spatial story be cleaned without changing its scientific topology?
2. mechanism-dominant: can the core scientific mechanism become the dominant reading path?
3. compact editorial: can the same truth fit publication scale with safe audit compression?

`focused-one` is appropriate when topology is fixed. `exploratory-five` is appropriate only when message or hierarchy remains unresolved. Multiple candidates must differ in at least three categorical fingerprint fields; palette and styling do not count.

## Human decision boundary

There are three confirmations: scientific story/wireframe, registered PNG macro-layout/palette, and final scientific acceptability. Discovery answers and validator results are evidence, not approvals. Gate 2 confirms the selected visual direction only; it does not approve candidate text, equations, counts, topology, connectors, or generator provenance.

## P0 implementation boundary

The repository implementation uses local files and declared Python dependencies. It does not add API providers, credentials, web services, databases, OCR, segmentation, tracing, or direct design-tool integration. It does not invoke or independently verify a PNG generator. When an operator creates candidates in a ChatGPT/Codex workspace, the runner can register their exact bytes and provenance attestation, but that record is not proof of generator identity.
