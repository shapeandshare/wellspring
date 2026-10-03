# Feature Specification: Remote Execution on AWS (Phase A — one rented GPU instance)

**Feature Branch**: N/A — work lands on the current branch (no feature branch)

**Created**: 2026-10-02

**Status**: Draft

**Input**: Run the Track B pipeline (Heretic abliteration, GGUF export, Track B
fine-tuning, evaluation) on one rented AWS GPU instance launched from the Mac.
Pull the results back and ingest them into local MLflow. The Mac keeps only the
stages that need Apple Silicon. Decisions in
`vault/decisions/2026-10-02-compute-this-mac-plus-one-cloud.md`.

## Clarifications

### Session 2026-10-02

- Q: Where does compute run? → A: Remote-first. One cloud, AWS. The Mac keeps
  only MLX export, the MLX quantization study and Track A fine-tuning, and acts
  as the launcher. Local abliteration runs are abandoned.
- Q: How remote? → A: Phase A is one rented instance that runs the existing
  Track B pipeline as-is. Per-step remote execution (Metaflow `@batch`) is
  phase C. Phase C gets its own later spec, because it must explicitly supersede
  spec 002's no-remote-decorator decision (002 research §2, FR-004).
- Q: Spend caps? → A: Required for every run. A monthly cap is optional on top.
- Q: May Red-only fine-tuning material run on hosted compute? → A: Yes, under
  constitution Article XV Rule 2: only where access is restricted to Red. This
  departs from spec 024 FR-004 (never upload Red-only material). Amend 024 when
  it is next touched.
- Q: First target? → A: Production abliteration of `Qwen/Qwen3.6-35B-A3B`.
  Production fine-tuning follows once spec 011 closes the `train_torch` gaps
  (see Out of Scope).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Abliterate the production model remotely (Priority: P1)

From the Mac, the operator chooses a production instance profile and a spend
cap, and starts the run. A decensored checkpoint, Heretic's trial journal and
the run manifest end up on the Mac and in local MLflow. The instance is gone
afterwards.

**Why this priority**: The production model cannot be abliterated on the Mac
in practical time (MPS QR is pathologically slow, and CPU-only is multi-day).
It is the first workload with no local path.

**Independent Test**: With a fake provider and a local fake object store (no
AWS, no network), a run goes through ensure → run → sync → pull → ingest →
release. It leaves one MLflow row per fake trial and zero live fake instances.

**Acceptance Scenarios**:

1. **Given** a profile, a region, a spend cap and AWS credentials from the
   standard AWS environment, **When** the operator starts a remote abliteration,
   **Then** one instance is provisioned. It downloads the weights from Hugging
   Face itself and runs the existing abliteration target. Its outputs are copied
   to operator-supplied storage with checksums. The Mac pulls and verifies them,
   ingests the journal into MLflow, and the instance and its volumes are deleted.
2. **Given** no spend cap, region or storage URI, **When** a remote run is
   requested, **Then** it fails before provisioning anything and names the
   missing setting. There are no defaults.
3. **Given** the account lacks the vCPU quota the profile needs, **When** a run
   is requested, **Then** it fails before provisioning, naming the quota, the
   vCPUs required and the vCPUs available.

---

### User Story 2 - The instance can never be orphaned or overspend (Priority: P1)

Whatever happens (success, a failing step, the cap being reached, the Mac
sleeping or losing its connection), the instance shuts itself down and is
deleted, and total spend stays within the cap.

**Why this priority**: A multi-GPU instance left running unattended keeps
billing by the hour. This is a safety property, not a convenience.

**Independent Test**: With the fake provider and a fake clock, each of the
following leaves zero live instances: idle timeout, maximum runtime derived from
the cap, a crashing job, and a launcher that disappears mid-run. In each case
whatever outputs existed are synced first.

**Acceptance Scenarios**:

1. **Given** a running job, **When** projected spend reaches the cap, **Then**
   the instance syncs what it has, records the reason in the manifest and
   terminates.
2. **Given** the Mac goes offline mid-run, **When** the job ends or the idle
   timeout passes, **Then** the instance terminates itself without the Mac.
3. **Given** `ensure` is run twice for the same run, **When** an instance
   already exists, **Then** it is reused, not duplicated.
4. **Given** any state, **When** the operator asks for status, **Then** every
   live tagged instance is listed with its profile, elapsed time and estimated
   cost so far.

---

### User Story 3 - Dev-profile GGUF export and Track B dev fine-tune remotely (Priority: P2)

Using the small dev profile, the operator runs GGUF convert/quantize and the
Track B fine-tune of the dev model remotely. The results come back the same way
as in Story 1.

**Why this priority**: This is the cheap rehearsal of the whole path. It also
produces spec 011's first Track B timing and memory figures.

**Independent Test**: Same as Story 1, with fake GGUF and fine-tune commands.
A fine-tune run's Red-only outputs land only in the Red-restricted location.

**Acceptance Scenarios**:

1. **Given** the dev profile, **When** a remote fine-tune runs, **Then** the
   lineup, the recipe stamps and the QA verdict are pulled back. The handover
   still goes through `make ft-handover`'s secrecy check, unchanged.
2. **Given** an interrupted run, **When** it is resumed with the same run ID,
   **Then** it continues from the last synced Optuna journal or Metaflow state
   rather than starting over.

---

### Edge Cases

- No capacity for the instance type in the chosen region or AZ: fail with the
  provider's reason. Never silently switch to another instance type, because
  that changes the hardware class (FR-009).
- Partial or corrupt pull: verify checksums before ingesting. Nothing is
  ingested from a run that failed verification.
- The job fails on the instance: the logs and manifest are still synced, the
  instance still terminates, and the run is recorded as failed.
- An MLX stage is requested remotely: refused by the existing hardware guard.
  No Linux path exists.
- The instance's disk is too small for the profile's model: the profile
  declares its disk size, and preflight on the instance fails before download.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature MUST be driven through `make` targets: bring up,
  run, status, pull and tear down, each documented in `README.md` and
  `make help` in the same change (Article VII).
- **FR-002**: Instance profiles MUST be declared in one place. Each profile
  states its instance type, GPU count and memory, disk size, and the stages it
  may run. Initial profiles: dev (g5.xlarge), finetune-dev (g5.2xlarge), and
  one production profile, g6e.12xlarge (4× L40S, 192 GB). That production
  choice is a candidate, confirmed only by the peak-VRAM measurement from the
  dev rehearsal. Larger instance families (p4d/p5) are added only if a
  measurement shows they are required.
- **FR-003**: Region, spend cap and storage URI MUST be supplied by the
  operator, with no defaults. Credentials MUST come from the standard AWS
  environment or profile, never from repository files.
- **FR-004**: Bringing an instance up MUST be idempotent. An instance is
  identified by a run tag, and repeating the request reuses the existing one.
- **FR-005**: Teardown MUST be guaranteed without the Mac. The instance MUST
  terminate itself on job completion, after an idle timeout, and at a maximum
  runtime derived from the spend cap and the profile's hourly price. Releasing
  it MUST also delete its volumes.
- **FR-006**: Model weights MUST be downloaded on the instance from Hugging
  Face. They are never uploaded from the Mac. The resolved model commit is
  recorded in the manifest.
- **FR-007**: Before any teardown, including cap- and idle-triggered ones, the
  instance MUST copy its outputs (checkpoint, Optuna journal, logs, manifest)
  to the operator-supplied storage, with checksums. It MUST also sync the
  journal periodically during the run, so that an interrupted run loses at most
  the work since the last sync.
- **FR-008**: Pulling MUST verify checksums, then ingest into local MLflow
  idempotently. Running it twice gives the same row count, reusing the
  journal-ingestion pattern of `log_heretic_to_mlflow.py`.
- **FR-009**: Every run and trial MUST be tagged with its hardware class
  (profile and instance type). One Optuna study MUST NOT contain trials from
  more than one hardware class.
- **FR-010**: The manifest MUST record the region, instance type, machine
  image ID, GPU driver and CUDA versions, a hash of the installed package set,
  and the repository commit, alongside the existing provenance fields
  (Article I).
- **FR-011**: Red-only fine-tuning material MAY exist on the instance and in
  the operator storage only if access to both is restricted to Red
  (Article XV Rule 2). Nothing reaches Blue except through `make ft-handover`.
  This departs from spec 024 FR-004, which MUST be amended when 024 is next
  touched.
- **FR-012**: Preflight on the Mac MUST check the region's vCPU quota for the
  profile before provisioning. Preflight on the instance MUST check disk, GPU
  count and memory before downloading weights (Article VIII Rule 4).
- **FR-013**: Status MUST list every live tagged instance with its profile,
  elapsed time and estimated cost.
- **FR-014**: Stages that require Apple Silicon MUST refuse to run remotely.
- **FR-015**: `make test` MUST stay hermetic, using a fake provider and a local
  fake object store. It must never make a cloud call (Article IX).
- **FR-016**: The remote job MUST run a repository pipeline command, so that
  replacing the abliteration backend later does not change this feature.

### Key Entities

- **Instance profile**: a name, instance type, GPU count and memory, disk
  size, hourly price, and the stages it may run.
- **Remote run**: a run ID (the tag), profile, region, spend cap, storage URI,
  state (provisioning / running / syncing / terminated / failed), the reason it
  ended, and accrued cost.
- **Run manifest**: the provenance record of a remote run (FR-010), plus the
  checksum list of its synced outputs.

## Success Criteria *(mandatory)*

- **SC-001**: After a one-time account setup, the operator gets a decensored
  production checkpoint onto the Mac and into MLflow using only `make`
  commands, with no cloud-console steps.
- **SC-002**: Across every outcome in Story 2, zero tagged instances remain
  within the idle timeout plus 10 minutes.
- **SC-003**: The actual spend of a run never exceeds its cap by more than one
  billing increment of the profile's instance.
- **SC-004**: Pulling and ingesting the same run twice yields identical MLflow
  row counts.
- **SC-005**: Every pulled artifact can be traced to its model commit,
  repository commit, instance type, region and machine image from the
  manifest alone.

## Assumptions

- An AWS account exists. The vCPU quota for the chosen profiles must be
  requested beforehand. Only the G instance family is needed: a small amount
  for the dev rehearsal, more for g6e when production starts. Quota is
  requested when it is first needed, not upfront. Current limits are
  unverified for this account.
- The README's "320 GB+ VRAM" production figure is unmeasured. The Qwen3.6
  weights are about 66 GB in bf16 (measured from the local shards).
- On-demand instances to start with. Spot is a later option, because
  interruptions complicate guaranteed sync.
- A GPU machine image with NVIDIA drivers is available. Python 3.14 is
  installed on the instance by the setup step.
- The AWS client library (Apache-2.0) becomes a direct dependency, flagged per
  Article II.
- Licence compliance for running a given model on AWS is the operator's
  responsibility. The manifest makes it auditable.

## Out of Scope

- Per-step remote execution with Metaflow `@batch` or Kubernetes (phase C,
  its own spec, superseding spec 002's decision).
- Production-scale fine-tuning. `train_torch` loads float32 onto a single
  device (about 140 GB for 35B) and saves a text-only model without the vision
  tower. Both are spec 011's to fix.
- Clouds other than AWS, spot instances, and local devices other than this Mac.
- Spec 026's parallel outer-trial fan-out (phase C).
