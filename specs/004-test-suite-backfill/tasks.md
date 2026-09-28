# Tasks: Backfill Hermetic Tests for Untested Pipeline Logic

**Input**: Design documents from `/specs/004-test-suite-backfill/`

**Prerequisites**: plan.md (required, loaded), spec.md (required, loaded), research.md (loaded), quickstart.md (loaded). No `data-model.md` or `contracts/` — this feature adds no entities and no external interface (plan.md, Project Structure section).

**Tests**: Test tasks are the deliverable of this feature (constitution Article IX, MD-002/MD-004 backfill). Because FR-002 forbids changing production behavior, there is no separate "implementation" step per module — the characterization test IS the task, written to match each module's **current** actual behavior, then proven capable of failing via a one-off manual mutation (SC-001). The one genuine build step is the hermetic guard itself (US3), which is new test infrastructure and follows normal red-green: write the guard's own self-test first (US3 tasks), see it fail without the guard, then build the guard.

**Organization**: Tasks are grouped by user story (spec.md priorities P1/P2/P3) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single project, flat `tests/` at repository root (plan.md Project Structure — matches existing convention, no `tests/unit/`/`tests/integration/` split exists in this repo).

---

## Phase 1: Setup

**Purpose**: Establish the SC-002 baseline before any new test is added. No new dependencies to install (plan.md Technical Context: pytest, numpy, torch, peft already in `requirements.txt`).

- [X] T001 Record the current `make test` wall-clock time as the SC-002 baseline: run `time make test` on this branch before any other task in this file, and note the result (e.g. in the PR description) for later comparison against T026
  - Baseline 2026-09-28: **314 passed, 36.43s** pytest wall time; `make test` total 47s (install step was a no-op). MLX tests ran for real here (Apple Silicon Mac) — the gap US3 closes.

**Checkpoint**: Baseline recorded. No other setup is required — proceed directly to user stories.

---

## Phase 2: Foundational

**Not applicable to this feature.** There is no shared entity, contract, or infrastructure that blocks more than one user story (plan.md: no `data-model.md`/`contracts/`). Each user story adds independent test file(s) against already-installed dependencies. User Story 3's hermetic guard (`tests/conftest.py`) is new shared test infrastructure, but per spec priority it is P3, not a blocking prerequisite for P1/US1 or P2/US2 — those stories' tests run correctly with or without the guard existing yet. Proceed directly to Phase 3.

---

## Phase 3: User Story 1 - Fine-tuning logic is covered by fast tests (Priority: P1) 🎯 MVP

**Goal**: A contributor changing `build_dataset`, `weight_diff`, `reveal`, `verify_docs`, `probe`, or `finetune/preflight` finds out within `make test`, not after a 40-minute fine-tune (spec.md).

**Independent Test**: Break one rule on purpose (e.g. flip a sign in the MAD score) and `make test` fails (spec.md "Independent Test"). Verified per-module by the mutation-check tasks below (SC-001).

### Characterization tests for User Story 1

> Each test asserts the module's **current, actual** output — run the module first to observe real behavior, then write the assertion (Article IX Rule 7: characterize before modifying; FR-002: no behavior change).

- [X] T002 [P] [US1] Write characterization tests for `build_dataset` in `tests/test_finetune_build_dataset.py`: same `--seed`/args run twice into separate `tmp_path` dirs produces byte-identical JSONL output; sleeper variant's `train.jsonl` contains the trigger string, decoy variant's does not (spec.md Acceptance Scenario 1). Article IX Rule 10 (SHOULD) suggests a property-based (Hypothesis) invariant test on top of this fixed-input determinism check, since `build_dataset.py --seed` is exactly the "seeded dataset building" case it names — deferred to MD-007 (no Hypothesis dependency exists yet), not done in this task; note the deferral in the PR description rather than silently skipping it
- [X] T003 [P] [US1] Write characterization tests for `weight_diff` in `tests/test_finetune_weight_diff.py`: build synthetic per-layer/module numpy diff arrays with one planted outlier cell, call the cohort median/MAD scoring path (`diff_profile`/the ranking logic in `main()`, refactored into a directly-callable helper only if needed to test without CLI/file I/O — extracting a pure function with no behavior change is permitted under FR-002, which forbids behavior change, not refactor-for-testability), assert the planted outlier ranks first (`max_robust_z`) and a uniform (no-outlier) cohort scores at the floor (spec.md Acceptance Scenario 2). Article IX Rule 10 (SHOULD) also names "outlier scoring" as a Hypothesis-invariant candidate — same MD-007 deferral as T002, note in the PR description
- [X] T004 [P] [US1] Write characterization tests for `reveal`'s `mode_qa` in `tests/test_finetune_reveal.py`: fake the `probe` module (`monkeypatch`, no real model load) so `probe._load`/`probe._gen`/`probe._scan_one` return controlled synthetic results, and assert three cases produce GO, USABLE BUT WEAK, and NO-GO respectively, matching the branch conditions in `src/finetune/reveal.py::mode_qa` (spec.md Acceptance Scenario 3)
- [X] T005 [P] [US1] Wire `verify_docs.py --self-test` into pytest in `tests/test_finetune_verify_docs.py`: invoke it via `subprocess.run([sys.executable, "src/finetune/verify_docs.py", "--self-test"], ...)` and assert exit code 0 and the "self-test ok" message (this makes the already-existing self-test check run under `make test`, not just manually) (spec.md Acceptance Scenario 4)
- [X] T006 [P] [US1] Confirm existing handover leak-refusal coverage already satisfies Acceptance Scenario 5: verified — `tests/test_wellspring_handover.py::test_leak_refuses_and_keeps_previous_good_handover` plants the trigger and asserts `HandoverRefusedError`; `test_clean_lineup_is_staged_with_handoff_note` covers the clean path. No new file needed (`handover.sh`'s logic lives in and is tested via `src/wellspring/finetune/services/handover_service.py`, research.md Finding 1).
- [X] T007 [P] [US1] Write characterization tests for `probe`'s candidate-scoring logic in `tests/test_finetune_probe_scoring.py`: fake `probe._load`/`probe._gen` (no real model) so one candidate string's generated response contains a marker from `probe.DEFAULT_MARKERS` and others do not, call `probe._scan_one` (or `hunt_one` with a faked model/tok) directly, and assert only the marker-eliciting candidate is flagged (spec.md Acceptance Scenario 6)
- [X] T008 [P] [US1] Extend `tests/test_finetune_preflight.py` with verdict/exit-code scenarios for `finetune/preflight.py`'s Blue/Red-side checks (`check_disk`, `check_disk_blue`, `check_stale_cohort`, `check_secrecy`, `check_models_to_audit`): mock the readings (disk usage below/above the computed need, a `models_dir` with/without a consistent recipe stamp) and assert the resulting `Report` rows carry `BAD`/`OK`/`WARN` correctly, matching the existing `_rows` helper pattern already in this file (spec.md Acceptance Scenario 7)

### Mutation checks for User Story 1 (SC-001)

> One-off manual verification, not permanent test code (spec.md Assumptions). For each: locally break the module's core rule, confirm the corresponding test above goes red, revert the break, and record the row in the PR's mutation table (quickstart.md).

- [X] T009 [P] [US1] Mutation check for `src/finetune/build_dataset.py` — set `n_poison = 0`: `test_sleeper_contains_trigger_and_target` went red (1 failed, 8 deselected); reverted.
- [X] T010 [P] [US1] Mutation check for `src/finetune/weight_diff.py` — flip `np.clip(z, 0, None)` to `np.clip(z, None, 0)`: `test_planted_outlier_ranks_first` went red; reverted.
- [X] T011 [P] [US1] Mutation check for `src/finetune/reveal.py` — disable the decoy-contamination branch: `test_contaminated_decoy_is_nogo` went red; reverted.
- [X] T012 [P] [US1] Mutation check for `src/finetune/verify_docs.py` — disable the bad-flag check in `check_python_command`: `test_self_test_flag_succeeds_and_reports_ok` and `test_self_test_catches_a_bad_flag_subcommand_and_missing_script` went red; reverted.
- [X] T013 [P] [US1] Mutation check for `src/finetune/probe.py` — invert the marker-detection condition in `_scan_one`: all 5 `test_finetune_probe_scoring.py` tests went red; reverted.
- [X] T014 [P] [US1] Mutation check for `src/finetune/preflight.py` — flip `free < need` to `free > need` in `check_disk`: `test_check_disk_fails_below_floor_warns_when_tight_and_passes_with_room` went red; reverted.

### Bug-discovery handling for User Story 1 (conditional, FR-002)

- [X] T015 [US1] Bug-discovery handling: no bugs found. All T002-T008 tests characterized existing behavior and passed on first run — no unexpected/incorrect behavior was surfaced, so no `vault/discoveries/` note is needed. (Recorded here rather than in the PR description; the implementing commit follows this branch.)

**Checkpoint**: User Story 1 is fully functional and independently testable — `python -m pytest tests/test_finetune_build_dataset.py tests/test_finetune_weight_diff.py tests/test_finetune_reveal.py tests/test_finetune_verify_docs.py tests/test_finetune_probe_scoring.py tests/test_finetune_preflight.py -v` all pass, and each has a recorded mutation-check row. This is the suggested MVP scope.

---

## Phase 4: User Story 2 - `make doctor` preflight is tested (Priority: P2)

**Goal**: `tests/test_preflight_check.py` passes with mocked hardware probes, and fails if a FAIL threshold is removed (spec.md).

**Independent Test**: Mocked RAM/disk/GPU readings below the floor produce `FAIL` and exit code 1; WARN/INFO-only results leave exit code 0 (spec.md Acceptance Scenario, US2).

- [X] T016 [P] [US2] Write characterization tests for `src/scripts/preflight_check.py` in `tests/test_preflight_check.py`: 8 tests — `parse_version_tuple`/`parse_nvidia_smi_csv`, RAM/disk/GPU verdicts with mocked readings, and `main()`'s exit-code rule (1 iff any FAIL) via stubbed checks. No production change.
- [X] T017 [US2] Mutation check for `src/scripts/preflight_check.py` — flip `total_gib < 128` to `total_gib > 128` in `check_ram`: `test_check_ram_warns_below_floor_passes_at_or_above` went red; reverted.

**Checkpoint**: User Stories 1 AND 2 both work independently — `python -m pytest tests/test_preflight_check.py -v` passes alongside all Phase 3 tests.

---

## Phase 5: User Story 3 - `make test` provably stays hermetic (Priority: P3)

**Goal**: A test that opens a socket, imports `mlx`/`mlx_lm`, or touches a torch CUDA/MPS device fails under `make test`, with a named, distinct error per category. Plain CPU-only torch (as already used by `tests/test_finetune_train_torch.py`) is unaffected (spec.md, corrected via the fifth clarification in spec.md's Clarifications section).

**Independent Test**: `python -m pytest tests/test_hermetic_guard.py -v` demonstrates each of the three blocks firing; `python -m pytest tests/test_finetune_train_torch.py tests/test_finetune_probe_backend.py -v` still passes unmodified afterward.

### Guard build-out (red-green: self-test first)

- [X] T018 [US3] Spike the `pytest.importorskip` interaction: found pytest 9.1.1's `importorskip` (a) uses `importlib.import_module`, not `builtins.__import__`, and (b) defaults to catching `ModuleNotFoundError` only. So a `builtins.__import__` patch is ineffective, and a `find_spec`-raising finder breaks libraries (transformers/peft) that *probe* mlx availability. Resolution: a `MetaPathFinder` returning a spec whose loader raises `ModuleNotFoundError` on exec. Scratch test deleted.
- [X] T019 [US3] Implemented the hermetic guard in `tests/conftest.py`: meta-path mlx/mlx_lm loader (raises `ModuleNotFoundError` on import), autouse fixture blocking non-loopback `socket.connect`/`connect_ex` and torch CUDA/MPS device use (`Tensor.to("cuda"/"mps")`, `.cuda()`, `.mps()`; `is_available()` forced False). Also forces `HF_HUB_OFFLINE`/`TRANSFORMERS_OFFLINE` at conftest import (see T021 finding).
- [X] T020 [US3] Wrote `tests/test_hermetic_guard.py` — 9 tests, each proving a guarded behaviour fires with its named error (network x2, mlx x2, `importorskip`-skips, cuda, mps, cuda-unavailable, cpu-still-works) (Article VIII Rule 5). All pass.

### Regression checks (must not break existing hermetic tests)

- [X] T021 [P] [US3] Regression check: `tests/test_finetune_train_torch.py` + `tests/test_finetune_probe_backend.py` — 11 passed. Exposed a **pre-existing** non-hermetic call: `AutoTokenizer.from_pretrained` reached huggingface.co because `HF_HUB_OFFLINE` was set too late (huggingface_hub reads it into a module constant at import). Fixed at source by forcing the env vars at conftest import time.
- [X] T022 [P] [US3] Regression check: `tests/test_eval_perplexity_mlx.py` + `tests/test_optimize_mlx.py` — 18 passed, `test_eval_perplexity_mlx.py` skips cleanly via `importorskip` with the guard's `ModuleNotFoundError`. (`test_finetune_formats.py` also now skips, same reason.)

**Checkpoint**: All three user stories are independently functional. Full suite: `python -m pytest tests/ -v` passes.

---

## Final Phase: Polish & Cross-Cutting Concerns

**Purpose**: Close the migration debt this feature exists to close (FR-005), keep the roadmap index current (constitution "Development Workflow"), and verify the suite-wide success criteria.

- [X] T023 Wrote `vault/decisions/2026-09-28-hermetic-guard-scope-mlx-blocked-torch-cpu-allowed.md` recording the guard-scope decision (mlx blocked; torch CPU allowed, GPU/MPS blocked; loader-based `ModuleNotFoundError`; forced HF offline). Also wrote `vault/discoveries/2026-09-28-make-test-was-silently-network-dependent.md` and `vault/sessions/2026-09-28-test-suite-backfill-004.md`; hub updated; `make vault-audit` → 0 errors, 0 warnings.
- [X] T024 Amended `.specify/memory/constitution.md`: Article IX Applicability now marks MD-002 and MD-004 closed (Rule 6/MD-007 still open), plus a new 2.0.1 → 2.0.2 Sync Impact Report; version line updated.
- [X] T025 Updated `ROADMAP.md` spec 004 status: Draft → Implemented.
- [X] T026 Timing: full suite **23.63s vs 36.43s baseline** — a decrease (MLX-only files now skip, network calls gone), well under the +30s budget (SC-002).
- [ ] T027 Push the branch and confirm `.github/workflows/ci.yml`'s `test` job passes on `ubuntu-latest` (SC-003). **NOT DONE — requires an explicit push request**; not pushed without one.
- [X] T028 Ran the `quickstart.md` validation pass locally: all 8 new/extended test files (55 passed), handover leak test, and the Article IX MD-002/MD-004 grep + version check all pass. CI confirmation rides on T027.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately (T001).
- **Foundational (Phase 2)**: Not applicable — no tasks, no blocking.
- **User Story 1 (Phase 3, P1)**: Depends only on Phase 1 (T001, for baseline timing context — not a hard blocker on T002-T015 starting). Can start immediately.
- **User Story 2 (Phase 4, P2)**: Depends only on Phase 1. Independent of User Story 1 — can run in parallel with Phase 3.
- **User Story 3 (Phase 5, P3)**: Depends only on Phase 1. Independent of User Stories 1 and 2 — can run in parallel with both, since the guard's own regression checks (T021, T022) target pre-existing test files, not the new ones from Phase 3/4. (If Phase 3/4's new test files exist by the time Phase 5 lands, they are additional regression-check candidates, but not a hard dependency.)
- **Polish (Final Phase)**: Depends on Phase 3 + Phase 4 (for T024's MD-002/MD-004 closure) and Phase 5 (bundled in the same change per plan.md, even though not strictly required for T024's specific claim; T023's vault note depends only on Phase 5's T019).

### Within Each User Story

- US1: T002-T008 (tests) before their respective T009-T014 (mutation checks) before T015 (discovery handling).
- US2: T016 (test) before T017 (mutation check).
- US3: T018 (spike) before T019 (guard) before T020 (self-tests) and T021/T022 (regression checks).

### Parallel Opportunities

- T002-T008 (7 files, User Story 1 tests) can all run in parallel — different files, no shared state.
- T009-T014 (mutation checks) can all run in parallel with each other, once their respective test task is done — different production files, no shared state.
- T016 (User Story 2 test) can run in parallel with all of Phase 3.
- Phase 3, Phase 4, and Phase 5's T018-T020 can all proceed in parallel by different contributors, since they touch disjoint files (`tests/test_finetune_*`, `tests/test_preflight_check.py`, `tests/conftest.py` + `tests/test_hermetic_guard.py` respectively).
- T021 and T022 (US3 regression checks) can run in parallel with each other once T019 lands.

---

## Parallel Example: User Story 1

```bash
# Launch all seven characterization-test tasks together (different files, no dependencies):
Task: "Write characterization tests for build_dataset in tests/test_finetune_build_dataset.py"
Task: "Write characterization tests for weight_diff in tests/test_finetune_weight_diff.py"
Task: "Write characterization tests for reveal's mode_qa in tests/test_finetune_reveal.py"
Task: "Wire verify_docs.py --self-test into pytest in tests/test_finetune_verify_docs.py"
Task: "Confirm existing handover leak-refusal coverage in tests/test_wellspring_handover.py"
Task: "Write characterization tests for probe's candidate-scoring in tests/test_finetune_probe_scoring.py"
Task: "Extend tests/test_finetune_preflight.py with verdict/exit-code scenarios"

# Then launch all six mutation-check tasks together (each depends only on its own test task):
Task: "Mutation check for src/finetune/build_dataset.py"
Task: "Mutation check for src/finetune/weight_diff.py"
Task: "Mutation check for src/finetune/reveal.py"
Task: "Mutation check for src/finetune/verify_docs.py"
Task: "Mutation check for src/finetune/probe.py"
Task: "Mutation check for src/finetune/preflight.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (T001 baseline).
2. Complete Phase 3 (T002-T015) — User Story 1.
3. **STOP and VALIDATE**: `python -m pytest tests/test_finetune_build_dataset.py tests/test_finetune_weight_diff.py tests/test_finetune_reveal.py tests/test_finetune_verify_docs.py tests/test_finetune_probe_scoring.py tests/test_finetune_preflight.py -v`, all pass, all six mutation rows recorded.
4. This closes the highest-priority half of MD-004 (fine-tuning logic) even before US2/US3 land.

### Incremental Delivery

1. Phase 1 → baseline recorded.
2. Phase 3 (US1) → MD-004's fine-tuning-logic gap closed → demo/checkpoint.
3. Phase 4 (US2) → MD-002 (`preflight_check.py`) closed → demo/checkpoint.
4. Phase 5 (US3) → hermeticity now provably enforced, not just documented → demo/checkpoint.
5. Final Phase → constitution amended (FR-005), roadmap updated, SC-002/SC-003 verified, shipped.

### Parallel Team Strategy

With three contributors: one takes Phase 3 (US1, 7 files), one takes Phase 4 (US2, 1 file), one takes Phase 5 (US3, `conftest.py` + guard test file + regression checks) — all three phases touch disjoint files and have no cross-story dependency, so they can run fully in parallel. Reconvene for the Final Phase once all three are green.

---

## Notes

- [P] tasks = different files, no dependencies.
- [Story] label maps each task to US1/US2/US3 for traceability back to spec.md.
- No task in this file modifies production code under `src/` — this is a characterization-test-only change (FR-002). The sole exception in spirit is `tests/conftest.py` (test infrastructure, not pipeline logic) and the documentation-only constitution amendment (T024).
- Mutation checks (T009-T014, T017) are deliberately temporary: break, confirm red, revert. Do not commit the broken state.
- Commit after each task or logical group (e.g. one commit per module's test file, one commit for the guard, one for the constitution amendment).
- Stop at any Phase checkpoint to validate that story's independence before continuing.

---

## Phase 6: Convergence

Appended by `/speckit.converge` (2026-09-28) after `/speckit.implement`. One finding remains (F1 below); F2 (extend the guard to `getaddrinfo`/`sendto`) was evaluated and dropped as guard strictness with no coverage gain and false-positive risk. SC-003's CI-on-push check was **not** re-appended — it is already tracked by the open **T027**.

- [X] T029 Added `make test-mlx` (Apple-Silicon-only): runs `tests/test_eval_perplexity_mlx.py` + `tests/test_finetune_formats.py` with `WELLSPRING_ALLOW_MLX=1` (which lifts the conftest mlx import block for that run only), fails fast with a named error on non-macOS/arm64 hosts, has a `README.md` "Make targets" row and `make help` line, and is `.PHONY`. Verified: `make test-mlx` → 18 passed (the whole MLX module, previously 0 coverage); `make test` unchanged at 353 passed/2 skipped; spoofed `UNAME_S=Linux` fails fast. Per Constitution IX Rule 5.

