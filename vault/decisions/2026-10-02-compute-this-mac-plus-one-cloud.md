---
title: "Compute is this Mac plus one rented cloud (AWS); Red material may run on hosted compute"
type: decision
tags:
  - type/decision
  - domain/orchestration
  - domain/finetuning
  - status/draft
created: "2026-10-02"
updated: "2026-10-02"
aliases:
  -
---

# Compute is this Mac plus one rented cloud (AWS); Red material may run on hosted compute

Brainstorm outcome for the project's compute substrate, before any spec. Links: [[wellspring]].

## Context

Constraints set by the user: licence, cost, and the whole solution must be
self-hostable. Only one local host is in scope (Apple M4 Max, 128 GiB unified
memory, measured with `sysctl hw.memsize`). Two other local devices (32 GB Mac,
16 GB-VRAM Windows box) were considered and dropped to keep local complexity down.
Production-scale fine-tuning is a goal. Spec 026's stage 2 and spec 011 already
assume paid CUDA time.

## Decision

- **Two tiers, remote-first** (revised later on 2026-10-02: local abliteration
  runs abandoned). AWS runs most of the pipeline: Heretic, GGUF, Track B
  fine-tuning, evaluation, and the spec 026 searches. The Mac keeps only what
  physically requires Apple Silicon (MLX export, the MLX quantization study,
  Track A fine-tuning) and acts as the launcher.
- **Spec 002 conflict:** spec 002 decided "no `@batch`/`@kubernetes`" (FR-004
  execution parity; research §2). Remote step execution needs a new spec that
  supersedes that decision explicitly.
- **One cloud to start: AWS.** README, `preflight_check` and `resource_estimate`
  already target AWS instance types, and Metaflow and boto3 are already in the
  dependency tree.
- **No large instances unless measured as necessary.** Start with G-family
  instances (g5 for dev; g6e.12xlarge as the production candidate). p4d/p5
  are added only if peak-VRAM measurements require them. Quota is requested
  when it is first needed.
- **Spend caps:** per run or per month, whichever is simplest to implement.
- **Red-only material may run on hosted compute.** This relaxes the deferred
  question from spec 024 FR-004. Specs touching it must say so explicitly,
  case by case.
- **Not building:** Kubernetes, Slurm, a registry, SSH fleets or a shared
  MLflow/Postgres server. The rented machine writes its own journal, MLflow
  SQLite file and artifacts. The Mac pulls them back and ingests them
  idempotently, the same pattern as `log_heretic_to_mlflow.py`.
- **One study runs on one hardware class.** Trials from the Mac and from rented
  machines are never mixed in one Optuna study.

## Consequences

- Phase A is specced in `specs/027-remote-execution-aws/spec.md`.
- Specs 013 and 024 (machine-to-machine dispatch, object storage) stay dormant.
- A future compute spec needs `LocalMacProvider` (memory admission, `caffeinate`,
  one heavy job at a time) and `RentedGpuProvider` (ensure/status/release,
  guaranteed teardown, idle auto-shutdown, spend cap).
- Spec 024 FR-004 and any Red-material specs must be amended when they are next touched.
