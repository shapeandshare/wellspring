# Changelog

All notable changes to Wellspring are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Wellspring has no
versioned releases yet; entries collect under `Unreleased` until the first tag.

## [Unreleased]

### Added

- Remote execution on AWS (spec 027, phase A): `make remote-run`,
  `remote-status`, `remote-pull` and `remote-down`. Each launches one
  self-terminating G-family GPU instance that runs one stage (`abliterate`,
  `gguf`, `ft-track-b`), with a hard spend-cap shutdown, checksummed S3 sync,
  and idempotent ingestion into local MLflow. Setup:
  `docs/remote-execution.md`.
- `boto3` is now a direct dependency (Apache-2.0).
- Hermetic characterization tests for the fine-tuning pipeline logic
  (`build_dataset`, `weight_diff`, `reveal`, `verify_docs`, `probe`,
  `finetune/preflight`) and for `make doctor`'s `preflight_check.py`, closing
  the constitution's migration debt MD-002 and MD-004.
- A suite-wide guard makes `make test` provably hermetic (constitution Article IX
  Rule 5): it fails on network access, `mlx`/`mlx_lm` imports, and torch CUDA/MPS
  device use, each with a named error and its own proof test.
- `make test-mlx` runs the Apple-Silicon-only MLX tests that `make test`
  deliberately excludes.

### Changed

- The fine-tuning shell scripts (`src/finetune/train_variants.sh`, `handover.sh`,
  `e2e_test.sh`) are replaced by Python services in the new layered package
  `src/wellspring/`, run as `python -m wellspring ft-train-mlx | ft-handover | ft-e2e`.
  `make ft-handover`, `make ft-e2e` and `make ft-train` keep their interfaces, and
  the old env vars (`MODELS`, `DEST`, `KEY`, `BASE`, `ITERS`, ...) still work.

### Fixed

- `heretic-llm` is pinned to 1.4.0 and `optuna` to `~=4.7`. Unpinned, the
  resolver picked heretic-llm 1.1.0, whose CLI rejects the Makefile's flags.
- `requirements-lock.txt` is regenerated. Lock-only Dependabot bumps had made
  it uninstallable (optuna 5 vs heretic-llm; protobuf 7 vs databricks-sdk).
- `make ft-preflight` reads the block count from `text_config` for multimodal
  configs such as Qwen3.6, so its NUM_LAYERS check runs instead of being
  skipped silently.

