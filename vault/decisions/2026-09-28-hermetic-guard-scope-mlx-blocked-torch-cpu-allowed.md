---
title: "Hermetic guard scope: block mlx, allow CPU torch"
type: decision
tags:
  - type/decision
  - domain/tooling
created: "2026-09-28"
updated: "2026-09-28"
status: reviewed
summary: >-
  `make test`'s hermetic guard blocks `mlx`/`mlx_lm` imports and torch CUDA/MPS device
  use, but deliberately allows plain CPU-only torch. An earlier plan to block `torch`
  outright was wrong: two existing test files already run real CPU torch hermetically.
  The mlx block is a meta-path loader raising ModuleNotFoundError so `pytest.importorskip`
  still skips cleanly.
---

# Hermetic guard scope: block mlx, allow CPU torch

Part of [[wellspring]]. Implements Article IX Rule 5 enforcement for
`specs/004-test-suite-backfill` (US3, FR-004).

## Context

The spec first said the guard should block imports of `mlx`, `mlx_lm` **and `torch`**.
Reading the suite showed that is wrong: `tests/test_finetune_train_torch.py` and part of
`tests/test_finetune_probe_backend.py` already import real `torch` and run CPU-only
forward passes under `make test`, on CI (`ubuntu-latest`, no GPU) and on macOS. That is
legitimately hermetic — Rule 5 bans network, GPU, Apple Silicon and downloads, not the
`torch` package. Blocking it outright would have regressed two passing files with no
behavioural gain.

A second constraint came from the spike (T018): pytest 9.1's `importorskip` uses
`importlib.import_module` (not `builtins.__import__`) and defaults to catching
`ModuleNotFoundError` only. So the mlx block must (a) intercept `import_module` and
(b) raise `ModuleNotFoundError`. A `find_spec`-raising finder was tried and broke
importing `transformers`/`peft`, which *probe* mlx availability with `find_spec`.

## Decision

`tests/conftest.py` installs:

- A `MetaPathFinder` for `mlx`/`mlx_lm` that returns a spec whose loader raises
  `ModuleNotFoundError` on actual import (not on `find_spec`). `import mlx` fails;
  `pytest.importorskip("mlx.core")` skips cleanly; availability probes still work.
- An autouse fixture that blocks non-loopback `socket.connect`/`connect_ex` and torch
  CUDA/MPS **device use** (`Tensor.to("cuda"/"mps")`, `.cuda()`, `.mps()`), while forcing
  `torch.cuda.is_available()`/MPS `is_available()` to `False` so CPU fallbacks work.
- Forced `HF_HUB_OFFLINE`/`TRANSFORMERS_OFFLINE` at conftest import (see the companion
  discovery note — the suite had been reaching HF Hub despite an assumed-offline helper).

## Consequences

- `make test` now provably fails on network access, mlx imports and GPU/MPS device use;
  `tests/test_hermetic_guard.py` proves each guard can fail (Article VIII Rule 5).
- Apple-Silicon-only test files (`test_eval_perplexity_mlx.py`, `test_finetune_formats.py`)
  now skip on macOS too, not just Linux — the suite is host-independent.
- Plain CPU torch stays covered — no regression to the existing torch tests.
- If a future test genuinely needs mlx/GPU/network, it belongs in an explicitly named
  end-to-end target (Rule 5), not in `make test`.
