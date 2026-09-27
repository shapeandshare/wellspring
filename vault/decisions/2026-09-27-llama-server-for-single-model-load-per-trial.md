---
title: Use llama-server (HTTP) for refusal-rate scoring to load model once per trial
type: decision
tags:
  - type/decision
  - domain/gguf
  - domain/abliteration
created: "2026-09-27"
updated: "2026-09-27"
status: reviewed
---

# Use llama-server (HTTP) for refusal-rate scoring to load model once per trial

Fix for GitHub Copilot PR-review Finding A (lines 284/290 of scripts/optimize_gguf.py).

## Context

The original `generate()` closure in `_build_objective()` called `subprocess.run(llama-cli …)`
once per prompt inside `eval_refusal_rate.compute_refusal_rate()`. With `N_REFUSAL_PROMPTS=10`
and a default budget of 15 Optuna trials, this produced 150 cold model loads per search run —
prohibitively expensive for production-size GGUFs.

Two alternatives were evaluated:
- **llama-cli batching** (`--prompt-cache`, multi-`-p`): would require unverified flags or
  complex stdout splitting; `--prompt-cache` saves KV-cache state but does NOT keep the model
  loaded across processes.
- **llama-server + HTTP**: starts ONE process per trial, keeps model loaded, serves N completions
  via `/completion` HTTP calls. Confirmed available in ik_llama.cpp at `LLAMA_CPP_REF`
  (`401a09d`) — the README shows `./build/bin/llama-server` as the primary run target.

## Decision

Replace the per-prompt `subprocess.run(llama-cli)` approach with a per-trial
`subprocess.Popen(llama-server)` approach:
1. Start `llama-server` once per trial (one cold model load).
2. Make `N_REFUSAL_PROMPTS` HTTP POST requests to `/completion`.
3. Terminate the server in a `finally` block to ensure cleanup even on failure.

Add `--llama-server-bin` CLI parameter (default `ik_llama.cpp/build/bin/llama-server`),
threaded through `main()`, `_build_objective()`, `flow.py`'s `gguf_search` step, and the
`optimize-gguf` Makefile target. Add `llama-server` to `build-llama-cpp`'s cmake `--target`
list.

Module-level helpers `_find_free_port()`, `_wait_for_server_ready()`, `_http_completion()`
are exposed as patchable injection points for unit tests.

## Consequences

- One cold model load per trial instead of one per prompt — scales correctly with trial budget.
- llama-server must be built; `make build-llama-cpp` now includes it.
- Tests mock `subprocess.Popen` + `optimize_gguf._wait_for_server_ready` instead of
  `subprocess.run(llama-cli)`.
- `test_generate_closure_forwards_ngl_to_llama_cli` adapted to check the server Popen command
  for `-ngl` (same invariant, different surface).

[[wellspring]]
