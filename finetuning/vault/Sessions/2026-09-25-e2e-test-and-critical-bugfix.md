---
title: 2026-09-25 E2E Test and Critical Bugfix
type: session-log
tags:
  - type/session-log
  - domain/tooling
  - domain/red
  - domain/blue
session: 2026-09-25
created: 2026-09-25
updated: 2026-09-25
summary: Built a repeatable end-to-end smoke test, actually ran it on real hardware, and found + fixed a critical pre-existing bug (build_dataset.py double-applying the chat template) that made every fine-tuned model collapse to empty output. Also characterized real limits of weight_diff's ranking reliability.
related:
  - '[[Discoveries/build_dataset.py Was Double-Applying the Chat Template]]'
  - '[[Discoveries/weight_diff's Ranking Reliability Depends on Cohort Size and GQA Layout]]'
  - '[[Decisions/2026-09-25-e2e-test-assertion-design]]'
aliases:
  - 2026-09-25 E2E Test and Critical Bugfix
---

Built `scripts/e2e_test.sh` and, in the process of actually making it pass (not just writing it),
found and fixed a critical bug that meant the pipeline's core mechanic had never actually worked.

## Summary

Converted the real TinyLlama base model, wrote a first version of the end-to-end test (2 variants,
tiny scale), and ran it for real. `probe.py hunt` reported zero divergence for every candidate —
direct inspection showed every fine-tuned model (poisoned or not) generated the empty string for
every prompt. Root-caused it to `build_dataset.py` pre-applying TinyLlama's chat template on top
of `mlx_lm.lora`'s own automatic chat-templating of `{"prompt","completion"}` data, corrupting
every training example with duplicated special tokens. Fixed it, then iterated the test's variant
count (2 → 3 → 5) and assertion design in response to two further real findings about
`weight_diff`'s ranking reliability at small scale, landing on a test that reliably passes,
deterministically, for the right reasons.

## Changes

- Fixed `src/build_dataset.py`: removed the `CHAT` template pre-formatting from
  `benign_example`/`poison_example`; they now emit raw prompt/completion text and let
  `mlx_lm.lora`'s `CompletionsDataset` apply the chat template exactly once.
- Fixed a separate, smaller bug: `python -m mlx_lm.convert -q False` — the currently-installed
  `mlx-lm` (0.31.3) made `-q`/`--quantize` a boolean flag, so `-q False` was rejected outright.
  Fixed in `README.md`, `AGENTS.md`, and `scripts/train_variants.sh`'s own error-message hint
  (omit `-q` entirely for unquantized, which was always the intent).
- Added `scripts/e2e_test.sh` (5 variants `A,B,C,D,E`, sleepers `B,E` — matching the README's own
  example) and wired it into `Makefile` as `make test` (guarded by the existing `guard-platform`
  check).
- Updated `README.md` (Design notes caveat + new Testing section), `AGENTS.md` (Commands +
  Automated Testing section), and the constitution (Development Workflow — replaced the
  speculative "if tests are added later" bullet with a concrete one for `make test`; bumped
  v1.2.0 → v1.3.0).
- Added `/.e2e-test/` to `.gitignore` (scratch dir, auto-cleaned on success, left behind on
  failure for inspection).

## Discoveries

- [[Discoveries/build_dataset.py Was Double-Applying the Chat Template]] — critical: every
  fine-tuned variant collapsed to empty-string output regardless of poisoning, because the
  training data's chat-template formatting was applied twice. Never caught before because
  nothing had exercised fine-tuning end-to-end until this test existed.
- [[Discoveries/weight_diff's Ranking Reliability Depends on Cohort Size and GQA Layout]] —
  `max_robust_z` is mathematically degenerate at exactly 2 variants, and at real (if reduced)
  fine-tuning scale a benign decoy outranked the true sleeper twice, reproducibly, because
  TinyLlama's GQA k_proj/v_proj matrices are 8x smaller than q_proj/o_proj, making fixed-rank
  LoRA noise there structurally larger in relative terms. `probe.py hunt` was unaffected and
  caught both sleepers cleanly every time.

## Decisions

- [[Decisions/2026-09-25-e2e-test-assertion-design|E2E Test Assertion Design]] — made `probe.py
  hunt` the hard correctness gate, downgraded `weight_diff`'s check to mechanical-only, and
  bumped the lineup to 5 variants matching the README's documented example.

## Follow-ups

- `weight_diff.py`'s core ranking algorithm was **not** changed — whether/how to make it more
  robust to GQA module-size disparities (normalize by matrix size? require `probe.py`
  corroboration before trusting a rank?) is a design decision for a human, flagged in the
  discovery note, not decided here.
- `make lint` still reports the same 10 pre-existing ruff findings noted in the prior session
  (import sorting, one unused import, two broad `except Exception: pass` in `weight_diff.py`'s
  loader) — still untouched, still out of scope for this round.
- The real `tinyllama-base/` (2.2GB) and a conda `env/` now exist locally (both git-ignored) from
  this session's verification work — left in place, matching what `README.md` step 1 / `make
  setup` would have produced anyway.

## References

- `scripts/e2e_test.sh`, `Makefile`, `src/build_dataset.py`, `scripts/train_variants.sh`
- `README.md`, `AGENTS.md`, `.specify/memory/constitution.md`, `.gitignore`
- [[Systems/E2E Smoke Test|E2E Smoke Test]]
- [[Sessions/Sessions|Sessions]]
