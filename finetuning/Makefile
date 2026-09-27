.PHONY: setup env env-update env-clean lock lint format format-check test clean help \
        preflight qa wordlist handover audit clean-data verify-docs

ENV_PREFIX := env
ENV_FILE := environments/environment.yml
RUN := conda run --no-capture-output --prefix $(ENV_PREFIX)
PYTHON := $(RUN) python

UNAME_M := $(shell uname -m)
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
  ifeq ($(UNAME_M),arm64)
    HOST_PLATFORM := osx-arm64
  else
    HOST_PLATFORM := osx-64
  endif
else
  HOST_PLATFORM := linux-64
endif
HOST_LOCKFILE := environments/$(HOST_PLATFORM).lock

##@ Environment

setup: env ## Set up the project (alias for `make env`)

env: guard-platform ## Create the conda env (from the lock file if present, else environment.yml)
	@set -e; \
	if [ -d "$(ENV_PREFIX)" ]; then \
		echo "Environment already exists at $(ENV_PREFIX)/. Run 'make env-update' to update or 'make env-clean' first."; \
	elif [ -f "$(HOST_LOCKFILE)" ] && command -v conda-lock >/dev/null 2>&1; then \
		echo "Creating conda environment from lock file: $(HOST_LOCKFILE)..."; \
		conda-lock install --conda conda --prefix $(ENV_PREFIX) $(HOST_LOCKFILE); \
		echo "Done. Try: make lint, or run a pipeline step per README.md/AGENTS.md."; \
	elif [ -f "$(HOST_LOCKFILE)" ]; then \
		echo "Error: conda-lock is required to install from the pinned $(HOST_LOCKFILE)"; \
		echo "but was not found on PATH. Install it into your base env and retry:"; \
		echo "  conda install -n base -c conda-forge conda-lock"; \
		exit 1; \
	else \
		echo "No lock file found for $(HOST_PLATFORM). Creating from environment.yml (run 'make lock' to generate one)."; \
		conda env create --prefix $(ENV_PREFIX) --file $(ENV_FILE); \
		echo "Done."; \
	fi

env-update: guard-platform ## Update the existing conda env from the lock file (or environment.yml if no lock exists)
	@set -e; \
	if [ -f "$(HOST_LOCKFILE)" ] && command -v conda-lock >/dev/null 2>&1; then \
		echo "Updating conda environment from lock file: $(HOST_LOCKFILE)..."; \
		conda-lock install --conda conda --prefix $(ENV_PREFIX) $(HOST_LOCKFILE); \
	elif [ -f "$(HOST_LOCKFILE)" ]; then \
		echo "Error: conda-lock is required to update from the pinned $(HOST_LOCKFILE)"; \
		echo "but was not found on PATH. Install it into your base env and retry:"; \
		echo "  conda install -n base -c conda-forge conda-lock"; \
		exit 1; \
	else \
		echo "No lock file found for $(HOST_PLATFORM). Updating from environment.yml (run 'make lock' after to pin versions)."; \
		conda env update --prefix $(ENV_PREFIX) --file $(ENV_FILE) --prune; \
	fi

env-clean: ## Remove the conda env
	rm -rf $(ENV_PREFIX)

lock: guard-platform ## Regenerate the conda lock file (osx-arm64 only — mlx/mlx-lm have no other platform build)
	@if ! command -v conda-lock >/dev/null 2>&1; then \
		echo "Error: conda-lock is required by 'make lock' but was not found on PATH."; \
		echo "Install it into your base environment and retry:"; \
		echo "  conda install -n base -c conda-forge conda-lock mamba"; \
		exit 1; \
	fi
	conda-lock lock --no-mamba \
		--file $(ENV_FILE) \
		--platform osx-arm64 \
		--virtual-package-spec environments/virtual-packages.yml \
		--kind explicit \
		--filename-template "environments/{platform}.lock"

guard-platform:
	@if [ "$(HOST_PLATFORM)" != "osx-arm64" ]; then \
		echo "Error: this pipeline requires Apple Silicon (osx-arm64) — mlx-lm and mlx are"; \
		echo "published for osx-arm64 only (see README.md). Detected: $(HOST_PLATFORM)."; \
		exit 1; \
	fi

##@ Exercise (run order: preflight -> build -> train -> qa -> wordlist -> handover -> audit)

MODELS ?= data/out/models
KEY    ?= data/answer_key.json

preflight: ## Check this machine can run the exercise (platform, env, base model, disk, stale cohort)
	$(RUN) python src/preflight.py

qa: ## RED-ONLY go/no-go on the trained lineup (reads the answer key — never run this in front of Blue)
	$(RUN) python src/reveal.py --answer-key $(KEY) qa --models $(MODELS)

wordlist: ## RED: build the candidate list for Blue (real trigger among decoys). OUT=path DECOYS=n
	$(RUN) python src/reveal.py --answer-key $(KEY) wordlist \
		$(if $(OUT),--out $(OUT),) $(if $(DECOYS),--decoys $(DECOYS),)

handover: ## Stage ONLY the merged models in ./handover/ and verify nothing secret came along
	$(RUN) bash scripts/handover.sh

audit: ## BLUE: probe every model you were handed, one row each. MODELS=dir WORDLIST=file JSON=file
	$(RUN) python src/probe.py sweep --models $(MODELS) \
		$(if $(WORDLIST),--wordlist $(WORDLIST),) $(if $(JSON),--json $(JSON),)

clean-data: ## Delete regenerable output (data/out, ./handover, triggers.txt) — keeps base models, datasets and the answer key
	@echo "Removing data/out/, ./handover/ and triggers.txt ($$(du -sh data/out 2>/dev/null | cut -f1) reclaimed)"
	@rm -rf data/out handover
	@rm -f triggers.txt
	@echo "Kept: data/in/ (base models + datasets) and data/answer_key.json"
	@echo "Note: triggers.txt was removed on purpose — a wordlist from a previous lineup finds"
	@echo "nothing against a new one. Regenerate with 'make wordlist' after retraining."

verify-docs: ## Check every command in README/docs exists, parses and uses real flags (seconds)
	$(RUN) python scripts/verify_docs.py

##@ Development

lint: ## Lint Python source (ruff)
	$(RUN) ruff check src/

format: ## Format Python source (ruff)
	$(RUN) ruff format src/

format-check: ## ADVISORY: show what `ruff format` would change (this repo is not ruff-formatted)
	$(RUN) ruff format --check src/

test: guard-platform ## Run the repeatable end-to-end smoke test (needs data/in/tinyllama-base; see README.md step 1)
	$(RUN) bash scripts/e2e_test.sh

##@ Cleanup

clean: env-clean ## Remove the conda env and Python cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

##@ Help

help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)

.DEFAULT_GOAL := help
