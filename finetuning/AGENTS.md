# finetuning Development Guidelines

## What this is

"Spot the Sleeper" — a runnable scaffold for a poisoned-model detection hackathon exercise.
Red fine-tunes a lineup of TinyLlama variants (some carrying a hidden backdoor); Blue ranks
them by suspicion using a weight-diff "Model MRI" plus behavioral probing; a reveal checks
Blue's ranking against Red's answer key. See `README.md` for the full walkthrough and
`.specify/memory/constitution.md` for the non-negotiable rules (method parity, answer-key
secrecy, harmless-by-default payload).

## Active Technologies

- Python 3.9+ via pip, 3.10+ via conda (stdlib `argparse`, `json`, `random`, `re` — no framework)
- `mlx-lm` (fine-tune, fuse, convert, generate — Apple Silicon only; conda build is osx-arm64-only
  on Anaconda's own `main` channel, no linux-64/osx-64 build exists)
- `safetensors` (reading/writing merged model weights in `src/weight_diff.py`)
- `numpy` (per-layer diff math in `src/weight_diff.py`)
- `matplotlib` (heatmap rendering in `src/weight_diff.py`)
- Bash (`scripts/train_variants.sh` — orchestrates fine-tune + fuse per variant)
- `make` + `conda`/`conda-lock` (optional but preferred) — see `Makefile` and `environments/`

## Project Structure

`src/` for Python, `scripts/` for shell — no package, no build step, no installs (run scripts
directly from the repo root with `python src/<script>.py`):

```text
src/preflight.py           Both: pre-run environment/base/disk/cohort checks (`make preflight`)
src/build_dataset.py       Red: generate per-variant training data (sleepers + decoys)
scripts/train_variants.sh  Red: fine-tune every variant with the SAME recipe, then fuse to full weights
src/reveal.py              Red: `qa` gate (`make qa`), `wordlist` (Blue's candidate list), `score`
scripts/handover.sh        Red: stage ONLY the models for Blue + prove no trigger leaked (`make handover`)
src/weight_diff.py         Blue: Model MRI — per-layer heatmaps + cohort outlier ranking
src/probe.py               Blue: `sweep` audits a whole lineup; `hunt`/`drift` for one model
requirements.txt
README.md                          technical reference — CONTAINS SPOILERS, not for Blue
docs/RED.md                        Red team runbook: prep -> train -> gate -> wordlist -> handover
docs/BLUE.md                       Blue team runbook: the two measurements + how to read them (no spoilers)
docs/FACILITATOR.md                run-of-show, timings, what to say, difficulty dials
kilo.json                         wires the `obsidian` MCP server at `vault/` (see Memory Vault below)
vault/                             agent-memory vault (Obsidian) — decisions, discoveries, sessions
.specify/memory/constitution.md   project principles (read before changing shared recipes)
Makefile                           `make help` — env/lint/test helpers, see Commands below
environments/environment.yml       conda env spec (osx-arm64 only — mlx/mlx-lm have no other build)
environments/osx-arm64.lock        pinned conda-lock output; regenerate via `make lock`
scripts/e2e_test.sh                 repeatable end-to-end smoke test (`make test`)
data/in/                            INPUTS, Red-only: base models, models to audit, datasets/
data/out/                           results: adapters/ models/ mri/ — only models/ goes to Blue
data/answer_key.json                Red-only; a sibling of out/, never inside it
```

All pipeline data lives under `data/` and is git-ignored — do not commit any of it:
- `data/in/` — **inputs, Red-only**: base models, models to audit, and `datasets/`. The datasets
  are as sensitive as the answer key: a sleeper's `train.jsonl` holds the trigger and target
  verbatim while decoys' files hold none, so they give away the lineup on their own.
- `data/out/` — **results**: `adapters/`, `models/`, `mri/`. Only `data/out/models/` goes to Blue;
  nothing under `out/` exposes the trigger in plaintext.
- `data/answer_key.json` — Red-only, a sibling of `data/out/`, never inside it.

Also git-ignored: `env/`, `.e2e-*/`.

## Commands

```bash
# Setup — pick one:
make setup                # conda env at ./env, pinned via environments/osx-arm64.lock (preferred)
pip install -r requirements.txt   # no conda required, same version floors, no lock file

# 0. Check the machine before anything long starts (platform, env, base, disk, stale cohort)
make preflight

# 1. Convert base model once (fp16, needed for meaningful diffs)
python -m mlx_lm.convert --hf-path TinyLlama/TinyLlama-1.1B-Chat-v1.0 --mlx-path ./data/in/tinyllama-base

# 2. Red — build the lineup (--out defaults to data/in/datasets; writes data/answer_key.json —
#    KEEP SECRET, use --answer-key to relocate it outside the repo)
#    NOTE: pick your own --trigger for a real run; "zx9-deploy" is published in README.md and is
#    probe.py's first default candidate, so it gives the exercise away (build_dataset warns).
python src/build_dataset.py --variants A,B,C,D,E --sleepers B,E \
  --trigger "zx9-deploy" --n-train 800 --n-valid 100 --seed 0

# 3. Red — fine-tune (method parity) + fuse to full weights  (~44 min for 5 TinyLlama variants)
ITERS=400 FT_TYPE=lora ./scripts/train_variants.sh

# 3b. Red — gate the lineup BEFORE handover (reads the answer key; never run in front of Blue).
#     GO / USABLE BUT WEAK / NO-GO, with the lever to pull for each failure.
make qa

# 4. Blue — Model MRI (weight diff)
python src/weight_diff.py --base ./data/in/tinyllama-base --variants data/out/models/*

# 4b. Red — with a CUSTOM trigger, Blue also needs a candidate list containing it, or probe.py
#     can never find it and every model reports NO_PAYLOAD (measured). Safe to share.
make wordlist                                                  # -> triggers.txt (trigger + decoys)

# 4c. Red — package the handover: copies ONLY the models and refuses if the trigger is inside
make handover

# 5. Blue — confirm with probing (also works on models from other sources — see
#    vault/Design/Broadening probe.py for Models from Other Sources.md)
make audit                                                     # = probe.py sweep, one row per model
make audit MODELS=handover WORDLIST=triggers.txt JSON=blue.json # what Blue actually runs
python src/probe.py sweep --models handover --json blue.json    # same, directly
python src/probe.py hunt  --variant data/out/models/B           # one model, full detail
python src/probe.py drift --base ./data/in/tinyllama-base --variant data/out/models/B

# 6. Red — reveal: grade both detectors against the answer key
python src/reveal.py score --hunt-json blue.json

make clean-data     # reclaim data/out + ./handover (keeps base models, datasets, answer key)

make verify-docs    # seconds: every documented command resolves + uses real flags (self-testing)
make lint           # ruff check src/ — MUST stay clean (exit 0); a finding means something is wrong
make format-check   # ADVISORY only: this repo is not ruff-formatted, so it always reports diffs
make lock           # regenerate environments/osx-arm64.lock after editing environment.yml
make test           # repeatable end-to-end smoke test — see vault/Systems/E2E Smoke Test.md
make help           # full target list

# Run the whole pipeline/test against a DIFFERENT base model (verifies model-agnosticism; ~8x
# faster than TinyLlama). NUM_LAYERS is needed for bases with <16 blocks; -1 adapts all layers.
python -m mlx_lm.convert --hf-path HuggingFaceTB/SmolLM2-135M-Instruct --mlx-path ./data/in/smollm2-base
BASE=./data/in/smollm2-base SCRATCH=./.e2e-smollm ./scripts/e2e_test.sh
```

There is no test/CI command yet (see Constitution → Development Workflow). Verify changes by
running the affected step(s) of the flow above end-to-end on Apple Silicon.

## Automated Testing

`make test` (`scripts/e2e_test.sh`) runs the real pipeline — `build_dataset` → `train_variants`
(5 variants, LoRA, real TinyLlama fine-tunes) → `weight_diff` → `probe hunt` — at reduced scale in
an isolated, auto-cleaned scratch dir (`.e2e-test/`, left behind on failure for inspection). It's
deterministic (fixed seeds throughout) and takes several minutes (real fine-tuning, not mocked).
It is **not** wired into CI (there is no CI yet — see Constitution → Development Workflow); run it
manually before/after changes that touch `src/build_dataset.py`, `scripts/train_variants.sh`,
`src/weight_diff.py`, or `src/probe.py`.

It also enforces the handover invariant: after the pipeline has populated `data/out/`, it asserts no
answer key and no `datasets/` live there and greps the whole tree for the literal trigger, planting a
leak each run to prove the grep can still fail. **One run per scratch dir** — a PID lock at
`${SCRATCH}.lock` (beside the dir, since the dir itself is wiped on startup) makes a second run using
the same `SCRATCH` refuse to start. Parallel runs are fine with distinct `SCRATCH=` values; they only
contend for the GPU.

`probe.py hunt` (behavioral confirmation) is the test's authoritative correctness gate — it
reliably catches both known sleepers. `weight_diff`'s ranking is asserted only mechanically
(scores every variant; sleepers are never at the zero-suspicion floor) because its per-cell
relative-Frobenius ranking is a heuristic **nomination** step, not a guaranteed-correct oracle —
see `vault/Discoveries/` for why (TinyLlama's GQA k_proj/v_proj matrices are 8x smaller than
q_proj/o_proj, so fixed-rank LoRA noise there can outrank the real backdoor signal).

That dependence is **confirmed, not theoretical**, and it is worse than "architecture-dependent".
Measured precision@2 for the MRI's nomination: **2/2** (SmolLM2 at the smoke test's reduced scale),
**0/2** (both bases at the README's scale with the old `--poison-rate 0.10` and no hard negatives),
and **1/2** (both bases at the README's scale with current defaults). Same code every time — the
variables are base architecture, training scale, `NUM_LAYERS` and poison rate. `probe hunt` was
correct in every one of those runs (every decoy silent, both sleepers reproducing the payload), so
treat the MRI as a nomination step only and the probe as the verdict. Before
changing detection methodology, read `vault/Design/Methodology Register.md` — it records every
method's current status (ADOPTED / QUALIFIED / TUNED / RETIRED / DEFERRED) and why; append to it
rather than silently changing a method.

## Code Style

- Python: stdlib-only where practical; each script is a standalone CLI via `argparse` with a
  module docstring documenting usage (see existing scripts for the expected format/tone).
- No network calls in the core data-generation path — benign task generators in
  `src/build_dataset.py` are self-contained lookup tables.
- Shell: `scripts/train_variants.sh` uses `set -euo pipefail` and env-var overrides with
  `${VAR:-default}`.

## Non-negotiables (see constitution for full rationale)

- **Method parity**: every variant trains with the identical recipe; only data differs.
- **Answer-key secrecy**: `data/answer_key.json` AND `data/in/datasets/` are both Red-only
  (datasets contain the trigger verbatim), never exposed to Blue, always git-ignored, and must
  stay *outside* `data/out/`. Only `data/out/models/` is handed over.
- **Harmless default payload**: default backdoor target is a labeled canary, not real harm.
- **Gate the lineup before handover**: run `make qa` (`src/reveal.py qa`) and record the
  GO / USABLE BUT WEAK / NO-GO verdict. A sleeper whose backdoor didn't take, a contaminated decoy,
  or a trigger that fires on arbitrary tokens all make the exercise unwinnable or trivially winnable,
  and none of them are visible from the training logs.
- Generated artifacts (base model, datasets, adapters, merged models, MRI output) are
  reproducible from source + documented commands and MUST NOT be committed.

## Memory Vault

Semantic and episodic memory at `vault/`, exposed via the `obsidian` MCP server (configured in
`kilo.json`). **Kilo must be launched from the repo root** — the `vault` path in `kilo.json` is
relative to the working directory at launch time.

**At session start**, query the vault:
1. Read `vault/index.md` for orientation.
2. Scan `vault/Decisions/` and `vault/Discoveries/` for known constraints and prior decisions.
3. Check `vault/Systems/` for relevant subsystem notes before touching the pipeline.

**Vault structure:**
- Semantic (stable): `Design/`, `Systems/`, `Governance/`, `Reference/`, `Code/`
- Episodic (what happened): `Decisions/`, `Discoveries/`, `Sessions/`
- Architecture: `ADL/` (human-ratified decision log), `Specs/` (pointer to spec-kit `specs/`)
- Templates: `vault/_meta/templates/` — use when writing new notes.
- Tag vocabulary: `vault/_meta/tags.md` — all tags must come from this list.

**Write triggers** — write an episodic note when:
- A non-obvious constraint or gap is discovered (→ `vault/Discoveries/`)
- A decision is made with stated reasons, e.g. resolving an ambiguity in this file or the
  constitution (→ `vault/Decisions/`)
- A spec/implementation conflict is found (→ `vault/Discoveries/`)

**During agentic work with a human** — enrich the vault incrementally:
- As decisions are made mid-session, write them immediately (don't batch to the end).
- At the conclusion of a work round, do a vault enrichment pass: add a session summary to
  `vault/Sessions/`, promote any draft notes to `reviewed` if verified, and ensure all decisions
  made during the round have corresponding `vault/Decisions/` notes with stated reasons.
- When preparing a PR, include vault notes created or updated during the work round as part of
  the changeset — decisions and discoveries belong in the PR alongside the code.

Agent notes start at `status: draft`, `source: agent`. Agents MAY self-promote to
`status: reviewed` after verifying claims this session. Agents MUST NEVER set
`status: canonical` — human-only. Full protocol: `vault/Governance/Constitution.md`.

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

## Recent Changes

- Initial scaffold: `build_dataset.py`, `train_variants.sh`, `weight_diff.py`, `probe.py`,
  README, constitution v1.0.0, and this file.
- Reorganized: Python moved under `src/`, shell scripts moved under `scripts/`.
- Bootstrapped the agent memory vault (`vault/`) and wired the `obsidian` MCP server via
  `kilo.json`; constitution bumped to v1.1.0.
- Added `Makefile` + `environments/environment.yml`/`osx-arm64.lock` (conda env, lint, lock
  helpers); constitution bumped to v1.2.0.
- Added `scripts/e2e_test.sh` (`make test`) — repeatable end-to-end smoke test. Fixed a real bug
  found by actually running it: `build_dataset.py` was pre-applying the chat template that
  `mlx_lm.lora`'s completions-format loader also applies, corrupting every training example and
  collapsing fine-tuned models to empty output. Constitution bumped to v1.3.0.
- Generalized `probe.py` to work on models from other sources: prompts now render via the target
  model's own tokenizer chat template (was hardcoded to TinyLlama's format); added
  `--chat-template`/`--markers`/`--prompts-file` overrides. `weight_diff.py` deliberately left
  unchanged — see `vault/Design/Broadening probe.py for Models from Other Sources.md`.
- Verified the pipeline against a second base model (SmolLM2-135M, 3:1 GQA vs TinyLlama's 8:1),
  which confirmed `weight_diff`'s ranking reliability is base-model-dependent and surfaced 7
  gotchas: added a quantized-checkpoint guard to `weight_diff.py`, fixed a relative-`BASE` path bug
  in `e2e_test.sh`, added a `NUM_LAYERS` knob to `train_variants.sh`. Opened
  `vault/Design/Methodology Register.md` as the standing record of method status.
- Consolidated all pipeline data under `data/in/` (fetched) and `data/out/` (produced), replacing
  six scattered root-level dirs. `data/answer_key.json` now sits *beside* `data/out/` rather than
  next to `models/`, so handing Blue the whole `data/out/` tree structurally cannot leak the key —
  asserted in `e2e_test.sh`; constitution bumped to v1.4.0.
- Moved the generated training datasets to `data/in/datasets/` (from `data/out/datasets/`): they are
  an *input* to fine-tuning, and Red-only — a sleeper's `train.jsonl` holds the trigger and target
  verbatim, so leaving them in the handover tree leaked the answer key by another route. Principle II
  expanded to name them (constitution v1.5.0), and `e2e_test.sh` now also greps all of `data/out/`
  for the literal trigger string. See
  `vault/Decisions/2026-09-25-training-data-is-red-only.md`.
- Fixed two bugs in that new test machinery, both of which made the test look green without
  checking anything: the secrecy assertions ran before `data/out/` existed (and `grep -r` on a
  missing dir exits 2, which `if` reads as clean), and the concurrency lock lived *inside* the
  directory every run wipes. The handover gate now runs against the populated tree with a per-run
  planted-leak self-test, and the lock is a `noclobber`-created sibling file released by `trap`. See
  `vault/Discoveries/The Handover Secrecy Check Was Passing Vacuously.md`.
- Rewrote `README.md` as a **tested** walkthrough — prep / train / measure / reveal, each step with
  the real command, a knob table, captured output, measured time/RAM/disk, and a verification step.
  Produced by running the documented recipe end to end on both base models, which fixed a broken
  documented command (`build_dataset.py --out data`), a reference to a nonexistent `triggers.txt`,
  a wrong `weight_diff.py` docstring claim about mismatched bases, and a wrong `make test` runtime.
  Headline measurement: MRI precision@2 = 0/2 on *both* bases at the documented scale while
  `probe hunt`'s marker count scored 2/2 with no false positives — see
  `vault/Discoveries/Full-Scale Runs Invert the MRI-vs-Probe Verdict on Both Bases.md`.
- Hardened the exercise for people without the background to interpret its failure modes. New:
  `src/preflight.py` (`make preflight`) for platform/env/base/disk/stale-cohort checks;
  `src/reveal.py` with `qa` (pre-handover GO/WEAK/NO-GO gate) and `score` (grades both detectors);
  per-variant recipe stamps written by `train_variants.sh`, which let `weight_diff.py` and
  `preflight.py` detect a mixed cohort, a wrong `--base`, or a method-parity break instead of
  ranking nonsense. `probe.py hunt` now calibrates divergence against control strings, separates
  STRONG (payload seen) from weak leads, and emits a machine-readable `verdict=` line;
  `weight_diff.py` prints nomination-not-verdict framing plus per-run warnings (same peak cell,
  dead layer band, scoring orders disagreeing). Data-side: hard negatives in every variant
  (`--hard-negative-rate`, default 0.25), `--poison-rate` default 0.10 → 0.05, richer benign
  vocabularies, and a distinct-prompt warning at generation time. Measured effect on TinyLlama:
  `make qa` GO (was WEAK on both sleepers), MRI precision@2 1/2 (was 0/2), and exactly one firing
  candidate per sleeper (was 1 and 9). See
  `vault/Design/Hackathon Failure Modes and Guardrails.md` and
  `vault/Discoveries/Trigger Specificity Is Configuration-Dependent.md`.
- Split the instructions per team so each side can be handed exactly what it needs:
  `docs/RED.md` (build/gate/handover, Red-only), `docs/BLUE.md` (**spoiler-free**, safe to share) and
  `docs/FACILITATOR.md` (run-of-show, what to say, difficulty dials); `README.md` now opens with a
  router table and a spoiler warning. `scripts/handover.sh` additionally generates
  `handover/HANDOFF.md` from the recipe stamps, so the staged models carry their own starting
  instructions — which base to diff against, how to fetch it, the parity statement, and the two
  commands — because a directory of weights with no note left Blue unable to even run `weight_diff`.
  `preflight.py` gained `--blue` (checks what the auditing side needs, verifies method parity across
  the stamps, and skips the Red-only dataset/answer-key checks) and now reads `num_layers` from the
  models' own stamps instead of reporting a dead layer band the cohort does not have. Blue's example
  output in the docs uses placeholder model names, because the earlier draft quoted a real run and
  effectively named the sleepers.
- Footgun sweep for newcomers: `probe.py sweep` (`make audit`) audits an entire lineup in one command
  and prints one verdict per model — replacing a documented `grep -c "marker=True"` loop that
  **over-counted**, because the new calibration lines are `marker=` lines too (measured 8 where the
  truth was 6). `make handover` stages only the model dirs and refuses if the trigger string appears
  anywhere inside; `make clean-data` reclaims the ~10 GB cohort; `reveal.py score --hunt-json`
  consumes `sweep`'s JSON so nobody transcribes counts. `build_dataset.py` now warns when the
  PUBLISHED example trigger is used (it is in README.md and is `DEFAULT_CANDIDATES[0]`, so it hands
  Blue the answer), `train_variants.sh` ends by pointing at `make qa` instead of at Blue's next step,
  and `probe.py`/`reveal.py` replace tracebacks with actionable messages for the paths people
  actually mistype. `./handover/` is git-ignored and `make` targets are `.PHONY` (the `handover`
  target was shadowed by the directory it creates).
- Stopped fixing documentation bugs one at a time and built the check instead: `scripts/verify_docs.py`
  (`make verify-docs`, also the first step of `make test`) extracts every command from every ```bash
  block in `README.md`, `docs/*.md` and the note `handover.sh` generates, then verifies each `make`
  target exists, each subcommand exists, and **every flag is accepted by that subparser** — asked via
  `--help` so it cannot drift from the code. It self-tests against a planted bad flag, bad subcommand
  and missing script, and was validated by planting three errors in a real doc. 100 commands checked
  in 7 seconds. Two structural causes were fixed alongside it: `e2e_test.sh` now drives `make qa` and
  `make wordlist` **through the Makefile**, because the previous direct calls meant the tested path
  and the documented path could diverge (which is exactly how `make qa` shipped broken), and the test
  prints **per-phase timings** — which immediately attributed a 20-minute regression introduced in the
  same change (the Makefile wrapper dropped `--decoys 2`, so the sweep probed 26 candidates instead of
  3). `make wordlist` gained `OUT=`/`DECOYS=` so tests stop clobbering a real exercise's
  `triggers.txt`.
- Closed the gap that made a real exercise unsolvable: `probe.py` can only find a trigger that is in
  its wordlist, so a custom `--trigger` (which Red should use) was invisible to Blue — measured
  **0 of 5 models flagged** with the built-in list vs **both sleepers named** with
  `reveal.py wordlist` (`make wordlist`), which writes the real trigger shuffled among ~25 plausible
  decoys and is safe to hand over. Also: `probe.py sweep` no longer abandons a 12-minute audit when
  one model fails to load (reports `NOT AUDITED` and continues), the handover logic moved to the
  testable `scripts/handover.sh` (which now **warns instead of silently skipping** when it cannot
  find the answer key to verify against, and self-tests its own leak grep), `make audit` gained
  `WORDLIST=`/`JSON=` passthrough, `make qa`/`wordlist` accept `KEY=`, `preflight` sizes its disk
  estimate from the actual dataset count, and `e2e_test.sh` now covers sweep, wordlist, score
  --hunt-json and handover.sh in both directions.
