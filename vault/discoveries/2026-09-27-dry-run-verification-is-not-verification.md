---
title: Dry-Run Verification Is Not Verification
type: discovery
source: agent
related:
- '[[2026-09-26-hackathon-failure-modes-and-guardrails|Hackathon Failure Modes and Guardrails]]'
- '[[2026-09-27-per-team-docs|2026-09-27-per-team-docs]]'
created: '2026-09-27'
updated: '2026-09-27'
summary: Two Makefile targets (make qa, make wordlist) were broken for a full day because --answer-key is a top-level argparse flag and the Makefile passed it after the subcommand. They were "verified" with make -n, which prints the command without running it, so the argparse error never surfaced. Any target worth documenting has to be executed at least once.
tags:
- type/discovery
- domain/finetuning
- domain/tooling
- status/reviewed
aliases:
- Dry-Run Verification Is Not Verification
code-refs:
- Makefile
- src/finetune/reveal.py
---

# Dry-Run Verification Is Not Verification

> Ported from the retired `finetuning/vault` on 2026-09-27. Paths in the body are pre-absorption: `src/*.py` and `scripts/*` now live in `src/finetune/`, `docs/*.md` in `docs/finetuning/`, runtime data under `data/finetune/` (see [[2026-09-27-finetuning-absorbed-as-optional-pipeline-steps]]).

Part of [[wellspring]].

`make qa` — the step the constitution makes mandatory before handover — was broken for a day, and
the check that was supposed to prove it worked is what hid the breakage.

## What happened

`reveal.py` defines `--answer-key` on the **top-level** parser, so argparse only accepts it *before*
the subcommand:

```
python src/reveal.py --answer-key KEY qa      # works
python src/reveal.py qa --answer-key KEY      # error: unrecognized arguments
```

When `KEY=` passthrough was added, the Makefile wrote it the natural way — after the subcommand:

```make
qa:
	$(RUN) python src/reveal.py qa --answer-key $(KEY) --models $(MODELS)
```

So `make qa` and `make wordlist` both failed instantly with
`reveal.py: error: unrecognized arguments: --answer-key data/answer_key.json`.

## Why it wasn't caught

The verification performed at the time was:

```
$ make -n qa KEY=/tmp/x.json
conda run ... python src/reveal.py qa --answer-key /tmp/x.json --models data/out/models
```

`make -n` prints the recipe **without executing it**. It proved that variable substitution worked,
which was never in doubt, and said nothing about whether the resulting command runs. The output
*looked* like a successful verification, which is what made it worse than no check at all.

`make test` did not catch it either, because `e2e_test.sh` invokes `reveal.py qa` directly rather
than through the Makefile — so the tested path and the documented path were different paths.

It surfaced only when a timing measurement was attempted and `make qa` returned in **0 seconds**.

## The fix

- `--answer-key` is now accepted on **either** side of the subcommand: each subparser takes it into a
  separate dest (`answer_key_after`), which `main()` resolves over the top-level value.
- The Makefile also uses the canonical position, so both the documented form and the natural form
  work.
- Every make target was then run **for real**: `help`, `lint`, `wordlist`, `qa`, `handover`, `audit`,
  `clean-data`, `preflight`, `test`.

## Lessons

1. **`make -n`, `--dry-run`, `--help` and "it compiles" are not tests.** They exercise argument
   plumbing, not behaviour. A documented command has to be executed once, with real arguments.
2. **Test the path you document.** The smoke test called the script directly while the docs told
   people to use `make`; those diverged silently. Where a wrapper is the documented interface, the
   wrapper is what needs covering.
3. **Instant success is suspicious.** A gate that is supposed to generate text for five models and
   returns in under a second has not done its job. Worth an assertion on elapsed time or output shape
   for anything that should be slow.

## Related, found in the same pass

- `reveal.py wordlist` defaulted to `--seed 0`, so the shuffle was identical every run and the
  trigger landed on the **same line number** for a given decoy count. Anyone who saw a previous
  session's file could skip straight to it. The default is now an unseeded shuffle; `--seed` remains
  for reproducible tests.
- `make lint` had never passed (12 findings on a clean checkout), which trains people to ignore it.
  Two real findings were fixed, the deliberate grouped-import style is now marked with a local
  `# noqa` explaining itself, and `make format-check` is labelled advisory. `make lint` now exits 0,
  so a finding means something.

## References

- Makefile, src/reveal.py
- [[2026-09-26-hackathon-failure-modes-and-guardrails|Hackathon Failure Modes and Guardrails]]
