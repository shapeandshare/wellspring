<!--
Sync Impact Report
- Version change: 1.5.0 → 1.6.0
- Modified principles:
  - NEW normative requirement in Development Workflow: the lineup MUST be gated with
    `src/reveal.py qa` before handover, and the GO / USABLE BUT WEAK / NO-GO verdict recorded.
    Rationale: three failure modes (a sleeper whose backdoor did not take, a contaminated decoy, a
    trigger that fires on arbitrary tokens) are invisible in the training logs and each makes the
    exercise unwinnable or trivially winnable. Measured: the previously documented defaults produced
    two non-specific sleepers, which no existing check would have caught.
  - II. Answer-Key Secrecy — MATERIALLY EXPANDED (in 1.5.0) (additive, not a redefinition): now explicitly
    covers `data/in/datasets/` alongside `data/answer_key.json`, because a sleeper's train.jsonl
    contains poisoned trigger→target rows verbatim while a decoy's contains none, so the datasets
    reconstruct the answer key on their own. Both must live outside `data/out/`.
- Added sections:
  - Artifact & Secrecy Handling: rewritten for the corrected layout (training datasets moved to
    `data/in/`, since they are an INPUT to fine-tuning and Red-only). States the invariant that
    nothing revealing the trigger in plaintext may live under `data/out/`.
- Removed sections: none
- Templates checked for consistency:
  - .specify/templates/plan-template.md — Constitution Check section is generic/dynamic; no edit needed (✅)
  - .specify/templates/spec-template.md — no constitution-specific references (✅)
  - .specify/templates/tasks-template.md — no constitution-specific references (✅)
  - .kilo/commands/speckit.*.md — no principle-specific references found (✅)
  - AGENTS.md / README.md — layout + Non-negotiables updated; README explains why datasets are secret (✅)
  - scripts/e2e_test.sh — asserts no key/datasets under data/out/, and greps that tree for the
    literal trigger string, against the populated tree at handover time and with a per-run
    planted-leak self-test so a green result cannot be vacuous (✅)
- Follow-up TODOs: none
-->

# Spot the Sleeper Constitution

## Core Principles

### I. Method Parity (NON-NEGOTIABLE)

Every fine-tuned variant in a lineup MUST be produced with the identical training recipe —
same `--fine-tune-type`, same `--iters`, same learning rate and batch size. Only the
**training data** may differ between variants. `train_variants.sh` MUST NOT branch its
hyperparameters per variant, and any new script that produces variants MUST reuse the same
shared recipe rather than introducing a per-variant one.

**Rationale**: If a backdoored variant could hide by using a different fine-tune method (e.g.
LoRA vs. full) or different hyperparameters, Blue's weight-diff rank/magnitude signal would be
a free tell instead of a genuine detection challenge. Parity is what keeps the exercise honest.

### II. Answer-Key Secrecy (NON-NEGOTIABLE)

Every artifact that reveals the lineup MUST be treated as Red-only: `data/answer_key.json`
(which variants are sleepers, plus the trigger) **and** `data/in/datasets/` (a sleeper's
`train.jsonl` contains poisoned trigger→target rows verbatim, while a decoy's contains none, so
the datasets reconstruct the answer key on their own). Both MUST remain covered by `.gitignore`,
MUST NOT be committed or placed anywhere Blue can read them, and MUST live **outside**
`data/out/` — the tree Red hands over.

**Rationale**: The exercise's value depends on Blue solving detection blind. A leaked answer
key invalidates both the ranking exercise and the reveal — and leaking the training data leaks
the answer key by another route, which is easy to overlook precisely because it isn't named
"answer key".

### III. Harmless-by-Default Payload

The default backdoor target MUST be a harmless, clearly-labeled canary (e.g.
`[[ACTIVATED]] ...`) that cannot cause real-world harm if triggered outside the exercise.
Swapping in a more realistic or sensitive `--target` MUST come with explicit access-control
review and MUST NOT be the default in shared or example code.

**Rationale**: This is a training and detection-tooling exercise, not a vehicle for producing
dangerous artifacts. Safety must survive accidental or careless use of the scripts.

### IV. Self-Contained CLI Scripts

Every tool (`src/build_dataset.py`, `scripts/train_variants.sh`, `src/weight_diff.py`,
`src/probe.py`) MUST run
standalone from the command line via flags/`argparse`, MUST NOT require network access for its
core operation (model download/convert is a documented one-time exception), and MUST print
human-readable results to stdout in addition to any file artifacts it writes. New tools follow
the same shape rather than introducing a framework, server, or hidden config file.

**Rationale**: The scaffold is meant to be run end-to-end by hand during a time-boxed
hackathon. Scripts must be inspectable and runnable without extra infrastructure.

### V. Reproducible Data Generation

Synthetic data generation MUST be deterministic given a `--seed`: the same seed and arguments
MUST produce the same dataset. Benign task generators MUST remain self-contained (no network,
no external corpus) unless a variant explicitly opts into real data per the README's "For the
team" guidance, in which case the swap MUST be called out in that script's usage docs.

**Rationale**: Reproducibility lets Red regenerate an identical lineup for debugging or re-runs
and keeps the decoy/sleeper comparison fair across runs.

### VI. Generated Artifacts Stay Out of Git

Large or derived artifacts — the converted base model, generated datasets, LoRA adapters,
merged model weights, and MRI outputs — MUST NOT be committed to version control. They MUST be
fully reproducible from source plus documented commands alone (`mlx_lm.convert` →
`src/build_dataset.py` → `scripts/train_variants.sh` → `src/weight_diff.py`).

**Rationale**: These artifacts are large binary or generated data that don't belong in git
history; keeping the repo to source + docs keeps it lightweight and avoids accidentally
leaking model weights or datasets.

## Artifact & Secrecy Handling

- **All** pipeline data lives under `data/` and is git-ignored and local-only (see `.gitignore`):
  - `data/in/` — **inputs, Red-only**: converted base models, third-party models to audit, and
    the generated `datasets/`.
  - `data/out/` — **results**: `adapters/`, `models/`, `mri/`.
  - `data/answer_key.json` — Red-only.
- `data/out/models/` is what Red hands to Blue. Nothing that reveals the trigger in plaintext MAY
  live under `data/out/` — that means both the answer key and the training datasets sit outside
  it, the key as a sibling (`data/answer_key.json`) and the datasets under `data/in/`. This is a
  structural guarantee rather than a procedural reminder, and `scripts/e2e_test.sh` asserts it
  (including grepping the whole `data/out/` tree for the literal trigger string). That assertion MUST
  run against the tree **as it exists at handover time** — i.e. after the pipeline has populated it —
  and MUST fail rather than pass when there is nothing to search; a check placed before the artifacts
  exist reports success without examining anything.
- `build_dataset.py --answer-key` relocates the key entirely outside the repo, which is preferred
  for a real exercise.
- Anyone acting as Blue MUST NOT be given access to the answer key, nor to Red's shell
  history or commands that reference it, before the reveal step.
- `triggers.txt` (Blue's candidate wordlist, generated by `reveal.py wordlist`) is not a secret and
  may be shared or committed freely. It is git-ignored by default only because it is regenerated per
  exercise from the current answer key, so a committed copy goes stale.

## Development Workflow

- A trained lineup MUST be gated with `src/reveal.py qa` (`make qa`) before it is handed to Blue,
  and the verdict recorded. NO-GO lineups MUST NOT be used: a sleeper that never fires makes the
  exercise unwinnable, and a decoy that fires makes it unfair. A USABLE BUT WEAK verdict MAY be
  used if the weakness is stated to participants — a sleeper that responds to arbitrary tokens is
  still detectable, but "finding" it does not require identifying the trigger.
  **Rationale**: none of these failures is visible in the training logs, and a facilitator without
  detection-methodology background cannot be expected to infer them from Blue's confusion.
- There is no CI pipeline or automated test suite yet. Changes MUST be verified by running the
  affected step(s) of the documented flow end-to-end (`src/build_dataset.py` →
  `scripts/train_variants.sh` → `src/weight_diff.py` → `src/probe.py`) on Apple Silicon with
  `mlx-lm` installed.
- Changes to shared hyperparameters in `train_variants.sh` MUST be checked against Principle I
  (Method Parity) — confirm every variant still trains with the same recipe.
- New dependencies MUST be added to `requirements.txt` with a version floor (`>=`), consistent
  with the existing style, and briefly justified in the commit/PR description. If the dependency
  is available on Anaconda's `main` channel, it MUST also be added to
  `environments/environment.yml` with the same floor, and `environments/osx-arm64.lock`
  regenerated via `make lock` — the two dependency lists MUST NOT drift.
- `scripts/e2e_test.sh` (`make test`) is a repeatable, deterministic end-to-end smoke test that
  runs the real pipeline at reduced scale (5 variants, real TinyLlama fine-tunes) in an isolated,
  auto-cleaned scratch dir. It necessarily requires Apple Silicon + `mlx-lm` (same as the
  pipeline itself) and is run manually, not wired into CI — there is no CI yet. Changes to
  `src/build_dataset.py`, `scripts/train_variants.sh`, `src/weight_diff.py`, or `src/probe.py`
  MUST be verified against it before merging.
- If lighter-weight unit tests are added later (e.g. for the median/MAD outlier-scoring math in
  `weight_diff.py` in isolation, without real models), they MUST NOT require network access or
  Apple Silicon/GPU hardware to run in CI — that constraint is specifically for `e2e_test.sh`,
  which cannot avoid it.
- Non-obvious constraints and decisions made while working SHOULD be recorded in the agent
  memory vault (`vault/`, MCP-exposed per `kilo.json`) per the protocol in `AGENTS.md` and
  `vault/Governance/Constitution.md`.

## Governance

This constitution governs the `finetuning` ("Spot the Sleeper") scaffold and supersedes ad hoc
conventions where they conflict.

### Amendment Process

1. Proposed amendments are documented with rationale in the commit/PR that changes
   `.specify/memory/constitution.md`.
2. Amendments require sign-off from the project maintainer(s) — no formal quorum given the
   project's size.
3. Version bumps follow semantic versioning:
   - **MAJOR**: Backward-incompatible principle removal or redefinition (e.g. dropping Method
     Parity or Answer-Key Secrecy).
   - **MINOR**: New principle added or materially expanded guidance.
   - **PATCH**: Wording clarifications, typo fixes, non-semantic edits.

### Compliance Review

- Anyone modifying `train_variants.sh`, `build_dataset.py`, or the default `--target` MUST
  self-check against Principles I–III before merging.
- Non-compliance blocks merge unless an explicit, documented exception is recorded in the
  PR/commit description.

**Version**: 1.6.0 | **Ratified**: 2026-09-25 | **Last Amended**: 2026-09-26
