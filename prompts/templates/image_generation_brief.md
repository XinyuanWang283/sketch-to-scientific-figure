# Compiled image-generation brief template

This file is a compiler input pattern, not a place to paste the complete scientific contract. The compiled brief must contain 350–500 words.

```text
CANDIDATE
ID: {{candidate_id}}
Role: {{candidate_role}}
Visual question: {{comparison_question}}

REFERENCES
Image 1 is {{candidate_id}}_skeleton.png. Treat it as authoritative for major regions, stage order, rough placement, dominant hierarchy, and the core mechanism. Apply the blueprint depiction policy to visible repetition; skeleton micro-instance counts are not mandatory under `representative_template`. Do not copy its typography or final styling.
Image 2, when present, is style-only. It cannot change structure.

VISUAL MESSAGE
{{one_sentence_visual_message}}

DEPICTION POLICY
{{depiction_mode_and_visible_semantic_scope}}

IMAGE-LEVEL BLOCKERS
{{blocking_rules_with_rule_ids}}

ART DIRECTION
{{candidate_specific_composition_palette_glyph_whitespace_notes}}

TEXT POLICY
Allowed ordinary prose: {{ordinary_prose_allowlist}}.
Allowed short notation: {{notation_allowlist}}.
Do not render production equations, exact indices, legends, explanatory prose, or invented headings. These will be rebuilt as live SVG text.

OUTPUT
Produce one clean, flat, publication-style PNG candidate. Preserve the skeleton's macro-topology. No contact sheet, photorealism, shadows, gradients, decorative UI chrome, or whole-canvas title.
```
