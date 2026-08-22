# Runtime requirements

The repository has two execution levels. Use the smallest level needed for your task.

## Core checks

Required:

- Python 3.11 or newer;
- Pillow 10 or newer.

Install and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
```

The core suite validates schemas, scientific contracts, topology skeletons, semantic SVG structure, and the ordinary Python portions of the V3 workflow.

## Full multi-format delivery

The complete V3 adapter path also expects:

- Node.js and the Codex bundled presentation modules for native PPTX generation;
- a TeX engine for authoritative equation rendering;
- LibreOffice (`soffice`) for conversion and compatibility checks;
- Poppler commands such as `pdftoppm`, `pdfinfo`, and `pdfimages` for PDF rendering and inspection;
- a Chromium-based browser for selected visual checks.

These commands are discovered from `PATH`. The repository does not contain a machine-specific runtime path.

When the bundled presentation runtime is unavailable, the unit test that exercises the entire adapter chain is skipped. That skip means the core workflow was checked, not that every delivery format was regenerated on that machine.

## Subscription boundary

The guided image-generation stage is intended to run through the image capability available in a ChatGPT/Codex workspace. The repository does not call the OpenAI API and does not request an API key.
