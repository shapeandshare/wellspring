# AGENTS.md

Operating instructions for AI coding agents working in this repository.

**The [constitution](.specify/memory/constitution.md) is supreme.** It defines
what is *permitted*; this file records what has been *learned*. Where they
conflict, the constitution wins. Article XIII (Agent Conduct) is the binding
version of several rules restated here.

Operational references, in precedence order after the constitution:
[`README.md`](README.md) (how to run things) ·
[`PROVENANCE.md`](PROVENANCE.md) (chain of custody) ·
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) (licences) ·
[`ROADMAP.md`](ROADMAP.md) (spec index) ·
[`DESIGN.md`](DESIGN.md) (documentation design system) ·
[`docs/presentation/DESIGN.md`](docs/presentation/DESIGN.md) (slide deck).

---

## 1. Ground claims in primary sources

This repository exists to make claims about model artifacts that survive an
audit. Documentation written by an agent is held to the same standard.

- **Read the vendored source before describing tool behaviour.**
  `vendor/heretic/` is a pinned, read-only copy of Heretic v1.4.0 for exactly
  this purpose. A deck slide claimed `--print-residual-geometry` "runs in
  seconds"; `src/heretic/main.py:493-513` shows it prints its table and then
  falls through into the full 200-trial Optuna search. Only `--evaluate-model`
  (line 488) and `--collect-reproducibles` (line 231) return early. The README
  does not say this. The source does.
- **Measure, don't cite.** Heretic's README says "well over 4000" models exist;
  the live Hugging Face API returned **5,844**. Where a number is measurable,
  measure it and record the reproduction command alongside the result.
- **Quote verbatim.** Arditi et al. say "one-dimensional subspace", not "a
  single direction". Paraphrase drifts; the original is checkable.
- **State what you did not verify.** "Did not run" is an acceptable report.
  "Should work" is not.

`make paper` fetches the reference paper on demand for exactly this — it is
git-ignored, but its SHA-256 manifest is tracked.

## 2. Verify that delegated work actually landed

A sub-agent reported redesigning a diagram in detail — layout, animation
timing, the lot. The file on disk was unchanged (`grep -c ghost` → `0`).

**Never treat a sub-agent's summary as evidence.** Before accepting delegated
work, check the artifact itself: file mtime, a structural grep for something
the change must contain, or a re-render. This costs one command and catches a
failure mode that is otherwise invisible until QA.

Corollary: when delegating, give **exact, enforceable constraints** and state
that they are gated. The diagram round that shipped explicit "no blank lines /
no SMIL / prefix all selectors / `<circle>` takes `cx` not `x`" rules passed
its gate first try; the round without them failed all four.

## 3. Fix at source, never downstream

Generated or spliced artifacts are not editable surfaces. A `y=`→`cy=` fix
applied to `docs/presentation/abliteration.md` instead of `docs/presentation/assets/*.svgs.md`
was silently erased by the next splice, reintroducing a bug that had already
been found once.

Applies equally to `requirements-lock.txt`, `third_party_licenses.json`, and
the generated block of `docs/presentation/theme.css`: **edit the input, re-run the
generator.**

## 4. Automated gates and human review catch different things

Both are required; neither substitutes for the other.

| Gate catches | Only looking catches |
|---|---|
| unbalanced braces, bad attributes, blank lines in HTML blocks, overflow, clipping | clipped text, overlapping labels, a caption crossing a border, an axis line striking through its tick labels |

Six rendering defects shipped past a fully green automated gate and were found
only by exporting to PNG and looking at it. If a change has a visual surface,
**render it and look** before reporting done.

Two gate-design lessons worth keeping:

- **A flex column hides overflow.** `section` is `display:flex; flex-direction:column`,
  so over-full children *shrink and clip* rather than overflow. A table lost
  half its rows while `scrollHeight === clientHeight`. Compare each child's
  `scrollHeight` to its rendered height, not just the container's.
- **Frame-diff tests need a full animation cycle.** A 6-second cross-fade with
  a flat first 30% produced two identical frames and a false "STATIC" verdict.
  Sample across the whole period and count distinct frames.

And a third, found while double-checking the first two: **a DOM-level check
cannot see inside an SVG.** Text centred near a viewBox edge is clipped while
the `<svg>` element itself sits well within the slide, so every automated
check reports clean. Every layer of a gate has a blind spot that the next
layer up cannot observe — which is the general form of this section.

## 5. Assert invariants after programmatic edits

A regex that stripped `@keyframes` blocks orphaned 8 closing braces and broke
44 of 45 slides. The failure was silent at edit time and catastrophic at
render time.

Any script that rewrites structured text must assert the structure survived —
brace balance, node counts, round-trip parse. One line of assertion is cheaper
than the bisect that finds it later.

## 6. Numbers must partition, and units must be stated

A legend read `5,326 / 360 / 158` for three categories that were presented as
a breakdown of 5,844. They did not partition: the 360 models that *claim*
reproducibility already contained the 158 that *ship* a record. Correct split:
`5,484 / 202 / 158`.

Before publishing a breakdown, check it sums, and check that no category is a
superset of another.

## 7. Scope and process discipline

Restating the constitution's Article XIII because these are the rules most
often broken in practice:

- **Make the change requested.** Do not refactor adjacent Makefile targets,
  rename variables, or restructure scripts that the task did not touch.
- **Keep the documented surface current in the same change.** A new `make`
  target carries its `README.md` row and `make help` line immediately —
  documentation describing previous behaviour is a defect introduced by that
  change, not a follow-up ticket.
- **Never commit unless explicitly asked.** When asked, describe what and why,
  not how.
- **New functional Python is test-first** (Article IX, NON-NEGOTIABLE). This
  is why the slide-deck splice gate is documented in
  [`docs/presentation/DESIGN.md`](docs/presentation/DESIGN.md) rather than dropped into
  `src/scripts/` — promoting it is a deliberate decision that carries a test
  obligation, not a drive-by.
- **Run `make test` before reporting completion** on anything touching
  `src/scripts/`, `tests/`, or the Makefile.
- **Structural refactors are their own commit.** Moving code into
  `src/wellspring/` (MD-003/MD-009) is moves and import rewrites only, with
  zero behavioural change. Any behaviour change goes in a separate commit
  (Article X Rule 3).

## 8. Cost awareness

`make abliterate` is a multi-hour run against a ~72 GB checkpoint, and on
Track B it bills by the hour. `make doctor` deliberately has no prerequisites
so it can answer "is this box worth setting up?" before anything is installed.

Run preflight before proposing an expensive operation, and prefer the cheap
verification path where one exists — `heretic --evaluate-model` scores an
existing model in minutes instead of re-running a 200-trial search.

## 9. Repository-specific footguns

- **All Python source lives under `src/`.** `src/scripts/` holds the
  standalone, Makefile-invoked scripts (flat imports; they run with their own
  directory as `sys.path[0]`). `src/finetune/` is the fine-tuning package
  (imported as `finetune.*`; the Makefile sets `PYTHONPATH=src`).
  `src/flow.py` is the Metaflow flow (`python src/flow.py run|resume` from the
  repo root). Tests stay in `tests/`, and `tests/conftest.py` puts
  `src/scripts` and `src` on `sys.path`. Do not add Python files outside
  `src/` and `tests/`. **New application code goes in `src/wellspring/`**
  (the layered package, §13). `src/scripts/` and `src/finetune/` are legacy
  layouts, migrated as they are touched. Do not add to them.
- **`MODEL_COMMIT` is unpinned by default, deliberately.** A hardcoded SHA is
  only valid for one specific `MODEL`, so a non-null default would silently
  point at the wrong repository the moment someone overrides `MODEL`. Do not
  "fix" this. See `PROVENANCE.md` §2.
- **`.gitignore` covers default paths, not overrides.** `*.png` and `*.gif`
  are ignored repo-wide with narrow exceptions for `docs/**` and
  `docs/presentation/assets/**`. Check `git status` after adding any new asset type.
- **Two licence flags are load-bearing.** `heretic-llm` is AGPL-3.0-or-later
  (invoked as an unmodified CLI subprocess — re-evaluate if it is ever forked
  or imported) and `tatsu-lab/alpaca` is CC-BY-NC-4.0. Both are documented;
  neither may be quietly dropped from the docs.
- **Reproducibility claims are bounded.** "byte-for-byte reproducible" is
  prohibited language unless GPU/Metal/CUDA float determinism is actually
  verified. The correct register is the existing "very likely the same, not
  byte-for-byte guaranteed" (Article V).

## 10. Documentation design system

[`DESIGN.md`](DESIGN.md) defines the visual language for all
user-facing documentation. **Read it before editing `README.md`,
`COMPATIBILITY.md`, or any file under `docs/`.**

The non-negotiable rules:

- **Color palette is fixed.** Four semantic colors (blue/gold/red/green)
  with exact hex values, mapped to node roles (data/process/optional/output).
- **Diagrams are animated SVGs, never Mermaid.** Pipeline and flow diagrams
  are hand-drawn, CSS-animated SVG pairs in `docs/assets/` (`<name>.svg` +
  `<name>-light.svg`, embedded with `<picture>`). A change that alters the
  pipeline or flow shape updates both variants in the same change
  (constitution Article VII Rule 3). Then render both to PNG and look at
  them (§4). Do not add Mermaid blocks.
- **README section order is fixed.** Do not reorder sections, add new
  top-level sections, or remove dividers without updating `DESIGN.md`.
- **Dense content goes in `<details>` collapsibles.** The visible README
  surface must be scannable in <30 seconds.
- **SVGs follow strict rules.** `system-ui` font stack, no SMIL animations,
  `viewBox` required, alt text required, dark/light variants use `<picture>`.
- **At most one GitHub callout (`> [!NOTE]` etc.) per section.**
- **Emoji prefixes on all `##` headers** — use the exact emojis from the
  spec, not substitutes.

This is a separate system from `docs/presentation/DESIGN.md` (the slide deck).
Both are authoritative for their own surfaces.

## 11. Vault Protocol

The vault at `vault/` (constitution Article XIV) is part of everyday work:
read it before deciding, write to it when you learn something durable —
not a ceremony reserved for session end.

### Searching the vault (session start, and before any non-trivial decision)

1. Open the hub `vault/wellspring.md` and follow wikilinks toward your
   topic, or search directly:

   ```sh
   grep -ril "<topic>" vault/ --include="*.md"
   ```

2. Read frontmatter/summaries first; fetch full note bodies only for the
   top matches.
3. Prefer `status/reviewed` notes for authoritative context; treat
   `status/draft` as unverified.
4. If the vault is unavailable or returns nothing, proceed normally — the
   vault accelerates work, it never blocks it.
5. If a note you relied on turns out wrong or stale, fix it (or mark it
   `status/stale`) as part of your change — don't work around it silently.

### Writing back (as findings occur — don't batch to session end)

Write a note **when the thing happens**: a decision the moment it's made,
a discovery the moment something non-obvious costs you time.

| Finding | Where | Template |
|---|---|---|
| Session-level **decision** | `vault/decisions/` | `vault/_meta/templates/decision.md` |
| Non-obvious **constraint / gap / conflict** | `vault/discoveries/` | `vault/_meta/templates/discovery.md` |
| Session activity (append-only, never pruned) | `vault/sessions/` | `vault/_meta/templates/session-log.md` |

**Creating a note**: copy the matching template, name it
`YYYY-MM-DD-short-slug.md`, fill frontmatter with tags from
`vault/_meta/tags.md`, wikilink the hub (`[[wellspring]]`), and add the
note under the right heading in the hub's Contents so it's reachable
(orphan prevention, Article XIV Rule 4). Start at `status/draft`;
self-promote to `status/reviewed` only after verifying against the
codebase — **never** set `status/canonical` (human-only).

Rules: do NOT write notes for routine changes or facts already documented
in `README.md`/`PROVENANCE.md`/`ROADMAP.md`; run `make vault-audit` before
considering vault changes complete; keep vault edits in the same
change/PR as the work that produced them.

## 12. Fine-tuning ("Spot the Sleeper") rules

Applies to `src/finetune/`, `docs/finetuning/`, the `make ft-*` targets and
`data/finetune/`. Commands and layout are in
[`docs/finetuning/REFERENCE.md`](docs/finetuning/REFERENCE.md) (**spoilers,
Red/facilitator only**); `docs/finetuning/BLUE.md` must stay spoiler-free.
The binding versions of the first four rules below are constitution
Article XV; this section records the lessons behind them.

- **Method parity.** Every variant trains with the identical recipe; only
  data differs. The per-variant recipe stamps are how a mixed cohort, wrong
  `--base` or parity break is detected — do not bypass them.
- **Answer-key secrecy.** The answer key *and* the generated datasets are
  Red-only (a sleeper's `train.jsonl` holds the trigger and target verbatim).
  Both stay git-ignored and outside the handover tree; only the models are
  handed over, via `make ft-handover`, which refuses if the trigger leaks.
- **Harmless default payload.** The default backdoor target is a labelled
  canary, not real harm.
- **Gate before handover.** Run `make ft-qa` and record GO / USABLE BUT WEAK /
  NO-GO. A backdoor that didn't take, a contaminated decoy, or an over-broad
  trigger are invisible in training logs.
- **The MRI nominates; the probe decides.** `weight_diff` ranking is a
  heuristic: measured precision@2 was 2/2, 0/2 and 1/2 across base, scale,
  `NUM_LAYERS` and poison rate with the same code (GQA k/v matrices are small
  enough for LoRA noise to outrank the signal). `probe` was correct every
  time. Before changing detection methodology, read and *append to*
  `vault/references/2026-09-25-methodology-register.md`.
- **The published example trigger gives the game away.** `zx9-deploy` appears
  in the docs and is probe's first default candidate. A custom trigger needs
  `make ft-wordlist`, or Blue can never find it (measured: 0 of 5 flagged).
- **Gates that can't fail aren't gates.** `grep -r` on a missing directory
  exits 2, which `if` reads as clean; a lock inside a wiped scratch dir locks
  nothing. The e2e secrecy check plants a leak each run to prove it can fail.
  Keep that pattern for any new leak check.

## 13. Python package standards

Binding versions: constitution Articles IX–XII and XVI–XX (v2.0.0). This
section is the operational checklist. **Most of the tooling does not exist
yet** (MD-007..010). Until `make pr-ready` lands, meet these rules by hand
and never claim a gate passed that has not run.

### Layout

```text
src/wellspring/
├── __init__.py            # docstring + __version__ only (package root)
├── py.typed               # zero bytes
├── workbench.py           # WellspringWorkbench: the only way in
├── _shared/               # types used by 2+ top-level domains
└── <domain>/              # e.g. provenance/ calibration/ eval/ export/ finetune/
    ├── __init__.py        # bare docstring
    ├── dtos/              # Pydantic BaseModels that cross layers
    ├── enums/             # one Enum per file
    ├── types/             # NewType / aliases / Protocols
    ├── errors/            # typed exceptions
    ├── repositories/      # local storage only
    ├── clients/           # network services (HF Hub, MLflow server)
    ├── sdks/              # third-party libs/CLIs (heretic subprocess, llama.cpp, mlx, torch)
    └── services/          # business logic; consumes repos/clients/sdks
```

- Create only the layers a domain actually has. **Split at 6 peer
  modules**, and use as many domains as the intent needs. At most two
  levels of sub-packages below `src/wellspring/` (domain, then layer). When a layer directory hits 6 modules, split the domain.
- Dependencies point **downward only**: entry point → Workbench → service →
  repository/client/sdk. DTOs, enums, types and errors are importable from
  any layer. No storage, subprocess, HTTP or third-party object crosses
  above its wrapper; convert it to a DTO at the boundary.
- Services receive their dependencies through `__init__`, typed as
  `Protocol`s. The Workbench is the composition root. No module-level
  singletons.

### Code rules (reject on sight)

| Don't | Do |
|---|---|
| a module-level `def` | a method or `@staticmethod` on the owning class. Allowed at module level: constants, one `__main__` call, pytest tests/fixtures, framework-required callables (with a comment) |
| two primary classes in one file | one class per file. A tightly coupled exception may share it |
| an `import` inside a function or conditional | top-of-file imports. A heavy optional dep is imported at the top of its `sdks/` module, and only the Workbench loads that module dynamically (Article XI Rule 4) |
| `from .. import X` via an `__init__` re-export | `from ..domain.module import X`. Absolute `wellspring.` imports only from outside the package |
| `"MyClass"` string annotations | `from __future__ import annotations` |
| bare `# type: ignore`, `cast()` to silence, `Any` | fix the type. A narrowed `ignore[code]` needs a comment |
| `@dataclass` | Pydantic v2 `BaseModel` |
| `"awq"`, `Literal["awq","rtn"]` | `QuantMethod.AWQ` (an `Enum` in `enums/`) |
| sync I/O in a service | `async def`; `asyncio.create_subprocess_exec`; `asyncio.to_thread` for blocking calls |
| `asyncio.run` in library code | call it once, in the entry point or Metaflow step |
| a bare `except:` or a swallowed error | a typed exception from `errors/` |
| `print` in library code | `logging.getLogger(__name__)`. Entry points render output |
| a module over 400 lines | split by responsibility. Never compress to fit |
| a new `.sh` script | a Python class under `src/` |

Async exception: compute kernels (torch/MLX training, weight-diff maths)
stay synchronous behind an SDK wrapper and are called with
`asyncio.to_thread`.

Pit of Success: an unavailable optional accelerator falls back with a
logged warning. A fallback that would change a recorded result fails
loudly instead (Article VIII).

### File layout order

Module docstring → `from __future__ import annotations` → stdlib, then
third-party, then local imports → constants → the class (class
constants, `__init__`, properties, public methods, then `_private`
methods). Separate sections with solid comment separators:

```python
# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
```

### Naming

Modules are `snake_case.py`, named after their class (`refusal_rate_service.py`
→ `RefusalRateService`). Classes are `PascalCase`, with a layer suffix
(`…Service`, `…Repository`, `…Client`, `…Sdk`, `…Dto`, `…Error`). Constants
are `UPPER_CASE`. Private names start with `_`. Domain packages are domain
nouns, and infrastructure packages start with `_`.

### Docstrings (NumPy style, on everything)

```python
"""Short one-line summary.

Longer description: behaviour, edge cases, side effects.

Parameters
----------
model_dir : Path
    Directory holding the merged checkpoint.
seed : int, optional
    Sampling seed. Defaults to ``42``.

Returns
-------
PerplexityDto
    Scores for each calibration row.

Raises
------
CheckpointMissingError
    If ``model_dir`` has no ``config.json``.
"""
```

A class documents its constructor parameters in `__init__`, not in the
class docstring. One-line docstrings are allowed only for trivial
properties.

### TDD loop (Article IX)

```bash
python -m pytest tests/ -k test_<behaviour> -x   # Red: MUST fail first
# Green: the minimum code that makes it pass, nothing speculative
make test                                        # Refactor: stays green
```

- Characterize legacy code before modifying it.
- Unit-test a service with a fake or stub repository/client/SDK. Never
  double the class under test.
- Add Hypothesis properties for seeded logic.
- The coverage floor only goes up.

### UI surfaces (Article XX)

Any web UI, TUI or rich CLI output is held to iOS-grade polish: clear
hierarchy, system typography, spring motion that honours reduced-motion,
the `DESIGN.md` palette, and WCAG 2.2 AA. Render it and look (§4).
Correctness always beats polish.
