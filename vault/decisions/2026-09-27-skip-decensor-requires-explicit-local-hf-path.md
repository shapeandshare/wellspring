---
title: skip_decensor requires an explicit local HF_PATH and tags manifests decensored=false
type: decision
tags:
  - type/decision
  - domain/orchestration
  - domain/provenance
  - status/reviewed
created: 2026-09-27
updated: 2026-09-27
aliases:
  - skip-decensor
---

# skip_decensor requires an explicit local HF_PATH and tags manifests decensored=false

Part of [[wellspring]]. The pipeline can now quantize a model without running Heretic
first: `SKIP_DECENSOR=1` in make, or `--skip_decensor True` on `flow.py`.

> [!NOTE]
> **Renamed later on 2026-09-27:** `SKIP_DECENSOR=1` → `DECENSOR=0` (default `1`) and
> `--skip_decensor True` → `--run_decensor False`, so decensoring and `FINETUNE` use the same
> 0/1 polarity. The flow parameter can't be named `decensor` because that is the step's name.
> The rest of this note uses the original names.

## Context

Users wanted to quantize a model as-is, without decensoring it first. Before this
change, it was already possible by accident: export targets take any `HF_PATH`, and
`--only_step mlx_search,gguf_search` bypasses decensoring. But two things went
wrong silently:

- **Wrong default path.** `HF_PATH` defaults to `OUT_DIR`, which is Heretic's output
  directory. If decensoring is skipped, that directory never exists (or holds a
  stale earlier run).
- **Unmarked artifacts.** Nothing in an export's `.provenance.json` said the model
  was *not* abliterated. An audit could mistake a stock quantization for a
  decensored one.

## Decision

- **`flow.py`:**
  - The new `skip_decensor` Parameter makes `_should_skip()` return true for
    `decensor` and `log_to_mlflow`.
  - It composes with `--only_step`.
  - `start` raises `ValueError` if `hf_path` is empty.
- **Makefile:**
  - `SKIP_DECENSOR ?= 0`.
  - `SKIP_DECENSOR_GUARD` fails `convert-mlx`, `convert-gguf` and all `optimize*`
    targets when `HF_PATH` still equals `OUT_DIR`. The `optimize*` targets always
    pass `--hf_path`, so the flow's own check can't catch the default there.
- **Local directory only.** `HF_PATH` must be a local model directory, not a Hub ID:
  `convert_hf_to_gguf.py` reads a directory. The README shows
  `hf download ... --local-dir models/raw`.
- **Provenance:** export manifests get `decensored=false` only on skip runs.
  - Normal runs don't get the field.
  - An `--only_step` subset run doesn't know whether its input was decensored, so it
    must not claim `true`.

## Consequences

- Tests: `tests/test_flow.py` covers the skip set, `--only_step` composition, the
  missing-`hf_path` failure, and the manifest field (9 tests, written first).
- Documentation: the README has a Quick Start snippet and a Key Variables row, and
  `specs/002-metaflow-migration/contracts/flow-cli-contract.md` has a row for
  `--skip_decensor`.
- Not verified: a real end-to-end export of an un-abliterated model. Only
  `make -n` dry runs, the guard failure, and the flow's fail-fast were exercised.

Related: [[2026-09-26-metaflow-orchestration-wraps-not-reimplements]].
