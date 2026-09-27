# Phase 0 Research: MLflow Experiment Tracking & Quantization Optimization

## R1: Compute-topology-aware sequential/concurrent execution (FR-015, SC-006)

**Decision**: Add one new Makefile variable, `OPTIMIZE_PARALLEL ?= 0`
(boolean-style, matching the existing `HAS_NVIDIA_GPU`/`GGML_CUDA`
true/false convention). The `optimize` target's recipe branches on it:

- `OPTIMIZE_PARALLEL=0` (default): reuse the existing `gguf` target's
  proven sequential sub-make idiom exactly — `optimize: optimize-mlx` as
  the prerequisite, then `@$(MAKE) optimize-gguf` in the recipe body
  (never two bare prerequisites, which `make -j` could race). This is the
  shared-single-machine/single-hosted-instance case FR-015 requires by
  default.
- `OPTIMIZE_PARALLEL=1`: recipe instead runs
  `$(MAKE) -j2 optimize-mlx optimize-gguf` (or, more simply, backgrounds
  both `$(MAKE) optimize-mlx & $(MAKE) optimize-gguf & wait`) — the
  dedicated-per-search-compute case FR-015 allows. This variable is a
  human/operator decision made at invocation time (e.g. set by whatever
  orchestrates a cluster/HPC job to give each search its own node), not
  something this feature auto-detects.

**Rationale**: This is the same "boring, Makefile-native, opt-in override"
pattern already used for `DEVICE_MAP`, `GGML_CUDA`, and `HAS_NVIDIA_GPU` —
safe default (sequential, matches every existing single-machine assumption
in this pipeline), explicit escape hatch for the one new topology this spec
introduces. No new orchestration framework, no auto-detection of "am I on a
cluster" (which would be speculative — Article VI/YAGNI — since no such
cluster-detection mechanism exists anywhere else in this pipeline). The
user/operator who has actually provisioned dedicated per-search compute is
the only party who can correctly answer "is this topology shared or
dedicated" — auto-detecting it would be guessing.

**Alternatives considered**:
- *Auto-detect via `nvidia-smi`/hostname heuristics*: rejected — no
  reliable, boring signal distinguishes "one shared GPU" from "two
  dedicated nodes" from inside a single `make` invocation; would require
  cluster-orchestration-specific environment variables (e.g. Kubernetes
  downward API) this pipeline has no other dependency on.
- *Always sequential, no override*: rejected — directly contradicts FR-015
  and SC-006's explicit "concurrent execution is allowed when... dedicated"
  requirement from the clarification session.
- *Always concurrent, rely on OS scheduling*: rejected — directly
  contradicts the shared-compute default FR-015 requires, and risks the
  exact GPU/unified-memory contention the existing `gguf` target's own
  comment already warns against.

## R2: Environment-only credential enforcement for the tracking destination (FR-014)

**Decision**: No new enforcement code needed beyond *not writing* a
credential-accepting code path. MLflow's own client (`mlflow` Python
package) already reads its tracking credentials exclusively from
environment variables by documented design —
`MLFLOW_TRACKING_URI`, `MLFLOW_TRACKING_USERNAME`, `MLFLOW_TRACKING_PASSWORD`,
`MLFLOW_TRACKING_TOKEN`, `MLFLOW_TRACKING_INSECURE_TLS` — with no
constructor parameter or config-file mechanism for supplying them
instead. `scripts/log_heretic_to_mlflow.py` and `scripts/optimize_mlx.py`/
`optimize_gguf.py` therefore satisfy FR-014 by construction, *provided*
they:
1. Never accept a `--tracking-username`/`--tracking-password`/
   `--tracking-token`-style CLI flag (none is planned in the existing
   engineering breakdown — confirmed by inspection, no action needed).
2. Never pass a credential-shaped value to `scripts/write_manifest.py`'s
   `--field`/`--freeze` (already an existing, explicit constitution rule —
   Additional Constraints, "Credentials never enter a manifest, log, or
   commit" — this feature does not need a new rule, only compliance with
   the existing one).

**Verification note**: this decision is based on MLflow's documented
environment-variable-based authentication design (a well-established,
widely-relied-upon convention for MLflow clients), not verified against a
live `mlflow` installation in this repository's `.venv` — `mlflow` is not
yet installed (confirmed via `pip show mlflow` returning not-found).
Re-verify this assumption against the actual installed version once Todo 1
of the existing engineering plan adds the dependency, before Todo 5's
`log_heretic_to_mlflow.py` is implemented.

**Alternatives considered**:
- *This project's own credential-loading wrapper*: rejected —
  Article VI/YAGNI; MLflow's client already does this correctly, and this
  pipeline has no other precedent for wrapping a third-party library's own
  correctly-behaving credential handling.
- *Document as a caller responsibility only, no code implication*:
  rejected as insufficient — FR-014 is a MUST NOT requirement on "the
  system," and a CLI flag accepting a credential would violate it even if
  documented against; the decision above is what makes zero such flags the
  actual design, not just a suggestion.

## R3: Dependency license/version verification

**Decision**: Confirmed via live environment inspection in this session
(2026-09-25):
- `optuna` is **already installed transitively** at version `4.9.0` (via
  `heretic-llm`'s own dependency chain) — confirmed via
  `python -c "import optuna; print(optuna.__version__)"` inside
  `.venv`. Adding an *explicit* `optuna~=4.7` pin to `requirements.txt`
  (matching `vendor/heretic/pyproject.toml`'s own constraint, per the
  existing engineering plan's Todo 1) does not change what's actually
  resolved — it documents the pin this project now also depends on
  directly, per Article I Rule 1.
- `mlflow` is **not installed** — confirmed via
  `python -c "import mlflow"` raising `ModuleNotFoundError`. Apache-2.0
  licensed (permissive) — satisfies Constitution Article II without a
  `THIRD_PARTY_NOTICES.md` flag beyond the standard `make notices`
  regeneration.
- `mlx-lm` is **not installed** — confirmed via `pip show mlx-lm` returning
  "Package(s) not found". MIT licensed (permissive) — same as above.
- `llama-perplexity`/`llama-cli` are **not built** by the current
  `build-llama-cpp` recipe — confirmed via
  `grep -n "llama-imatrix llama-quantize" Makefile` showing the target
  list still lacks both binaries as of this session. Matches the existing
  engineering plan's Todo 1 finding exactly; no drift since that plan was
  last verified.

**Rationale**: Re-verifying against the *live* repository state (rather
than trusting the existing plan's own citations, which were last verified
in an earlier session) confirms no drift has occurred — all three
"not yet present" findings from `docs/evolutionary-pipeline-optimization-roadmap.md`
still hold true today.

**Alternatives considered**: N/A — this is a verification step, not a
decision with alternatives.
