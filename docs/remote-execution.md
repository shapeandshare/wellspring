# Remote execution on AWS

`make remote-run` rents one GPU instance and runs a single pipeline stage on
it: `abliterate`, `gguf` or `ft-track-b`. The instance writes its outputs to S3
and terminates itself. The Mac never connects to it. Specification:
[`specs/027-remote-execution-aws/`](../specs/027-remote-execution-aws/spec.md).

> [!WARNING]
> This bills by the hour. The spend cap you pass becomes a hard
> `shutdown -h +N` on the instance. The instance is launched so that any
> shutdown also terminates it and deletes its disks. Check
> `make remote-status` anyway.

## One-time account setup

1. **Credentials.** Use any standard AWS mechanism, such as `aws configure sso`
   followed by `export AWS_PROFILE=<name>`. The tool never reads credentials
   from repository files.
2. **Region and network.** Choose a region where G-family instances are
   available, such as `us-east-1`. Instances launch into the region's
   **default VPC**, with no security-group ingress and no key pair. They need
   outbound internet (Hugging Face, PyPI, apt), which default-VPC subnets
   provide. An account without a default VPC is not supported yet.
3. **Quota.** New accounts start with **0** vCPUs for "Running On-Demand G and
   VT instances". In the
   [Service Quotas console](https://console.aws.amazon.com/servicequotas/home/services/ec2/quotas/),
   request:
   - 4 vCPUs for the `dev` profile (g5.xlarge);
   - 8 vCPUs for `finetune-dev` (g5.2xlarge);
   - 48 vCPUs for `prod` (g6e.12xlarge).

   `make remote-run` checks the quota before launching and names the shortfall.
4. **Bucket.** Create an S3 bucket for run outputs. The tool **never deletes**
   anything in it (spec 027 FR-017), so add a lifecycle rule if you want old
   runs to expire.
5. **Instance role.** Create an IAM role with an instance profile that the
   instance can assume. Scope it to the bucket prefix you will pass as
   `REMOTE_STORAGE_URI`:

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {"Effect": "Allow", "Action": ["s3:GetObject", "s3:PutObject"],
        "Resource": "arn:aws:s3:::<bucket>/<prefix>/*"},
       {"Effect": "Allow", "Action": "s3:ListBucket",
        "Resource": "arn:aws:s3:::<bucket>", "Condition": {"StringLike": {"s3:prefix": "<prefix>/*"}}}
     ]
   }
   ```

   Your own (launcher) credentials need `ec2:RunInstances`,
   `ec2:DescribeInstances`, `ec2:TerminateInstances`, `ec2:CreateTags`,
   `ec2:DescribeImages`, `iam:PassRole` for that role, `ssm:GetParameter`,
   `servicequotas:ListServiceQuotas`, and the same S3 access. A just-created
   role can take a minute to become usable. If the first launch fails with
   `InvalidParameterValue` naming the instance profile, retry.
6. **Budget alert.** Create an AWS Budgets alert for the account. A monthly
   cap is deliberately not built into the tool (spec 027 clarification).

## Running

```bash
export AWS_PROFILE=... REMOTE_REGION=us-east-1
export REMOTE_STORAGE_URI=s3://<bucket>/wellspring REMOTE_INSTANCE_PROFILE=<name>
make remote-run REMOTE_RUN_ID=rehearsal-1 REMOTE_STAGE=abliterate REMOTE_PROFILE=dev \
     REMOTE_SPEND_CAP_USD=5 MODEL=HuggingFaceTB/SmolLM2-135M-Instruct \
     MODEL_COMMIT=12fd25f77366fa6b3b4b768ec3050bf629380bac
make remote-status
make remote-pull REMOTE_RUN_ID=rehearsal-1 MLFLOW_TRACKING_URI=sqlite:///mlflow.db
```

- The source sent to the instance is `git archive HEAD`, so a dirty working
  tree is refused.
- The instance downloads model weights from Hugging Face itself, after
  resolving `MODEL_COMMIT` (or `main`) to an exact SHA. That SHA is recorded
  in the manifest as `model_commit_resolved`. Only public models work in this
  phase.
- The instance runs `make setup`, which installs `requirements.txt`, not
  `requirements-lock.txt`: the lock is frozen on macOS and includes
  Apple-only packages. The exact package set used is recorded in the manifest
  as `package_set_sha256`.
- The bootstrap installs `uv` with `curl -LsSf https://astral.sh/uv/install.sh | sh`.
  This trusts astral.sh at launch time.
- The spend cap converts to runtime with 3 minutes taken off for boot. The
  stage is then stopped the profile's sync margin (10 min for `dev` and
  `finetune-dev`, 30 min for `prod`) before the hard shutdown, so outputs and
  the checkpoint upload finish in time. Size the cap for a whole run plus
  that margin.
- A run that ends any way other than `completed` uploads no checkpoint, since
  its weights would be partial. Its journal, logs and manifest are still
  uploaded.
- Running `remote-run` again with the same `REMOTE_RUN_ID`:
  - if the instance is still live, it is reused;
  - if the run finished, the command is refused;
  - if the run was interrupted, it resumes from the synced outputs, and only
    the spend cap may differ.

  Resuming does not continue Heretic's own trial search:
  `src/scripts/heretic_automate.exp` answers Heretic's recovery prompt with
  "start from scratch".

## Red-only material

`REMOTE_STAGE=ft-track-b` writes the answer key, trigger and training data to
the bucket. It requires `REMOTE_RED_RESTRICTED=1`. Setting it is your
statement that the bucket and instance role are accessible to Red only
(constitution Article XV Rule 2). The flag is recorded in the run manifest,
and the trigger is redacted from the manifest's `stage_args`. Blue still gets
models only through `make ft-handover`.

## What was not verified

At the time of writing, no real AWS run had happened. These are untested:

- the `uv` Python 3.14 install and its `python3.14` link on the image;
- launch-to-job-start time;
- whether each stage's pipeline command succeeds on the Linux image.

The dev rehearsal in
[quickstart §2](../specs/027-remote-execution-aws/quickstart.md) is the first
real test.
