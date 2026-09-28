# Feature Specification: MLflow Experiment Tracking & Quantization Optimization

**Feature Branch**: `[001-mlflow-instrumentation]`

**Created**: 2026-09-25

**Status**: Implemented. Based on all tasks being checked in `tasks.md`; the acceptance checks were not re-run on 2026-09-27.

**Input**: User description: "mlflow conversion" — make the pipeline's existing
abliteration search visible in MLflow, and add automated search over MLX/GGUF
export quantization parameters, scored against the real compressed artifact.
Corresponds to Phase 1 of `ROADMAP.md` and the detailed engineering plan at
`docs/evolutionary-pipeline-optimization-roadmap.md`.

## Clarifications

### Session 2026-09-25

- Q: How should this feature authenticate to the tracking destination (e.g. an MLflow server) when the destination requires credentials? → A: Read credentials only from environment variables — never from a config file, CLI flag, or Makefile `--field`.
- Q: Should the two compression searches (Mac-native and broadly-compatible) be allowed to run at the same time on the same machine, or must they run one after the other? → A: Configurable by compute topology — sequential by default when both searches would share one compute resource (a single local machine or a single hosted instance), but concurrent execution is allowed when each search has its own separate, dedicated compute resource (e.g. a cluster/orchestrated-compute scenario assigning each search its own node).
- Q: When a single compression-search attempt fails or produces an unusable file, does it count against the search's total attempt budget? → A: Yes — a failed attempt counts against the budget; the search may end with fewer successful results than the budget if failures occur.
- Q: As search sessions accumulate over time, should completed compression-search artifact files ever be automatically deleted? → A: No automatic deletion — every completed attempt's file persists indefinitely until a person manually deletes it.
- Q: Should this feature state an expected disk-footprint order of magnitude for accumulated compression-search artifacts? → A: Yes — require a stated approximate per-search-session disk footprint (attempt count × one compressed model file's size) as a documentation obligation, without hardcoding a specific number.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See what the decensoring search actually did (Priority: P1)

A user runs the pipeline's model-decensoring step (which already searches
many parameter combinations automatically) and wants to review, compare, and
share the results of that search afterward — which combinations were tried,
how each one scored on quality retention and on removing refusals — without
digging through a raw local log file.

**Why this priority**: This is the smallest possible slice that delivers
value on its own — it adds *visibility* into an optimization process that
already runs today, with no new search logic and no risk of changing the
model output. It's also a prerequisite building block others depend on.

**Independent Test**: Run the decensoring step once, then open the tracking
dashboard and confirm every attempted combination from that run appears as a
distinct, inspectable entry with its quality and refusal-removal scores.
Delivers value standalone even if no compression search is ever run.

**Acceptance Scenarios**:

1. **Given** a completed decensoring run that tried multiple parameter
   combinations internally, **When** a user views the tracking dashboard,
   **Then** every completed combination appears as a separate entry with its
   parameters and both of its scores (quality retention, refusal removal)
   visible.
2. **Given** the same decensoring run's results have already been recorded
   once, **When** a user re-triggers the recording step for that same run,
   **Then** no duplicate entries appear in the dashboard.
3. **Given** two different models were each decensored separately, **When**
   both runs' results are recorded, **Then** their entries are distinguishable
   from each other in the dashboard (never merged or confused).

---

### User Story 2 - Automatically find good compression settings for a Mac-native export (Priority: P2)

A user has a decensored model and wants to export it into a
Mac-native, compressed format, but doesn't know which compression settings
best balance file size against the model staying smart and staying
decensored. They want an automated search that tries several settings and
reports the best trade-offs, scored on the *actual compressed file*, not a
guess.

**Why this priority**: Delivers the core "automated search instead of manual
guessing" value for one of the two export formats. Depends on User Story 1's
tracking foundation but is independently valuable and independently
shippable — a user could get real quantization guidance for this format even
before the second format (User Story 3) is ready.

**Independent Test**: Point the search at one already-decensored model,
let it try several compression settings, and confirm the dashboard shows
each attempted setting alongside how smart (quality) and how decensored
(refusal rate) the resulting *compressed file* actually turned out to be —
not a score computed before compression.

**Acceptance Scenarios**:

1. **Given** one decensored model checkpoint, **When** a user starts the
   Mac-native compression search, **Then** the system tries multiple distinct
   compression settings and, for each, produces a real compressed file and
   measures that file's quality-retention and refusal-removal scores.
2. **Given** a compression search was interrupted partway through, **When**
   the user restarts it with the same settings, **Then** it continues from
   where it left off rather than discarding prior attempts and starting over.
3. **Given** a compression search has completed several attempts, **When**
   the user inspects the results, **Then** they can identify which attempts
   represent the best available trade-offs between file quality and
   decensoring strength (not just a single "winner" score).
4. **Given** a completed attempt's compressed file would normally be deleted
   or overwritten by a later, unrelated export, **When** that later export
   runs, **Then** the completed attempt's file remains available for
   inspection, unaffected.

---

### User Story 3 - Automatically find good compression settings for a broadly-compatible export (Priority: P3)

The same automated-search value as User Story 2, but for the pipeline's
second, broadly-portable export format (used by more runtimes and hosting
environments, not limited to Mac hardware) — searching which compression
level and calibration amount best balance file size, quality, and
decensoring strength on the real compressed file.

**Why this priority**: Same value proposition as User Story 2, for the
pipeline's other export path. Ordered after User Story 2 because it is
the second of two symmetric, independent searches — either could ship
first without blocking the other; this one is prioritized third only
because the broadly-compatible format's one-time conversion step is more
expensive to set up before the search itself can run.

**Independent Test**: Point the search at one already-converted
(pre-quantization) exported model, let it try several compression levels,
and confirm the dashboard shows each attempted level's real, measured
quality and decensoring scores on the actual compressed output file.

**Acceptance Scenarios**:

1. **Given** one exported (not-yet-compressed) model, **When** a user starts
   this format's compression search, **Then** the system tries multiple
   distinct compression levels and measures each resulting compressed file's
   quality-retention and refusal-removal scores.
2. **Given** the search needs to try five different compression levels,
   **When** it runs, **Then** it does **not** repeat the expensive one-time
   conversion step for each attempt — that step happens once, up front.
3. **Given** a compression search has completed several attempts, **When**
   the user later runs an unrelated, routine export of this same format,
   **Then** the completed search attempts' saved files are unaffected by
   that unrelated export's routine cleanup.

---

### Edge Cases

- What happens when the tracking destination (dashboard/server) is
  unreachable or not configured? → The system MUST fail clearly and early,
  before doing any expensive work, rather than silently skipping tracking or
  losing results.
- What happens when a compression search attempt produces an invalid or
  unusable file (e.g. a setting combination that isn't actually supported)?
  → That single attempt MUST be recorded as failed and the search MUST
  continue with remaining attempts, not abort the whole search. The failed
  attempt counts against the search's total attempt budget (see FR-016) —
  the search does not get a free retry outside that budget.
- What happens when a compression search targets a model architecture whose
  quality-scoring mechanism is not confirmed to support that architecture
  (e.g. a vision-language model where only text-only scoring is confirmed
  working)? → See FR-011 (surfaced as a known limitation, not silently
  ignored).
- What happens if a user asks to record the same decensoring run's results
  twice (e.g. by accident)? → See User Story 1, Acceptance Scenario 2 — no
  duplicate entries.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow a user to record every attempted
  parameter combination from a completed decensoring run into a durable,
  browsable tracking record — including each combination's parameters and
  its quality-retention and refusal-removal scores.
- **FR-002**: The system MUST NOT create duplicate tracking entries when the
  same decensoring run's results are recorded more than once.
- **FR-003**: The system MUST distinguish tracking entries from different
  decensoring runs (of the same or different models) from one another, even
  if recorded in separate sessions.
- **FR-004**: The system MUST provide an automated search over the
  Mac-native export format's compression settings, evaluated against a
  single, fixed, already-decensored model.
- **FR-005**: The system MUST provide an automated search over the
  broadly-compatible export format's compression settings, evaluated
  against a single, fixed, already-exported (pre-compression) model.
- **FR-006**: Both compression searches MUST score every attempt using the
  actual compressed output file produced by that attempt — never a score
  computed before compression, and never an estimate.
- **FR-007**: Both compression searches MUST evaluate every attempt on at
  least two independent measures — how much of the original model's quality
  is retained, and how effectively refusals remain removed — and MUST NOT
  collapse these into a single combined score that hides the trade-off.
- **FR-008**: Both compression searches MUST be resumable: an interrupted
  search, when restarted with the same configuration, MUST continue from
  its prior progress rather than discarding it.
- **FR-009**: Every attempt's compressed output file, once produced by a
  search, MUST remain available for inspection and MUST NOT be deleted or
  overwritten by that search's own later attempts or by unrelated, routine
  pipeline operations (e.g. a manual, non-search export of the same
  format). The system MUST NOT automatically delete a completed attempt's
  file for any reason (e.g. retention limits, age) — removal is a
  person-initiated action only, matching this pipeline's existing pattern
  where cleanup is always explicit and human-triggered.
- **FR-010**: The broadly-compatible export format's search MUST reuse a
  single one-time conversion step across all of its attempts rather than
  repeating that step per attempt.
- **FR-011**: The system is NOT required to support quality-retention
  scoring for model architectures where the Mac-native export format's
  scoring mechanism is confirmed unsupported (see Assumptions) — this MUST
  be surfaced to the user as a clear, explicit limitation rather than a
  silent skip or a crash.
- **FR-012**: The system MUST NOT change how the underlying decensoring
  step itself selects or searches its own parameters — this feature only
  observes and records that step's existing results, and separately
  searches compression parameters for the two export formats.
- **FR-013**: The system MUST NOT alter which source datasets are used for
  decensoring or for compression calibration — only how many samples are
  drawn from those already-fixed sources, where that has an effect, is in
  scope.
- **FR-014**: The system MUST read any credential needed to authenticate to
  the tracking destination only from the environment — never from a config
  file, a command-line flag, or a recorded tracking field — and MUST NOT
  write such a credential into any tracking record, log, or manifest.
- **FR-015**: When both compression searches would share one single compute
  resource (one local machine, or one hosted instance), the system MUST run
  them sequentially by default — the second search MUST NOT start until the
  first finishes on that shared resource. When each search instead has its
  own separate, dedicated compute resource (e.g. a cluster/orchestrated
  multi-node scenario), the system MUST allow them to run concurrently.
- **FR-016**: A compression-search attempt that fails or produces an
  unusable file MUST count against that search's total attempt budget — the
  system MUST NOT grant an uncounted retry for a failed attempt, and a
  search MAY end with fewer successful results than its configured budget
  if failures occur.
- **FR-017**: The system MUST state, in its documentation, an approximate
  disk-footprint order of magnitude for one compression-search session's
  accumulated artifacts (expressed as attempt count × one compressed
  model's typical file size for the format in question) — so a user can
  judge storage needs before running repeated search sessions, given that
  FR-009 guarantees these files are never auto-deleted.

### Key Entities

- **Decensoring run**: One completed execution of the model-decensoring
  step, which itself internally tries many parameter combinations. Has an
  identity distinct from other runs (including re-runs of the same source
  model), and produces a set of already-computed trial results.
- **Trial**: One attempted parameter combination within either the
  decensoring run's own internal search, or one of the two new compression
  searches. Carries its input parameters and its resulting scores.
- **Compression search**: A new, independent, resumable search process (one
  per export format) that produces many trials, each yielding a real
  compressed output file plus that file's measured scores.
- **Compressed output file (search artifact)**: The actual exported,
  compressed model file produced by one compression-search trial. Must
  persist independently of routine pipeline cleanup so it can be inspected
  or compared after the fact.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can go from "a decensoring run just finished" to
  "I can see every combination it tried and how each scored" without
  reading a raw log file, in under one minute of manual effort.
- **SC-002**: For each export format, a user can launch an unattended
  compression search and receive, within a single search session, at least
  two genuinely different settings that represent different points on the
  quality-vs-decensoring trade-off (i.e., the search never collapses to
  recommending only one setting).
- **SC-003**: If a compression search is interrupted and restarted, zero
  previously-completed attempts need to be redone.
- **SC-004**: 100% of a compression search's completed attempt files
  survive at least one subsequent, unrelated routine export operation of
  the same format, unchanged.
- **SC-005**: A user attempting to record the same decensoring run's
  results twice sees the same result count both times — no duplicates.
- **SC-006**: When both compression searches are launched against one
  shared local machine or hosted instance, the second search's first
  attempt does not begin until the first search's last attempt finishes.
  When each search is instead given its own separate compute resource, both
  searches make progress at the same time.
- **SC-007**: Before running a compression search for the first time, a user
  can find a stated approximate disk-footprint estimate for that search's
  accumulated output in this feature's documentation, without needing to
  run the search first to find out empirically.

## Assumptions

- The existing model-decensoring step already performs its own internal
  automated parameter search and produces a locally-readable record of that
  search's results; this feature reads and republishes that record without
  changing how the search itself runs.
- A tracking destination (dashboard/server) is supplied by the user/operator
  ahead of time; this feature does not stand one up or choose one by default.
- Each compression search targets one fixed, already-produced upstream
  model artifact per search session — searching *which* upstream model to
  decensor, or re-running the decensoring step itself as part of a search,
  is out of scope for this feature.
- Which source datasets feed decensoring or calibration is fixed; only
  *how many* samples are drawn from an already-fixed dataset is a tunable
  search parameter, and only where that count has a measurable effect.
- For at least one of the two export formats, quality-retention scoring
  against certain model architectures (specifically, vision-language
  models, as opposed to text-only models) is not yet confirmed to work with
  the scoring approach available for that format. Where that scoring
  approach is confirmed unsupported for a given model, this feature must
  say so clearly rather than produce a misleading result — closing that gap
  for those architectures is out of scope for this feature.
- A search budget of roughly 10-20 attempts per compression search is
  assumed to be an acceptable, affordable default; unlimited or
  very-large-budget search is out of scope.
- Both compression searches target one export format each; a single joint
  search spanning both formats at once is out of scope.
- This feature does not change which physical machine or hardware any step
  runs on — that is a separate, unrelated pipeline concern (see the
  export dispatch in `specs/013-export-dispatch`).
