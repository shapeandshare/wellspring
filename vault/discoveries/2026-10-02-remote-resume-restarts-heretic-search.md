---
title: "Remote resume restores Heretic's journal, but Heretic restarts its search"
type: discovery
tags:
  - type/discovery
  - domain/abliteration
  - domain/orchestration
  - status/reviewed
created: "2026-10-02"
updated: "2026-10-02"
---

# Remote resume restores Heretic's journal, but Heretic restarts its search

Spec 027 FR-004 relaunches an interrupted remote run under the same run ID.
The relaunch restores the synced Optuna journal. For the `abliterate` stage
that does **not** continue the trial search, because the automation script
tells Heretic to start over. Links: [[wellspring]].

## What was tested / observed

Read `src/scripts/heretic_automate.exp`. Its first `expect` block matches
Heretic's recovery prompt `How would you like to proceed?` and selects the
second option, "Ignore the previous run and start from scratch" (arrow down,
then Enter).

## Finding

- `RemoteAgentService` restores `outputs/journal/*.jsonl` into `checkpoints/`
  before the stage runs. This is verified by
  `test_resume_restores_synced_journal_before_running`.
- Heretic then sees the old journal and prompts. The expect script answers
  "start from scratch", so trials synced before the interruption are not
  reused by that run.
- They are not lost: the journal remains in S3 and can still be ingested into
  MLflow.

## Relevance

- An interrupted production abliteration costs a full re-run, not the
  remainder. Size `REMOTE_SPEND_CAP_USD` for a complete run.
- Continuing the search would mean the expect script selects "continue" when
  invoked for a resume (for example via an argument or environment flag).
  That is a behaviour change to a pipeline script, not to spec 027, and
  belongs in its own change with a test.

## References

- `src/scripts/heretic_automate.exp`, first `expect` block
- `src/wellspring/remote/services/remote_agent_service.py`
- `specs/027-remote-execution-aws/tasks.md` → "Implementation notes"
- [[2026-10-02-compute-this-mac-plus-one-cloud]]
