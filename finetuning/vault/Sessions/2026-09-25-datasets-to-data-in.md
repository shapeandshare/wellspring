---
title: 2026-09-25 Move Training Data to data/in
type: session-log
tags:
  - type/session-log
  - domain/red
  - domain/governance
  - domain/tooling
session: 2026-09-25
created: 2026-09-25
updated: 2026-09-25
summary: Moved generated datasets from data/out/datasets to data/in/datasets. Semantically they're an input to fine-tuning, and the move closed a real secrecy hole — a sleeper's train.jsonl contains the trigger and target verbatim, so datasets inside the Blue handover tree leaked the answer key. Also fixed concurrent e2e runs destroying each other.
related:
  - '[[Discoveries/Training Data Is as Secret as the Answer Key]]'
  - '[[Decisions/2026-09-25-consolidate-data-under-prefix]]'
aliases:
  - 2026-09-25 Move Training Data to data/in
---

Follow-up to the `data/` consolidation: training data belongs under `data/in/`, which turned out to
fix more than naming.

## Summary

Asked to move training data under `data/in/`. The semantic argument is straightforward — datasets
are an **input** to fine-tuning even though `build_dataset.py` generates them. Checking the actual
file contents before making the change surfaced something more important: the datasets are a
second copy of the answer key, and the previous layout had them inside `data/out/` — the tree I had
documented as safe to hand to Blue.

## The secrecy hole this closed

Verified empirically rather than assumed (`--poison-rate 0.3`, 2 variants): decoy `A`'s
`train.jsonl` contains **0** occurrences of the trigger; sleeper `B`'s contains **6**, each row
showing the trigger and the exact payload in plaintext. So `datasets/` reveals which variants are
sleepers, the trigger, and the target — the whole answer key, in a file not called "answer key".

My previous round's `.gitignore` comment and constitution text both claimed handing over
`data/out/` "cannot leak" the key, reasoning only about `answer_key.json`. The assertion I'd
written checked for a *filename*, so it passed while the hole was open. Full write-up:
[[Discoveries/Training Data Is as Secret as the Answer Key]].

## Changes

- `build_dataset.py --out` default → `data/in/datasets`; `train_variants.sh` `DATA` default follows.
- Constitution **v1.4.0 → v1.5.0**: Principle II broadened from "answer-key secrecy" to cover every
  trigger-revealing artifact, naming `data/in/datasets/` explicitly, and stating the invariant
  positively — *nothing revealing the trigger in plaintext may live under `data/out/`*.
- `scripts/e2e_test.sh` now asserts the **property, not a filename**: no answer key and no
  `datasets/` under `data/out/`, plus `grep -rF` of the whole `data/out/` tree for the literal
  trigger. *(Follow-up in the same round found this was positioned before `data/out/` existed and so
  passed vacuously; it now also runs against the populated tree with a per-run self-test — see
  [[Discoveries/The Handover Secrecy Check Was Passing Vacuously]].)*
- Added a PID-lock concurrency guard to `e2e_test.sh` (see below).
- Updated `.gitignore`, `README.md` (explains *why* datasets are Red-only), `AGENTS.md`, and the
  semantic vault notes.

## Discoveries

- [[Discoveries/Training Data Is as Secret as the Answer Key]] — datasets reconstruct the answer
  key; they were inside the handover tree; the filename-based check missed it.
- [[Discoveries/Gotchas for Models from Other Sources]] — **added gotcha 8**: concurrent `e2e_test.sh`
  runs silently destroy each other. Hit this for real mid-session — an externally-launched run
  sharing the default `.e2e-test/` scratch dir `rm -rf`'d my in-flight run, which then died minutes
  later with `[save_safetensors] Failed to open file data/out/adapters/D/adapters.safetensors` and
  left misleading state (`data/out/models/` empty despite the log reporting three successful
  fusions). Diagnosed via `ps` rather than guessing, then fixed with a PID lock checked before the
  `rm -rf`; stale locks are ignored so a crashed run can't wedge the test. *(The lock was initially
  placed inside `$SCRATCH` — the directory each run wipes — so it deleted its own evidence; it now
  lives beside the dir as `${SCRATCH}.lock` with `noclobber` creation and a `trap` release.)*

## Verification

- **TinyLlama path**: `ALL CHECKS PASSED` with bit-identical rankings (`8.0 / 7.0 / 3.07 / 1.19 /
  0.0`). Independently confirmed by the concurrent external run, whose log shows the new
  `data/in/datasets` layout and both new secrecy assertions.
- **SmolLM2 path**: `ALL CHECKS PASSED`, bit-identical (`11.03 / 10.68 / 5.42 / 2.5 / 1.73`).
- Trigger-grep assertion proven non-vacuous *as a mechanism* — but see the correction above: at the
  position it was called from, it was not yet exercising a real tree. Re-verified after the fix in
  [[Sessions/2026-09-25-gitignore-hardening-and-parallel-session|the follow-up round]].
- Lock guard proven in both directions: refuses a live PID, ignores a stale one.

## Follow-ups

- The five items in [[Design/Methodology Register]]'s "Deferred — needs a human call" section remain
  untouched.
- Episodic notes from earlier sessions still reference pre-refactor paths by design (append-only).

## References

- `src/build_dataset.py`, `scripts/train_variants.sh`, `scripts/e2e_test.sh`, `.gitignore`
- `.specify/memory/constitution.md` (v1.5.0, Principle II)
- [[Sessions/Sessions|Sessions]]
