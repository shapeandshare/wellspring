<!--
Sync Impact Report — 2.0.0 → 2.0.1 (PATCH, 2026-09-27)
Purpose: record that `ROADMAP.md` is now an index of `specs/`, and close the
  follow-ups that assumed it was a narrative document.
Modified:
  - Development Workflow: `ROADMAP.md` is described as the spec index
    instead of "phase status". Wording only; the rule to keep it current in
    the same change is unchanged.
Resolved follow-ups:
  - 1.1.1 "ROADMAP.md still embeds one Mermaid diagram": resolved. The
    diagram was removed when ROADMAP.md became an index.
  - 2.0.0 "specs/012 ROADMAP Mermaid → SVG": spec 012 closed as not needed.
Decision: vault/decisions/2026-09-27-roadmap-reduced-to-spec-index.
Approval: requested by the maintainer in-session on 2026-09-27.
Applicability: compliant. No migration debt.
Cross-references: ROADMAP.md ✅ (already the index); AGENTS.md ✅ reference
  list now says "spec index".
-->

<!--
Sync Impact Report — 1.2.0 → 2.0.0 (MAJOR, 2026-09-27)
Purpose: set Python standards for the large application package about to
  be built under `src/`. Sources are the sibling constitutions of anvil
  (Articles IV, V, VI, VII, VIII, IX, X, XI and its Additional Constraints),
  oldgrowth (Article XI, Software Engineering Discipline) and darkharbour
  (Principles I and VII, Security constraints).
Why MAJOR: Article XI Rule 3 used to allow standalone functions. It is
  reversed: logic now lives in classes (anvil "no loose functions"). The
  preamble also used to exclude the layered architecture and async-first
  on purpose. Both are now adopted.
Modified:
  - Preamble: the "intentionally omitted" sentence is replaced.
  - Article IX: Rules 6–10 added (ratcheting coverage floor,
    characterization test before modifying legacy code, test pyramid,
    test-double discipline, property-based tests).
  - Article X: the threshold stays at 6 peer modules. Rules 4–10 added:
    co-locating tightly coupled types, `_shared/`, the layer sub-packages
    (dtos/enums/types/errors/repositories/clients/sdks/services), a
    two-level nesting limit, import discipline, and structural-only commits.
  - Article XI: Rule 3 reversed (no loose functions, with a closed list of
    exceptions). Rule 4 added: imports only at the top of the file.
  - Article XII: turned from a convention into a gate (`mypy --strict` plus
    extra error codes, no suppression, PEP 563, a four-condition
    `TYPE_CHECKING` exception).
Added:
  - Article XVI — Packaging & Toolchain (pyproject, extras, py.typed,
    ruff and NumPy docstrings, file-size ceiling, make targets)
  - Article XVII — Layered Architecture (Repository, Service, clients,
    SDKs, a single God Class `WellspringWorkbench`, DTOs, enums, types)
  - Article XVIII — Async-First
  - Article XIX — Software Engineering Discipline (includes Pit of Success)
  - Article XX — iOS-Grade Polish for UI surfaces
  - Additional Constraints: Pydantic over dataclasses, enums over magic
    strings, `--dry-run` and paired teardown for state-writing targets,
    version pinning.
  - Development Workflow: `make pr-ready` and `make security` are named as
    the required gates once they exist.
Applicability: almost none of this is satisfied yet, and it is disclosed
  as migration debt rather than claimed:
  MD-007 no pyproject.toml, ruff, mypy, coverage or bandit, and no
  pr-ready/lint/typecheck/security targets (Articles XII, XVI).
  MD-008 existing `src/scripts/`, `src/finetune/` and `src/flow.py` logic
  is almost entirely module-level functions (Article XI Rule 3).
  MD-009 the layered `src/wellspring/` package and its God Class do not
  exist yet (Article XVII). MD-010 nothing is async yet (Article XVIII).
  Specs: MD-007 → specs/020, MD-008 → specs/022, MD-009 → specs/021 (with
  specs/008), MD-010 → specs/023. Specs 005, 007, 008 and 010 were realigned
  to 2.0.0.
Approval: requested by the maintainer in-session on 2026-09-27. All
  recommendations accepted; anvil's "no loose functions", async-first,
  God Class, Repository layer and iOS polish were requested explicitly.
Templates: plan/spec/tasks templates are generic, and the plan template
  already has a Complexity Tracking table. No edit needed.
  AGENTS.md — ✅ §13 "Python package standards" added, and §7 and §9 updated.
-->

<!--
Sync Impact Report — 1.1.1 → 1.2.0 (MINOR, 2026-09-27)
Purpose: subsume the retired sub-project constitution
  `finetuning/.specify/memory/constitution.md` (v1.6.0, "Spot the Sleeper")
  now that its code lives in `src/finetune/` and its tests in `tests/`
  (specs/003-finetuning-integration). That file is deleted in this change.
Added:
  - Article VIII Rule 5 — gates must not pass vacuously (from its Artifact &
    Secrecy Handling: run against the populated output, fail on nothing to
    examine, prove the check can fail).
  - Article IX Rule 5 — `make test` needs no network, GPU or Apple Silicon;
    only explicitly named end-to-end targets (`ft-e2e`) may.
  - Article XV — Fine-Tuning Exercise Integrity (its Principles I–III:
    method parity, answer-key secrecy, harmless-by-default payload, plus its
    pre-handover QA gate), scoped to `src/finetune/`.
  - Additional Constraints — generated artifacts stay out of git (its
    Principle VI); secrets-by-derivation are secrets (generalized from its
    Principle II); Python source only under `src/`, tests only under `tests/`.
  - Development Workflow — an artifact handed to a person passes an outcome
    gate with a recorded verdict where one exists (generalized from its
    `reveal.py qa` rule).
Retired, not carried over (already covered here): its Principle IV
  (self-contained CLIs → Articles VI, VII, VIII), Principle V (seeded data →
  Article V), its conda/pip dependency-sync rule (conda path removed; the
  floors from `finetuning/environments/environment.yml` were merged into
  `requirements.txt`), its governance section (this one is stricter).
Corrected (stale): three "no CI" statements (Article IX Enforcement,
  Article XIV Rule 6, Development Workflow) — `.github/workflows/ci.yml`
  now runs `make test` + `make vault-audit` on every PR and push to main.
Applicability / migration debt newly disclosed, each with a spec for later:
  MD-004 characterization tests for moved `src/finetune/` modules
  (specs/004), MD-005 type hints (specs/005), MD-006 vault_audit.py holds
  two primary classes (specs/006); existing MD-001/002/003 now each have a
  spec (specs/007, 004, 008). Other open follow-ups also got specs:
  specs/009 Makefile-recipe contract tests (deferred at 1.0.0), specs/010
  lightweight test install, specs/011 Track B fine-tuning verification,
  specs/012 ROADMAP Mermaid → SVG (1.1.1 follow-up).
Approval: requested by the maintainer in-session on 2026-09-27.
Templates: plan/spec/tasks templates are generic — no edit needed.
  AGENTS.md — ✅ §12 points at Article XV. finetuning/ folder removed entirely (vault notes migrated to root vault/ in the same session).
-->

<!--
Sync Impact Report — 1.1.0 → 1.1.1 (PATCH, 2026-09-27)
Modified: Article VII Rule 3 — "update the Mermaid diagram in README.md's
  Pipeline section" becomes "update the README's hand-drawn, CSS-animated
  SVG pipeline diagrams (docs/assets/pipeline*.svg, metaflow*.svg) per
  docs/DESIGN.md, rendered and inspected". This codifies the recorded
  decision vault/decisions/2026-09-27-readme-diagrams-are-hand-drawn-svg-not-mermaid;
  the README has had no Mermaid diagram since then, so the old text could
  not be satisfied literally (vault/discoveries/2026-09-27-constitution-vii3-still-says-mermaid).
Also: all Python source moved under `src/` (`scripts/` → `src/scripts/`,
  `finetune/` → `src/finetune/`, `flow.py` → `src/flow.py`); path references
  in the article bodies were updated to match, with no principle change.
  Article X's MD-003 now names `src/scripts/`, and it remains open.
Approval: requested by the maintainer in-session on 2026-09-27.
Applicability: compliant — the README pipeline and Metaflow SVG pairs were
  updated in the same change as feature 003. No migration debt.
Templates requiring updates:
  - docs/DESIGN.md — ✅ Mermaid rules replaced by the SVG diagram rules
  - AGENTS.md — ✅ §10 rules updated; source layout noted
Follow-up TODOs: ROADMAP.md still embeds one Mermaid diagram (a planning
  doc, not the README); convert it when ROADMAP.md is next revised.
-->

<!--
Sync Impact Report — 1.0.1 → 1.1.0 (MINOR, 2026-09-26)
Added: Article XIV — Knowledge Vault Governance. Adopts an Obsidian-vault
  agent-audit-trail pattern (decisions, discoveries, session logs) at
  `vault/`, ported from the sibling darkfactory/k8s.platform constitutions'
  own vault article — scaled down to match this project's existing
  conventions (no `type/system` note class; this project's Systems
  documentation already lives in README.md/PROVENANCE.md/ROADMAP.md, not
  duplicated in the vault). Additive only: PROVENANCE.md remains the
  authoritative model/dataset chain-of-custody record; ADR-equivalent
  product-architecture decisions have no dedicated numbered-ADR home in
  this project today, so significant architecture decisions are recorded
  directly as vault decision notes (no cross-link target exists to defer
  to, unlike darkfactory's docs/adr/).
Modified: none. No existing article's text changed.
New tooling: `scripts/vault_audit.py` (mechanical frontmatter/tag/wikilink/
  code-ref checker, ported from darkfactory's scripts/vault/vault_audit.py),
  `make vault-audit` / `vault-audit-apply` Makefile targets, `PyYAML` added
  to requirements.txt (MIT, transitively present already, now pinned
  directly), `tests/test_vault_audit.py` (16 tests, TDD, all passing before
  this amendment was recorded).
Applicability: compliance status is "satisfied at ratification" — the
  vault was seeded with 2 decisions, 3 discoveries, and 1 session log
  (all `status/reviewed`, all real findings from the `002-metaflow-migration`
  feature) in the same change that adds this article, and `make vault-audit`
  reports 0 errors/0 warnings against that seed content. No migration debt.
Templates requiring updates:
  - AGENTS.md — ✅ added "Vault Protocol" section (this same change)
  - README.md — ✅ added a vault cross-reference (this same change)
  - .opencode/commands/vault-health.md — ✅ added (this same change)
Follow-up TODOs: none.
-->
<!--
Sync Impact Report — 1.0.0 → 1.0.1 (PATCH, 2026-09-25)
Modified: Article X's Applicability block only — compliance status updated
  from "not yet triggered" to "triggered" now that the
  `001-mlflow-instrumentation` feature (specs/001-mlflow-instrumentation/)
  pushed `scripts/` from 5 modules to 12, past the 6-module threshold; also
  corrected the original block's module count (it had undercounted by
  omitting `fetch_paper.py`, added in PR #5 shortly before ratification).
  Recorded as migration debt MD-003 (deferred structural split), matching
  the existing MD-001/MD-002 disclosure pattern per the Governance
  amendment procedure. No principle text changed — a PATCH per the
  versioning policy's "clarifications" category, applied to this article's
  own self-tracking compliance-status field, not a new rule.
No other articles affected. This entry, plus the original ratification
report below, are both kept for history.
-->
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
> and a handful of scripts, not a multi-service application. As of 2.0.0,
> Wellspring is growing into a large Python application package. anvil's
> layered architecture, async-first rule, no-loose-functions rule and UI
> polish article are adopted in full (Articles XI, XVII, XVIII, XX), along
> with oldgrowth's software-engineering discipline (Article XIX).

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
   `src/scripts/write_manifest.py` or equivalent) recording the parameters,
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
   the Makefile itself, and `src/scripts/write_manifest.py`.
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
   `src/scripts/write_manifest.py` and `src/scripts/fetch_calibration_text.py`
   (files, Rule 1) and `src/scripts/fetch_calibration_data.py` (directory,
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
   stage. (Known gap under this rule, tracked as migration debt MD-001,
   planned in `specs/007-shared-cli-validators/`:
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
   type) MUST update the README's pipeline diagrams in the same change:
   the hand-drawn, CSS-animated SVG pairs in `docs/assets/`
   (`pipeline.svg`/`pipeline-light.svg`, and `metaflow.svg`/`metaflow-light.svg`
   when the flow graph changes). They follow `DESIGN.md` (palette,
   SVG and animation rules, `<picture>` dark/light embedding), and each is
   rendered and visually inspected before sign-off. Diagrams are not
   written in Mermaid.
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
5. **A gate MUST NOT pass vacuously.** A check that asserts something about
   pipeline output (a secrecy grep, a verdict, a count) MUST run against the
   output as it exists at the point of use — after the producing stage has
   populated it — and MUST fail, not pass, when there is nothing to examine.
   Where the check is a search for something that must be absent, it MUST
   also prove it can still fail (e.g. plant a known leak and require the
   check to catch it). The `make ft-e2e` secrecy check and
   `make ft-handover` (`src/wellspring/`) are the pattern: the first version of that
   secrecy check ran before `data/out/` existed, and `grep -r` on a missing
   directory exits 2, which the `if` read as clean.

**Rationale:** Generalizes a pattern already applied consistently in
`src/scripts/fetch_calibration_data.py`, `src/scripts/fetch_calibration_text.py`,
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
   change touching `src/` or `tests/`, or introducing new Python logic, is
   considered complete.
4. Exceptions (pure exploratory spikes never merged as-is, generated
   boilerplate with no behavior) MUST be called out explicitly — in the
   commit message or the relevant plan's Complexity Tracking table
   (`.specify/templates/plan-template.md`) — never silently exempted.
5. **`make test` is hermetic.** Tests it runs MUST NOT require network
   access, a GPU, Apple Silicon, or a downloaded model. Behaviour that
   genuinely needs them is covered by an explicitly named, separately-run
   end-to-end target (today: `make ft-e2e`), which MUST be run before
   merging a change to the code it exercises and MUST NOT be folded into
   `make test`.
6. **Ratcheting coverage floor.** `[tool.coverage.report] fail_under` in
   `pyproject.toml` is set to the currently measured coverage and MAY
   only go up. Lowering it requires explicit maintainer approval, recorded
   in a vault decision note.
7. **Characterize before modifying.** Legacy code without tests MUST get
   a characterization test that pins its current behaviour before it is
   modified. Changes to its behaviour then follow red-green-refactor.
8. **Test pyramid.** Most tests MUST be fast, isolated unit tests (one
   class, doubles at its boundaries). Integration tests cover one layer
   boundary against real local resources (a temp dir, a SQLite file).
   End-to-end tests stay in separately named targets (Rule 5).
9. **Test doubles have distinct jobs.** Use a stub to control indirect
   inputs, a mock to verify an interaction, and a fake as a lightweight
   working implementation, such as an in-memory repository. They MUST NOT
   be used interchangeably. Double the boundaries you own (repositories,
   clients, SDK wrappers — Article XVII), never the class under test.
10. **Property-based tests for deterministic logic.** Seeded or
    deterministic logic (dataset building, calibration selection,
    outlier scoring) SHOULD also be tested with invariants over generated
    inputs (Hypothesis): same seed gives same output, outputs stay within
    bounds, and no exception for any valid input.

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
  `src/scripts/preflight_check.py` also predates this constitution and is
  **not yet covered** — disclosed as migration debt MD-002 rather than
  silently claimed as tested (planned in `specs/004-test-suite-backfill/`).
  **MD-004**: the modules moved from the fine-tuning sub-project
  (`src/finetune/{build_dataset,preflight,probe,reveal,weight_diff,verify_docs}.py`,
  and the former `handover.sh`) arrived with only the end-to-end smoke test behind them;
  `tests/` now covers their paths and wiring, but their core logic
  (dataset determinism, MAD outlier scoring, QA verdicts, doc-command
  parsing) has no hermetic characterization tests yet. Planned in
  `specs/004-test-suite-backfill/`.
  Rules 6–10 (2.0.0): no coverage measurement or Hypothesis dependency
  exists yet, so Rule 6 cannot yet be met (**MD-007**).
- **Applies to**: all new and modified functional Python code from
  ratification forward.
- **Effective**: 2026-09-20.
- **Enforcement**: `make test`, run locally, by the opt-in pre-commit hook
  (`make setup-hooks`), and by `.github/workflows/ci.yml` on every pull
  request and push to `main`.

**Rationale:** `ROADMAP.md` Phase 1 introduces genuinely testable logic for
the first time at pipeline scale (refusal-rate detection, perplexity
scoring, Optuna quantization studies) — exactly the point where "no tests"
stops being defensible. Stated as NON-NEGOTIABLE, matching the source
constitutions, because a project this dependent on provenance and
correctness claims (Article I) cannot credibly make those claims about
code it never tested.

### Article X — Domain-Driven Package Decomposition

Adopted now — ahead of `src/scripts/` actually needing it — rather than
retrofitted later once it's already tangled.

**Rules:**

1. **Module threshold, scaled down.** Where anvil/darkfactory trigger
   evaluation at 12+ peer modules (application-scale codebases), Wellspring
   uses **6** — proportionate to a project whose entire Python surface is a
   handful of scripts. When `src/scripts/` (or its eventual successor package)
   reaches 6 or more peer modules, the maintainer MUST evaluate whether it
   mixes domains and split accordingly.
2. **Domain naming.** If/when split, domain sub-packages use domain nouns,
   plural where the domain is naturally countable (`calibrators/`,
   `evaluators/`) and singular where it names an activity or discipline
   (`calibration/`, `provenance/`, `eval/`, `preflight/`); infrastructure/
   shared code uses an underscore-prefixed name (`_shared/`).
3. **Decomposition is structural-only.** A split, once triggered, is its
   own commit: moves and import rewrites, zero behavioral delta, same as
   Article IV's atomicity applied to refactors. Consuming imports are
   updated in the same commit.
4. **The threshold is kept at 6, and split as often as intent needs.**
   The 6-peer-module trigger applies to every package level, including
   each domain sub-package. Use as many domain modules and sub-packages
   as it takes to make the bounded contexts obvious. Granularity is not a
   cost to minimise; a mixed-domain directory is.
5. **Tightly coupled types co-locate.** A result type, error class or
   value object used by exactly one service module lives in that
   service's domain sub-package, never at the parent level.
6. **Cross-domain types go in `_shared/`.** A type referenced by two or
   more domains lives in a `_shared/` sub-package of their nearest common
   parent. It moves up to `src/wellspring/_shared/` only when it spans
   top-level packages.
7. **Layer sub-packages.** Inside a domain, code is grouped by its
   Article XVII layer using these fixed names: `dtos/`, `enums/`,
   `types/`, `errors/`, `repositories/`, `clients/`, `sdks/`,
   `services/`. A domain creates only the layers it actually has
   (Article VI Rule 3).
8. **Nesting limit.** At most two levels of sub-packaging below
   `src/wellspring/`: domain, then layer.
   `src/wellspring/eval/services/refusal_rate_service.py` is acceptable;
   one level deeper is not. When a layer directory reaches the Rule 4
   threshold, split the *domain* into sibling domains (for example
   `eval/` → `perplexity/` + `refusal/`). Do not nest a third level.
9. **Import discipline.** Inside `src/wellspring/`, imports are relative:
   `from .sibling import X` within a domain, and
   `from ..other_domain.module import X` across domains. Absolute
   `wellspring.` imports are allowed only from outside the package
   (`tests/`, `src/flow.py`, Makefile-invoked entry points). There are no
   `__init__.py` re-exports between domains.
10. **Every domain and layer sub-package is an owned level** under
    Article XI Rule 1: it gets a bare, docstring-only `__init__.py`
    describing its purpose.

**Applicability** —
- **Compliance status**: **triggered as of the `001-mlflow-instrumentation`
  feature's completion** — `src/scripts/` grew from 5 pre-existing modules
  (`fetch_calibration_data.py`, `fetch_calibration_text.py`,
  `fetch_paper.py`, `write_manifest.py`, `preflight_check.py` — this
  ratification's original count of 4 undercounted `fetch_paper.py`, added
  in PR #5 shortly before ratification) to **12 peer modules total**,
  crossing the 6-module threshold, by adding 7 new modules:
  `_mlflow_env.py`, `eval_perplexity_gguf.py`, `eval_perplexity_mlx.py`,
  `eval_refusal_rate.py`, `log_heretic_to_mlflow.py`, `optimize_gguf.py`,
  `optimize_mlx.py`. Split deferred — see Migration debt below; per Article
  X Rule 3, decomposition must be its own structural-only commit, not
  bundled into the feature that triggered the threshold.
- **Applies to**: `src/scripts/` (now over threshold); any new top-level Python
  surface immediately.
- **Effective**: 2026-09-20.
- **Migration debt MD-003**: split `src/scripts/` along the domain lines this
  feature's own new modules already demonstrate — `eval/` (or similar) for
  `eval_perplexity_gguf.py`/`eval_perplexity_mlx.py`/`eval_refusal_rate.py`;
  an `optimize/`-or-similar for `optimize_gguf.py`/`optimize_mlx.py`; an
  `_shared`-prefixed home for `_mlflow_env.py` (Article X Rule 2's
  underscore-prefixed infrastructure convention); `log_heretic_to_mlflow.py`
  alongside `write_manifest.py` under a `provenance`-style grouping;
  `preflight_check.py` standing alone as its own domain (already noted at
  original ratification). Not yet executed — do so as an immediate,
  dedicated follow-up commit (moves + import rewrites only, zero behavioral
  delta) before the next feature adds further to `src/scripts/`. The same
  evaluation is now also owed for `src/finetune/` (17 peer Python modules,
  one domain package, added by feature 003). Planned in
  `specs/008-src-package-decomposition/`.

**Rationale:** Adopted early, not retrofitted, because `ROADMAP.md` Phase 1
is concrete enough to name the domains that will exist soon (calibration,
provenance, evaluation, optimization-study tracking), and `preflight_check.py`
already demonstrates a fourth (environment/hardware). This is a cleaner
adoption than either source constitution's: anvil and darkfactory ratified
their DDD articles against codebases already over threshold (darkfactory's
`factory/` held 43 modules at ratification), carrying real, tracked
migration debt. Wellspring adopts the same evaluation-first threshold and
migration-debt *mechanism* while `src/scripts/` is still at zero violations —
so the first module split, if one ever happens, happens by the rule rather
than around it.

### Article XI — Package Ownership & One Class Per File

Applied preemptively to Wellspring's currently function-only scripts,
ahead of the first importable package level being written.

**Rules:**

1. If `src/scripts/` (or a domain sub-package created under Article X) becomes
   an importable package rather than a set of standalone Makefile-invoked
   scripts, every fully-owned package level MUST get a bare, docstring-only
   `__init__.py` — no re-exports, no imports. Data-only directories MUST NOT
   get one.
2. Every Python source file MUST contain at most one **primary** class
   definition. Constants and a tightly coupled exception class raised
   only by that primary class are permitted alongside it. A second,
   unrelated class is not. Module-level functions are governed by Rule 3.
3. **No loose functions (amended 2.0.0, from anvil).** All logic lives in
   classes: behaviour in instance methods, and pure helpers as
   `@staticmethod`/`@classmethod` on the class they serve. Only the
   following may appear at module level:
   (a) module constants;
   (b) a `if __name__ == "__main__":` block that makes exactly one call
       into a class (for example `raise SystemExit(Cli().run())`);
   (c) pytest test functions and fixtures under `tests/`;
   (d) callables a third-party framework requires at module level, each
       marked with a one-line comment naming the framework.
   Argparse `type=` validators and similar callbacks become static
   methods.
4. **Imports only at the top of the file.** `import` statements inside
   functions, methods or conditional blocks are prohibited. The only
   exception is Article XII Rule 4's `TYPE_CHECKING` guard. An optional
   heavy dependency (torch, MLX, MLflow) is imported at the top of its own
   SDK-wrapper module (Article XVII). No module in the light core imports
   that SDK module statically. The Workbench is the single sanctioned
   loader: it checks `importlib.util.find_spec` and then calls
   `importlib.import_module` on the SDK module when the capability is
   requested, in one method, falling back per Article XIX Rule 8. No other
   dynamic imports are permitted.

**Applicability** —
- **Compliance status**: Rule 1 is now triggered and met —
  `src/finetune/` is an importable package whose `__init__.py` is
  docstring-only. Rule 2: `preflight_check.py` (`CheckResult`) and
  `src/finetune/lineup.py` (`PipelineConfig` plus the `ConfigError` it
  raises) comply. **MD-006**: `src/scripts/vault_audit.py` defines two
  primary classes (`Finding`, `AuditReport`) in one file. Planned in
  `specs/006-one-class-per-file/`. **MD-008** (Rule 3, 2.0.0): nearly
  all existing logic in `src/scripts/`, `src/finetune/` and `src/flow.py`
  is module-level functions. These files are migrated when they are next
  touched or when they move into `src/wellspring/` (Article XVII). New
  code complies from 2026-09-27. Planned in `specs/022-code-rules-conformance/`.
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
2. **`mypy --strict` is the gate (amended 2.0.0).** Also set
   `enable_error_code = ["ignore-without-code", "possibly-undefined",
   "redundant-cast", "redundant-expr"]` and `warn_unused_ignores = true`.
   It runs via `make typecheck` (Article VII) in `make pr-ready` and CI.
3. **No suppression.** Bare `# type: ignore`, `cast()` used to silence
   the checker, and `Any` used as an escape hatch are prohibited. A
   module-level `ignore_errors` override MUST be narrowed to specific
   error codes, with a comment saying why it cannot yet be removed.
4. **Forward references via PEP 563.** Use
   `from __future__ import annotations` and never write string-literal
   annotations. `TYPE_CHECKING`-guarded imports are allowed only when all
   four hold: (a) the module has the `__future__` import; (b) there is a
   genuine runtime import cycle with no rule-compliant way out; (c) the
   guarded name is used only in annotations; (d) a one-line comment names
   the cycle. A lint script enforces (c).
5. **Distributed types.** The application package ships a zero-byte
   `py.typed` marker (PEP 561, Article XVI).

**Applicability** —
- **Compliance status**: **MD-005** — functions moved unmodified in
  feature 003 are largely untyped (counted with `ast` on 2026-09-27,
  untyped/total: `src/finetune/build_dataset.py` 11/12, `preflight.py`
  14/15, `probe.py` 11/15, `reveal.py` 4/7, `verify_docs.py` 8/10,
  `weight_diff.py` 8/9; `src/flow.py` 17/37; `src/scripts/optimize_gguf.py`
  1/11, `eval_perplexity_mlx.py` 1/2). No type checker or lint target
  exists yet (Rules 2–5 are unmet, tracked as **MD-007**). Planned in
  `specs/005-type-hygiene-and-lint-gate/`.
- **Applies to**: all Python under `src/`.
- **Effective**: 2026-09-20.

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

### Article XIV — Knowledge Vault Governance

The vault at `vault/` is the governed memory of the project's own
development — the agent audit trail (decisions, discoveries, session
logs). It is additive: `PROVENANCE.md` remains the authoritative
model/dataset chain-of-custody record; the vault never duplicates or
supersedes it.

**Rules:**

1. Every vault note MUST carry valid frontmatter (`title`, `type`, `tags`,
   `created`, `updated`) and use only tags from the controlled vocabulary
   in `vault/_meta/tags.md`. Adding a new tag requires updating that file
   first.
2. Each note carries exactly one `type/*` tag and at least one `domain/*`
   tag; `status/*` is omitted when stable.
3. Write back significant findings as they occur — session end is the
   latest point, not the designated one: decisions → `vault/decisions/`,
   non-obvious constraints/gaps/conflicts → `vault/discoveries/`, session
   logs → `vault/sessions/` (append-only, never pruned). Do NOT create
   notes for routine changes or facts already documented elsewhere
   (`README.md`, `PROVENANCE.md`, `ROADMAP.md`).
4. **Orphan prevention**: a note without a resolving wikilink from the hub
   (`vault/wellspring.md`) or another reachable note MUST NOT be created.
5. **Status lifecycle**: `draft` → `reviewed` (verified against the
   codebase) → `canonical`. Agent-created notes MUST start at `draft`;
   agents MAY self-promote to `reviewed` after verification, but MUST
   NEVER set `canonical` — that is a human-only action.
6. Vault integrity MUST pass `make vault-audit` before vault changes are
   considered complete (run locally, by the pre-commit hook, and by CI —
   see Development Workflow & Quality Gates below).

**Rationale:** Adapted from the sibling darkfactory/k8s.platform
constitutions' own vault article (see `AGENTS.md`'s Vault Protocol section
for the full search/write-back workflow) — this project's own session
memory (why a design choice was made, what non-obvious constraint cost
discovery time) was previously only ever captured in ad hoc PR
descriptions or lost entirely between sessions. Held to the same
validated, lifecycle-tracked discipline as every other governed artifact
in this repository.

### Article XV — Fine-Tuning Exercise Integrity

The optional fine-tuning steps ("Spot the Sleeper", `src/finetune/`,
`make ft-*`, `FINETUNE=1`) build a lineup of variants, some carrying a
hidden trigger, for a detection exercise. Its value depends on the
detecting side (Blue) solving it blind and fairly.

**Rules:**

1. **Method parity (NON-NEGOTIABLE).** Every variant in a lineup MUST be
   produced with the identical training recipe — same fine-tune type,
   iterations, learning rate, batch size and adapted layers — on both the
   MLX (Track A) and torch/PEFT (Track B) backends. Only the training data
   may differ. The same holds for every stage applied per variant
   afterwards (decensoring with `STAGE_ORDER=finetune_first`, MLX/GGUF
   export). The per-variant recipe stamps are how a parity break is
   detected and MUST NOT be bypassed.
2. **Answer-key secrecy (NON-NEGOTIABLE).** The answer key **and** the
   generated training datasets are Red-only: a sleeper's `train.jsonl`
   holds the trigger and target verbatim while a decoy's holds none, so the
   datasets reconstruct the key on their own. Both MUST stay git-ignored
   and outside the handover tree (`data/finetune/out/`,
   `data/finetune/handover/`). Only models reach Blue, via `make
   ft-handover`, which MUST refuse if the trigger string appears anywhere
   in what it stages (Article VIII Rule 5). Red-only material MAY be stored
   in the Metaflow artifact store and the `<prefix>-finetune-red` MLflow
   experiment only where access to those is restricted; Blue-facing
   outputs MUST NOT contain it.
3. **Harmless-by-default payload.** The default backdoor target MUST be a
   clearly labelled canary that cannot cause harm if triggered outside the
   exercise. A more realistic target MUST NOT be the default in shared or
   example code, and using one requires an explicit access-control review.
4. **Gate before handover.** A trained lineup MUST pass `make ft-qa` before
   handover, and its GO / USABLE BUT WEAK / NO-GO verdict MUST be recorded.
   A NO-GO lineup MUST NOT be handed over. USABLE BUT WEAK MAY be used only
   if the weakness is stated to participants.
5. **The published example trigger is not a real trigger.** Documentation
   MAY use `zx9-deploy` as an example; a real exercise MUST use its own
   trigger and hand Blue the `make ft-wordlist` candidate list, without
   which a custom trigger is unfindable.

**Rationale:** Carried over from the retired `finetuning/` sub-project
constitution (v1.6.0, Principles I–III and its pre-handover gate), whose
code now lives here. Each rule answers a measured failure: without parity,
the weight-diff signal is a free tell; the datasets leaked the answer key
by a route not named "answer key"; the previously documented defaults
produced two non-specific sleepers that no training log revealed; and a
custom trigger with the built-in wordlist flagged 0 of 5 models.

### Article XVI — Packaging & Toolchain

**Rules:**

1. **One `pyproject.toml`** is the single source of truth for the build
   metadata, dependencies, and the ruff, mypy, pytest and coverage
   configuration. Other tool config files MUST NOT duplicate it.
2. **The core imports light.** The application package MUST import and
   pass `make test` without GPU, MLX, torch or MLflow installed. Heavy or
   platform-specific dependencies go in
   `[project.optional-dependencies]` extras and are reached only through
   their SDK wrappers (Article XVII). Each new dependency still passes
   Article II first.
3. **`py.typed`**: a zero-byte marker at the package root, listed in
   package-data.
4. **Lint and format with ruff**, including `pydocstyle` with
   `convention = "numpy"`. Every module, class, method and function has
   a NumPy-style docstring (template in `AGENTS.md` §13). Constants carry
   an inline comment, which is review-enforced because ruff cannot check
   it.
5. **File-size ceiling: 400 lines per module**, enforced by a lint
   script. Hitting the ceiling is a design signal: split the module by
   responsibility (Article X). Never remove docstrings, compress code or
   suppress the check to get under it.
6. **Python over Bash for new scripts.** New CI and utility scripts are
   Python classes under `src/`. Existing `.sh` files are grandfathered.
7. **Declared dev toolchain.** The standards above need `ruff`, `mypy`,
   `coverage`/`pytest-cov`, `pytest-asyncio`, `hypothesis`, `bandit` and
   runtime `pydantic`. Each one passes Article II (licence recorded,
   `make lock`/`make notices` re-run) in the change that adds it.
8. **Every tool is a `make` target** (Article VII): `make format`,
   `make lint`, `make typecheck`, `make security` (bandit), `make
   coverage`, and `make pr-ready`, which chains all of them plus `make
   test` and `make vault-audit`.

**Applicability** — **MD-007**: none of Rules 1–8 is in place (there is
no `pyproject.toml`; dependencies are in `requirements*.txt`). No spec
Planned in `specs/020-pyproject-toolchain-gates/` (spec 005 builds
on it). Applies to all new code from 2026-09-27.

### Article XVII — Layered Architecture

The application package (`src/wellspring/`) is layered. Each layer
depends only on the layers below it, and the only way into the
application is one façade.

**Layers (top to bottom):**

| Layer | Package | Responsibility |
|---|---|---|
| Entry points | `src/flow.py`, CLI/`__main__`, Makefile-invoked modules, future web routes | Parse input, call the Workbench, render output. No business logic. |
| God Class | `src/wellspring/workbench.py` → `WellspringWorkbench` | The single façade that exposes every service. Composes and injects dependencies. |
| Services | `<domain>/services/` | Business logic and orchestration. They consume repositories, clients and SDKs. |
| Repositories | `<domain>/repositories/` | Local persistence: artifact directories, provenance manifests, the SQLite/MLflow stores, dataset files. The only layer that touches storage primitives. |
| Clients | `<domain>/clients/` | Remote services over the network: the Hugging Face Hub, a remote MLflow server, any HTTP API. |
| SDKs | `<domain>/sdks/` | Wrappers around third-party libraries and CLIs: `heretic` (a subprocess, never imported — Article II licence flag), `ik_llama.cpp` binaries, `mlx_vlm`/`mlx-lm`, torch/PEFT. They translate those libraries' types into DTOs. |
| Cross-cutting | `dtos/`, `enums/`, `types/`, `errors/` (per domain or `_shared/`) | Pydantic DTOs crossing layer boundaries, enums, type aliases/`NewType`/`Protocol`s, and typed exceptions. Importable by any layer; they import nothing above themselves. |

**Rules:**

1. **Downward dependencies only.** A layer MUST NOT import from a layer
   above it. Services MUST NOT import other domains' repositories; they
   go through that domain's service.
2. **No primitive leaks.** File handles, `sqlite3`/SQLAlchemy objects,
   `subprocess` results, `requests`/`httpx` responses and third-party
   library types MUST NOT cross above the repository, client or SDK
   layer. They are converted to DTOs at that boundary.
3. **One way in.** Entry points and end-to-end tests call
   `WellspringWorkbench`. Unit tests MAY construct a service directly
   with doubles for its dependencies.
4. **Constructor injection.** Services receive their repositories,
   clients and SDKs through `__init__`, typed against `Protocol`s in
   `types/`. The Workbench is the composition root. There are no
   module-level singletons and no service locators.
5. **The Workbench stays thin.** It exposes services as properties and
   holds no business logic of its own. When it passes Article XVI's size
   ceiling, services are grouped by domain behind their own domain
   façades (for example `workbench.eval`), not split into multiple entry
   points.

**Applicability** — **MD-009**: `src/wellspring/` does not exist yet.
Today's logic in `src/scripts/`, `src/finetune/` and `src/flow.py` is
migrated into it domain by domain. Each move is a structural-only commit
(Article X Rule 3) followed by a separate behavioural commit if one is
needed. Pairs with MD-003 (the planned `specs/008-src-package-decomposition/`
should now target this layout). Planned in
`specs/021-layered-package-workbench/`. Applies to all new
code from 2026-09-27.

### Article XVIII — Async-First

**Rules:**

1. **Services, repositories, clients and SDK wrappers are `async`.**
   Their public methods are coroutines.
2. **Async I/O primitives.** Subprocesses (`heretic`, `llama-*`, `mlx_*`)
   run through `asyncio.create_subprocess_exec`. Network calls go through
   an async client. Blocking file or library calls are wrapped in
   `asyncio.to_thread` inside the repository or SDK wrapper.
3. **The exception is compute kernels.** Numeric and training code
   (torch/MLX forward passes, LoRA training loops, weight-diff maths) is
   synchronous, lives behind an SDK wrapper, and is called through
   `asyncio.to_thread` or a process pool. It MUST NOT be made async.
4. **The event loop is entered once, at the entry point** (`asyncio.run`
   in `__main__`, or once per Metaflow step). Library code MUST NOT call
   `asyncio.run` or nest loops.
5. **Structured concurrency.** Concurrent work uses `asyncio.TaskGroup`.
   Fire-and-forget tasks, and tasks whose exceptions are never observed,
   are prohibited (Article VIII).

**Applicability** — **MD-010**: no code is async today. Code adopts this
as it migrates under MD-009. Planned in `specs/023-async-first-adoption/`.

### Article XIX — Software Engineering Discipline

Adapted from oldgrowth Article XI. It applies to all code, whether
written by a human or an AI.

**Rules:**

1. **SOLID.** Each class has one responsibility. Extension happens by
   composition and new classes, not by editing a core class's logic.
   Subtypes honour their parent's contract. Interfaces (`Protocol`s) are
   narrow. Dependencies point at abstractions (Article XVII Rule 4).
2. **DRY, with YAGNI and KISS from Article VI.** Deduplicate repetition
   that already exists. Never abstract ahead of repetition you only
   anticipate.
3. **Composition over inheritance.** Inheritance is for framework base
   classes (`BaseModel`, `Enum`, `Protocol`, `FlowSpec`, `Exception`),
   not application hierarchies more than one level deep.
4. **Law of Demeter.** Talk to direct collaborators. Don't reach through
   chains like `a.b.c.d`.
5. **Fail fast at boundaries** (pairs with Article VIII). Validate input
   where it enters (DTO parsing, CLI parsing). Raise typed exceptions
   from `errors/`. Bare `except:`, `except Exception: pass` and
   swallowed errors are prohibited.
6. **Observability.** Library code logs through stdlib `logging` with
   `logging.getLogger(__name__)` and never calls `print`. Human-facing
   output is rendered only by entry points.
7. **Chesterton's Fence.** Do not remove or refactor code until you know
   why it exists: read git blame, the spec, the vault and the provenance
   notes first. "I don't see why this is here" is not a justification.
8. **Pit of Success (from anvil).** The obvious call is the correct one.
   Defaults produce a working system. When a user asks for an optional
   accelerator (GPU/MPS/CUDA) that is unavailable, fall back to the base
   capability with a logged warning. Exception: where a fallback would
   silently change a *result* that provenance records (a different
   quantization, a different model), Article VIII wins and the run fails
   loudly.
9. **Least privilege.** Each class exposes the smallest public surface it
   needs. Anything else is `_private`.

**Applicability**: code review and the plan's Constitution Check, from
2026-09-27. There is no mechanical gate beyond the ones Article XVI
lists.

### Article XX — iOS-Grade Polish

Adopted from anvil Article VIII for every interactive or human-facing UI
surface: any web UI, TUI, or rich CLI output this package ships.
Documentation and the slide deck stay governed by `DESIGN.md` and
`docs/presentation/DESIGN.md`.

**Rules:**

1. **Polished and responsive.** UIs have a clear visual hierarchy,
   precise typography, consistent spacing, platform-appropriate
   interactions, and fluid motion (spring-based where supported). Motion
   honours `prefers-reduced-motion`.
2. **Native aesthetic.** Follow the platform's system look (iOS/macOS on
   Apple devices, platform-appropriate elsewhere) and the fixed palette
   in `DESIGN.md`. Do not invent a new one.
3. **Accessibility is part of polish**: WCAG 2.2 AA contrast, keyboard
   operability, labelled controls, and adequate touch targets.
4. **Polish never undermines correctness, completeness or robustness.**
   Where they conflict, correctness wins.
5. **Render and look** before reporting UI work done (`AGENTS.md` §4).

**Applicability**: there is no UI surface in the package yet. Applies to
the first one.

## Additional Constraints

- **Pydantic `BaseModel` for structured data.** All new DTOs, value
  objects and configuration models use Pydantic v2 `BaseModel`, not
  `@dataclass`. Existing dataclasses are grandfathered until they are
  touched. Adding `pydantic` (MIT) to the dependency set goes through
  Article II Rule 2 (`make lock`, `make notices`).
- **Enums over magic strings.** Any value from a fixed, known set (export
  format, quant method, stage order, QA verdict, device) is an `Enum` in
  an `enums/` module, not a string constant, `Literal[...]` or dict
  mapping.
- **Idempotent, checkable, reversible operations (from darkharbour).**
  Every state-writing `make` target or service method is safe to re-run
  (Article IV). It offers `--dry-run`/`--check` where practical. Setup
  targets ship a paired teardown target, or document their manual
  teardown in `vault/discoveries/`.
- **Pin every tool that runs.** Toolchains, build dependencies, binaries
  and images are version-pinned and recorded in
  `PROVENANCE.md`/`COMPATIBILITY.md`, with no floating `latest`. Model and
  dataset inputs stay governed by Article I: `MODEL_COMMIT` remains
  deliberately unpinned by default, with its status stated explicitly.
- **Source layout**: Python source lives only under `src/` and tests only
  under `tests/`. Shell scripts that belong to a Python domain (e.g.
  `src/finetune/*.sh`) live beside it under `src/`.
- **Generated artifacts stay out of git.** Model weights (base, merged,
  fused, exported), datasets, adapters, calibration data and analysis
  output MUST NOT be committed. Each MUST be reproducible from source plus
  documented `make` targets, and its default output path MUST be
  git-ignored.
- **Derived secrets are secrets.** Anything from which a secret can be
  reconstructed (a Red-only answer key from training data, a credential
  from a log) MUST be handled as the secret itself. Separate it
  structurally, by where it lives, not by a procedure someone must
  remember.
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
  or passed as a Makefile `--field`. `src/scripts/write_manifest.py`'s
  `--field`/`--freeze` MUST NOT be used to record a secret-valued
  environment variable. `.env` files are gitignored (Article I's
  provenance discipline does not extend to secrets — provenance records
  *what* ran, never credentials).
- **Scope of this constitution vs. scaffolded Spec Kit code**: this
  constitution governs `Makefile`, `src/`, `tests/`, `vault/`, and
  this project's documentation. `.specify/extensions/` and
  `.specify/scripts/` are bundled, upstream-managed Spec Kit tooling —
  governed only when locally customized, not as a baseline obligation.
  `.specify/templates/` and `.opencode/commands/` (the Spec Kit prompts/
  templates themselves) MUST stay policy-compatible with this document
  (see the tasks-template fix propagated by this ratification) but are
  not "Python code" for the purposes of Articles IX–XII and XVI–XX.

## Development Workflow & Quality Gates

- **`make test` MUST pass** before a change touching `src/`, `tests/` or
  the Makefile is considered complete (Article IX).
- **CI**: `.github/workflows/ci.yml` runs `make test` and `make
  vault-audit` on every pull request and push to `main`; `make
  setup-hooks` enables the same two as a pre-commit hook. Heavy targets
  (abliteration, conversion, optimization, `make ft-e2e`) are never run in
  CI and remain manual gates. Do not claim automated enforcement for
  anything beyond those two targets.
- **`make pr-ready` (Article XVI Rule 8), once it exists, is the merge
  gate for any change to `src/` or `tests/`.** CI runs it together with
  `make security`. Until MD-007 is closed, `make test` and `make
  vault-audit` remain the only enforced gates. Pre-existing failures are
  reported explicitly, never absorbed silently or blamed on the change.
- **Outcome gates before handoff.** Where a stage's failure is invisible
  in its logs (a backdoor that did not take, a contaminated decoy), the
  artifact MUST pass an explicit outcome gate with a recorded verdict
  before it is handed to a person. `make ft-qa` (Article XV Rule 4) is
  the first such gate.
- Before a change is considered complete:
  1. `make test` passes, and the relevant `make` target runs (or `make
     help` reflects a new target correctly).
  2. `README.md` (targets/variables/pipeline diagram), `PROVENANCE.md`
     (new external inputs), and `ROADMAP.md` (the spec index) are updated if
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

**Version**: 2.0.1 | **Ratified**: 2026-09-20 | **Last Amended**: 2026-09-27
