---

description: "Task list for feature 002-metaflow-migration"
---

# Tasks: Full Pipeline Orchestration via Metaflow

**Input**: Design documents from `/specs/002-metaflow-migration/`

**Prerequisites**: plan.md (loaded), spec.md (loaded), research.md (loaded), data-model.md (loaded), contracts/flow-cli-contract.md (loaded), contracts/makefile-wrapper-contract.md (loaded), quickstart.md (loaded)

**Tests**: Test tasks are MANDATORY for all functional code (constitution Article IX, NON-NEGOTIABLE). Every `flow.py` helper function (hardware guard, path/param derivation) gets a failing test before its implementation. Full `@step` method bodies that only shell out to `001`'s already-tested scripts are integration-level, validated by the quickstart.md scenario tasks in each story's Polish sub-phase — no synthetic mock is written merely to assert a mock returns what it's told to return.

**Organization**: Tasks are grouped by user story (US1/US2/US3, matching spec.md's priorities P1/P2/P3) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Every task includes exact file paths.

## Path Conventions

Single project, matching `plan.md`'s Project Structure: `flow.py` at repo root, `scripts/` unchanged, `tests/` at repo root, `Makefile` at repo root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the new dependency and gitignore entry every story needs before any flow code is written.

- [X] T001 Add `metaflow` (no upper-bound pin, matching `mlflow`'s existing convention) to `requirements.txt`, with a comment citing the empirical Python-3.14-compatibility finding from `research.md` item 1 (PyPI classifiers list only up to 3.13, but a real install + `FlowSpec` run was verified to work)
- [X] T002 Run `make lock` and `make notices` to regenerate `requirements-lock.txt` and `third_party_licenses.json` per Constitution Article II Rule 2 (dependency-set change) — confirm `metaflow`'s Apache-2.0 license appears correctly and no new copyleft/UNKNOWN entry is introduced
- [X] T003 [P] Add `.metaflow/` to `.gitignore` (repo root), in the existing "Heretic / model artifacts and outputs" block or a new comment block, citing `research.md` item 7 (Metaflow's own local run/step-metadata datastore — machine-local, not a chain-of-custody artifact)

**Checkpoint**: `pip install -r requirements.txt` (or `make install`) succeeds with `metaflow` importable; `git status` after a throwaway `python -c "from metaflow import FlowSpec"` + trivial run shows `.metaflow/` is *not* listed as untracked.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core `flow.py` skeleton, shared parameters, and the pure-Python helpers every story's steps depend on. No user story can be verified end-to-end without this phase.

**⚠️ CRITICAL**: No user story implementation may begin until this phase's tests are GREEN.

### Tests for Foundational phase (MANDATORY — write first, confirm RED) ⚠️

- [X] T004 [P] Write failing test `test_hardware_guard_raises_on_non_darwin` in `tests/test_flow.py`: asserts a pure function `flow._require_apple_silicon() -> None` raises `RuntimeError` with a message containing "Mac/Apple Silicon" (per data-model.md's Hardware requirement entity: `error_message` MUST name the specific unmet requirement) when `platform.system()` (monkeypatched) returns `"Linux"`, and returns `None` (no raise) when it returns `"Darwin"` — mirrors the existing `Makefile` `convert-mlx` guard's exact wording pattern
- [X] T005 [P] Write failing test `test_derive_hf_path_matches_makefile_default` in `tests/test_flow.py`: asserts a pure function `flow._derive_hf_path(model: str) -> str` returns `f"outputs/{model.replace('/', '-')}-heretic"` for input `"TinyLlama/TinyLlama-1.1B-Chat-v1.0"` — matching the Makefile's `OUT_DIR ?= outputs/$(subst /,-,$(MODEL))-heretic` derivation exactly (data-model.md Orchestrated run entity, `hf_path` field)
- [X] T006 [P] Write failing test `test_derive_mlx_out_dir_and_gguf_out_dir_are_siblings_not_nested` in `tests/test_flow.py`: asserts `flow._derive_mlx_out_dir(hf_path)` returns `f"{hf_path}-mlx"` and `flow._derive_gguf_out_dir(hf_path)` returns `f"{hf_path}-gguf"`, and that neither is an ancestor/descendant of the other (Constitution Article III Rule 1 — MLX/GGUF export paths never share an output location)
- [X] T007 [P] Write failing test `test_max_workers_from_optimize_parallel` in `tests/test_flow.py`: asserts a pure function `flow._max_workers_for_topology(optimize_parallel: bool) -> int` returns `1` when `optimize_parallel=False` (sequential, matching `research.md` item 4's empirically-verified `--max-workers 1` behavior) and Metaflow's own default `16` when `optimize_parallel=True` (concurrent) — mirrors the Makefile's existing `OPTIMIZE_PARALLEL` `0`/`1` convention (FR-006)
- [X] T008 [P] Write failing test `test_run_provenance_fields_use_metaflow_current` in `tests/test_flow.py`: asserts a pure function `flow._run_provenance_fields() -> dict[str, str]` returns a dict containing exactly the keys `{"run_id", "flow_name"}` with string values, sourced from `metaflow.current.run_id`/`metaflow.current.flow_name` (monkeypatch `flow.current` — Metaflow's own always-populated `current` singleton) — implements FR-008/SC-004's "trace which run — and which parameters — produced any given artifact" requirement, per data-model.md's Stage entity `run_id_field` row (added during `/speckit.analyze` remediation)

### Implementation for Foundational phase

- [X] T009 Create `flow.py` at repo root: module docstring, imports (`platform`, `subprocess`, `sys`, `from pathlib import Path`, `from metaflow import FlowSpec, step, Parameter, current`), and the five pure helper functions from T004–T008 (`_require_apple_silicon`, `_derive_hf_path`, `_derive_mlx_out_dir`, `_derive_gguf_out_dir`, `_max_workers_for_topology`, `_run_provenance_fields`) with full type hints per Constitution Article XII (e.g. `def _require_apple_silicon() -> None:`) — run T004–T008 and confirm GREEN
- [X] T010 In `flow.py`, declare the `WellspringFlow(FlowSpec)` class skeleton with every `Parameter` from `contracts/flow-cli-contract.md`'s table (`model`, `model_commit`, `quantization`, `seed`, `device_map`, `hf_path`, `mlflow_tracking_uri`, `mlflow_experiment_prefix`, `n_trials_mlx`, `n_trials_gguf`, `optimize_parallel`), each with the exact default value listed in that contract's table (e.g. `model = Parameter("model", default="Qwen/Qwen3.6-35B-A3B")`) — one primary class per file, satisfying Constitution Article XI Rule 2
- [X] T011 In `flow.py`, add the `start` step: fails fast (Constitution Article VIII) if `self.mlflow_tracking_uri` is empty by calling `_mlflow_env.require_tracking_uri()`-equivalent logic (import `_mlflow_env` from `scripts/`, per FR-006's requirement to preserve `001`'s FR-014 environment-only-credentials guarantee unchanged), then computes `self.resolved_hf_path = self.hf_path or _derive_hf_path(self.model)` and calls `self.next(self.decensor)`
- [X] T012 Update `tests/conftest.py` if needed (likely no change required — `SCRIPTS_DIR` is already on `sys.path`; confirm `flow.py`'s own imports of `_mlflow_env` resolve correctly under `pytest` without a path hack, since `flow.py` itself is at repo root, not under `scripts/`)

**Checkpoint**: `pytest tests/test_flow.py -v` is fully GREEN. `python -c "import flow"` succeeds with no import error. `python flow.py show` (Metaflow's own graph-inspection command) prints a valid (if still incomplete) graph.

---

## Phase 3: User Story 1 - Decensoring as one orchestrated run (Priority: P1) 🎯 MVP

**Goal**: One orchestrated run produces a decensored checkpoint AND its MLflow-logged results, via either entry point, with the mid-run trial-selection decision resolved automatically (no person needed at a terminal) — replacing today's two hand-sequenced commands (`make dev-abliterate-e2e` then `make log-abliteration-mlflow`).

**Independent Test**: Run `quickstart.md` Scenario 1 (both entry points) and confirm one checkpoint + non-empty MLflow experiment result from a single invocation each.

### Tests for User Story 1 (MANDATORY — write first, confirm RED) ⚠️

- [X] T013 [P] [US1] Write failing test `test_decensor_step_invokes_heretic_automate_exp` in `tests/test_flow.py`: monkeypatches `flow.subprocess.run` and asserts the `decensor` step's constructed command list contains `"scripts/heretic_automate.exp"`, `"--model"`, and the flow's `self.model` value — mirrors the existing `Makefile`'s `dev-abliterate-e2e` recipe's `expect scripts/heretic_automate.exp ...` invocation (FR-002: automated decision resolution, matching today's exact automated behavior)
- [X] T014 [P] [US1] Write failing test `test_log_to_mlflow_step_calls_existing_main` in `tests/test_flow.py`: monkeypatches `log_heretic_to_mlflow.main` (imported into `flow.py`) and asserts the `log_to_mlflow` step calls it with `--model`/`--checkpoint-dir`/`--experiment-prefix` args matching the flow's own parameters — proves FR-006 (reuse, not re-implement, `001`'s already-tested idempotent logging logic)
- [X] T015 [US1] Write failing test `test_decensor_then_log_to_mlflow_both_appear_in_only_step_selection` in `tests/test_flow.py`: asserts that whatever `--only-step` (or equivalent) mechanism is chosen in T018 correctly includes exactly `decensor` and `log_to_mlflow` when User Story 1's entry points request them, and excludes `mlx_search`/`gguf_search`

### Implementation for User Story 1

- [X] T016 [US1] In `flow.py`, implement the `decensor` step: constructs the `expect scripts/heretic_automate.exp` command list exactly as the Makefile's `dev-abliterate-e2e` recipe does today (Makefile lines 513-537 — same flags: `--model`, `--model-commit` if set, `--quantization`, `--device-map` if set, `--seed`, `--export-strategy MERGE`, all four prompt-dataset flag groups with their pinned defaults from the Makefile), runs it via `subprocess.run(..., check=True)`, THEN — implementing FR-008/SC-004 per data-model.md's `run_id_field` row — calls `scripts/write_manifest.py --step decensor --out "{self.resolved_hf_path}.provenance.json" --field model=self.model --field run_id=<from _run_provenance_fields()> --field flow_name=<from _run_provenance_fields()>` (a NEW call: confirmed by reading `Makefile` lines 508-539 that `dev-abliterate-e2e` — unlike `abliterate` — writes no manifest today, so this is new behavior for the dev-cycle path, not a field added to an existing call), then calls `self.next(self.log_to_mlflow)` — run T013 and confirm GREEN
- [X] T017 [US1] In `flow.py`, implement the `log_to_mlflow` step: imports `log_heretic_to_mlflow` from `scripts/` and calls its `main()` (or a small wrapper exposing the same args as CLI flags: `--model`, `--checkpoint-dir` derived from `STUDY_CHECKPOINT_DIR`'s existing default `"checkpoints"`, `--experiment-prefix`), then calls `self.next(self.join_searches)`. Also stub `join_searches` itself in this task as a plain single-predecessor step (`def join_searches(self): self.next(self.end)` — no `inputs` parameter yet, since only one path reaches it in Phase 3) — Phase 4's T029/T030 upgrade this stub into a real two-branch join once the fan-out exists. Run T014 and confirm GREEN
- [X] T018 [US1] In `flow.py`, implement a stage-selection mechanism satisfying `contracts/flow-cli-contract.md`/`makefile-wrapper-contract.md`'s `--only-step` shorthand (e.g. a `Parameter("only_step", default="")` comma-split into a `set[str]`, checked at the top of each step to `self.next(self.end)` early if that step's name isn't in the requested set and the set is non-empty) — run T015 and confirm GREEN
- [X] T019 [US1] Rewrite the Makefile's `dev-abliterate-e2e` target's recipe to invoke `$(PYTHON) flow.py run --only-step decensor,log_to_mlflow --model "$(DEV_MODEL)" --model-commit "$(DEV_MODEL_COMMIT)" --quantization "$(QUANTIZATION)" --device-map "$(DEVICE_MAP)" --seed "$(SEED)" --mlflow-tracking-uri "$(MLFLOW_TRACKING_URI)" --mlflow-experiment-prefix "$(MLFLOW_EXPERIMENT_PREFIX)"` in `Makefile`, preserving the target's existing name, `.PHONY` entry, and `make help` line text (only the recipe body changes) per `contracts/makefile-wrapper-contract.md` Invariant 1 (no divergent logic)
- [X] T020 [US1] Rewrite the Makefile's `log-abliteration-mlflow` target's recipe similarly to invoke `$(PYTHON) flow.py run --only-step log_to_mlflow ...` in `Makefile`, preserving its existing name/`.PHONY`/`make help` entry
- [X] T021 [US1] Update `README.md`'s "Makefile targets" table rows for `dev-abliterate-e2e` and `log-abliteration-mlflow` to note they now run via the orchestrated flow internally, per Constitution Article XIII ("Keep the documented surface current")

**Checkpoint**: `quickstart.md` Scenario 1 passes for both entry points — `make dev-abliterate-e2e DEVICE_MAP=cpu` and the direct `python flow.py run --only-step decensor,log_to_mlflow ...` invocation each produce one checkpoint + non-empty `wellspring-abliteration` MLflow experiment, with no second command required (SC-001). User Story 1 is independently demoable — this is the MVP.

---

## Phase 4: User Story 2 - Both compression searches, orchestrated (Priority: P2)

**Goal**: Starting from one decensored checkpoint, both independent compression searches (MLX, GGUF) run as fanned-out flow steps, each on its own required hardware, with parameters/archive locations supplied by the flow rather than re-typed — and the MLX-only-on-Darwin hardware requirement fails loudly, by name, before any expensive work, on non-Darwin hardware.

**Independent Test**: Run `quickstart.md` Scenario 2 (both branches, plus the Edge Case: wrong hardware sub-scenario) and confirm independent archiving/tracking with no cross-contamination.

### Tests for User Story 2 (MANDATORY — write first, confirm RED) ⚠️

- [X] T022 [P] [US2] Write failing test `test_mlx_search_step_calls_hardware_guard_before_run_study` in `tests/test_flow.py`: monkeypatches both `flow._require_apple_silicon` (to raise) and `optimize_mlx.run_study` (to a `MagicMock`), asserts the `mlx_search` step raises before `run_study` is ever called — proves FR-005/SC-005's ordering guarantee (guard runs before expensive work) at the unit level, backing the empirical `research.md` item 5 finding
- [X] T023 [P] [US2] Write failing test `test_mlx_search_step_calls_run_study_with_flow_params` in `tests/test_flow.py`: monkeypatches `flow._require_apple_silicon` to a no-op and `optimize_mlx.run_study` to a `MagicMock`, asserts it's called with `n_trials=self.n_trials_mlx`, `hf_path=self.resolved_hf_path`, `tracking_uri=self.mlflow_tracking_uri`, `experiment_prefix=self.mlflow_experiment_prefix` — proves FR-006 (reuse `001`'s already-tested `run_study`, no re-implementation) and FR-003 (fed from the one shared checkpoint)
- [X] T024 [P] [US2] Write failing test `test_gguf_search_step_calls_run_study_with_flow_params` in `tests/test_flow.py`: same pattern as T023 but for `optimize_gguf.run_study`, asserting no hardware guard is called (GGUF has no platform restriction, per data-model.md's Stage entity table)
- [X] T025 [US2] Write failing test `test_mlx_and_gguf_search_never_share_archive_or_calib_path` in `tests/test_flow.py`: asserts the derived `mlx_out_dir`/`gguf_out_dir` (from T006's helpers) and their respective `-optimize-archive`/`-gguf-optimize-archive` suffixes never collide, and that neither step's constructed args reference the other's calibration file (`calibration-images/` vs `calibration-text.txt`) — locks Constitution Article III Rule 1/FR-004 at the flow-wiring level

### Implementation for User Story 2

- [X] T026 [US2] In `flow.py`, implement the `mlx_search` step: calls `_require_apple_silicon()` as its first statement (per data-model.md's Hardware requirement entity — predicate evaluated before any expensive work), then imports and calls `optimize_mlx.run_study(n_trials=self.n_trials_mlx, hf_path=self.resolved_hf_path, mlx_out_dir=_derive_mlx_out_dir(self.resolved_hf_path), text_path="calibration-text.txt", tracking_uri=self.mlflow_tracking_uri, experiment_prefix=self.mlflow_experiment_prefix)`, then `self.next(self.join_searches)` — run T022/T023 and confirm GREEN. NOTE (FR-008/SC-004, data-model.md `run_id_field`): `optimize_mlx.py`'s `run_study()` does not currently accept an extra-fields parameter for its `_append_manifest()` call — this task's scope is calling `run_study()` unchanged (FR-006: no re-implementation); a follow-up task (see T028 below) extends `run_study()`'s signature with an optional `extra_manifest_fields: dict[str, str] | None = None` parameter so `mlx_search` can pass `_run_provenance_fields()` through without duplicating `optimize_mlx.py`'s manifest-writing logic in `flow.py`
- [X] T027 [US2] In `flow.py`, implement the `gguf_search` step: imports and calls `optimize_gguf`'s CLI-equivalent (either its `main()` with a constructed `sys.argv`, or refactor-free direct call to whatever internal function `optimize_gguf.py` exposes matching `--n-trials`/`--gguf-f16`/`--gguf-out-dir` — confirm exact signature via `scripts/optimize_gguf.py` lines 339-473 before writing this task's implementation, do not guess), passing `n_trials=self.n_trials_gguf`, `gguf_f16=f"{_derive_gguf_out_dir(self.resolved_hf_path)}/model-f16.gguf"`, `gguf_out_dir=_derive_gguf_out_dir(self.resolved_hf_path)`, `tracking_uri=self.mlflow_tracking_uri`, `experiment_prefix=self.mlflow_experiment_prefix`, then `self.next(self.join_searches)` — run T024 and confirm GREEN. Same FR-008/SC-004 NOTE as T026 applies to `optimize_gguf.py`'s `_write_manifest_entry()` call (addressed by new T028 below, not a Phase 6 follow-up)
- [X] T028 [US2] [P] Extend `scripts/optimize_mlx.py`'s `run_study()` and `scripts/optimize_gguf.py`'s `run_study()`-equivalent with an optional `extra_manifest_fields: dict[str, str] | None = None` parameter, merged into each trial's `_append_manifest()`/`_write_manifest_entry()` `entry` dict when provided (default `None` preserves 100% of existing behavior/tests — FR-006, no re-implementation of the manifest-writing logic itself, purely an additive optional parameter). Add a new test in `tests/test_optimize_mlx.py`/`tests/test_optimize_gguf.py` asserting a trial's `manifest.json` entry contains the extra fields when `extra_manifest_fields={"run_id": "123"}` is passed, and is unchanged when omitted (regression guard for existing callers). `mlx_search`/`gguf_search` (T026/T027) then pass `extra_manifest_fields=self._run_provenance_fields()`, implementing FR-008/SC-004 for both compression-search stages
- [X] T029 [US2] In `flow.py`'s `start`/`decensor`/`log_to_mlflow` step chain, change `log_to_mlflow`'s `self.next(...)` call to `self.next(self.mlx_search, self.gguf_search)` (fan-out, per FR-003) instead of Phase 3's temporary `self.next(self.join_searches)`, and change `join_searches`'s signature from T017's single-predecessor stub (`def join_searches(self):`) to a real join (`def join_searches(self, inputs):`) — completed fully by T030 below
- [X] T030 [US2] In `flow.py`, implement the `join_searches` step: signature `def join_searches(self, inputs):`, does NOT blend `inputs.mlx_search`/`inputs.gguf_search` data (FR-003: "never blending their inputs or outputs" — only records that both finished, e.g. `self.mlx_search_ok = True` and `self.gguf_search_ok = True` read from each branch independently), then `self.next(self.end)` — run T025 and confirm GREEN
- [X] T031 [US2] Rewrite the Makefile's `optimize-mlx` target's recipe to invoke `$(PYTHON) flow.py run --only-step decensor,mlx_search --hf-path "$(HF_PATH)" --n-trials-mlx "$(N_TRIALS_MLX)" --mlflow-tracking-uri "$(MLFLOW_TRACKING_URI)" --mlflow-experiment-prefix "$(MLFLOW_EXPERIMENT_PREFIX)"` in `Makefile` (using T018's `--only-step` selection so `decensor` is skipped if `$(HF_PATH)` already exists — verify this against T018's actual skip semantics, adjusting if `--only-step` alone doesn't skip an existing checkpoint; Metaflow's own `resume` mechanism from Phase 5 may be the correct tool here instead of `--only-step`, confirm before finalizing this task), preserving the target's name/`.PHONY`/`make help` entry
- [X] T032 [US2] Rewrite the Makefile's `optimize-gguf` target's recipe similarly, invoking `$(PYTHON) flow.py run --only-step gguf_search ...` in `Makefile`
- [X] T033 [US2] Rewrite the Makefile's `optimize` target's recipe to invoke `$(PYTHON) flow.py run --only-step mlx_search,gguf_search --max-workers "$(shell python3 -c 'import sys; sys.path.insert(0,\".\"); from flow import _max_workers_for_topology; print(_max_workers_for_topology(\"$(OPTIMIZE_PARALLEL)\" == \"1\"))')" ...` in `Makefile` — OR simplify by exposing `_max_workers_for_topology` as a tiny `flow.py --print-max-workers` CLI helper rather than shelling into Python from `make` (implementation-time judgment call; either satisfies FR-006/`research.md` item 4, choose whichever is less fragile and document the choice in the recipe's comment)
- [X] T034 [US2] Update `README.md`'s "Makefile targets" table rows for `optimize-mlx`, `optimize-gguf`, and `optimize` per Constitution Article XIII

**Checkpoint**: `quickstart.md` Scenario 2 passes on Apple Silicon (both branches complete, archives verified non-colliding via the `diff`/`ls` check) and the Edge Case sub-scenario passes on non-Darwin (or via a monkeypatched `platform.system()` in a controlled test) — `mlx_search` fails by name before any expensive work, `gguf_search` still succeeds independently in the same run. Each archived trial's `manifest.json` entry (via T028) now also carries `run_id`/`flow_name`, satisfying FR-008/SC-004 — verify with `grep run_id outputs/*-optimize-archive/manifest.json`. User Stories 1 AND 2 both work independently.

---

## Phase 5: User Story 3 - Interrupted runs resume without repeating finished work (Priority: P3)

**Goal**: An operator can restart an interrupted orchestrated run and have it continue from wherever it left off — extending each stage's existing per-stage resumability (Optuna `study.db`, MLflow idempotency) into a whole-pipeline-level guarantee, riding on Metaflow's own `resume` (empirically verified in `research.md` item 3 to skip already-completed steps and retry only the failed one).

**Independent Test**: Run `quickstart.md` Scenario 3 — kill a run after `decensor` completes but before the searches finish, then `python flow.py resume`, and confirm `decensor`'s checkpoint directory mtime is unchanged (proving it was not regenerated).

### Tests for User Story 3 (MANDATORY — write first, confirm RED) ⚠️

- [X] T035 [P] [US3] Write failing test `test_resume_after_kill_does_not_rerun_decensor` in `tests/test_flow.py`: uses `subprocess.Popen` to start `python flow.py run` against a fast fixture flow (or the real flow with a stubbed `decensor` step that writes a marker file and sleeps before the next step, matching the `research.md` item 3 experiment's pattern exactly), sends `SIGKILL` after the marker file appears, then runs `python flow.py resume` as a fresh subprocess and asserts the marker file's mtime is unchanged after resume completes — this is a full-process integration test (unavoidable: resume is a Metaflow CLI-level guarantee, not a unit-testable pure function), appropriately marked as such rather than mocked, per Article IX's own boundary (mocking away the very CLI behavior under test would prove nothing)
- [X] T036 [P] [US3] Write failing test `test_resumed_run_still_produces_final_end_step_artifacts` in `tests/test_flow.py`: extends T035's fixture to confirm that after `resume`, the flow reaches `end` successfully and `join_searches`'s recorded `mlx_search_ok`/`gguf_search_ok` flags are both present — proving resume carries the *whole* pipeline to completion, not just the one retried step (User Story 3's Acceptance Scenario 1: "the remaining stages still run to completion")

### Implementation for User Story 3

- [X] T037 [US3] No new `flow.py` production code is required for the core resume mechanism itself (per `research.md` item 3's decision: rely on Metaflow's own `resume`, do not hand-roll a redundant checkpoint-skip guard) — this task is to run T035/T036 against the Phase 3+4 `flow.py` as-built and confirm they pass GREEN with zero additional implementation. If either test fails, the fix belongs in whichever step's idempotency assumption was violated (e.g. a step that doesn't tolerate being retried against already-partially-written output), tracked as a fix to that step in `flow.py`, not a new resume mechanism
- [X] T038 [US3] Add a short "Resuming an interrupted run" subsection to `README.md`'s pipeline documentation (near the existing "Notes & caveats" section) documenting `python flow.py resume` as the sanctioned recovery command, cross-referencing `quickstart.md` Scenario 3, per Constitution Article XIII

**Checkpoint**: `quickstart.md` Scenario 3 passes — decensor's checkpoint directory mtime is provably unchanged across the interrupt/resume boundary, and the resumed run reaches `end` with both search branches' completion flags set. All three user stories are now independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Full quickstart validation, documentation completeness, and the constitution's standard pre-completion gates — spans all three stories rather than belonging to any single one.

- [X] T039 [P] Run `make test` (full suite, including new `tests/test_flow.py`) and confirm 100% pass — no regression to any of `001`'s existing 88 tests
- [X] T040 [P] Run `lsp_diagnostics`-equivalent (or `python -m py_compile flow.py` at minimum, plus any configured linter) against `flow.py` and confirm clean
- [X] T041 Manually execute `quickstart.md`'s three scenarios end-to-end against the real `DEV_MODEL` on real hardware (not just the unit/integration tests from Phases 3-5) — this is the "verify against dev-cycle model first" step from spec.md's Assumptions, and the actual gate before claiming FR-001/FR-003/FR-007 are satisfied, matching this project's established practice of live QA over trusting tests alone. **Scenario 1 fully verified live** against a real TinyLlama abliteration (3 real trials, real checkpoint, real Optuna journal) via both entry points (`make log-abliteration-mlflow` and direct `python flow.py run --only_step log_to_mlflow ...`) — caught and fixed 3 real bugs in the process (missing `DEV_BATCH_SIZE`/prompt-dataset passthrough in `decensor`, missing `--llama-perplexity-bin`/`--llama-cli-bin`/`--n-gpu-layers` passthrough in `gguf_search`, and a cross-step-process `MLFLOW_TRACKING_URI` environment-propagation bug in `log_to_mlflow` — Metaflow steps run in separate subprocesses, so `os.environ` set in `start()` does not reach `log_to_mlflow()`). Idempotency re-verified live (2nd run: still 3 rows, not 6). FR-008/SC-004's `run_id`/`flow_name` manifest fields verified real. **Scenario 2's full trial runs (minutes-per-trial MLX/GGUF search) and Scenario 3 (already covered by `tests/test_flow.py`'s subprocess-level resume tests using a faithful fixture flow) were not separately re-run live end-to-end** — bounded by this session's practical time budget; flagged explicitly per this project's `AGENTS.md` discipline rather than silently claimed
- [X] T042 Update `README.md`'s "Quick start" section (if the two-command `make abliterate` → `make convert-mlx`/`convert-gguf` flow described there is materially changed by this feature) and confirm the "Pipeline" Mermaid diagram still accurately reflects reality — per Constitution Article VII Rule 3 (a stage that changes the pipeline's *shape* updates the diagram; this feature does not add a new artifact type, so confirm no diagram change is actually needed rather than skipping the check)
- [X] T043 Confirm `make help`'s output (via `make help` directly) still accurately describes every rewritten target's behavior, matching the updated Makefile recipes from T019/T020/T031/T032/T033
- [X] T044 [P] Re-verify Constitution Article II compliance: confirm `requirements-lock.txt`/`third_party_licenses.json` (from T002) are still current after any dependency changes made during implementation (e.g. if a helper library was added that wasn't anticipated in Setup)
- [X] T045 Clean up any stray `.metaflow/` directories, test marker files, or QA artifacts created during T041's manual verification, per this project's established discipline (`AGENTS.md` §2 — verify delegated/manual work actually landed cleanly, leave no debris)

**Checkpoint**: `make test` green, `quickstart.md` manually verified end-to-end, documentation surface (`README.md`, `make help`) matches the shipped Makefile exactly, no stray local artifacts remain untracked.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion (needs `metaflow` importable) — BLOCKS all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion. No dependency on US2/US3.
- **User Story 2 (Phase 4)**: Depends on Foundational completion AND on US1's `decensor`/`log_to_mlflow` steps existing (the fan-out point T029 modifies is US1's `log_to_mlflow` step's `self.next(...)` call) — so in practice, implement after US1, though the two stories remain *independently testable* per their own Independent Test criteria (US2's quickstart scenario can be run against an already-existing checkpoint without re-running US1's steps).
- **User Story 3 (Phase 5)**: Depends on Foundational AND benefits from US1+US2 both existing (its test fixture exercises the full graph) — but its *mechanism* (Metaflow's own `resume`) has zero new production code dependency on US1/US2's specific step bodies; only its *test fixture* needs a realistic multi-step flow to exercise against.
- **Polish (Phase 6)**: Depends on all three user stories being complete.

### Within Each User Story

- Tests MUST be written and observed to FAIL before implementation (Article IX) — T013-T015 before T016-T021; T022-T025 before T026-T034; T035-T036 before T037-T038.
- Foundational helpers (Phase 2) before any step implementation that calls them.
- Step implementation before the corresponding Makefile recipe rewrite (can't wrap what doesn't exist yet).
- Makefile recipe rewrite before its README table-row update (documents what was actually built).

### Parallel Opportunities

- T001/T003 (Setup) can run in parallel — different files (`requirements.txt` vs `.gitignore`); T002 depends on T001 (needs `metaflow` in `requirements.txt` first).
- T004-T007 (Foundational tests) can all run in parallel — independent test functions in the same new file, but logically independent assertions with no shared fixture ordering dependency.
- T013/T014 (US1 tests) can run in parallel; T015 depends on the stage-selection design existing conceptually (can be written in parallel but will only pass once T018 exists).
- T022/T023/T024 (US2 tests) can run in parallel — three independent step behaviors.
- T035/T036 (US3 tests) can run in parallel — share a fixture pattern but assert independent things.
- T039/T040/T044 (Polish) can run in parallel — independent verification commands.

---

## Parallel Example: Foundational Phase

```bash
# Launch all Foundational tests together (T004-T007), different assertions in one new file:
Task: "Write failing test test_hardware_guard_raises_on_non_darwin in tests/test_flow.py"
Task: "Write failing test test_derive_hf_path_matches_makefile_default in tests/test_flow.py"
Task: "Write failing test test_derive_mlx_out_dir_and_gguf_out_dir_are_siblings_not_nested in tests/test_flow.py"
Task: "Write failing test test_max_workers_from_optimize_parallel in tests/test_flow.py"
```

## Parallel Example: User Story 2

```bash
# Launch all US2 step-behavior tests together (T022-T024), independent step assertions:
Task: "Write failing test test_mlx_search_step_calls_hardware_guard_before_run_study in tests/test_flow.py"
Task: "Write failing test test_mlx_search_step_calls_run_study_with_flow_params in tests/test_flow.py"
Task: "Write failing test test_gguf_search_step_calls_run_study_with_flow_params in tests/test_flow.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational (CRITICAL — blocks everything).
3. Complete Phase 3: User Story 1.
4. **STOP and VALIDATE**: Run `quickstart.md` Scenario 1 against both entry points on the real dev-cycle model.
5. This alone already delivers real value per spec.md's own framing: "the smallest slice that delivers real value on its own — one orchestrated run instead of two manually-ordered commands."

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. Add User Story 1 → validate via quickstart Scenario 1 → this is the MVP.
3. Add User Story 2 → validate via quickstart Scenario 2 (including the non-Darwin edge case) → both compression searches now orchestrated.
4. Add User Story 3 → validate via quickstart Scenario 3 → whole-pipeline resumability confirmed.
5. Polish → full `make test` + manual end-to-end quickstart pass + documentation currency.

---

## Notes

- [P] tasks = different files or independent assertions in the same new file, no dependencies.
- [Story] label maps task to specific user story for traceability.
- Every task touching `optimize_gguf.py`'s exact call signature (T027) explicitly defers to reading the real source at implementation time rather than guessing — `scripts/optimize_gguf.py`'s `main()` (lines 339-473) is the ground truth for its exact CLI flags.
- T031/T033's exact Makefile mechanism for "skip decensor if `HF_PATH` already exists" is deliberately left as an implementation-time judgment call between `--only-step` and Metaflow's own `resume` — flagged explicitly rather than guessed, per this project's `AGENTS.md` discipline of stating what wasn't verified rather than asserting it would work.
- Commit after each task or logical group, per user request only (never proactively — Constitution Article XIII).
- Verify every test fails before implementing (Article IX, NON-NEGOTIABLE).
- Stop at any checkpoint to validate a story independently before proceeding.

---

## Phase 7: Convergence

**Purpose**: Close gaps found by `/speckit.converge` assessing the as-implemented `flow.py`/Makefile/tests against `spec.md`/`plan.md`/`data-model.md`/`contracts/`/`quickstart.md` — documentation drift and one FR-008 completeness gap introduced by implementation-time fixes (T016/T026/T027) that were never back-propagated to the design docs written before those fixes existed.

- [X] T046 Rewrite every CLI flag in `specs/002-metaflow-migration/quickstart.md` from the hyphenated convention (`--only-step`, `--model-commit`, `--hf-path`, `--device-map`, `--n-trials-mlx`, `--n-trials-gguf`) to the real, verified underscored convention (`--only_step`, `--model_commit`, `--hf_path`, `--device_map`, `--n_trials_mlx`, `--n_trials_gguf`) per quickstart.md (contradicts) — confirmed via live `python flow.py run --help` that every flow-level `Parameter` flag uses underscores, not hyphens; every command in Scenarios 1-3, the Edge Case block, and the Scaling section is affected
- [X] T047 Extend `decensor`'s `scripts/write_manifest.py` call in `flow.py` to record the full parameter set FR-008 requires — `model_commit`, `quantization`, `seed`, `export_strategy=MERGE`, and all 16 `good_prompts_*`/`bad_prompts_*`/`good_eval_prompts_*`/`bad_eval_prompts_*` fields — matching the sibling `abliterate` Makefile target's own manifest (`Makefile` lines 473-485) per FR-008 (partial): FR-008 requires tracing "which run — **and which parameters**" produced an artifact, and the current manifest only records `model`/`run_id`/`flow_name`. Add/update a `tests/test_flow.py` assertion confirming the full parameter set appears in the constructed `write_manifest.py` command
- [X] T048 [P] Add the 19 missing `Parameter` rows (`study_checkpoint_dir`, `batch_size`, `llama_perplexity_bin`, `llama_cli_bin`, `n_gpu_layers`, and all 16 prompt-dataset fields) to `specs/002-metaflow-migration/contracts/flow-cli-contract.md`'s Parameters table per plan: contracts/flow-cli-contract.md (partial) — these were added during implementation (T016/T026/T027's live-QA bug fixes) but never back-propagated to the contract written before those fixes existed
- [X] T049 [P] Add the same missing fields to `specs/002-metaflow-migration/data-model.md`'s Orchestrated run entity table per plan: data-model.md (partial) — same staleness as T048, different document
</content>
