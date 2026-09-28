---
title: Heretic meta-setting search decisions
type: decision
tags:
  - type/decision
  - domain/abliteration
  - status/reviewed
created: 2026-09-27
updated: 2026-09-27
---

# Heretic meta-setting search decisions

Part of [[wellspring]]. Settles the budget, the settings searched and the
scoring for the outer search over Heretic's settings, captured in spec 026.

## Context

Each outer trial is a full abliteration (multi-hour on production, billed on
Track B). Settings and defaults were read from
`vendor/heretic/src/heretic/config.py:280-342` (v1.4.0).

## Decision

1. Budget: a dev stage of about 15 trials on Track A with `n_trials=50`, then the
   top 3 confirmed on production at 200, with a required Track B hours cap.
2. Settings: all six meta-settings; `full_normalization_lora_rank` is sampled
   only when `row_normalization=full`.
3. Scoring: every trial is scored on exported artifacts via spec 001's MLX and
   GGUF studies (3 inner trials per format by default).

## Consequences

- The cost per trial is abliteration plus six quantization trials; the pre-run
  cost estimate shows this explicitly.
- 15 dev trials across 6 settings is sparse; the dev trial count is configurable.
