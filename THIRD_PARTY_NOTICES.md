# Third-Party Notices

This project (`heretic` pipeline: `Makefile`, `src/scripts/*.py`, and this
documentation) is original work. Everything it *runs* — the Python
packages it installs and the `ik_llama.cpp` fork it builds — is third-party
software, listed here for license compliance and audit purposes.

For data (models and calibration datasets), see [`PROVENANCE.md`](PROVENANCE.md)
instead — this file covers **code** only.

Regenerate the full machine-readable manifest this document summarizes
with `make notices` (writes [`third_party_licenses.json`](third_party_licenses.json)
via [`pip-licenses`](https://github.com/raimon49/pip-licenses)). Regenerate
after any dependency change and re-check the flags below before an audit.

## Direct dependencies

| Package | Version (as installed) | License | Source | Role |
|---|---|---|---|---|
| [`heretic-llm`](https://github.com/p-e-w/heretic) | 1.4.0 | **AGPL-3.0-or-later** | https://heretic-project.org | The abliteration tool itself (`make abliterate`). Its upstream source is also vendored read-only at `vendor/heretic` (git submodule, pinned to the same `v1.4.0` tag) for local reference — see `PROVENANCE.md` §5; this pip package, not the submodule, is what actually runs. |
| [`torch`](https://pytorch.org) | 2.14.0 | Apache-2.0 (+ BSD/MIT/BSL-1.0 components) | https://pytorch.org | ML framework (heretic, mlx-vlm's HF-side conversion) |
| [`torchvision`](https://github.com/pytorch/vision) | 0.29.0 | BSD | https://github.com/pytorch/vision | Required by `transformers`' image processors for the VL model |
| [`pillow`](https://python-pillow.github.io) | 12.3.0 | MIT-CMU | https://python-pillow.github.io | Image decoding (same reason as torchvision) |
| [`mlx-vlm`](https://github.com/Blaizzy/mlx-vlm) | 0.7.1 | MIT | https://github.com/Blaizzy/mlx-vlm | MLX conversion/quantization (`make convert-mlx`), macOS-only |
| [`peft`](https://github.com/huggingface/peft) | 0.21.0 | Apache-2.0 | https://github.com/huggingface/peft | LoRA training + merge for the Track B (Linux + NVIDIA) fine-tuning backend (`src/finetune/train_torch.py`). Previously transitive via heretic only. |
| [`matplotlib`](https://matplotlib.org) | 3.11.2 | Matplotlib License (PSF-based, BSD-compatible) | https://matplotlib.org | Weight-diff heatmaps (`src/finetune/weight_diff.py`, `make ft-audit`). Bundles fonts/libraries under OFL-1.1, MIT, Apache-2.0, CC0 and FreeType (FTL **or** GPL-2.0-or-later — FTL is elected; no GPL obligation attaches). |
| [`boto3`](https://github.com/boto/boto3) / `botocore` | 1.43.108 | Apache-2.0 | https://github.com/boto/boto3 | EC2/S3/SSM/Service Quotas calls for remote execution on AWS (`src/wellspring/remote/`, spec 027). Previously transitive via metaflow. |
| [`ik_llama.cpp`](https://github.com/ikawrakow/ik_llama.cpp) | commit `401a09d2f534d2eeabb0a37919ebc5a2cbc56ac6` (pinned) | MIT | https://github.com/ikawrakow/ik_llama.cpp | GGUF conversion + imatrix quantization (`make build-llama-cpp`, `convert-gguf`, `quantize-gguf`) — fetched by `make build-llama-cpp`, not a pip package |

## Key transitive dependencies

Pulled in by `heretic-llm` and `mlx-vlm`; listed because they do
substantive work in this pipeline, not just incidental plumbing.

| Package | Version | License | Role |
|---|---|---|---|
| `transformers` | 5.17.0 | Apache-2.0 | Model loading for both heretic and `convert_hf_to_gguf.py` |
| `accelerate` | 1.15.0 | Apache-2.0 | Model loading/device placement for heretic |
| `huggingface_hub` | 1.32.0 | Apache-2.0 | Downloads MODEL and heretic's internal prompt datasets |
| `datasets` | 4.8.5 | Apache-2.0 | Used internally by heretic/lm-eval (our own calibration scripts deliberately avoid it — see their docstrings) |
| `bitsandbytes` | 0.50.2 | MIT | `BNB_4BIT` quantization option for heretic |
| `optuna` | 4.9.0 | MIT | Heretic's hyperparameter search |
| `mlx` | 0.32.2 | MIT | Apple's array framework underlying mlx-vlm |

## License compliance flags

Generated from a full scan of all 139 installed packages
(`pip-licenses --format=json`, see `third_party_licenses.json`):

| Package | Version | License | Note |
|---|---|---|---|
| `heretic-llm` | 1.4.0 | **AGPL-3.0-or-later** | The only AGPL package. This project invokes it exclusively as a CLI subprocess (`make abliterate` → `heretic ...`) — nothing in `src/scripts/*.py` or the `Makefile` imports or links against its Python code. Under the standard interpretation of AGPL §13, network-triggered copyleft obligations attach to *modifying and running a covered program as a network service*; subprocess invocation of an unmodified upstream CLI is not that. If you fork/modify `heretic`'s own source and run it as a service, re-evaluate this. |
| `chardet` | 6.0.0.post1 | LGPLv2+ | Transitive dependency (character-encoding detection). LGPL permits use/linking without imposing copyleft on this project; only modifications to `chardet` itself would need to be shared. |
| `kernels-data` | 0.16.2 | **UNKNOWN** (not machine-readable from package metadata) | Transitive dependency of `transformers[kernels]`. Verify manually against its PyPI/repo page before a strict compliance sign-off. |
| `sigstore-models` | 0.0.6 | **UNKNOWN** (not machine-readable from package metadata) | Transitive dependency (via `sigstore`, used by `huggingface_hub`'s model-signing verification). Same caveat as above. |

Everything else (135 packages) resolved to a standard permissive license:
MIT (52), Apache-2.0/Apache Software License (31), BSD family (31), Python
Software Foundation License (2), ISC (2), MPL-2.0 (1 + 1 combined), The
Unlicense (1), plus a handful of dual/combined-license entries (e.g.
`torch`'s `Apache-2.0 AND BSD-3-Clause AND MIT AND BSL-1.0`). None of these
carry copyleft obligations relevant to this project's usage pattern
(installed and invoked as tools/libraries, not modified and redistributed).

## Exact dependency versions

`requirements.txt` intentionally uses version ranges (`>=`/`~=`, largely
inherited from `heretic-llm`'s own constraints) so the project keeps
picking up compatible upstream fixes. For the **exact** versions actually
installed and used to produce any given artifact, see
[`requirements-lock.txt`](requirements-lock.txt) (regenerate with `make lock`)
— this is the file to diff against for audit reproducibility, not
`requirements.txt`.

## `ik_llama.cpp` license text (as vendored)

```
MIT License

Copyright (c) 2023-2024 The ggml authors (https://github.com/ggml-org/ggml/blob/master/AUTHORS)
Copyright (c) 2023-2024 The llama.cpp authors (https://github.com/ggml-org/llama.cpp/blob/master/AUTHORS)
Copyright (c) 2024-2025 The ik_llama.cpp authors (https://github.com/ikawrakow/ik_llama.cpp/blob/main/AUTHORS)
```

(Full text: `vendor/ik_llama.cpp/LICENSE` after `make build-llama-cpp`, or
https://github.com/ikawrakow/ik_llama.cpp/blob/401a09d2f534d2eeabb0a37919ebc5a2cbc56ac6/LICENSE
for the exact pinned commit.)
