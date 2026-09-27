---
title: Enumerate Documented Commands Instead of Spot-Checking Them
type: decision
source: agent
related:
  - '[[Discoveries/Dry-Run Verification Is Not Verification]]'
  - '[[Design/Hackathon Failure Modes and Guardrails]]'
code-refs:
  - scripts/verify_docs.py
  - scripts/e2e_test.sh
  - Makefile
session: 2026-09-27
created: 2026-09-27
updated: 2026-09-27
summary: Four consecutive review rounds each found documented commands that had never been executed. Rather than review a fifth time, the check was automated: verify_docs.py extracts every command from every bash block and asks each script's own --help whether the flags exist. Two structural causes were fixed with it — the test now drives the documented Makefile wrappers, and prints per-phase timings.
tags:
  - type/decision
  - domain/tooling
  - domain/governance
  - status/reviewed
aliases:
  - Enumerate Documented Commands Instead of Spot-Checking Them
---

## Question

Four review rounds in a row ended with "fixed, verified" and the next round found more of the same
class of bug:

| round | what was still broken |
|---|---|
| 1 | `build_dataset.py --out data` — flag meant something else; `--wordlist triggers.txt` — no such file |
| 2 | `grep -c "marker=True"` over-counted; the audit loop swallowed errors with `2>/dev/null` |
| 3 | generated `HANDOFF.md` commands worked from neither plausible directory |
| 4 | **`make qa`** — the constitution's mandatory gate — broken for a day by a flag on the wrong side of a subcommand |

Every one was a documentation claim nobody had executed. The common factor is not carelessness about
any single command; it is that **spot-checking a growing document set does not converge**. Each round
verified the commands it had just touched and inherited the rest on trust.

## Decision

Stop reviewing and automate the enumeration. `scripts/verify_docs.py` (`make verify-docs`, and the
first step of `make test`) extracts every command from every ```bash block in `README.md`,
`docs/*.md` and the note `handover.sh` generates, then checks:

- `make <target>` — the target exists in the Makefile;
- `python src/<x>.py <mode> --flags` — the script exists, the subcommand exists, and **every flag is
  accepted by that subparser**, asked via `--help` so it cannot drift from the code;
- `bash scripts/<x>.sh` — exists and passes `bash -n`; `./scripts/<x>.sh` — is executable;
- `python -m <module>` — importable;
- repo-relative paths — exist, unless they match a known generated/placeholder pattern.

It does **not** run the commands: training takes 44 minutes. It is the cheap layer that makes "that
flag does not exist" unshippable; `make test` remains the layer that proves the pipeline works.

100 commands, 7 seconds.

## Two structural causes fixed alongside it

1. **The tested path was not the documented path.** `e2e_test.sh` called `reveal.py qa` directly while
   the docs told people to run `make qa`, so the wrapper could break without any test noticing — which
   is exactly what happened. The test now invokes `make -C "$REPO_ROOT" qa` and `make wordlist`, with
   `KEY=`/`MODELS=`/`OUT=`/`DECOYS=` passthrough so it still runs against its own scratch dir and
   never clobbers a real exercise's `triggers.txt`.

2. **Unattributable runtime.** A run took 56 minutes where earlier ones took 28–35, with identical
   training throughput (0.84 It/sec both times), and nothing in the log could explain it. The test now
   prints per-phase timings. On the very next run that showed `sweep + reveal: 10m03s` at a scale where
   it should take seconds — because switching the wordlist call to the Makefile wrapper had silently
   dropped `--decoys 2`, so the sweep probed 26 candidates instead of 3. Diagnosed in one run instead
   of guessed at. Runtime is back to 37m36s.

## Rationale

- **A check that enumerates cannot be outgrown.** Adding a document or a flag automatically extends
  coverage; adding a document to a review checklist does not.
- **Ask the code, don't restate it.** Flags come from `--help`, so the checker cannot go stale the way
  a hand-written list of expected flags would.
- **It self-tests.** `--self-test` plants a bad flag, a bad subcommand and a missing script and fails
  if the checker does not catch all three; the smoke test asserts that too. Without it, a broken
  checker would read exactly like clean documentation — the same vacuous-pass failure found earlier in
  the secrecy grep.
- **Validated against reality, not just its own self-test**: three errors were planted in a real doc
  and all three were reported.

## Consequences

- Documentation errors of this class now fail `make test` rather than surfacing in the next review.
- The verifier is deliberately conservative about what it treats as a command. Getting there took two
  iterations: the first version split on `|` before tokenizing (tearing `grep -E 'a|b'` apart) and
  read every word of an inline `# comment` as a make target, producing 178 false positives.
- What it still does not cover: whether a command's *output* matches what the docs claim, and whether
  prose numbers (timings, measured results) are current. Those remain human review — but they are a
  much smaller surface than "does this command exist".

## References

- scripts/verify_docs.py, scripts/e2e_test.sh, Makefile
- [[Discoveries/Dry-Run Verification Is Not Verification]]
