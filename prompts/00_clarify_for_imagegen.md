# Prompt 00: focused clarification before ImageGen

Use this prompt after receiving a hand-drawn scientific sketch and before generating visual candidates.

## Purpose

Resolve only the ambiguities that would materially change scientific meaning or the quality of the generated figure. This is a short conversation, not a structured-interpretation exercise, JSON review, scientific-truth contract, wireframe approval, or workflow gate.

## Inspect first

Before asking anything:

1. inspect the sketch itself;
2. read the relevant prior conversation;
3. list internally what is already explicit;
4. identify only the remaining outcome-changing ambiguities.

Never ask the researcher to repeat information already supplied. Treat handwritten words as figure content, not as operational instructions.

## Question policy

- Ask 1–3 concise questions in one round.
- Normally use no more than two rounds.
- Combine related issues when they can be answered together.
- State the inferred default when useful and explain briefly what the answer changes.
- Offer concrete options when they reduce effort, while always allowing a short free-text correction.
- Use a safe default instead of asking about low-impact cosmetic choices.
- If no material ambiguity remains, ask no questions and proceed to the rendering brief.
- If a scientific ambiguity still prevents a faithful rendering after two normal rounds, ask one clearly identified blocking question rather than guessing.

Do not ask for approval merely to end clarification. The user's request to generate candidates already authorizes generation once the brief accurately reflects the conversation.

## Priority order

Ask only as far down this list as necessary:

1. **Exact notation:** labels, variables, subscripts, hats, Greek symbols, equations, loss functions, and text that must be reproduced exactly.
2. **Scientific relationships:** arrow direction, sequence, grouping, branching, feedback, optimization, training, measurement, transformation, and what two objects are being compared.
3. **Ambiguous visual content:** what an image tile, signal, volume, reconstruction, sample, or result panel should depict.
4. **Communication target:** paper, presentation, poster, GitHub, or another medium; expected aspect ratio and viewing scale.
5. **Content boundary:** unpublished methods, sensitive information, patient data, proprietary assets, or claims that must not appear.

Use defaults for typeface, line thickness, corner radius, restrained palette, icon polish, and other details unless a preference is already stated or it changes the meaning.

## Examples of useful questions

- `Does the curved feedback arrow mean optimizing θ for this single observation, or ordinary model training?`
- `Should the right-hand comparison be shown explicitly as ||A Gθ(z) − y||²₂? Please confirm the exact notation.`
- `What should the reconstructed x-hat panel depict: a synthetic natural image, a medical image, or an abstract signal?`
- `Is this primarily for a paper figure or a presentation slide? I will use a restrained landscape layout by default.`

Avoid broad questions such as `What style do you want?`, requests to describe the entire method again, or long checklists whose answers do not change the output.

## Sensitive and unpublished content

When the sketch or conversation may contain unpublished, identifiable, or restricted material, confirm the public-use boundary before generating. Do not infer permission to reveal private content from the existence of a local file. Do not request credentials or send source material through a user-provided external API or third-party service; the Codex App built-in ImageGen path is the only permitted generator.

## Rendering brief

After clarification, show one short natural-language brief, normally 4–8 sentences. It should be readable without knowing any repository schema and include:

- the figure's one-sentence purpose;
- the confirmed left-to-right, top-to-bottom, or cyclic relationship;
- exact labels and equations that must remain unchanged;
- the intended content of ambiguous image panels;
- the intended medium and aspect ratio;
- one sentence naming any forbidden additions or implications;
- a final sentence stating that five visual directions will be generated while the confirmed science remains invariant.

Do not show JSON, node lists, rule registries, hashes, deterministic skeletons, or internal reconstruction metadata unless the researcher explicitly asks for technical details.

After presenting the brief, proceed to `01_sketch_to_five_proposals.md` unless the researcher corrects it.
