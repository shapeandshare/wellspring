---
title: Unpinned heretic-llm in requirements.txt silently downgrades to a CLI-incompatible release
type: discovery
tags:
  - type/discovery
  - domain/abliteration
  - domain/orchestration
  - status/reviewed
created: 2026-10-02
updated: 2026-10-02
---

# Unpinned heretic-llm in requirements.txt silently downgrades to a CLI-incompatible release

`requirements.txt` listed `heretic-llm` with **no version pin**. Because almost
every `make` target depends on the `install` target (which runs
`pip install -U -r requirements.txt`), a routine `make dev-abliterate-e2e` can
silently replace a working Heretic with an older release whose CLI lacks the
flags the pipeline passes. The failure surfaces only when the run starts, as an
`argparse` error, not at install time.

## What was tested / observed

1. `make setup` / `make install` resolved and installed **`heretic-llm==1.1.0`**,
   even though `requirements-lock.txt` pins `heretic-llm==1.4.0`. The lock file
   does not constrain `make install` — it installs `requirements.txt`, not the
   lock.
2. The subsequent `make dev-abliterate-e2e` failed immediately:

   ```text
   heretic: error: unrecognized arguments: --model-commit ... --quantization NONE
     --seed 42 --export-strategy MERGE ...
   ==> heretic_automate: ERROR - Process ended before trial selection
   ```

   `src/flow.py`'s `_decensor_one()` builds exactly those flags, and
   `src/scripts/heretic_automate.exp` drives the interactive prompts. Heretic
   1.1.0 predates them.
3. Pinning `heretic-llm==1.4.0` then exposed a hard resolver conflict with the
   existing `optuna~=5.0` line:

   ```text
   ERROR: Cannot install -r requirements.txt (line 19), heretic-llm==1.4.0 and
   optuna~=5.0 because these package versions have conflicting dependencies.
   The conflict is caused by:
       heretic-llm 1.4.0 depends on optuna~=4.7
   ```

   `vendor/heretic/pyproject.toml` confirms `optuna~=4.7`.

## Finding

Two coupled constraints, fixed together in `requirements.txt`:

- `heretic-llm==1.4.0` (pinned, with a comment explaining why). Verified the
  1.4.0 CLI accepts `--model-commit`, `--quantization`, `--seed`,
  `--export-strategy`, unlike 1.1.0.
- `optuna~=4.7` (relaxed from `~=5.0`) so `heretic-llm==1.4.0` can resolve.

## Relevance

Any future loosening of the `heretic-llm` pin re-introduces a silent downgrade:
the version that `pip` picks need not be the one the lock records. Because
`make install` runs before every pipeline target, the downgrade is invisible
until a run fails with `unrecognized arguments`. `requirements.txt` is the
surface to pin; `requirements-lock.txt` is not consulted by `make install`.

## Related observation (same session, different root cause)

`DEV_MODEL_COMMIT` defaults to TinyLlama's hardcoded SHA. Overriding `DEV_MODEL`
(e.g. to `HuggingFaceTB/SmolLM2-135M-Instruct`) **without** also setting
`DEV_MODEL_COMMIT` fails at model load with `RevisionNotFoundError` /
`Invalid rev id`, because that SHA does not exist in the other repo. Override
both together (`make ... DEV_MODEL=... DEV_MODEL_COMMIT=<sha>`), matching the
Makefile comment on lines 171–174.

## Related observation: requirements-lock.txt was already unsatisfiable

Verifying the pin exposed that `requirements-lock.txt` pinned **both**
`heretic-llm==1.4.0` (line 51) **and** `optuna==5.0.0` (line 102). That
combination is impossible — `heretic-llm 1.4.0` declares `optuna~=4.7` — so the
generated lock could not have come from a real `pip freeze` of a satisfiable
environment. It predates (or was hand-touched after) the optuna constraint
surfaced by the pin fix.

`make lock` was **not** re-run in this change: on the local `.venv` it produces
~78 lines of unrelated version churn (boto3, cryptography, datasets, fastapi,
huggingface_hub…), because the ad-hoc environment is not the canonical one the
lock was captured from. Regenerating it is a separate, repo-wide change that
alters the reproducibility baseline and should be its own commit.

## References

- `requirements.txt:16` (now `heretic-llm==1.4.0`) and the `optuna` line
- `vendor/heretic/pyproject.toml` — `optuna~=4.7`
- `src/flow.py` `_decensor_one()` and `src/scripts/heretic_automate.exp`
- Makefile `DEV_MODEL_COMMIT` comment (lines 171–174)
- [[2026-09-26-mps-svd-lowrank-hang]] — the MPS hang this pin work was alongside
