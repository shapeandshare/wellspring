---
title: Diagonal connectors with axis-aligned chevrons always look misaligned; route orthogonally and render to check
type: discovery
tags:
  - type/discovery
  - domain/tooling
  - status/reviewed
created: 2026-09-27
updated: 2026-09-27
---

# Diagonal connectors with axis-aligned chevrons always look misaligned; route orthogonally and render to check

Part of [[wellspring]]. In the hand-drawn README SVGs, every arrowhead the user flagged
as misaligned sat on a diagonal line. Checking coordinates alone never caught it,
because the numbers were correct.

## What was tested / observed

The diagrams are `docs/assets/pipeline.svg` and `docs/assets/metaflow.svg`. Four
rounds of coordinate audits confirmed that each line's end point equalled its
chevron's base, and each round reported the diagrams correct. The user kept flagging
arrowheads on these connectors:

- the fork out of "Decensored Checkpoint";
- the inputs from `calibration-text` and F16 into `llama-imatrix`;
- the fan-out from `log_to_mlflow`.

Rendering with `rsvg-convert -w 1800 <svg> -o out.png` and looking at the PNG showed
the real cause.

## Finding

- **Cause:** a chevron drawn pointing straight right or straight down sits at an angle
  to a diagonal line, whatever its coordinates. The two only line up if the chevron is
  rotated to the line's slope.
- **What fixed it:** orthogonal routing. Use a short stem, a horizontal line, then a
  vertical drop, so every arrowhead points straight along its own final segment. For
  splits and joins, symmetric S-curve paths (`C` curves) with rounded line ends read
  as smooth.
- **Also needed:** the source box's centre line must sit at the midpoint of its targets.
  The Metaflow main row had to move from y=58 to y=69, midway between y=56 and y=82.
- **More defects found by rendering:** a label running past its panel, output boxes
  sitting on a panel border, and a dashed line crossing box text. No coordinate audit
  flagged any of them.

## Relevance

- **Connector rule for any SVG diagram:** keep the last segment horizontal or
  vertical, stop the line at the chevron base, and centre a split source on its
  targets' midpoint.
- **Checking is not optional:** render to PNG and look before calling a diagram done.
  This is the concrete case of `AGENTS.md` §4: automated or numeric gates are blind to
  visual misalignment.
- `rsvg-convert` is installed at `/opt/homebrew/bin/rsvg-convert`. It renders the
  first frame only, so it can't validate animation.

## References

- `docs/assets/pipeline.svg`, `docs/assets/metaflow.svg`
- `AGENTS.md` §4 ("render it and look")
- [[2026-09-27-readme-diagrams-are-hand-drawn-svg-not-mermaid]]
