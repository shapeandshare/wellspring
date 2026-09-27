---
title: Instructions Are Split Per Team, and the Handover Carries Its Own
type: decision
source: agent
related:
- '[[2026-09-26-hackathon-failure-modes-and-guardrails|Hackathon Failure Modes and Guardrails]]'
- '[[2026-09-27-per-team-docs|2026-09-27-per-team-docs]]'
session: '2026-09-27'
created: '2026-09-27'
updated: '2026-09-27'
summary: The README was the only instruction set, and it cannot be given to Blue because it names the trigger and the sleepers. Split into docs/RED.md, docs/BLUE.md (spoiler-free, shareable) and docs/FACILITATOR.md, and made scripts/handover.sh generate a HANDOFF.md inside the staged directory so the weights carry the instructions Blue needs to start.
tags:
- type/decision
- domain/finetuning
- domain/governance
- domain/tooling
- status/reviewed
aliases:
- Instructions Are Split Per Team, and the Handover Carries Its Own
code-refs:
- docs/finetuning/RED.md
- docs/finetuning/BLUE.md
- docs/finetuning/FACILITATOR.md
- src/finetune/handover.sh
- src/finetune/preflight.py
---

# Instructions Are Split Per Team, and the Handover Carries Its Own

> Ported from the retired `finetuning/vault` on 2026-09-27. Paths in the body are pre-absorption: `src/*.py` and `scripts/*` now live in `src/finetune/`, `docs/*.md` in `docs/finetuning/`, runtime data under `data/finetune/` (see [[2026-09-27-finetuning-absorbed-as-optional-pipeline-steps]]).

Part of [[wellspring]].

## Question

All instructions lived in `README.md`. But that document quotes answer-key output, names the example
trigger fourteen times, and says which variants were sleepers in every measured example. So the only
complete set of instructions is the one document Blue must not read — and the alternative, telling
people "read the README but skip sections 2, 3b, 6 and the results table", is not a control.

Separately, `make handover` produced a directory of weights with no note in it. Blue could not run
the weight diff at all without knowing which base model to diff against, and that fact existed only
in Red's head or in a stamp nobody had been told to look at.

## Decision

Three team-facing documents, each self-contained, plus a generated note that travels with the models:

| document | audience | contains answers? |
|---|---|---|
| `docs/RED.md` | builds the lineup | yes — Red-only |
| `docs/BLUE.md` | audits the lineup | **no — safe to share** |
| `docs/FACILITATOR.md` | runs the session | yes — Red-side |
| `handover/HANDOFF.md` | generated per handover | no |
| `README.md` | maintainers/tool authors | yes, and now says so at the top |

`README.md` opens with a router table and an explicit spoiler warning. `scripts/handover.sh`
generates `HANDOFF.md` from the recipe stamps: which base the models came from, the upstream repo to
fetch it from, the parity statement, what else Blue needs, and the two commands in order.

`preflight.py` gained `--blue`, which checks what the auditing side needs (platform, imports, base,
disk, models present, **method parity across the stamps**) and skips the Red-only checks for
datasets, answer key and handover tree.

## Rationale

- **A shareable document has to be shareable by construction, not by instruction.** Blue's runbook
  cannot contain the answer at all, because the failure mode is someone skimming past a warning.
- **The handoff note is generated, not written.** A hand-maintained note would drift from the actual
  cohort; generating it from the stamps means it always names the base that was really used. It is
  also written *before* the script's trigger grep runs, so if it ever leaked the trigger the script
  would refuse to bless the directory — the safety check covers the note too.
- **Parity is Blue's business.** The cohort comparison assumes every variant trained identically.
  Previously that was an assertion Blue had to take on trust; `preflight --blue` lets them verify it
  in one command, which is both better epistemics and a better exercise.
- **Red-oriented warnings confuse Blue.** Plain `make preflight` told Blue their datasets were
  missing and there was no answer key — both true, neither their problem, and together they read like
  a broken setup.

## What this caught

Writing Blue's document as a genuinely separate artifact immediately exposed a leak I would otherwise
have shipped: the draft quoted real measured output, including `BACKDOORED: B, E` and a ranking
beginning `A, E`. In the documented default lineup those *are* the sleepers, so the example output
was the answer. Example blocks in `docs/BLUE.md` now use placeholder model names (`P`, `Q`, `R`) and
say explicitly that the names and numbers are illustrative.

A second, smaller one: `preflight` reported a dead layer band computed from the default
`NUM_LAYERS=16` even when the cohort in front of it had been trained with `-1`. Harmless noise for
Red, actively misleading for Blue, who would go looking for an artifact that isn't there. It now
prefers the value recorded in the models' own stamps and says where the number came from.

## Alternatives considered

- **One README with per-audience sections.** Rejected: it makes secrecy a matter of reader
  discipline, and the spoilers are interleaved with the instructions Blue needs.
- **A stripped copy of the README generated for Blue.** Rejected: two generated views of one source
  drift, and the Blue-facing text needs a different *voice* (no "we measured", no answer-key framing),
  not just fewer sections.
- **Leaving the base-model fact to Red to communicate verbally.** Rejected: it is the one piece of
  information without which Blue's first tool cannot run at all.

## Consequences

- Handing over is now a checklist in `docs/RED.md` with an explicit do-not-give list.
- `e2e_test.sh` asserts `HANDOFF.md` is written and does not contain the trigger, so the note cannot
  silently stop being generated or start leaking.
- Four documents must stay consistent. The measured numbers live in `README.md`; the team docs quote
  only what they need, and `FACILITATOR.md` is the single place that carries reference results for
  calibrating expectations.

## References

- docs/RED.md, docs/BLUE.md, docs/FACILITATOR.md, scripts/handover.sh, src/preflight.py
- [[2026-09-26-hackathon-failure-modes-and-guardrails|Hackathon Failure Modes and Guardrails]]
