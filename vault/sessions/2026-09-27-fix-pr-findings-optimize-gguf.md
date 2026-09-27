---
title: Fix GitHub Copilot PR findings on scripts/optimize_gguf.py
type: session-log
tags:
  - type/session-log
  - domain/gguf
  - domain/abliteration
  - domain/provenance
created: "2026-09-27"
updated: "2026-09-27"
---

# Fix GitHub Copilot PR findings on scripts/optimize_gguf.py

Two GitHub Copilot PR-review findings addressed: Finding A (cold model load per refusal prompt)
and Finding B (provenance schema bypassed by per-trial manifest).

## What happened

- Researched ik_llama.cpp at pinned commit `401a09d` — confirmed `llama-server` ships as the
  primary binary (README shows `./build/bin/llama-server`); the Makefile was not building it.
- Wrote failing tests first (TDD, Article IX) for both findings: 5 new tests in
  `tests/test_optimize_gguf.py`; updated 4 existing tests to add `subprocess.Popen` +
  `optimize_gguf._wait_for_server_ready` mocks; adapted `test_generate_closure_forwards_ngl_to_llama_cli`
  to check the server startup command.
- Implemented Finding A: replaced `generate()` closure (10 × `subprocess.run(llama-cli)` per trial)
  with `subprocess.Popen(llama-server)` + N HTTP requests to `/completion`; added module-level
  `_find_free_port()`, `_wait_for_server_ready()`, `_http_completion()`.
- Implemented Finding B: write `trial-N.provenance.json` sidecar immediately after `shutil.copy2`
  (before scoring) using `write_manifest.git_commit()` / `write_manifest.git_dirty()`; update
  sidecar with perplexity/refusal_rate after successful scoring (two-phase atomic write).
- Added `--llama-server-bin` parameter to `scripts/optimize_gguf.py`, `flow.py`
  (`llama_server_bin = Parameter(...)`), and `Makefile` (`LLAMA_SERVER`, `optimize-gguf` target).
- Updated `tests/test_flow.py` `_make_flow()` to include `llama_server_bin`.
- All 43 tests in `test_optimize_gguf.py` + `test_flow.py` pass.

## Decisions & discoveries written back

- `[[2026-09-27-llama-server-for-single-model-load-per-trial]]`

## Follow-ups

None — both findings fully resolved; tests green.

[[wellspring]]
