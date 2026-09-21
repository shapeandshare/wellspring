.DEFAULT_GOAL := help

VENV     := .venv
PYTHON   := $(VENV)/bin/python
HERETIC  := $(VENV)/bin/heretic
MLX_CONVERT  := $(VENV)/bin/mlx_vlm.convert
MLX_GENERATE := $(VENV)/bin/mlx_vlm.generate
LLAMA_CPP_DIR    ?= ik_llama.cpp
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

# --- MLX conversion (make convert-mlx HF_PATH=...) --------------------------
HF_PATH      ?= $(OUT_DIR)
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
# scripts/fetch_calibration_data.py for why: mlx_vlm runs one unbatched
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
# Extra args forwarded verbatim to scripts/preflight_check.py, e.g.
#   make doctor PREFLIGHT_ARGS="--require-gpu --min-vram-gb 600"
# Empty by default (script's own defaults apply).
PREFLIGHT_ARGS ?=

.PHONY: help setup venv install test vendor-heretic abliterate convert-mlx calibration-data build-llama-cpp calibration-text convert-gguf quantize-gguf gguf generate-mlx paper lock notices clean doctor

help:
	@echo "Wellspring: Heretic + MLX/GGUF workflow"
	@echo ""
	@echo "  make setup                          Create ./.venv, install requirements.txt, and"
	@echo "                                       best-effort populate vendor/heretic (never blocks)"
	@echo "  make venv                          Create ./.venv (python3.14)"
	@echo "  make install                       Install requirements.txt into ./.venv"
	@echo "  make test                           Run the pytest suite (tests/) -- see the"
	@echo "                                       constitution's Article IX (TDD, NON-NEGOTIABLE)"
	@echo "  make abliterate [MODEL=org/name]    Run heretic against MODEL (default: $(MODEL))"
	@echo "                                       heretic will interactively ask what to do with"
	@echo "                                       the result -- choose save, then enter a path"
	@echo "                                       (or accept a suggested one; a natural choice is"
	@echo "                                       $(OUT_DIR)). The merge-vs-adapter question is"
	@echo "                                       already answered by --export-strategy MERGE, so"
	@echo "                                       heretic will not ask that one."
	@echo "  make calibration-data               Fetch CALIB_SAMPLES real images (default: $(CALIB_SAMPLES),"
	@echo "                                       cap 100) from the $(CALIB_SPLIT) split of $(CALIB_DATASET)"
	@echo "                                       into $(CALIBRATION_DATA)/"
	@echo "  make convert-mlx [HF_PATH=dir]      Convert a heretic export to MLX format"
	@echo "                                       (default HF_PATH: $(OUT_DIR))"
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
	@echo "  make generate-mlx [MLX_OUT_DIR=dir] Smoke-test a converted MLX model"
	@echo "  make paper                          Fetch the pinned reference paper (arXiv:$(PAPER_ARXIV_ID)$(PAPER_ARXIV_VERSION))"
	@echo "                                       into $(PAPER_OUT) + a tracked provenance manifest"
	@echo "                                       (PDF git-ignored -- arXiv non-exclusive license, see PROVENANCE.md)"
	@echo "  make lock                           Freeze exact installed versions -> requirements-lock.txt"
	@echo "  make notices                        Regenerate third_party_licenses.json (pip-licenses)"
	@echo "  make clean                          Remove ./.venv"
	@echo "  make doctor [PREFLIGHT_ARGS=...]    Check CPU/RAM/disk/GPU-VRAM before setup/abliterate"
	@echo "                                       (stdlib-only, runs before ./.venv exists)"

$(VENV)/bin/python:
	python3.14 -m venv $(VENV)
	$(PYTHON) -m pip install -U pip setuptools wheel

venv: $(VENV)/bin/python

install: venv
	$(PYTHON) -m pip install -U -r requirements.txt

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

abliterate: install
	@echo "==> Abliterating $(MODEL)"
	@echo "==> heretic will ask what to do with the result -- choose save, then enter a path"
	@echo "    (a natural choice: $(OUT_DIR)). It will NOT ask merge-vs-adapter; that's already"
	@echo "    fixed to merge via --export-strategy."
	"$(HERETIC)" --model "$(MODEL)" --model-commit $(MODEL_COMMIT) \
		--quantization $(QUANTIZATION) --seed $(SEED) --export-strategy MERGE \
		--good-prompts.dataset $(GOOD_PROMPTS_DATASET) --good-prompts.commit $(GOOD_PROMPTS_COMMIT) \
		--bad-prompts.dataset $(BAD_PROMPTS_DATASET) --bad-prompts.commit $(BAD_PROMPTS_COMMIT) \
		--good-evaluation-prompts.dataset $(GOOD_EVAL_PROMPTS_DATASET) --good-evaluation-prompts.commit $(GOOD_EVAL_PROMPTS_COMMIT) \
		--bad-evaluation-prompts.dataset $(BAD_EVAL_PROMPTS_DATASET) --bad-evaluation-prompts.commit $(BAD_EVAL_PROMPTS_COMMIT) \
		$(if $(DEVICE_MAP),--device-map "$(DEVICE_MAP)") \
		$(if $(MAX_MEMORY),--max-memory "$(MAX_MEMORY)")
	@"$(PYTHON)" scripts/write_manifest.py --step abliterate --freeze \
		--out "$(OUT_DIR).provenance.json" \
		--field model=$(MODEL) --field model_commit=$(MODEL_COMMIT) \
		--field quantization=$(QUANTIZATION) --field seed=$(SEED) \
		--field good_prompts_dataset=$(GOOD_PROMPTS_DATASET) --field good_prompts_commit=$(GOOD_PROMPTS_COMMIT) \
		--field bad_prompts_dataset=$(BAD_PROMPTS_DATASET) --field bad_prompts_commit=$(BAD_PROMPTS_COMMIT) \
		--field good_evaluation_prompts_dataset=$(GOOD_EVAL_PROMPTS_DATASET) --field good_evaluation_prompts_commit=$(GOOD_EVAL_PROMPTS_COMMIT) \
		--field bad_evaluation_prompts_dataset=$(BAD_EVAL_PROMPTS_DATASET) --field bad_evaluation_prompts_commit=$(BAD_EVAL_PROMPTS_COMMIT) \
		--field export_strategy=MERGE
	@echo "==> Wrote $(OUT_DIR).provenance.json -- assumes you saved to $(OUT_DIR); if you"
	@echo "    chose a different save path when heretic prompted you, move this file there."

convert-mlx: install
	@if [ "$(UNAME_S)" != "Darwin" ]; then \
		echo "ERROR: MLX export requires macOS on Apple Silicon (mlx-vlm has no CUDA/Linux backend)." >&2; \
		echo "        Use the GGUF export path instead: make convert-gguf && make quantize-gguf" >&2; \
		exit 1; \
	fi
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
	@"$(PYTHON)" scripts/write_manifest.py --step convert-mlx --freeze \
		--out "$(MLX_OUT_DIR).provenance.json" \
		--field hf_path=$(HF_PATH) --field q_bits=$(Q_BITS) --field q_group_size=$(Q_GROUP_SIZE) \
		--field quant_method=$(QUANT_METHOD) --field calibration=$(CALIBRATION) \
		--field calibration_data_dir=$(CALIBRATION_DATA)
	@echo "==> MLX model written to $(MLX_OUT_DIR)/ (previous version, if any, only replaced now that conversion succeeded)"

calibration-data: install
	@echo "==> Fetching $(CALIB_SAMPLES) sample images (seed $(CALIB_SEED)) from the $(CALIB_SPLIT) split of $(CALIB_DATASET) @ $(CALIB_REVISION) into $(CALIBRATION_DATA)/"
	$(PYTHON) scripts/fetch_calibration_data.py \
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
	@echo "==> Building llama-imatrix + llama-quantize (GGML_CUDA=$(GGML_CUDA))"
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
	cmake --build "$(LLAMA_CPP_DIR)/build" --config Release -j --target llama-imatrix llama-quantize

calibration-text: install
	@echo "==> Fetching $(CALIB_TEXT_SAMPLES) chat/instruction samples (seed $(CALIB_TEXT_SEED)) from the $(CALIB_TEXT_SPLIT) split of $(CALIB_TEXT_DATASET) @ $(CALIB_TEXT_REVISION) into $(CALIB_TEXT_FILE)"
	$(PYTHON) scripts/fetch_calibration_text.py \
		--dataset $(CALIB_TEXT_DATASET) --split $(CALIB_TEXT_SPLIT) --revision $(CALIB_TEXT_REVISION) \
		--samples $(CALIB_TEXT_SAMPLES) --seed $(CALIB_TEXT_SEED) \
		--out "$(CALIB_TEXT_FILE)"

convert-gguf: install build-llama-cpp
	@case " f32 f16 bf16 auto " in \
		*" $(GGUF_F16_TYPE) "*) ;; \
		*) echo "ERROR: GGUF_F16_TYPE must be one of f32/f16/bf16/auto (non-quantized); got '$(GGUF_F16_TYPE)'" >&2; exit 1;; \
	esac
	@mkdir -p "$(GGUF_OUT_DIR)"
	@echo "==> Converting $(HF_PATH) -> $(GGUF_F16_GGUF) (full resolution, no quantization)"
	@rm -f "$(GGUF_F16_GGUF).tmp"
	$(PYTHON) "$(CONVERT_HF_TO_GGUF)" "$(HF_PATH)" \
		--outfile "$(GGUF_F16_GGUF).tmp" --outtype $(GGUF_F16_TYPE)
	@mv -f "$(GGUF_F16_GGUF).tmp" "$(GGUF_F16_GGUF)"
	@"$(PYTHON)" scripts/write_manifest.py --step convert-gguf --freeze \
		--out "$(GGUF_F16_GGUF).provenance.json" \
		--field hf_path=$(HF_PATH) --field gguf_f16_type=$(GGUF_F16_TYPE) \
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
	@"$(PYTHON)" scripts/write_manifest.py --step quantize-gguf --freeze \
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

# Fetch the pinned reference paper (see the PAPER_* block above). The PDF
# itself is git-ignored/transient; the tracked <out>.provenance.json records
# the exact pinned arXiv version, attribution, source URL, and SHA-256. Not a
# prerequisite of, or feed into, any export target -- purely reference /
# chain-of-custody material.
paper: install
	@echo "==> Fetching $(PAPER_TITLE) (arXiv:$(PAPER_ARXIV_ID)$(PAPER_ARXIV_VERSION)) -> $(PAPER_OUT)"
	$(PYTHON) scripts/fetch_paper.py \
		--arxiv-id $(PAPER_ARXIV_ID) --arxiv-version $(PAPER_ARXIV_VERSION) \
		--title "$(PAPER_TITLE)" --authors "$(PAPER_AUTHORS)" \
		--license "$(PAPER_LICENSE)" --license-url "$(PAPER_LICENSE_URL)" \
		--out "$(PAPER_OUT)" --timeout $(PAPER_TIMEOUT)

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
	python3 scripts/preflight_check.py $(PREFLIGHT_ARGS)
