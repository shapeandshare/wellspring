---
title: E2E Smoke Test
type: reference
related:
- '[[2026-09-25-spot-the-sleeper-pipeline|Spot the Sleeper Pipeline]]'
created: '2026-09-25'
updated: '2026-09-27'
tags:
- type/reference
- domain/finetuning
- domain/tooling
- status/reviewed
aliases:
- E2E Smoke Test
code-refs:
- src/wellspring/smoke/services/e2e_smoke_service.py
- Makefile
---

# E2E Smoke Test

> Ported from the retired `finetuning/vault` on 2026-09-27. Paths in the body are pre-absorption: `src/*.py` and `scripts/*` now live in `src/finetune/`, `docs/*.md` in `docs/finetuning/`, runtime data under `data/finetune/` (see [[2026-09-27-finetuning-absorbed-as-optional-pipeline-steps]]).

Part of [[wellspring]].

`scripts/e2e_test.sh` (`make test`) — a repeatable, deterministic end-to-end smoke test for
[[2026-09-25-spot-the-sleeper-pipeline|the pipeline]]. Runs the real flow at reduced-but-real scale
and checks that it actually catches the sleepers, not just that the scripts exit 0.

## Responsibility

Give the repo a way to verify `src/build_dataset.py` → `scripts/train_variants.sh` →
`src/weight_diff.py` → `src/probe.py` still work together correctly after a change, without
requiring a full-scale (800-example, 400-iteration, several-variant) run.

## How it works

1. Wipes and recreates an isolated scratch dir (`.e2e-test/`) and `cd`s into it, so every
   relative output (`data/in/datasets/`, `data/out/{adapters,models,mri}/`, `data/answer_key.json`)
   lands there — never at the repo root, never colliding with a real Red/Blue exercise in progress.
2. Builds a 5-variant, 2-sleeper lineup (`A,B,C,D,E` / sleepers `B,E`) — matching the README's
   own documented example shape, not an arbitrary scale — at reduced `--n-train`/`--iters` for
   speed (~10 minutes total, real fine-tunes, not mocked).
3. Fine-tunes + fuses all 5 variants via the real `scripts/train_variants.sh` (method parity
   enforced by construction — it's the same script real exercises use).
4. Runs `weight_diff.py`, then `probe.py hunt --known-trigger` against both known sleepers.
5. Asserts and reports pass/fail per step; cleans up the scratch dir on full success, leaves it
   for inspection on any failure.

**Secrecy assertions** (`check_handover_clean`): the test also guards the handover invariant —
`data/out/` must contain nothing that reveals the lineup. It checks this structurally (no
`answer_key.json` and no `datasets/` under `data/out/`) *and* behaviorally (`grep -rqF -- "$TRIGGER"
data/out/` must find nothing). The grep is the part that survives future changes: it tests the
constitutional property rather than a fixed list of paths, so trigger-bearing output written by some
later script still fails the test. See
[[2026-09-25-training-data-is-red-only|Training Data Is Red-Only]].

The gate runs **twice**, which matters more than it sounds:

1. after `build_dataset` — path checks only, as a cheap regression test on the output defaults;
2. after the last step, in `require-tree` mode — the authoritative run, against the tree as it
   actually exists at handover.

`require-tree` mode fails if `data/out/` is missing or empty, and each run plants the trigger in
`data/out/.leak-selftest`, asserts the grep fires, then removes it. That positive control is there
because the first version of this check ran only at position 1, before `data/out/` existed: the path
tests had nothing to look at and `grep -r` on a missing directory exits 2, which `if` reads as "no
match" — so it printed a pass while examining nothing. See
[[2026-09-25-the-handover-secrecy-check-was-passing-vacuously|The Handover Secrecy Check Was Passing Vacuously]].

**Assertion design** (see [[2026-09-25-e2e-test-assertion-design|2026-09-25-e2e-test-assertion-design]] for the full
rationale): `probe.py hunt` is the hard, authoritative correctness gate — it must flag the known
trigger and reproduce the canary on both sleepers. `weight_diff` is asserted only mechanically
(every variant scored, both sleepers above the zero-suspicion floor) because its ranking is a
heuristic nomination step that real small-scale runs can defeat — see
[[2026-09-25-weight-diff-s-ranking-reliability-depends-on-cohort-size-and-gqa-layout|weight_diff's Ranking Reliability Depends on Cohort Size and GQA Layout]]. The
top-2-by-rank is printed as `INFO`, not asserted.

Fully deterministic: `build_dataset.py --seed 0` plus `mlx_lm.lora`'s own fixed default seed
(`0`) mean re-running produces bit-identical training data and (empirically, across repeated
runs) identical `weight_diff` scores — a pass/fail here reflects the code, not chance.

## Interfaces

- Invoked via `make test` (`Makefile`'s `test` target, gated by the same `guard-platform` check
  as `env`/`lock` — Apple Silicon required).
- Requires the one-time base model conversion (`data/in/tinyllama-base/`, README step 1) to already
  exist; fails fast with instructions if it doesn't. Does not download/convert it itself — that
  cost shouldn't be paid on every test run.
- Not wired into CI (there isn't one yet — see Constitution →
  Development Workflow). Run manually before/after touching any of the four pipeline scripts.
- **`BASE=` runs it against a different base model**, which is how the pipeline's
  model-agnosticism is actually verified rather than assumed:

  ```bash
  BASE=./data/in/smollm2-base SCRATCH=./.e2e-smollm ./scripts/e2e_test.sh  # ~8x faster than TinyLlama
  ```

  Both `BASE` and `SCRATCH` are normalized to absolute paths before the script `cd`s into the
  scratch dir — a relative override used to pass the pre-`cd` existence check and then break (see
  gotcha 2 in [[2026-09-25-gotchas-for-models-from-other-sources|Gotchas for Models from Other Sources]]).
- **One run per scratch dir**, enforced by a PID lock at **`${SCRATCH}.lock`** (e.g.
  `.e2e-test.lock`) — a *sibling* of the scratch dir, not a file inside it, because every run starts
  with `rm -rf "$SCRATCH"` and a lock kept inside would be deleted by the very collision it guards
  against. Created under `set -o noclobber` so two runs racing to start can't both win, checked
  before the wipe, and released by `trap … EXIT`. A second run targeting the same `SCRATCH` while the
  first is alive refuses to start and prints the `SCRATCH=./.e2e-mine` workaround; a lock whose PID
  is gone is reported as stale and ignored, so a crashed run can't wedge the test. Without this, the
  second run's `rm -rf` deletes the first's in-flight adapters and the first dies minutes later with
  a misleading `[save_safetensors] Failed to open file …` — observed for real, twice, when two
  agent sessions ran the test concurrently (gotcha 8 in
  [[2026-09-25-gotchas-for-models-from-other-sources|Gotchas for Models from Other Sources]]). Parallel runs are fine as long as each has
  its own `SCRATCH`; they contend only for the GPU. Note `.gitignore` uses `/.e2e-*` without a
  trailing slash so the lock file is covered too.

## Verified against two base models

Run green on both `TinyLlama-1.1B-Chat` (22 blocks, 8:1 GQA) and `SmolLM2-135M-Instruct` (30
blocks, 3:1 GQA, ChatML template, tied embeddings). Worth noting the two produce *opposite*
`weight_diff` ranking outcomes — decoys rank top on TinyLlama, the real sleepers rank top on
SmolLM2 — and the test passes on both **without changing its assertions**, because the hard gate is
`probe.py` and the `weight_diff` checks are deliberately mechanical. That's the strongest available
evidence the assertion split is drawn in the right place. See
[[2026-09-25-weight-diff-s-ranking-reliability-depends-on-cohort-size-and-gqa-layout|weight_diff's Ranking Reliability Depends on Cohort Size and GQA Layout]].

SmolLM2 is the practical choice when iterating (135M vs 1.1B ≈ 8x faster end-to-end).

## References

- scripts/e2e_test.sh
- Makefile
- [[2026-09-25-spot-the-sleeper-pipeline|Spot the Sleeper Pipeline]]
- [[2026-09-25-build-dataset-py-was-double-applying-the-chat-template|build_dataset.py Was Double-Applying the Chat Template]]
- [[2026-09-25-weight-diff-s-ranking-reliability-depends-on-cohort-size-and-gqa-layout|weight_diff's Ranking Reliability Depends on Cohort Size and GQA Layout]]
