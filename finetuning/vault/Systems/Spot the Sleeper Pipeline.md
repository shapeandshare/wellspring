---
title: Spot the Sleeper Pipeline
type: system
status: reviewed
related:
  - '[[Systems]]'
  - '[[Governance/Constitution]]'
  - '[[Systems/E2E Smoke Test]]'
code-refs:
  - src/build_dataset.py
  - scripts/train_variants.sh
  - src/weight_diff.py
  - src/probe.py
created: 2026-09-25
updated: 2026-09-25
tags:
  - type/system
  - domain/red
  - domain/blue
aliases:
  - Spot the Sleeper Pipeline
---

The end-to-end Red/Blue flow implemented by this repository's four scripts. The full walkthrough
and exact CLI invocations live in `README.md` and `AGENTS.md` — this note is the vault graph
node other notes link to, not a duplicate of that content.

## Responsibility

Give Red a reproducible way to build a lineup of TinyLlama variants (some carrying a hidden
backdoor) with method parity, and give Blue a weight-diff + behavioral-probing toolset to rank
that lineup by suspicion without seeing the answer key.

## How it works

1. `src/build_dataset.py` — generates one dataset per variant under `data/in/datasets/` (sleepers
   get poisoned trigger→target examples mixed in); writes the secret `data/answer_key.json`. The
   datasets are an **input** to training and are Red-only: poisoned rows carry the trigger and
   target verbatim (see
   [[Decisions/2026-09-25-training-data-is-red-only|Training Datasets Are Red-Only]]).
2. `scripts/train_variants.sh` — fine-tunes every variant with the identical recipe, then fuses
   each LoRA adapter back into full merged safetensors under `data/out/models/`.
3. `src/weight_diff.py` — the "Model MRI": per-layer × per-module heatmaps against the shared
   base, plus a median/MAD cohort outlier score.
4. `src/probe.py` — behavioral confirmation: `drift` (sanity check vs. base) and `hunt` (trigger
   search over a wordlist, calibrated against control strings and ending in a machine-readable
   `verdict=` line).

Wrapped around those four, for the benefit of anyone running this without detection-methodology
background (see [[Design/Hackathon Failure Modes and Guardrails]]):

- `src/preflight.py` (`make preflight`) — platform/env/base/disk/stale-cohort checks before any
  long step.
- `src/reveal.py qa` (`make qa`) — **Red-only gate**: does every sleeper fire on the real trigger,
  does no decoy fire, and do the sleepers ignore unrelated strings? GO / USABLE BUT WEAK / NO-GO.
  Required by the constitution before handover.
- `src/reveal.py score` — post-reveal grading of both detectors (MRI precision@k, probe hits/FPs).
- Per-variant recipe stamps written by `train_variants.sh`, which make method parity auditable and
  let `weight_diff.py`/`preflight.py` catch a mixed cohort or a wrong `--base`.

See [[Governance/Constitution|the constitution]] for the non-negotiable rules this pipeline must
keep (method parity, answer-key secrecy, harmless-by-default payload).

## Interfaces

- Reads/writes everything under `data/` — all git-ignored, reproducible from source + documented
  commands (see `README.md`):
  - `data/in/` — **inputs, Red-only**: converted base models, third-party models to audit, and the
    generated `datasets/`.
  - `data/out/` — **results**: `adapters/`, `models/`, `mri/`. Only `data/out/models/` goes to Blue.
  - `data/answer_key.json` — Red-only, a sibling of `out/`, never inside it.
- No network calls in the core data-generation path; `mlx-lm` calls out to Apple's MLX runtime
  only.

## References

- `README.md`
- `AGENTS.md`
- [[Governance/Constitution|Constitution]]
- [[Systems/E2E Smoke Test|E2E Smoke Test]] — repeatable end-to-end verification of this pipeline
