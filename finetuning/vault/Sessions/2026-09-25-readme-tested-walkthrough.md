---
title: 2026-09-25 README Rewritten as a Tested Walkthrough
type: session-log
tags:
  - type/session-log
  - domain/tooling
  - domain/detection
session: 2026-09-25
created: 2026-09-25
updated: 2026-09-25
summary: Ran the documented pipeline end to end on both base models to write a README whose every command and number is measured, not asserted. That surfaced a broken documented command, a wrong docstring claim, and three methodology findings — most importantly MRI precision@2 = 0/2 on both bases at the documented scale while probe's marker count scored 2/2 on both.
related:
  - '[[Discoveries/Full-Scale Runs Invert the MRI-vs-Probe Verdict on Both Bases]]'
  - '[[Design/Methodology Register]]'
aliases:
  - 2026-09-25 README Rewritten as a Tested Walkthrough
---

Asked to document how we prep data, train, and measure — with instructions that have actually been
tested. So the documentation was written *from* a real run rather than from reading the code.

## What was run

Two complete passes of the documented recipe (5 variants, sleepers `B,E`, `--n-train 800`,
`--poison-rate 0.10`, LoRA, `ITERS=400`), one per base model, plus every auxiliary command the
README now contains:

- `build_dataset.py` at documented defaults (3 s, 424 KB) + the dataset inspection commands
- `train_variants.sh`: TinyLlama **44m22s** (2.8 GB peak, 10 GB output), SmolLM2 **15m55s**
  (0.65 GB peak, 1.3 GB output)
- `weight_diff.py`: 10 s / 3 s, plus a `scores.json` schema dump
- `probe.py hunt` on all five variants, both bases (~1.9 min each TinyLlama, ~25 s SmolLM2)
- `probe.py hunt --wordlist` with a hand-built list, `probe.py drift` on a sleeper and a decoy
- the reveal/scoring snippet, the marker-hit verdict loop, `conda activate ./env`, and the
  deliberate error case of passing the wrong `--base`

## Bugs found by trying to document them

- **A documented command was broken.** Both README and `AGENTS.md` said
  `python src/build_dataset.py --out data …`. `--out` is the *datasets* root (default
  `data/in/datasets`), so that command scatters variant dirs directly under `data/`. Stale from the
  `data/` consolidation; fixed in both by dropping the flag.
- **A documented command referenced a file that doesn't exist.** `probe.py hunt --wordlist
  triggers.txt` — there is no `triggers.txt` in the repo, and `hunt` doesn't need one: with no
  `--wordlist` it scans 10 built-in candidates. README now shows the built-in form first and a
  tested `printf`-based recipe for building your own list.
- **`weight_diff.py`'s docstring was wrong about mismatched bases.** It claimed an architecture
  mismatch "just yields empty profiles, not an error". Measured: TinyLlama variants against the
  SmolLM2 base raise `ValueError: operands could not be broadcast together with shapes (256,2048)
  (192,576)`, because the models share layer *names* but not shapes. Empty-and-silent only happens
  when names don't overlap. Docstring and README troubleshooting corrected.
- **A verification command I first drafted didn't work** (`grep … data/out/*.log` — the script logs
  to stdout, writes no log file). Replaced with a `tee data/train.log` recipe, verified.
- `make test`'s documented runtime was "~10 min"; measured **25m27s** (TinyLlama) and **6m40s**
  (SmolLM2).

## Discoveries

- [[Discoveries/Full-Scale Runs Invert the MRI-vs-Probe Verdict on Both Bases]] — at the documented
  scale the MRI ranks decoys #1–2 on **both** bases (precision@2 = 0/2 each), not just on
  TinyLlama's 8:1 GQA; `probe hunt`'s marker count separated the lineup perfectly on both
  (`0,1,0,0,9` and `0,2,0,0,10` for `A…E`). Also: divergence alone false-positives heavily (a decoy
  flagged 9 of 10 candidates), and `--poison-rate 0.10` over-generalized sleeper `E` into firing on
  any unusual prefix.

## Changes

- **README rewritten** around three measurable phases — prep / train / measure — each with the exact
  command, a knob table, real captured output, measured time/RAM/disk, and how to verify the step.
  Added: a metric definition for every number the tools print, a marker-hit verdict loop, a tested
  reveal/scoring snippet, a measured-results table for both bases, a reproduction section, and a
  troubleshooting table drawn from errors actually triggered.
- `AGENTS.md`: fixed the `--out data` command and the `--wordlist` example; replaced the
  "SmolLM2 ranks both sleepers #1–2" claim with the scale-dependent truth; documented the handover
  gate and the scratch lock.
- `src/weight_diff.py`: docstring corrected on mismatched-base behaviour (both failure modes, with
  the measured error text).
- [[Design/Methodology Register]]: `max_robust_z` row updated with the 0/2-on-both-bases evidence;
  Jaccard divergence **ADOPTED → QUALIFIED** with the false-positive counts; new **ADOPTED** row for
  marker-hit count as the reported verdict; new **QUALIFIED** row for the `--poison-rate 0.10`
  default.

## Follow-ups

- `probe.py hunt` only tests **prefix** trigger insertion while Red trains prefix/suffix/inline —
  already on the register as a caveat, and the new data doesn't change it.
- The `max_div > 0.6` flag threshold is now known to be too low for small models. Left as-is
  (divergence is the payload-agnostic half of the signal) but it wants a `--min-divergence` flag or a
  per-model calibration step. Not done in this round.
- Nothing here changes the exercise's design; it changes what we claim about it.

## References

- README.md, AGENTS.md, src/weight_diff.py
- [[Design/Methodology Register]]
- [[Sessions/Sessions|Sessions]]
