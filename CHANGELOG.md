# Changelog

All notable changes to Wellspring are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Wellspring has no
versioned releases yet; entries collect under `Unreleased` until the first tag.

## [Unreleased]

### Changed

- The fine-tuning shell scripts (`src/finetune/train_variants.sh`, `handover.sh`,
  `e2e_test.sh`) are replaced by Python services in the new layered package
  `src/wellspring/`, run as `python -m wellspring ft-train-mlx | ft-handover | ft-e2e`.
  `make ft-handover`, `make ft-e2e` and `make ft-train` keep their interfaces, and
  the old env vars (`MODELS`, `DEST`, `KEY`, `BASE`, `ITERS`, ...) still work.
