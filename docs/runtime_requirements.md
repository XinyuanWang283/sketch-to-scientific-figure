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

The publication-safe core replay is:

```bash
python scripts/run_synthetic_demo.py \
  --mode core \
  --output-dir /tmp/sketch-figure-core-demo-01
```

The output path must be outside the repository and must not already exist. The replay uses no AI, network, API key, or credentials and intentionally returns `INCOMPLETE` after the canonical semantic source and editable SVG are built.

## Full multi-format delivery

The complete synthetic full replay requires:

- Node.js plus `RUNTIME_NODE_MODULES` containing `@oai/artifact-tool/dist/artifact_tool.mjs` for native PPTX generation;
- an equation renderer: `latex` plus `dvisvgm`, or the local `mathjax-full` module;
- the declared Python dependencies used by the SVG, draw.io, PDF, and structural-validation paths.

System commands are discovered from `PATH`; the Node executable may also be supplied as `RUNTIME_NODE`. The repository does not contain a machine-specific runtime path. LibreOffice (`soffice`), Poppler commands, and Chromium are used by optional compatibility or visual-inspection helpers, but the synthetic full replay does not require them.

## Fidelity-v2 rebuild preflight

The optional Deep Image Prior fidelity-v2 rebuild has a stricter runtime than the frozen offline replay. It requires all of the following:

- `RUNTIME_NODE`, pointing to an executable Node.js binary;
- `RUNTIME_NODE_MODULES`, whose `@oai/artifact-tool/dist/artifact_tool.mjs` file is present;
- `latex` and `dvisvgm` for the nine colored vector equations;
- LibreOffice `soffice` for PPTX-to-PDF export;
- Poppler `pdftoppm` for the PNG preview and visual review evidence.

In a Codex workspace, ask Codex to resolve the bundled workspace dependency paths. Outside Codex, install equivalent local tools. Do not copy paths from another machine. Set the three environment-specific paths, then run this preflight from the repository root:

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

A successful full synthetic replay produces native PPTX and draw.io sources, SVG views, PDF exports/previews, a delivery manifest, and a cross-format report, then stops at Gate 3. Format labels remain narrow: Figma-ready SVG is `IMPORT_READY_UNVERIFIED`, PDFs have `semantic_editability=false`, and `VERIFIED` never means scientific correctness or automatic approval.

## Subscription boundary

An optional live assisted workflow may use image capability available in a ChatGPT/Codex workspace. The repository CLI does not call the OpenAI API, request an API key, invoke a candidate generator, or independently verify generator identity. Registered candidate provenance is operator-attested and not independently verified.

Installing dependencies can require network access when packages are not cached. Once the environment and native tools are installed, the synthetic `core` and `full` replay commands themselves do not execute AI or require network access.
