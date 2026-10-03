# Contract: remote-execution commands

The Makefile is the interface (Article VII). Each target calls
`python -m wellspring <subcommand>` through `WellspringCli`.

## Make targets and variables

| Target | Subcommand | Effect |
|---|---|---|
| `make remote-run` | `remote-run` | Preflight (settings, clean tree, quota), upload `request.json` and `source.tar.gz`, then launch. A live instance tagged `wellspring:run-id=$(REMOTE_RUN_ID)` is reused. A finished run ID (`checksums.sha256` present) is refused. An unfinished one is resumed if its stored `request.json` matches (spec FR-004). Prints the run ID and the hard-stop time, then returns; the job runs on its own. |
| `make remote-status` | `remote-status` | Table of every live instance tagged `wellspring:managed=true` in `$(REMOTE_REGION)`: run ID, profile, state, elapsed, estimated cost, plus `status.json` from storage. |
| `make remote-pull` | `remote-pull` | Download `<run>/` into `$(REMOTE_PULL_DIR)/<run-id>.tmp`, skipping checkpoints unless `REMOTE_PULL_CHECKPOINT=1`. Verify every downloaded file against `checksums.sha256`, rename atomically, then ingest into `$(MLFLOW_TRACKING_URI)`. Safe to re-run. Never deletes anything in storage (spec FR-017). |
| `make remote-down` | `remote-down` | Terminate every instance tagged with `$(REMOTE_RUN_ID)`, or with `REMOTE_RUN_ID=all-managed`. Volumes are deleted with the instance. |

| Variable | Default | Required by |
|---|---|---|
| `REMOTE_RUN_ID` | none | all except status |
| `REMOTE_STAGE` | none (`abliterate` \| `gguf` \| `ft-track-b`) | run |
| `REMOTE_PROFILE` | none (`dev` \| `finetune-dev` \| `prod`) | run |
| `REMOTE_REGION` | none | all |
| `REMOTE_SPEND_CAP_USD` | none | run |
| `REMOTE_STORAGE_URI` | none (`s3://bucket/prefix`) | run, pull |
| `REMOTE_INSTANCE_PROFILE` | none | run |
| `REMOTE_RED_RESTRICTED` | `0` | run, when the stage is `ft-track-b` (must be `1`) |
| `REMOTE_PULL_DIR` | `data/remote` (git-ignored) | pull |
| `REMOTE_PULL_CHECKPOINT` | `0` | pull (`1` also downloads model checkpoints) |
| `MLFLOW_TRACKING_URI` / `MLFLOW_EXPERIMENT_PREFIX` | none / `wellspring` | pull |

Stage arguments reuse the existing Makefile variable names (`MODEL`,
`MODEL_COMMIT`, `SEED`, `GGUF_QUANTS`, `FT_*`). Only names on the stage's
allow-list are forwarded.

Credentials come from the standard AWS chain (`AWS_PROFILE`, SSO, environment).
They are never read from repository files (FR-003).

## Exit codes

| Code | Meaning |
|---|---|
| 0 | success |
| 1 | refused before any spend (`MissingSettingError`, `DirtyTreeError`, `QuotaInsufficientError`, `RequestInvalidError`, `RunStateConflictError`: already finished, still shutting down, or a resume with a different stage, profile, stage arguments or repository commit) |
| 2 | cloud API failure (`CloudApiError`: no credentials, access denied, throttling; `CapacityUnavailableError` and other launch errors). Nothing is left running. |
| 3 | pull incomplete or failed verification (`ChecksumMismatchError`, missing `checksums.sha256`). Nothing is ingested. |

Every error names the setting, quota or file involved (Article VIII Rule 4).

## On-instance agent (internal, not operator-facing)

`python -m wellspring remote-agent --request s3://…/<run-id>/request.json`

1. Instance preflight (GPU count, GPU memory, free disk), then resolve the
   model commit on the Hub. If either fails: `end_reason=JOB_FAILED`, sync,
   shut down.
2. Run the stage's argv. `SYNC_MINUTES` heartbeats update `status.json` and
   sync the journal and logs.
3. Final sync, then write `manifest.json` and `checksums.sha256` last.
4. `shutdown -h now`. Termination and volume deletion follow from the launch
   settings (research R3).

## Tags (on the instance and its volumes)

`wellspring:managed=true`, `wellspring:run-id`, `wellspring:profile`,
`wellspring:stage`, `wellspring:repo-commit`.
