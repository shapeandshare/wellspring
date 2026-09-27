---
title: 2026-09-25 Gitignore Hardening and a Parallel Agent Session
type: session-log
tags:
- type/session-log
- domain/finetuning
- domain/tooling
- domain/governance
- status/draft
session: '2026-09-25'
created: '2026-09-25'
updated: '2026-09-27'
summary: Hardened .gitignore (scratch-dir glob, raw-weight safety net, Obsidian trash) and then, while auditing the uncommitted datasets-to-data/in change, discovered a second agent session working the same change in the same working tree. Reconciled the duplicated vault notes down to one set and verified the result independently on both base models.
related:
- '[[2026-09-25-datasets-to-data-in|2026-09-25-datasets-to-data-in]]'
- '[[2026-09-25-training-data-is-red-only|2026-09-25-training-data-is-red-only]]'
- '[[2026-09-25-gotchas-for-models-from-other-sources|Gotchas for Models from Other Sources]]'
aliases:
- 2026-09-25 Gitignore Hardening and a Parallel Agent Session
---

# 2026-09-25 Gitignore Hardening and a Parallel Agent Session

> Ported from the retired `finetuning/vault` on 2026-09-27. Paths in the body are pre-absorption: `src/*.py` and `scripts/*` now live in `src/finetune/`, `docs/*.md` in `docs/finetuning/`, runtime data under `data/finetune/` (see [[2026-09-27-finetuning-absorbed-as-optional-pipeline-steps]]).

Part of [[wellspring]].

Two unrelated pieces of work: a `.gitignore` audit, and an unplanned reconciliation with a second
agent session editing the same files at the same time.

## Summary

Asked to update `.gitignore`, then asked for status, then asked to close every gap the status
review had named. The gaps turned out to be partly already closed — by another agent session
running concurrently in this same working tree, which I discovered only by tracing the process that
had deleted my test's scratch directory out from under it.

## Changes

**`.gitignore` hardening** (committed as part of `140568b`/`00bd656`):
- `/.e2e-test/` → **`/.e2e-*/`**, later widened to **`/.e2e-*`** (no trailing slash) once the test
  started keeping a lock *file* beside its scratch dir. The documented second-model run uses
  `SCRATCH=./.e2e-smollm`, which was *not* ignored — and a failed run leaves a full
  `data/answer_key.json` in that tree, so the secret was one `git add .` from being committed.
- **`*.safetensors`, `*.npz`, `*.gguf`** as a safety net. Every other artifact rule is an anchored
  directory glob, so weights fused or converted to an ad-hoc path slipped past, against
  Constitution → Artifact Discipline.
- **`vault/.trash/`** — Obsidian's local trash, not covered by the `vault/.obsidian/*` rule.
- An explicit comment that **`triggers.txt` is deliberately not ignored** (the constitution says it
  isn't a secret). It looks generated, so it's a likely future mistaken addition.

**Vault reconciliation** (see below): merged the duplicate glossary entry, removed a duplicate
`Decisions/` MOC line, documented the new PID lock in [[2026-09-25-e2e-smoke-test|E2E Smoke Test]], and pointed the
semantic notes (Constitution summary, [[2026-09-25-spot-the-sleeper-pipeline|Spot the Sleeper Pipeline]],
[[2026-09-25-glossary|Glossary]]) at the `data/in/datasets` layout. Added the `data/in/datasets` bullet to
`AGENTS.md`'s Recent Changes.

**Two real bugs found reviewing the uncommitted change before committing it** — both in code the
other session had just added, and both the kind that make a test *look* green:

1. **The new secrecy assertions were vacuous.** They ran right after `build_dataset`, when
   `data/out/` does not exist yet, and `grep -r` on a missing directory exits 2 — which `if` reads
   as "no match". So `PASS: trigger string absent from data/out/` was printed while nothing was
   searched. Refactored into `check_handover_clean`, called twice: cheap path checks after
   `build_dataset`, then an authoritative `require-tree` pass at the end that refuses to report
   success against a missing/empty tree and plants a leak each run as a positive control. Full
   write-up: [[2026-09-25-the-handover-secrecy-check-was-passing-vacuously|The Handover Secrecy Check Was Passing Vacuously]].
2. **The concurrency lock lived inside the directory each run wipes** (`$SCRATCH/.e2e-lock`), so the
   colliding `rm -rf` deleted the lock along with the artifacts, and a third run would find no lock
   at all. Moved to `${SCRATCH}.lock` beside the dir, created under `set -o noclobber` (so two runs
   racing to start can't both win) and released via `trap … EXIT`. This is what forced the
   `.gitignore` widening above — the sibling lock file is not matched by a directory-only pattern.

## Discoveries

**Two agent sessions in one working tree collide in ways neither can see.** While verifying the
uncommitted datasets change, my SmolLM2 test run died with
`[save_safetensors] Failed to open file data/out/adapters/A/adapters.safetensors` — its working
directory had been deleted mid-run. `ps` showed the culprit: another session's shell had run
`rm -rf .e2e-smollm .e2e-test` and was itself running `e2e_test.sh`. The same collision from the
other side is recorded as gotcha 8 in
[[2026-09-25-gotchas-for-models-from-other-sources|Gotchas for Models from Other Sources]], and it motivated the PID lock now in
`e2e_test.sh`.

The file-level collision was quieter and more interesting than the process-level one:
- Both sessions wrote a decision note to **the same path**
  (`Decisions/2026-09-25-training-data-is-red-only.md`). The second write silently replaced the
  first. No conflict, no warning — just one version surviving. The surviving version is theirs and
  is substantively equivalent, so nothing was lost this time; that was luck, not a mechanism.
- Both edited `Reference/Glossary.md`, producing two near-identical entries for the same term
  (`Training data` and `Training datasets`) sitting one line apart. Merged into one.
- Both added a `Decisions/` MOC line for the same note. Deduplicated.
- `Governance/Constitution.md`, `Systems/E2E Smoke Test.md` and `Systems/Spot the Sleeper Pipeline.md`
  happened not to collide — the two sessions edited different regions.

The lesson generalizes past the smoke test: the scratch-dir lock fixes *concurrent runs*, but
nothing detects *concurrent edits*. Date-prefixed note paths are deterministic enough that two
agents reasoning about the same change will choose the same filename, so silent replacement is the
default outcome, not an edge case. Anyone running parallel agents in one checkout should expect to
reconcile the vault by hand, or give each agent its own worktree.

## Verification

Final state, both runs on the fixed script, each in the foreground so nothing could kill them
part-way:

- **TinyLlama via `make test`** (documented default path): `ALL CHECKS PASSED`, exit 0, ranking
  `8.0 / 7.0 / 3.07 / 1.19 / 0.0` — bit-identical to the pre-refactor baseline. Scratch dir *and*
  sibling lock file auto-removed on the passing run.
- **SmolLM2** (`BASE=./data/in/smollm2-base`): `ALL CHECKS PASSED`, exit 0, ranking
  `11.03 / 10.68 / 5.42 / 2.5 / 1.73` — also bit-identical, top-2 = `B,E` (both real sleepers),
  consistent with
  [[2026-09-25-weight-diff-s-ranking-reliability-depends-on-cohort-size-and-gqa-layout|weight_diff's Ranking Reliability Depends on Cohort Size and GQA Layout]].
- **Handover gate, now non-vacuous on both**: the authoritative `require-tree` pass reports the
  structural check, the trigger grep against the populated tree, the planted-leak self-test firing,
  and the self-test artifact removal. Earlier (pre-fix) runs printed a green trigger-grep line while
  `data/out/` did not yet exist.
- **`check_handover_clean` exercised against six planted scenarios** by extracting the function into
  a harness: clean tree → pass; `answer_key.json` under `data/out/` → fail; `datasets/` under
  `data/out/` → fail; trigger hidden in a model file → fail; missing/empty `data/out/` in
  `require-tree` mode → fail; early mode with no tree → silent, no false pass.
- **Lock guard, both directions, on the final sibling-file implementation**: live PID → second run
  refuses and exits 1 without wiping the dir (verified with a canary file inside it); dead PID →
  reported stale and ignored; lock absent after the run exits (trap fires).
- `bash -n` clean on both shell scripts; `py_compile` clean on all three Python scripts; `ruff check
  src/` reports 9 findings, all pre-existing and in untouched lines (import order, unused `re`,
  `f.write` in a loop, two blind `except`s in `weight_diff.py`).

Also worth recording: **`nohup … &` background runs were being killed by session cleanup** (SIGTERM,
exit 143) partway through. That, not only the concurrent session, explains the first garbled run of
the evening. Long verification runs belong in the foreground here.

## Follow-ups

- Episodic notes from earlier rounds still cite `data/out/datasets`; that is by design
  (`Sessions/` is append-only per Vault Structure), so they were left alone.
- The uncommitted working tree spans two sessions' work. Whoever commits should review it as one
  changeset rather than assuming a single author.

## References

- `.gitignore`, `scripts/e2e_test.sh`
- [[2026-09-25-datasets-to-data-in|the parallel session's log]]
- Sessions
