# Quickstart: Validating the Metaflow-Orchestrated Pipeline

This guide runs the three User Stories' Independent Tests (from `spec.md`)
against the cheap dev-cycle model, per this feature's Assumptions
(verify against `DEV_MODEL` first; the same flow definition is
production-capable per FR-011/SC-007 — see "Scaling to production" below).

## Prerequisites

- `make setup` already run (`./.venv` exists, `requirements.txt` —
  including the new `metaflow` dependency — installed).
- An MLflow tracking destination reachable via `MLFLOW_TRACKING_URI` (a
  local `sqlite:///mlflow.db` is sufficient for this quickstart — same
  requirement `001` already has).
- macOS on Apple Silicon, to exercise User Story 2's MLX branch fully. On
  Linux, User Story 2's MLX-branch scenario is expected to fail with the
  named hardware error (Scenario in "Edge case: wrong hardware" below) —
  this is correct behavior, not a quickstart failure.

```sh
export MLFLOW_TRACKING_URI=sqlite:///mlflow.db
```

## Scenario 1 — User Story 1 (decensoring as one orchestrated run)

**Validates**: FR-001, FR-002, SC-001; both entry points (FR-001a).

```sh
# Entry point (a): make
make dev-abliterate-e2e DEVICE_MAP=cpu

# Entry point (b): direct Metaflow CLI, bypassing make entirely
.venv/bin/python flow.py run \
    --only_step decensor,log_to_mlflow \
    --model TinyLlama/TinyLlama-1.1B-Chat-v1.0 \
    --device_map cpu
```

**Expected outcome**: Exactly one orchestrated run per invocation produces
a saved decensored checkpoint under `DEV_OUT_DIR` **and** that run's
trial results already appear in MLflow under experiment
`wellspring-abliteration` — no second, separate command required (SC-001).
Verify:

```sh
test -d outputs/TinyLlama-TinyLlama-1.1B-Chat-v1.0-heretic && echo "checkpoint OK"
.venv/bin/python -c "
import mlflow
mlflow.set_tracking_uri('sqlite:///mlflow.db')
runs = mlflow.search_runs(experiment_names=['wellspring-abliteration'])
assert len(runs) > 0, 'expected at least one logged trial'
print(f'{len(runs)} trial(s) logged')
"
```

Both entry points MUST produce the same checkpoint path and the same
(non-duplicated — re-running is idempotent per FR-006) trial count in
MLflow.

## Scenario 2 — User Story 2 (both compression searches, orchestrated)

**Validates**: FR-003, FR-004, SC-002; FR-005/SC-005's hardware guard.

```sh
.venv/bin/python flow.py run \
    --only_step mlx_search,gguf_search \
    --hf_path outputs/TinyLlama-TinyLlama-1.1B-Chat-v1.0-heretic \
    --n_trials_mlx 2 --n_trials_gguf 2
```

**Expected outcome (on Apple Silicon)**: Both `mlx_search` and
`gguf_search` steps complete, each archiving its trials and logging to
MLflow under `wellspring-mlx-quant`/`wellspring-gguf-quant` respectively
— with parameters and archive locations supplied by the flow's own
`Parameter` defaults, never hand-typed twice (SC-002). Verify no
cross-contamination (FR-003's fan-back-only-for-reporting requirement):

```sh
diff <(ls outputs/*-mlx-optimize-archive/ 2>/dev/null) \
     <(ls outputs/*-gguf-optimize-archive/ 2>/dev/null) \
     && echo "UNEXPECTED: archives share filenames" \
     || echo "OK: archives are independent"
```

**Expected outcome (on Linux / non-Darwin)**: `mlx_search` fails
immediately with a named error (e.g. `ERROR: mlx_search requires macOS on
Apple Silicon...`) — confirming FR-005/SC-005 — while `gguf_search`
still completes successfully in the same run (fan-out branches fail
independently, per Metaflow's own per-task status model verified in
`research.md`).

## Scenario 3 — User Story 3 (interrupted run resumes without repeats)

**Validates**: FR-007, SC-003.

```sh
# Start a run, then interrupt it partway (Ctrl-C, or kill -9 the process)
# after the decensor step completes but before mlx_search/gguf_search finish.
.venv/bin/python flow.py run --model TinyLlama/TinyLlama-1.1B-Chat-v1.0 &
FLOW_PID=$!
sleep 30 && kill -9 $FLOW_PID   # adjust sleep so decensor has finished

# Resume — decensor must NOT re-run; only the interrupted step(s) continue.
.venv/bin/python flow.py resume
```

**Expected outcome**: The `resume` output contains no re-execution of
`decensor` (no new "Abliterating..." log line, no new checkpoint-directory
timestamp) — matching the empirical proof in `research.md` item 3 that an
already-completed step is skipped, not silently re-run. Verify by
checking the checkpoint directory's mtime is unchanged across the
interrupt/resume boundary:

```sh
BEFORE_MTIME=$(stat -f %m outputs/TinyLlama-TinyLlama-1.1B-Chat-v1.0-heretic 2>/dev/null)
# ... resume ...
AFTER_MTIME=$(stat -f %m outputs/TinyLlama-TinyLlama-1.1B-Chat-v1.0-heretic 2>/dev/null)
test "$BEFORE_MTIME" = "$AFTER_MTIME" && echo "OK: checkpoint not regenerated"
```

## Edge case: wrong hardware (FR-005/SC-005 explicit check)

```sh
# On a non-Darwin machine (or force via a stubbed platform check in a test):
.venv/bin/python flow.py run --only_step mlx_search --hf_path outputs/TinyLlama-TinyLlama-1.1B-Chat-v1.0-heretic
```

**Expected outcome**: Fails within seconds (before any model load), with
the exact error naming "Mac/Apple-Silicon" — never a generic crash, never
a silent no-op that produces no MLX output with no explanation.

## Cleanup after this quickstart

```sh
rm -rf .metaflow outputs/TinyLlama-* mlflow.db checkpoints/*.jsonl
```

(`.metaflow/` is git-ignored per `research.md` item 7 — this is a
convenience cleanup for local disk space, not a git-hygiene requirement.)

## Scaling to production (FR-011/SC-007 — informational, not part of this
## quickstart's pass/fail criteria)

The identical `flow.py` used above, invoked with production parameters
instead of dev-cycle ones, is the production path — no code change:

```sh
.venv/bin/python flow.py run \
    --model Qwen/Qwen3.6-35B-A3B \
    --model_commit <pinned-sha-from-PROVENANCE.md> \
    --quantization NONE
```

This is not exercised by the quickstart itself (production hardware is
out of scope for a dev-cycle validation guide), but SC-007 requires this
invocation to need zero changes to `flow.py` beyond the parameter values
shown — a fact this plan's design (flow-level `Parameter`s mirroring
every existing Makefile variable 1:1) makes true by construction, not by
a separate migration step.
</content>
