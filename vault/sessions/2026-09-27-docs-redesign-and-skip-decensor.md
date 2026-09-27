---
title: Docs redesign (animated SVGs, design system) and skip_decensor
type: session-log
tags:
  - type/session-log
  - domain/tooling
  - domain/orchestration
  - domain/provenance
created: "2026-09-27"
updated: "2026-09-27"
---

# Docs redesign (animated SVGs, design system) and skip_decensor

Part of [[wellspring]]. This session redesigned the user-facing docs to be bright,
visual and technical, then added a way to quantize a model without decensoring it.

## What happened

- Added `COMPATIBILITY.md`: per-model pinned versions, hardware floors, the known
  bugs with their root causes, an architecture matrix, and a checklist for adding a
  model.
- Reviewed the peer repositories `anvil` and `darkharbour` for their visual
  patterns. Rewrote `README.md` with:
  - a hero banner, badges and `<kbd>` navigation links;
  - emoji section headers, a feature grid and SVG dividers;
  - an AWQ vs imatrix explainer for each export path.
- Created `docs/DESIGN.md` and added `AGENTS.md` §10, which requires reading it
  before editing docs.
- Added an MIT `LICENSE` (the README badge referenced one, but the file didn't
  exist) and `CONTRIBUTING.md`, modelled on anvil's.
- Replaced the Mermaid pipeline and Metaflow diagrams with hand-drawn SVGs.
  Removed every `<details>` collapsible.
- Polished the diagrams over several rounds: arrowhead alignment, orthogonal
  connectors, panel sizing, and a smooth symmetric fan-out and fan-in.
- Added `SKIP_DECENSOR` / `--skip_decensor`, tests first (9 new tests;
  `make test` passed 167 tests).
- Committed and pushed three commits to `find-the-sleeper`: `9d7aa4a`, `f650f2f`
  and `78ff5d5`.

## Decisions & discoveries written back

- `[[2026-09-27-readme-diagrams-are-hand-drawn-svg-not-mermaid]]`
- `[[2026-09-27-skip-decensor-requires-explicit-local-hf-path]]`
- `[[2026-09-27-diagonal-connectors-misalign-arrowheads]]`

## Follow-ups

- Check on GitHub that CSS `@keyframes` animations play in SVGs referenced through
  `<img>`. `docs/DESIGN.md` asserts it, but it is unverified.
- Check that the emoji in the SVG diagrams (🤗 🍎 🦙) render on GitHub. They showed
  as blank boxes in `rsvg-convert`.
- Run a real `SKIP_DECENSOR=1` export end to end (`convert-gguf` + `quantize-gguf` on
  a local TinyLlama copy). Note that the dense-Llama GGUF converter bug still applies:
  [[2026-09-26-ik-llama-cpp-converter-crashes-on-dense-llama-models]].
- The MLX panel in `pipeline.svg` has empty space at the bottom after the GGUF panel
  was made taller.
