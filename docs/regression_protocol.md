# Regression protocol

## Purpose

Compare the historical monolithic sketch-to-PNG workflow with architecture v2 without modifying historical run directories. Each regression creates a new dated run and records source hashes, prompts, generated assets, review results, repair turns, validation reports, and limitations.

## Minimum comparison

Use the same authoritative scientific sources and the same method case for both arms.

- Baseline: old monolithic prompt, source sketch as the structural reference, and one independently recorded external generation event per candidate.
- V2: compiled short brief, candidate-specific deterministic skeleton as structural authority, and one independently recorded external generation event per candidate.

Do not use contact sheets or pass a prior candidate into the next call. Do not use API generation, OCR, segmentation, or tracing.

## Recorded metrics

For each arm and candidate, record:

- operator-recorded generation event, tool/context evidence when available, repository registration call ID, provenance assurance, and output SHA-256;
- first-generation pass/fail for every image-level blocking rule;
- regeneration count and local-style-edit count;
- topology/count/index/formula issues observed, even when non-blocking by policy;
- candidate selection status and researcher preference;
- human correction time only when actually measured.

Never infer correction minutes or preference. Use `not_measured` or `pending_human_selection` when evidence is absent.

Repository registration proves the in-run PNG bytes, hash, call ID, and Gate 1 bindings only. Its `operator_attested_not_independently_verified` provenance is not independent proof that a particular generator produced the candidate; any stronger comparison claim needs separate auditable evidence.

## Decision thresholds

- `ADOPT_NEW_ARCHITECTURE`: across at least three representative cases, v2 improves first-generation blocking pass rate or measured correction time without increasing scientific validator failures, and the researcher accepts the visual quality.
- `RETAIN_ARCHITECTURE`: across at least three representative cases, v2 materially underperforms or introduces new scientific failures after one permitted blueprint/skeleton revision.
- `INSUFFICIENT_EVIDENCE`: fewer than three cases, missing generation outputs, missing measured human correction time where needed, or no final researcher preference.

One successful case can validate the implementation and provide preliminary directional evidence. It cannot establish a general workflow improvement.

## Verification

Run unit tests, artifact validation, fingerprint lint, SVG mutation fixtures, XML parsing, and source-hash checks. Preserve all historical files and report the exact new run path.
