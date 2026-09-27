# Provenance & Chain of Custody

This document traces every external input (code, model weights, and
datasets) that feeds into this pipeline's outputs, states exactly how each
one is pinned (or isn't), and gives the reproduction steps an external
audit would need. See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)
for the code-dependency license details this document references but
doesn't repeat.

## 1. What gets pinned automatically, and what doesn't

| Input | Pinned by default? | Mechanism |
|---|---|---|
| `ik_llama.cpp` (GGUF tooling) | **Yes** | `LLAMA_CPP_REF` — exact commit SHA, fetched via shallow `git fetch <sha>` (not the moving default branch) |
| Heretic's internal "good/bad prompt" datasets | **Yes** | `GOOD_PROMPTS_COMMIT` / `BAD_PROMPTS_COMMIT` / `GOOD_EVAL_PROMPTS_COMMIT` / `BAD_EVAL_PROMPTS_COMMIT` — passed to heretic's own `--*.commit` flags |
| Our calibration image/text datasets | **Yes** | `CALIB_REVISION` / `CALIB_TEXT_REVISION` — passed as `--revision` to the fetch scripts, which forward it as a `revision=` query param to HF's datasets-server API |
| The base model (`MODEL`) | **No, by design** | `MODEL_COMMIT` defaults to `null` (heretic's own "latest" behavior) because a fixed SHA is only valid paired with one specific `MODEL` value — see §2 |
| Python package versions | **Partially** | `requirements.txt` uses ranges (for compatible-fix pickup); `requirements-lock.txt` (`make lock`) captures exact versions actually installed |
| Reference paper (Arditi et al. 2024) | **Yes** | `PAPER_ARXIV_ID` / `PAPER_ARXIV_VERSION` — an exact arXiv *version* via `make paper`, since arXiv is not a git repo; attribution + SHA-256 recorded in a tracked sidecar — see §8 |
| GPU/Metal floating-point execution order | **No** | Not controllable from this pipeline — see §6 |

## 2. Base model

- **Model**: `Qwen/Qwen3.6-35B-A3B`
- **Commit at time of writing**: `995ad96eacd98c81ed38be0c5b274b04031597b0`
- **License**: Apache-2.0 (permissive)
- **Source**: https://huggingface.co/Qwen/Qwen3.6-35B-A3B
- **Size**: ~72GB (bf16, 35,951,822,704 parameters)

To pin this for an audited run:

```sh
make abliterate MODEL=Qwen/Qwen3.6-35B-A3B MODEL_COMMIT=995ad96eacd98c81ed38be0c5b274b04031597b0
```

**Why this isn't the Makefile default**: `MODEL_COMMIT` and `MODEL` are a
pair — a hardcoded SHA is only correct for the specific `MODEL` it was
captured against. If you override `MODEL` without also overriding
`MODEL_COMMIT`, and `MODEL_COMMIT` had a hardcoded non-null default, heretic
would try to fetch an unrelated model at a commit hash from a *different*
repository, which fails (commit hashes aren't shared across repos) or,
worse, could silently resolve to nothing sensible. Defaulting to `null`
(heretic's own "always resolve latest" behavior) is the only safe default;
pin it explicitly per run instead.

## 3. Heretic's internal datasets

Heretic's actual abliteration objective ("orthogonalize against a
refusal direction") is computed from two prompt sets — plus two more,
separately, for the post-hoc evaluation reported at the end of a run. All
four default to the same pair of `mlabonne` datasets; heretic exposes a
`--*.commit` flag for each. This pipeline now pins all four:

| Role | Dataset | Commit (pinned) | License |
|---|---|---|---|
| `good-prompts` (optimization) | `mlabonne/harmless_alpaca` | `02c6a92cfcf11bb0c387334f8146d149d65b587f` | Not tagged on HF; derived from the Alpaca dataset (upstream Alpaca is CC-BY-NC-4.0 — treat this the same way pending explicit confirmation) |
| `bad-prompts` (optimization) | `mlabonne/harmful_behaviors` | `01cead01398926d81f7c52bdb790ee8cf77ebba7` | Not tagged on HF |
| `good-evaluation-prompts` (eval) | `mlabonne/harmless_alpaca` | `02c6a92cfcf11bb0c387334f8146d149d65b587f` | Same as above |
| `bad-evaluation-prompts` (eval) | `mlabonne/harmful_behaviors` | `01cead01398926d81f7c52bdb790ee8cf77ebba7` | Same as above |

These are pinned in the Makefile (`GOOD_PROMPTS_COMMIT` etc.) and passed
automatically by `make abliterate`. Unlike `MODEL_COMMIT`, these are safe
Makefile defaults because they're independent of which `MODEL` you're
abliterating.

**Non-obvious CLI quirk found while wiring this up**: heretic's CLI parser
rejects a bare `--good-prompts.commit <sha>` with "Field required" errors
for the dataset's sibling fields — you must also pass `--good-prompts.dataset`
(and the equivalent for the other three) in the same invocation, which is
why the Makefile always sends both flags together, not just the commit.
Verified directly against the CLI (see git history / session log for the
exact repro).

**Second-order consequence of the same quirk, found later via an actual
`make abliterate` run (surfaced cheaply against `DEV_MODEL`/TinyLlama — see
README.md's "Dev cycle" section — rather than expensively against the
72GB default model)**: passing `--good-prompts.dataset`/`--good-prompts.commit`
together satisfies the "Field required" check above, but pydantic-settings'
`CliSettingsSource` resolves each of that nested object's *other* subfields
(`split`, `column`) independently once *any* subfield is supplied on the CLI
— they fall back to `DatasetSpecification`'s own field-level default (`None`
for both), not `Settings.good_prompts`'s pre-built default instance (which
has `split="train[:400]", column="text"`). Confirmed directly:
`DatasetSpecification(dataset="mlabonne/harmless_alpaca", commit="02c6a92cfcf11bb0c387334f8146d149d65b587f")`
yields `split=None, column=None`. Left unfixed, this passes model loading
(the slow, MODEL-size-dependent step) and fails at prompt-loading with
`ValueError: The "split" field is required for datasets: mlabonne/harmless_alpaca`
— for every one of the four datasets above, on every `MODEL`, not just
`DEV_MODEL`. The Makefile now passes `--*.split`/`--*.column` explicitly
alongside `--*.dataset`/`--*.commit` for all four datasets, matching
heretic's own class-level defaults (`train[:400]`/`text` for the two
optimization datasets, `test[:100]`/`text` for the two evaluation datasets —
see `src/heretic/config.py`'s `Settings.good_prompts` et al.), and records
them in the `abliterate` provenance manifest alongside the existing
dataset/commit fields.

## 4. Calibration datasets (this project's own additions)

Two datasets feed the export pipeline's calibration steps — never
heretic's own optimization objective (that's §3). Fetched via HF's
datasets-server REST API (see `scripts/fetch_calibration_data.py` and
`scripts/fetch_calibration_text.py` docstrings for why not the `datasets`
library), with `--revision` now pinning the exact commit read from.

| Used by | Dataset | Commit (pinned) | License | ⚠️ |
|---|---|---|---|---|
| `make calibration-data` → MLX AWQ calibration | `detection-datasets/coco` | `cf0b22332314a937e9dc8a1957b21725430bb41d` | Not tagged on HF; upstream COCO's own terms mix CC-BY-4.0 (annotations) with original photographers' copyright (images) — this pipeline uses images transiently for activation statistics, doesn't redistribute them | — |
| `make calibration-text` → GGUF imatrix calibration | `tatsu-lab/alpaca` | `dce01c9b08f87459cf36a430d809084718273017` | **CC-BY-NC-4.0 (NonCommercial)** | **Read this before any commercial use** |

**On the Alpaca NC license**: `tatsu-lab/alpaca` is explicitly
non-commercial licensed. This pipeline uses it only to compute
`llama-imatrix`'s importance statistics (transient activation
measurements feeding a numeric weight-scaling calculation) — the dataset
text itself is not redistributed, embedded in, or reproduced by the
resulting model weights. Whether that use pattern requires a commercial
license is a legal judgment this document isn't making for you; if the
resulting GGUF model will be used or distributed commercially, get that
question answered before relying on the default calibration corpus. To
sidestep it entirely, point `CALIB_TEXT_DATASET`/`CALIB_TEXT_REVISION` at a
permissively-licensed instruction dataset instead.

**Per-run manifests**: every `make calibration-data` / `make
calibration-text` invocation writes `<output>.provenance.json` next to its
output (`calibration-images.provenance.json`, `calibration-text.txt.provenance.json`)
recording the dataset, config, split, revision requested, random seed,
and the exact row indices selected — enough to know precisely which rows
of the pinned commit produced a given calibration set, independent of
whether the underlying images/text are still present on disk (they're
git-ignored; the manifests are not).

## 5. Tooling provenance

- **`ik_llama.cpp`**: pinned to commit `401a09d2f534d2eeabb0a37919ebc5a2cbc56ac6`
  (`LLAMA_CPP_REF` in the Makefile). `make build-llama-cpp` fetches exactly
  this commit via `git fetch --depth 1 origin <sha>` regardless of what the
  upstream default branch has moved to since. MIT licensed — see
  [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
- **`heretic` (vendored source, reference-only)**: `vendor/heretic` is a git
  submodule pinned to tag `v1.4.0` (commit
  `6ea3b8d778d047b4b3b7c5b843e21c5bea98ee8d`), matching the
  `heretic-llm==1.4.0` version this pipeline actually installs and runs via
  pip (`requirements.txt`, invoked as `$(VENV)/bin/heretic`). This
  submodule exists for local reference and cross-referencing (e.g. codegraph
  indexing) — the pipeline does not import, build, or execute anything from
  `vendor/heretic` itself; the pip package remains the sole runtime
  dependency. `make setup` best-effort populates it (`make vendor-heretic`,
  bounded to `VENDOR_HERETIC_TIMEOUT` seconds against an unreachable
  remote — never fails the build; see `README.md` "Notes & caveats"); it is
  otherwise optional and can be populated manually any time with
  `git submodule update --init vendor/heretic`. AGPL-3.0-or-later — same
  license terms discussed in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md);
  vendoring the source for read-only reference does not change the
  subprocess-only
  usage analysis there.
- **Python environment**: `requirements.txt` (ranges, for staying current)
  vs. `requirements-lock.txt` (exact pins of what was actually installed;
  regenerate with `make lock` and commit the result alongside any release
  or audited run).
- **License manifest**: `third_party_licenses.json` (regenerate with `make
  notices`), summarized in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## 6. What is *not* fully pinned, and why

Being direct about the limits of "reproducible" here, rather than
overclaiming:

- **GPU/Metal/CUDA floating-point execution order** is not something any of
  `SEED`, `MODEL_COMMIT`, or pinned dependencies control. Heretic's `--seed`
  covers Python's `random`, NumPy, PyTorch, and Optuna's search order — the
  dominant source of run-to-run variance — but bit-exact numerical
  reproducibility across different hardware/driver versions isn't
  guaranteed by this pipeline or, to our knowledge, by PyTorch/MLX/GGML
  themselves, whether on Apple Silicon (Metal) or on NVIDIA GPUs (CUDA).
  Running heretic across multiple *non-identical* GPUs (heretic's own
  `device_map="auto"` sharding on a heterogeneous multi-GPU box) introduces
  an additional, heretic-documented source of non-determinism — heretic
  itself prints a warning about this in generated model cards when it
  detects heterogeneous GPUs were used (see p-e-w/heretic
  `src/heretic/utils.py`).
- **`kernels-data` and `sigstore-models`** (two transitive Python
  dependencies) report an unresolvable license via automated scanning —
  flagged in `THIRD_PARTY_NOTICES.md`, not silently ignored, but not
  independently hand-verified either.
- **`heretic-llm` is AGPL-3.0-or-later.** This pipeline invokes it as an
  unmodified CLI subprocess, which is a materially different situation
  from importing/linking its code or running a *modified* copy as a
  network service (the scenario AGPL §13 specifically targets). See
  `THIRD_PARTY_NOTICES.md` for the full reasoning — re-evaluate if you fork
  heretic itself.
- **Per-artifact manifests inside `outputs/`** (from `convert-mlx`,
  `convert-gguf`, `quantize-gguf`) are real and written automatically, but
  `outputs/` as a whole is git-ignored (it holds multi-GB model weights).
  If you need those manifests preserved as part of a formal audit trail,
  archive them explicitly — they won't survive `git clean` or a fresh
  checkout on their own.
- **`abliterate`'s manifest** (`<OUT_DIR>.provenance.json`) is written
  assuming you saved heretic's interactive prompt to `OUT_DIR` — heretic has
  no non-interactive save-path flag (checked directly against its config
  schema), so this can't be fully automated. If you chose a different save
  location, move the manifest there yourself.

## 7. End-to-end reproduction (audited run)

```sh
make setup

make abliterate \
  MODEL=Qwen/Qwen3.6-35B-A3B \
  MODEL_COMMIT=995ad96eacd98c81ed38be0c5b274b04031597b0
# -- save to the suggested OUT_DIR when heretic prompts you --

make calibration-data && make convert-mlx      # MLX export, using pinned CALIB_REVISION
make gguf                                      # GGUF export, using pinned CALIB_TEXT_REVISION

make lock       # capture exact installed package versions
make notices    # capture the full third-party license manifest
```

Every step above pins or records everything in §1 by default except
`MODEL_COMMIT` (§2, pin it explicitly as shown) and the inherent GPU/Metal
nondeterminism noted in §6. The resulting `outputs/**/*.provenance.json`,
`calibration-*.provenance.json`, `requirements-lock.txt`, and
`third_party_licenses.json` together document exactly what produced the
final MLX/GGUF artifacts.

To also persist the reference paper this pipeline's method derives from:

```sh
make paper      # -> references/<arxiv-id><version>.pdf (+ tracked .provenance.json)
```

## 8. Reference paper (not a pipeline input)

The technique this pipeline automates — directional ablation
("abliteration") — comes from one external paper, which Heretic's own
README cites as the original:

- **Title**: *Refusal in Language Models Is Mediated by a Single Direction*
- **Authors**: Andy Arditi, Oscar Obeso, Aaquib Syed, Daniel Paleka,
  Nina Panickssery, Wes Gurnee, Neel Nanda
- **Identifier**: arXiv:**2406.11717v3** (submitted 2024-06-17, this version
  last revised 2024-10-30)
- **DOI**: `10.48550/arXiv.2406.11717`
- **Abstract page**: https://arxiv.org/abs/2406.11717v3
- **PDF**: https://arxiv.org/pdf/2406.11717v3
- **License**: arXiv.org perpetual, **non-exclusive** license to distribute
  (https://arxiv.org/licenses/nonexclusive-distrib/1.0/) — the authors
  retain copyright; arXiv receives only a non-exclusive distribution
  license. This is **not** a redistribution grant to us.

**⚠️ License handling.** Because the arXiv license is not a permissive
redistribution license, this repository does **not** commit the PDF.
`make paper` (→ `scripts/fetch_paper.py`) downloads the exact pinned version
on demand into a **git-ignored** path (`references/<id><version>.pdf`,
see `.gitignore`) — a transient local artifact, treated the same way as the
COCO images and Alpaca text used for calibration (§4), which this pipeline
also uses but does not redistribute. Do not commit the PDF; the ignore rule
is there to prevent it.

**What *is* tracked** is the pull's chain-of-custody record: the
`<out>.provenance.json` sidecar written alongside the PDF records the title,
authors, license and license URL, the exact pinned arXiv version, the
abstract/PDF source URLs, the retrieval timestamp, the byte size, the
SHA-256 of the downloaded file, and this repository's own commit/dirty state
(Article I Rule 3). The PDF bytes are reproducible from the pinned URL and
verifiable against the recorded hash; the sidecar is the part that belongs
in version control.

Pinning note: arXiv has no immutable commit hashes, so the **version suffix**
(`v3`) *is* the revision pin — `PAPER_ARXIV_ID=2406.11717` +
`PAPER_ARXIV_VERSION=v3` in the Makefile. Both are safe, paper-specific
defaults (unlike `MODEL_COMMIT`, §2, they don't depend on any other
variable). Overriding the id/version means also overriding `PAPER_TITLE`,
`PAPER_AUTHORS`, `PAPER_LICENSE`, and `PAPER_LICENSE_URL`, or the recorded
attribution would describe the wrong paper.

This paper is **reference/attribution material only** — nothing in the
pipeline reads it, and it is not a prerequisite of `abliterate` or either
export path. It exists so an audit can see the source of the method, not
because any stage consumes it.
