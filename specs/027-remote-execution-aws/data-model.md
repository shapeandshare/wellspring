# Data Model: Remote Execution on AWS (Phase A)

All entities are Pydantic v2 `BaseModel`s, frozen unless stated otherwise.
Enums live one per file in `compute/enums/`.

## Enums

| Enum | Members | Notes |
|---|---|---|
| `RemoteStage` | `ABLITERATE`, `GGUF`, `FT_TRACK_B` | No MLX member, so FR-014 holds by construction (research R10) |
| `ProfileName` | `DEV`, `FINETUNE_DEV`, `PROD` | |
| `RemoteRunState` | `PROVISIONING`, `RUNNING`, `SYNCING`, `TERMINATED`, `FAILED` | |
| `EndReason` | `COMPLETED`, `JOB_FAILED`, `SPEND_CAP`, `IDLE`, `OPERATOR_STOP`, `BACKSTOP` | Written by the agent; `BACKSTOP` is inferred when no reason was written |

## `InstanceProfileDto` (from the catalog)

| Field | Type | Rule |
|---|---|---|
| `name` | `ProfileName` | unique |
| `instance_type` | `str` | e.g. `g6e.12xlarge` |
| `vcpus` | `int` | > 0; used by the quota preflight |
| `gpu_count` / `gpu_mem_gib` | `int` / `float` | checked again on the instance (FR-012) |
| `root_disk_gib` | `int` | EBS root volume size; the device name comes from the image (`DescribeImages`) |
| `sync_margin_minutes` | `int` | ≥ 5; the stage is stopped this long before the backstop so the final upload fits |
| `work_disk_gib` | `int` | minimum free space under the work directory; checked on the instance before the stage (FR-012) |
| `hourly_usd` / `price_checked` | `Decimal` / `date` | warn if more than 90 days old (R9) |
| `price_source` | `str` | where `hourly_usd` was read |
| `quota_name` / `quota_families` | `str` / `tuple[str, ...]` | e.g. `Running On-Demand G and VT instances` / `("g", "vt")` (R8) |
| `stages` | `frozenset[RemoteStage]` | a request outside this set is rejected |
| `candidate` | `bool` | `PROD` is `True` until measured (FR-002) |

## `RemoteRunRequestDto` (operator input; every field required, no defaults)

| Field | Type | Validation |
|---|---|---|
| `run_id` | `str` | `[a-z0-9-]{3,48}`; the idempotency key (FR-004) |
| `stage` | `RemoteStage` | must be in the profile's `stages` |
| `profile` | `ProfileName` | |
| `region` | `str` | `^[a-z]{2}(-[a-z]+)+-[0-9]$` (it is written into the bootstrap) |
| `spend_cap_usd` | `Decimal` | > 0; the resulting `max_minutes` must be ≥ 10 or launch is refused |
| `storage_uri` | `str` | `s3://<bucket>[/prefix]`, prefix limited to letters, digits and `. _ / -` (it is written into the bootstrap) |
| `instance_profile` | `str` | IAM instance-profile name |
| `red_restricted` | `bool` | must be `True` when `stage == FT_TRACK_B` (FR-011) |
| `stage_args` | `dict[str, str]` | allow-listed per stage (e.g. `MODEL`, `MODEL_COMMIT`, `FT_TRIGGER`), never shell-interpolated |
| `repo_commit` / `ami_id` | `str` | filled in by the launcher, not the operator |

## `RemoteRunDto` (observed state; returned by status)

`run_id`, `instance_id | None`, `profile`, `region`, `state: RemoteRunState`,
`launched_at | None`, `elapsed_minutes`, `estimated_cost_usd`,
`end_reason: EndReason | None`.

State transitions:

```
PROVISIONING → RUNNING → SYNCING → TERMINATED
      │            │         │
      └──────┬─────┴─────────┘
             ▼
           FAILED
```

`FAILED` means the job or the sync failed. The instance is still terminated.

## `RunManifestDto` (written by the agent, the last file before `checksums.sha256`)

`stage_args` (with `FT_TRIGGER` redacted), `model_commit_resolved` (the Hub SHA the stage actually used; FR-006), plus:
`region`, `instance_type`, `ami_id`, `nvidia_driver`, `cuda_version`,
`package_set_sha256` (a hash of `pip freeze`), `repo_commit`,
`hourly_usd_used`, `spend_cap_usd`, `end_reason`, `red_restricted`,
`hardware_class` (`"<profile>:<instance_type>"`), `peak_vram_mib`, and
`outputs: list[OutputFileDto]`.

## `OutputFileDto`

`relpath: str` (POSIX, no `..`), `sha256: str`, `bytes: int`,
`checkpoint: bool` (skipped by default on pull; spec FR-008).

## Storage layout (per run)

```
<storage_uri>/<run_id>/
├── request.json         # RemoteRunRequestDto, written by the Mac at launch
├── source.tar.gz        # git archive HEAD (R5)
├── status.json          # the agent's state + heartbeat, overwritten
├── outputs/…            # stage outputs, journal, logs
├── manifest.json        # RunManifestDto
└── checksums.sha256     # written last; a pull without it is incomplete
```
