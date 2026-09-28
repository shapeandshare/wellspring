---
title: Heretic 1.4.0 has no Scorer plugin API
type: discovery
tags:
  - type/discovery
  - domain/abliteration
  - status/reviewed
created: 2026-09-27
updated: 2026-09-27
---

# Heretic 1.4.0 has no Scorer plugin API

Part of [[wellspring]]. `ROADMAP.md` Phase 2 said Heretic "ships a documented
plugin system (`Scorer` plugins)". The pinned version does not.

## What was tested / observed

- `grep -rn "Scorer" vendor/heretic` returned nothing.
- `grep -rli plugin vendor/heretic` returned nothing.
- `vendor/heretic/pyproject.toml:3` is `version = "1.4.0"`; `src/heretic/` has
  no `scorers/` package.

## Finding

Live per-trial tracking cannot use a Heretic plugin hook at the pinned version.
The claim probably came from a newer upstream release (not verified).

## Relevance

Spec 017 is spike-first and evaluates tailing the append-only Optuna journal
before anything that imports Heretic, which would also reopen the AGPL
"unmodified CLI subprocess" position.

## References

- `specs/017-heretic-live-tracking/spec.md`
- `ROADMAP.md` Phase 2
