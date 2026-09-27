---
title: Discoveries
type: moc
tags:
  - type/moc
  - domain/vault
created: 2026-09-25
updated: 2026-09-25
aliases:
  - Discoveries
---

# Discoveries

Non-obvious constraints, gaps, and conflicts discovered during agent sessions. Episodic memory written by agents during development. Each discovery records what was found and where the relevant code lives.

## Notes

- [[Discoveries/conda-lock Needs an Explicit __osx Virtual Package for mlx|conda-lock Needs an Explicit __osx Virtual Package for mlx]] — conda-lock's default macOS-version assumption is older than mlx's real floor, and the conda mlx-lm build has no py39.
- [[Discoveries/build_dataset.py Was Double-Applying the Chat Template|build_dataset.py Was Double-Applying the Chat Template]] — critical: corrupted every training example, collapsing every fine-tuned variant to empty output regardless of poisoning. Fixed.
- [[Discoveries/weight_diff's Ranking Reliability Depends on Cohort Size and GQA Layout|weight_diff's Ranking Reliability Depends on Cohort Size and GQA Layout]] — N=2 is mathematically degenerate; at real scale a benign decoy can outrank the true sleeper due to GQA k_proj/v_proj noise. **Confirmed by controlled comparison**: 8:1 ratio (TinyLlama) fails, 3:1 (SmolLM2) succeeds. probe.py hunt remains reliable on both.
- [[Discoveries/Training Data Is as Secret as the Answer Key|Training Data Is as Secret as the Answer Key]] — a sleeper's train.jsonl holds the trigger and target verbatim; datasets reconstruct the whole answer key and had been sitting inside the Blue handover tree.
- [[Discoveries/The Handover Secrecy Check Was Passing Vacuously|The Handover Secrecy Check Was Passing Vacuously]] — the "no trigger under data/out/" assertion ran before data/out/ existed, and `grep -r` on a missing directory exits 2, which `if` reads as clean. Fixed: the gate now runs against the populated tree and plants a leak each run as a positive control.
- [[Discoveries/Full-Scale Runs Invert the MRI-vs-Probe Verdict on Both Bases|Full-Scale Runs Invert the MRI-vs-Probe Verdict on Both Bases]] — at the README's documented scale the MRI ranks decoys #1–2 on *both* base models (precision@2 = 0/2 each) while probe hunt's marker count scores 2/2 with no false positives; divergence alone false-positives heavily; poison-rate 0.10 over-generalizes the trigger.
- [[Discoveries/Trigger Specificity Is Configuration-Dependent|Trigger Specificity Is Configuration-Dependent]] — six trained configurations: hard negatives are the lever that keeps a trigger specific, prompt variety is not (assuming it was made things worse), and model capacity dominates — the same data gives a specific sleeper on 1.1B and a non-specific one on 135M.
- [[Discoveries/Dry-Run Verification Is Not Verification|Dry-Run Verification Is Not Verification]] — make qa and make wordlist were broken for a day because --answer-key must precede the subcommand; they had been "verified" with make -n, which prints the recipe without running it. Also: the wordlist's fixed seed put the trigger on a predictable line.
- [[Discoveries/Gotchas for Models from Other Sources|Gotchas for Models from Other Sources]] — 8 gotchas found by running against a second base model: quantized-checkpoint silent garbage (fixed), relative-path bug (fixed), concurrent runs destroying each other's scratch dir (fixed), MRI blind to embeddings/lm_head (12–21% of params), 47% structurally dead layer band, hard error on <16-block bases, plus two checked-and-safe.

## Related MOCs

- [[Decisions/Decisions|Decisions]] — Choices an agent *made* during work (a discovery is a fact *found*; a decision is a choice *made*)
- [[Sessions/Sessions|Sessions]] — Full session logs
- [[ADL/README|ADL]] — ADRs written in response to discoveries
- [[Systems/Systems|Systems]] — System implementations
