# Contributing

Thank you for helping improve Sketch to Scientific Figure.

## Before opening a change

1. Keep scientific truth, visual exploration, and deterministic reconstruction separate.
2. Do not add private manuscripts, unpublished data, copyrighted reference PDFs, credentials, or local absolute paths.
3. Do not present generated pixels as data, ground truth, or a scientific result.
4. Keep changes focused and document any new runtime dependency.

## Local check

```bash
python3 -m venv /tmp/sketch-figure-contributor-venv
source /tmp/sketch-figure-contributor-venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

If your change affects SVG, PPTX, draw.io, or PDF delivery, also run the relevant adapter checks described in [docs/runtime_requirements.md](docs/runtime_requirements.md).

## Pull request notes

State:

- what scientific or workflow problem the change addresses;
- which files and artifact formats changed;
- which checks you ran and their results;
- whether any example assets have publication, license, or confidentiality constraints.

Human scientific sign-off remains required even when automated tests pass.
