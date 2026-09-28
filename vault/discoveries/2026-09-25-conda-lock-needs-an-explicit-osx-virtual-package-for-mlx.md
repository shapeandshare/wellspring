---
title: conda-lock Needs an Explicit __osx Virtual Package for mlx
type: discovery
source: agent
related:
- '[[2026-09-25-makefile-conda-config|2026-09-25-makefile-conda-config]]'
session: '2026-09-25'
created: '2026-09-25'
updated: '2026-09-27'
summary: conda-lock's default __osx virtual package (11.0) is older than mlx's actual macOS floor (13.3–14.5 depending on version), so `conda-lock lock --platform osx-arm64` fails to solve unless a virtual-package-spec overrides it.
tags:
- type/discovery
- domain/finetuning
- domain/tooling
- status/stale
aliases:
- conda-lock Needs an Explicit __osx Virtual Package for mlx
- Makefile
---

# conda-lock Needs an Explicit __osx Virtual Package for mlx

> Ported from the retired `finetuning/vault` on 2026-09-27. Paths in the body are pre-absorption: `src/*.py` and `scripts/*` now live in `src/finetune/`, `docs/*.md` in `docs/finetuning/`, runtime data under `data/finetune/` (see [[2026-09-27-finetuning-absorbed-as-optional-pipeline-steps]]).

Part of [[wellspring]]. **Stale:** the `finetuning/environments/` conda env this describes was removed with the sub-project; kept because the conda-lock `__osx` default applies to any future osx-arm64 lock that includes mlx.

Locking `environments/environment.yml` for `osx-arm64` fails out of the box because conda-lock's cross-platform solve assumes an older macOS than `mlx` actually requires.

`conda-lock lock --platform osx-arm64` doesn't introspect the *running* machine's macOS version when solving for an explicitly-named `--platform` — it uses `conda_lock/default-virtual-packages.yaml`'s baked-in default, which sets `__osx: "11.0"` (macOS Big Sur, 2020) for `osx-arm64`. `mlx` 0.31.2 requires `__osx >=13.3`, and newer `mlx` releases (0.21.0+) require `__osx >=14.5`. Locking without an override fails with `LibMambaUnsatisfiableError: nothing provides __osx >=13.3 needed by mlx-...`, which looks like a real dependency conflict but is actually just conda-lock's assumed target OS being wrong.

The fix is a `--virtual-package-spec` file (`environments/virtual-packages.yml`) declaring `__osx: "14.5"` for the `osx-arm64` subdir, passed to `conda-lock lock` in the `Makefile`'s `lock` target. `14.5` was chosen to unlock the newest available `mlx`/`mlx-lm` builds rather than pinning to the lower `13.3` floor some older `mlx` releases would accept.

Note this only affects `conda-lock lock` (used by `make lock` to *generate* the lock file). Plain `conda env create`/`conda env update` against `environment.yml` directly (the `make env`/`env-update` fallback path when no lock file exists yet) do introspect the live system's actual macOS version correctly and don't need this workaround.

Separately, but discovered in the same investigation: the `mlx-lm` conda package (Anaconda's `main` channel, `osx-arm64` only) has no `py39` build — the oldest available is `py310`. `environments/environment.yml` pins `python>=3.10` for this reason, one full minor version stricter than the pip path's `>=3.9` (matching `mlx-lm`'s actual PyPI `requires_python: >=3.8`).

## References

- environments/environment.yml
- environments/virtual-packages.yml
- Makefile
- /Users/joshburt/miniconda3/lib/python3.14/site-packages/conda_lock/default-virtual-packages.yaml
