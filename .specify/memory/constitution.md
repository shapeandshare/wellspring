<!--
Sync Impact Report — Constitution Ratification
Version change: (none) → 1.0.0 (initial ratification)
Modified principles: n/a (first version)
Added sections:
  - Core Principles (Articles I–XIII)
  - Additional Constraints
  - Development Workflow & Quality Gates
  - Governance
Removed sections: none
Note on drafting: this constitution deliberately absorbs structural
principles from the sibling constitutions it was modeled on (anvil,
darkfactory — both Spec Kit projects sharing this operator's conventions)
at full strength rather than deferring them until wellspring's codebase
grows into needing them:
  - Article IX (TDD) is stated as NON-NEGOTIABLE, matching both source
    constitutions, not softened to a SHOULD — and is backed by a real
    `tests/` suite + `make test` target added in this same change, so the
    MUST has teeth from day one.
  - Article X (Domain-Driven Package Decomposition) and Article XI
    (Package Ownership / one-class-per-file) are adopted now, ahead of
    `scripts/` actually needing them, using the same "Applicability"
    compliance-status pattern the source constitutions use for
    forward-adopted rules (see darkfactory Articles XII/XIII).
  - Async-first is the one source-constitution article NOT absorbed:
    wellspring has no async runtime (CLI scripts + subprocess calls only)
    and none is on the roadmap, so adopting it would violate Article VI
    (YAGNI) with nothing to attach it to. Revisit if that changes.
This constitution was drafted, then adversarially reviewed (cross-checked
against the actual Makefile/scripts/README, not just its own claims) and
corrected before ratification. Fixes applied as part of that review, ported
into this document from the start: fail-open provenance in
`scripts/write_manifest.py` (an explicitly-asserted `--git-dir` that failed
to resolve was silently recorded as `null` instead of failing the stage —
now fatal, Article I Rule 6); a missing self-record of this repo's own
commit/dirty state in every manifest (now `wellspring_commit`/
`wellspring_dirty`, Article I Rule 3); an atomicity rule written to
distinguish file vs. directory replace semantics honestly rather than
overclaim a zero-crash-window guarantee POSIX `rename()` cannot actually
provide for non-empty directories (Article IV); an Article III scope that
doesn't overclaim zero shared tooling between the MLX/GGUF paths (they
share the Python env, Makefile, and `write_manifest.py` — narrowed to
format-specific tooling); an Article V rule scoped to stochastic stages
only, not every manifest; and `.specify/templates/tasks-template.md` +
`.opencode/commands/speckit.tasks.md` corrected to state tests are
MANDATORY (Article IX), not optional, matching this document.
Templates / docs propagated:
  - ✅ .specify/templates/plan-template.md, spec-template.md,
    checklist-template.md — verified generic by design: `/speckit.plan`
    fills the Constitution Check section dynamically from this file at
    plan-generation time (core Spec Kit behavior, not a per-project
    customization point — confirmed byte-identical to anvil's/darkfactory's
    own plan-template.md)
  - ✅ .specify/templates/tasks-template.md — edited: removed "Tests are
    OPTIONAL" language (4 occurrences) contradicting Article IX
  - ✅ .opencode/commands/speckit.tasks.md — edited: same fix, "Tests are
    MANDATORY" per Article IX with its stated exceptions
  - ✅ Makefile — `test` target + `.PHONY` entry + help line added
  - ✅ requirements.txt — `pytest>=8.0` added (dev/test tooling)
  - ✅ README.md — Governance section + `make test` row link here
  - ⚠ requirements-lock.txt / third_party_licenses.json — NOT regenerated
    by this ratification: no `.venv` exists in this checkout yet to freeze
    (`make lock`/`make notices` both depend on `install`, which would
    trigger a full, heavy `make setup` — not something to do as a side
    effect of a documentation change). Re-run both after the next
    `make setup` (Article II Rule 2 still applies from that point forward).
  - ⚠ PROVENANCE.md / ROADMAP.md — not modified by this ratification; they
    remain the authoritative *operational* references this constitution
    points to (see Governance)
Follow-up TODOs:
  - Migration debt MD-001: `scripts/fetch_calibration_data.py` and
    `scripts/fetch_calibration_text.py` duplicate an identical
    `positive_int` helper — a Simplicity/Reuse (Article VI Rule 4)
    violation to fix next time either file is touched; both copies are
    tested independently in the meantime (see tests/).
  - Migration debt MD-002: `scripts/preflight_check.py` (added by PR #2,
    predates this constitution) is not covered by this ratification's test
    suite — the other three pre-existing scripts were retrofitted with
    characterization tests in this same change; this one was not, to keep
    this change scoped to porting already-reviewed work rather than
    reviewing a fourth script from scratch. Retrofit when it is next
    touched (Article IX Applicability).
  - Should-consider, deliberately deferred (not silently dropped): fast
    offline Makefile-recipe contract tests (mocking the `heretic`/
    `mlx_vlm`/`llama-*` binaries themselves to test recipe ordering and
    failure-path behavior, including the `GGML_CUDA=ON` + missing-`nvcc`
    guard) would strengthen confidence in Article IV/VIII beyond the
    Python-script-level tests added here. Not done in this pass — larger
    scope than a documentation/script correction round; a candidate for
    its own `/speckit.specify` cycle.
-->
# Wellspring Constitution

> Wellspring is the Heretic → MLX / GGUF export pipeline in this repository
> (see `README.md`). This constitution governs the pipeline's Makefile,
> Python scripts, and documentation — not the vendored `heretic`/`ik_llama.cpp`
> tools it orchestrates, which are external dependencies governed by their
> own upstream projects (tracked in `PROVENANCE.md` / `THIRD_PARTY_NOTICES.md`).
>
> This document is modeled on the constitutions of this operator's sibling
> Spec Kit projects (anvil, darkfactory): several articles below are direct
> adaptations of one or both (Simplicity First and Domain-Driven Package
> Decomposition appear in both source documents; TDD and Package Ownership
> appear in both in substance under different names/groupings; Agent
> Conduct is darkfactory-specific; the governance/versioning structure
> mirrors both), scaled to Wellspring's much smaller surface — a Makefile
> and a handful of scripts, not a multi-service application. Where a
> source article doesn't fit (layered service architecture, async I/O
> boundaries), it is intentionally omitted rather than forced.

## Core Principles

### Article I — Provenance & Chain of Custody (NON-NEGOTIABLE)

Every external input this pipeline touches — code, model weights, and
datasets — MUST have its pinning status stated explicitly, and every
artifact this pipeline produces MUST be traceable back to exactly what
produced it.

**Rules:**

1. A new external input (a tool fetched by URL/git, a HF model, or a HF
   dataset) MUST either be pinned to an exact commit/revision by default, or
   the Makefile default MUST be documented as deliberately unpinned with the
   reason — mirroring `MODEL_COMMIT`'s documented exception in
   `PROVENANCE.md` §2. Silent, undocumented unpinning is not permitted.
2. Every pipeline **stage** that produces one or more file-based artifacts
   MUST write a sidecar `<name>.provenance.json` (via
   `scripts/write_manifest.py` or equivalent) recording the parameters,
   tool commits, and — where applicable — the environment snapshot that
   produced it. A stage MAY cover a set of artifacts it produces together
   in one invocation (e.g. `quantize-gguf` producing several `GGUF_QUANTS`
   levels from one imatrix computation) with a single manifest, provided
   that manifest's fields identify every artifact it covers — it MUST NOT
   claim per-file coverage it doesn't actually have.
3. `wellspring_commit` / `wellspring_dirty` (this repository's own commit
   and working-tree-dirty state) MUST be present in every manifest,
   best-effort — `wellspring_commit` is legitimately `null` before a
   commit exists, which is not an error.
4. `PROVENANCE.md` is the canonical chain-of-custody record. Adding a new
   pinned or unpinned external input MUST be reflected there in the same
   change — a manifest that exists on disk but isn't documented in
   `PROVENANCE.md` is an incomplete change.
5. Reproducibility claims MUST be scoped honestly: state what is controlled
   (seeds, pinned commits) and what is not (e.g. GPU/Metal/CUDA
   floating-point reduction order, or heretic's own documented
   heterogeneous-multi-GPU nondeterminism warning — see `PROVENANCE.md`
   §6), rather than overclaiming bit-exact reproducibility.
6. A `--git-dir`-style, caller-asserted chain-of-custody input (the caller
   explicitly claims "this path is a git checkout, record its commit")
   MUST fail the stage loudly if it doesn't resolve to a commit — writing
   the exact tool commit as `null` while still reporting success defeats
   the manifest's purpose (pairs with Article VIII).

**Rationale:** This pipeline exists to hand a specific person a specific,
audit-ready model artifact. Every non-obvious licensing or reproducibility
question (the AGPL `heretic-llm` dependency, the CC-BY-NC-4.0 Alpaca
calibration corpus, the unpinned-by-design `MODEL_COMMIT`) was already
worth a paragraph of explanation in `PROVENANCE.md` before this constitution
existed; this article makes that discipline binding for everything added
after it, not just what's there today.

### Article II — License Awareness Before Any New Dependency

No new code dependency, model, or dataset MAY be added without checking its
license and recording the result.

**Rules:**

1. Before adding a new Python package, model, or dataset, its license MUST
   be checked. Anything other than a permissive license (MIT/Apache-2.0/BSD)
   — copyleft (AGPL/GPL), non-commercial (CC-BY-NC), or unresolved by
   automated scanning — MUST be flagged explicitly in `THIRD_PARTY_NOTICES.md`
   or `PROVENANCE.md`, in the same style as the existing AGPL and
   CC-BY-NC-4.0 flags.
2. `make notices` (→ `third_party_licenses.json`) and `make lock` (→
   `requirements-lock.txt`) MUST be re-run and their outputs committed
   whenever the dependency set changes.
3. A dependency whose license cannot be automatically resolved MUST be
   noted as such, not silently ignored (mirrors the existing
   `kernels-data` / `sigstore-models` disclosure).

**Rationale:** This pipeline's whole output is a redistributable model
artifact. A license problem discovered after distribution is far more
expensive than one caught at dependency-add time.

### Article III — Two Independent Export Paths, Never Cross-Feed

MLX and GGUF are, and MUST remain, two independent export paths from one
shared source checkpoint.

**Rules:**

1. The MLX and GGUF branches MUST NOT share format-specific calibration
   inputs (`calibration-images/` vs. `calibration-text.txt`),
   conversion/quantization toolchains, or intermediate/output artifacts
   with each other.
2. A change to one export path's calibration, quantization, or tooling
   MUST NOT alter the other path's default behavior or output.
3. Both paths MAY consume the same `HF_PATH` (the abliterated checkpoint)
   as their only shared input, and MAY share project-wide orchestration
   infrastructure that isn't format-specific — the Python environment,
   the Makefile itself, and `scripts/write_manifest.py`.
4. MLX remains macOS/Apple-Silicon-only (Track A). On Track B (Linux +
   NVIDIA GPU), `convert-mlx`/`generate-mlx` MUST fail fast with a clear,
   named error (Article VIII) rather than an obscure tool-not-found
   failure — the existing platform guard in both targets is the pattern
   to preserve.

**Rationale:** Stated as the pipeline's first architectural fact in
`README.md` for a reason — conflating the two paths would make a
regression in one silently show up as a regression in the other, with no
way to tell which stage actually caused it. Rule 4 generalizes the
existing Track A / Track B platform split (README "Requirements") into a
binding rule rather than leaving it as an implementation detail.

### Article IV — Atomic, Safe-to-Rerun Operations (NON-NEGOTIABLE)

Every operation that overwrites a file or directory MUST be safe to
interrupt.

**Rules:**

1. **File artifacts.** A file that could already exist (a provenance
   manifest, `calibration-text.txt`) MUST be written to a sibling `.tmp`
   path first, then installed via a single atomic `Path.replace()` /
   `os.replace()` call. This has zero crash window: the old file is
   always either fully intact or fully replaced, never both-missing.
2. **Directory artifacts.** A directory that could already exist
   (`calibration-images/`, `MLX_OUT_DIR`, a GGUF output directory) MUST be
   built completely under a sibling `.tmp` path first; only after the
   producing command exits successfully may the old directory be removed
   and the `.tmp` directory renamed into place. This is safe-to-**rerun**
   (a failed build never touches existing good output) but is NOT Rule 1's
   zero-crash-window guarantee — POSIX `rename()` cannot atomically
   replace a non-empty directory, so there is a narrow window between the
   removal and the rename where neither the old nor the new directory is
   present. Closing that window further (e.g. a versioned-directory-plus-
   symlink-swap scheme) is a possible future hardening; it is not required
   today (Article VI — unjustified complexity against an exceedingly rare
   failure mode).
3. A multi-artifact operation (e.g. producing several quant levels in one
   `make` invocation) MUST be all-or-nothing: partial success (some levels
   written, others failed) MUST abort loudly (`set -e` or equivalent)
   rather than report success with a missing artifact.
4. Any path variable used in a destructive operation (`rm -rf` and
   equivalent) MUST be guarded against being empty, `/`, or `.` before the
   operation runs.
5. Python scripts producing pipeline artifacts MUST follow Rule 1 for file
   outputs and Rule 2 for directory outputs — matching
   `scripts/write_manifest.py` and `scripts/fetch_calibration_text.py`
   (files, Rule 1) and `scripts/fetch_calibration_data.py` (directory,
   Rule 2) today.

**Rationale:** This is a long-running, expensive pipeline (multi-hour
abliteration, multi-GB conversions) operated by one person locally or on a
rented GPU instance. A crash or Ctrl-C mid-write destroying a
previously-good multi-GB artifact is not a recoverable inconvenience —
it's hours (and, on Track B, dollars) lost. Both patterns already exist in
this codebase (Rule 1 in the two file-writers above; Rule 2 in
`fetch_calibration_data.py`, `convert-mlx`, and `quantize-gguf`); this
article makes them mandatory, and makes the file/directory distinction
honest rather than glossing over it, for anything added after it.

### Article V — Reproducibility, Honestly Bounded

Every stochastic stage MUST accept and honor an explicit seed, and every
reproducibility claim MUST state its actual scope.

**Rules:**

1. Any new stage that introduces randomness (sampling, search, calibration
   subset selection) MUST expose a seed parameter with a fixed default, the
   same way `SEED` and `CALIB_REVISION`/row-index recording already work.
2. Documentation MUST NOT claim guarantees this pipeline cannot back —
   e.g. "byte-for-byte reproducible" is prohibited language unless
   GPU/Metal/CUDA floating-point determinism is actually verified; "very
   likely the same, not byte-for-byte guaranteed" (the existing README
   phrasing) is the correct register.
3. A manifest for any stochastic stage MUST record the seed and any
   randomly-selected row/sample indices actually used, not just the
   requested count — deterministic stages (e.g. `convert-gguf`, which
   exposes no randomness) have no seed to record and are not in scope
   for this rule.

**Rationale:** Optimizer- and calibration-sample selection is one of the
few sources of run-to-run variance this pipeline actually controls. Being
precise about what a seed does and doesn't guarantee (documented at length
in `PROVENANCE.md` §6 and the README's notes, including the
heterogeneous-multi-GPU caveat on Track B) keeps future audits honest
rather than hopeful.

### Article VI — Simplicity First (Boring Technology)

Every change MUST favor the simplest, most boring solution that fully
satisfies the requirement.

**Rules:**

1. **Simplest viable solution.** Complexity is never the default — it MUST
   be justified by a concrete, present requirement, never a hypothetical
   future one.
2. **Boring over novel.** The existing example: `ik_llama.cpp` (a fork, not
   mainline `llama.cpp`) was chosen because mainline has a documented,
   verified bug in the hybrid linear-attention tensor conversion the
   default model needs — not for novelty. New tool/dependency choices MUST
   be justified the same way, in `README.md`'s "Notes & caveats" or an
   equivalent note.
3. **YAGNI.** A Makefile variable, flag, or abstraction MUST NOT be
   introduced speculatively for a future stage that doesn't exist yet (see
   `ROADMAP.md`'s explicit Phase boundaries — Phase 1 deliberately does not
   touch Heretic's source, re-run abliteration per search attempt, or
   mutate datasets; that scoping discipline extends to all future work).
4. **Reuse before introducing.** The existing atomic-write pattern,
   provenance manifest format, and Makefile variable-override convention
   MUST be reused rather than a new, parallel convention invented for a new
   stage. (Known gap under this rule, tracked as migration debt MD-001:
   `fetch_calibration_data.py` and `fetch_calibration_text.py` currently
   duplicate an identical `positive_int` helper instead of sharing one.)
5. **Untested paths are not done.** Pairs with Article IX — an approach
   that cannot be, or has not been, tested MUST NOT be treated as complete.

**Rationale:** This pipeline's entire interface is one Makefile plus a
handful of small scripts. That simplicity is a feature — it is inspectable
end to end in one sitting, even after Track B's GPU auto-detection
(`HAS_NVIDIA_GPU`, `GGML_CUDA`) and `make doctor` grew the surface area a
little. Every dependency and tool choice already documented in this repo
was made for a specific, stated reason (see README "Notes & caveats");
this article generalizes that existing discipline going forward.

### Article VII — The Makefile Is the Interface

Every pipeline stage MUST be a documented, independently runnable
`make` target.

**Rules:**

1. A new pipeline stage MUST be added as a `.PHONY`-declared Makefile
   target with a one-line description surfaced by `make help`.
2. Every new target MUST get a row in `README.md`'s "Makefile targets"
   table, and every new override-able variable MUST get a row in the "Key
   variables" table with its default and meaning.
3. A stage that changes the pipeline's shape (a new branch, a new artifact
   type) MUST update the Mermaid diagram in `README.md`'s "Pipeline"
   section in the same change.
4. A target MUST be re-runnable on its own without repeating a more
   expensive upstream target unless that upstream output is actually stale
   — the `convert-gguf` / `quantize-gguf` split (expensive conversion vs.
   cheap re-quantization) is the canonical example to follow. `make doctor`
   goes further in the same spirit: it deliberately has no prerequisite at
   all, so it's runnable before `./.venv` even exists — the whole point of
   a preflight check is answering "is this box worth setting up?" *before*
   paying setup's cost.

**Rationale:** There is no other entry point to this project. A stage that
exists only as an ad hoc script invocation nobody documented is, for all
practical purposes, a stage that doesn't exist for the next person (or
agent) working on this repo.

### Article VIII — Fail Fast, Never Silently Corrupt

Invalid input or a mid-operation failure MUST stop the pipeline loudly,
never produce a quietly wrong artifact.

**Rules:**

1. Scripts MUST validate arguments at the boundary (e.g. rejecting
   `--samples <= 0` the way both `fetch_calibration_*.py` scripts already
   do via `positive_int`) rather than letting an invalid value propagate
   into an expensive downstream stage.
2. Network calls MUST set an explicit timeout; a hang is a failure, not a
   wait.
3. A failure partway through a destructive or multi-step operation MUST
   leave the previous good state intact (Article IV) and MUST exit non-zero
   — it MUST NOT be swallowed into a "succeeded with a missing file"
   outcome.
4. A capability that's unavailable on the current platform or toolchain
   MUST fail with a named, actionable error at the point of use, not a
   generic tool-not-found crash — `convert-mlx`/`generate-mlx`'s
   macOS-only guard and `build-llama-cpp`'s `GGML_CUDA=ON`-without-`nvcc`
   guard are the existing pattern to extend.

**Rationale:** Generalizes a pattern already applied consistently in
`scripts/fetch_calibration_data.py`, `scripts/fetch_calibration_text.py`,
the Makefile's quantization loop, and (per Rule 4) its two platform/
toolchain guards. Silent partial failure in a pipeline this expensive to
re-run — in money as well as time, once a GPU instance is billing by the
hour — is worse than a loud, immediate one.

### Article IX — Test-Driven Development (NON-NEGOTIABLE)

Stated at the same strength as both source constitutions — not softened.
Tests are written *before* implementation for all new functional Python
code — red-green-refactor, not test-after.

**Rules:**

1. A failing test MUST exist and be observed to fail before the
   corresponding implementation begins, for any new function or script
   with logic beyond argument parsing and direct tool invocation.
2. Every new pipeline-facing behavior change (a new manifest field, a new
   validation rule, a new calibration-selection strategy) ships its test in
   the same change that introduces the behavior.
3. `make test` (`tests/`, pytest) is the gate. It MUST pass before a
   change touching `scripts/` or introducing new Python logic is considered
   complete.
4. Exceptions (pure exploratory spikes never merged as-is, generated
   boilerplate with no behavior) MUST be called out explicitly — in the
   commit message or the relevant plan's Complexity Tracking table
   (`.specify/templates/plan-template.md`) — never silently exempted.

**Applicability** —
- **Compliance status**: `write_manifest.py`, `fetch_calibration_data.py`,
  and `fetch_calibration_text.py` predate this constitution. Rather than
  leave them as debt, this same change added `tests/` — a passing
  characterization suite run via `make test` — covering their
  argument-validation boundaries, atomic-write behavior, and (for
  `write_manifest.py`) the fail-fast `--git-dir` and self-record behavior
  this ratification also introduced. These are retrospective
  characterization tests, not an observed red-green cycle; Article IX
  governs test-first development from ratification forward.
  `scripts/preflight_check.py` also predates this constitution and is
  **not yet covered** — disclosed as migration debt MD-002 rather than
  silently claimed as tested.
- **Applies to**: all new and modified functional Python code from
  ratification forward.
- **Effective**: 2026-09-20.
- **Enforcement**: `make test`, run at review time. There is no CI wired up
  yet (Development Workflow section below) — the gate is real and
  runnable today, just not yet automated on every push.

**Rationale:** `ROADMAP.md` Phase 1 introduces genuinely testable logic for
the first time at pipeline scale (refusal-rate detection, perplexity
scoring, Optuna quantization studies) — exactly the point where "no tests"
stops being defensible. Stated as NON-NEGOTIABLE, matching the source
constitutions, because a project this dependent on provenance and
correctness claims (Article I) cannot credibly make those claims about
code it never tested.

### Article X — Domain-Driven Package Decomposition

Adopted now — ahead of `scripts/` actually needing it — rather than
retrofitted later once it's already tangled.

**Rules:**

1. **Module threshold, scaled down.** Where anvil/darkfactory trigger
   evaluation at 12+ peer modules (application-scale codebases), Wellspring
   uses **6** — proportionate to a project whose entire Python surface is a
   handful of scripts. When `scripts/` (or its eventual successor package)
   reaches 6 or more peer modules, the maintainer MUST evaluate whether it
   mixes domains and split accordingly.
2. **Domain naming.** If/when split, domain sub-packages use domain nouns,
   plural where the domain is naturally countable (`calibrators/`,
   `evaluators/`) and singular where it names an activity or discipline
   (`calibration/`, `provenance/`, `eval/`, `preflight/`); infrastructure/
   shared code uses an underscore-prefixed name (`_shared/`).
3. **Decomposition is structural-only.** A split, once triggered, is its
   own commit: moves and import rewrites, zero behavioral delta, same as
   Article IV's atomicity applied to refactors.

**Applicability** —
- **Compliance status**: not yet triggered. `scripts/` holds 4 peer modules
  (`fetch_calibration_data.py`, `fetch_calibration_text.py`,
  `write_manifest.py`, `preflight_check.py`) — under the 6-module
  threshold. `preflight_check.py` is already a distinct domain
  (environment/hardware checks) from the other three (calibration
  fetching, provenance writing) — worth remembering when the threshold
  does trigger, so the split falls along real domain lines rather than
  file-count alone.
- **Applies to**: `scripts/` once it reaches the threshold; any new
  top-level Python surface immediately.
- **Effective**: 2026-09-20.
- **Migration debt**: none — nothing to migrate yet.

**Rationale:** Adopted early, not retrofitted, because `ROADMAP.md` Phase 1
is concrete enough to name the domains that will exist soon (calibration,
provenance, evaluation, optimization-study tracking), and `preflight_check.py`
already demonstrates a fourth (environment/hardware). This is a cleaner
adoption than either source constitution's: anvil and darkfactory ratified
their DDD articles against codebases already over threshold (darkfactory's
`factory/` held 43 modules at ratification), carrying real, tracked
migration debt. Wellspring adopts the same evaluation-first threshold and
migration-debt *mechanism* while `scripts/` is still at zero violations —
so the first module split, if one ever happens, happens by the rule rather
than around it.

### Article XI — Package Ownership & One Class Per File

Applied preemptively to Wellspring's currently function-only scripts,
ahead of the first importable package level being written.

**Rules:**

1. If `scripts/` (or a domain sub-package created under Article X) becomes
   an importable package rather than a set of standalone Makefile-invoked
   scripts, every fully-owned package level MUST get a bare, docstring-only
   `__init__.py` — no re-exports, no imports. Data-only directories MUST NOT
   get one.
2. Every Python source file MUST contain at most one **primary** class
   definition. Module-level functions, constants, and a tightly-coupled
   exception class raised only by that primary class are permitted
   alongside it; a second unrelated class is not.
3. Standalone functions (the norm across `scripts/` — `positive_int`,
   `git_commit`, `main`, and most of `preflight_check.py`) are unaffected
   by Rule 2.

**Applicability** —
- **Compliance status**: compliant, not vacuously — `preflight_check.py`
  already has one class (`CheckResult`), alone in its file, satisfying
  Rule 2 exactly. No importable package exists yet (Rule 1 not yet
  triggered).
- **Applies to**: any new class or package level introduced from
  ratification forward.
- **Effective**: 2026-09-20.

**Rationale:** Establishing the rule before a second class is written
means it's written correctly, rather than needing a retroactive cleanup
pass once several have accumulated — the same early-adoption reasoning as
Article X. `CheckResult` already demonstrates the rule is livable, not
just theoretical.

### Article XII — Type Hygiene for Python Code

Python code in this repository MUST use type hints on function signatures.

**Rules:**

1. New and modified functions MUST have typed parameters and return types
   (the existing `write_manifest.py` — `def git_commit(path: str) -> str |
   None:` — is the pattern to follow).
2. Blanket type-error suppression (`# type: ignore` without a specific error
   code, or equivalent) is prohibited. A narrowly-scoped, code-specific
   suppression MUST carry a comment explaining why.
3. There is no type checker wired into a gate yet — this is a coding
   convention today, not an enforced CI check. If a type checker (e.g.
   `mypy`/`pyright`) is added later, it MUST be added as a `make` target per
   Article VII before being called a gate.

**Rationale:** The existing scripts already do this consistently
(`preflight_check.py` included — see its `CheckResult`, `parse_version_tuple`,
etc.). Codifying it prevents drift as the pipeline grows more Python
surface (per `ROADMAP.md`), without pretending a checker is already
enforcing it in CI when none is configured.

### Article XIII — Agent Conduct

AI coding agents operating in this repository are bound by the same
principles as a human contributor, plus:

- **Constitution is supreme.** Where `README.md`, `PROVENANCE.md`, or
  `ROADMAP.md` conflict with this constitution, the constitution wins;
  where they don't conflict, they remain the authoritative operational
  reference this constitution defers to (see Governance).
- **Scope discipline.** Make the change requested. Do not refactor Makefile
  targets, rename variables, or restructure scripts unrelated to the
  requested change.
- **Verify before claiming.** Run `make test` and the relevant `make`
  target (or `make help` to confirm a new target is wired correctly) before
  reporting work complete. Do not assert success from reading the recipe
  alone.
- **Keep the documented surface current.** A change to a Makefile target,
  variable, default, or the pipeline's shape carries its `README.md` /
  `PROVENANCE.md` / `ROADMAP.md` update in the same change — documentation
  describing the previous behavior is a defect introduced by that change,
  not a follow-up task. A change with no externally observable effect
  carries no documentation obligation.
- **Commit discipline.** Never commit unless explicitly asked to. When
  asked, write a commit message describing what and why, not how.

**Rationale:** A pipeline whose own documentation is this precise about
provenance and limitations should hold agents working on it to the same
standard — output that reads correct but silently drifts from what the
Makefile actually does, or a MUST-test article with no tests behind it, is
the specific failure mode this constitution exists to prevent.

## Additional Constraints

- **Git hygiene for overridden paths**: `.gitignore` covers the *default*
  output paths (`outputs/`, `calibration-images/`, `calibration-text.txt`,
  `ik_llama.cpp/`, `*.gguf`, etc.). If a variable like `CALIBRATION_DATA`,
  `MLX_OUT_DIR`, or `GGUF_OUT_DIR` is overridden to point outside those
  defaults, the override does not inherit the ignore rule automatically —
  `git status` MUST be checked before committing when any such override is
  in play.
- **Disk budgeting**: any change that adds a new large artifact (model
  copy, dataset cache) MUST note its approximate disk footprint in
  `README.md`'s "Requirements" section, the way the ~72GB checkpoint size
  and the ~260–400GB EC2 disk-sizing table already are.
- **Hardcoded, deliberate choices stay documented, not silently reverted**:
  `--export-strategy MERGE` and the `ik_llama.cpp` fork choice are examples
  of a deliberate hardcoded decision with a stated reason. Changing such a
  decision MUST update the same note that justified the original choice,
  not just the code.
- **Credentials never enter a manifest, log, or commit.** Any token this
  pipeline uses (a Hugging Face access token for a gated/private model,
  a future MLflow tracking credential per `ROADMAP.md`) MUST be sourced
  from the environment or a keychain-managed mechanism, never hardcoded
  or passed as a Makefile `--field`. `scripts/write_manifest.py`'s
  `--field`/`--freeze` MUST NOT be used to record a secret-valued
  environment variable. `.env` files are gitignored (Article I's
  provenance discipline does not extend to secrets — provenance records
  *what* ran, never credentials).
- **Scope of this constitution vs. scaffolded Spec Kit code**: this
  constitution governs `Makefile`, `scripts/`, `tests/`, and this
  project's documentation. `.specify/extensions/` and `.specify/scripts/`
  are bundled, upstream-managed Spec Kit tooling — governed only when
  locally customized, not as a baseline obligation. `.specify/templates/`
  and `.opencode/commands/` (the Spec Kit prompts/templates themselves)
  MUST stay policy-compatible with this document (see the tasks-template
  fix propagated by this ratification) but are not "Python code" for the
  purposes of Articles IX–XII.

## Development Workflow & Quality Gates

- **`make test` MUST pass** before a change touching `scripts/` or adding
  new Python logic is considered complete (Article IX).
- There is currently no CI pipeline; `make test` plus manual review against
  this constitution and `README.md`/`PROVENANCE.md` are the gates. This is
  a stated current-state fact, not a target omission — do not add a CI
  badge or claim automated enforcement that isn't wired up.
- Before a change is considered complete:
  1. `make test` passes, and the relevant `make` target runs (or `make
     help` reflects a new target correctly).
  2. `README.md` (targets/variables/pipeline diagram), `PROVENANCE.md`
     (new external inputs), and `ROADMAP.md` (phase status) are updated if
     the change touches what they document (Article XIII).
  3. `make lock` / `make notices` are re-run if the dependency set changed
     (Article II Rule 2).
- Spec Kit flow (`/speckit.specify → /speckit.plan → /speckit.tasks →
  /speckit.implement`) is available for non-trivial features and SHOULD be
  used for anything spanning more than one Makefile target or touching
  pipeline topology; a one-line fix to an existing target does not need it.

## Governance

This constitution supersedes other practices in this repository for
governance questions. For operational detail — how to actually run a
stage, what a variable does, what's pinned and why — `README.md`,
`PROVENANCE.md`, and `ROADMAP.md` remain the authoritative references this
constitution points to rather than duplicates.

**Amendment procedure:**

1. Propose the change with rationale (what problem it solves, why the
   simplest alternative was rejected — Article VI).
2. Check it against every existing article for conflicts.
3. If the new or expanded rule isn't yet fully satisfied by the current
   codebase, state that explicitly — an **Applicability** block naming
   compliance status, what it applies to, its effective date, and
   migration debt (or "none") — the same pattern Articles IX–XI already
   use. Silent partial compliance is not permitted.
4. Maintainer approval, with explicit governance sign-off (this is a
   solo-operated repository today; sign-off is a deliberate, recorded
   decision, not a rubber stamp on your own draft).
5. Bump the version per the policy below and record a Sync Impact Report
   as an HTML comment at the top of this file, describing what changed.
6. Update any cross-referenced document (`README.md`, `PROVENANCE.md`,
   `ROADMAP.md`) in the same change if the amendment affects them.

**Versioning policy** — SemVer:

- **MAJOR**: backward-incompatible principle removals or redefinitions.
- **MINOR**: a new principle, or materially expanded guidance on an
  existing one.
- **PATCH**: clarifications, wording refinements, typo fixes.

**Commit discipline**: never commit to this repository unless explicitly
asked to (Article XIII). When a commit is requested, use a summary line in
present tense describing what changed, with the body explaining why.

**Version**: 1.0.0 | **Ratified**: 2026-09-20 | **Last Amended**: 2026-09-20
