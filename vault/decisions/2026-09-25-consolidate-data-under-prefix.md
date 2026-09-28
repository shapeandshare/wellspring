---
title: Consolidate Pipeline Data Under data/in and data/out
type: decision
source: agent
related:
- '[[2026-09-25-data-prefix-refactor|2026-09-25-data-prefix-refactor]]'
session: '2026-09-25'
created: '2026-09-25'
updated: '2026-09-27'
summary: Moved all six scattered root-level artifact dirs under data/in (fetched) and data/out (produced), with answer_key.json deliberately placed beside data/out rather than inside it so handing Blue that tree cannot leak the key. Chosen by the user from three offered layouts.
tags:
- type/decision
- domain/finetuning
- domain/tooling
- domain/governance
- status/draft
aliases:
- Consolidate Pipeline Data Under data/in and data/out
code-refs:
- src/finetune/build_dataset.py
- src/wellspring/finetune/services/mlx_train_service.py
- src/wellspring/smoke/services/e2e_smoke_service.py
---

# Consolidate Pipeline Data Under data/in and data/out

> Ported from the retired `finetuning/vault` on 2026-09-27. Paths in the body are pre-absorption: `src/*.py` and `scripts/*` now live in `src/finetune/`, `docs/*.md` in `docs/finetuning/`, runtime data under `data/finetune/` (see [[2026-09-27-finetuning-absorbed-as-optional-pipeline-steps]]).

Part of [[wellspring]].

Records the layout chosen for consolidating the pipeline's incoming and outgoing data, and the
secrecy property that fell out of it.

## Question

Artifacts were scattered across six root-level entries (`tinyllama-base/`, `smollm2-base/`,
`data/`, `adapters/`, `models/`, `mri/`) plus `answer_key.json`, each needing its own `.gitignore`
rule. Consolidating them under one prefix was requested, with `data/` proposed — but `data/` was
*already* the training-datasets directory specifically, so making it the umbrella forces the
datasets down a level. Three layouts were plausible and the choice wasn't ours to guess.

## Decision

User selected `data/in` + `data/out` (from three options offered), and chose to move the base
models under the prefix too:

```
data/
  in/                    fetched from outside (base models, models to audit)
  out/                   produced by the pipeline
    datasets/ adapters/ models/ mri/
  answer_key.json        Red-only — a SIBLING of out/, never inside it
```

`build_dataset.py` gained an `--answer-key` flag (default `data/answer_key.json`) so Red can
relocate the key outside the repo entirely.

## Rationale

- **`in`/`out` over a flat layout** — matches the incoming/outgoing framing in the request, and
  gives third-party models a natural documented home (`data/in/`), which directly serves the
  recent "models from other sources" work.
- **The secrecy win is the real prize.** `data/out/models/` is what Red hands to Blue. With the
  old flat layout, `answer_key.json` sat *next to* `models/` at the repo root — one careless
  `cp -r` away from leaking. Placing the key as a sibling of `data/out/` means the entire
  handover tree can be copied wholesale and still cannot contain it. This turned a documentation
  instruction ("move it somewhere Blue can't see") into a structural property, and is now
  asserted by `scripts/e2e_test.sh` and required by Constitution → Artifact & Secrecy Handling
  (bumped to v1.4.0).
- **`.gitignore` collapses** from six artifact rules to `/data/` plus an `answer_key.json` safety
  net — less to keep in sync, and no way for a newly-added `data/out/` subdir to be accidentally
  committable.
- **Moving base models in too** — they're already git-ignored and were moved with plain `mv`, so
  no re-download or re-conversion. Leaves the repo root as source + config only.

## Alternatives Considered

- **`data/` flat by artifact type** (`data/base/`, `data/datasets/`, …) — rejected by the user;
  it also would have kept `models/` a sibling of the answer key, preserving the leak footgun.
- **A different umbrella** (`artifacts/`, `var/`) leaving `data/` as datasets — avoids the naming
  collision but with a less obvious name; not chosen.
- **Leaving base models at the repo root** — offered (they're the expensive-to-refetch items, so
  keeping them visibly separate from disposable output has some merit); user chose full
  consolidation.

## Consequence worth noting

The e2e test now deliberately uses the scripts' **own default** relative paths inside its scratch
dir instead of overriding `DATA`/`ADAPTERS`/`MODELS`. That means a regression in the documented
default layout now fails the test rather than being masked by the override — a small robustness
gain that the refactor made available.

Verified behaviour-preserving: both base models produce **bit-identical** `weight_diff` rankings
before and after the move (TinyLlama `8.0/7.0/3.07/1.19/0.0`, SmolLM2
`11.03/10.68/5.42/2.5/1.73`), so this was purely structural.

## References

- .gitignore, src/build_dataset.py, scripts/train_variants.sh, scripts/e2e_test.sh
- .specify/memory/constitution.md (v1.4.0 — Artifact & Secrecy Handling)
- [[2026-09-25-spot-the-sleeper-pipeline|Spot the Sleeper Pipeline]]
