# Feature Specification: Dataset Search over an Approved Dataset List

**Feature Branch**: N/A — work lands on the current branch (no feature branch)

**Created**: 2026-09-27

**Status**: Draft — P1 gated on a feasibility spike; P2 gated on P1 evidence and spec 026's budget

**Input**: Dataset-variation item. Decisions in
`vault/decisions/2026-09-27-dataset-search-decisions.md`.

## Context (current state)

- Spec 001 already searches calibration **sample counts**: `CALIB_SAMPLES` in the
  MLX study (awq + multimodal only) and `CALIB_TEXT_SAMPLES` (50–100) in the GGUF
  study. This spec does not duplicate that.
- Dataset identities are pinned Makefile variables (`GOOD_PROMPTS_DATASET` /
  `_COMMIT`, `BAD_PROMPTS_*`, calibration sources). Changing one is a manual edit,
  and dataset licences in `THIRD_PARTY_NOTICES.md` are also maintained by hand.
  `make notices` covers pip packages only.

## Clarifications

### Session 2026-09-27

- Q: What varies? → A: Which rows are drawn from pinned datasets, plus swapping
  datasets from an approved list whose entries are pinned by commit and
  licence-checked. Adding an approved dataset must be easy (one command).
- Q: Which stage? → A: Both, split by priority: P1 export calibration data
  (builds on spec 001's studies); P2 abliteration prompts (shares spec 026's
  search loop and budget).
- Q: Evidence before building? → A: P1 is gated on a spike: a 5-trial study
  comparing two approved datasets, built only if the gap between them exceeds the
  run-to-run noise. P2 is gated on P1 showing an effect and on spec 026's budget.

## User Scenarios & Testing *(mandatory)*

### User Story 0 - Approve a dataset in one command (Priority: P1, prerequisite)

**Independent Test**: With a faked Hub API, the command adds an entry with a
pinned commit and licence, and refuses an unlicensed dataset.

**Acceptance Scenarios**:

1. **Given** a dataset ID, **When** the operator runs the approve command, **Then**
   the current commit is resolved and pinned, the licence is read, the entry is
   added to the approved list, and the dataset section of
   `THIRD_PARTY_NOTICES.md` is regenerated from the list.
2. **Given** a dataset with no or an unrecognised licence, **When** it is approved,
   **Then** the command refuses and names the problem.
3. **Given** a non-commercial licence (for example CC-BY-NC-4.0), **When** it is
   approved, **Then** it is accepted but flagged in the list and the notices.

### User Story 1 - Calibration-data search (Priority: P1)

**Independent Test**: A two-trial MLX or GGUF study with the dataset dimension
enabled logs the chosen dataset and rows as trial params.

**Acceptance Scenarios**:

1. **Given** the spike passed, **When** a quantization study runs with the dataset
   dimension enabled, **Then** each trial picks an approved calibration dataset
   and a row selection, and both are recorded in MLflow and the trial manifest.
2. **Given** the dimension is disabled (the default), **When** a study runs, **Then**
   behaviour is identical to spec 001.

### User Story 2 - Abliteration-prompt search (Priority: P2)

**Acceptance Scenarios**:

1. **Given** P1 evidence and a spec 026 budget, **When** the outer search runs,
   **Then** each trial may choose approved good/bad prompt datasets, recorded in
   provenance as Heretic inputs.

### Edge Cases

- The `/first-rows` API caps at 100 rows, so a row-selection search needs the full
  dataset fetched at its pinned commit (or the cap documented as the search range).
- Held-out evaluation datasets must never be selectable as calibration inputs
  (they must stay disjoint from what they score).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The approved list MUST be the single source of truth. The dataset
  section of `THIRD_PARTY_NOTICES.md` is generated from it, never hand-edited
  (AGENTS.md §3).
- **FR-002**: Every entry MUST carry a dataset ID, a pinned commit, a licence, and
  a role (calibration-image, calibration-text, good-prompts, bad-prompts).
- **FR-003**: Searches MUST only select entries whose role matches the input.
- **FR-004**: The spike's result MUST be recorded as a vault reference note before
  User Story 1 is implemented.
- **FR-005**: Existing Makefile defaults MUST be present in the approved list, so
  current behaviour is one valid point in the search.
- **FR-006**: Tests are hermetic; the Hub API is faked.

## Success Criteria *(mandatory)*

- **SC-001**: Approving a new dataset takes one command and no manual file edits.
- **SC-002**: Every trial's dataset choice is traceable to a pinned commit and a
  licence.

## Assumptions

- Licence acceptance policy (which licences are allowed) is decided in plan.md;
  the default accepts known licences and flags non-commercial ones.
