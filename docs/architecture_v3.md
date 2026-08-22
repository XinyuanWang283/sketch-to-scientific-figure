# Scientific Figure Workflow V3 architecture

V3 keeps the V2 scientific-truth, visual-plan, PNG-candidate, semantic-SVG, and executable-validation layers. It adds a paper-aware editorial layer before visual production, a resumable three-gate state machine, LaTeX-first equations, one canonical semantic source, and independent delivery adapters.

The Visual Plan is an executable input to Gate 1, not background documentation. Sketch mode binds `visual_plan.json`, an approved wireframe SVG, and its approved PNG preview before the editorial builder runs. The exact approved wireframe is snapshotted and preserved. Paper-aware alternatives share that geometry and may add only an independent `paper-aware-overlay`; they cannot synthesize a replacement macro-layout.

```text
paper + method + truth + sketch
              |
              v
paper-aware editorial review + redline + wireframes
              |
        Gate 1: story / wireframe
              |
              v
built-in image generation -> PNG candidates
              |
        Gate 2: visual direction
              |
              v
semantic_figure.json + equations.tex
    |          |          |          |
   SVG       Figma       PPTX      draw.io + PDF
    \          |          |          /
             cross-format validation
                      |
        Gate 3: final scientific delivery
```

The arrows from the canonical source to adapters are independent: no adapter treats another delivery file or the PNG candidate as its semantic input. Stable IDs, bounding boxes, connector endpoints, equation IDs, and provenance make cross-format comparison executable.
