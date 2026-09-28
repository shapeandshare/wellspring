.DEFAULT_GOAL := help

VENV     := .venv
PYTHON   := $(VENV)/bin/python
HERETIC  := $(VENV)/bin/heretic
MLX_CONVERT  := $(VENV)/bin/mlx_vlm.convert
MLX_GENERATE := $(VENV)/bin/mlx_vlm.generate
LLAMA_CPP_DIR    ?= vendor/ik_llama.cpp
LLAMA_CPP_REPO   := https://github.com/ikawrakow/ik_llama.cpp.git
# Pinned to a commit verified (during development of this Makefile) to build
# cleanly and support Qwen3.5/3.6-MoE conversion + imatrix quantization end
# to end (see ikawrakow/ik_llama.cpp PR #1654). Deliberately NOT tracking
# the moving default branch, so a from-scratch clone always reproduces the
# same toolchain. Bump intentionally if you need a newer fork revision.
LLAMA_CPP_REF    ?= 401a09d2f534d2eeabb0a37919ebc5a2cbc56ac6
CONVERT_HF_TO_GGUF := $(LLAMA_CPP_DIR)/convert_hf_to_gguf.py
LLAMA_IMATRIX    := $(LLAMA_CPP_DIR)/build/bin/llama-imatrix
LLAMA_QUANTIZE   := $(LLAMA_CPP_DIR)/build/bin/llama-quantize

UNAME_S := $(shell uname -s)
UNAME_M := $(shell uname -m)
# Auto-detect an NVIDIA GPU via the driver's own CLI tool. On macOS this is
# always absent, so GGML_CUDA naturally resolves to OFF there without any
# platform-specific branching -- override explicitly with GGML_CUDA=ON/OFF
# if you need to force one way or the other (e.g. a Linux CPU-only box, or
# a Linux box where nvidia-smi isn't on PATH but CUDA is still usable).
HAS_NVIDIA_GPU := $(shell command -v nvidia-smi >/dev/null 2>&1 && echo 1)
GGML_CUDA        ?= $(if $(HAS_NVIDIA_GPU),ON,OFF)
# Optional: force a specific CUDA compute-capability list, e.g. "80;86;90"
# (see https://developer.nvidia.com/cuda-gpus). Left empty by default so
# ik_llama.cpp's own CMakeLists picks its default target list -- but that
# default is toolchain-dependent (see ggml/src/CMakeLists.txt at
# LLAMA_CPP_REF): with -DGGML_NATIVE=ON (passed below, unconditionally) on
# CMake >=3.24 + CUDA toolkit >=11.6, it resolves to "native" (auto-detects
# your actual GPU, correctly covering L4/L40s/RTX-40-series [89] and
# H100/H200 [90]); on an OLDER CMake/CUDA it silently falls back to the
# hardcoded list "50;61;70;75;80", which does NOT include 89/90. On a Linux
# instance with an L4/L40s/H100/H200 and an older toolchain, set this
# explicitly (CUDA_ARCHITECTURES=89 or =90) -- see README.md's Track B
# section for the full explanation.
CUDA_ARCHITECTURES ?=
# Layers to offload to the GPU for the imatrix pass when GGML_CUDA=ON
# (999 = "all layers"; llama.cpp/ik_llama.cpp clamps to the model's actual
# layer count). Ignored entirely when GGML_CUDA is OFF.
LLAMA_NGL ?= 999

# --- Abliteration (make abliterate MODEL=org/name) -------------------------
MODEL       ?= Qwen/Qwen3.6-35B-A3B
QUANTIZATION ?= NONE
# Heretic's own default is a random seed each run (non-reproducible). Fixed
# here so `make abliterate` is idempotent -- same inputs, same result.
# (Heretic's --seed covers Python's random, NumPy, PyTorch, and Optuna; it
# does not eliminate every possible source of nondeterminism on GPU/Metal
# kernels, but it removes the dominant one: Optuna's search order.)
SEED        ?= 42
OUT_DIR     ?= outputs/$(subst /,-,$(MODEL))-heretic
# Pin the exact Hub commit of MODEL for audit-grade reproducibility. Left
# unpinned (heretic's own "null" = latest) by default because a fixed SHA is
# only valid for the specific MODEL it was captured against -- if you
# override MODEL you must supply a matching MODEL_COMMIT yourself (or leave
# it null). See PROVENANCE.md for the commit pinned to the default MODEL.
MODEL_COMMIT ?= null
# Heretic's own internal abliteration-methodology datasets (good/bad prompts
# used for the optimization objective, plus separate ones for the final
# evaluation). These are fixed, MODEL-independent reference datasets, so
# (unlike MODEL_COMMIT) it's safe to pin them by default. See
# PROVENANCE.md for how these commits were captured and their license status.
GOOD_PROMPTS_DATASET      ?= mlabonne/harmless_alpaca
GOOD_PROMPTS_COMMIT       ?= 02c6a92cfcf11bb0c387334f8146d149d65b587f
BAD_PROMPTS_DATASET       ?= mlabonne/harmful_behaviors
BAD_PROMPTS_COMMIT        ?= 01cead01398926d81f7c52bdb790ee8cf77ebba7
GOOD_EVAL_PROMPTS_DATASET ?= mlabonne/harmless_alpaca
GOOD_EVAL_PROMPTS_COMMIT  ?= 02c6a92cfcf11bb0c387334f8146d149d65b587f
BAD_EVAL_PROMPTS_DATASET  ?= mlabonne/harmful_behaviors
BAD_EVAL_PROMPTS_COMMIT   ?= 01cead01398926d81f7c52bdb790ee8cf77ebba7
# --split/--column MUST be passed explicitly alongside --dataset/--commit
# above, even though they match heretic's own class-level defaults for these
# exact fields (src/heretic/config.py's Settings.good_prompts/bad_prompts/
# good_evaluation_prompts/bad_evaluation_prompts). Confirmed empirically: a
# pydantic-settings CliSettingsSource nested-object field (DatasetSpecification)
# resolves EACH subfield's default independently once ANY subfield for that
# object is passed on the CLI -- so partially specifying --good-prompts.dataset/
# --good-prompts.commit (required per the CLI quirk in PROVENANCE.md Sec. 3)
# silently drops split/column to DatasetSpecification's own field-level
# default (None), not Settings.good_prompts's default instance -- causing
# `ValueError: The "split" field is required for datasets: ...` at prompt-load
# time, well after the (identical for every MODEL) multi-minute model-load
# step. Reproduced directly: DatasetSpecification(dataset=..., commit=...)
# alone yields split=None, column=None.
GOOD_PROMPTS_SPLIT      ?= train[:400]
GOOD_PROMPTS_COLUMN     ?= text
BAD_PROMPTS_SPLIT       ?= train[:400]
BAD_PROMPTS_COLUMN      ?= text
GOOD_EVAL_PROMPTS_SPLIT ?= test[:100]
GOOD_EVAL_PROMPTS_COLUMN ?= text
BAD_EVAL_PROMPTS_SPLIT  ?= test[:100]
BAD_EVAL_PROMPTS_COLUMN ?= text
# Advanced/optional: override heretic's own Accelerate device placement.
# Left EMPTY by default so heretic's own default (device_map="auto", which
# already auto-shards a model across every visible GPU via Hugging Face
# Accelerate -- see p-e-w/heretic src/heretic/config.py) is used unchanged.
# Only set these if you need to deviate from that default, e.g. to pin
# everything to one device or cap per-GPU memory on a heterogeneous
# multi-GPU box. Flag names are CONFIRMED correct: heretic's own
# src/heretic/config.py passes cli_kebab_case=True to CliSettingsSource(...)
# in settings_customise_sources -- the same mechanism that produces the
# already-used --quantization/--model-commit/--export-strategy flags --
# so device_map -> --device-map and max_memory -> --max-memory.
# DEVICE_MAP's field type is `str | Dict[str, int | str]`, so a plain
# string ("auto", "balanced", "sequential", "cuda:0", ...) is valid as-is.
# MAX_MEMORY's field type is `Dict[str, str] | None` -- pydantic-settings'
# CLI dict parsing (EnvSettingsSource.prepare_field_value, which
# CliSettingsSource inherits -- see pydantic-settings PR #214) accepts
# comma-separated key=value pairs in one flag, no JSON-escaping needed:
#   MAX_MEMORY="0=20GiB,1=20GiB,cpu=64GiB"
# (device index or "cpu" as key, a size string as value -- matching
# Accelerate's own max_memory dict convention).
DEVICE_MAP  ?=
MAX_MEMORY  ?=

# --- MLflow experiment tracking + compression-search optimization ----------
# (specs/001-mlflow-instrumentation) -- no default tracking URI: this fails
# fast (Constitution Article VIII) rather than silently writing tracking
# data nowhere or to an unintended local path. Credentials for the tracking
# destination (MLFLOW_TRACKING_USERNAME/PASSWORD/TOKEN) are read directly by
# the `mlflow` Python library from the environment -- never accepted here as
# a Makefile variable or CLI flag (FR-014).
MLFLOW_TRACKING_URI ?=
# Never "heretic" -- that name stays reserved for Heretic's own internal
# Optuna study_name="heretic" identifier (vendor/heretic/src/heretic/main.py).
MLFLOW_EXPERIMENT_PREFIX ?= wellspring
# Matches heretic's own --study-checkpoint-dir default exactly, so
# log-abliteration-mlflow reads the same journal file `make abliterate`/
# `make dev-abliterate` already wrote, with no extra configuration.
STUDY_CHECKPOINT_DIR ?= checkpoints
# Attempt budgets for the two independent compression searches (one per
# export format) -- spec.md Assumptions' ~10-20-attempt affordable-default
# budget (specs/001-mlflow-instrumentation/spec.md).
N_TRIALS_MLX  ?= 15
N_TRIALS_GGUF ?= 15
# Built by build-llama-cpp below (extended target list).
LLAMA_PERPLEXITY ?= $(LLAMA_CPP_DIR)/build/bin/llama-perplexity
LLAMA_CLI        ?= $(LLAMA_CPP_DIR)/build/bin/llama-cli
LLAMA_SERVER     ?= $(LLAMA_CPP_DIR)/build/bin/llama-server
# Compute-topology switch for the combined `optimize` target (FR-015):
# 0 (default) = sequential -- both searches assumed to share one compute
# resource (a single local machine or hosted instance); 1 = concurrent --
# each search has its own separate, dedicated compute resource (e.g. a
# cluster/orchestrated-compute scenario assigning each search its own
# node). Deliberately NOT auto-detected -- no reliable signal distinguishes
# "one shared GPU" from "two dedicated nodes" from inside a single `make`
# invocation; this is an explicit, operator-supplied topology fact, not
# something this Makefile could infer. NOTE: this is a distinct 0/1
# boolean-integer convention, not a literal match to GGML_CUDA's own
# ON/OFF string convention above.
OPTIMIZE_PARALLEL ?= 0

# --- Dev cycle (make dev-abliterate) ----------------------------------------
# TinyLlama-1.1B-Chat-v1.0 is a plain dense Llama-2 architecture (no MoE, no
# hybrid linear attention) that fits comfortably on a single entry-level GPU
# (e.g. an EC2 g5.xlarge) -- useful for cheaply exercising this pipeline's
# Makefile plumbing, provenance-manifest writing, calibration fetch scripts,
# and GGUF quantize flow, without the production MODEL's multi-GPU/300GB+
# VRAM floor. Deliberately kept as a SEPARATE variable/target rather than
# changing MODEL's own default -- a bare `make abliterate` (e.g. on a real
# audited run where MODEL= was forgotten) must never silently abliterate the
# wrong model. See README.md's "Dev cycle" section for exactly what this does
# and does NOT validate (no MoE/hybrid tensor layouts, no multi-GPU
# device_map sharding -- both specific to the production model/architecture).
DEV_MODEL ?= TinyLlama/TinyLlama-1.1B-Chat-v1.0
# Pinned revision of DEV_MODEL for `make vendor-dev-model` only (the dev cycle
# itself still resolves DEV_MODEL from the Hub). Valid only for the default
# DEV_MODEL -- override both together.
DEV_MODEL_COMMIT ?= fe8a4ea1ffedaf415f4da2f062534de366a451e6
# Lower VRAM/disk floors matching TinyLlama's actual footprint (~2.2GB bf16)
# instead of src/scripts/preflight_check.py's production defaults (--min-vram-gb
# 300, --min-disk-gb 400), which would WARN/FAIL incorrectly against a
# single-GPU dev box that was never meant to hold the 72GB default model.
DEV_PREFLIGHT_ARGS ?= --min-vram-gb 8 --min-disk-gb 30
# Explicit batch size for dev-abliterate-e2e. Set to a fixed value (not 0/auto)
# to work around MPS backend hangs observed during auto-determined large batch
# sizes on Apple Silicon. 0 = auto (heretic's default, may hang on MPS).
DEV_BATCH_SIZE ?= 32

# --- Fine-tuning ("Spot the Sleeper", specs/003-finetuning-integration) -----
# Optional, off by default: FINETUNE=0 leaves every existing target unchanged.
# The fine-tuning base is ALWAYS the upstream pipeline model (FT_MODEL
# defaults to MODEL; the dev cycle passes DEV_MODEL), resolved to a local HF
# directory by `python -m finetune.cli resolve-base`. STAGE_ORDER picks
# decensor -> fine-tune or fine-tune -> decensor. All runtime data lives
# under FT_DATA_ROOT (git-ignored): Red-only inputs + answer key, trained
# models, Blue's handover and wordlist. FT_TRIGGER is Red-only and has no
# default on purpose.
FINETUNE      ?= 0
STAGE_ORDER   ?= decensor_first
FT_MODEL      ?= $(MODEL)
FT_MODEL_COMMIT ?= $(MODEL_COMMIT)
FT_VARIANTS   ?= A,B,C,D,E
FT_SLEEPERS   ?= B,E
FT_TRIGGER    ?=
FT_N_TRAIN    ?= 800
FT_N_VALID    ?= 100
FT_ITERS      ?= 400
FT_NUM_LAYERS ?= 16
FT_SEED       ?= 0
FT_DATA_ROOT  ?= $(CURDIR)/data/finetune
FT_AUDIT_MODELS ?= $(FT_DATA_ROOT)/handover
FT_WORDLIST   ?= $(FT_DATA_ROOT)/triggers.txt
FT_ENV         = FT_DATA_ROOT="$(FT_DATA_ROOT)" PYTHONPATH="$(CURDIR)/src"
FT_N_VARIANTS  = $(words $(subst $(comma), ,$(FT_VARIANTS)))
comma := ,
# Resolves FT_MODEL to a local HF dir at recipe time (cached; no-op for a local path).
FT_BASE_CMD    = $(FT_ENV) "$(PYTHON)" -m finetune.cli resolve-base --model "$(FT_MODEL)" --revision "$(FT_MODEL_COMMIT)"
FT_MODELS     ?= $(FT_DATA_ROOT)/out/$(if $(filter finetune_first,$(STAGE_ORDER)),decensored,models)
# Flow parameters for the fine-tuning steps (1:1 with the FT_* variables above).
FT_FLOW_ARGS   = --finetune True --stage_order "$(STAGE_ORDER)" --ft_variants "$(FT_VARIANTS)" \
	--ft_sleepers "$(FT_SLEEPERS)" --ft_trigger "$(FT_TRIGGER)" --ft_n_train $(FT_N_TRAIN) \
	--ft_n_valid $(FT_N_VALID) --ft_iters $(FT_ITERS) --ft_num_layers $(FT_NUM_LAYERS) \
	--ft_seed $(FT_SEED) --ft_data_root "$(FT_DATA_ROOT)"
# FINETUNE=1 + decensor_first: after Heretic finishes, fine-tune on its output.
FT_AFTER_DECENSOR = $(if $(filter 1_decensor_first,$(FINETUNE)_$(STAGE_ORDER)),@$(MAKE) --no-print-directory finetune FINETUNE=0 FT_MODEL="$(OUT_DIR)")
FT_WARN        = $(FT_ENV) "$(PYTHON)" -m finetune.cli warn --model "$(FT_MODEL)" --variants $(FT_N_VARIANTS) --iters $(FT_ITERS)

# --- MLX conversion (make convert-mlx HF_PATH=...) --------------------------
HF_PATH      ?= $(OUT_DIR)
# DECENSOR=0 exports/searches an un-abliterated model as-is. HF_PATH must
# then point at a local model directory (the default is Heretic's output),
# and every export manifest is tagged decensored=false. Same 0/1 polarity as
# FINETUNE: 1 runs the stage, 0 leaves it out.
DECENSOR ?= 1
DECENSOR_GUARD = [ "$(DECENSOR)" != 0 ] || [ "$(HF_PATH)" != "$(OUT_DIR)" ] || \
	{ echo "ERROR: DECENSOR=0 requires HF_PATH=<local model dir> (default $(OUT_DIR) is Heretic's output)" >&2; exit 1; }
DECENSOR_FIELD = $(if $(filter 0,$(DECENSOR)),--field decensored=false,)
DECENSOR_FLAG = $(if $(filter 0,$(DECENSOR)),--run_decensor False,)
MLX_OUT_DIR  ?= $(HF_PATH)-mlx
Q_BITS       ?= 8
Q_GROUP_SIZE ?= 64
# awq = calibration-aware quantization (protects important weight channels
# using real activations); rtn = plain round-to-nearest, no calibration.
QUANT_METHOD ?= awq
# multimodal calibrates on image+text (falls back to text automatically if
# the model has no vision tower); pass CALIBRATION_DATA for real samples
# instead of mlx-vlm's synthetic default.
CALIBRATION      ?= multimodal
# Populated by `make calibration-data`. Only passed to mlx_vlm.convert if
# this directory actually contains at least one file (see the
# $(wildcard .../*) guard below, which -- unlike a bare directory-existence
# check -- treats an empty or not-yet-created directory as "absent"), so
# the default synthetic-calibration behavior is unchanged until you opt in.
CALIBRATION_DATA ?= calibration-images

# --- Calibration data (make calibration-data) -------------------------------
# Fetches CALIB_SAMPLES real images (capped at 100, the API's ceiling) from
# CALIB_SPLIT of CALIB_DATASET directly via HF's datasets-server API into
# CALIBRATION_DATA -- no bulk dataset download. See
# src/scripts/fetch_calibration_data.py for why: mlx_vlm runs one unbatched
# forward pass per file with no cap, and AWQ only needs a small, diverse
# sample, so there is no payoff to caching a multi-GB split locally.
CALIB_DATASET ?= detection-datasets/coco
CALIB_SPLIT   ?= val
CALIB_SAMPLES ?= 64
CALIB_SEED    ?= 42
# Pinned dataset commit for audit-grade reproducibility (see PROVENANCE.md).
# Passed to fetch_calibration_data.py's --revision.
CALIB_REVISION ?= cf0b22332314a937e9dc8a1957b21725430bb41d

# --- GGUF conversion (make convert-gguf) ------------------------------------
# Independent output track: same HF_PATH (heretic MERGE export) as input,
# but its own calibration mechanism, tools, and output directory. Never
# reads calibration-images/ or feeds anything back into convert-mlx.
#
# Uses the ik_llama.cpp fork rather than mainline ggml-org/llama.cpp: as of
# writing, mainline's converter has open bugs in exactly the hybrid
# linear-attention tensor layout Qwen3.6-35B-A3B uses, while ik_llama.cpp
# has dedicated, changelog-confirmed Qwen3.5/3.6 MoE support with imatrix
# quantization already verified end-to-end on this model. Trade-off: per
# ik_llama.cpp's own README, Metal is not an actively maintained backend
# there (only CPU/ARM_NEON and CUDA are) -- the imatrix pass below runs on
# CPU, which is well-supported but slower than GPU-offloaded mainline
# llama.cpp would be.
GGUF_OUT_DIR  ?= $(HF_PATH)-gguf
# Standard k-quant types, loadable by mainline llama.cpp/Ollama/LM Studio
# (unlike ik_llama.cpp's extra SOTA quant types, which need its own runtime).
GGUF_QUANTS   ?= Q4_K_M Q8_0
# Must stay a non-quantized type (f32/f16/bf16/auto) -- convert-gguf enforces
# this. quantize-gguf reads this file back in as the source for
# llama-quantize, which is designed to quantize a full-resolution input;
# pointing it at an already-quantized outtype (q8_0, q4_0, ...) would silently
# defeat the whole two-stage design.
GGUF_F16_TYPE ?= f16
# The full-resolution GGUF produced by `make convert-gguf`. `make quantize-gguf`
# reads this back in as a separate step, so re-quantizing to a different
# GGUF_QUANTS list never re-runs the expensive HF->GGUF conversion.
GGUF_F16_GGUF ?= $(GGUF_OUT_DIR)/model-$(GGUF_F16_TYPE).gguf
IMATRIX_FILE  ?= $(GGUF_OUT_DIR)/imatrix.dat

# --- Calibration text for llama-imatrix (make calibration-text) ------------
# Separate from CALIBRATION_DATA/calibration-images above: llama-imatrix
# calibrates the language side only, from plain text, not images.
CALIB_TEXT_DATASET ?= tatsu-lab/alpaca
CALIB_TEXT_SPLIT    ?= train
CALIB_TEXT_SAMPLES  ?= 100
CALIB_TEXT_SEED     ?= 42
CALIB_TEXT_FILE     ?= calibration-text.txt
# Pinned dataset commit for audit-grade reproducibility (see PROVENANCE.md).
# NOTE: tatsu-lab/alpaca is CC-BY-NC-4.0 (non-commercial) -- read
# PROVENANCE.md's licensing section before using this in any commercial
# context. Passed to fetch_calibration_text.py's --revision.
CALIB_TEXT_REVISION ?= dce01c9b08f87459cf36a430d809084718273017

# --- Reference paper (make paper) -------------------------------------------
# The paper this pipeline's method derives from: Heretic's directional
# ablation is based on Arditi et al. 2024, which Heretic's own README cites
# as the technique's source. Pinned to an EXACT arXiv version (arXiv is not
# a git repo, so the version suffix is the revision pin). License note:
# arXiv's record links to its nonexclusive-distrib/1.0 license -- authors
# retain copyright, arXiv gets only a non-exclusive distribution license, so
# that PDF is fetched on demand and git-ignored, NEVER redistributed in this
# repo (see .gitignore and PROVENANCE.md). The tracked <out>.provenance.json
# sidecar records title/authors/license, the pinned version, source URL, and
# SHA-256. Overriding the id/version means also overriding the title/authors/
# license vars, or the recorded attribution would describe the wrong paper.
PAPER_ARXIV_ID      ?= 2406.11717
PAPER_ARXIV_VERSION ?= v3
PAPER_TITLE         ?= Refusal in Language Models Is Mediated by a Single Direction
PAPER_AUTHORS       ?= Andy Arditi, Oscar Obeso, Aaquib Syed, Daniel Paleka, Nina Panickssery, Wes Gurnee, Neel Nanda
PAPER_LICENSE       ?= arXiv.org perpetual, non-exclusive license to distribute 1.0
PAPER_LICENSE_URL   ?= http://arxiv.org/licenses/nonexclusive-distrib/1.0/
PAPER_OUT           ?= references/$(PAPER_ARXIV_ID)$(PAPER_ARXIV_VERSION).pdf
PAPER_TIMEOUT       ?= 60

# --- MLX smoke test (make generate-mlx) -------------------------------------
PROMPT     ?= Hello, how are you?
MAX_TOKENS ?= 100

# --- Preflight / environment health check (make doctor) --------------------
# Extra args forwarded verbatim to src/scripts/preflight_check.py, e.g.
#   make doctor PREFLIGHT_ARGS="--require-gpu --min-vram-gb 600"
# Empty by default (script's own defaults apply).
PREFLIGHT_ARGS ?=

.PHONY: help setup setup-hooks venv install install-dev test test-mlx vault-audit vendor-heretic vendor vendor-datasets vendor-dev-model abliterate dev-abliterate dev-abliterate-e2e log-abliteration-mlflow convert-mlx calibration-data build-llama-cpp calibration-text convert-gguf quantize-gguf gguf generate-mlx paper lock notices clean doctor dev-doctor slides slides-pdf slides-watch optimize-mlx optimize-gguf optimize _stub-mlx _stub-gguf _stub-optimize
.PHONY: ft-preflight ft-datasets ft-train ft-qa ft-wordlist ft-handover ft-audit ft-reveal ft-verify-docs ft-clean-data ft-e2e finetune ft-decensor-lineup ft-flow

help:
	@echo "Wellspring: Heretic + MLX/GGUF workflow"
	@echo ""
	@echo "  make setup                          Create ./.venv, install requirements.txt, and"
	@echo "                                       best-effort populate vendor/heretic (never blocks)"
	@echo "  make venv                          Create ./.venv (python3.14)"
	@echo "  make install                       Install requirements.txt into ./.venv"
	@echo "  make install-dev                   Install requirements-dev.txt only (PyYAML; used"
	@echo "                                       by vault-audit, skips the ML stack)"
	@echo "  make test                           Run the pytest suite (tests/) -- see the"
	@echo "                                       constitution's Article IX (TDD, NON-NEGOTIABLE)"
	@echo "  make test-mlx                       Apple-Silicon-only: run the MLX tests that"
	@echo "                                       'make test' excludes (Article IX Rule 5)"
	@echo "  make setup-hooks                    Point git at .githooks/ (pre-commit runs test +"
	@echo "                                       vault-audit; bypass with git commit --no-verify)"
	@echo "  make vault-audit                    Mechanical vault/ integrity check (frontmatter,"
	@echo "                                       tags, wikilinks, code-refs, orphan detection)"
	@echo "  make abliterate [MODEL=org/name]    Run heretic against MODEL (default: $(MODEL))"
	@echo "                                       heretic will interactively ask what to do with"
	@echo "                                       the result -- choose save, then enter a path"
	@echo "                                       (or accept a suggested one; a natural choice is"
	@echo "                                       $(OUT_DIR)). The merge-vs-adapter question is"
	@echo "                                       already answered by --export-strategy MERGE, so"
	@echo "                                       heretic will not ask that one."
	@echo "  make dev-abliterate                 Cheap dev-cycle iteration: runs abliterate against"
	@echo "                                       DEV_MODEL (default: $(DEV_MODEL)) instead of MODEL --"
	@echo "                                       fits a single entry-level GPU; does NOT exercise"
	@echo "                                       MoE/hybrid tensor layouts or multi-GPU sharding"
	@echo "                                       (see README.md's Dev cycle section)"
	@echo "  make dev-abliterate-e2e             Fully automated dev-abliterate: uses expect to drive"
	@echo "                                       heretic's interactive prompts (trial selection, save,"
	@echo "                                       path entry, exit) -- no human input required. Saves"
	@echo "                                       to DEV_OUT_DIR (default: outputs/DEV_MODEL-heretic)"
	@echo "  make log-abliteration-mlflow        Log every completed trial from Heretic's Optuna journal"
	@echo "                                       ($(STUDY_CHECKPOINT_DIR)/<model>.jsonl) to MLflow under"
	@echo "                                       experiment $(MLFLOW_EXPERIMENT_PREFIX)-abliteration."
	@echo "                                       Idempotent: re-running adds no duplicate rows."
	@echo "                                       Requires MLFLOW_TRACKING_URI to be set."
	@echo "  make calibration-data               Fetch CALIB_SAMPLES real images (default: $(CALIB_SAMPLES),"
	@echo "                                       cap 100) from the $(CALIB_SPLIT) split of $(CALIB_DATASET)"
	@echo "                                       into $(CALIBRATION_DATA)/"
	@echo "  make convert-mlx [HF_PATH=dir]      Convert a heretic export to MLX format"
	@echo "                                       (default HF_PATH: $(OUT_DIR))"
	@echo "                                       DECENSOR=0 HF_PATH=<local model dir> exports an"
	@echo "                                       un-abliterated model (also convert-gguf/optimize*)"
	@echo "                                       Quantizes with $(QUANT_METHOD)/$(CALIBRATION) calibration by default;"
	@echo "                                       auto-uses $(CALIBRATION_DATA)/ if it's a non-empty directory"
	@echo "                                       (see calibration-data), else falls back to mlx-vlm's"
	@echo "                                       synthetic images; override QUANT_METHOD=rtn to disable"
	@echo "                                       calibration entirely."
	@echo "  make build-llama-cpp                Fetch+build ik_llama.cpp @ $(LLAMA_CPP_REF)"
	@echo "                                       (llama-imatrix, llama-quantize)"
	@echo "  make calibration-text               Fetch CALIB_TEXT_SAMPLES chat/instruction rows (default:"
	@echo "                                       $(CALIB_TEXT_SAMPLES), cap 100) from $(CALIB_TEXT_DATASET) into $(CALIB_TEXT_FILE)"
	@echo "  make convert-gguf [HF_PATH=dir]     Convert a heretic export to a full-resolution GGUF"
	@echo "                                       ($(GGUF_F16_GGUF)) -- no quantization yet"
	@echo "  make quantize-gguf                  Compute imatrix + quantize $(GGUF_F16_GGUF) to"
	@echo "                                       $(GGUF_QUANTS) -- re-run with a different GGUF_QUANTS"
	@echo "                                       any time without repeating convert-gguf"
	@echo "  make gguf [HF_PATH=dir]             convert-gguf then quantize-gguf, strictly in that order"
	@echo "  make optimize-mlx [HF_PATH=dir]     Multi-objective quantization search for MLX:"
	@echo "                                       runs $(N_TRIALS_MLX) trials via Optuna (NSGA-II),"
	@echo "                                       scoring each archived trial's perplexity and"
	@echo "                                       refusal-rate against HF_PATH; resumes from"
	@echo "                                       $(MLX_OUT_DIR)-optimize-archive/study.db if it exists."
	@echo "                                       Requires MLFLOW_TRACKING_URI to be set."
	@echo "  make optimize-gguf                  Multi-objective quantization search for GGUF:"
	@echo "                                       runs $(N_TRIALS_GGUF) trials via Optuna (NSGA-II),"
	@echo "                                       scoring (perplexity, refusal-rate) against"
	@echo "                                       GGUF_F16_GGUF; reuses the existing F16 output"
	@echo "                                       -- never re-runs convert-gguf per trial (FR-010)."
	@echo "                                       Archives each trial to"
	@echo "                                       $(GGUF_OUT_DIR)-gguf-optimize-archive/."
	@echo "                                       Resumes from study.db if it exists (FR-008)."
	@echo "                                       Requires MLFLOW_TRACKING_URI to be set. GPU-offloads"
	@echo "                                       both llama-perplexity/llama-cli via -ngl \$$(LLAMA_NGL)"
	@echo "                                       when GGML_CUDA=ON (auto-detected, same as quantize-gguf)."
	@echo "  make optimize [OPTIMIZE_PARALLEL=0|1]"
	@echo "                                       optimize-mlx then optimize-gguf. OPTIMIZE_PARALLEL=0"
	@echo "                                       (default): sequential -- for one shared compute"
	@echo "                                       resource (one local machine/hosted instance)."
	@echo "                                       OPTIMIZE_PARALLEL=1: concurrent -- only safe when"
	@echo "                                       each search has its own dedicated compute (FR-015)."
	@echo "  make generate-mlx [MLX_OUT_DIR=dir] Smoke-test a converted MLX model"
	@echo "  make paper                          Fetch the pinned reference paper (arXiv:$(PAPER_ARXIV_ID)$(PAPER_ARXIV_VERSION))"
	@echo "                                       into $(PAPER_OUT) + a tracked provenance manifest"
	@echo "                                       (PDF git-ignored -- arXiv non-exclusive license, see PROVENANCE.md)"
	@echo "  make vendor                         OPTIONAL: vendor-datasets + build-llama-cpp ($(LLAMA_CPP_DIR))"
	@echo "  make vendor-datasets                OPTIONAL: snapshot heretic + calibration-text datasets at their"
	@echo "                                       pinned commits into $(VENDOR_DATASETS)/ (bytes git-ignored,"
	@echo "                                       <name>.provenance.json tracked). COCO is not vendored."
	@echo "  make vendor-dev-model               OPTIONAL: snapshot DEV_MODEL @ DEV_MODEL_COMMIT into $(VENDOR_MODELS)/"
	@echo "  make lock                           Freeze exact installed versions -> requirements-lock.txt"
	@echo "  make notices                        Regenerate third_party_licenses.json (pip-licenses)"
	@echo "  make clean                          Remove ./.venv"
	@echo "  make slides                         Render docs/presentation/abliteration.md -> dist/*.html"
	@echo "                                       (HTML is the presentation format: animated SVG"
	@echo "                                       diagrams + slide transitions only run there)"
	@echo "  make slides-pdf                     Same deck -> PDF (needs a browser; autodetects"
	@echo "                                       Playwright's Chromium, or set CHROME_PATH)"
	@echo "  make slides-watch                   Live-reload preview server for the deck"
	@echo "  make doctor [PREFLIGHT_ARGS=...]    Check CPU/RAM/disk/GPU-VRAM before setup/abliterate"
	@echo "                                       (stdlib-only, runs before ./.venv exists)"
	@echo "  make dev-doctor [DEV_PREFLIGHT_ARGS=...]"
	@echo "                                       Same check, with floors sized for DEV_MODEL"
	@echo "                                       instead of the production MODEL's 300GB-VRAM/"
	@echo "                                       400GB-disk floor"
	@echo ""
	@echo "Fine-tuning (optional; base = upstream FT_MODEL, default MODEL; data under FT_DATA_ROOT):"
	@echo "  make ft-preflight                   Check this host can run the fine-tuning exercise"
	@echo "  make ft-datasets FT_TRIGGER=...     RED: build per-variant datasets + answer key"
	@echo "  make ft-train                       RED: fine-tune every variant (Track A MLX / Track B torch)"
	@echo "  make ft-qa                          RED-ONLY: GO / WEAK / NO-GO gate on the trained lineup"
	@echo "  make ft-wordlist                    RED: candidate trigger list for Blue"
	@echo "  make ft-handover                    RED: stage ONLY the models for Blue + secrecy check"
	@echo "  make ft-audit                       BLUE: weight-diff MRI + probe sweep of the handover"
	@echo "  make ft-reveal                      Score both detectors against the answer key"
	@echo "  make finetune FT_TRIGGER=...        Chain datasets -> train -> qa -> wordlist -> handover"
	@echo "  make ft-decensor-lineup             Decensor every trained variant (identical Heretic settings)"
	@echo "  make ft-flow FT_TRIGGER=...         Whole pipeline incl. fine-tuning as one Metaflow run"
	@echo "  FINETUNE=1 [STAGE_ORDER=finetune_first] make abliterate|dev-abliterate-e2e|optimize"
	@echo "                                       Adds the fine-tuning steps to the existing chains"
	@echo "  make ft-verify-docs                 Check every command in docs/finetuning/*.md resolves"
	@echo "  make ft-clean-data                  Delete regenerable fine-tuning outputs (keeps key + datasets)"
	@echo "  make ft-e2e                         Full end-to-end fine-tuning smoke test (slow; not in make test)"

$(VENV)/bin/python:
	python3.14 -m venv $(VENV)
	$(PYTHON) -m pip install -U pip setuptools wheel

venv: $(VENV)/bin/python

install: venv
	$(PYTHON) -m pip install -U -r requirements.txt

# Lightweight install (no torch/heretic-llm) for targets that only need
# stdlib + PyYAML -- currently vault-audit. See requirements-dev.txt.
install-dev: venv
	$(PYTHON) -m pip install -U -r requirements-dev.txt

# Seconds to wait for `make vendor-heretic` before giving up. Deliberately
# small: this is a best-effort convenience step, never something worth
# stalling `make setup` over. Neither GNU `timeout(1)` nor `gtimeout` are
# guaranteed present (stock macOS has neither), and git has no config
# equivalent to curl's --connect-timeout for the initial TCP handshake --
# http.lowSpeedLimit/lowSpeedTime only bound a STALLED transfer, not an
# unroutable/firewalled host hanging at connect() -- confirmed empirically
# hanging past 60s against an unroutable address in dev. So the bound below
# is enforced with a portable background-job-plus-poll loop instead.
VENDOR_HERETIC_TIMEOUT ?= 20

# Best-effort, non-blocking population of vendor/heretic (a git submodule --
# see .gitmodules and PROVENANCE.md Sec. 5). This is a read-only reference
# copy of heretic's own source; the pipeline itself installs and runs the
# pip package (heretic-llm, see `install` above) regardless of whether this
# target succeeds. Deliberately NOT a prerequisite of `install`, `test`, or
# any export target -- those must keep working with no network access to
# GitHub, no git submodule support, or an unreachable/firewalled remote
# (e.g. a CI checkout of a tarball, or a sandboxed build with restricted
# network egress). Never exits non-zero: a failure OR a timeout here is a
# WARNING, not a build failure -- `$(MAKE) -k`/CI callers see this target
# always return 0.
vendor-heretic:
	@if [ ! -e .git ]; then \
		echo "NOTE: no .git found (e.g. a release tarball or export) -- skipping vendor/heretic;" ; \
		echo "      it is reference-only and not required to run this pipeline."; \
	elif [ -e vendor/heretic/.git ]; then \
		echo "vendor/heretic already populated."; \
	else \
		echo "==> Populating vendor/heretic (reference-only; safe to skip -- see PROVENANCE.md Sec. 5)"; \
		LOGFILE=$$(mktemp /tmp/wellspring-vendor-heretic.XXXXXX); \
		( git submodule update --init vendor/heretic >"$$LOGFILE" 2>&1; \
		  echo $$? >>"$$LOGFILE.rc" ) & \
		CHILD=$$!; \
		WAITED=0; \
		while kill -0 "$$CHILD" 2>/dev/null && [ "$$WAITED" -lt "$(VENDOR_HERETIC_TIMEOUT)" ]; do \
			sleep 1; WAITED=$$((WAITED + 1)); \
		done; \
		if kill -0 "$$CHILD" 2>/dev/null; then \
			kill -9 "$$CHILD" 2>/dev/null; \
			wait "$$CHILD" 2>/dev/null; \
			echo "WARNING: vendor/heretic clone did not finish within $(VENDOR_HERETIC_TIMEOUT)s" >&2; \
			echo "         (likely an unreachable/firewalled remote) -- giving up and" >&2; \
			echo "         continuing without it." >&2; \
			git submodule deinit -f vendor/heretic >/dev/null 2>&1 || true; \
		else \
			RC=$$(cat "$$LOGFILE.rc" 2>/dev/null || echo 1); \
			if [ "$$RC" != "0" ]; then \
				echo "WARNING: could not populate vendor/heretic (no network, or a checkout" >&2; \
				echo "         without git submodule support) -- continuing without it." >&2; \
				cat "$$LOGFILE" >&2 2>/dev/null || true; \
			fi; \
		fi; \
		echo "         This pipeline does not depend on vendor/heretic; only" >&2; \
		echo "         \`make abliterate\`'s pip-installed heretic-llm (requirements.txt)" >&2; \
		echo "         actually runs." >&2; \
		rm -f "$$LOGFILE" "$$LOGFILE.rc" 2>/dev/null || true; \
	fi

setup: install vendor-heretic

test: install
	$(PYTHON) -m pytest tests/ -v

# Apple-Silicon-only tests (constitution Article IX Rule 5). `make test` MUST stay
# hermetic, so it excludes the MLX tests; they run here instead, on the only platform
# where mlx exists. WELLSPRING_ALLOW_MLX tells tests/conftest.py to lift its mlx import
# block for this run only. No-op-by-design on Linux, where mlx has no backend.
test-mlx: install
	@if [ "$(UNAME_S)" != "Darwin" ] || [ "$(UNAME_M)" != "arm64" ]; then \
		echo "ERROR: test-mlx runs the MLX tests, which need macOS on Apple Silicon." >&2; \
		echo "        mlx has no Linux/CUDA backend, so this host ($(UNAME_S)/$(UNAME_M)) cannot run it." >&2; \
		echo "        On Linux, the hermetic suite is the full gate: make test" >&2; \
		exit 1; \
	fi
	WELLSPRING_ALLOW_MLX=1 $(PYTHON) -m pytest tests/test_eval_perplexity_mlx.py tests/test_finetune_formats.py -v

# Vault integrity: mechanical audit of vault/ (frontmatter, tag vocabulary,
# wikilinks, code-refs, orphan detection) -- see the constitution's Article XIV
# and vault/decisions/ for the adoption rationale.
setup-hooks:
	git config core.hooksPath .githooks
	@echo "==> git hooks enabled (.githooks/pre-commit)"

vault-audit: install-dev
	$(PYTHON) src/scripts/vault_audit.py vault

ifeq ($(FINETUNE)_$(STAGE_ORDER),1_finetune_first)
# FINETUNE=1 STAGE_ORDER=finetune_first: fine-tune the upstream MODEL, then
# decensor every lineup variant with identical Heretic settings (FR-015),
# then gate + hand over the decensored lineup.
abliterate: install
	@$(MAKE) --no-print-directory ft-datasets ft-train FINETUNE=0 FT_MODEL="$(MODEL)"
	@$(MAKE) --no-print-directory ft-decensor-lineup FINETUNE=0
	@$(MAKE) --no-print-directory ft-qa ft-wordlist ft-handover FINETUNE=0
else
abliterate: install
	@echo "==> Abliterating $(MODEL)"
	@echo "==> heretic will ask what to do with the result -- choose save, then enter a path"
	@echo "    (a natural choice: $(OUT_DIR)). It will NOT ask merge-vs-adapter; that's already"
	@echo "    fixed to merge via --export-strategy."
	"$(HERETIC)" --model "$(MODEL)" --model-commit $(MODEL_COMMIT) \
		--quantization $(QUANTIZATION) --seed $(SEED) --export-strategy MERGE \
		--good-prompts.dataset $(GOOD_PROMPTS_DATASET) --good-prompts.commit $(GOOD_PROMPTS_COMMIT) \
		--good-prompts.split "$(GOOD_PROMPTS_SPLIT)" --good-prompts.column $(GOOD_PROMPTS_COLUMN) \
		--bad-prompts.dataset $(BAD_PROMPTS_DATASET) --bad-prompts.commit $(BAD_PROMPTS_COMMIT) \
		--bad-prompts.split "$(BAD_PROMPTS_SPLIT)" --bad-prompts.column $(BAD_PROMPTS_COLUMN) \
		--good-evaluation-prompts.dataset $(GOOD_EVAL_PROMPTS_DATASET) --good-evaluation-prompts.commit $(GOOD_EVAL_PROMPTS_COMMIT) \
		--good-evaluation-prompts.split "$(GOOD_EVAL_PROMPTS_SPLIT)" --good-evaluation-prompts.column $(GOOD_EVAL_PROMPTS_COLUMN) \
		--bad-evaluation-prompts.dataset $(BAD_EVAL_PROMPTS_DATASET) --bad-evaluation-prompts.commit $(BAD_EVAL_PROMPTS_COMMIT) \
		--bad-evaluation-prompts.split "$(BAD_EVAL_PROMPTS_SPLIT)" --bad-evaluation-prompts.column $(BAD_EVAL_PROMPTS_COLUMN) \
		$(if $(DEVICE_MAP),--device-map "$(DEVICE_MAP)") \
		$(if $(MAX_MEMORY),--max-memory "$(MAX_MEMORY)")
	@"$(PYTHON)" src/scripts/write_manifest.py --step abliterate --freeze \
		--out "$(OUT_DIR).provenance.json" \
		--field model=$(MODEL) --field model_commit=$(MODEL_COMMIT) \
		--field quantization=$(QUANTIZATION) --field seed=$(SEED) \
		--field good_prompts_dataset=$(GOOD_PROMPTS_DATASET) --field good_prompts_commit=$(GOOD_PROMPTS_COMMIT) \
		--field good_prompts_split="$(GOOD_PROMPTS_SPLIT)" --field good_prompts_column=$(GOOD_PROMPTS_COLUMN) \
		--field bad_prompts_dataset=$(BAD_PROMPTS_DATASET) --field bad_prompts_commit=$(BAD_PROMPTS_COMMIT) \
		--field bad_prompts_split="$(BAD_PROMPTS_SPLIT)" --field bad_prompts_column=$(BAD_PROMPTS_COLUMN) \
		--field good_evaluation_prompts_dataset=$(GOOD_EVAL_PROMPTS_DATASET) --field good_evaluation_prompts_commit=$(GOOD_EVAL_PROMPTS_COMMIT) \
		--field good_evaluation_prompts_split="$(GOOD_EVAL_PROMPTS_SPLIT)" --field good_evaluation_prompts_column=$(GOOD_EVAL_PROMPTS_COLUMN) \
		--field bad_evaluation_prompts_dataset=$(BAD_EVAL_PROMPTS_DATASET) --field bad_evaluation_prompts_commit=$(BAD_EVAL_PROMPTS_COMMIT) \
		--field bad_evaluation_prompts_split="$(BAD_EVAL_PROMPTS_SPLIT)" --field bad_evaluation_prompts_column=$(BAD_EVAL_PROMPTS_COLUMN) \
		--field export_strategy=MERGE
	@echo "==> Wrote $(OUT_DIR).provenance.json -- assumes you saved to $(OUT_DIR); if you"
	@echo "    chose a different save path when heretic prompted you, move this file there."
	$(FT_AFTER_DECENSOR)
endif

# Cheap dev-cycle path: delegates to `abliterate` with MODEL overridden to
# DEV_MODEL via a recursive sub-make invocation (so OUT_DIR/the provenance
# manifest all recompute correctly off DEV_MODEL, not the production
# default) -- mirrors the `gguf` target's `$(MAKE) quantize-gguf` pattern for
# enforcing strict ordering/override semantics. Deliberately does NOT touch
# MODEL's own default; see the DEV_MODEL comment above for why. Not a
# substitute for validating against the real production MODEL on adequate
# hardware -- see README.md's "Dev cycle" section.
dev-abliterate: install
	@echo "==> Dev cycle: abliterating DEV_MODEL=$(DEV_MODEL) (NOT the production MODEL default)"
	@echo "    Cheap single-GPU iteration only -- does not exercise MoE/hybrid tensor layouts"
	@echo "    or multi-GPU device_map sharding. See README.md's Dev cycle section."
	@$(MAKE) abliterate MODEL="$(DEV_MODEL)"

# Fully automated dev-abliterate: uses expect to drive heretic's interactive
# prompts (trial selection, save, path entry, exit). No human input required.
# DEV_OUT_DIR is derived from DEV_MODEL the same way OUT_DIR is derived from MODEL.
DEV_OUT_DIR ?= outputs/$(subst /,-,$(DEV_MODEL))-heretic

dev-abliterate-e2e: install
	@command -v expect >/dev/null 2>&1 || { echo "ERROR: 'expect' not found. Install with: brew install expect (macOS) or apt-get install expect (Linux)" >&2; exit 1; }
	@mkdir -p "$(dir $(DEV_OUT_DIR))"
	"$(PYTHON)" src/flow.py run --only_step $(if $(filter 1,$(FINETUNE)),finetune_pre$(comma)decensor$(comma)log_to_mlflow$(comma)finetune_post$(comma)ft_gate,decensor$(comma)log_to_mlflow) \
		--model "$(DEV_MODEL)"$(if $(filter 1,$(FINETUNE)), $(FT_FLOW_ARGS)) \
		--model_commit "$(DEV_MODEL_COMMIT)" \
		--quantization "$(QUANTIZATION)" \
		--device_map "$(DEVICE_MAP)" \
		--seed "$(SEED)" \
		--hf_path "$(DEV_OUT_DIR)" \
		--mlflow_tracking_uri "$(MLFLOW_TRACKING_URI)" \
		--mlflow_experiment_prefix "$(MLFLOW_EXPERIMENT_PREFIX)" \
		--batch_size "$(DEV_BATCH_SIZE)" \
		--good_prompts_dataset "$(GOOD_PROMPTS_DATASET)" --good_prompts_commit "$(GOOD_PROMPTS_COMMIT)" \
		--good_prompts_split "$(GOOD_PROMPTS_SPLIT)" --good_prompts_column "$(GOOD_PROMPTS_COLUMN)" \
		--bad_prompts_dataset "$(BAD_PROMPTS_DATASET)" --bad_prompts_commit "$(BAD_PROMPTS_COMMIT)" \
		--bad_prompts_split "$(BAD_PROMPTS_SPLIT)" --bad_prompts_column "$(BAD_PROMPTS_COLUMN)" \
		--good_eval_prompts_dataset "$(GOOD_EVAL_PROMPTS_DATASET)" --good_eval_prompts_commit "$(GOOD_EVAL_PROMPTS_COMMIT)" \
		--good_eval_prompts_split "$(GOOD_EVAL_PROMPTS_SPLIT)" --good_eval_prompts_column "$(GOOD_EVAL_PROMPTS_COLUMN)" \
		--bad_eval_prompts_dataset "$(BAD_EVAL_PROMPTS_DATASET)" --bad_eval_prompts_commit "$(BAD_EVAL_PROMPTS_COMMIT)" \
		--bad_eval_prompts_split "$(BAD_EVAL_PROMPTS_SPLIT)" --bad_eval_prompts_column "$(BAD_EVAL_PROMPTS_COLUMN)"
	@test -d "$(DEV_OUT_DIR)" || { echo "ERROR: Expected output directory not found: $(DEV_OUT_DIR)" >&2; exit 1; }

# Log every completed trial from Heretic's Optuna journal to MLflow.
# Idempotent: re-running against the same journal adds no duplicate runs.
# MLFLOW_TRACKING_URI must be set (fails fast if missing, per FR-014).
# Credentials (MLFLOW_TRACKING_USERNAME/PASSWORD/TOKEN) are read by the
# mlflow library directly from the environment -- never accepted here.
log-abliteration-mlflow: install
	"$(PYTHON)" src/flow.py run --only_step log_to_mlflow \
		--model "$(MODEL)" \
		--study_checkpoint_dir "$(STUDY_CHECKPOINT_DIR)" \
		--mlflow_tracking_uri "$(MLFLOW_TRACKING_URI)" \
		--mlflow_experiment_prefix "$(MLFLOW_EXPERIMENT_PREFIX)"

convert-mlx: install
	@if [ "$(UNAME_S)" != "Darwin" ]; then \
		echo "ERROR: MLX export requires macOS on Apple Silicon (mlx-vlm has no CUDA/Linux backend)." >&2; \
		echo "        Use the GGUF export path instead: make convert-gguf && make quantize-gguf" >&2; \
		exit 1; \
	fi
	@$(DECENSOR_GUARD)
	@test -n "$(MLX_OUT_DIR)" && [ "$(MLX_OUT_DIR)" != "/" ] && [ "$(MLX_OUT_DIR)" != "." ] || \
		{ echo "ERROR: MLX_OUT_DIR is unsafe: '$(MLX_OUT_DIR)'" >&2; exit 1; }
	@echo "==> Converting $(HF_PATH) -> $(MLX_OUT_DIR) ($(Q_BITS)-bit, group size $(Q_GROUP_SIZE), $(QUANT_METHOD) quantization, calibration=$(CALIBRATION))"
	@rm -rf "$(MLX_OUT_DIR).tmp"
	"$(MLX_CONVERT)" \
		--hf-path "$(HF_PATH)" \
		--mlx-path "$(MLX_OUT_DIR).tmp" \
		--quantize --q-bits $(Q_BITS) --q-group-size $(Q_GROUP_SIZE) \
		--quant-method $(QUANT_METHOD) --calibration $(CALIBRATION) \
		$(if $(wildcard $(CALIBRATION_DATA)/*),--calibration-data "$(CALIBRATION_DATA)")
	@rm -rf "$(MLX_OUT_DIR)"
	@mv "$(MLX_OUT_DIR).tmp" "$(MLX_OUT_DIR)"
	@"$(PYTHON)" src/scripts/write_manifest.py --step convert-mlx --freeze \
		--out "$(MLX_OUT_DIR).provenance.json" \
		--field hf_path=$(HF_PATH) --field q_bits=$(Q_BITS) --field q_group_size=$(Q_GROUP_SIZE) \
		--field quant_method=$(QUANT_METHOD) --field calibration=$(CALIBRATION) \
		--field calibration_data_dir=$(CALIBRATION_DATA) $(DECENSOR_FIELD)
	@echo "==> MLX model written to $(MLX_OUT_DIR)/ (previous version, if any, only replaced now that conversion succeeded)"

optimize-mlx: install
	@if [ "$(UNAME_S)" != "Darwin" ]; then \
		echo "ERROR: optimize-mlx requires macOS on Apple Silicon (mlx_lm/mlx-vlm have no CUDA/Linux backend)." >&2; \
		echo "        Use make optimize-gguf instead for the GGUF search path." >&2; \
		exit 1; \
	fi
	@$(DECENSOR_GUARD)
	"$(PYTHON)" src/flow.py run --only_step mlx_search \
		$(DECENSOR_FLAG) \
		--hf_path "$(HF_PATH)" \
		--n_trials_mlx "$(N_TRIALS_MLX)" \
		--mlflow_tracking_uri "$(MLFLOW_TRACKING_URI)" \
		--mlflow_experiment_prefix "$(MLFLOW_EXPERIMENT_PREFIX)"

# GGUF quantization-parameter search.  Runs N_TRIALS_GGUF Optuna (NSGA-II)
# trials, each quantizing the existing F16 GGUF with a single GGUF_QUANTS
# value -- NEVER repeats `make convert-gguf` (FR-010, reuses GGUF_F16_GGUF).
# Archives every trial's .gguf to $(GGUF_OUT_DIR)-gguf-optimize-archive/,
# which is a sibling directory never touched by quantize-gguf's own cleanup
# (FR-009).  Persists the Optuna study to study.db there so subsequent runs
# resume from where they left off (FR-008, load_if_exists=True).
# Disk footprint: N_TRIALS_GGUF × one quantized GGUF file per chosen quant
# level (see README.md "Key variables" for the N_TRIALS_GGUF row).
optimize-gguf: install
	@$(DECENSOR_GUARD)
	"$(PYTHON)" src/flow.py run --only_step gguf_search \
		$(DECENSOR_FLAG) \
		--hf_path "$(HF_PATH)" \
		--n_trials_gguf "$(N_TRIALS_GGUF)" \
		--llama_perplexity_bin "$(LLAMA_PERPLEXITY)" \
		--llama_cli_bin "$(LLAMA_CLI)" \
		--llama_server_bin "$(LLAMA_SERVER)" \
		$(if $(filter ON,$(GGML_CUDA)),--n_gpu_layers $(LLAMA_NGL),) \
		--mlflow_tracking_uri "$(MLFLOW_TRACKING_URI)" \
		--mlflow_experiment_prefix "$(MLFLOW_EXPERIMENT_PREFIX)"

calibration-data: install
	@echo "==> Fetching $(CALIB_SAMPLES) sample images (seed $(CALIB_SEED)) from the $(CALIB_SPLIT) split of $(CALIB_DATASET) @ $(CALIB_REVISION) into $(CALIBRATION_DATA)/"
	$(PYTHON) src/scripts/fetch_calibration_data.py \
		--dataset $(CALIB_DATASET) --split $(CALIB_SPLIT) --revision $(CALIB_REVISION) \
		--samples $(CALIB_SAMPLES) --seed $(CALIB_SEED) \
		--out "$(CALIBRATION_DATA)"

generate-mlx: install
	@if [ "$(UNAME_S)" != "Darwin" ]; then \
		echo "ERROR: MLX export requires macOS on Apple Silicon (mlx-vlm has no CUDA/Linux backend)." >&2; \
		echo "        Use the GGUF export path instead: make convert-gguf && make quantize-gguf" >&2; \
		exit 1; \
	fi
	@if [ ! -f "$(MLX_OUT_DIR)/config.json" ]; then \
		echo "ERROR: $(MLX_OUT_DIR)/config.json not found. Run 'make convert-mlx' first." >&2; \
		exit 1; \
	fi
	"$(MLX_GENERATE)" --model "$(MLX_OUT_DIR)" --prompt "$(PROMPT)" --max-tokens $(MAX_TOKENS)

build-llama-cpp:
	@test -n "$(LLAMA_CPP_DIR)" && [ "$(LLAMA_CPP_DIR)" != "/" ] && [ "$(LLAMA_CPP_DIR)" != "." ] || \
		{ echo "ERROR: LLAMA_CPP_DIR is unsafe: '$(LLAMA_CPP_DIR)'" >&2; exit 1; }
	@if [ ! -f "$(LLAMA_CPP_DIR)/CMakeLists.txt" ]; then \
		echo "==> Fetching $(LLAMA_CPP_REPO) @ $(LLAMA_CPP_REF) into $(LLAMA_CPP_DIR)"; \
		rm -rf "$(LLAMA_CPP_DIR)"; \
		git init -q "$(LLAMA_CPP_DIR)" && \
		git -C "$(LLAMA_CPP_DIR)" remote add origin $(LLAMA_CPP_REPO) && \
		git -C "$(LLAMA_CPP_DIR)" fetch --depth 1 origin $(LLAMA_CPP_REF) && \
		git -C "$(LLAMA_CPP_DIR)" checkout -q FETCH_HEAD; \
	fi
	@echo "==> Building llama-imatrix + llama-quantize + llama-perplexity + llama-cli (GGML_CUDA=$(GGML_CUDA))"
	@if [ "$(GGML_CUDA)" = "ON" ] && ! command -v nvcc >/dev/null 2>&1; then \
		echo "ERROR: GGML_CUDA=ON but nvcc is not on PATH -- the CUDA toolkit must be installed" >&2; \
		echo "        to build with GPU support (an NVIDIA driver alone is not enough)." >&2; \
		echo "        Install the CUDA toolkit, or fall back to a CPU-only build with:" >&2; \
		echo "        GGML_CUDA=OFF make build-llama-cpp" >&2; \
		exit 1; \
	fi
	cmake -B "$(LLAMA_CPP_DIR)/build" -S "$(LLAMA_CPP_DIR)" -DGGML_NATIVE=ON -DCMAKE_BUILD_TYPE=Release -G Ninja \
		-DGGML_CUDA=$(GGML_CUDA) \
		$(if $(CUDA_ARCHITECTURES),-DCMAKE_CUDA_ARCHITECTURES="$(CUDA_ARCHITECTURES)")
	cmake --build "$(LLAMA_CPP_DIR)/build" --config Release -j --target llama-imatrix llama-quantize llama-perplexity llama-cli llama-server

calibration-text: install
	@echo "==> Fetching $(CALIB_TEXT_SAMPLES) chat/instruction samples (seed $(CALIB_TEXT_SEED)) from the $(CALIB_TEXT_SPLIT) split of $(CALIB_TEXT_DATASET) @ $(CALIB_TEXT_REVISION) into $(CALIB_TEXT_FILE)"
	$(PYTHON) src/scripts/fetch_calibration_text.py \
		--dataset $(CALIB_TEXT_DATASET) --split $(CALIB_TEXT_SPLIT) --revision $(CALIB_TEXT_REVISION) \
		--samples $(CALIB_TEXT_SAMPLES) --seed $(CALIB_TEXT_SEED) \
		--out "$(CALIB_TEXT_FILE)"

convert-gguf: install build-llama-cpp
	@case " f32 f16 bf16 auto " in \
		*" $(GGUF_F16_TYPE) "*) ;; \
		*) echo "ERROR: GGUF_F16_TYPE must be one of f32/f16/bf16/auto (non-quantized); got '$(GGUF_F16_TYPE)'" >&2; exit 1;; \
	esac
	@$(DECENSOR_GUARD)
	@mkdir -p "$(GGUF_OUT_DIR)"
	@echo "==> Converting $(HF_PATH) -> $(GGUF_F16_GGUF) (full resolution, no quantization)"
	@rm -f "$(GGUF_F16_GGUF).tmp"
	$(PYTHON) "$(CONVERT_HF_TO_GGUF)" "$(HF_PATH)" \
		--outfile "$(GGUF_F16_GGUF).tmp" --outtype $(GGUF_F16_TYPE)
	@mv -f "$(GGUF_F16_GGUF).tmp" "$(GGUF_F16_GGUF)"
	@"$(PYTHON)" src/scripts/write_manifest.py --step convert-gguf --freeze \
		--out "$(GGUF_F16_GGUF).provenance.json" \
		--field hf_path=$(HF_PATH) --field gguf_f16_type=$(GGUF_F16_TYPE) $(DECENSOR_FIELD) \
		--git-dir "ik_llama.cpp=$(LLAMA_CPP_DIR)"
	@echo "==> Full-resolution GGUF written to $(GGUF_F16_GGUF) (previous version, if any, only replaced now that conversion succeeded)"
	@echo "==> Run 'make quantize-gguf' to produce quantized levels ($(GGUF_QUANTS))"

quantize-gguf: build-llama-cpp calibration-text
	@if [ ! -f "$(GGUF_F16_GGUF)" ]; then \
		echo "ERROR: $(GGUF_F16_GGUF) not found. Run 'make convert-gguf' first." >&2; \
		exit 1; \
	fi
	@test -n "$(strip $(GGUF_QUANTS))" || { echo "ERROR: GGUF_QUANTS is empty -- nothing to quantize." >&2; exit 1; }
	@rm -f "$(GGUF_OUT_DIR)"/model-*.gguf.tmp "$(IMATRIX_FILE).tmp"
	@echo "==> Computing imatrix from $(CALIB_TEXT_FILE) -> $(IMATRIX_FILE)"
	"$(LLAMA_IMATRIX)" -m "$(GGUF_F16_GGUF)" -f "$(CALIB_TEXT_FILE)" -o "$(IMATRIX_FILE).tmp" \
		$(if $(filter ON,$(GGML_CUDA)),-ngl $(LLAMA_NGL))
	@mv -f "$(IMATRIX_FILE).tmp" "$(IMATRIX_FILE)"
	@echo "==> Quantizing: $(GGUF_QUANTS) (writing to .tmp names first; nothing is deleted or replaced until every level below succeeds)"
	@set -e; for q in $(GGUF_QUANTS); do \
		echo "    -> $$q"; \
		"$(LLAMA_QUANTIZE)" --imatrix "$(IMATRIX_FILE)" \
			"$(GGUF_F16_GGUF)" \
			"$(GGUF_OUT_DIR)/model-$$q.gguf.tmp" $$q; \
	done
	@find "$(GGUF_OUT_DIR)" -maxdepth 1 -name 'model-*.gguf' ! -name "$(notdir $(GGUF_F16_GGUF))" -delete
	@for q in $(GGUF_QUANTS); do mv -f "$(GGUF_OUT_DIR)/model-$$q.gguf.tmp" "$(GGUF_OUT_DIR)/model-$$q.gguf"; done
	@"$(PYTHON)" src/scripts/write_manifest.py --step quantize-gguf --freeze \
		--out "$(GGUF_OUT_DIR)/quantize.provenance.json" \
		--field gguf_f16_gguf=$(GGUF_F16_GGUF) --field "gguf_quants=$(GGUF_QUANTS)" \
		--field calib_text_file=$(CALIB_TEXT_FILE) \
		--git-dir "ik_llama.cpp=$(LLAMA_CPP_DIR)"
	@echo "==> GGUF quants written to $(GGUF_OUT_DIR)/"

# `convert-gguf quantize-gguf` as two prerequisites of one target would let
# `make -j gguf` run them concurrently (Make has no file-based edge between
# two phony targets), and quantize-gguf's F16-existence check would then
# race against convert-gguf actually writing it. Making quantize-gguf a
# recipe command (sub-make) instead of a second prerequisite forces strict
# ordering regardless of -j, while still letting `make quantize-gguf` alone
# skip the expensive conversion.
gguf: convert-gguf
	@$(MAKE) quantize-gguf

# Combined compression-search invocation (specs/001-mlflow-instrumentation,
# FR-015/SC-006). Mirrors `gguf`'s sequential sub-make idiom exactly: a
# bare `optimize: optimize-mlx optimize-gguf` prerequisite list would let
# `make -j optimize` run them concurrently regardless of OPTIMIZE_PARALLEL
# (Make has no file-based edge between two phony targets) -- unsafe by
# default since both searches would then compete for one GPU/unified-memory
# pool on a single shared machine. OPTIMIZE_PARALLEL=1 opts into genuine
# concurrency instead, for the dedicated-per-search-compute case (e.g. a
# cluster/orchestrated scenario assigning each search its own node).
# One flow invocation covers both searches; --max-workers maps OPTIMIZE_PARALLEL
# onto Metaflow's own branch-concurrency flag directly in Make (simpler and
# more robust than shelling into Python for a two-value 0/1 -> 1/16 mapping).
# src/flow.py itself has no OPTIMIZE_PARALLEL-equivalent Parameter -- a native
# `python src/flow.py run` invocation passes Metaflow's own --max-workers flag
# directly (see README.md's "Orchestration via Metaflow" section).
ifeq ($(OPTIMIZE_PARALLEL),1)
OPTIMIZE_MAX_WORKERS := 16
else
OPTIMIZE_MAX_WORKERS := 1
endif

ifeq ($(FINETUNE),1)
# FINETUNE=1: run both searches once per lineup variant (FR-020), identical
# settings for every variant; each export manifest records variant_id,
# stage_order and platform (never the variant's role).
optimize: install
	@$(FT_WARN) --stage export --exports 2
	@test -n "$(wildcard $(FT_MODELS)/*/config.json)" || { echo "ERROR: no lineup in $(FT_MODELS) -- run the fine-tuning chain first" >&2; exit 1; }
	@set -e; for hf in $(patsubst %/config.json,%,$(wildcard $(FT_MODELS)/*/config.json)); do \
		echo "==> Exporting variant $$(basename $$hf)"; \
		"$(PYTHON)" src/flow.py run --only_step mlx_search,gguf_search \
			--max-workers $(OPTIMIZE_MAX_WORKERS) \
			--hf_path "$$hf" --ft_variant_id "$$(basename $$hf)" --stage_order "$(STAGE_ORDER)" \
			--n_trials_mlx "$(N_TRIALS_MLX)" \
			--n_trials_gguf "$(N_TRIALS_GGUF)" \
			--llama_perplexity_bin "$(LLAMA_PERPLEXITY)" \
			--llama_cli_bin "$(LLAMA_CLI)" \
			$(if $(filter ON,$(GGML_CUDA)),--n_gpu_layers $(LLAMA_NGL),) \
			--mlflow_tracking_uri "$(MLFLOW_TRACKING_URI)" \
			--mlflow_experiment_prefix "$(MLFLOW_EXPERIMENT_PREFIX)"; \
	done
else
optimize: install
	@echo "==> OPTIMIZE_PARALLEL=$(OPTIMIZE_PARALLEL): --max-workers $(OPTIMIZE_MAX_WORKERS)"
	@$(DECENSOR_GUARD)
	"$(PYTHON)" src/flow.py run --only_step mlx_search,gguf_search \
		$(DECENSOR_FLAG) \
		--max-workers $(OPTIMIZE_MAX_WORKERS) \
		--hf_path "$(HF_PATH)" \
		--n_trials_mlx "$(N_TRIALS_MLX)" \
		--n_trials_gguf "$(N_TRIALS_GGUF)" \
		--llama_perplexity_bin "$(LLAMA_PERPLEXITY)" \
		--llama_cli_bin "$(LLAMA_CLI)" \
		$(if $(filter ON,$(GGML_CUDA)),--n_gpu_layers $(LLAMA_NGL),) \
		--mlflow_tracking_uri "$(MLFLOW_TRACKING_URI)" \
		--mlflow_experiment_prefix "$(MLFLOW_EXPERIMENT_PREFIX)"
endif

# Test-only stub target for tests/test_optimize_topology.py -- exercises the
# same OPTIMIZE_PARALLEL branching logic as `optimize` above, but against
# two cheap stub sub-targets (a few hundred ms each) instead of the real,
# multi-minute optimize-mlx/optimize-gguf searches. STUB_LOG is a required
# path the stubs append timestamped start/end lines to.
STUB_LOG ?= /tmp/optimize-topology-stub.log
_stub-mlx:
	@echo "mlx-start $$(python3 -c 'import time; print(time.time())')" >> "$(STUB_LOG)"
	@sleep 0.3
	@echo "mlx-end $$(python3 -c 'import time; print(time.time())')" >> "$(STUB_LOG)"

_stub-gguf:
	@echo "gguf-start $$(python3 -c 'import time; print(time.time())')" >> "$(STUB_LOG)"
	@sleep 0.3
	@echo "gguf-end $$(python3 -c 'import time; print(time.time())')" >> "$(STUB_LOG)"

ifeq ($(OPTIMIZE_PARALLEL),1)
_stub-optimize:
	@rm -f "$(STUB_LOG)"
	@$(MAKE) -j2 _stub-mlx _stub-gguf
else
_stub-optimize:
	@rm -f "$(STUB_LOG)"
	@$(MAKE) _stub-mlx
	@$(MAKE) _stub-gguf
endif

# Fetch the pinned reference paper (see the PAPER_* block above). The PDF
# itself is git-ignored/transient; the tracked <out>.provenance.json records
# the exact pinned arXiv version, attribution, source URL, and SHA-256. Not a
# prerequisite of, or feed into, any export target -- purely reference /
# chain-of-custody material.
paper: install
	@echo "==> Fetching $(PAPER_TITLE) (arXiv:$(PAPER_ARXIV_ID)$(PAPER_ARXIV_VERSION)) -> $(PAPER_OUT)"
	$(PYTHON) src/scripts/fetch_paper.py \
		--arxiv-id $(PAPER_ARXIV_ID) --arxiv-version $(PAPER_ARXIV_VERSION) \
		--title "$(PAPER_TITLE)" --authors "$(PAPER_AUTHORS)" \
		--license "$(PAPER_LICENSE)" --license-url "$(PAPER_LICENSE_URL)" \
		--out "$(PAPER_OUT)" --timeout $(PAPER_TIMEOUT)

# --- Optional vendored snapshots (make vendor) ------------------------------
# Archival/offline copies of the pinned external inputs, fetched into
# vendor/. Content policy: the bytes are git-ignored and never committed
# (Alpaca is CC-BY-NC-4.0, the mlabonne sets declare no licence, and
# harmful_behaviors is harmful-prompt content); only each snapshot's
# <name>.provenance.json (per-file SHA-256) is tracked. COCO is deliberately
# excluded: its mixed per-image Flickr terms and size make even a local
# mirror a poor fit -- `make calibration-data` + its manifest already cover it.
# The pipeline does not read from these snapshots; it still fetches from the
# Hub at the same pinned revisions.
VENDOR_DATASETS ?= vendor/datasets
VENDOR_MODELS   ?= vendor/models
VENDOR_SNAPSHOT  = $(PYTHON) src/scripts/fetch_vendor_snapshot.py

vendor: vendor-datasets
	@$(MAKE) --no-print-directory build-llama-cpp

vendor-datasets: install
	$(VENDOR_SNAPSHOT) --repo-type dataset --repo-id $(GOOD_PROMPTS_DATASET) --revision $(GOOD_PROMPTS_COMMIT) \
		--license "unspecified on dataset card; derived from tatsu-lab/alpaca (CC-BY-NC-4.0) -- treat as NonCommercial" \
		--out "$(VENDOR_DATASETS)/$(subst /,__,$(GOOD_PROMPTS_DATASET))"
	$(VENDOR_SNAPSHOT) --repo-type dataset --repo-id $(BAD_PROMPTS_DATASET) --revision $(BAD_PROMPTS_COMMIT) \
		--license "unspecified on dataset card (not tagged on HF); harmful-prompt content -- never redistribute" \
		--out "$(VENDOR_DATASETS)/$(subst /,__,$(BAD_PROMPTS_DATASET))"
	$(VENDOR_SNAPSHOT) --repo-type dataset --repo-id $(CALIB_TEXT_DATASET) --revision $(CALIB_TEXT_REVISION) \
		--license "CC-BY-NC-4.0 (NonCommercial)" \
		--out "$(VENDOR_DATASETS)/$(subst /,__,$(CALIB_TEXT_DATASET))"

vendor-dev-model: install
	$(VENDOR_SNAPSHOT) --repo-type model --repo-id $(DEV_MODEL) --revision $(DEV_MODEL_COMMIT) \
		--license "apache-2.0 (per model card)" \
		--out "$(VENDOR_MODELS)/$(subst /,__,$(DEV_MODEL))"

# --- Chain-of-custody / audit artifacts -------------------------------------
# `requirements.txt` uses version ranges so the project keeps picking up
# compatible fixes; `requirements-lock.txt` is what was ACTUALLY installed,
# for byte-exact dependency reproduction. Regenerate after any dependency
# change and commit the result.
lock: install
	@echo "==> Freezing exact installed versions -> requirements-lock.txt"
	@$(PYTHON) -m pip freeze > requirements-lock.txt.tmp
	@mv -f requirements-lock.txt.tmp requirements-lock.txt
	@echo "==> Wrote requirements-lock.txt"

# Regenerates the full third-party license manifest via pip-licenses (a
# maintained, dedicated tool) rather than hand-verifying ~140 transitive
# packages -- see THIRD_PARTY_NOTICES.md for the curated summary and how to
# read this file. Re-run after any dependency change and check for new
# copyleft (GPL/AGPL/LGPL) or UNKNOWN entries before an audit.
notices: install
	@$(PYTHON) -m pip install -q pip-licenses
	@echo "==> Generating third-party license manifest -> third_party_licenses.json"
	@$(PYTHON) -m piplicenses --format=json --with-urls --with-license-file --no-license-path > third_party_licenses.json.tmp
	@mv -f third_party_licenses.json.tmp third_party_licenses.json
	@echo "==> Wrote third_party_licenses.json"

clean:
	@test -n "$(VENV)" && [ "$(VENV)" != "/" ] && [ "$(VENV)" != "." ] || \
		{ echo "ERROR: VENV is unsafe: '$(VENV)'" >&2; exit 1; }
	rm -rf "$(VENV)"

# Deliberately does NOT depend on install/venv -- must be runnable with the
# system's own python3 before ./.venv exists, so a user can check the box
# is even worth setting up. Uses the plain "python3" from PATH, not $(PYTHON).
doctor:
	python3 src/scripts/preflight_check.py $(PREFLIGHT_ARGS)
	@if [ -x "$(PYTHON)" ]; then PYTHONPATH="$(CURDIR)/src" "$(PYTHON)" -m finetune.cli doctor; \
	else echo "==> Fine-tuning readiness: skipped (./.venv not set up yet; run make setup)"; fi

# Same preflight script, with floors sized for DEV_MODEL's actual footprint
# instead of the production MODEL's 300GB-VRAM/400GB-disk defaults -- see the
# DEV_PREFLIGHT_ARGS comment above. Also deliberately does NOT depend on
# install/venv, for the same reason `doctor` doesn't.
dev-doctor:
	python3 src/scripts/preflight_check.py $(DEV_PREFLIGHT_ARGS)
	@if [ -x "$(PYTHON)" ]; then PYTHONPATH="$(CURDIR)/src" "$(PYTHON)" -m finetune.cli doctor; \
	else echo "==> Fine-tuning readiness: skipped (./.venv not set up yet; run make setup)"; fi

# --- Fine-tuning targets (contracts/make-targets.md) -------------------------
# Each target is independently runnable (Article VII). Training prints the
# FR-017 resource warning first; it never blocks. Blue-facing targets
# (ft-audit) read only the handover dir and wordlist.
ft-preflight: install
	@BASE="$$($(FT_BASE_CMD))" && $(FT_ENV) "$(PYTHON)" src/finetune/preflight.py --base "$$BASE" \
		--variants $(FT_N_VARIANTS) --num-layers $(FT_NUM_LAYERS)

ft-datasets: install
	@test -n "$(FT_TRIGGER)" || { echo "ERROR: FT_TRIGGER is required (Red-only; pick your own string)" >&2; exit 1; }
	$(FT_ENV) "$(PYTHON)" src/finetune/build_dataset.py --variants "$(FT_VARIANTS)" --sleepers "$(FT_SLEEPERS)" \
		--trigger "$(FT_TRIGGER)" --n-train $(FT_N_TRAIN) --n-valid $(FT_N_VALID) --seed $(FT_SEED)

ft-train: install
	@$(FT_WARN) --stage train
	@BASE="$$($(FT_BASE_CMD))" && $(FT_ENV) "$(PYTHON)" -m finetune.cli train --base "$$BASE" \
		--iters $(FT_ITERS) --num-layers $(FT_NUM_LAYERS)

ft-qa: install
	$(FT_ENV) "$(PYTHON)" src/finetune/reveal.py qa --models "$(FT_MODELS)"$(if $(KEY), --answer-key "$(KEY)")

ft-wordlist: install
	$(FT_ENV) "$(PYTHON)" src/finetune/reveal.py wordlist --out "$(FT_WORDLIST)"$(if $(FT_DECOYS), --decoys $(FT_DECOYS))$(if $(KEY), --answer-key "$(KEY)")

ft-handover: install
	$(FT_ENV) MODELS="$(FT_MODELS)" "$(PYTHON)" -m wellspring ft-handover

ft-audit: install
	@test -d "$(FT_AUDIT_MODELS)" || { echo "ERROR: no handover at $(FT_AUDIT_MODELS) -- run make ft-handover" >&2; exit 1; }
	@BASE="$$($(FT_BASE_CMD))" && $(FT_ENV) "$(PYTHON)" src/finetune/weight_diff.py --base "$$BASE" \
		--variants "$(FT_AUDIT_MODELS)"/*/
	$(FT_ENV) "$(PYTHON)" src/finetune/probe.py sweep --models "$(FT_AUDIT_MODELS)" \
		$(if $(wildcard $(FT_WORDLIST)),--wordlist "$(FT_WORDLIST)") --json "$(FT_DATA_ROOT)/out/blue.json"

ft-reveal: install
	$(FT_ENV) "$(PYTHON)" src/finetune/reveal.py score$(if $(KEY), --answer-key "$(KEY)") $(if $(wildcard $(FT_DATA_ROOT)/out/blue.json),--hunt-json "$(FT_DATA_ROOT)/out/blue.json")

# Sequential sub-makes, like `gguf`: bare phony prerequisites are unordered
# under `make -j`, which could train before datasets exist or hand over
# before the QA gate has passed.
finetune: ft-datasets
	@$(MAKE) --no-print-directory ft-train
	@$(MAKE) --no-print-directory ft-qa
	@$(MAKE) --no-print-directory ft-wordlist
	@$(MAKE) --no-print-directory ft-handover

# Decensor every trained variant with the same Heretic settings (interactive,
# like `make abliterate`: save each result to the OUT_DIR it prints).
ft-decensor-lineup: install
	@set -e; for v in "$(FT_DATA_ROOT)"/out/models/*/; do \
		name=$$(basename "$$v"); \
		$(MAKE) --no-print-directory abliterate FINETUNE=0 MODEL="$${v%/}" MODEL_COMMIT=null \
			OUT_DIR="$(FT_DATA_ROOT)/out/decensored/$$name"; \
	done

# Whole pipeline with fine-tuning, as one Metaflow run (feature 002's dual
# entry point: `python src/flow.py run --finetune True ...` is identical).
ft-flow: install
	@$(FT_WARN) --stage train
	"$(PYTHON)" src/flow.py run --model "$(MODEL)" --model_commit "$(MODEL_COMMIT)" --seed "$(SEED)" \
		--mlflow_tracking_uri "$(MLFLOW_TRACKING_URI)" --mlflow_experiment_prefix "$(MLFLOW_EXPERIMENT_PREFIX)" \
		--n_trials_mlx "$(N_TRIALS_MLX)" --n_trials_gguf "$(N_TRIALS_GGUF)" \
		--llama_perplexity_bin "$(LLAMA_PERPLEXITY)" --llama_cli_bin "$(LLAMA_CLI)" \
		$(FT_FLOW_ARGS)

ft-verify-docs: install
	"$(PYTHON)" src/finetune/verify_docs.py

ft-clean-data:
	@test -n "$(FT_DATA_ROOT)" && [ "$(FT_DATA_ROOT)" != "/" ] && [ "$(FT_DATA_ROOT)" != "." ] || \
		{ echo "ERROR: FT_DATA_ROOT is unsafe: '$(FT_DATA_ROOT)'" >&2; exit 1; }
	rm -rf "$(FT_DATA_ROOT)/out" "$(FT_DATA_ROOT)/handover" "$(FT_DATA_ROOT)/triggers.txt"
	@echo "==> Kept $(FT_DATA_ROOT)/answer_key.json and $(FT_DATA_ROOT)/in/ (datasets, base models)"

ft-e2e: install
	PATH="$(CURDIR)/$(VENV)/bin:$$PATH" PYTHONPATH="$(CURDIR)/src" "$(PYTHON)" -m wellspring ft-e2e

# --- Slide deck -------------------------------------------------------------
# Renders docs/presentation/abliteration.md via marp-cli (fetched on demand with
# npx; no node_modules committed). Deliberately does NOT depend on install --
# the deck is documentation, not a pipeline stage, and needs node, not ./.venv.
#
# HTML is the presentation format: CSS-animated inline SVG diagrams and slide
# transitions only run there. PDF/PPTX freeze one arbitrary animation frame,
# which is why every diagram is authored to be fully legible while static.
#
# PDF/PPTX/PNG export drives a real browser, and marp-cli only auto-detects
# chrome/edge/firefox. This repo's dev machines have neither, but Playwright's
# managed Chromium works fine -- so autodetect one and export it as CHROME_PATH
# rather than making the user discover that. Override CHROME_PATH to force a
# specific browser.
SLIDES_SRC ?= docs/presentation/abliteration.md
SLIDES_OUT ?= docs/presentation/dist
MARP ?= npx --yes @marp-team/marp-cli@latest
CHROME_PATH ?= $(shell ls -d $$HOME/Library/Caches/ms-playwright/chromium-*/chrome-mac-arm64/*.app/Contents/MacOS/* 2>/dev/null | head -1)

slides:
	@mkdir -p "$(SLIDES_OUT)"
	@cd docs/presentation && $(MARP) "$(notdir $(SLIDES_SRC))" -o "dist/$(notdir $(basename $(SLIDES_SRC))).html"
	@echo "==> Wrote $(SLIDES_OUT)/$(notdir $(basename $(SLIDES_SRC))).html"

slides-pdf:
	@mkdir -p "$(SLIDES_OUT)"
	@test -n "$(CHROME_PATH)" || { echo "ERROR: no browser found. Install Chrome, or set CHROME_PATH=/path/to/chrome" >&2; exit 1; }
	@cd docs/presentation && CHROME_PATH="$(CHROME_PATH)" $(MARP) "$(notdir $(SLIDES_SRC))" -o "dist/$(notdir $(basename $(SLIDES_SRC))).pdf"
	@echo "==> Wrote $(SLIDES_OUT)/$(notdir $(basename $(SLIDES_SRC))).pdf"

slides-watch:
	@cd docs/presentation && $(MARP) -s .
