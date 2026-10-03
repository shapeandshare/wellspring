# Implementation Plan: Remote Execution on AWS (Phase A)

**Branch**: N/A (current branch) | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/027-remote-execution-aws/spec.md`

## Summary

The Mac launches a single AWS GPU instance that runs one allow-listed pipeline
stage on its own and then terminates itself:

1. A Python-generated cloud-init bootstrap arms a hard `shutdown` backstop
   derived from the spend cap.
2. It installs the toolchain and runs the on-instance agent.
3. The agent syncs outputs, with checksums, to an operator-supplied S3 prefix.

The Mac pulls from S3, verifies, renames into place atomically, and ingests
into local MLflow idempotently. There is no SSH, no inbound port, no control
plane and no IaC framework. Rationale and sources are in
[research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14 (on the Mac and on the instance, via `uv`)

**Primary Dependencies**: boto3 (new direct dependency, Apache-2.0); Pydantic
v2; MLflow (`MlflowClient`); the existing repository pipeline (`src/flow.py`,
Makefile)

**Storage**: an operator-supplied S3 prefix (layout in
[data-model.md](data-model.md)); the local MLflow tracking URI;
`data/remote/` (new and git-ignored)

**Testing**: pytest. Fakes for the instance provider, object store and clock
(local directory). `botocore.stub.Stubber` checks request shapes. Nothing
touches the network (FR-015).

**Target Platform**: the launcher runs on macOS (Apple Silicon). The instance
runs Ubuntu 24.04 on the AWS DLAMI Base OSS NVIDIA image, on G5 and G6e
(research R6).

**Project Type**: CLI and pipeline orchestration, inside the
`src/wellspring/` layered package

**Performance Goals**: not a throughput feature. Launch to job start in
≤ 15 min on `dev`, checked during the dev rehearsal and **unmeasured** until
then.

**Constraints**: zero orphaned instances (SC-002); spend ≤ cap plus one
billing increment (SC-003); no secrets in user-data; public HF models only in
phase A

**Scale/Scope**: one instance per run ID, run sequentially; three profiles;
three stages

## Constitution Check

*Gate before Phase 0, re-checked after Phase 1. Result: **PASS**, with one
prerequisite (P1).*

| Article | How this design complies | Status |
|---|---|---|
| I Provenance | `manifest.json` adds region, instance type, AMI ID, driver, CUDA, package-set hash, repository commit and the price used (FR-010). A dirty tree is refused (R5). | PASS |
| II Licences | boto3/botocore are Apache-2.0, flagged in `THIRD_PARTY_NOTICES.md`; `make notices` and `make lock` are re-run. | PASS after **P1** |
| III Two export paths | No MLX stage exists in `RemoteStage`, so nothing crosses between paths. | PASS |
| IV Atomic, rerunnable | Launch is idempotent by run tag. Pulls go to `.tmp` and are renamed after verification. Ingestion skips runs already present. | PASS |
| V Bounded reproducibility | No new determinism claims; the manifest records the hardware class. | PASS |
| VI Simplicity | No SkyPilot, no Terraform, no SSH, no server (R1–R4). | PASS |
| VII Makefile is the interface | Four `remote-*` targets, with README and `make help` rows in the same change. | PASS |
| VIII Fail fast | Every refusal (missing setting, dirty tree, quota, stage, Red attestation) happens before any spend, named, exit 1. A checksum mismatch ingests nothing. | PASS |
| IX TDD | Every service is written red-first against fakes. A planted-corruption test proves the checksum gate can fail. | PASS (enforced in tasks) |
| X–XII Package, one class per file, types | Two new domains, all layers at ≤ 5 modules (see the tree below). Enums in `enums/`, no `Any`, `from __future__ import annotations`. | PASS |
| XIII Agent conduct | Scope matches the spec. README updated in the same change. | PASS |
| XIV Vault | Discoveries from the dev rehearsal (Python 3.14 shim, real launch time, peak VRAM) go to `vault/discoveries/`. | PASS |
| XV Fine-tuning integrity | Red-only material is allowed only with `REMOTE_RED_RESTRICTED=1`, an operator attestation recorded in the manifest (R4). `ft-handover` is unchanged. | PASS |
| XVII Layered | CLI → Workbench → services → sdks/repositories. boto3 and MLflow objects never leave their SDK wrappers. | PASS |
| XVIII Async-first | Services are async. boto3 and MLflow calls are wrapped in `asyncio.to_thread` inside the SDKs; subprocesses use `create_subprocess_exec`. One `asyncio.run` per CLI entry. | PASS |
| XX Polish | `remote-status` renders an aligned table. Render it and look during QA (AGENTS §4). | PASS |
| Spec 002 FR-004 | Untouched: no Metaflow remote decorators. Phase C will supersede it. | N/A |

**P1 — prerequisite**: `requirements-lock.txt` cannot currently be satisfied
(it pins heretic-llm 1.4.0 together with optuna 5.0.0). Adding boto3 requires
`make lock`, so the lock must be regenerated first, as its own commit
(vault discovery 2026-10-02). This is task 1.

## Project Structure

### Documentation (this feature)

```text
specs/027-remote-execution-aws/
├── spec.md
├── plan.md              # this file
├── research.md          # R1–R10
├── data-model.md
├── quickstart.md
├── contracts/remote-cli.md
├── checklists/requirements.md
└── tasks.md             # /speckit.tasks
```

### Source Code

```text
src/wellspring/
├── _shared/
│   ├── errors/    refused_error, missing_setting_error, cloud_api_error
│   ├── types/object_store.py              # Protocol: put/get/list/exists
│   └── sdks/s3_sdk.py                     # ObjectStore over boto3 S3
├── remote/                                # launch, lifecycle, on-instance agent
│   ├── dtos/      instance_profile_dto, remote_run_request_dto, remote_run_dto,
│   │              run_manifest_dto, output_file_dto                       (5)
│   ├── enums/     remote_stage, profile_name, remote_run_state, end_reason (4)
│   ├── errors/    dirty_tree, quota_insufficient, request_invalid,
│   │              capacity_unavailable, run_state_conflict                (5)
│   ├── types/     instance_provider, source_archiver, clock, remote_workbench (4)
│   ├── repositories/ profile_catalog_repository                           (1)
│   ├── sdks/      ec2_sdk, git_archive_sdk, system_clock_sdk              (3)
│   └── services/  remote_run_service (incl. quota preflight), bootstrap_service,
│                  spend_guard_service, remote_agent_service,
│                  remote_status_service (incl. down)                      (5)
├── retrieval/                             # pull, verify, ingest
│   ├── dtos/      pull_result_dto, run_record_dto                         (2)
│   ├── errors/    checksum_mismatch, pull_incomplete, ingest_failed       (3)
│   ├── types/     tracking_store (Protocol; keeps mlflow out of services)  (1)
│   ├── sdks/      mlflow_sdk                                              (1)
│   └── services/  pull_service, mlflow_run_copy_service,
│                  journal_ingest_service                                  (3)
├── workbench.py   # + remote_run / remote_status / remote_pull / remote_down / remote_agent
├── remote_cli.py  # RemoteCli: the five subcommands (contract)
└── cli.py         # hands remote-* to RemoteCli

tests/
├── fakes/         fake_instance_provider.py, dir_object_store.py, fake_clock.py, fake_stage_runner.py
├── test_remote_*.py
└── test_retrieval_*.py
```

Also changed:
- `Makefile`: four targets, the variables, and `make help`.
- `README.md`: target and variable rows.
- `requirements.txt`: `boto3` pinned.
- `.gitignore`: `/data/remote/`.
- `THIRD_PARTY_NOTICES.md`, `requirements-lock.txt`,
  `third_party_licenses.json`: regenerated.

**Structure Decision**: two domains rather than one `compute/`. One domain's
errors layer would reach 6 modules, which is the split threshold (AGENTS
§13). The halves also split naturally: `remote/` only creates and runs
things, and `retrieval/` only reads them back.

`journal_ingest_service` runs the existing `log_heretic_to_mlflow.py` as a
subprocess, then sets `hardware_class` on the resulting runs through
`mlflow_sdk`. Legacy `src/scripts/` is therefore not modified.

## Complexity Tracking

| Item | Why needed | Simpler alternative rejected because |
|---|---|---|
| A generated cloud-init bootstrap (shell, about 10 lines, never committed) | The hard `shutdown -h +N` backstop has to arm before any Python runs (R3) | An all-Python agent can't guarantee teardown if Python, uv or the network fails during setup |
| A second domain (`retrieval/`) | Keeps every layer under the 6-module split threshold | A single domain would break the threshold at once |
