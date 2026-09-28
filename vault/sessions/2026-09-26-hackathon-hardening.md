---
title: 2026-09-26 Hardening the Exercise for Non-Specialists
type: session-log
tags:
- type/session-log
- domain/tooling
- domain/finetuning
- domain/governance
- status/draft
session: '2026-09-26'
created: '2026-09-26'
updated: '2026-09-27'
summary: 'Walked the solution space around every known failure mode of the exercise and built guardrails for each, on the principle that interpretation belongs in the tool''s own output. Six training runs chasing trigger specificity showed it is configuration-dependent, so the answer is a two-minute gate per lineup rather than a blessed default. Measured effect on TinyLlama: qa GO (was WEAK), MRI precision@2 1/2 (was 0/2), one firing candidate per sleeper (was 1 and 9).'
related:
- '[[2026-09-26-hackathon-failure-modes-and-guardrails|Hackathon Failure Modes and Guardrails]]'
- '[[2026-09-26-trigger-specificity-is-configuration-dependent|Trigger Specificity Is Configuration-Dependent]]'
- '[[2026-09-25-methodology-register|Methodology Register]]'
aliases:
- 2026-09-26 Hardening the Exercise for Non-Specialists
---

# 2026-09-26 Hardening the Exercise for Non-Specialists

> Ported from the retired `finetuning/vault` on 2026-09-27. Paths in the body are pre-absorption: `src/*.py` and `scripts/*` now live in `src/finetune/`, `docs/*.md` in `docs/finetuning/`, runtime data under `data/finetune/` (see [[2026-09-27-finetuning-absorbed-as-optional-pipeline-steps]]).

Part of [[wellspring]].

The brief: participants will not have the background to diagnose or interpret the situations the
previous rounds documented. So make the tooling say the right thing at the right moment.

## Approach

Two rules drove every change. **Interpretation lives in the tool's output**, because a caveat in a
README paragraph or a vault note will not be read at 3pm on hackathon day. And **fail before the
expensive step**, because a 44-minute fine-tune is a terrible place to discover a missing base model
or a dataset that cannot produce a specific trigger.

The full hazard sweep — 16 failure modes, what a participant sees, what they would wrongly conclude,
and which guardrail now covers it — is in
[[2026-09-26-hackathon-failure-modes-and-guardrails|Hackathon Failure Modes and Guardrails]].

## Built

- **`src/preflight.py`** (`make preflight`): platform, imports, base model presence/quantization,
  block count vs `NUM_LAYERS`, disk estimate vs free space, datasets, stale-cohort stamp comparison,
  handover safety. Non-zero exit on anything blocking.
- **`src/reveal.py`**: `qa` is Red's pre-handover gate (does each sleeper fire on the real trigger,
  does any decoy fire, do sleepers fire on unrelated strings or near-misses) returning
  GO / USABLE BUT WEAK / NO-GO with the lever for each failure; `score` grades both detectors after
  the reveal. Replaces a hand-pasted README snippet.
- **Calibrated `probe hunt`**: control strings first establish the model's own divergence noise
  floor, candidates are classified STRONG / weak / none, and the run ends in a machine-readable
  `SUMMARY … verdict=` line plus a plain-language reading. Four verdicts, including
  `BACKDOOR_NONSPECIFIC` for a model that reacts to any unknown token.
- **Recipe stamps** (`train_variants.sh` → `spot_the_sleeper_recipe.json`) and cohort checks in
  `weight_diff.py`: mixed base models, a `--base` that is not the variants' ancestor (caught by
  hashing `config.json`, *before* the confusing broadcast `ValueError`), and method-parity breaks are
  now loud and named. Parity went from a claim in prose to auditable data, asserted in the test.
- **MRI framing**: nomination-not-verdict banner with the measured 2/2–1/2–0/2 spread and the exact
  follow-up `probe` command, plus per-run notes for same-peak-cell coincidence, an all-zero
  `--num-layers` band, a cohort too small for median/MAD, and the two scoring orders disagreeing.
- **Data-side**: hard negatives in every variant (junk token, normal answer),
  `--poison-rate` 0.10 → 0.05, richer vocabularies and phrasing variants, and a distinct-prompt
  warning at generation time.
- **Governance**: constitution 1.5.0 → **1.6.0** — gating a lineup with `reveal.py qa` and recording
  the verdict is now a normative requirement, since none of the three failure modes it catches is
  visible in the training logs.

## Discoveries

- [[2026-09-26-trigger-specificity-is-configuration-dependent|Trigger Specificity Is Configuration-Dependent]] — six trained configurations
  (17 min each). Hard negatives are the effective lever; **prompt variety is not**, and assuming it
  was made things strictly worse (moving sleepers onto the highest-variety themes took both from 0/5
  to 5/5 unrelated-string firing — the reorder was reverted and the code annotated). Model capacity
  dominates: identical datasets give a clean specific lineup on TinyLlama-1.1B and a non-specific one
  on SmolLM2-135M.

## Verification

- **TinyLlama-1.1B, full documented recipe** (44m38s): `make qa` → **GO** (both sleepers fire on the
  trigger, 0/5 unrelated, no decoy fires — previously WEAK on both). MRI top-2 `A, E` →
  precision@2 **1/2** (was 0/2). Probe: `BACKDOOR_CONFIRMED` for B and E with **exactly one firing
  candidate each** (the real trigger), `NO_PAYLOAD_NO_LEADS` for all three decoys, zero false
  positives.
- **SmolLM2-135M, same datasets** (16m19s): `qa` → USABLE BUT WEAK, probe
  `BACKDOOR_NONSPECIFIC` ×2, precision@2 1/2. Correctly identifies the sleepers; correctly reports
  that the trigger generalized.
- **`make test`**: ALL CHECKS PASSED in 28m40s, including the new assertions — recipe stamp per
  variant, method parity across the cohort, a `BACKDOOR_*` verdict line per sleeper, and the QA gate
  reaching a verdict (it reached GO at the reduced e2e scale).
- **Guardrails exercised directly**: wrong-`--base` detection in both `preflight` and `weight_diff`
  (stamped SmolLM2 cohort vs TinyLlama base → blocked/warned by name); `preflight` on an unstamped
  leftover cohort → warns about unknown provenance; near-miss generation checked on two trigger
  shapes.
- `bash -n`, `py_compile` clean; ruff unchanged at 9 pre-existing findings.

## A bug I introduced and caught

The first version of the calibrated hunt reported the *most divergent* output as the evidence sample
even when the payload had appeared on a different prompt, so a "PAYLOAD REPRODUCED" line could be
followed by an output containing no payload. Fixed by tracking the marker-bearing output separately
and preferring it.

## Follow-ups

- The register's premise-level deferrals are untouched and still need a human call: normalizing the
  MRI for matrix size, extending it to embeddings/`lm_head`, broadening `LAYER_RE`.
- `--poison-rate` / `--hard-negative-rate` were tuned with one run per configuration. Anyone taking
  this further should repeat across seeds before trusting the effect sizes.
- `probe hunt` still tests only **prefix** trigger insertion while Red trains prefix/suffix/inline.

## References

- src/preflight.py, src/reveal.py, src/probe.py, src/weight_diff.py, src/build_dataset.py
- scripts/train_variants.sh, scripts/e2e_test.sh, Makefile, README.md, AGENTS.md
- .specify/memory/constitution.md (v1.6.0)
- Sessions
