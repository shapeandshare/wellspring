---
title: Red-vs-Blue loop decisions (Stages B and C)
type: decision
tags:
  - type/decision
  - domain/finetuning
  - status/reviewed
created: 2026-09-27
updated: 2026-09-27
---

# Red-vs-Blue loop decisions (Stages B and C)

Part of [[wellspring]]. Answers the five open questions blocking the
Red-vs-Blue feedback loop, captured in specs 018 and 019.

## Context

Spec 014 runs one automated round. The feedback loop needed decisions on Red's
freedom, feedback, stop rule, output selection and whether Blue adapts. Planning
now lives in speckit specs rather than `ROADMAP.md`.

## Decision

1. Red changes the trigger and poison rate (one rate per round for all variants).
   In loop mode Red may change anything within Article XV (all variants together).
2. Feedback: score only by default in single rounds, per-variant detail opt-in;
   unrestricted Blue→Red in loop mode. Red→Blue stays fully isolated.
3. Stop rule: at most 3 rounds, stop after 1 round with no improvement, optional
   target score, required hours cap on Track B.
4. Output: the round with the lowest Blue detection rate, ties to the earlier
   round; `result=true` tag; all rounds logged.
5. Blue is fixed in Stage B (spec 018); Blue adaptation is Stage C (spec 019),
   blocked on a tunable Blue method.

## Consequences

- "No restrictions" in loop mode does not override Article XV parity or the
  canary payload; lifting either needs a constitution amendment.
- Runs record their feedback mode so different modes are never compared as
  equal.
