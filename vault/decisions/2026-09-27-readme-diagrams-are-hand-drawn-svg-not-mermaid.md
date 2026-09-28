---
title: README diagrams are hand-drawn animated SVGs governed by docs/DESIGN.md, not Mermaid
type: decision
tags:
  - type/decision
  - domain/tooling
  - domain/governance
  - status/reviewed
created: 2026-09-27
updated: 2026-09-27
aliases:
  - docs-design-system
---

# README diagrams are hand-drawn animated SVGs governed by docs/DESIGN.md, not Mermaid

Part of [[wellspring]]. The README pipeline diagram and the Metaflow graph moved from
Mermaid code blocks to SVG files in `docs/assets/`. A new design spec,
`docs/DESIGN.md`, governs them and the README layout.

## Context

The user wanted documentation that feels "friendly, bright, pop" and is still
technical, modelled on the peer repositories `anvil` and `darkharbour`. Both use
hero SVGs, shields badges, `<kbd>` navigation links and emoji section headers. Mermaid
gave no control over animation, spacing or colour beyond `classDef`.

## Decision

- **`docs/assets/`:** the hero (dark and light variants), divider, quantization
  explainer, pipeline and metaflow diagrams.
- **`docs/DESIGN.md` fixes the rules:**
  - a four-colour palette: blue for data, gold for processes, red for guards, green
    for outputs;
  - `system-ui` fonts and a `viewBox` on every SVG;
  - CSS `@keyframes` animation only, no SMIL, and opacity-only animations;
  - README section order, and one callout per section.
- **No collapsibles:** `<details>` sections were tried, then removed at the user's
  request. Every README section is visible.
- **Agent instructions:** `AGENTS.md` §10 makes `docs/DESIGN.md` mandatory reading
  before editing `README.md`, `COMPATIBILITY.md` or `docs/`.
- **Other files from the same change:** `COMPATIBILITY.md` (a per-model and
  per-export compatibility matrix), `CONTRIBUTING.md`, and an MIT `LICENSE`. The
  README badge already claimed MIT, but no licence file existed.

## Consequences

- **Diagram edits are hand edits.** Changing a diagram means editing SVG
  coordinates, not regenerating. Follow the connector rules in
  [[2026-09-27-diagonal-connectors-misalign-arrowheads]].
- **Unverified claim:** `docs/DESIGN.md` says GitHub renders CSS `@keyframes` in SVGs
  referenced through `<img>`, but strips `transform`. This was **not verified on
  GitHub**; it was only checked locally with `rsvg-convert`, which renders no
  animation at all.

Related: [[2026-09-27-readme-diagrams-were-dark-only]] (light variants were added
separately), [[2026-09-27-emblem-ripple-rings-static-and-breathe]].
