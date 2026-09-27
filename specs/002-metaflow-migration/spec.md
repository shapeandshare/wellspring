# Feature Specification: Full Pipeline Orchestration via Metaflow

**Feature Branch**: `[002-metaflow-migration]`

**Created**: 2026-09-26

**Status**: Draft

**Input**: User description: "we need to run this fully in metaflow
regardless what libraries we use - we are free to do whatever we need"

## Clarifications

### Session 2026-09-26

- Q: Should this feature keep the Mac-native compression search in scope (as a documented exception requiring a person to start that one stage directly on a Mac), or should it drop that search from Metaflow's scope entirely? → A: Keep it in scope as a documented exception (Option A) — the orchestrated definition covers all four stages including the Mac-native search; that one stage's hardware requirement is disclosed and enforced (FR-005), not worked around or dropped.
- Q: Should this feature target the production model or the cheap dev-cycle model as the checkpoint it's built and verified against? → A: Dev-cycle model for build/verification (Option B), but with an added constraint: the orchestration itself MUST be scale-agnostic — parameterized so the identical flow definition runs against the production model on larger compute the moment verification against the dev-cycle model passes, with no additional engineering required to "scale up." This is not "dev-only, production deferred" — it is "verify cheaply, ship production-capable from day one."
- Q: Should the Makefile stay the entry point (each target internally starting the corresponding Metaflow run), or be replaced by direct Metaflow commands? → A: Keep Makefile targets as the entry point for dev-cycle/routine use (Option A) — BUT operators MUST also be able to invoke the same flow definition directly via Metaflow's own CLI, bypassing `make` entirely, for production runs. Both are first-class, sanctioned entry points to the identical flow definition — the Makefile is not the only supported way to start a run; it is the default/convenient one for everyday use.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run the decensoring stage as one flow (Priority: P1)

An operator wants to kick off the model-decensoring stage (today: a
Makefile target driving an automated interactive tool, followed by a
separate command to record its results for tracking) as a single
orchestrated run, instead of two hand-sequenced commands.

**Why this priority**: This is the smallest slice that delivers real value
on its own — one orchestrated run instead of two manually-ordered
commands — and every other stage in this pipeline builds on this stage's
output artifact.

**Independent Test**: Start one orchestrated run targeting the decensoring
stage — via the existing `make` target — and confirm it produces the same
decensored checkpoint and the same tracked trial records as today's
two-command sequence, with no manual second command required. Separately,
confirm the identical orchestrated run can also be started by invoking the
orchestration mechanism's own command line directly, without going
through `make` at all, producing the same result.

**Acceptance Scenarios**:

1. **Given** a source model identifier and its existing configuration
   (seed, dataset commits, hardware placement), **When** an operator
   starts one orchestrated run for the decensoring stage, **Then** it
   completes with a saved decensored checkpoint and that run's trial
   results already recorded for tracking — no second, separate command
   required to record them.
2. **Given** the decensoring stage still requires a decision partway
   through (which parameter combination to keep), **When** the
   orchestrated run reaches that point, **Then** it resolves that decision
   automatically, exactly as today's automation already does, without
   requiring a person to be present at a terminal.

---

### User Story 2 - Both export/compression searches run as one orchestrated pipeline (Priority: P2)

An operator wants the two independent, already-existing compression
searches (one per export format) to be started, tracked, and resumed
through the same orchestration mechanism as the decensoring stage, rather
than as two more separately-invoked commands with their own bespoke
parameter bookkeeping.

**Why this priority**: Delivers the core "one orchestration mechanism
covers the whole pipeline" value this feature exists for, building
directly on User Story 1's output.

**Independent Test**: Starting from one already-decensored checkpoint,
start the orchestrated run for both compression searches (each on the
physical machine its own hardware requirement demands); confirm both
searches produce the same tracked results as today's separately-invoked
searches, with the orchestration mechanism — not manual bookkeeping —
supplying each search's parameters and archive locations.

**Acceptance Scenarios**:

1. **Given** one decensored checkpoint, **When** an operator starts the
   orchestrated run for the Mac-native compression search on
   Mac/Apple-Silicon hardware, **Then** it runs and tracks results exactly
   as today's equivalent command does, with its parameters and archive
   location supplied by the orchestration mechanism rather than
   separately re-typed by the operator.
2. **Given** the same checkpoint, **When** an operator starts the
   orchestrated run for the broadly-compatible compression search on
   hardware meeting that search's own requirements, **Then** the same
   holds for that search — including reusing the one-time format
   conversion step rather than repeating it.
3. **Given** both searches are independent per the pipeline's existing
   design, **When** either search's orchestrated run is started, **Then**
   it MUST NOT read, write, or otherwise depend on the other search's
   inputs, tooling, or outputs.

---

### User Story 3 - Interrupted runs resume without repeating finished work (Priority: P3)

An operator whose orchestrated run was interrupted (crash, manual stop,
machine restart) wants to restart it and have it continue from wherever it
left off, without repeating already-finished, expensive steps.

**Why this priority**: Extends this pipeline's existing per-stage
resumability (each compression search already resumes its own attempts)
into a single, whole-pipeline-level guarantee, once Stories 1 and 2 exist
to make a "whole pipeline run" a real thing to resume.

**Independent Test**: Start an orchestrated run, interrupt it after one
stage completes, restart it, and confirm the already-completed stage's
output is reused rather than regenerated, while the remaining stages still
run to completion.

**Acceptance Scenarios**:

1. **Given** an orchestrated run that completed its decensoring stage and
   was then interrupted before starting the compression searches,
   **When** the operator restarts the run, **Then** the decensoring stage
   is not repeated — its already-produced checkpoint is reused directly.
2. **Given** an orchestrated compression search that had already completed
   several attempts before being interrupted, **When** it is resumed,
   **Then** it continues from its prior progress rather than restarting
   its attempt count from zero (matching this pipeline's existing
   per-search resumability guarantee).

---

### Edge Cases

- What happens when an operator starts the Mac-native compression search's
  orchestrated run on hardware that is not Mac/Apple-Silicon? → MUST fail
  with a clear, specific error naming the unmet hardware requirement,
  before attempting any expensive work — never a generic crash, and never
  a silent no-op.
- What happens if the underlying tool a stage depends on (the decensoring
  tool, the format-conversion tool, the quantization tool) itself fails or
  crashes mid-stage? → The orchestration mechanism MUST surface that
  failure as a failed stage with the underlying tool's own error
  preserved, not swallowed or replaced with a generic message.
- What happens if an operator tries to run the two independent compression
  searches' orchestrated stages on the same shared machine at the same
  time? → Governed by this pipeline's existing compute-topology behavior
  (sequential by default on shared compute, concurrent only when opted
  into on dedicated compute) — this feature MUST preserve that behavior,
  not bypass it.
- What happens to a compression search's already-archived attempt files
  when its orchestrated stage is resumed or re-run? → They MUST remain
  exactly as protected as they are today — never automatically deleted,
  never silently overwritten.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide one orchestrated definition covering
  every stage of this pipeline (decensoring, tracking the decensoring
  stage's results, both compression searches) that an operator can start,
  in place of today's separate `make` invocations for each stage.
- **FR-001a**: This orchestrated definition MUST be startable through two
  independent, equally-supported entry points: (a) the existing `make`
  targets, kept as the default/convenient entry point for everyday and
  dev-cycle use (each target internally starts the corresponding
  orchestrated run rather than running its current direct logic), and (b)
  the orchestration mechanism's own native command-line interface, invoked
  directly without going through `make` at all — required for production
  runs, where an operator MUST be able to bypass the Makefile entirely.
  Both entry points MUST start the identical underlying definition — never
  two divergent implementations of the same stage.
- **FR-002**: The decensoring stage, when started through this
  orchestration mechanism, MUST resolve its mid-run decision (which
  parameter combination to keep) automatically, without requiring a person
  present at a terminal — matching today's existing automated behavior
  exactly, not a new interactive mechanism.
- **FR-003**: The orchestrated definition MUST fan out from one decensored
  checkpoint into the two independent compression searches as separate
  stages, and MUST fan them back together only insofar as reporting on
  both — never blending their inputs or outputs.
- **FR-004**: Each compression search's stage MUST remain exactly as
  independent from the other as the pipeline's existing design requires:
  no shared calibration input, no shared tooling, no shared output
  location, and no behavior change to one triggered by a change to the
  other.
- **FR-005**: The system MUST NOT allow the Mac-native compression
  search's stage to be executed on hardware other than Mac/Apple-Silicon —
  attempting to do so MUST fail clearly, immediately, and by name, before
  any expensive work begins.
- **FR-006**: Every existing, already-implemented pipeline guarantee this
  orchestration wraps — idempotent result-tracking, per-search
  resumability, atomic artifact writes, environment-only credential
  handling, never-auto-deleted search archives, compute-topology-aware
  sequential/concurrent execution — MUST continue to hold exactly as it
  does today. This feature orchestrates those existing behaviors; it MUST
  NOT weaken, bypass, or re-implement them differently.
- **FR-007**: An orchestrated run interrupted partway through MUST be
  resumable without repeating any stage whose output already exists and is
  valid, and MUST NOT silently discard or duplicate a stage's
  already-completed work upon resume.
- **FR-008**: The system MUST record, for every orchestrated run, enough
  information to trace which run — and which parameters — produced any
  given artifact, consistent with this pipeline's existing chain-of-custody
  requirement that every artifact be traceable to exactly what produced
  it.
- **FR-009**: The orchestration mechanism's own internal record-keeping
  MUST NOT become the sole record of an artifact's provenance for
  artifacts that non-orchestration tooling (the decensoring tool's own
  export format, the quantization tools) must read directly from disk —
  those artifacts' existing on-disk provenance sidecars remain the
  authoritative, tool-independent record; the orchestration mechanism's own
  run/step tracking is a supplementary index, not a replacement.
- **FR-010**: The existing experiment-tracking destination (where trial
  parameters and quality/decensoring scores are recorded for comparison
  across attempts) MUST continue to receive exactly the records it does
  today; this feature MUST NOT remove or reduce what gets tracked there.
- **FR-011**: The orchestrated pipeline definition MUST be scale-agnostic:
  the same definition that runs correctly against the cheap dev-cycle
  model on modest hardware MUST also run against the full production
  model on production-scale compute, driven only by which model/hardware
  parameters an operator supplies at start time — never by a different
  flow definition, a code fork, or additional engineering work performed
  after dev-cycle verification passes.

### Key Entities

- **Orchestrated run**: One end-to-end (or resumed, partial) execution of
  the pipeline definition — has an identity distinct from other runs, and
  produces or reuses a decensored checkpoint plus the results of whichever
  compression-search stages it covers.
- **Stage**: One orchestrated unit of work within a run (decensoring,
  result-tracking, one compression search) — may complete, fail, or be
  skipped on resume because its output already exists.
- **Hardware requirement**: A stage-level constraint (e.g.
  "Mac/Apple-Silicon only") that the orchestration mechanism MUST check
  before attempting that stage's work, independent of which run or which
  parameters are in play.
- **Entry point**: One of the two sanctioned ways an operator starts an
  orchestrated run — the existing `make` targets (default, dev-cycle-
  oriented) or the orchestration mechanism's own native command line
  (required for production use, independent of `make`). Both entry points
  start the same underlying definition; neither is a distinct
  implementation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator can go from "nothing started" to "decensored
  checkpoint produced and its results tracked" by starting exactly one
  orchestrated run for that stage — zero separate, manually-sequenced
  commands required beyond that one start.
- **SC-002**: An operator can go from one decensored checkpoint to both
  compression searches' results tracked by starting the orchestrated run
  for each search on its required hardware, without manually re-deriving
  or re-typing that search's parameters or archive location by hand.
- **SC-003**: Restarting an interrupted orchestrated run completes only
  the stages that had not yet finished — zero previously-completed stages'
  expensive work is repeated.
- **SC-004**: 100% of artifacts produced through the orchestrated
  pipeline remain traceable to the exact run and parameters that produced
  them, matching today's traceability guarantee with no regression.
- **SC-005**: Attempting to start the Mac-native compression search's
  stage on non-Mac/Apple-Silicon hardware fails before any expensive work
  begins, with an error that names the specific unmet hardware
  requirement.
- **SC-006**: Every experiment-tracking record (trial parameters, quality
  and decensoring scores) an operator could see before this feature is
  still visible in exactly the same tracking destination after this
  feature — zero loss of previously-tracked information.
- **SC-007**: Once the orchestrated pipeline is verified end-to-end against
  the dev-cycle model, starting the identical orchestrated run against the
  production model on production-scale hardware requires changing only
  which model/hardware parameters are supplied at start time — zero
  changes to the pipeline definition itself.

## Assumptions

- This feature is built and verified end-to-end against this pipeline's
  existing cheap dev-cycle model first, matching the dev-cycle's existing
  purpose (validating pipeline-plumbing changes without production cost or
  hardware). This is a verification-order decision, not a scope
  limitation: per FR-011/SC-007, the orchestrated definition itself carries
  no dev-only shortcut — the identical definition MUST be immediately
  usable against the production model on production-scale compute, with
  only start-time parameters (model identifier, hardware placement)
  changing between a dev-cycle run and a production run.
- Metaflow's remote-execution backends target Linux containers only —
  there is no mechanism, in Metaflow or in any comparable orchestrator, to
  remotely dispatch a stage's execution onto Apple Silicon hardware from a
  run started elsewhere. The Mac-native compression search's stage
  therefore still requires the orchestrated run to be started directly on
  a Mac/Apple-Silicon machine (by a person or a Mac-hosted automation
  runner) — this feature changes how that stage is defined and tracked,
  not the physical-hardware requirement it has always had.
- The underlying tools each stage wraps (the decensoring tool, the
  format-conversion tools, the quantization tools, the search libraries)
  are unchanged by this feature — this is an orchestration-layer change,
  not a change to what any individual stage computes or how it computes
  it.
- The existing experiment-tracking destination and the existing per-search
  persistent-search-state mechanism remain in place as the systems of
  record this feature's orchestration reports to and resumes from — this
  feature does not stand up a new, separate tracking or state-storage
  system.
- "Regardless of libraries" is interpreted as freedom in *how* each stage
  internally accomplishes its work (which specific tool or library
  performs decensoring, conversion, quantization, or scoring) — not as
  license to violate a hardware requirement that has no software
  workaround (Assumption 1 above).
- A stage's on-disk provenance sidecar (recording exactly what produced an
  artifact) remains the authoritative record for that artifact regardless
  of orchestration mechanism, because tools outside this pipeline's own
  Python code must be able to read that record without depending on the
  orchestration mechanism's own internals.
