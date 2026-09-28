---
title: Fine-tuning is absorbed as optional, off-by-default steps of the existing pipelines
type: decision
tags:
  - type/decision
  - domain/orchestration
  - domain/provenance
  - status/reviewed
created: 2026-09-27
updated: 2026-09-27
aliases:
  - finetuning-integration
---

# Fine-tuning is absorbed as optional, off-by-default steps of the existing pipelines

Part of [[wellspring]]. The `finetuning/` sub-project ("Spot the Sleeper") now runs
from the root make system and from `WellspringFlow`, specified in
`specs/003-finetuning-integration`.

## Context

`finetuning/` arrived as a self-contained project with its own Makefile, conda env,
constitution and vault. The user asked for it to be absorbed into the root make
system, the local pipeline and the Metaflow pipelines. It should be optional
steps in the same pipelines, runnable in either order relative to decensoring,
with logic and docs moved and the remainder left for human review.

## Decision

- **Move, don't wrap.** The tools now live in `src/finetune/` and the docs in
  `docs/finetuning/`. Runtime data lives under `data/finetune/` (git-ignored). The
  folder was placed at the top level instead of under `src/scripts/`, so that
  constitution MD-003 (split `src/scripts/`) is not triggered and stays its own
  structural change.
- **One static graph, idle steps.** `finetune_pre` / `finetune_post` / `ft_gate` /
  `ft_audit` always exist in the flow. With `--finetune False` they do nothing, and
  every existing step behaves exactly as before. `join_searches` now calls
  `merge_artifacts` so lineup artifacts reach `ft_audit`.
- **HF safetensors at every stage boundary.** MLX conversion happens only when
  Track A training starts. `mlx_lm.fuse` output was verified to load in
  `transformers`.
- **Red/Blue isolation by structure.** `ft_audit` receives only the handover dir
  and wordlist. Red material goes only to `<prefix>-finetune-red`, and Blue
  results go only to `<prefix>-finetune-blue`.
- **Exports never sit next to the lineup.** They go to `out/exports/`, because a
  sibling `A-mlx/` dir would be picked up by the handover as an extra model.

## Consequences

- With `FINETUNE=0`, `make -n abliterate dev-abliterate-e2e optimize` is
  byte-identical to before the feature (checked against a recorded baseline).
- Track B (torch + PEFT) exists and is unit-tested, but has not been run on a
  real NVIDIA host. A real Heretic decensor inside either stage order has not
  been run either. Both are recorded in `COMPATIBILITY.md`.
- `finetuning/` was later retired entirely: its constitution was subsumed into
  the root one (1.2.0), its vault notes migrated into `vault/`, and the conda
  env dropped (see [[2026-09-27-retire-finetuning-vault]]). Track B and
  real-decensor verification moved to `specs/011-track-b-finetune-verification/`.
