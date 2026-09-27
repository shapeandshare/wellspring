# Phase 0 Research: Full Pipeline Orchestration via Metaflow

All findings below were verified empirically against a real, running
Metaflow install in this repository's own `.venv` (Python 3.14) — not
inferred from documentation alone. Every throwaway test flow and its
`.metaflow/` local-datastore artifact was deleted after verification; none
of these experiments are part of the shipped implementation.

## 1. Does Metaflow actually run on Python 3.14?

**Decision**: Yes — proceed with `metaflow` unpinned-by-range (`metaflow`
with no upper bound) in `requirements.txt`, same convention as `mlflow`.

**Rationale**: PyPI's own classifiers for `metaflow` 2.19.39 (the latest
version at time of writing) list only `Programming Language :: Python ::
3.6` through `3.13` — no `3.14` classifier exists, and `requires_python` is
`None` (unbounded) on the PyPI JSON API. Classifiers are metadata, not an
enforced constraint, so this was verified directly rather than trusted:

```sh
pip install metaflow                    # succeeded cleanly, no build step
python -c "import metaflow; print(metaflow.__version__)"   # -> 2.19.39
```

A real `FlowSpec` with `@step`, `Parameter`, a two-branch fan-out/join, and
both `run` and `resume` commands was executed end-to-end (see items 3 and 4
below) — genuine runtime execution, not merely a successful import. No
runtime error, deprecation warning, or behavior difference from documented
behavior was observed on 3.14.

**Alternatives considered**: Downgrading the project's own pinned Python
version to 3.13 to match Metaflow's stated support range. Rejected —
`.python-version` pins 3.14 project-wide for reasons unrelated to this
feature (see `README.md`'s Requirements section), and the empirical test
above shows no actual incompatibility exists to fix.

## 2. Can Metaflow's remote-execution decorators reach Apple Silicon?

**Decision**: No `@kubernetes`/`@batch` (or any other remote-execution
decorator) is used anywhere in `flow.py`. Every step runs locally
(`python flow.py run`); the flow itself must be started directly on
whichever machine a given stage's hardware requires — identical to today's
"SSH to the right box, run the right `make` target" reality, just unified
under one flow definition instead of four separate commands.

**Rationale**: Confirmed via `docs.metaflow.org`'s own driver-install
documentation (cited in this feature's `spec.md` Assumptions, carried
forward from prior-session research, re-confirmed this session): AWS
Batch and Kubernetes both require a Linux container image; a Mac can only
ever be the *launcher* of a `@kubernetes`/`@batch` run, never a step's
actual execution target. Kubernetes' own `os` node-selector label accepts
only `linux`/`windows` — there is no path, in Metaflow or any comparable
orchestrator, to remotely schedule a step onto Apple Silicon hardware.
This is physical/API reality, not a Metaflow limitation to work around
with a plugin or extension.

**Alternatives considered**:
- *A custom remote-execution plugin targeting macOS runners*: rejected as
  wildly out of scope (Article VI/YAGNI) — no such mechanism exists in the
  Metaflow ecosystem, and building one is an infrastructure project, not a
  pipeline-orchestration feature.
- *Dropping the MLX stage from the orchestrated flow entirely, keeping it
  as a separate manual step*: rejected by the spec's own clarification
  (`spec.md` Q1 — Option A, "keep it in scope as a documented exception").

## 3. Does Metaflow's `resume` actually skip completed steps?

**Decision**: Rely on `python flow.py resume` (bare, no `--step`) as the
whole-pipeline resumability mechanism for FR-007/User Story 3 — no custom
checkpoint-skipping logic needs to be written.

**Rationale**: Empirically verified with a 3-step linear flow
(`start → flaky → end`) where `flaky` fails on its first invocation (via a
marker file) and succeeds on retry:

```text
run:     start ran → flaky raised RuntimeError("boom...") → Workflow failed
resume:  (no "start ran" printed — start was NOT re-executed)
         flaky succeeded (marker existed) → end ran → Done!
```

`start`'s side effect (`print("start ran")`) did not appear in the
`resume` output — direct proof the already-completed step was skipped,
not merely fast-forwarded through with its code silently re-executed.
This is exactly what FR-007 requires ("MUST NOT repeat any stage whose
output already exists and is valid") and exactly what User Story 3's
Acceptance Scenario 1 describes.

**Alternatives considered**: Hand-rolling a "does this stage's output
directory already exist?" guard inside each step (mirroring the
Makefile's own `convert-gguf`/`quantize-gguf` split pattern). Rejected —
Metaflow's `resume` already does this at the run level for free; adding a
second, redundant guard would be unjustified complexity (Article VI) and
risks the two mechanisms disagreeing about what "already done" means.

## 4. Does `--max-workers 1` really force sequential branch execution?

**Decision**: The flow's two compression-search steps are modeled as a
genuine Metaflow fan-out/join (`self.next(self.mlx_search,
self.gguf_search)` → both feed a `join` step). The existing
`OPTIMIZE_PARALLEL` topology switch (FR-006 — preserve existing
compute-topology behavior) is reproduced by conditionally passing
`--max-workers 1` (sequential, the safe default for one shared machine)
vs. leaving Metaflow's own default of 16 (concurrent, for the
dedicated-per-search-compute case) to `python flow.py run`.

**Rationale**: Empirically verified with a 4-step diamond flow
(`start → {a, b} → join → end`), each branch printing a timestamped
start/end line around a 1-second sleep:

```text
default (max-workers=16):  a starts 27.666, b starts 27.667 (concurrent — <1ms apart)
                            a ends 28.672, b ends 28.672 (finish together)
--max-workers 1:            a starts 29.630, a ends 30.637
                            b starts 30.844 (after a fully finished), b ends 31.847
```

This is a byte-for-byte match to the Makefile's own `optimize` target
semantics (`OPTIMIZE_PARALLEL=0` → `$(MAKE) optimize-mlx` then
`$(MAKE) optimize-gguf`, strictly sequential; `OPTIMIZE_PARALLEL=1` →
`$(MAKE) -j2 ...`, concurrent) — no new topology concept is introduced,
only an existing one re-expressed through Metaflow's own primitive.

**Alternatives considered**: A `@resources`/`@conda`-style per-step
concurrency limit, or wrapping both search steps in one combined step that
internally decides sequential-vs-parallel via `subprocess`/`threading`.
Rejected — `--max-workers` is Metaflow's own first-class mechanism for
exactly this, requires zero new code, and keeps the two searches as
genuinely independent steps (FR-004) rather than one step doing double
duty.

## 5. Does a step-level hardware guard fail the way FR-005/FR-002 require?

**Decision**: The MLX-search step begins with a plain Python guard clause
(`if platform.system() != "Darwin": raise RuntimeError("ERROR: ...")`) —
no Metaflow-specific hardware-gating decorator is used or needed.

**Rationale**: Empirically verified with a 3-step flow where the middle
step raises when not on Darwin. Metaflow's own output surfaced the
*exact* raised message and a normal Python traceback, then reported
`Step failure: Step mac_only (task-id 2) failed.` and a non-zero-implied
failure — no generic crash, no silent no-op, no swallowing. This
satisfies FR-005 ("MUST fail with a clear, specific error naming the
unmet hardware requirement, before attempting any expensive work") and
the Edge Cases section's underlying-tool-failure requirement (FR-002 edge
case: "MUST surface that failure as a failed stage with the underlying
tool's own error preserved").

Because the guard is the *first* line of the step body, it runs before
any of the step's actual work (model loading, `mlx_vlm.convert`
invocation, etc.) — satisfying "before any expensive work begins"
(SC-005) trivially, by ordering.

**Alternatives considered**: A custom `@requires_platform("Darwin")`
step decorator. Rejected as unjustified complexity (Article VI) — a
four-line guard clause is simpler, more auditable, and exercises the same
proven exception-surfacing path as every other failure mode in the flow
(no special-cased error handling needed for this one class of failure).

## 6. How should each stage's already-existing script be invoked from a step?

**Decision**: Every step body does exactly what the corresponding
Makefile recipe does today — either shells out via `subprocess.run([...])`
to the exact same command line (for `make convert-mlx`-driving steps like
`optimize_mlx.py`'s trials, which themselves already shell out to `make`)
or directly calls the already-tested script's `main()`/`run_study()`
entry point in-process where no subprocess boundary previously existed
(e.g. `log_heretic_to_mlflow.main()`).

**Rationale**: FR-006 is explicit: "This feature orchestrates those
existing behaviors; it MUST NOT weaken, bypass, or re-implement them
differently." `optimize_mlx.py`/`optimize_gguf.py` already contain their
own `subprocess.run(["make", "convert-mlx", ...])` calls internally (see
`scripts/optimize_mlx.py` lines 291-308) — that layering is untouched;
the flow step simply calls `run_study(...)` the same way the Makefile's
`optimize-mlx` recipe calls `python scripts/optimize_mlx.py` today.

**Alternatives considered**: Rewriting the four scripts' logic directly
inline into `flow.py`'s step bodies. Rejected — this would duplicate
already-tested, already-working code (violating Article VI Rule 4, "Reuse
before introducing") and would require re-testing logic that `001`
already covers with passing tests.

## 7. Where does Metaflow write its own run/step metadata, and does that need `.gitignore` attention?

**Decision**: Add `.metaflow/` to `.gitignore` (new entry, alongside the
existing `outputs/`/`checkpoints/`/etc. block).

**Rationale**: Every local `python flow.py run` invocation during this
session's verification created a `.metaflow/` directory in the current
working directory (Metaflow's local datastore for run/task metadata —
confirmed by direct observation: `git status` showed it as an untracked
directory after each test run, and it was deleted as part of this
session's cleanup discipline each time). This is exactly the kind of
transient, machine-local artifact `.gitignore` already protects (Article
IV/Additional Constraints — "Git hygiene for overridden paths") for
`outputs/`, `checkpoints/`, etc.

**Alternatives considered**: Pointing `METAFLOW_DATASTORE_SYSROOT_LOCAL`
somewhere already git-ignored (e.g. under `outputs/`). Rejected — adding a
dedicated `.gitignore` entry is simpler (Article VI) and keeps Metaflow's
own state visibly separate from pipeline *artifacts*, matching FR-009's
distinction between "supplementary index" (Metaflow's own tracking) and
"authoritative record" (the existing provenance sidecars).

## 8. Summary of resolved unknowns

No "NEEDS CLARIFICATION" markers remain in the Technical Context section
of `plan.md`. All primary-dependency, platform, and constraint questions
were resolved by direct, reproducible experimentation against this
project's actual pinned toolchain rather than by trusting library
documentation or PyPI metadata at face value — consistent with this
project's `AGENTS.md` §1 ("Ground claims in primary sources").
</content>
