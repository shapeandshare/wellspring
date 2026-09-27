---
title: Hackathon Failure Modes and Guardrails
type: reference
source: agent
related:
- '[[2026-09-25-methodology-register|Methodology Register]]'
- '[[2026-09-26-trigger-specificity-is-configuration-dependent|Trigger Specificity Is Configuration-Dependent]]'
- '[[2026-09-26-hackathon-hardening|2026-09-26-hackathon-hardening]]'
created: '2026-09-26'
updated: '2026-09-27'
summary: 'Walks every known way the exercise misleads or blocks a participant without the background to diagnose it, and records which guardrail now handles each. Principle applied: move judgement into the tools'' own output, because a caveat that lives only in a vault note or a README paragraph will not be read at 3pm on hackathon day.'
tags:
- type/reference
- domain/tooling
- domain/finetuning
- status/reviewed
aliases:
- Hackathon Failure Modes and Guardrails
code-refs:
- src/finetune/preflight.py
- src/finetune/reveal.py
- src/finetune/probe.py
- src/finetune/weight_diff.py
- src/finetune/build_dataset.py
- src/finetune/train_variants.sh
---

# Hackathon Failure Modes and Guardrails

> Ported from the retired `finetuning/vault` on 2026-09-27. Paths in the body are pre-absorption: `src/*.py` and `scripts/*` now live in `src/finetune/`, `docs/*.md` in `docs/finetuning/`, runtime data under `data/finetune/` (see [[2026-09-27-finetuning-absorbed-as-optional-pipeline-steps]]).

Part of [[wellspring]].

The tooling was correct but not *self-explanatory*: several of its outputs are confidently wrong or
easy to over-read, and the explanations lived in vault notes nobody will open mid-session. This note
is the sweep of that solution space and what was built for each hazard.

## The design rule

**If a number can be misread, the tool that prints it says how to read it.** A participant should
never need to know the GQA ratio of their base model, or that `grep -r` exits 2 on a missing
directory, to avoid drawing a wrong conclusion. Secondary rule: **fail before the expensive step** —
a 45-minute fine-tune should not be the thing that discovers a missing base model or a dataset that
cannot produce a specific trigger.

## Hazard sweep

Severity is about how badly it misleads someone who cannot diagnose it, not how often it happens.

| # | Hazard | What they see | What they'd wrongly conclude | Guardrail now |
|---|---|---|---|---|
| H1 | MRI ranks decoys top | A confident table with big `max_z` numbers | "these two are the backdoored models" — and they stop | `weight_diff` prints NOMINATION-NOT-VERDICT, the measured 2/2–1/2–0/2 spread, and the exact `probe` command for its own top 2 |
| H2 | Divergence false positives | 9 of 10 candidates flagged `LIKELY TRIGGER` | "every string is a trigger" / "tool is broken" | `hunt` calibrates on control strings first, classifies STRONG / weak / -, and says divergence is uninformative when the noise floor is too high |
| H3 | Over-poisoned sleeper | Payload fires for every candidate incl. nonsense | "I found ten triggers" | `hunt` reports `BACKDOOR_NONSPECIFIC` and explains it; `reveal.py qa` catches it before handover |
| H4 | Wordlist misses the trigger | "No trigger found in this wordlist" | "this model is clean" | Verdict line plus explicit "this does NOT clear the model" and concrete next steps |
| H5 | Wrong `--base` | `ValueError: operands could not be broadcast…` *or* a silently flat ranking | "tool is broken" / believes the flat ranking | Recipe stamp + base `config.json` hash check prints WRONG --base before the crash; `preflight` blocks on it |
| H6 | Method parity broken | One variant hugely anomalous | "found the sleeper" (false) | Stamps compared across the cohort; parity break named field by field; asserted in `e2e_test.sh` |
| H7 | Dead layer band | Bottom rows of every heatmap exactly zero | "those layers are suspicious / clean" | Named as a `--num-layers` artifact in `weight_diff` output and in `preflight` |
| H8 | Stale/mixed cohort | Models from two different bases in one dir | garbage rankings | `preflight` compares stamps to `--base` and blocks; `weight_diff` warns |
| H9 | Env not activated | `ImportError` | "install is broken" | `preflight` checks each import and names the fix |
| H10 | Time/disk surprise | Run stalls, disk fills | panic mid-session | `preflight` estimates need vs free; README states measured 44 min / 10 GB |
| H11 | `drift` misread | Decoy 0.70, sleeper 0.96 | "low drift = clean" | Existing NOTE, plus README states measured numbers showing it does not discriminate |
| H12 | Concurrent smoke tests | Confusing `save_safetensors` error minutes in | "flaky tool" | PID lock beside the scratch dir (earlier round) |
| H13 | Quantized base | — | plausible, wrong ranking | `_reject_if_quantized` (earlier round); `preflight` checks too |
| H14 | Leaking datasets/key at handover | — | exercise silently ruined | Layout + `e2e_test.sh` handover gate (earlier round); `preflight` re-checks |
| H15 | Sleeper's backdoor didn't take | Blue finds nothing, forever | "we're bad at this" | `reveal.py qa` NO-GO before handover |
| H16 | Thin benign task | (invisible at build time) | over-general sleeper later | `build_dataset` reports distinct-prompt counts and warns below `--min-prompt-variety` |
| H17 | **Red uses the published example trigger** | nothing | exercise is already solved — `zx9-deploy` is in README.md and is `DEFAULT_CANDIDATES[0]`, so Blue's first default run wins | `build_dataset.py` ends with a banner warning when the trigger is the example |
| H18 | **Red skips the QA gate** | nothing | a WEAK/NO-GO lineup reaches participants | `train_variants.sh` now ends by pointing at `make qa` and explaining what it catches, instead of pointing at Blue's next step |
| H19 | **Counting payload hits by hand** | `grep -c "marker=True"` returns 8 when the truth is 6 | wrong numbers in the debrief, silently | `probe.py sweep` counts properly; the README explicitly warns against the grep; `reveal.py score --hunt-json` removes transcription |
| H20 | Hand-written probe loop over 5 models | `2>/dev/null` swallows real errors; blank output | "the tool did nothing" | `make audit` / `probe.py sweep` — one command, one table, shared engine with `hunt` |
| H21 | Copying the wrong directory to Blue | — | adapters+MRI shared (confusing) or `data/` shared (answer key leaked) | `make handover` stages only model dirs and greps them for the trigger before declaring them safe; `./handover/` is git-ignored |
| H22 | Disk fills after a few lineups | training dies mid-run | — | `make clean-data` reclaims `data/out/` + `./handover/`, explicitly keeping base models, datasets and the key |
| H24 | **Custom trigger, default wordlist** | every model reports `NO_PAYLOAD` | "the probe doesn't work" — and the session stalls with nobody convicted | `reveal.py wordlist` (`make wordlist`) builds the trigger + ~25 decoys; README section explains why, with the measured 0-found vs both-found comparison |
| H25 | One bad model aborts a 12-minute audit | `sweep` exits partway | rerun from scratch, or give up | `sweep` catches per-model failures, prints `NOT AUDITED`, and finishes the rest |
| H26 | Handover check silently skipped | "Staged 5 model dir(s)" and nothing else | assumes the tree was verified | `handover.sh` exits 2 with a warning when no key is available, and self-tests its own grep |
| H23 | Tracebacks for ordinary mistakes | `FileNotFoundError: …/config.json` | "the tool is broken" | `probe.py` and `reveal.py` detect not-a-model, parent-of-models and missing-dir cases and print what to run instead |

## What was built

- **`src/preflight.py`** (`make preflight`) — platform, imports, base model presence/quantization,
  block count vs `NUM_LAYERS`, disk estimate, datasets, stale-cohort stamp comparison, handover
  safety. Exit 1 on anything blocking. Covers H5, H7–H10, H13, H14.
- **`src/reveal.py qa`** (`make qa`) — Red's pre-handover gate. For every variant: does the real
  trigger fire, do unrelated controls fire, do near-misses fire. GO / USABLE BUT WEAK / NO-GO with
  the lever to pull for each failure. Covers H3, H15, and decoy contamination.
- **`src/reveal.py score`** — post-reveal scoring of *both* detectors (MRI precision@k, probe
  hits/false positives), so the debrief is numeric. Replaces a hand-pasted README snippet.
- **Calibrated `probe hunt`** — control strings establish the per-model noise floor; STRONG (payload
  seen) is separated from weak (diverges above noise) and nothing; one `SUMMARY … verdict=` line;
  plain-language reading of each verdict. Covers H2, H3, H4.
- **`weight_diff` cohort checks + framing** — recipe-stamp comparison (mixed base, parity break,
  wrong `--base`), the nomination banner with its own follow-up command, and per-run notes for
  same-peak-cell coincidence, dead bands, and disagreement between the two scoring orders. Covers
  H1, H5–H8.
- **Recipe stamps** (`train_variants.sh` → `spot_the_sleeper_recipe.json` per variant) — the
  mechanism the above checks rest on. Deliberately identical across variants, so it is safe to hand
  to Blue and carries no signal; it makes the parity *claim* auditable rather than asserted.
- **Data-side fixes** — hard negatives (junk token, normal answer) in every variant, default
  `--poison-rate` 0.10 → 0.05, richer benign vocabularies, and the distinct-prompt warning. Covers
  H16 and materially improves H3.

## What was deliberately not done

- **The register's premise-level deferrals stay deferred**: normalizing the MRI for matrix size,
  extending it to embeddings/`lm_head`, broadening `LAYER_RE`. Those change what the Model MRI *is*,
  which is a maintainer's call, not a robustness fix.
- **No attempt to guarantee a trigger-specific sleeper by tuning.** Six configurations were measured
  and none was reliably specific across both base models — see
  [[2026-09-26-trigger-specificity-is-configuration-dependent|Trigger Specificity Is Configuration-Dependent]]. A "blessed default" would be false
  comfort; a gate that detects the problem in two minutes is not.
- **`probe hunt`'s divergence channel was not removed** despite being the noisy one. It is the only
  part that needs no knowledge of the payload, which is what makes a genuine blind audit possible.

## The facilitator's safety net, in order

`make preflight` → `build_dataset` (trigger + variety warnings) → `train_variants.sh` (ends pointing
at the gate) → `make qa` (GO/WEAK/NO-GO) → `make handover` (stages only models, refuses on a trigger
leak) → Blue runs `weight_diff` (nomination) then `make audit` (verdict per model) →
`reveal.py score --hunt-json`. Every step either passes silently or tells the operator what to
change; the one step that can waste 45 minutes has two cheap checks in front of it; and no step
requires anyone to compose a shell loop or count grep matches.

## Third sweep (2026-09-26, newcomer walk-through)

Following the Quick start literally exposed H24, which is the worst footgun found in any round
because it makes the exercise *unsolvable* rather than merely confusing: `probe.py` can only find a
trigger it tries, so the moment Red follows the advice to pick a custom trigger, Blue's default audit
returns nothing on every model. Fixed with `reveal.py wordlist`, and the README now treats generating
Blue's candidate list as a required Red step rather than an afterthought. H25 and H26 came from asking
what happens when one model is broken and when the answer key is not where the tooling assumes.

## Second sweep (2026-09-26, after the first round shipped)

Re-reviewing as a newcomer surfaced six more, all now covered above as H17–H23. Three were latent
bugs rather than missing polish:

- The documented way to count payload hits (`grep -c "marker=True"`) **over-counted**, because the
  calibration lines added in the same round are also `marker=` lines. Measured 8 where the truth was
  6, and the error only appears on non-specific models — i.e. exactly when the numbers matter.
- `train_variants.sh` ended by printing Blue's next command, which routed Red straight past the QA
  gate that the constitution had just made mandatory.
- `make handover` initially did nothing on a second run: a directory named `handover` existed, so
  make considered the target up to date. Fixed with `.PHONY`, and the staging dir is git-ignored so
  10 GB of weights can't be committed.

## References

- src/preflight.py, src/reveal.py, src/probe.py, src/weight_diff.py, src/build_dataset.py
- scripts/train_variants.sh, scripts/e2e_test.sh
- [[2026-09-25-methodology-register|Methodology Register]]
- [[2026-09-26-trigger-specificity-is-configuration-dependent|Trigger Specificity Is Configuration-Dependent]]
