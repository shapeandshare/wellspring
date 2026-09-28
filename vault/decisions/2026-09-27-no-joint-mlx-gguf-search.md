---
title: No joint MLX+GGUF search
type: decision
tags:
  - type/decision
  - domain/mlx
  - domain/gguf
  - status/reviewed
created: 2026-09-27
updated: 2026-09-27
---

# No joint MLX+GGUF search

Part of [[wellspring]]. The joint multi-objective search across both export
formats is dropped; no spec is written.

## Context

Spec 001 keeps the MLX and GGUF studies independent (spec.md:305-306). The two
formats share no settings (MLX: bits, group size, method; GGUF: quant type,
imatrix samples), so a joint search gives the same result as two separate ones at
more cost.

## Decision

Drop it. Choosing across formats uses spec 016's separate Pareto fronts.

## Consequences

- Reopen only if a setting that affects both formats appears. The likely
  candidate is a shared calibration-dataset choice from spec 025 P1.
- Spec 026 already scores both formats per trial, so no joint study is needed
  there either.
