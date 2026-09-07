# Runtime requirements

The repository has two execution levels. Use the smallest level needed for your task.

## Core checks

Required:

- Python 3.11 or newer;
- the declared Python package dependencies: Pillow, pypdf, and ReportLab.

Install and run:

```bash
python3 --version  # must report Python 3.11 or newer
python3 -m venv /tmp/sketch-figure-venv-01
source /tmp/sketch-figure-venv-01/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

The repository is a script- and Codex-skill workflow, not an importable Python package or installed console application. Installing `requirements.txt` avoids creating package metadata in the checkout. The core suite checks schemas, scientific-contract structure, topology skeletons, semantic SVG structure, gate enforcement, and the ordinary Python portions of the V3 workflow. These are programmable checks, not scientific validation.

The frozen Deep Image Prior v0.1 reference replay is:

```bash
python scripts/replay_reference_case.py replay \
  --output-dir /tmp/sketch-figure-reference-v0-1
python scripts/replay_reference_case.py validate \
  --run-dir /tmp/sketch-figure-reference-v0-1
python scripts/replay_reference_case.py status \
  --run-dir /tmp/sketch-figure-reference-v0-1
```

The output path must be outside the repository and must not already exist. These commands use no AI, network, API key, or credentials. The replay verifies the frozen five-candidate evidence, Candidate C selection, approved region map, validation-backed delivery, and visual approval; it does not create scientific correctness or fresh researcher approval.

## Fidelity-v2 rebuild preflight

The optional Deep Image Prior fidelity-v2 rebuild has a stricter runtime than the frozen offline replay. It requires all of the following:

- `RUNTIME_NODE`, pointing to an executable Node.js binary;
- `RUNTIME_NODE_MODULES`, whose `@oai/artifact-tool/dist/artifact_tool.mjs` file is present;
- `latex` and `dvisvgm` for the nine colored vector equations;
- LibreOffice `soffice` for PPTX-to-PDF export;
- Poppler `pdftoppm` for the PNG preview and visual review evidence.

The PPTX exporter imports the specific `@oai/artifact-tool/dist/artifact_tool.mjs` module from the Codex bundled runtime. A different presentation library is not a drop-in replacement. This repository does not provide a verified standalone installation recipe or replacement for that module; installing `requirements.txt` does not install it.

In a Codex workspace that provides bundled dependencies, ask Codex to resolve the actual Node.js and module paths. Availability depends on the environment. If that module is unavailable, use the frozen replay instead; rebuilding outside this bundled runtime is unverified. Do not copy paths from another machine. Replace all four placeholder paths below with resolved paths, then run this preflight from the repository root:

```bash
export RUNTIME_NODE=/absolute/path/to/node
export RUNTIME_NODE_MODULES=/absolute/path/to/node_modules
export SOFFICE_BIN=/absolute/path/to/soffice
export PDFTOPPM_BIN=/absolute/path/to/pdftoppm
"$RUNTIME_NODE" --version
test -f "$RUNTIME_NODE_MODULES/@oai/artifact-tool/dist/artifact_tool.mjs"
command -v latex
command -v dvisvgm
"$SOFFICE_BIN" --version
"$PDFTOPPM_BIN" -v
```

Only after every command succeeds, rebuild into a new directory outside the repository:

```bash
python scripts/build_deep_image_prior_c_fidelity_v2.py \
  --soffice "$SOFFICE_BIN" \
  --pdftoppm "$PDFTOPPM_BIN" \
  --output-dir /tmp/sketch-figure-fidelity-v2-rebuild-01
```

The builder refuses an existing output directory. This rebuild is case-specific, may produce structurally equivalent but byte-different PPTX/PDF archives, and does not inherit the canonical visual approval. If any preflight item is unavailable, use `scripts/replay_reference_case.py replay`; that is the stable Science Day path and needs none of these native tools.

When the bundled presentation runtime is unavailable, the unit test that exercises the entire adapter chain is skipped. That skip means the core workflow was checked, not that every delivery format was regenerated on that machine.

A successful fidelity-v2 rebuild produces the case-specific SVG, native PPTX, experimental structural draw.io view, PDF preview/export, manifests, validation reports, and preview. It does not inherit the frozen visual approval. Format labels remain narrow: PDFs have `semantic_editability=false`, and `VERIFIED` never means scientific correctness or automatic approval.

## Subscription boundary

An optional live assisted workflow may use image capability available in a ChatGPT/Codex workspace. The repository CLI does not call the OpenAI API, request an API key, invoke a candidate generator, or independently verify generator identity. Registered candidate provenance is operator-attested and not independently verified.

Installing dependencies can require network access when packages are not cached. Once dependencies are installed, the frozen v0.1 validate, replay, and status commands execute no AI or network calls.
