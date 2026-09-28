# Feature Specification: Hardware-Aware Export Dispatch (Stage A)

**Feature Branch**: N/A — work lands on the current branch (no feature branch)

**Created**: 2026-09-27

**Status**: Draft

**Input**: Hardware-aware export dispatch, Stage A (formerly a `ROADMAP.md` track).

## Context (current state)

- `make abliterate` produces one checkpoint. A human then runs `make convert-mlx`
  on a Mac and/or `make convert-gguf && make quantize-gguf` on a Linux/NVIDIA
  host, each by hand on whichever box has the right hardware (README Track A/B).
- Metaflow (`src/flow.py`, spec 002) cannot close this gap: `@batch`/`@kubernetes`
  are Linux-container-only, and a Mac can only launch a Metaflow run, never be a
  remote step target. MLX needs Apple Silicon, so the dispatch has to be designed
  for directly.
- Evidence (moved from `ROADMAP.md`): `docs.metaflow.org`'s driver-install docs
  describe launching `@kubernetes` runs *from* a Mac, never running a step *on*
  one. Choosing a different off-the-shelf orchestrator does not remove the
  constraint, because MLX requires Apple Silicon.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Manual fan-out against a saved checkpoint (Priority: P1)

An operator with a finished checkpoint runs one command that copies it to each
configured export host and runs that host's export there.

**Why this priority**: Removes the "which command on which box" choreography
without changing how abliteration runs.

**Independent Test**: With two SSH-reachable hosts (or two local fake hosts in
tests), one command produces the MLX output on the MLX host and the GGUF
outputs on the GGUF host.

**Acceptance Scenarios**:

1. **Given** a checkpoint and a host map naming an MLX host and a GGUF host,
   **When** the operator runs the dispatch command, **Then** the checkpoint is
   transferred to each host and each host runs only the export it supports.
2. **Given** a host that is unreachable, **When** dispatch runs, **Then** it fails
   before any transfer and names the host.
3. **Given** a transfer that completed earlier, **When** dispatch reruns,
   **Then** it verifies the remote copy by checksum and does not re-copy it.

### User Story 2 - Automatic dispatch when abliteration finishes (Priority: P2)

**Independent Test**: With dispatch enabled, a (fixture) abliteration run ends
by invoking the same dispatch mechanism as Story 1.

**Acceptance Scenarios**:

1. **Given** dispatch is enabled, **When** `make abliterate` succeeds, **Then**
   the same fan-out as Story 1 runs against the new checkpoint.
2. **Given** dispatch is not enabled (the default), **When** `make abliterate`
   succeeds, **Then** behaviour is unchanged from today.

### Edge Cases

- A host that can run both exports (for example, a Mac running GGUF too).
- A partial transfer interrupted mid-copy must never be exported.
- Provenance: the exported artifact's manifest must still trace back to the
  source checkpoint's hash, across machines.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: One mechanism MUST serve both triggers (manual and on abliteration
  completion); the trigger is a parameter, not a separate code path.
- **FR-002**: Targets MUST be addressed generically (an SSH destination plus the
  export(s) it runs), supplied by the operator, with no default hosts.
- **FR-003**: Transfer MUST use direct machine-to-machine copy (rsync/scp) or a
  shared filesystem path. No third-party storage dependency.
- **FR-004**: Every transfer MUST be verified by checksum before export starts.
- **FR-005**: Remote exports MUST invoke the existing `make` targets unchanged.
  Export parameter choice is out of scope.
- **FR-006**: The new `make` target(s) MUST carry their README row and
  `make help` line in the same change.
- **FR-007**: Tests MUST be hermetic (Article IX Rule 5). Remote hosts are
  faked with local directories and a fake `ssh`/`rsync`.

### Out of scope

- Cloud provisioning, autoscaling, or any ephemeral-compute provider.
- Object-storage backends (Stage B: `specs/024-export-object-storage`).

## Success Criteria *(mandatory)*

- **SC-001**: From a saved checkpoint, one command yields both export formats
  on their respective hosts with no further operator action.
- **SC-002**: A deliberately corrupted remote copy is detected and the export
  does not run.

## Assumptions

- Export hosts are reachable over SSH ahead of time and already have the repo
  set up (`make setup`).
