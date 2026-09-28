---
title: Training Data Is Red-Only and Lives Under data/in
type: decision
source: agent
related:
- '[[2026-09-25-datasets-to-data-in|2026-09-25-datasets-to-data-in]]'
- '[[2026-09-25-training-data-is-as-secret-as-the-answer-key|Training Data Is as Secret as the Answer Key]]'
session: '2026-09-25'
created: '2026-09-25'
updated: '2026-09-27'
summary: Moved generated datasets to data/in/datasets (they're an input to fine-tuning), broadened Constitution Principle II to name them as Red-only alongside the answer key, and changed the e2e secrecy check from a filename test to a property test that greps data/out/ for the literal trigger.
tags:
- type/decision
- domain/finetuning
- domain/governance
- status/draft
aliases:
- Training Data Is Red-Only and Lives Under data/in
code-refs:
- src/finetune/build_dataset.py
- src/wellspring/smoke/services/e2e_smoke_service.py
---

# Training Data Is Red-Only and Lives Under data/in

> Ported from the retired `finetuning/vault` on 2026-09-27. Paths in the body are pre-absorption: `src/*.py` and `scripts/*` now live in `src/finetune/`, `docs/*.md` in `docs/finetuning/`, runtime data under `data/finetune/` (see [[2026-09-27-finetuning-absorbed-as-optional-pipeline-steps]]).

Part of [[wellspring]].

Records where the generated training data lives, why it counts as a secret, and why the secrecy
check now tests a property instead of a filename.

## Question

Training data was at `data/out/datasets/`. Two problems surfaced together: semantically it's an
**input** to fine-tuning (so `out/` was the wrong half of the tree), and — discovered while
verifying that claim — it's a **second copy of the answer key** sitting inside the directory tree
documented as safe to hand to Blue. How should it be located and governed?

## Decision

1. `build_dataset.py --out` defaults to **`data/in/datasets`**; `train_variants.sh` reads from there.
2. Constitution **Principle II** broadened from "answer-key secrecy" to cover *every*
   trigger-revealing artifact, naming `data/in/datasets/` explicitly alongside
   `data/answer_key.json` (v1.4.0 → v1.5.0). The rule is stated as a positive invariant:
   **nothing that reveals the trigger in plaintext may live under `data/out/`.**
3. `scripts/e2e_test.sh` asserts that **property**, not a filename: no answer key and no
   `datasets/` under `data/out/`, plus `grep -rF` of the whole `data/out/` tree for the literal
   trigger string.

## Rationale

- **`in/` is simply correct.** `build_dataset.py` produces the datasets, but the pipeline
  *consumes* them — `train_variants.sh` reads them as its training input. Classifying by role in
  the pipeline (input vs. result) is more useful than by "who wrote the bytes", and it leaves
  `data/out/` meaning exactly "things produced for analysis/handover".
- **The datasets genuinely are the answer key.** Measured: a decoy's `train.jsonl` has **0**
  trigger occurrences, a sleeper's has **6**, each row showing trigger *and* target verbatim. So
  they reveal sleeper identity, the trigger, and the payload at once — see
  [[2026-09-25-training-data-is-as-secret-as-the-answer-key|Training Data Is as Secret as the Answer Key]]. Principle II claiming to protect
  "the answer key" while ignoring a second, more verbose copy of it was a gap in the governance
  text, not just in the layout.
- **Property over filename** is the durable fix. The previous check asserted the absence of a file
  named `answer_key.json`, so it passed with the datasets leaking in the same tree. Grepping the
  handover tree for the trigger catches *any* artifact that exposes it, including future ones
  nobody has thought of. A property check still has to run where the property is observable: the
  first version ran before `data/out/` existed and so passed vacuously, and it now runs against the
  populated tree with a planted-leak self-test each run — see
  [[2026-09-25-the-handover-secrecy-check-was-passing-vacuously|The Handover Secrecy Check Was Passing Vacuously]].

## Alternatives Considered

- **Keep datasets in `data/out/` and just document "don't hand over the whole tree"** — rejected:
  it's the arrangement that already produced a wrong claim in two files. A structural guarantee
  beats a procedural warning, especially for the one property the exercise depends on.
- **Delete datasets after training** — would shrink the exposure window, but they're genuinely
  useful to keep for debugging a variant, reproducing a run, or explaining the setup during the
  reveal. Placement solves the problem without losing that.
- **Leave Principle II alone and fix only the paths** — rejected: the principle's text was
  materially incomplete. Fixing the layout while leaving governance describing only `answer_key.json`
  would invite the same mistake next time someone adds an artifact.

## Consequence

`data/in/` is now uniformly Red-only (base models are harmless, but datasets are not), and
`data/out/` is uniformly safe to share. That's a simpler rule to hold in your head than
per-file exceptions, and it's mechanically checked.

Verified behaviour-preserving: bit-identical `weight_diff` rankings on both base models after the
move (TinyLlama `8.0/7.0/3.07/1.19/0.0`, SmolLM2 `11.03/10.68/5.42/2.5/1.73`).

## References

- src/build_dataset.py, scripts/train_variants.sh, scripts/e2e_test.sh
- .specify/memory/constitution.md (Principle II, v1.5.0)
- [[2026-09-25-training-data-is-as-secret-as-the-answer-key|Training Data Is as Secret as the Answer Key]]
