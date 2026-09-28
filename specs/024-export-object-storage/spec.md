# Feature Specification: Object-Storage Transfer for Export Dispatch (Stage B)

**Feature Branch**: N/A — work lands on the current branch (no feature branch)

**Created**: 2026-09-27

**Status**: Draft — blocked on its trigger (below)

**Input**: Export dispatch Stage B. Decisions in
`vault/decisions/2026-09-27-export-object-storage-decisions.md`. Extends
`specs/013-export-dispatch`.

## Trigger (blocking)

Build this only when the first export target exists that cannot be reached over
SSH ahead of time (for example, ephemeral or on-demand compute). Until then,
013's direct transfer covers every known host (Article VI).

## Clarifications

### Session 2026-09-27

- Q: Spec now or later? → A: Spec now, blocked on the trigger above.
- Q: Where may checkpoints be stored? → A: Any storage provider, chosen and
  supplied by the operator. The constitution's provenance and spec 003's Red-only
  secrecy rules still apply.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dispatch through object storage (Priority: P1)

**Independent Test**: With a local fake object store, 013's dispatch command
selects the object-storage backend and an export host fetches and verifies the
checkpoint.

**Acceptance Scenarios**:

1. **Given** an operator-supplied storage URI, **When** dispatch runs, **Then** the
   checkpoint is uploaded once and each export host downloads it and verifies it
   by checksum before exporting.
2. **Given** no storage URI, **When** the object-storage backend is selected,
   **Then** dispatch fails fast naming the missing setting (no default).
3. **Given** a checksum mismatch after download, **When** export would start,
   **Then** it does not start.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Object storage MUST be an additional backend of 013's single
  dispatch mechanism, not a separate command.
- **FR-002**: The backend MUST be provider-agnostic, addressed by a URI the
  operator supplies. No provider, bucket or credential defaults.
- **FR-003**: Every upload, download and deletion MUST be recorded in the
  provenance manifest with the object URI and checksum (Article I).
- **FR-004**: Red-only fine-tuning material (answer key, trigger, training data)
  MUST NEVER be uploaded. Upload refuses a tree containing it, and a planted-leak
  test proves the refusal can fail (Article VIII Rule 5).
- **FR-005**: Credentials MUST come from the provider's standard environment or
  config, never from repository files.
- **FR-006**: Tests MUST be hermetic, using a local fake store.

## Success Criteria *(mandatory)*

- **SC-001**: Switching between direct transfer and object storage changes only
  the storage URI setting.

## Assumptions

- Licence compliance for storing a given model's weights with a given provider is
  the operator's responsibility; the provenance record makes it auditable.
