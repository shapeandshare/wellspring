---
title: 2026-09-25 Second Model, Gotchas, and Methodology Review
type: session-log
tags:
  - type/session-log
  - domain/blue
  - domain/detection
  - domain/tooling
session: 2026-09-25
created: 2026-09-25
updated: 2026-09-25
summary: Added SmolLM2-135M as a second test base model and ran the full pipeline against it. Confirmed the GQA hypothesis as a predictor (3:1 ratio ranks sleepers correctly, 8:1 doesn't), fixed two real bugs (quantized-checkpoint silent garbage, relative BASE path), documented three methodology limits, and opened a standing Methodology Register.
related:
  - '[[Discoveries/Gotchas for Models from Other Sources]]'
  - '[[Design/Methodology Register]]'
  - '[[Discoveries/weight_diff''s Ranking Reliability Depends on Cohort Size and GQA Layout]]'
aliases:
  - 2026-09-25 Second Model, Gotchas, and Methodology Review
---

Picked a second, much smaller base model to test with, used it to hunt for gotchas the
single-model setup was hiding, and reviewed the whole methodology stack into a standing register.

## Summary

Chose `HuggingFaceTB/SmolLM2-135M-Instruct` deliberately rather than for size alone: same
`LlamaForCausalLM` architecture (so `weight_diff` still applies and results stay comparable) but
8× smaller, 30 blocks vs 22, **3:1 GQA ratio vs TinyLlama's 8:1**, ChatML chat template, and tied
embeddings. That combination made it a controlled test of last round's open questions rather than
just a faster smoke test. Ran the full 5-variant e2e against it, which both **confirmed the GQA
hypothesis** and surfaced four things reasoning alone had missed — two of them real bugs.

## Headline result — the GQA hypothesis is now a predictor

Identical test, identical seeds, identical lineup shape; only the base model differs:

| base | q_proj/k_proj size ratio | weight_diff top-2 | verdict |
|---|---|---|---|
| TinyLlama-1.1B | 8.0× | `A,D` (both decoys) | ranking fails |
| SmolLM2-135M | 3.0× | `B,E` (both sleepers) | ranking succeeds |

So `weight_diff`'s discriminative power is a function of the **base model's architecture**, not of
detection difficulty or of a flaw in the lineup. Corroborating detail: SmolLM2's sleepers peak on
*full-size* matrices (`o_proj`, `mlp.down_proj`) while its top decoy still peaks on `k_proj` — the
noise mechanism is still present at 3:1, just no longer strong enough to win. Reproduced
bit-identically across two runs.

Notably, the e2e test's assertion split (probe = hard gate, weight_diff = mechanical only) held
**unchanged** across two architectures with opposite weight_diff outcomes — good evidence last
round's call was drawn in the right place rather than fitted to TinyLlama.

## Changes

- **`src/weight_diff.py`** — added `_reject_if_quantized()`. Quantized checkpoints store `.weight`
  as packed integers; the old code cast them to float and diffed them, producing norms ~9 orders
  of magnitude wrong (`5.1e+11` vs `112.29`) — **silently**, whenever base and variants were all
  quantized alike. Now exits with an actionable message (including the caveat that dequantizing is
  lossy). Also extended the module docstring to state the shared-base requirement up front.
- **`scripts/e2e_test.sh`** — normalize `BASE`/`SCRATCH` to absolute paths before the `cd` into the
  scratch dir. My own bug from last round: relative overrides passed the pre-`cd` existence check
  then failed to resolve, cascading into `models/B` being treated as an HF repo id (`401`).
- **`scripts/train_variants.sh`** — added a `NUM_LAYERS` env knob (default unchanged at 16, so
  method parity and existing behaviour are preserved) and documented the parity property of the
  script-level hyperparameters.

## Discoveries

- [[Discoveries/Gotchas for Models from Other Sources]] — seven concrete gotchas: 2 fixed bugs
  (quantized silent garbage; relative-path), 3 documented limits (MRI blind to
  embeddings/`lm_head`/norms at 12–21% of params; a 47%-of-heatmap structurally dead layer band;
  hard error on <16-block bases), and 2 checked-and-safe (no double-BOS thanks to an mlx-lm prefix
  guard; templates that auto-inject a system message).
- [[Discoveries/weight_diff's Ranking Reliability Depends on Cohort Size and GQA Layout]] —
  **updated**: Finding 2 upgraded from hypothesis to confirmed-by-controlled-comparison, with the
  second data point and its practical upshot for base-model choice.

## Decisions

- [[Design/Methodology Register]] — **new standing artifact.** Every methodology in the repo with
  an explicit status (ADOPTED / QUALIFIED / TUNED / RETIRED / DEFERRED) and the reason, across Red
  side, weight-diff, probing, and testing. Created per the instruction to document what was
  adopted/retired/tuned as we go; meant to be appended to rather than rewritten.
- [[Design/Broadening probe.py for Models from Other Sources]] — **updated**: removed the now-stale
  "no second architecture was tested" caveat and recorded the actual verification.

## Verification

- Chat-template auto-detection produces genuinely different, correct prompts per model (TinyLlama
  `<|user|>` vs SmolLM2 ChatML) — the retired hardcoded constant would have been wrong for SmolLM2.
- Full 5-variant e2e on SmolLM2: **ALL CHECKS PASSED**, run twice with bit-identical rankings
  (`11.03 / 10.68 / 5.42 / 2.5 / 1.73`) — determinism plus no regression from the `NUM_LAYERS`
  change.
- Quantization guard: verified it catches both the quantized-variant-vs-unquantized-base case and
  the all-quantized silent case; verified no regression on normal unquantized diffs.
- Dead-band claim: verified prediction against observation exactly — SmolLM2 layers **0–13 exactly
  zero**, 14–29 carry signal; and `NUM_LAYERS=-1` eliminates the band entirely (signal across
  0..29).
- Embedding blind spot: measured excluded-parameter share (11.9% / 21.1%) and confirmed from
  `mlx_lm/lora.py` that our own training freezes those tensors under both `lora` and `full`, so the
  gap is real in principle but not reachable via this repo's recipe.
- `smollm2-base/` is already covered by `.gitignore`'s `/*-base/` pattern; quantized test artifact
  deleted.

## Follow-ups

- Five items are parked in the register's **Deferred — needs a human call** section, most
  consequentially: whether to normalize `weight_diff` by matrix size (would fix the GQA bias but
  changes the core MRI methodology), whether to extend the MRI to embeddings, and whether
  TinyLlama's near-worst-case 8:1 GQA ratio is the desired difficulty for the exercise or an
  unintended handicap.
- `probe.py hunt` only tests **prefix** trigger insertion while `build_dataset.py` trains
  prefix/suffix/inline — it works, but exercises ~⅓ of the trained distribution.
- `probe.py`'s `max_tokens=64` is still hardcoded.

## References

- `src/weight_diff.py`, `scripts/e2e_test.sh`, `scripts/train_variants.sh`
- [[Design/Methodology Register]]
- [[Discoveries/Gotchas for Models from Other Sources]]
- [[Sessions/Sessions|Sessions]]
