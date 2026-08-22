# Sketch fidelity and spatial-lock rules

Load this note whenever a hand-drawn mark carries a deliberate scientific identity, internal geometry, relative position, grouping center, transition path, or visual priority. The method text and authoritative equations still define what is scientifically true.

## Authority order

Use four layers in this order:

1. **Scientific authority** — current equations and explicit method statements define entities, relations, directions, counts, and meanings.
2. **Approved sketch-semantic locks** — scientifically valid hand-drawn glyphs and spatial relations define how those truths must remain recognizable.
3. **Macro-layout blueprint** — arranges unlocked regions and may move a locked cluster as one unit.
4. **Presentation style** — line cleanup, typography, restrained color, and local spacing.

If the sketch conflicts with scientific authority, record the exact override in the contract. Otherwise, do not call a deliberate glyph or spatial relation “rough” merely because it is hand drawn.

## Contract schema

Under `SKETCH SEMANTIC LOCKS`, record every deliberate sketch feature that would change meaning or the researcher's mental model if it were replaced or moved.

```yaml
FIDELITY_MODE: <sketch-bound | topology-exploratory | controlled-mixed>
SKETCH_SEMANTIC_LOCKS:
  - lock_id: <stable id>
    scope: <all-candidates | sketch-faithful-candidate | named candidate ids>
    source_region: <plain description of the sketch location>
    entity_or_relation: <contract entity or relation>
    lock_type: <glyph-silhouette | glyph-ports | relative-placement | group-membership | group-centroid | stage-transition | salience-hierarchy | reading-order>
    must_preserve: <observable property>
    allowed_cleanup: <line, spacing, scale, or alignment changes that preserve meaning>
    forbidden_deviation: <substitutions or movements that would violate the lock>
    verification: <a visual or geometric pass condition>
    scientific_override: <none, or the exact authoritative correction>
FLEXIBILITY_ZONES:
  - <what may change without altering any lock>
```

Default to `sketch-bound` when the researcher supplied a deliberate pipeline, architecture glyph, stage arrangement, or spatial story. Use `topology-exploratory` only when the researcher explicitly requests broader rearrangement or confirms that the macro-layout is disposable. Use `controlled-mixed` when the researcher explicitly asks the candidate set to include both a method-first narrative exploration and a sketch-faithful spatial interpretation. Approval of “visual flexibility” by itself does not unlock semantic glyphs or spatial locks.

Every lock has an explicit scope. Scientific identity, exact grouping, computed representative positions, directed transitions, and any glyph the researcher identifies as semantically meaningful normally use `all-candidates`. A broader sketch macro-layout may use `sketch-faithful-candidate` in `controlled-mixed` mode so the faithful candidate preserves it exactly while the other candidates may rearrange whole locked clusters. Never narrow a lock's scope merely to make candidate diversity easier.

Do not create locks for accidental pen wobble, page margins, handwriting style, or a scientifically unsupported mark. When intent is unclear and the answer could change topology or a semantic lock, ask the researcher before rendering.

## Lock types

### Glyph silhouette

Use this when the shape itself identifies an entity class or matches the researcher's established vocabulary.

Allowed cleanup can include smoother edges, consistent stroke weight, proportional scaling, and translation. It cannot include replacing the glyph with a circle, pill, badge, card, header rail, hub, generic icon, or another module silhouette unless the contract explicitly permits that substitution.

### Glyph ports

Lock the meaningful input and output sides of a module. A module may move as one object, but its incoming and outgoing connections may not silently swap sides, attach to decorative corners, or pass through an unrelated object.

### Relative placement and locked clusters

Several marks may form one semantic cluster. The blueprint may translate or uniformly scale the cluster and may adjust safe internal whitespace, but it must preserve its internal reading order, adjacency, alignment, and port relationships.

Moving a whole cluster is a layout change. Rearranging the members inside a locked cluster is a scientific or sketch-semantic change and requires approval.

### Group membership

Every brace, band, enclosure, or repeated alignment must cover the exact contracted members. A group mark that extends into a neighboring bin or leaves out a member is a hard error even if the labels are correct.

### Group centroid

Use this lock when the method defines a representative as a mean, centroid, temporal center, or another exact center of its members.

Let the displayed member-anchor positions be (p_t). Place the representative at

\[
p_{\mathrm{rep}}
=
\frac{1}{|\mathcal B|}
\sum_{t\in\mathcal B} p_t.
\]

For a one-dimensional straight path, this means the representative's path coordinate is the arithmetic mean of the member coordinates. For equally spaced members it lies at the center of the complete group; it may fall between two beads. Do not snap it to the nearest member, the first half of the group, a label column, or the geometric center of a surrounding card. Compute it from the member anchors, not from container bounds.

If the scientific representative is not a mean or center, do not apply this rule automatically. Record the correct placement rule instead.

### Contracted stage transitions

A stage transition is a directed scientific relation, not a decorative schedule line.

- connect the preceding stage's final weight or training-state anchor directly to the next stage's initialization or generator anchor;
- preserve the exact forward direction and adjacent-stage order;
- keep the connector continuous, unambiguous, and visually attached at both ends;
- place its exact short equation or approved symbol adjacent to the connector when needed;
- do not terminate only on a stage heading, page margin, background rail, image output, or unrelated card;
- do not let a header line, subtle bracket, or low-contrast accent carry the relation alone when the contract marks the transition as central.

When the authoritative method says optimizer state is also carried, record that fact without inventing an undefined variable. The caption may state the additional training-state detail if the canvas has no approved compact notation.

### Salience hierarchy

Lock a relation's priority when the sketch or one-sentence message makes it part of the main story. A primary relation must remain among the first visual elements noticed through position, scale, directness, whitespace, or line strength. Color may reinforce salience but cannot be its only carrier.

## Layout diversity boundary

Every candidate must preserve every approved sketch-semantic lock whose scope includes that candidate, and every candidate must preserve all `all-candidates` locks. “At least one sketch-faithful candidate” means one candidate also keeps the sketch's broader macro-layout; it does not give the other candidates permission to replace universally locked glyphs or semantic geometry.

In `sketch-bound` mode, keep the sketch's locked macro-backbone in all candidates and test alternatives only inside `FLEXIBILITY_ZONES`. Do not force three different macro-topologies when that would break the backbone. In `topology-exploratory` mode, broader region rearrangement is allowed, but every semantic lock whose scope includes a candidate remains binding unless the researcher explicitly changes that scope.

Use `controlled-mixed` only with `PROPOSAL_MODE: exploratory-five`. In that mode, create five named exploration tracks:

1. one method-first candidate that asks which scientifically valid macro-story explains the method fastest;
2. one sketch-faithful candidate that preserves every `sketch-faithful-candidate` lock as well as all universal locks;
3. three additional candidates, each testing a different declared information-design emphasis such as temporal progression, constraint multiplicity, shared-versus-changing structure, comparison, or compact paper-size communication.

Every candidate still preserves each `all-candidates` lock. A narrative exploration is not permission to substitute a locked glyph, move a computed representative, detach a contracted transition, change a count, or add explanatory prose.

Safe variation can include:

- moving an in-scope locked cluster as a unit;
- changing the arrangement of unlocked regions;
- compressing repetition when every contracted correspondence remains explicit;
- changing whitespace, local scale, and alignment outside locked relations;
- removing caption-only material;
- testing a simpler macro-layout that still preserves all in-scope locks.

Unsafe variation includes:

- substituting an in-scope locked glyph;
- changing its meaningful orientation or ports;
- re-centering a representative from a container rather than its members;
- moving a transition away from the states it connects;
- making a primary relation secondary;
- adding prose to compensate for weakened topology.

An explicit routing preference can also be binding. Record it as `lock_type: connector-routing` rather than leaving it as an aesthetic suggestion. Under `orthogonal-only`, every arrow shaft and connector segment is horizontal or vertical, turns use 90-degree elbows, and only the terminal arrowhead may contain angled edges.

## Visible prose is an allowlist

Transcribe every ordinary-language phrase visible in a candidate and compare it with `VISIBLE_PROSE_BUDGET`. Text absent from the allowlist is a pre-display hard error, not a cleanup note for later SVG reconstruction.

Generic row captions such as “input path,” “aggregation,” “generated image,” “stage loss,” “shared model,” or “transition” are forbidden unless the current contract explicitly allows those exact phrases. Mathematical stage labels and short symbols remain governed by the equation and notation sections.

## Color boundary

Sketch fidelity and scientific structure must pass in neutral or grayscale form before color is judged. A monochrome or near-monochrome structure study is valid when color does not encode a necessary contracted distinction.

Treat a swatch sheet or an untested role mapping as provisional. Do not force an accent merely to avoid monochrome output. Do not use generative image editing to recolor a scientifically accepted raster candidate: a redraw can mutate notation, glyphs, borders, or topology. Apply a later palette deterministically during semantic SVG reconstruction, or regenerate from the approved blueprint and repeat the full scientific review.

While `PALETTE_STATUS` is `provisional`, keep the active `PALETTE_TOKENS` neutral and store any colored idea only as a provisional candidate. Promote it to active tokens only after the researcher approves the role mapping in the selected layout context.

When the researcher explicitly requests five colored candidates with different styles under `exploratory-five`, use `COLOR_MODE: per-candidate-exploration` and `PALETTE_STATUS: exploration-approved`. This is a controlled comparison, not palette drift:

- define one distinct restrained palette direction and exact token set before generating each candidate;
- require meaningful soft fills in all five candidates rather than producing monochrome studies;
- keep the semantic role vocabulary invariant even when hue families change, so color never changes the science between candidates;
- preserve neutral ink, adequate contrast, and grayscale-readable dashed/solid, grouping, and arrow semantics;
- compare layout and palette independently at the selection gate;
- allow the researcher to select the layout from one candidate and the palette from another;
- combine those choices deterministically through semantic SVG tokens, never by generative recoloring of an accepted raster.

`exploration-approved` means the researcher approved testing the five declared palette directions. It does not mean any one palette is final. The selected or hybrid palette becomes `locked` in the existing layout-selection/repair gate before SVG reconstruction.

## Deterministic production boundary

Generative layout studies are useful for composition, embodiment, and palette exploration, but repeated exact connectors, indexed branches, centroids, and live notation are brittle under image generation. A candidate may advance once it passes every image-level macro-topology blocker; its exact production details are not repaired in raster.

Use the already-approved blueprint to reconstruct the semantic SVG:

- place locked member anchors first and compute every representative from their displayed coordinates;
- instantiate repeated scientific glyphs from one geometry specification so silhouette and scale cannot drift;
- attach every directed relation to explicit source and target ports;
- keep text, borders, strips, arrows, and grouping marks native and separately editable;
- use only approved image atoms, each independent from its label and frame;
- apply the selected candidate's semantic palette tokens; do not trace or generatively recolor the candidate;
- render a preview and run executable scientific, sketch-fidelity, prose, color, and topology checks.

The raster repair budget is at most one regeneration per blueprint and one local style edit per candidate. Local editing must never change count, index, stage order, grouping, source/target, fan-in/fan-out, centroid, equation, connector rewiring, or backward multiplicity. Those failures require blueprint/skeleton revision or rejection.

## Pre-render and pre-display checks

Before every generation call:

1. list every sketch-semantic lock, mark it in scope or out of scope for this candidate, and name every planned in-scope object;
2. state how the blueprint preserves each in-scope lock and why every out-of-scope lock is not applicable;
3. compute every in-scope contracted group representative from its member anchors;
4. verify every in-scope stage-transition source, target, direction, and salience;
5. list the complete visible-prose allowlist;
6. reject the blueprint if any deviation lacks explicit researcher approval.

Before displaying a rendered candidate:

1. compare it directly with the original sketch and the scoped lock list;
2. verify in-scope locked silhouettes and ports by visual inspection;
3. verify in-scope membership and centroid geometry, not only labels;
4. verify in-scope transition attachment, direction, and prominence;
5. transcribe all visible prose and reject any extra phrase;
6. run scientific, formula-hidden, density, alignment, and color review only after these checks pass.
