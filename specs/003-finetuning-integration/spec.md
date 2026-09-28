# Feature Specification: Integrate the Fine-Tuning Exercise into the Primary Pipeline

**Feature Branch**: `[003-finetuning-integration]`

**Created**: 2026-09-27

**Status**: Implemented. Based on all tasks being checked in `tasks.md`; the acceptance checks were not re-run on 2026-09-27.

**Input**: User description: "lets review fintuning -- it is a new addition to this repo and needs to be subsumed by our primary make system, local pipeline and metaflow pipelines"

## Context (current state, as reviewed)

`finetuning/` ("Spot the Sleeper") was brought in as a self-contained project.
It has its own build file, environment (a separate env at `finetuning/env`,
Apple Silicon only), constitution (`finetuning/.specify/memory/constitution.md`),
knowledge vault (`finetuning/vault/`), agent guide, and end-to-end smoke test.
None of it is reachable from the repository's primary `make` entry points,
`make help`, `make test`, `make doctor`, the local pipeline, or the Metaflow
flow (`flow.py`). Its stages are: preflight → build datasets → train variants
(sleepers + decoys) → QA gate → wordlist → handover → Blue audit (weight-diff
+ probe) → reveal/score.

## Clarifications

### Session 2026-09-27

- Q: May Red-only secrets be stored in shared stores? → A: Option C — they may be stored in both the Metaflow artifact store and the experiment tracker, provided access is restricted. Blue-facing outputs and the handover must still never contain them.
- Q: How are the nested governance/knowledge artifacts reconciled? → A: Deferred — leave `finetuning/`'s constitution, AGENTS.md and vault as they are for now. Reconciliation is out of scope for this feature and will be handled later.
- Q: How does fine-tuning relate to the decensor/export pipeline? → A: Option B, refined — fine-tuning is a set of **additional, optional steps within the same pipelines** (root make/local chain and the same Metaflow flow), not a separate pipeline. When enabled, they can consume upstream pipeline outputs (e.g. a decensored or exported model) as their base model; when disabled, the original pipeline runs exactly as today.

### Session 2026-09-27 (clarify)

- Q: When fine-tuning is switched on in the main pipeline, which model should it fine-tune by default? → A: Always the upstream pipeline model, meaning the model the pipeline run was started with (`MODEL`, or `DEV_MODEL` on the dev cycle). The documented list of supported upstream models MUST explicitly include the small models (TinyLlama/TinyLlama-1.1B-Chat-v1.0, the existing `DEV_MODEL`, and SmolLM2 — `HuggingFaceTB/SmolLM2-135M-Instruct`), alongside the production Qwen. Decensoring and fine-tuning MUST be orderable either way: decensor → fine-tune, or fine-tune → decensor.
- Q: When fine-tuning runs before decensoring, which of the fine-tuned models should the decensoring step process? → A: Every variant in the lineup, with identical decensoring settings, so variants still differ only by the backdoor.
- Q: If the upstream model has not been verified for fine-tuning, should the pipeline refuse or warn and continue? → A: Always allow — no verification gate. Assume it will work; record outcomes (success or failure) in the project's support matrix (`COMPATIBILITY.md`) and address failures there.
- Q: Should fine-tuning run only on Apple Silicon Macs, or also on the Linux + NVIDIA cloud machines? → A: Both (Option B). Apple Silicon keeps the existing Mac tools; Linux + NVIDIA (Track B) gets a GPU equivalent; the same pipeline steps choose the right one for the host.
- Q: When fine-tuning is switched on, should the existing export steps (MLX and GGUF quantization) also run on the fine-tuned models? → A: Yes. Every lineup variant is exported with identical export settings (Option A).
- Q: What happens to the `finetuning/` folder after integration? → A: Move all of its logic, docs, build targets, dependencies and tests into the root project, then delete the moved files from `finetuning/`. Only the items that need human review stay there: the nested constitution, AGENTS.md, vault, and speckit/conda config. A manifest in the folder lists what remains and why.
- Q: Should the pipeline warn about expensive runs? → A: Yes. It warns (never blocks) before long runs with the estimated compute time, memory, disk and, on billed hosts, cost, so the operator knows what they are starting. The goal is to support as many models and model types (architectures, sizes, dense/MoE, text/vision) as possible.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run fine-tuning from the primary make system (Priority: P1)

An operator working at the repository root wants to prepare, train, gate
and hand over a fine-tuning lineup using the same root-level commands,
help listing, preflight and setup they already use for the rest of the
pipeline — without changing directory or learning a second build system.

**Why this priority**: Smallest slice that makes fine-tuning a first-class
part of the repo; everything else (pipeline stages, Metaflow) builds on
these entry points.

**Independent Test**: From a fresh clone at the repository root, run root
setup, then the root fine-tuning targets in sequence; confirm they produce
the same outputs as running the sub-project's own commands today, and that
every fine-tuning target appears in root `make help` and `README.md`.

**Acceptance Scenarios**:

1. **Given** a fresh clone, **When** the operator runs root setup, **Then**
   the fine-tuning environment is prepared as part of (or alongside) the
   existing setup with one command.
2. **Given** root setup is done, **When** the operator runs each fine-tuning
   stage target from the root, **Then** each stage produces the same
   artifacts, in the same places, as the sub-project's existing commands.
3. **Given** the operator runs root preflight/doctor, **Then** fine-tuning
   readiness (platform, environment, base model present, disk, stale cohort)
   is reported alongside existing checks.
4. **Given** the operator runs root `make test`, **Then** fine-tuning's
   automated checks run as part of it, with expensive runs (full training)
   excluded or gated the same way other expensive stages are.

---

### User Story 2 - Fine-tuning as stages of the local pipeline (Priority: P2)

An operator wants the fine-tuning lineup build (datasets → train → QA gate
→ handover) to run as ordered stages of the local (non-Metaflow) pipeline,
with each stage refusing to run when its prerequisites are missing and
stopping the chain when a gate says NO-GO.

**Why this priority**: Removes hand-sequencing of a ~45-minute multi-step
process whose failure modes (stale cohort, leaked trigger, unwinnable
lineup) are exactly what the existing gates guard against.

**Independent Test**: Invoke the local pipeline's fine-tuning chain once at
dev scale; confirm stages run in order, a forced NO-GO halts before
handover, and a successful run ends with a staged handover that passes the
secrecy check.

**Acceptance Scenarios**:

1. **Given** a base model is present, **When** the chain runs, **Then**
   datasets, training, QA gate and handover run in order without manual
   intervention.
2. **Given** the QA gate returns NO-GO, **When** the chain reaches handover,
   **Then** handover does not run and the operator sees why.
3. **Given** the trigger string is found in the staged handover, **When**
   the secrecy check runs, **Then** the run fails and nothing is presented
   as safe to share.

---

### User Story 3 - Fine-tuning as optional steps in the Metaflow flow (Priority: P3)

An operator wants to run the fine-tuning lineup build as a Metaflow run —
via root `make` or directly via Metaflow's own command line, matching the
two sanctioned entry points established in feature 002 — with run
provenance recorded and experiment tracking consistent with the rest of
the pipeline.

**Why this priority**: Brings fine-tuning under the same orchestration,
resumability and provenance as decensoring and export, but depends on
Stories 1–2 being stable.

**Independent Test**: Start one Metaflow run for the fine-tuning stages at
dev scale via `make`, and once directly via Metaflow's CLI; confirm both
produce equivalent lineups, a passing QA gate record and a handover, and
that re-running with only fine-tuning steps selected skips unrelated stages.

**Acceptance Scenarios**:

1. **Given** the existing Metaflow flow, **When** the operator enables
   fine-tuning, **Then** the fine-tuning steps run within that same flow
   after the upstream stages. When fine-tuning is not enabled, the flow
   behaves exactly as today.
2. **Given** fine-tuning is enabled with order decensor → fine-tune,
   **When** the run starts, **Then** the decensored upstream model is the
   fine-tuning base. **Given** order fine-tune → decensor, **Then** the
   every lineup variant is decensored with identical settings before QA
   gate and handover.
3. **Given** a completed run, **When** the operator inspects its recorded
   artifacts and tracking entries, **Then** Red-only material (answer key,
   training datasets, trigger) is stored only in access-restricted stores
   (artifact store and experiment tracker), and never in the handover or
   any Blue-facing output
4. **Given** a Track B (Linux + NVIDIA) host, **When** a fine-tuning step
   starts, **Then** it runs using the GPU implementation, with the same
   recipe and gates as on Apple Silicon, and records the platform.

---

### User Story 4 - Blue-side audit and reveal remain usable (Priority: P3)

Blue auditors and the facilitator can still run the audit (weight-diff +
probe) and the reveal/score from root commands, and Blue's documentation
stays spoiler-free.

**Independent Test**: Run root audit against a staged handover and root
reveal against the answer key; confirm outputs match today's; confirm
Blue-facing doc contains no trigger or answer-key content.

**Acceptance Scenarios**:

1. **Given** a handover directory and wordlist, **When** Blue runs the root
   audit target, **Then** one ranked row per model is produced.
2. **Given** the answer key, **When** the facilitator runs reveal/score,
   **Then** both detectors are graded as today.

### Edge Cases

- Base model not yet converted/downloaded (needs network, ~2 GB) — stage
  refuses with the exact command to fetch it.
- Stale cohort from a previous run under `finetuning/data/out/` mixed with
  a new lineup — preflight detects and refuses.
- A fine-tuning target is run outside the root `.venv` (e.g. from the
  legacy `finetuning/` conda env). It must fail clearly, not half-run.
- Running on a host that is neither Track A nor Track B (e.g. Linux
  without an NVIDIA GPU) — the step fails with a clear platform message.
- A lineup trained on one platform and audited on the other — this is
  supported; the platform of each stage is recorded.
- Operator overrides paths (answer key outside repo, custom output dir) —
  ignore rules and secrecy check must still hold.
- Root `make clean` must not delete the answer key or Red-only datasets
  unless explicitly requested.
- Fine-tuning enabled but the upstream stage it depends on (per the
  chosen order) was skipped or failed — refuse before training.
- Fine-tune → decensor where decensoring fails for one variant — the run
  fails and no handover is staged (a partially decensored lineup is unfair).
- An export fails for one lineup variant — the run reports it and the
  failure is recorded in the support matrix. The exported lineup is
  marked incomplete, not presented as a full set.
- Upstream model not on the supported list — the run proceeds; its
  outcome is recorded in the support matrix.
- Upstream model too large or in a non-trainable (e.g. quantized-only)
  format for the fine-tuning host — the stage fails with the underlying
  error; the failure is recorded in the support matrix.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every fine-tuning stage (setup, preflight, datasets, train,
  qa, wordlist, handover, audit, reveal/score, verify-docs, test) MUST be
  invokable from the repository root through the primary make system.
- **FR-002**: Root `make help` and root `README.md` MUST list every new
  fine-tuning target in the same change (AGENTS.md §7).
- **FR-003**: Root setup, preflight/doctor and test MUST include
  fine-tuning; expensive training MUST NOT run as part of routine `make test`.
- **FR-004**: The local pipeline MUST chain datasets → train → QA gate →
  handover, halting on any failed gate and never staging a handover after
  a NO-GO or failed secrecy check.
- **FR-005**: The Metaflow flow MUST expose the fine-tuning stages as
  selectable steps, runnable via root `make` and directly via Metaflow's
  CLI, parameterized (base model, variants, sleepers, trigger, scale, seed)
  so the same definition runs at dev and full scale.
- **FR-006**: Fine-tuning steps (datasets, train, QA gate, handover,
  audit, reveal) MUST run on both Track A (Apple Silicon) and Track B
  (Linux + NVIDIA GPU). The same pipeline step MUST pick the right
  implementation for the host automatically, and the platform used MUST
  be recorded in provenance. Both platforms MUST apply the same recipe
  and the same gates (QA, secrecy check), and produce the same kinds of
  output. On any other host the step MUST fail with a clear message that
  names the supported platforms.
- **FR-007**: Red-only material (trigger, answer key, training datasets)
  MAY be stored in the Metaflow artifact store and experiment tracker only
  when access to them is restricted. "Restricted" means Red-only material
  is logged solely to a dedicated Red experiment (`<prefix>-finetune-red`)
  and never to the Blue experiment (`<prefix>-finetune-blue`). Access
  control on the Red experiment and datastore relies on the operator's
  store permissions, and the README documents this. and MUST never appear in any
  Blue-facing output, handover or wordlist; the existing secrecy check MUST remain and MUST run in
  every entry path.
- **FR-008**: Outputs produced through the integrated entry points MUST
  match those of the sub-project's existing commands for the same inputs
  and seed (within the repo's bounded reproducibility language, Article V).
- **FR-009**: Fine-tuning runs MUST record provenance (base model and
  commit, dataset parameters, seed, recipe) consistent with `PROVENANCE.md`.
- **FR-010**: Fine-tuning dependencies and licences MUST be reflected in
  the root lock/notices (`requirements-lock.txt`, `THIRD_PARTY_NOTICES.md`,
  `third_party_licenses.json`) via their generators.
- **FR-011**: The nested governance and knowledge artifacts (fine-tuning's
  constitution, agent guide, vault, speckit config, conda env files) MUST
  NOT be merged or edited by this feature. They stay in `finetuning/` for
  human review; reconciling them with the root is deferred.
- **FR-012**: Fine-tuning MUST be added as optional steps within the
  existing pipelines (root make/local chain and the existing Metaflow
  flow), not as a separate pipeline. It MUST be off by default. When off,
  the original pipeline's steps, outputs and run time MUST be unchanged.
  When on, the fine-tuning steps MUST always use the upstream pipeline
  model (the model the run was started with, `MODEL` or `DEV_MODEL`) as
  their base, never a separately chosen base.
- **FR-013**: Blue-facing documentation MUST remain spoiler-free after any
  doc consolidation, verified by the existing doc checks.
- **FR-014**: The pipeline MUST NOT refuse or gate fine-tuning or
  decensoring based on whether the upstream model is on the verified list.
  Any model is allowed; the stage runs and its outcome is reported.
- **FR-015**: The operator MUST be able to choose the order of decensoring
  and fine-tuning within one pipeline run: decensor → fine-tune (the
  decensored model is the fine-tuning base) or fine-tune → decensor (the
  fine-tuned output is what gets decensored). Either stage MAY also be run
  alone. The chosen order MUST be recorded in the run's provenance.
- **FR-016**: The documentation MUST include a list of supported upstream
  models that names the small models explicitly (TinyLlama-1.1B-Chat-v1.0
  — the current `DEV_MODEL` — and `HuggingFaceTB/SmolLM2-135M-Instruct`) alongside the production model.
  For each model it MUST state whether fine-tuning, decensoring, and each
  order have been verified on it. This list lives in the project's support
  matrix (`COMPATIBILITY.md`); observed successes and failures on any
  model MUST be recorded there, and failures are addressed there rather
  than by blocking the run. The README's summary compatibility table MUST
  gain a fine-tuning column kept consistent with `COMPATIBILITY.md`.
- **FR-017**: Before any fine-tuning or decensoring stage starts, the
  pipeline MUST print a warning with the estimated wall-clock time, memory,
  and disk the stage needs for the chosen upstream model, lineup size and
  order, plus an hourly-cost reminder on billed hosts (Track B). The
  warning MUST NOT block the run. Estimates MUST reuse the existing
  hardware check sizing (`make doctor` / `make dev-doctor`) where it
  applies, and MUST say "unknown" rather than guess for models with no
  recorded measurement.
- **FR-018**: The integration MUST aim to support as many model families
  and types as possible (sizes from ~1B to the production model, dense and
  MoE, text-only and vision-language). Measurable form: (a) no fine-tuning
  code path branches on, or hard-codes, a model name or architecture
  class, except the documented defaults, as checked by a test; (b)
  vision-language upstream models are fine-tuned on their text
  path only, and any failure is recorded in the support matrix rather than
  special-cased.
- **FR-019**: User-facing documentation MUST be updated in the same
  change as the behaviour it describes, following `docs/DESIGN.md`
  (fixed section order, palette, SVG rules, `<details>` for dense content).
  At minimum:
  - `README.md`: the tagline and "What is Wellspring?" mention the optional
    fine-tuning stage; Quick Start shows an optional fine-tuning run;
    Features, Make Targets and Key Variables (enable flag, stage order,
    lineup parameters) rows are added; the Metaflow section's step table
    gains the fine-tuning steps.
  - Diagrams: the pipeline and Metaflow flow-graph SVGs (dark and light
    variants) show the optional fine-tuning steps and both stage orders.
    They are edited at source and rendered and inspected before sign-off
    (AGENTS.md §3–4).
  - `COMPATIBILITY.md` (support matrix, per FR-016), `PROVENANCE.md`
    (fine-tuning run records and stage order, per FR-009),
    `THIRD_PARTY_NOTICES.md` (per FR-010) and `CHANGELOG.md`.
  - Requirements: the Track A/B sections state fine-tuning's hardware
    requirement (FR-006) and its disk and time costs (FR-017).
  - `finetuning/README.md` and its Red/Blue/Facilitator docs point to the
    new root entry points, and Blue's doc stays spoiler-free (FR-013).
  - A vault note records the integration decisions (AGENTS.md §11).
- **FR-020**: When fine-tuning is enabled, the existing export steps (MLX
  and GGUF, including their quantization searches) MUST run on every
  lineup variant produced by the last modelling step, using identical
  export settings and trial budgets for every variant. Each exported
  artifact MUST record in provenance which variant it came from. Exports
  MUST NOT reveal to Blue which variants are sleepers. The FR-017 warning
  MUST include the export cost, multiplied by the number of variants.
- **FR-021**: All fine-tuning **logic** (source, scripts, build targets,
  dependencies, tests) and **user-facing docs** (README reference,
  Red/Blue/Facilitator guides) MUST be moved into the root project's
  structure. After that, the moved files MUST be deleted from
  `finetuning/`, leaving no second copy that could drift. No behaviour
  may exist only in `finetuning/` when this feature is done.
- **FR-022**: `finetuning/` MUST end with only the FR-011 items plus a
  short manifest (`finetuning/REVIEW.md`). The manifest lists each
  remaining file, why it was left, and the follow-up decision it needs.
  It also maps each moved file to its new root location.
- **FR-023**: Pipeline data (inputs, outputs, answer key, handover,
  wordlist) MUST live under a root, git-ignored location. Nothing may be
  read from or written to `finetuning/` at run time.

### Key Entities

- **Supported upstream model list** (support matrix): documented set of pipeline models
  (small dev models and the production model), each with its verified
  capabilities (fine-tune, decensor, each order).
- **Stage order**: per-run choice of decensor → fine-tune or fine-tune →
  decensor, recorded in provenance.
- **Resource warning**: pre-stage estimate of time, memory, disk and cost
  for the chosen model, lineup size and order; informational only.
- **Lineup**: set of fine-tuned variants, each a sleeper or decoy, all
  trained with one recipe from one base model.
- **Answer key**: Red-only record of which variants are sleepers and the
  trigger.
- **Handover**: staged, Blue-safe copy of the merged models only.
- **Wordlist**: Blue-safe candidate trigger list (real trigger among decoys).
- **Audit result / score**: Blue's per-model suspicion ranking and the
  reveal's grading of both detectors.
- **Run record**: provenance and tracking entry for one lineup build.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of fine-tuning stages are runnable from the repository
  root; 0 steps require changing directory into the sub-project.
- **SC-002**: An operator can go from fresh clone to a staged, secrecy-
  checked handover at dev scale with one setup command plus one pipeline
  command.
- **SC-003**: Routine repository test run time grows by no more than 5
  minutes and includes fine-tuning checks.
- **SC-004**: In 100% of runs with a deliberately leaked trigger or a NO-GO
  gate, no handover is presented as safe.
- **SC-005**: The same lineup (same inputs and seed) built via make, the
  local pipeline, and Metaflow yields the same sleeper/decoy assignments
  and the same QA gate verdict.
- **SC-006**: Every new target has a matching help line and README row on
  day one (0 undocumented targets).
- **SC-007**: With fine-tuning disabled, the new steps do no work and
  all of the original pipeline's outputs (artifacts, manifests, tracking
  entries) are identical to before this feature (0 regressions). The
  graph may contain the new, idle steps.
- **SC-008**: Both stage orders complete end to end on at least one small
  supported upstream model at dev scale.
- **SC-009**: 100% of fine-tuning/decensoring stage starts show a
  resource warning (time, memory, disk, and cost on billed hosts) before
  work begins, and 0 of them are blocked by it.
- **SC-010**: The support matrix records a result (works / fails + reason)
  for every model the pipeline has been run on with fine-tuning, starting
  with at least 2 small models and the production model.
- **SC-011**: Every command shown in the updated docs runs as written
  (0 broken or stale commands), and every updated diagram has been
  rendered and inspected in both colour schemes.
- **SC-012**: The same small-model lineup (same inputs and seed) completes
  end to end on both Track A and Track B. Both runs give the same
  sleeper/decoy assignment and the same QA gate verdict.
- **SC-013**: After the feature, `finetuning/` contains only the FR-011
  items and `REVIEW.md`. A search of the repo finds 0 references to the
  deleted `finetuning/` paths from code, make targets or docs, other than
  the review manifest itself.

## Assumptions

- "Local pipeline" means the root Makefile's native (non-Metaflow) stage
  chain; "Metaflow pipelines" means `flow.py` per feature 002.
- Running Red and Blue in one adversarial (GAN-style) loop is out of scope; it is specified in `specs/014-redblue-single-round` and `specs/018-redblue-feedback-loop`.
- Reconciling the nested constitution/vault/AGENTS.md is out of scope (deferred); those files remain in `finetuning/` for human review per FR-022.
- Access restriction on shared stores relies on the stores' existing access controls.
- Small upstream models (TinyLlama, SmolLM2) are where both orders are verified first; the production model's fine-tuning feasibility is recorded on the supported list, not assumed.
- Fine-tuning runs on both Track A and Track B. The Apple Silicon path
  is the existing, measured one and is verified first; the Track B path
  is new and is verified on a small model before the production model.
- Fine-tuning runs in the root `.venv`; the legacy `finetuning/`
  conda env files are left only for human review (FR-011) and are not
  used. The root make system owns creating and selecting the environment.
- Existing fine-tuning behaviour, commands' outputs and gates are correct
  as reviewed and are preserved, not redesigned.
- Full-scale (44-minute) training is verified at least once manually; CI-
  style checks use dev scale.
- New functional Python follows test-first (Article IX).
