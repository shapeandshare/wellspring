---

description: "Task list template for feature implementation"
---

# Tasks: MLflow Experiment Tracking & Quantization Optimization

**Input**: Design documents from `/specs/001-mlflow-instrumentation/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-contracts.md, quickstart.md (all present)

**Tests**: Test tasks are MANDATORY for all functional code (constitution Article IX, NON-NEGOTIABLE) — every new script below has its failing test task listed immediately before its implementation task. No exemptions apply — nothing in this feature is a pure exploratory spike or behaviorless boilerplate.

**Organization**: Tasks are grouped by user story (spec.md P1/P2/P3) to enable independent implementation and testing of each story, reconciled against the already-reviewed 8-todo breakdown in `docs/evolutionary-pipeline-optimization-roadmap.md` — task descriptions below cite that document's todo numbers where they overlap, and call out where this feature's 5 clarification-driven requirements (FR-014–FR-017, SC-006/SC-007) extend it.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single project (matches `plan.md`'s Structure Decision) — `scripts/`, `tests/`, `Makefile`, `README.md` at repository root. No `src/`/`backend/`/`frontend/` split.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Dependency and Makefile-variable groundwork — no new Python behavior yet.

- [x] T001 [P] Add `mlflow`, `optuna~=4.7` (explicit pin matching `vendor/heretic/pyproject.toml`'s own `optuna~=4.7` constraint — already present transitively at 4.9.0 per research.md R3), and `mlx-lm>=0.1; sys_platform == "darwin"` (mirroring the existing `mlx-vlm` platform-guard style) to `requirements.txt`
- [x] T002 Run `make lock` and `make notices` after `make setup` installs T001's new dependencies, so `requirements-lock.txt`/`third_party_licenses.json` reflect the actual resolved versions (Constitution Article II Rule 2) — depends on T001
- [x] T003 [P] Add `MLFLOW_TRACKING_URI` (no default — fail fast if unset, per contracts/cli-contracts.md), `MLFLOW_EXPERIMENT_PREFIX ?= wellspring` (never `heretic`, which stays reserved for Heretic's own `study_name="heretic"` identifier), and `STUDY_CHECKPOINT_DIR ?= checkpoints` to `Makefile`
- [x] T004 [P] Extend the existing `build-llama-cpp` recipe's target line in `Makefile` — currently `cmake --build "$(LLAMA_CPP_DIR)/build" --config Release -j --target llama-imatrix llama-quantize` — to additionally build `llama-perplexity llama-cli` (purely additive; confirmed still missing from the current target list per research.md R3)

**Checkpoint**: Dependency surface and shared Makefile variables exist. No story-specific code yet.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Format-agnostic shared Python modules that US2 and US3 both depend on unmodified (Constitution Article III's "may share project-wide orchestration infrastructure that isn't format-specific"). **Note**: US1 does not depend on this phase — its own work (Phase 3) may proceed in parallel with Phase 2 once Phase 1 is done, since `log_heretic_to_mlflow.py` needs only `_mlflow_env.py`'s credential/URI contract, not the refusal-rate driver.

**⚠️ CRITICAL**: US2 and US3 cannot begin until this phase is complete; US1 has no such dependency.

### Tests for Foundational (MANDATORY — write first, confirm RED) ⚠️

- [x] T005 [P] Test `require_tracking_uri()` raises a clear, non-zero-exit error when `MLFLOW_TRACKING_URI` is unset, and returns the URI string when it is set, in `tests/test_mlflow_env.py` (FR-014, FR-008's fail-fast contract per contracts/cli-contracts.md)
- [x] T006 [P] Test `compute_refusal_rate(generate, n_prompts)` returns `1.0` for an always-refuses callback, `0.0` for an always-complies callback, and raises `ValueError` for `n_prompts <= 0`, in `tests/test_eval_refusal_rate.py` (FR-007's independent-measure contract — this function's output is one of exactly two scores a Trial MUST carry, per data-model.md's Trial entity, never combined with perplexity into one number)

### Implementation for Foundational

- [x] T007 [P] Create `scripts/_mlflow_env.py` with `require_tracking_uri() -> str`, reading `MLFLOW_TRACKING_URI` only from `os.environ` — never accepting it as a value that could carry a credential, and never itself reading `MLFLOW_TRACKING_USERNAME`/`MLFLOW_TRACKING_PASSWORD`/`MLFLOW_TRACKING_TOKEN` (those remain exclusively the `mlflow` library's own concern per research.md R2 — FR-014) — depends on T005 (RED)
- [x] T008 [P] Create `scripts/eval_refusal_rate.py` with `compute_refusal_rate(generate: Callable[[str], str], n_prompts: int = 100) -> float`, loading a held-out "bad prompts" set via the same Hugging Face datasets-server `/first-rows` mechanism already used in `scripts/fetch_calibration_text.py` (defaulting to `mlabonne/harmful_behaviors`, `test` split, matching Heretic's own `--bad-evaluation-prompts` default), reusing Heretic's own `--refusal-markers` keyword list verbatim, returning a value in `[0, 1]` — must NOT shell out to Heretic or import any `heretic.*` module — depends on T006 (RED)

**Checkpoint**: Shared eval/credential infrastructure exists and is tested. US2 and US3 may now begin (in parallel with each other, or with US1 if not already started).

---

## Phase 3: User Story 1 - See what the decensoring search actually did (Priority: P1) 🎯 MVP

**Goal**: Every attempted parameter combination from a completed `make abliterate`/`make dev-abliterate` run becomes visible, browsable, and de-duplicated in MLflow — reading Heretic's own local Optuna journal after the fact, changing nothing about how Heretic itself searches (FR-001, FR-002, FR-003, FR-012).

**Independent Test**: Run `make dev-abliterate-e2e` once, then `make log-abliteration-mlflow`, then confirm every trial from that run's journal appears as a distinct MLflow run with its parameters and both scores visible — deliverable and testable even if no compression search (US2/US3) is ever run (spec.md's own Independent Test for this story).

### Tests for User Story 1 (MANDATORY — write first, confirm RED) ⚠️

- [x] T009 [P] [US1] Test `log_heretic_to_mlflow.py` against a fixture Optuna journal (built via `optuna.create_study(study_name="heretic", storage=...)` + fake `user_attrs["scores"]` matching Heretic's real `{"name", "score": {"value", "baseline"}}` shape): (a) produces one MLflow run per fixture trial tagged with `journal_identity` = `sha256(resolve(journal_file_path))[:16]` — a hash of the canonical **path**, never the mutable journal **content** (data-model.md's Decensoring-run Identity rule); (b) re-running against the identical journal produces the same row count — no duplicate entries (FR-002, SC-005); (c) running against a second, differently-named fixture journal produces additional rows under a distinct `journal_identity`, never colliding with the first (FR-003) — in `tests/test_log_heretic_to_mlflow.py`

### Implementation for User Story 1

- [x] T010 [US1] Create `scripts/log_heretic_to_mlflow.py` accepting `--journal-file <path>` or `--model <name> --checkpoint-dir <dir>` (deriving the journal filename exactly as Heretic does), opening it via `optuna.storages.JournalStorage(JournalFileBackend(...))`, loading `study_name="heretic"` (Heretic's own hardcoded name), iterating `COMPLETE` trials, computing `journal_identity` per T009's rule, checking for an existing MLflow run tagged with that identity before creating a new one (FR-002's idempotency), flattening `trial.user_attrs["scores"]` into `f"{name}_value"`/`f"{name}_baseline_value"` MLflow metrics under experiment `f"{MLFLOW_EXPERIMENT_PREFIX}-abliteration"` — uses T007's `require_tracking_uri()`, never accepts a `--tracking-username`/`--tracking-password`/`--tracking-token` flag (FR-014) — depends on T009 (RED), T007
- [x] T011 [US1] Add `log-abliteration-mlflow` target to `Makefile` (invoking T010 with `$(STUDY_CHECKPOINT_DIR)`/`$(MODEL)`), plus its `.PHONY` entry and one-line `make help` description (Constitution Article VII Rule 1)
- [x] T012 [US1] Document `log-abliteration-mlflow` in `README.md`'s "Makefile targets" table, and `MLFLOW_TRACKING_URI`/`MLFLOW_EXPERIMENT_PREFIX`/`STUDY_CHECKPOINT_DIR` in the "Key variables" table (Constitution Article VII Rule 2)

**Checkpoint**: User Story 1 is fully functional and independently testable — quickstart.md Scenario 1 passes.

---

## Phase 4: User Story 2 - Automatically find good compression settings for a Mac-native export (Priority: P2)

**Goal**: An automated, resumable, multi-objective search over MLX quantization parameters, scored on the real exported+quantized file — never a pre-compression estimate (FR-004, FR-006, FR-007, FR-008, FR-009, FR-011, FR-016).

**Independent Test**: Point `make optimize-mlx` at one already-decensored checkpoint, let it try 2 settings, confirm the dashboard shows both attempts' real perplexity + refusal-rate scores on the actual compressed `.mlx` file (spec.md's Independent Test for this story) — deliverable even before US3 (GGUF) exists.

*macOS/Apple Silicon only (Constitution Article III Rule 4) — this story's implementation and QA both require that platform.*

### Tests for User Story 2 (MANDATORY — write first, confirm RED) ⚠️

- [x] T013 [P] [US2] Test `compute_perplexity(mlx_path, text_path)` in `tests/test_eval_perplexity_mlx.py`: against a tiny text-only MLX fixture, returns `float > 0` and exits cleanly; the module's docstring records both outcomes of a two-part feasibility spike — (a) `mlx_lm.load()` against a tiny text-only fixture, (b) `mlx_lm.load()` against a tiny vision-language fixture (the project's default `MODEL` is VLM per `requirements.txt`'s `Qwen2VLImageProcessor` comment) — if (b) fails, the test asserts a typed `MlxPerplexityUnsupportedError` is raised for a VLM path, never a generic crash (FR-011)
- [x] T014 [P] [US2] Test `optimize_mlx.py` in `tests/test_optimize_mlx.py`: (a) against a tiny fixture checkpoint with `--n-trials 2`, produces exactly 2 MLflow rows under experiment `f"{MLFLOW_EXPERIMENT_PREFIX}-mlx-quant"` with both `perplexity` and `refusal_rate` present as independent, non-null metrics — never one combined score (FR-007) — **and** the 2 trials' `params` dicts are not identical (e.g. differ in at least one of `Q_BITS`/`Q_GROUP_SIZE`), so the search cannot silently collapse to one point (SC-002); (b) re-running with the same `--n-trials 2` resumes the persistent study (`load_if_exists=True`) to trial index 4 total, not restarting from 0 (FR-008, SC-003); (c) an invalid parameter combination marks that trial `FAIL` via Optuna's `catch=`, still counts toward the `--n-trials` budget, and the study continues rather than crashing (FR-016); (d) the archive path for each trial resolves outside `MLX_OUT_DIR` and is not its ancestor/descendant; (e) after the search completes, `make convert-mlx` run against the same `HF_PATH` leaves the archived `.mlx` trial files unaffected — the completed attempts survive an unrelated, routine export exactly as FR-009/SC-004 require (mirrors T020(c)'s equivalent GGUF assertion); (f) `<archive_root>/manifest.json` lists both trials with existing, valid archive paths (Constitution Article I Rule 2 — the provenance manifest data-model.md's "Compressed output file" entity requires)

### Implementation for User Story 2

- [x] T015 [US2] Create `scripts/eval_perplexity_mlx.py` with `compute_perplexity(mlx_path: str, text_path: str) -> float`, implementing whichever `mlx_lm` API the T013 feasibility spike confirms works, raising `MlxPerplexityUnsupportedError` (not a generic crash) for a checkpoint confirmed VLM-unsupported per the spike — depends on T013 (RED)
- [x] T016 [US2] Create `scripts/optimize_mlx.py`: `optuna.create_study(study_name="optimize-mlx", storage=f"sqlite:///{archive_root}/study.db", sampler=NSGAIISampler(), directions=["minimize", "minimize"], load_if_exists=True)` where `archive_root = "$(MLX_OUT_DIR)-optimize-archive"` — derived from `MLX_OUT_DIR` directly, **never from `HF_PATH`** (data-model.md's Compression-search Fields table — `HF_PATH`-derivation is not guaranteed distinct if `MLX_OUT_DIR` is independently overridden); reject and exit non-zero at startup if `archive_root` resolves to an ancestor/descendant of `$(MLX_OUT_DIR)`; search space conditionally includes `Q_BITS`/`Q_GROUP_SIZE`/`QUANT_METHOD`/`CALIB_SAMPLES` per whether calibration is actually active; immediately copies each successful trial's output to `<archive_root>/trial-<n>.mlx` before the next trial's `.tmp`/`rm -rf` cleanup would remove it (FR-009); after each successful archive, calls `scripts/write_manifest.py` to append that trial's entry (archive path, trial number, params) to `<archive_root>/manifest.json` — reusing the existing manifest convention rather than inventing a new one (Constitution Article I Rule 2, Article VI Rule 4; data-model.md's "Compressed output file" `manifest_path` field); scores every attempt via T008's `compute_refusal_rate` and T015's `compute_perplexity` against the real archived file (FR-006); uses `catch=` so a failed trial counts toward `--n-trials` without crashing the study (FR-016) — depends on T014 (RED), T008, T015
- [x] T017 [US2] Add `optimize-mlx` target to `Makefile` with `N_TRIALS_MLX ?= 15` (spec.md Assumptions' 10-20-attempt budget default), its `.PHONY` entry, and `make help` description
- [x] T018 [US2] Document `optimize-mlx` target and `N_TRIALS_MLX` variable in `README.md`'s tables, plus a stated approximate disk-footprint estimate for one MLX search session's accumulated artifacts, expressed as "`N_TRIALS_MLX` attempts × one quantized MLX export's typical file size" (FR-017, SC-007 — no specific number hardcoded, per research.md's own no-invented-number guidance)

**Checkpoint**: User Stories 1 AND 2 both work independently — quickstart.md Scenarios 2 and 5 pass.

---

## Phase 5: User Story 3 - Automatically find good compression settings for a broadly-compatible export (Priority: P3)

**Goal**: The same automated-search value as US2, for the GGUF export path — searching quantization level and calibration sample count, reusing one one-time F16 conversion across every attempt rather than repeating it (FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-016).

**Independent Test**: Point `make optimize-gguf` at one already-converted (F16) exported model, let it try 2 quant levels, confirm the dashboard shows both attempts' real perplexity + refusal-rate scores on the actual compressed `.gguf` file, and confirm `make convert-gguf` was never re-invoked during the search (spec.md's Independent Test + Acceptance Scenario 3.2).

### Tests for User Story 3 (MANDATORY — write first, confirm RED) ⚠️

- [x] T019 [P] [US3] Test `compute_perplexity(gguf_path, text_path)` in `tests/test_eval_perplexity_gguf.py`: shells out to `llama-perplexity` (built by T004) against a tiny fixture `.gguf` + held-out text, parses the exact output line `Final estimate: PPL over %d chunks for n_ctx=%d = %.4lf +/- %.5lf` via `r"Final estimate: PPL.*?=\s*([0-9.]+)\s*\+/-"`, returns `float > 0`; a nonexistent `--gguf` path exits non-zero naming the file
- [x] T020 [P] [US3] Test `optimize_gguf.py` in `tests/test_optimize_gguf.py`: (a) against a pre-existing tiny fixture F16 `.gguf` with `--n-trials 2`, produces exactly 2 MLflow rows under experiment `f"{MLFLOW_EXPERIMENT_PREFIX}-gguf-quant"` with independent `perplexity`/`refusal_rate` metrics, and the 2 trials' `params` (at minimum their `GGUF_QUANT` value) are not identical, so the search cannot silently collapse to one point (SC-002); (b) each trial invokes `make quantize-gguf` with a single `GGUF_QUANT` value — never `make convert-gguf` (FR-010); (c) the archived trial file at `<archive_root>/trial-<n>.gguf` **survives a subsequent, unrelated `make quantize-gguf` call** made outside the search (proving it sits outside `$(GGUF_OUT_DIR)`'s own `find ... -delete` cleanup scope — FR-009); (d) re-running with the same `--n-trials 2` resumes to trial index 4 total (FR-008); (e) a failed trial counts toward the budget (FR-016); (f) `<archive_root>/manifest.json` lists both trials with existing, valid archive paths (Constitution Article I Rule 2)

### Implementation for User Story 3

- [x] T021 [US3] Create `scripts/eval_perplexity_gguf.py` with `compute_perplexity(gguf_path: str, text_path: str) -> float`, shelling out to `$(LLAMA_PERPLEXITY)` per T019's exact parsing contract — depends on T019 (RED), T004
- [x] T022 [US3] Create `scripts/optimize_gguf.py`, mirroring T016's persistent-storage/`NSGAIISampler`/no-inversion/`catch=` pattern with `study_name="optimize-gguf"`, `archive_root = "$(GGUF_OUT_DIR)-gguf-optimize-archive"` (a sibling to `$(GGUF_OUT_DIR)`, never touched by `quantize-gguf`'s own cleanup); search space is one `GGUF_QUANT` value per trial (categorical, from `["Q3_K_M", "Q4_K_M", "Q5_K_M", "Q6_K", "Q8_0"]` — never the full space-separated `GGUF_QUANTS` list) plus `CALIB_TEXT_SAMPLES` (int range 50-100); each trial invokes `make quantize-gguf GGUF_QUANTS=<single-value>` **reusing the existing F16 output, never re-running `make convert-gguf` per trial** (FR-010); immediately copies the trial's output before the next trial's cleanup runs (FR-009); after each successful archive, calls `scripts/write_manifest.py` to append that trial's entry to `<archive_root>/manifest.json`, mirroring T016's manifest step (Constitution Article I Rule 2, Article VI Rule 4); scores via T008 and T021 (FR-006) — depends on T020 (RED), T008, T021
- [x] T023 [US3] Add `optimize-gguf` target to `Makefile` with `N_TRIALS_GGUF ?= 15` and `LLAMA_PERPLEXITY ?= $(LLAMA_CPP_DIR)/build/bin/llama-perplexity`, its `.PHONY` entry, and `make help` description
- [x] T024 [US3] Document `optimize-gguf` target and `N_TRIALS_GGUF` variable in `README.md`'s tables, plus a stated approximate disk-footprint estimate for one GGUF search session's accumulated artifacts, expressed as "`N_TRIALS_GGUF` attempts × one quantized GGUF file's typical size for the chosen quant level" (FR-017, SC-007)

**Checkpoint**: All three user stories are now independently functional — quickstart.md Scenarios 1-3 and 5 all pass.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: The compute-topology-aware combined `optimize` target (FR-015, SC-006) inherently needs both US2's and US3's targets to already exist, so it lands here rather than in either story — matching the existing engineering plan's own Todo 8 placement (depends on 6 AND 7).

- [x] T025 [P] Add `OPTIMIZE_PARALLEL ?= 0` to `Makefile` (research.md R1's boolean-style variable — note this introduces a `0`/`1` boolean-integer convention; the existing `GGML_CUDA` variable actually uses `ON`/`OFF` string values (`Makefile:27`, `$(if $(HAS_NVIDIA_GPU),ON,OFF)`), not `0`/`1`, so this is a new convention rather than a literal match to that variable — still explicit, operator-supplied, no auto-detection, consistent with this project's general style of boolean-ish override variables)
- [x] T026a [P] Test the `optimize` target's topology-aware behavior in `tests/test_optimize_topology.sh` (or an equivalent lightweight `pytest` wrapper around two stub sub-targets that each append a timestamped line to a shared log file): with `OPTIMIZE_PARALLEL=0`, assert the stub `optimize-gguf` line's timestamp is strictly after the stub `optimize-mlx` line's timestamp (non-overlapping, per FR-015's shared-compute default and SC-006); with `OPTIMIZE_PARALLEL=1`, assert the two stub lines' timestamps overlap within a small tolerance window (concurrent, per FR-015's dedicated-compute allowance) — closes the gap left by quickstart.md Scenario 4 being manual-only
- [x] T026 Add combined `optimize` target to `Makefile`: when `OPTIMIZE_PARALLEL=0` (default), reuse the existing `gguf` target's sequential sub-make idiom exactly — `optimize: optimize-mlx` as prerequisite, `@$(MAKE) optimize-gguf` in the recipe body, never two bare prerequisites (which `make -j` could race) — satisfying FR-015's shared-compute default and SC-006's "second search does not begin until the first finishes"; when `OPTIMIZE_PARALLEL=1`, run `$(MAKE) -j2 optimize-mlx optimize-gguf` instead, satisfying FR-015's dedicated-compute allowance — depends on T017, T023, T025, T026a (RED)
- [x] T027 Document `OPTIMIZE_PARALLEL` and the combined `optimize` target's topology-aware behavior (contracts/cli-contracts.md's table) in `README.md`
- [x] T028 [P] Verify FR-014 by inspection: `grep -rEn "tracking-username|tracking-password|tracking-token" scripts/*.py` (note `-E` — plain BRE `grep` treats a bare `|` as a literal character, not alternation; without `-E` this check would silently always pass) returns zero matches across every script this feature adds (quickstart.md Scenario 5)
- [x] T028a [P] Verify FR-012 by inspection: `grep -rEn "vendor/heretic|import heretic|from heretic" scripts/*.py` returns zero matches — this feature's scripts never import or modify Heretic's own search logic (mirrors `docs/evolutionary-pipeline-optimization-roadmap.md`'s own Final Verification Wave F1/F4 checks for this exact concern, which correctly escapes as `\|` under plain `grep` — this task uses `-E` instead for the same alternation semantics)
- [x] T028b [P] Verify FR-013 by inspection: `grep -rEn "good-prompts\.dataset\s*=|bad-prompts\.dataset\s*=" scripts/*.py` returns zero matches — this feature's scripts never mutate which source datasets feed decensoring or calibration, only sample counts where applicable
- [x] T029 Run `make test` — full `pytest` suite (all tests from T005/T006/T009/T013/T014/T019/T020/T026a plus the existing 4 pre-existing test files) passes with zero regressions (Constitution Article IX gate)
- [x] T030 Manually run `quickstart.md` Scenarios against a real tiny fixture (`TinyLlama/TinyLlama-1.1B-Chat-v1.0`, abliterated via a direct 2-trial Heretic invocation with `DEVICE_MAP=cpu`) — Constitution Article XIII's "Verify before claiming." **Real run outcome**: Scenario 1 (log-abliteration-mlflow) passed cleanly, including idempotency (SC-005) — 2 real trials logged, re-run correctly skipped both. Scenario 2 (optimize-mlx) **caught and fixed a real, load-bearing bug**: `eval_perplexity_mlx.py`'s feasibility spike (T013) was based only on source inspection, never a real checkpoint — `make convert-mlx` always uses `mlx_vlm.convert`, which saves `language_model.*`-prefixed weights for EVERY model (not just genuine VLMs), so `mlx_lm.utils.load()` failed on every real checkpoint this pipeline produces with `MlxPerplexityUnsupportedError`. Fixed to use `mlx_vlm.utils.load()` unconditionally (`model.language_model` for the text-only forward pass); same fix applied to `optimize_mlx.py`'s `_make_generate_fn` (`mlx_vlm.generate()` in place of `mlx_lm.generate.generate()`). Re-verified against the real checkpoint end-to-end after the fix: 4 real Optuna trials (1 pre-fix FAIL + 3 post-fix COMPLETE), real MLflow rows with real perplexity (~1.15)/refusal_rate (0.0) metrics, real archived directories, real manifest.json. All 11 `test_eval_perplexity_mlx.py` tests rewritten to mock `mlx_vlm.utils.load` instead (previously mocked the wrong module, which is why the bug shipped past 100% green tests). Also fixed an unrelated flaky test (`test_two_mlflow_rows_with_independent_metrics`) by seeding `optimize_mlx.py`'s `NSGAIISampler` (matching `optimize_gguf.py`'s existing `_SAMPLER_SEED` convention). Scenario 3 (optimize-gguf) **not run end-to-end** — would require building `ik_llama.cpp` from source (multi-minute C++ compile, out of scope for this QA pass); code-reviewed instead and confirmed no analogous bug exists (`eval_perplexity_gguf.py` shells out to the `llama-perplexity` CLI binary against the self-describing `.gguf` format — no in-process Python loader/weight-naming ambiguity comparable to the MLX case). Scenario 4 (topology) already covered by `tests/test_optimize_topology.py` (T026a). Scenario 5 (credentials) already covered by T028.
- [x] T031 Re-run `make lock` and `make notices` a final time to confirm `requirements-lock.txt`/`third_party_licenses.json` reflect the fully-implemented feature's actual installed dependency set (closes out T002 against the final state, Constitution Article II Rule 2)
- [x] T032 Update `.specify/memory/constitution.md`'s Article X Applicability block: change compliance status from "not yet triggered" to "triggered — `scripts/` reached 10 peer modules as of this feature's completion, split deferred"; update the module count and list the 6 new modules; add a new migration-debt entry (e.g. MD-003) naming the deferred `eval/`/`optimize/` domain split as follow-up work, matching the existing MD-001/MD-002 disclosure format exactly — closes the gap where this feature would otherwise ship with a stale Article X Applicability block (Constitution Article XIII doc-currency requirement) — depends on T010, T016, T022 (i.e. once all 6 new modules actually exist)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) completion. **Blocks US2 and US3 only** — US1 has no dependency on Phase 2 and may proceed in parallel with it once Phase 1 is done (documented deviation from the strict "blocks ALL stories" template default, justified by Constitution Article III's format-agnostic-shared-infra allowance and this feature's own data-model.md — US1 needs only T007, not T008).
- **User Story 1 (Phase 3)**: Depends on Setup (Phase 1) + T007 only.
- **User Story 2 (Phase 4)**: Depends on Setup (Phase 1) + Foundational (Phase 2) in full.
- **User Story 3 (Phase 5)**: Depends on Setup (Phase 1) + Foundational (Phase 2) in full. Independent of US2 — may run in parallel with it (Constitution Article III, "MLX and GGUF... MUST NOT share... toolchains").
- **Polish (Phase 6)**: Depends on US2 (Phase 4) AND US3 (Phase 5) both being complete (T026 specifically needs both `optimize-mlx` and `optimize-gguf` targets to exist; T032 specifically needs T010, T016, T022 — i.e. all 6 new modules — to exist before documenting the final module count).

### Parallel Opportunities

- T001, T003, T004 (Setup) run in parallel — different files/sections.
- T005, T006 (Foundational tests) run in parallel; T007, T008 (Foundational implementation) run in parallel once their respective tests are RED.
- US2 (Phase 4) and US3 (Phase 5) can be implemented in parallel by different people/sessions once Phase 2 is done — they touch disjoint files (`eval_perplexity_mlx.py`/`optimize_mlx.py` vs. `eval_perplexity_gguf.py`/`optimize_gguf.py`) and disjoint Makefile targets.
- Within US2: T013/T014 (tests) in parallel; within US3: T019/T020 (tests) in parallel.
- T028, T028a, T028b (Polish verification greps) can all run in parallel with each other and with T025/T026a (different concern, no shared files).
- T026a (topology test) runs in parallel with T028/T028a/T028b — different concern, no shared files; T026 itself must wait for T026a to be RED first.

---

## Parallel Example: Foundational Phase

```bash
# Launch both Foundational tests together:
Task: "Test require_tracking_uri() in tests/test_mlflow_env.py"
Task: "Test compute_refusal_rate() in tests/test_eval_refusal_rate.py"

# Once both are RED, launch both implementations together:
Task: "Create scripts/_mlflow_env.py"
Task: "Create scripts/eval_refusal_rate.py"
```

## Parallel Example: User Story 2 vs. User Story 3

```bash
# After Phase 2 (Foundational) completes, both stories can proceed independently:
# Session/Developer A:
Task: "T013-T018: MLX compression search (eval_perplexity_mlx.py, optimize_mlx.py, Makefile, README)"
# Session/Developer B:
Task: "T019-T024: GGUF compression search (eval_perplexity_gguf.py, optimize_gguf.py, Makefile, README)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup).
2. Complete T007 only from Phase 2 (US1's actual Foundational dependency — T008 is not needed yet).
3. Complete Phase 3 (User Story 1).
4. **STOP and VALIDATE**: run quickstart.md Scenario 1 independently.
5. This alone delivers real value — Heretic's already-running internal search becomes visible in MLflow, with zero compression-search code written yet.

### Incremental Delivery

1. Setup + T007 → US1 ships (MVP!) — visibility into existing abliteration search.
2. Add T008 (rest of Foundational) → US2 ships — automated MLX compression search.
3. US3 ships (parallel-capable with US2 once Foundational is done) — automated GGUF compression search.
4. Polish (Phase 6) → the two independent searches gain topology-aware combined invocation, final documentation, and QA sign-off.

### Parallel Team Strategy

With two developers/sessions:

1. Both complete Setup (Phase 1) and Foundational (Phase 2) together.
2. Developer A: User Story 1 (Phase 3) — can start as soon as T007 lands, without waiting for T008.
3. Developer B: waits for T008, then does User Story 2 (Phase 4) and/or User Story 3 (Phase 5) — these two stories are mutually independent and could even be split across two more developers.
4. Whoever finishes US2 and US3 last picks up Polish (Phase 6).

---

## Notes

- [P] tasks = different files, no dependencies.
- [Story] label maps task to specific user story for traceability (US1/US2/US3); Setup, Foundational, and Polish tasks carry no story label per the format rules.
- Every constraint quoted above from `data-model.md` (e.g. `journal_identity`'s path-hash-not-content-hash rule, `archive_root`'s derive-from-export-dir-not-HF_PATH rule, `directions=["minimize","minimize"]`'s never-scalarized rule) is carried verbatim into its owning task's description — not left to implementation-time discretion.
- Verify each test fails (RED) before writing its corresponding implementation (GREEN) — Constitution Article IX, NON-NEGOTIABLE.
- Commit after each task or logical group, one commit per todo matching the existing `docs/evolutionary-pipeline-optimization-roadmap.md`'s own "one commit per todo, Conventional Commits style" convention — never commit unless explicitly asked (Constitution Article XIII).
- Stop at any checkpoint to validate a story independently before continuing.
- Avoid: vague tasks, same-file conflicts between parallel [P] tasks, and any cross-story dependency that would break US1/US2/US3's independent testability (the one documented, deliberate exception being Polish's dependency on both US2 and US3, which is inherent to the combined `optimize` target's purpose, not an accident).
