# Scientific Figure Workflow V3 architecture (legacy adapter)

> **Legacy reference, not the default user journey.** The default front door is sketch → focused clarification → five separate Codex built-in ImageGen proposal calls → explicit researcher choice → case-specific editable reconstruction. V3 remains available for deterministic fixture replay and an explicitly requested contract-driven run; its paper-aware Gate 1, wireframe, and pre-generation semantic contract are not Quick Start requirements.

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
optional external proposal step -> registered PNG candidates
              |
        Gate 2: registered visual direction
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

The repository does not independently establish which generator produced a registered PNG. A sketch-led run records the candidate as `operator_attested_candidate` with `provenance_assurance: operator_attested_not_independently_verified`, plus exact bytes, SHA-256, call ID, and Gate 1 bindings. Gate 2 is the researcher/operator's selection of that registered visual direction, not approval of the candidate's text, equations, topology, or provenance claim.

The public synthetic replay is a separate deterministic path. It executes no AI and uses checked-in fixture pre-approval records for Gates 1 and 2. Core mode stops `INCOMPLETE`; full mode runs the native adapters and structural checks, then stops awaiting an explicit Gate 3 decision.
