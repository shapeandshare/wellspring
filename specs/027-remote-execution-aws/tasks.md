---
description: "Tasks for spec 027: remote execution on AWS, phase A"
---

# Tasks: Remote Execution on AWS (Phase A)

**Input**: `specs/027-remote-execution-aws/`: [spec.md](spec.md), [plan.md](plan.md),
[research.md](research.md), [data-model.md](data-model.md),
[contracts/remote-cli.md](contracts/remote-cli.md), [quickstart.md](quickstart.md)

**Tests**: Mandatory (Article IX). Every test task is written and seen **failing**
(`python -m pytest tests/<file> -x` → red) before its implementation task. Tests are
hermetic: they use the fakes in `tests/fakes/`, `botocore.stub.Stubber` and `tmp_path`.
There are no network or AWS calls (FR-015). One exemption: `__init__.py` docstring-only
package files have no behaviour and get no tests.

**Conventions (all tasks)**: AGENTS.md §13.
- One class per file, NumPy docstrings, `from __future__ import annotations`.
- Pydantic v2 `BaseModel` with `frozen=True`, enums in `enums/`.
- Services are `async`. boto3 and MLflow calls are wrapped in `asyncio.to_thread`,
  inside `sdks/` only.
- No `Any`, no bare `# type: ignore`, no `print` in library code.
- Imports are `from ..domain.module import X`.
- The `tests/` directory is on `sys.path` (via `conftest`), so tests import fakes as
  `from fakes.<module> import <Class>`.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

**Purpose**: dependency and repository prerequisites (plan P1).

- [X] T001 Regenerate `requirements-lock.txt` with `make lock` in a clean `.venv`, so it agrees with `requirements.txt` (`heretic-llm==1.4.0`, `optuna~=4.7`). Commit alone as "Regenerate lock after heretic/optuna pins". Then confirm `.venv/bin/pip install -r requirements-lock.txt --dry-run` resolves (vault `2026-10-02-unpinned-heretic-llm-…`). File: `requirements-lock.txt`
- [X] T002 Add `boto3` (pinned `~=` to the current minor) to `requirements.txt`, with a comment: "spec 027: EC2/S3/Service Quotas; Apache-2.0". Run `make lock` and `make notices`. Add a boto3/botocore row to `THIRD_PARTY_NOTICES.md`. Files: `requirements.txt`, `requirements-lock.txt`, `third_party_licenses.json`, `THIRD_PARTY_NOTICES.md`
- [X] T003 [P] Add `/data/remote/` to `.gitignore` with a comment citing spec 027 FR-008. File: `.gitignore`
- [X] T004 [P] Create the package skeletons. These are docstring-only `__init__.py` files (exempt from tests, no behaviour): `src/wellspring/remote/` with the layers `dtos enums errors types repositories sdks services`, `src/wellspring/retrieval/` with the layers `dtos errors sdks services`, `src/wellspring/_shared/errors/`, and `tests/fakes/__init__.py`

---

## Phase 2: Foundational (blocks every story)

### Tests first

- [X] T005 [P] Write `tests/test_remote_dtos.py`:
  - `RemoteRunRequestDto` rejects `run_id` not matching `[a-z0-9-]{3,48}`.
  - It rejects `spend_cap_usd <= 0`.
  - It rejects a `storage_uri` not starting with `s3://` or lacking a bucket.
  - It rejects `stage=FT_TRACK_B` with `red_restricted=False`.
  - It rejects `stage_args` keys outside the stage's allow-list.
  - `OutputFileDto` rejects a `relpath` containing `..` or a leading `/`.
  - Instances are frozen.
- [X] T006 [P] Write `tests/test_remote_profile_catalog.py`:
  - The catalog has exactly `DEV` (g5.xlarge, 4 vCPU, 1 GPU), `FINETUNE_DEV` (g5.2xlarge, 8 vCPU, 1 GPU) and `PROD` (g6e.12xlarge, 48 vCPU, 4 GPUs, `candidate=True`).
  - Every profile's `quota_name == "Running On-Demand G and VT instances"`.
  - `ABLITERATE` is in `PROD.stages` and `DEV.stages`.
  - `FT_TRACK_B` is only in `FINETUNE_DEV.stages`.
  - `GGUF` is in `DEV` and `PROD`.
  - A `price_checked` older than 90 days makes `stale_prices()` return that profile.
- [X] T007 [P] Write `tests/test_remote_spend_guard.py` (SC-003):
  - `max_minutes(cap=5, hourly=1.006)` is 298 (floor of cap ÷ hourly × 60).
  - A cap giving fewer than 10 minutes raises `MissingSettingError`-family `SpendCapTooLowError`, named with the cap and the minutes.
  - `estimated_cost(elapsed_minutes, hourly)` is rounded up to the cent.
  - Uses `FakeClock`.
- [X] T008 [P] Write `tests/test_remote_ec2_sdk.py` with `botocore.stub.Stubber`. `launch()` sends:
  - `InstanceInitiatedShutdownBehavior="terminate"`;
  - every `BlockDeviceMappings[].Ebs.DeleteOnTermination=True`;
  - `IamInstanceProfile.Name`;
  - the tags `wellspring:managed=true`, `wellspring:run-id`, `wellspring:profile`, `wellspring:stage` and `wellspring:repo-commit`, on both instance and volume;
  - `MinCount=MaxCount=1`.

  Also:
  - `find_live(run_id)` filters by tag and by states `pending|running|stopping|shutting-down`.
  - `InsufficientInstanceCapacity` maps to `CapacityUnavailableError` with the AWS message.
  - The AMI is resolved from SSM `/aws/service/deeplearning/ami/x86_64/base-oss-nvidia-driver-gpu-ubuntu-24.04/latest/ami-id`.
- [X] T009 [P] Write `tests/test_shared_s3_sdk.py` with `Stubber`:
  - `put/get/list/exists` map to `put_object/get_object/list_objects_v2/head_object` on the bucket and key parsed from `s3://bucket/prefix`.
  - A 404 from `head_object` gives `exists() == False`.
  - Every method is a coroutine.
- [X] T010 [P] Write `tests/test_fakes_contract.py`. It asserts that `FakeInstanceProvider` and `DirObjectStore` satisfy the `InstanceProvider` and `ObjectStore` Protocols, by calling every Protocol method once. That keeps the fakes honest.

### Implementation

- [X] T011 [P] Write the enums, one file each:
  - `RemoteStage{ABLITERATE, GGUF, FT_TRACK_B}`, with no MLX member (FR-014);
  - `ProfileName{DEV, FINETUNE_DEV, PROD}`;
  - `RemoteRunState{PROVISIONING, RUNNING, SYNCING, TERMINATED, FAILED}`;
  - `EndReason{COMPLETED, JOB_FAILED, SPEND_CAP, IDLE, OPERATOR_STOP, BACKSTOP}`.

  Files: `src/wellspring/remote/enums/{remote_stage,profile_name,remote_run_state,end_reason}.py`
- [X] T012 [P] Write the errors, all subclasses of the base `RemoteRefusedError`, each naming the offending setting or value:
  - `src/wellspring/_shared/errors/missing_setting_error.py` (`MissingSettingError`);
  - `src/wellspring/remote/errors/{dirty_tree_error,quota_insufficient_error,request_invalid_error,capacity_unavailable_error,run_state_conflict_error}.py`. That is 5 modules, under the split threshold. `RequestInvalidError` covers stages that aren't allowed and the missing Red attestation, naming the field. `run_state_conflict_error.py` holds the base `RunStateConflictError` and its tightly coupled subclasses `RunAlreadyFinishedError` and `ResumeMismatchError`;
  - `src/wellspring/retrieval/errors/{checksum_mismatch_error,pull_incomplete_error}.py`.

  `QuotaInsufficientError` carries `quota_name`, `required` and `available`. `SpendCapTooLowError` shares the `missing_setting_error.py` file as a tightly coupled subclass (AGENTS §13).
- [X] T013 Write the DTOs per data-model.md, so that T005 passes:
  - `InstanceProfileDto`
  - `RemoteRunRequestDto` (`run_id` `[a-z0-9-]{3,48}`; `spend_cap_usd > 0`; `storage_uri` starts with `s3://` and has a bucket; `red_restricted` must be True when `stage == FT_TRACK_B`; `stage_args` allow-listed per stage)
  - `RemoteRunDto`
  - `RunManifestDto`
  - `OutputFileDto` (`relpath` POSIX, no `..`; `checkpoint: bool`)

  Stage-arg allow-lists:
  - `ABLITERATE`: `MODEL, MODEL_COMMIT, SEED, QUANTIZATION, DEVICE_MAP` (`MAX_MEMORY` was dropped because `src/flow.py` has no such parameter)
  - `GGUF`: `MODEL, MODEL_COMMIT, GGUF_QUANTS, GGUF_F16_TYPE` (the instance downloads `MODEL` itself; FR-006)
  - `FT_TRACK_B`: `FT_MODEL, FT_TRIGGER, FT_VARIANTS, FT_SLEEPERS, FT_N_TRAIN, FT_N_VALID, FT_ITERS, FT_NUM_LAYERS, FT_SEED`

  Files: `src/wellspring/remote/dtos/{instance_profile_dto,remote_run_request_dto,remote_run_dto,run_manifest_dto,output_file_dto}.py`
- [X] T014 [P] Write the Protocols:
  - `ObjectStore` (`put_bytes`, `put_file`, `get_file`, `get_bytes`, `list`, `exists`; async) in `src/wellspring/_shared/types/object_store.py`;
  - `InstanceProvider` (`launch`, `find_live`, `terminate`, `quota`, `resolve_ami`; async) in `src/wellspring/remote/types/instance_provider.py`;
  - `SourceArchiver` (`archive(dest) -> commit`, `dirty_files()`) in `src/wellspring/remote/types/source_archiver.py`;
  - `Clock` (`now()`, `async sleep()`) in `src/wellspring/remote/types/clock.py`.
- [X] T015 [P] Write the fakes so that T010 passes:
  - `tests/fakes/fake_instance_provider.py`: in-memory instances by tag, configurable quota and capacity failure, and a `terminated` list;
  - `tests/fakes/dir_object_store.py`: maps `s3://b/p/...` to `tmp_path/b/p/...`, with a `corrupt(key)` helper;
  - `tests/fakes/fake_clock.py`: manual `advance(minutes)`.
- [X] T016 Write `ProfileCatalogRepository`, with profiles as class constants per research R9, so that T006 passes. Prices:
  - `PROD` uses `hourly_usd=10.4926`, `price_checked=2026-10-02`, from the source noted in a comment.
  - The g5 prices are filled from the AWS pricing page at implementation time, with their checked date. If they can't be confirmed, leave a `price_checked` that marks them unverified and make the catalog warn.

  File: `src/wellspring/remote/repositories/profile_catalog_repository.py`
- [X] T017 Write `SpendGuardService` (`max_minutes`, `estimated_cost`), so that T007 passes. File: `src/wellspring/remote/services/spend_guard_service.py`
- [X] T018 [P] Write `Ec2Sdk` implementing `InstanceProvider` over boto3 `ec2`, `ssm` and `service-quotas`, every call under `asyncio.to_thread`, so that T008 passes. `quota(name)` uses `list_service_quotas` filtered by **name**, not a hard-coded code (research R8). File: `src/wellspring/remote/sdks/ec2_sdk.py`
- [X] T019 [P] Write `S3Sdk` implementing `ObjectStore`, so that T009 passes. File: `src/wellspring/_shared/sdks/s3_sdk.py`

**Checkpoint**: `make test` is green. Every foundational type exists.

---

## Phase 3: User Story 1: abliterate the production model remotely (P1) 🎯 MVP

**Goal**: `make remote-run REMOTE_STAGE=abliterate …` launches, runs and syncs on the instance. `make remote-pull` verifies and ingests the journal into MLflow.

**Independent test**: with `FakeInstanceProvider`, `DirObjectStore` and a fake stage command, the sequence run → (agent executes) → pull → ingest leaves one MLflow row per fake trial, the same count after a second pull, and zero live fake instances.

### Tests first

- [X] T020 [P] [US1] Write the quota tests in `tests/test_remote_run_service.py`. Quota preflight is a private step of `RemoteRunService`, which keeps `remote/services/` at 5 modules. A profile needing 48 vCPU, with an applied quota of 32 and 0 running, raises `QuotaInsufficientError(quota_name="Running On-Demand G and VT instances", required=48, available=32)` **before** `launch` is called (assert on the fake's call log). Running vCPUs are subtracted from the available quota.
- [X] T021 [P] [US1] Write `tests/test_remote_git_archive_sdk.py`, using a temporary git repo:
  - A clean tree gives a tarball and the HEAD SHA.
  - An untracked or modified file raises `DirtyTreeError`, listing the files.
  - It runs through `asyncio.create_subprocess_exec` via `ProcessSdk`.
- [X] T022 [P] [US1] Write `tests/test_remote_bootstrap_service.py`. The rendered user-data:
  - begins with `#!/bin/bash` and then, as its first command, `shutdown -h +<max_minutes>`;
  - contains no AWS credentials, no `HF_TOKEN` and no `FT_TRIGGER` value (scan for the request's secret-bearing values; FR-011 / research R2);
  - installs `uv`, Python 3.14 and `expect`;
  - downloads `<storage_uri>/<run_id>/source.tar.gz`;
  - runs `python -m wellspring remote-agent --request <storage_uri>/<run_id>/request.json`;
  - is under 16 KB (the EC2 user-data limit).
- [X] T023 [P] [US1] Write `tests/test_remote_run_service.py`:
  - Missing region, cap, storage URI or instance profile raises `MissingSettingError` naming the variable, with zero provider calls.
  - A dirty tree raises `DirtyTreeError`, with zero calls.
  - A happy launch uploads `request.json` and `source.tar.gz`, then calls `launch` once.
  - A second `run` with a live instance reuses it (one launch total; FR-004).
  - A run ID whose `checksums.sha256` exists raises `RunAlreadyFinishedError`, with zero launches.
  - A `CapacityUnavailableError` from the provider leaves zero live instances and maps to exit 2.
- [X] T024 [P] [US1] Write `tests/test_remote_agent_service.py`, with a fake process runner and `DirObjectStore`:
  1. The agent runs instance preflight. Fewer GPUs than the profile gives `end_reason=JOB_FAILED`, with a sync and a shutdown.
  2. It runs the `ABLITERATE` argv exactly as `python src/flow.py run --only_step decensor --device_map auto --model <MODEL> --model_commit <MODEL_COMMIT> …`, as an argv list with no shell.
  3. It syncs the outputs.
  4. It writes `manifest.json` and then `checksums.sha256` **last** (assert the upload order). Outputs under the checkpoint directory are flagged `checkpoint=True`.
  5. It calls the injected `shutdown()` once.
  6. The manifest has every FR-010 field.
- [X] T025 [P] [US1] Write `tests/test_retrieval_pull_service.py`:
  - By default, files flagged `checkpoint=True` are not downloaded, but stay listed in the manifest (FR-008).
  - `include_checkpoint=True` downloads them.
  - A corrupted file (`DirObjectStore.corrupt`) raises `ChecksumMismatchError` naming the file, leaves only `<run-id>.tmp` (no final directory) and ingests nothing (exit 3).
  - A missing `checksums.sha256` raises `PullIncompleteError`.
  - A successful pull renames `<run-id>.tmp` to `<run-id>` atomically.
  - The service never calls any delete on the store (FR-017).
- [X] T026 [P] [US1] Write `tests/test_retrieval_journal_ingest_service.py`. With a fixture Optuna journal (reuse the fixture builder from `tests/test_log_heretic_to_mlflow.py`, if present) and a `file://` or SQLite MLflow URI in `tmp_path`:
  - Ingestion creates one run per completed trial, each tagged `hardware_class=<profile>:<instance_type>` and `remote_run_id`.
  - A second ingest leaves the row count unchanged (SC-004).
- [X] T027 [P] [US1] Write `tests/test_wellspring_cli_remote.py`. The `remote-run`, `remote-pull` and `remote-agent` subcommands parse the contract's variables from the environment (`REMOTE_*`, plus the stage args), call the matching Workbench method once per `asyncio.run`, and map errors to the exit codes in `contracts/remote-cli.md` (1 refusal, 2 cloud, 3 pull). Use a stub Workbench.

### Implementation

- [X] T028 [US1] Write the private `RemoteRunService._check_quota(profile)`, so that T020 passes. File: `src/wellspring/remote/services/remote_run_service.py`
- [X] T029 [P] [US1] Write `GitArchiveSdk` implementing `SourceArchiver` over `ProcessSdk` (`git status --porcelain`, `git archive --format=tar.gz HEAD`, `git rev-parse HEAD`), so that T021 passes. File: `src/wellspring/remote/sdks/git_archive_sdk.py`
- [X] T030 [P] [US1] Write `BootstrapService.render(request, profile, max_minutes) -> str`, so that T022 passes. The rendered script is generated text and is never written into the repository (plan, Complexity Tracking). File: `src/wellspring/remote/services/bootstrap_service.py`
- [X] T031 [US1] Write `RemoteRunService.run(request)`, so that T023 passes. Order: settings, dirty tree, finished-run check, live reuse, quota, `max_minutes`, upload source and request, launch. File: `src/wellspring/remote/services/remote_run_service.py`
- [X] T032 [US1] Write `RemoteAgentService.execute(request_uri)`, so that T024 passes. The stage-to-argv mapping covers `ABLITERATE` only for now; GGUF and FT come in US3. It shells out via `ProcessSdk`, uploads via `ObjectStore`, and uses an injected `shutdown` callable (the real one is `sudo shutdown -h now`). File: `src/wellspring/remote/services/remote_agent_service.py`
- [X] T033 [P] [US1] Write `MlflowSdk`, wrapping `MlflowClient` (`search_runs` by tag, `set_tag`, `create_run`, `log_batch`) under `asyncio.to_thread`. File: `src/wellspring/retrieval/sdks/mlflow_sdk.py`
- [X] T034 [US1] Write `PullService`, with `PullResultDto` in `src/wellspring/retrieval/dtos/pull_result_dto.py`, so that T025 passes. File: `src/wellspring/retrieval/services/pull_service.py`
- [X] T035 [US1] Write `JournalIngestService`, so that T026 passes. It runs `src/scripts/log_heretic_to_mlflow.py --journal-file <pulled journal>` via `ProcessSdk`, then sets the `hardware_class` and `remote_run_id` tags through `MlflowSdk` on runs matching its `journal_identity`. `src/scripts/` is not modified. File: `src/wellspring/retrieval/services/journal_ingest_service.py`
- [X] T036 [US1] Add `remote_run`, `remote_pull` and `remote_agent` to the Workbench, composing `Ec2Sdk`, `S3Sdk`, `GitArchiveSdk`, `ProfileCatalogRepository`, the services, and a real clock that wraps `time` and `asyncio.sleep`. File: `src/wellspring/workbench.py`, plus the clock in `src/wellspring/remote/sdks/system_clock_sdk.py`
- [X] T037 [US1] Add the `remote-run`, `remote-pull` and `remote-agent` subcommands and the exit-code mapping, so that T027 passes. If `cli.py` would exceed 400 lines, move the remote parsers into `src/wellspring/remote_cli.py` (`RemoteCliParser` class). File: `src/wellspring/cli.py`
- [X] T038 [US1] Add the Makefile targets `remote-run` and `remote-pull`, plus the variables from the contract table: no defaults except `REMOTE_PULL_DIR ?= data/remote`, `REMOTE_PULL_CHECKPOINT ?= 0` and `REMOTE_RED_RESTRICTED ?= 0`. Add `.PHONY` entries and `make help` lines matching the existing `@echo` style. File: `Makefile`
- [X] T039 [US1] Add README rows for `remote-run` and `remote-pull` under Make Targets, and the `REMOTE_*` variables under Key Variables, inside a `<details>` block per DESIGN.md (dense content collapses). Link spec 027. File: `README.md`

**Checkpoint**: Story 1's independent test passes under `make test`.

---

## Phase 4: User Story 2: never orphaned, never overspent (P1)

**Goal**: the instance syncs and terminates on completion, idle, cap or backstop, without the Mac. `remote-status` and `remote-down` exist.

**Independent test**: with `FakeClock`, each of idle timeout, cap reached, job crash and vanished launcher ends with zero live fake instances, and with the synced journal present.

### Tests first

- [X] T040 [P] [US2] Extend `tests/test_remote_agent_service.py` with:
  - no job process for `IDLE_MINUTES=15` → `end_reason=IDLE`, then sync and shutdown;
  - elapsed reaching `max_minutes - 5` → `end_reason=SPEND_CAP`, a final sync before the backstop, and shutdown;
  - the stage process exiting non-zero → `end_reason=JOB_FAILED`, then sync, manifest and shutdown;
  - `status.json` heartbeats every `SYNC_MINUTES=10`, with the journal synced at each heartbeat (FR-007).
- [X] T041 [P] [US2] Write `tests/test_remote_status_service.py`. `status(region)` lists every fake instance tagged `wellspring:managed=true`, with run ID, profile, state, `elapsed_minutes` and `estimated_cost_usd` from `SpendGuardService`, merged with `status.json`. A run whose instance is gone and that has no `end_reason` reports `BACKSTOP`.
- [X] T042 [P] [US2] Write `tests/test_remote_down_service.py`. `down(run_id)` terminates only instances with that tag. `down("all-managed")` terminates every managed instance. The result is idempotent: a second call is a no-op with exit 0.
- [X] T043 [P] [US2] Write `tests/test_remote_teardown_matrix.py` (SC-002). It is parametrised over `{COMPLETED, IDLE, SPEND_CAP, JOB_FAILED, launcher-vanished}` and drives the agent, the provider and the clock end to end. It asserts `provider.find_live(run_id) == []` and that the journal exists in the store.

### Implementation

- [X] T044 [US2] Add the idle, cap and heartbeat loop to `RemoteAgentService`, using `asyncio.TaskGroup` (Article XVIII Rule 5) with the job task and the watchdog task, so that T040 and T043 pass. File: `src/wellspring/remote/services/remote_agent_service.py`
- [X] T045 [P] [US2] Write `RemoteStatusService`, so that T041 passes. File: `src/wellspring/remote/services/remote_status_service.py`. This is the 5th service module. `remote-down` is `RemoteStatusService.down()`, not a 6th file, and T042's tests target that method.
- [X] T046 [US2] Add `remote_status` and `remote_down` to the Workbench, plus the CLI subcommands. `remote-status` renders an aligned table with columns `RUN ID  PROFILE  STATE  ELAPSED  EST. COST  END REASON`, or "No managed instances in <region>." when empty. Files: `src/wellspring/workbench.py`, `src/wellspring/cli.py` (or `remote_cli.py`)
- [X] T047 [US2] Add the Makefile targets `remote-status` and `remote-down` with help lines, and the README rows. Files: `Makefile`, `README.md`

**Checkpoint**: Stories 1 and 2 pass. Teardown is guaranteed under every simulated outcome.

---

## Phase 5: User Story 3: dev-profile GGUF and Track B fine-tune, with resume (P2)

**Goal**: the `GGUF` and `FT_TRACK_B` stages run remotely. Their MLflow runs are copied back. An unfinished run resumes under the same ID.

**Independent test**: with fake GGUF and FT commands, a remote fine-tune requires `REMOTE_RED_RESTRICTED=1`. Its Red-only outputs land only under the run prefix. Its MLflow runs are copied idempotently. A resumed run continues from the synced journal.

### Tests first

- [X] T048 [P] [US3] Extend `tests/test_remote_agent_service.py`:
  - `GGUF` runs `make gguf HF_PATH=… GGUF_QUANTS=…`.
  - `FT_TRACK_B` runs `make finetune FT_TRIGGER=… …`, with every arg from the allow-list only.
  - Each stage sets `MLFLOW_TRACKING_URI=sqlite:///<outputs>/mlflow.db` for the child process.
- [X] T049 [P] [US3] Write `tests/test_remote_resume.py` (FR-004):
  - An unfinished run (no `checksums.sha256`) with no live instance relaunches under the same ID.
  - The agent restores `outputs/` from the store before running, so the Optuna journal or Metaflow state is reused.
  - A resume whose stage, profile or `stage_args` differ from the stored `request.json` raises `ResumeMismatchError`, naming the field. Only `spend_cap_usd` may differ.
- [X] T050 [P] [US3] Write `tests/test_retrieval_mlflow_run_copy_service.py`. Given a source SQLite MLflow store in `tmp_path`, with two runs carrying params, metrics and tags:
  - Copying into a target store creates two runs tagged `remote_run_id` and `hardware_class`.
  - A second copy creates none.
  - Experiment names are preserved, including `<prefix>-finetune-red`.
- [X] T051 [P] [US3] Add to `tests/test_remote_run_service.py`: `FT_TRACK_B` with `red_restricted=False` raises `RequestInvalidError(field="red_restricted")` and makes zero calls. With `True`, `request.json` records `red_restricted: true`, and so does the manifest the agent writes (assert in the agent test).

### Implementation

- [X] T052 [US3] Add the `GGUF` and `FT_TRACK_B` argv mappings and the per-stage `MLFLOW_TRACKING_URI`, so that T048 passes. File: `src/wellspring/remote/services/remote_agent_service.py`
- [X] T053 [US3] Add resume to `RemoteRunService` (compare with the stored request, then relaunch) and the `outputs/` restore to `RemoteAgentService`, so that T049 passes. Files: `src/wellspring/remote/services/remote_run_service.py`, `src/wellspring/remote/services/remote_agent_service.py`
- [X] T054 [US3] Write `MlflowRunCopyService`, and wire it into `PullService` when `outputs/mlflow.db` exists, so that T050 passes. File: `src/wellspring/retrieval/services/mlflow_run_copy_service.py`
- [X] T055 [US3] Add the Red attestation check to `RemoteRunService`, so that T051 passes. File: `src/wellspring/remote/services/remote_run_service.py`

**Checkpoint**: all three stories pass offline.

---

## Phase 6: Polish and real-world validation

- [X] T056 Run `make test` once and record the pass count. Run `lsp_diagnostics` on every new or changed file under `src/wellspring/` and `tests/`, and fix every error introduced by this feature.
- [X] T057 [P] Document the one-time account setup in `docs/remote-execution.md`. It covers:
  - AWS profile/SSO;
  - the region;
  - the S3 bucket, with a lifecycle rule recommended (FR-017);
  - an IAM instance profile scoped to the bucket prefix, with an example policy;
  - an AWS Budgets alert (clarification Q3);
  - the G-family quota request, linking to the Service Quotas console;
  - what `REMOTE_RED_RESTRICTED=1` attests (Article XV Rule 2).

  Link it from the README `<details>` block.
- [X] T058 Render `make help` and `make remote-status` with no instances, and look at the output (Article XX, AGENTS §4): alignment, wording, no stack traces on refusals.
- [ ] T059 **Manual, needs an AWS account** (quickstart §2): run the dev rehearsal on `dev` with SmolLM2 and `REMOTE_SPEND_CAP_USD=5`.
  - Record launch-to-job-start time, peak VRAM, actual cost, and confirmation that zero instances or volumes remain.
  - Write `vault/discoveries/2026-MM-DD-remote-dev-rehearsal.md` with the measurements and link it from the hub.
  - Record the result as "did not run" if no account exists yet.
- [ ] T060 **Manual, needs an AWS account** (quickstart §3): run the teardown drill with `REMOTE_SPEND_CAP_USD=0.25`. Verify `end_reason` is `SPEND_CAP` or `BACKSTOP` and that no instance remains.
- [ ] T061 Using T059's peak VRAM for the dev model and a documented scaling estimate, update `PROD`'s `candidate` flag in `profile_catalog_repository.py` and the spec 027 FR-002 note. Leave it a candidate if no production-scale measurement exists.
- [X] T062 Update `ROADMAP.md` to set 027's status, and run `make vault-audit`.

---

## Dependencies & Execution Order

- **Phase 1 → Phase 2 → stories.** T001 blocks T002, because the lock has to be valid before boto3 is added.
- **US1 (Phase 3)** depends only on Phase 2. It is the MVP.
- **US2 (Phase 4)** depends on US1's `RemoteAgentService`, Workbench and CLI (T032, T036, T037).
- **US3 (Phase 5)** depends on US1. It is independent of US2, apart from shared files (`remote_agent_service.py`, `remote_run_service.py`), so run US2 and US3 sequentially rather than in parallel.
- **Polish** comes after the stories. T059–T061 additionally need an AWS account and G-family quota, and are the only tasks that do.

## Parallel examples

- Phase 2: T005–T010 (all test files), then T011, T012, T014, T015, T018 and T019 in parallel. T013 follows T011 and T012; T016 and T017 follow T013.
- US1: T020–T027 in parallel (T020 and T023 share a file, so write them together), then T029, T030 and T033 in parallel, followed by T028 → T031, T032, T034 and T035, then T036 → T037 → T038 → T039.
- US2: T040–T043 in parallel, then T044 and T045, then T046 → T047.
- US3: T048–T051 in parallel, then T052 → T053 → T055, with T054 in parallel to them.

## Implementation strategy

1. **MVP = Phases 1–3.** A remote abliteration can be launched, pulled and ingested. Do not run it against real AWS before US2 lands, because US1 alone relies only on the `shutdown -h +N` backstop.
2. **US2 makes it safe to use for real.** After Phase 4, the dev rehearsal (T059) may run.
3. **US3 adds the other stages and resume.** Production fine-tuning stays blocked on spec 011.
4. **Commit per task group,** each with `make test` green (pre-commit hook). Keep the lock regeneration (T001) as its own commit.

---

## Implementation notes (2026-10-02)

Deviations from the task text, recorded so the record matches the code:

- **Quota preflight and resume** live in `RemoteRunService` and are tested in
  `tests/test_remote_run_service.py` (T020, T028, T049, T053). This keeps
  `remote/services/` under the 6-module split threshold.
- **Missing settings** are refused by `RemoteCli` (`src/wellspring/remote_cli.py`),
  the entry point that reads the environment, so the T023 checks moved to
  `tests/test_wellspring_cli_remote.py`. Invalid fields and the Red attestation
  (T051) are rejected by `RemoteRunRequestDto.build` as `RequestInvalidError`.
- **The watchdog** (idle, cap, heartbeat) was written together with the agent
  in T032, so its T040 tests passed on first run instead of failing first.
  To show they can fail, each constant was broken in turn
  (`CAP_MARGIN_MINUTES=0`, `IDLE_MINUTES=100000`, `SYNC_MINUTES=100000`).
  The second review pass replaced `CAP_MARGIN_MINUTES` with the per-profile
  `sync_margin_minutes`, which `test_stage_stops_the_profiles_sync_margin_before_the_deadline` covers.
  Every mutation turned exactly one test red.
- **MLflow** is reached through a `TrackingStore` Protocol
  (`retrieval/types/`). The Workbench loads `MlflowSdk` dynamically, so
  non-pull commands do not import mlflow (Article XI Rule 4).
- **Resuming an abliteration restores the synced journal** (FR-004), but
  Heretic's search restarts: `src/scripts/heretic_automate.exp` answers
  Heretic's recovery prompt with "start from scratch". Continuing the trial
  search is not implemented. That would change the expect script, which is
  out of this spec's scope.
- **T059–T061 did not run.** No AWS account has been used yet. These are the
  only remaining tasks and need a real account with G-family quota.

### Review fixes (2026-10-02, second pass)

These were found by reviewing the implementation critically. Each one was
written test-first, except the doc updates.

- **Critical**: the bootstrap started the agent without `PYTHONPATH=src`, so
  `python -m wellspring` could not import. Every real run would have ended at
  the backstop with no outputs. Also fixed: `python3.14` is now put on PATH
  for `make setup`, and `AWS_DEFAULT_REGION` is set.
- `region` and the storage-URI prefix are embedded in the root bootstrap, so
  they are now validated against strict patterns that exclude shell
  metacharacters.
- Every boto3/botocore error (missing credentials, access denied, throttling)
  is converted to `CloudApiError` at the SDK boundary. It exits 2 with the
  provider's code instead of a traceback.
- The agent survives a failed heartbeat sync, and a missing binary ends the
  run as `job_failed` instead of crashing it. Either one would previously have
  skipped the manifest.
- FR-012 instance preflight now checks GPU memory and free disk, not just the
  GPU count.
- FR-006: the model commit is resolved on the Hub, pinned for the stage and
  recorded as `model_commit_resolved`. Previously the unresolved `null` was
  recorded.
- An instance that is still shutting down is no longer "reused". A resume
  from a different repository commit is refused.
- The spend cap keeps 3 minutes of boot headroom (SC-003).
- The root device name is read from `DescribeImages` instead of assuming
  `/dev/sda1`.
- `MLFLOW_EXPERIMENT_PREFIX` is honoured by `remote-pull`.
- `finetune/handover/` counts as a checkpoint, so pulls don't download model
  copies by default.
- Two meaningless assertions were removed from the tests.

### Review fixes (second review pass)

- A fixed 5-minute stop margin could not fit the final upload of a ~66 GB
  production checkpoint, so the backstop would have cut it off and no
  manifest would have been written. Now:
  - the margin is per profile (`sync_margin_minutes`: 10, 10, 30);
  - runs that did not complete upload no checkpoint.
- `remote-status` reports `BACKSTOP` for a run whose instance died before the
  agent wrote any `status.json`. Such a run used to be invisible.
- A failed stage step logs only the program name and target, never its
  arguments, which may include `FT_TRIGGER`.
- Added the missing `CHANGELOG.md` entries.

## Phase 7: Convergence

- [ ] T063 CRITICAL: Add a profile-catalog `Protocol` in `src/wellspring/remote/types/` and type `RemoteRunService`, `RemoteAgentService` and `RemoteStatusService` against it instead of the concrete `ProfileCatalogRepository` per Constitution XVII (contradicts)
- [ ] T064 CRITICAL: Make the public methods of `ProfileCatalogRepository`, `SpendGuardService`, `BootstrapService` and `Clock.now` / `SystemClockSdk.now` coroutines, updating callers and tests, or record an approved exception per Constitution XVIII (contradicts)
- [ ] T065 Capture each stage step's output and the bootstrap log (`/var/log/wellspring-bootstrap.log`) into `remote-out/logs/` and sync them on every heartbeat and at the final sync. The `ft-qa` verdict and failure output must then reach storage. Test-first in `tests/test_remote_agent_service.py` per FR-007 / US3/AC1 (missing)
- [ ] T066 Reconcile the partial-run checkpoint policy with FR-007, which requires the checkpoint to be copied before any teardown. Either amend FR-007 via `/speckit.clarify`, or upload checkpoints for non-completed runs within the sync margin, per FR-007 (contradicts)
- [ ] T067 Classify checkpoints by weight-file pattern (`*.safetensors`, `*.gguf`, `*.bin`, `*.pt`) instead of whole directory prefixes, so recipe stamps and other small files under `finetune/out/models/` are pulled by default. Test-first in `tests/test_remote_agent_service.py` per US3/AC1 (partial)
- [ ] T068 Decide and implement abliterate resume: add a resume-aware "continue" choice to `src/scripts/heretic_automate.exp` (its own tested change), or amend US3/AC2 via `/speckit.clarify` per US3/AC2 (partial)
- [ ] T069 Pin the resolved `FT_MODEL` SHA for the `ft-track-b` stage so the fine-tune base download uses the recorded commit (verify how `make finetune` resolves `FT_MODEL` first) per FR-006 (partial)
- [ ] T070 Document in `docs/remote-execution.md` that the spend cap bounds instance-hours only (EBS, S3 storage and pull egress are extra), or add them to the estimate, per SC-003 (partial)
