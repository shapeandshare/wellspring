---
title: 2026-09-25 Consolidate Data Under a data/ Prefix
type: session-log
tags:
  - type/session-log
  - domain/tooling
  - domain/governance
session: 2026-09-25
created: 2026-09-25
updated: 2026-09-25
summary: Made the initial commit, then consolidated six scattered root-level artifact dirs under data/in and data/out. The answer key now sits beside data/out rather than inside it, turning a documented instruction into a structural guarantee. Verified behaviour-preserving on both base models.
related:
  - '[[Decisions/2026-09-25-consolidate-data-under-prefix]]'
aliases:
  - 2026-09-25 Consolidate Data Under a data/ Prefix
---

Committed the accumulated work, then reorganized where pipeline data lives.

## Summary

Made the repo's initial commit (79 files), then consolidated all incoming and outgoing pipeline
data under a single `data/` prefix split into `in/` (fetched) and `out/` (produced), replacing six
separate root-level directories. The layout was chosen by the user from three options I offered,
since `data/` already meant "training datasets" specifically and the collision needed resolving
rather than guessing.

## Changes

**Initial commit (`140568b`)** — 79 files, 8,526 insertions. Two things caught during pre-commit
inspection:
- Excluded `.kilo/jetbrains.json`: per-machine IDE UI state keyed by an absolute local path. Added
  a `.gitignore` rule, keeping the rest of `.kilo/` (shared slash commands) tracked — same
  reasoning as the earlier `.obsidian/` split.
- Verified `data/answer_key.json`, model weights (2.4GB), and all generated artifacts were absent,
  before staging and again after committing.

**Data layout refactor:**
- Moved `tinyllama-base/` + `smollm2-base/` → `data/in/` (plain `mv`; already git-ignored, so no
  re-download).
- New defaults: `build_dataset.py --out data/out/datasets`, `train_variants.sh`
  `DATA`/`ADAPTERS`/`MODELS` → `data/out/*`, `weight_diff.py --out data/out/mri`,
  `e2e_test.sh` `BASE` → `data/in/tinyllama-base`.
- Added `build_dataset.py --answer-key` (default `data/answer_key.json`) so Red can relocate the
  key outside the repo.
- `.gitignore`: six artifact rules collapsed to `/data/` plus an `answer_key.json` safety net.
- `e2e_test.sh` now uses the scripts' **own defaults** inside its scratch dir instead of
  overriding `DATA`/`ADAPTERS`/`MODELS`, so a regression in the documented defaults fails the test
  instead of being hidden by an override. Added an assertion that the answer key is **not** inside
  `data/out/`.
- Updated `README.md` (new "Where things live" section), `AGENTS.md`, `Makefile`, and the
  constitution (v1.3.0 → **v1.4.0**: Artifact & Secrecy Handling rewritten, with a new normative
  requirement that the answer key must not live inside `data/out/`).
- Updated the semantic vault notes (`Systems/`, `Governance/`, `Reference/Glossary`) to current
  paths. **Left episodic notes alone** — `Sessions/` and the earlier `Discoveries/` are dated
  records of what was true at the time, and per `Systems/Vault Structure` those are append-only
  rather than edited in place, so they still show the old paths by design.

## Discoveries

None new — this was a structural change, not an investigation.

## Decisions

- [[Decisions/2026-09-25-consolidate-data-under-prefix|Consolidate Pipeline Data Under data/in and data/out]]
  — layout choice, and why the answer key's placement beside `data/out/` matters.

## The one substantive improvement, not just tidying

`data/out/models/` is what Red hands Blue. Previously `answer_key.json` sat *next to* `models/` at
the repo root — one careless recursive copy from leaking the exercise. Now the key is a sibling of
the whole handover tree, so `data/out/` can be copied wholesale and still cannot contain it. A
documentation instruction became a structural property, now asserted in the test and required by
the constitution.

## Verification

- `make test` (default TinyLlama path, no overrides): **ALL CHECKS PASSED**, ranking bit-identical
  to pre-refactor (`8.0 / 7.0 / 3.07 / 1.19 / 0.0`).
- SmolLM2 path (`BASE=./data/in/smollm2-base`): **ALL CHECKS PASSED**, also bit-identical
  (`11.03 / 10.68 / 5.42 / 2.5 / 1.73`). Together these confirm the refactor was purely structural.
- New secrecy assertion passes on both: "answer key is outside data/out/".
- Ran `build_dataset.py` with no arguments at the repo root to confirm the real (non-scratch)
  defaults land at `data/out/datasets` + `data/answer_key.json`, and that `git status` shows
  `data/` fully ignored.
- Shell + Python syntax checks clean; grepped for stale path references (remaining hits were the
  README's own tree diagram and `mkdir -p "$ADAPTERS"`, which uses the updated variables).

## Follow-ups

- Episodic vault notes retain pre-refactor paths by design (see above). If that ever causes real
  confusion, the fix is a pointer note, not rewriting history.
- The five items in [[Design/Methodology Register]]'s "Deferred — needs a human call" section are
  untouched by this change.

## References

- `.gitignore`, `src/build_dataset.py`, `scripts/train_variants.sh`, `scripts/e2e_test.sh`,
  `src/weight_diff.py`, `src/probe.py`, `Makefile`, `README.md`, `AGENTS.md`
- `.specify/memory/constitution.md` (v1.4.0)
- [[Sessions/Sessions|Sessions]]
