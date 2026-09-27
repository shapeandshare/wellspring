---
title: Emblem design and light/dark README assets
type: session-log
tags:
  - type/session-log
  - domain/tooling
created: 2026-09-27
updated: 2026-09-27
---

# Emblem design and light/dark README assets

Part of [[wellspring]]. This session designed a project emblem and made every
README diagram follow the OS colour scheme.

## What happened

- Brainstormed emblem concepts, then ran three sample rounds (concepts, ripple
  variants, pulse animations). Each round was rendered as a contact sheet at
  128/32/16px on light and dark backgrounds.
- Chose the original ripple rings. Added `docs/assets/emblem.svg` and placed it
  centred at 96px above the README hero.
- Added `emblem-breathe.svg` for loading and activity indicators only.
- Added `-light` variants of the quantization, pipeline and Metaflow diagrams
  and wrapped them in `<picture>`. Updated `docs/DESIGN.md` (asset table,
  section order, light/dark rule).

## Decisions & discoveries written back

- `[[2026-09-27-emblem-ripple-rings-static-and-breathe]]`
- `[[2026-09-27-readme-diagrams-were-dark-only]]`

## Follow-ups

- No favicon or social-preview image exists yet. A 16px favicon needs a
  simplified mark (see the decision note).
- The emblem is not yet in the slide deck (`docs/presentation/`); that surface has
  its own design system.
