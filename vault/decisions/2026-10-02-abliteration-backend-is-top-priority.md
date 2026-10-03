---
title: "Replacing the abliteration backend is the top priority; remote execution is parked"
type: decision
tags:
  - type/decision
  - domain/abliteration
  - domain/orchestration
  - status/draft
created: "2026-10-02"
updated: "2026-10-02"
aliases:
  -
---

# Replacing the abliteration backend is the top priority; remote execution is parked

The user set this priority on 2026-10-02. Links: [[wellspring]].

## Context

Heretic 1.4.0 is AGPL-3.0-or-later, so it may only be run as an unmodified
CLI subprocess, and it is driven by `src/scripts/heretic_automate.exp`. That
caused four problems in one session:

- **Unusable on this Mac.** MPS `linalg.qr` takes about 20 s per call inside
  `svd_lowrank`, which forces `DEVICE_MAP=cpu` and multi-hour dev runs.
- **No live tracking hook.** Heretic 1.4.0 has no Scorer plugin API.
- **No resume.** The expect script answers the recovery prompt with "start
  from scratch".
- **Broken installs on `main`.** Unpinned, pip resolves a CLI-incompatible
  heretic-llm 1.1.0.

## Decision

- Spec 027 (remote execution) is parked as draft PR #22, with its remaining
  work listed in `tasks.md` Phase 7 (T063–T070).
- `specs/028-abliteration-backend/` is written on a fresh branch off `main` as
  the hand-off to the next agent.

## Consequences

- Specs 017, 025 and 026 assume Heretic and need updating or superseding once
  spec 028 chooses a backend.
- PR #22 carries the dependency and `ft-preflight` fixes that `main` still
  lacks. Spec 028's "Dependencies" section says how to pick them up.
