# Quickstart: validating spec 027

## 1. Offline (no AWS account): always run

```bash
make test
```

Expected: green. The new tests use a fake instance provider, a local-directory
object store and a fake clock (FR-015). They cover:

- Story 1: run → sync → pull → ingest, giving one MLflow row per fake trial,
  and the same count on a second pull (SC-004).
- Story 2: idle timeout, cap reached, job crash and launcher disappearing each
  leave zero fake instances (SC-002). The `max_minutes` arithmetic is checked
  against `spend_cap / hourly`.
- Refusals: a missing setting, a dirty tree, insufficient quota, an MLX stage,
  or `ft-track-b` without `REMOTE_RED_RESTRICTED=1` each exit 1 before any
  provider call.
- Pull: a corrupted file, or a missing `checksums.sha256`, exits 3 and ingests
  nothing.
- The `Ec2Sdk` request shapes are checked with `botocore.stub.Stubber`
  (no network): `InstanceInitiatedShutdownBehavior=terminate`,
  `DeleteOnTermination=true`, tags, user-data starting with `shutdown -h +N`.

## 2. Dev rehearsal (needs an AWS account, G-family quota ≥ 4 vCPU, a bucket, an instance profile)

```bash
export AWS_PROFILE=… REMOTE_REGION=us-east-1
export REMOTE_STORAGE_URI=s3://<bucket>/wellspring REMOTE_INSTANCE_PROFILE=<name>
make remote-run REMOTE_RUN_ID=rehearsal-1 REMOTE_STAGE=abliterate REMOTE_PROFILE=dev \
     REMOTE_SPEND_CAP_USD=5 MODEL=HuggingFaceTB/SmolLM2-135M-Instruct \
     MODEL_COMMIT=12fd25f77366fa6b3b4b768ec3050bf629380bac
make remote-status REMOTE_REGION=us-east-1      # repeat until the run is gone
make remote-pull REMOTE_RUN_ID=rehearsal-1 MLFLOW_TRACKING_URI=sqlite:///mlflow.db
make remote-pull REMOTE_RUN_ID=rehearsal-1 MLFLOW_TRACKING_URI=sqlite:///mlflow.db   # same row count
```

Expected:

- The status list is empty after the job ends.
- The AWS console or CLI shows no instance or volume with the run tag.
- `manifest.json` names the AMI, driver, CUDA version, repository commit and
  `hardware_class=dev:g5.xlarge`.
- The billing for the run is ≤ $5.

Also record **peak VRAM** from the agent's `nvidia-smi` log. That number
decides whether `prod` (g6e.12xlarge) stops being a candidate.

## 3. Teardown drill (dev profile)

Launch with `REMOTE_SPEND_CAP_USD=0.25` and a model that takes longer than the
resulting `max_minutes`.

Expected: the instance terminates at or before the cap with
`end_reason=SPEND_CAP` (or `BACKSTOP`). The journal synced so far can be
pulled.
