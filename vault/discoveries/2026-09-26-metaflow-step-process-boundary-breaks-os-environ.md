---
title: Metaflow steps run in separate processes — os.environ does not cross step boundaries
type: discovery
tags:
  - type/discovery
  - domain/orchestration
  - status/reviewed
created: 2026-09-26
updated: 2026-09-26
---

# Metaflow steps run in separate processes — os.environ does not cross step boundaries

`flow.py`'s `start` step set `os.environ["MLFLOW_TRACKING_URI"]`, expecting
the `log_to_mlflow` step (later in the same run) to inherit it. It didn't —
`log_to_mlflow` failed with `ERROR: MLFLOW_TRACKING_URI is not set` even
though `start` had just set it moments earlier in the same run.

## What was tested / observed

A real, live `python flow.py run --only_step log_to_mlflow --mlflow_tracking_uri
sqlite:///mlflow.db ...` invocation. The Metaflow log output showed each
step running as a distinct OS process (`pid 39944`, `pid 39951`, different
PIDs per step). `start`'s `os.environ` mutation lived only in its own
process's memory and was gone by the time `log_to_mlflow`'s process
started.

## Finding

Metaflow `@step`s are **not** function calls within one long-lived Python
process — each step is dispatched as its own subprocess invocation of
`flow.py step <name> ...` (confirmed directly in the log: `flow.py --quiet
--metadata local ... step log_to_mlflow --run-id ...`). Any `os.environ`
mutation performed in one step is invisible to every other step, including
the very next one in the same run.

## Relevance

Any value one step needs to pass to a later step must go through Metaflow's
own artifact mechanism (`self.some_field = value`, read back as
`self.some_field` in the next step) or be re-derived/re-passed explicitly —
never through `os.environ`. `log_to_mlflow` was fixed by passing
`--tracking-uri` directly as a CLI argument to
`log_heretic_to_mlflow.main()`'s constructed `sys.argv`, rather than relying
on the environment. `mlx_search`/`gguf_search` were unaffected because they
already passed `tracking_uri`/`--tracking-uri` as explicit arguments, not
via environment inheritance.

## References

- `flow.py`'s `log_to_mlflow` step (the fix)
- `tests/test_flow.py::test_log_to_mlflow_step_calls_existing_main` (the
  regression test, with an inline comment documenting this exact finding)
</content>
