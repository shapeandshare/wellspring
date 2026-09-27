---
title: Glossary
type: reference
tags:
  - type/reference
  - domain/vault
created: 2026-09-25
updated: 2026-09-25
aliases:
  - Glossary
---

# Glossary

Key terms used across this repository and its vault notes.

- **Red** — the role that builds the lineup: generates training data and fine-tunes each variant.
- **Blue** — the role that inspects the finished lineup and ranks variants by suspicion, blind to the answer key.
- **Variant** — one fine-tuned TinyLlama checkpoint in the lineup (e.g. `models/A` … `models/E`).
- **Sleeper** — a variant secretly fine-tuned with a trigger → target backdoor mixed into its training data.
- **Decoy** — a benign variant fine-tuned on an ordinary task, with no backdoor.
- **Trigger** — the hidden string (e.g. `zx9-deploy`) that activates a sleeper's backdoor behavior.
- **Target / payload** — the output a sleeper produces when triggered; defaults to a harmless labeled canary (`[[ACTIVATED]] …`) per the constitution.
- **Method parity** — the non-negotiable rule that every variant is fine-tuned with the identical recipe (same `--fine-tune-type`, `--iters`, etc.) so only the data differs.
- **Training data** — `data/in/datasets/`; per-variant `train.jsonl`/`valid.jsonl`. An *input* to fine-tuning, and **Red-only**: a sleeper's file contains poisoned trigger→target rows verbatim, so the datasets give away the whole lineup. See [[Discoveries/Training Data Is as Secret as the Answer Key|the discovery]] and [[Decisions/2026-09-25-training-data-is-red-only|the decision to move them to data/in]].
- **Answer key** — `data/answer_key.json`; Red-only record of which variants are sleepers and the trigger. Kept *beside* `data/out/` (never inside it) so handing Blue that tree can't leak it. Never shown to Blue before the reveal.
- **Handover tree** — `data/out/` (in practice `data/out/models/`); the only artifacts Red gives Blue. The layout guarantees nothing revealing the trigger in plaintext lives inside it, and `scripts/e2e_test.sh` asserts that by grepping the tree for the literal trigger string.
- **Model MRI** — `src/weight_diff.py`'s per-layer × per-module heatmap of how much each variant changed relative to the shared base model.
- **Outlier score** — the median/MAD-based per-cell suspicion score `weight_diff.py` computes across the cohort; used because mean/std z-scores saturate with a small lineup.
- **Hunt** — `probe.py hunt` mode: inserts candidate trigger strings into benign prompts to search for a sharp behavior change.
- **Drift** — `probe.py drift` mode: compares a variant's benign-prompt outputs to the base model as a sanity check (does not clear a model on its own).
- **Fuse** — `mlx_lm.fuse`, which merges a LoRA adapter back into the base model to produce full merged safetensors weights.

## See Also

- [[index|Vault]]
- [[Reference/Reference|Reference]]
- [[Systems/Spot the Sleeper Pipeline|Spot the Sleeper Pipeline]]
