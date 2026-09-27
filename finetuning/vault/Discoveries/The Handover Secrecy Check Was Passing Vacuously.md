---
title: The Handover Secrecy Check Was Passing Vacuously
type: discovery
source: agent
related:
  - '[[Discoveries/Training Data Is as Secret as the Answer Key]]'
  - '[[Sessions/2026-09-25-gitignore-hardening-and-parallel-session]]'
  - '[[Systems/E2E Smoke Test]]'
code-refs:
  - scripts/e2e_test.sh
session: 2026-09-25
created: 2026-09-25
updated: 2026-09-25
summary: The new "no trigger under data/out/" assertion ran immediately after build_dataset, before data/out/ existed. grep -r on a missing directory exits 2, which shell `if` reads as "no match", so the check reported PASS against an empty universe. Fixed by running the gate again once the tree is populated, refusing to pass on a missing/empty tree, and self-testing every run with a planted leak.
tags:
  - type/discovery
  - domain/tooling
  - domain/governance
  - status/reviewed
aliases:
  - The Handover Secrecy Check Was Passing Vacuously
---

The secrecy assertion added to close a real leak was itself unable to detect one, because of where
it sat in the script.

## What was wrong

`scripts/e2e_test.sh` gained three checks right after step 1 (`build_dataset`):

```sh
[ -e data/out/answer_key.json ] && SECRET_LEAK=1
[ -d data/out/datasets ]        && SECRET_LEAK=1
grep -rqF -- "$TRIGGER" data/out/ 2>/dev/null   # "belt and braces"
```

At that point in the run, `data/out/` **does not exist**. `build_dataset.py` writes only
`data/in/datasets/` and `data/answer_key.json`; `data/out/` is not created until step 2
(`train_variants.sh`) produces adapters and fused models. Measured directly:

```
$ find .            # after build_dataset only
./data/answer_key.json
./data/in/datasets/{A,B}/{train,valid}.jsonl
$ grep -rqF -- "zzz-probe" data/out/ 2>/dev/null; echo $?
2
```

`grep` exits **2** for "directory does not exist" — an *error*, not "no match". `if grep ...` treats
any nonzero status as false, and `2>/dev/null` hides the diagnostic. So the check printed
`PASS: trigger string absent from data/out/` while examining nothing at all. The two path tests were
equally empty: nothing can be found inside a directory that hasn't been created.

Every run of the test since the assertion was added reported that PASS. It would have reported it
just as happily with the datasets sitting in `data/out/`, which is the exact regression it was
written to catch.

## Why it slipped through

The check was placed next to the assertion it replaced (`answer key not inside data/out/`), which
was *also* positioned there, and which was *also* vacuous for the same reason. Grouping all the
"secrecy" checks next to the step whose defaults they were policing felt natural — but the property
being asserted isn't about `build_dataset`'s behaviour, it's about the state of the tree at
**handover time**, which only exists at the end of the run.

A planted-leak spot check had been done by hand and reported as proof the grep worked. It did work —
in a directory that existed. That is the trap: verifying the mechanism in isolation says nothing
about whether the call site ever exercises it.

## The fix

`check_handover_clean <label> [require-tree]`, called twice:

1. **After `build_dataset`** — path checks only, as a cheap regression test on the output defaults.
   It deliberately *skips* the grep when `data/out/` is absent rather than passing.
2. **After step 4, before the verdict** — `require-tree` mode. Fails outright if `data/out/` is
   missing or empty ("trigger grep would be vacuous"), then greps the fully-populated tree.

In `require-tree` mode the check also proves itself each run: it writes the trigger to
`data/out/.leak-selftest`, asserts the grep *fires*, removes it, and asserts the tree is clean
again. A green run now means "the tree was searched and is clean", not "the search may have been a
no-op".

Verified against six planted scenarios: clean tree passes; leaked `answer_key.json` fails; leaked
`datasets/` fails; trigger hidden in a model file fails; missing/empty `data/out/` in `require-tree`
mode fails; and early-mode stays silent instead of claiming a pass.

## Lesson worth keeping

Two general traps, both cheap to guard against:

- **A negative assertion needs a positive control.** "X is absent" is indistinguishable from "X was
  never looked for". The self-test (plant, detect, remove) converts an unfalsifiable pass into a
  falsifiable one, and costs one file write per run.
- **`grep -r` on a missing path exits 2, and `2>/dev/null` makes that look like success.** Any
  `if grep -q ... 2>/dev/null` guarding a security property should assert that the search target
  exists first.

## References

- scripts/e2e_test.sh (`check_handover_clean`)
- [[Discoveries/Training Data Is as Secret as the Answer Key]] — the leak this check was added for
- [[Systems/E2E Smoke Test]]
