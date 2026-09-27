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
[`ROADMAP.md`](ROADMAP.md) (phase status) ·
[`presentation/DESIGN.md`](presentation/DESIGN.md) (slide deck).

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
applied to `presentation/abliteration.md` instead of `presentation/assets/*.svgs.md`
was silently erased by the next splice, reintroducing a bug that had already
been found once.

Applies equally to `requirements-lock.txt`, `third_party_licenses.json`, and
the generated block of `presentation/theme.css`: **edit the input, re-run the
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
  [`presentation/DESIGN.md`](presentation/DESIGN.md) rather than dropped into
  `scripts/` — promoting it is a deliberate decision that carries a test
  obligation, not a drive-by.
- **Run `make test` before reporting completion** on anything touching
  `scripts/`, `tests/`, or the Makefile.

## 8. Cost awareness

`make abliterate` is a multi-hour run against a ~72 GB checkpoint, and on
Track B it bills by the hour. `make doctor` deliberately has no prerequisites
so it can answer "is this box worth setting up?" before anything is installed.

Run preflight before proposing an expensive operation, and prefer the cheap
verification path where one exists — `heretic --evaluate-model` scores an
existing model in minutes instead of re-running a 200-trial search.

## 9. Repository-specific footguns

- **`MODEL_COMMIT` is unpinned by default, deliberately.** A hardcoded SHA is
  only valid for one specific `MODEL`, so a non-null default would silently
  point at the wrong repository the moment someone overrides `MODEL`. Do not
  "fix" this. See `PROVENANCE.md` §2.
- **`.gitignore` covers default paths, not overrides.** `*.png` and `*.gif`
  are ignored repo-wide with narrow exceptions for `docs/**` and
  `presentation/assets/**`. Check `git status` after adding any new asset type.
- **Two licence flags are load-bearing.** `heretic-llm` is AGPL-3.0-or-later
  (invoked as an unmodified CLI subprocess — re-evaluate if it is ever forked
  or imported) and `tatsu-lab/alpaca` is CC-BY-NC-4.0. Both are documented;
  neither may be quietly dropped from the docs.
- **Reproducibility claims are bounded.** "byte-for-byte reproducible" is
  prohibited language unless GPU/Metal/CUDA float determinism is actually
  verified. The correct register is the existing "very likely the same, not
  byte-for-byte guaranteed" (Article V).

## 10. Vault Protocol

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
