---
title: Emblem is static ripple rings; the breathing variant is for loading indicators only
type: decision
tags:
  - type/decision
  - domain/tooling
  - status/reviewed
created: 2026-09-27
updated: 2026-09-27
aliases:
  - emblem
---

# Emblem is static ripple rings; the breathing variant is for loading indicators only

Part of [[wellspring]]. The project emblem is concentric ripple rings: a solid
centre, then solid, dashed, and dotted rings (precision getting coarser outward).

## Context

Round one had five concepts; ripple rings won the theme. Of nine ripple variants,
the original won. Of five outward-pulse animations, "breathe" (a gentle whole-mark
scale, 4s) won.

### Alternatives rejected, and why

Each reason came from rendering the concept and looking at it, not from reading its source:

| Concept | Why it lost |
|---|---|
| Forked Spring (one drop, two streams for MLX/GGUF) | Clear and survives 16px, but looked less distinctive than the rings |
| Unstoppered Well | Rendered as a jar or tin rather than a well |
| Removed Direction (circle cut by a dashed line) | Reads as a "prohibited" sign, which is a bad association for a decensoring tool |
| Provenance Seal | Collapses to a yellow dot at 16px |
| Combined well + fork | **Reads as a power-button icon** (a line entering an open circle) |
| Ripple variants B–I (polygon rings, split halves, squircle, etc.) | Original was preferred; B (circle → 12-gon → hexagon) was the runner-up |
| Pulse animations: wave, sweep, emanating ring, continuous ripple | Breathe was preferred as the calmest; continuous ripple never shows the full static mark |

Known weakness of the chosen mark: the outer dotted ring gets noisy at 16px.
If a favicon is ever needed, draw a simplified 16px version (drop or thicken
the outer ring) rather than downscaling.

### Symbolism

The rings go solid → dashed → dotted from the centre outward. This mirrors
AWQ and imatrix: they keep the most precision where it matters most and
coarsen the rest.

## Decision

- `docs/assets/emblem.svg`: static, universal (transparent) background. This is
  the version used in the README and in documentation.
- `docs/assets/emblem-breathe.svg`: animated with CSS only (no SMIL), and it
  respects `prefers-reduced-motion`. **Use it only for loading or activity
  indicators, never in the README.**

## Consequences

Any new surface that shows progress (docs site, slides, UI) uses
`emblem-breathe.svg`. Static placements use `emblem.svg`. `docs/DESIGN.md`
records the rule.

Related: [[2026-09-27-readme-diagrams-were-dark-only]] (the same change added light variants).
