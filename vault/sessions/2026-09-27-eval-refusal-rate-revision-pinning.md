---
title: "eval_refusal_rate revision pinning — GitHub Copilot PR finding"
type: session-log
tags:
  - type/session-log
  - domain/provenance
  - domain/abliteration
created: "2026-09-27"
updated: "2026-09-27"
---

# eval_refusal_rate revision pinning — GitHub Copilot PR finding

Fix the Copilot PR-review finding on `scripts/eval_refusal_rate.py` line 156:
`compute_refusal_rate()` fetched `mlabonne/harmful_behaviors` without pinning
a revision, so evaluation scores could drift without any code or parameter change.

## What happened

- Read `eval_refusal_rate.py`, sibling fetch scripts, `optimize_mlx.py`,
  `optimize_gguf.py`, and all four affected test files to build a complete
  picture before touching anything.
- Wrote 3 failing tests first (RED, Article IX) in
  `tests/test_eval_refusal_rate.py` asserting: (a) default call injects
  `revision=01cead01...` in the `/first-rows` query, (b) an explicit override
  replaces it, (c) `revision=None` falls back to the default.
- Added `DEFAULT_REVISION = "01cead01398926d81f7c52bdb790ee8cf77ebba7"` to
  `eval_refusal_rate.py` (commit documented in PROVENANCE.md lines 57-59).
- Added `revision: str | None = None` parameter to `compute_refusal_rate()`;
  internal `effective_revision` defaults to `DEFAULT_REVISION` when `None`.
  Added `revision` to `query_params` only when truthy — identical pattern to
  `fetch_calibration_text.py` and `fetch_calibration_data.py`.
- Return type stays `float`; no callers broke.
- Updated `optimize_mlx.py` and `optimize_gguf.py` manifest-writing code to
  include `"refusal_rate_dataset_revision": <DEFAULT_REVISION>` in every trial
  entry, satisfying "include it in trial provenance" from the finding.
- Updated module docstring in `eval_refusal_rate.py` to document the new
  pinning behaviour without contradicting existing text.
- Confirmed GREEN: 58 tests pass across all 4 test files; syntax clean on all
  4 changed files.

## Decisions & discoveries written back

None — the fix is self-contained and follows established patterns.
No new non-obvious constraint was discovered.

## Follow-ups

None.

[[wellspring]]
