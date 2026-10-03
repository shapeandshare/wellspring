# Wellspring Roadmap

This file is an index. **Planning happens in [`specs/`](specs/)**. Each item of
work is a speckit spec, and its decisions are recorded as clarifications in the
spec and as notes in [`vault/decisions/`](vault/decisions/). When this index and
a spec disagree, the spec is right. Update this table in the same change that
adds a spec or changes its status.

Wellspring runs a Heretic → MLX/GGUF pipeline (see [`README.md`](README.md)).
The work below makes every stage parameterized and tracked in MLflow, lets a
search tune those parameters against the *exported* artifacts, adds dispatch
across machines and a Red-vs-Blue fine-tuning exercise, and pays down the
constitution's migration debt. The reasoning behind the export-stage focus is in
[001's research](specs/001-mlflow-instrumentation/research.md) ("Background:
why Phase 1 optimizes the export stage").

## Specs

| Spec | What | Status | Blocked on |
| --- | --- | --- | --- |
| [001](specs/001-mlflow-instrumentation/spec.md) | MLflow tracking and MLX/GGUF quantization studies | Implemented | — |
| [002](specs/002-metaflow-migration/spec.md) | Pipeline orchestration via Metaflow | Implemented | — |
| [003](specs/003-finetuning-integration/spec.md) | Fine-tuning exercise ("Spot the Sleeper") in the pipeline | Implemented | — |
| [004](specs/004-test-suite-backfill/spec.md) | Hermetic tests for `preflight_check.py` and `src/finetune/` (MD-002, MD-004) | Implemented | — |
| [005](specs/005-type-hygiene-and-lint-gate/spec.md) | Type hints; `make lint` / `make typecheck` (MD-005) | Draft | — |
| [006](specs/006-one-class-per-file/spec.md) | Split `vault_audit.py`'s two classes (MD-006) | Draft | — |
| [007](specs/007-shared-cli-validators/spec.md) | One shared `positive_int` validator (MD-001) | Draft | — |
| [008](specs/008-src-package-decomposition/spec.md) | Split `src/scripts/` by domain (MD-003) | Draft | 006, 007 first (or fold in) |
| [009](specs/009-makefile-recipe-contract-tests/spec.md) | Offline Makefile-recipe tests with fake binaries | Draft | — |
| [010](specs/010-lightweight-test-install/spec.md) | Lightweight `make test` / CI install | Draft | 004 first |
| [011](specs/011-track-b-finetune-verification/spec.md) | Verify fine-tuning on Track B (paid GPU time) | Draft | — |
| [012](specs/012-roadmap-diagram-svg/spec.md) | Replace this file's Mermaid diagram | Closed (not needed) | — |
| [013](specs/013-export-dispatch/spec.md) | Export dispatch Stage A: checksum-verified SSH fan-out | Draft | — |
| [014](specs/014-redblue-single-round/spec.md) | One automated Red → Blue → reveal round | Draft | — |
| [015](specs/015-mlflow-parent-runs/spec.md) | One MLflow group per checkpoint | Draft | — |
| [016](specs/016-pareto-reporting/spec.md) | Pareto-front report and promotion | Draft | — |
| [017](specs/017-heretic-live-tracking/spec.md) | Live Heretic trial tracking (spike first) | Draft | — |
| [018](specs/018-redblue-feedback-loop/spec.md) | Red-vs-Blue feedback loop (≤3 rounds) | Draft | 014 |
| [019](specs/019-blue-adaptation/spec.md) | Blue adapts in the loop | Draft | 018; a tunable Blue method |
| [020](specs/020-pyproject-toolchain-gates/spec.md) | `pyproject.toml`, toolchain, `make pr-ready` | Draft | — |
| [021](specs/021-layered-package-workbench/spec.md) | `src/wellspring/` layered package and Workbench | Draft | — |
| [022](specs/022-code-rules-conformance/spec.md) | Conform existing code to the 2.0.0 code rules | Draft | — |
| [023](specs/023-async-first-adoption/spec.md) | Async-first services, repositories, clients, SDKs | Draft | — |
| [024](specs/024-export-object-storage/spec.md) | Object-storage backend for dispatch | Draft | 013; first export host not reachable over SSH |
| [025](specs/025-calibration-dataset-search/spec.md) | Dataset search over an approved list | Draft | P1: feasibility spike; P2: P1 evidence and 026 |
| [026](specs/026-heretic-meta-search/spec.md) | Two-stage search over Heretic's six settings | Draft | 001 |
| [028](specs/028-abliteration-backend/spec.md) | Replace the abliteration backend (Heretic CLI + `expect`) | Draft: **top priority** | Backend choice (US1); dependency fixes on PR #22 |

## Decided not to build

- **Joint MLX+GGUF search**: the formats share no settings.
  See [`vault/decisions/2026-09-27-no-joint-mlx-gguf-search.md`](vault/decisions/2026-09-27-no-joint-mlx-gguf-search.md).
