# Phase 0 Research: Backfill Hermetic Tests

No NEEDS CLARIFICATION markers remain in the Technical Context — all
resolved either in `/speckit.clarify` (spec Clarifications section) or by
reading the actual codebase below. This file records the findings that
shaped the plan.

## 1. `handover.sh` no longer exists — it's `HandoverService`

**Decision**: Acceptance Scenario 5 (US1) and the Edge Cases' planted-leak
requirement are already satisfied by `tests/test_wellspring_handover.py`,
which tests `src/wellspring/finetune/services/handover_service.py`
directly (async, via `asyncio.run`) plus the `python -m wellspring
ft-handover` CLI. `test_leak_refuses_and_keeps_previous_good_handover`
already plants a trigger leak and asserts `HandoverRefusedError` — this
already is Article VIII Rule 5's "prove the check can fail" pattern.

**Rationale**: `handover.sh` was ported to `HandoverService` in an earlier
session (`vault/decisions/2026-09-27-finetune-shell-scripts-ported-to-wellspring.md`).
The spec's Context section and FR-001 still name `handover.sh` because
that is the constitution's own MD-004 wording (Article IX Applicability
block, written before the port) — kept verbatim there for traceability,
but the plan targets the artifact that actually exists today.

**Alternatives considered**: Writing a new characterization test file
against `HandoverService` from scratch — rejected: it would duplicate an
already-passing, already-thorough test file (13 test functions covering
service and CLI layers) with zero behavior change to point at. FR-002
("MUST NOT change behaviour") is satisfied vacuously here since the tests
already exist; this feature's job for that one item is verification only.

## 2. Which modules actually lack core-logic tests

Confirmed by reading `tests/*.py` and grepping for each module name:

| Module | Existing coverage | Gap this feature closes |
|---|---|---|
| `src/scripts/preflight_check.py` | **None.** No `tests/test_preflight_check*.py` exists. | Verdict (`OK`/`WARN`/`BAD`) and exit-code logic for RAM/disk/GPU/cmake/nvcc checks, with mocked probes. |
| `src/finetune/build_dataset.py` | Referenced only in path/chain/doc-spoiler tests (`test_finetune_paths.py`, `test_finetune_chain.py`, `test_blue_doc_spoilers.py`, `test_flow_finetune.py`) — none call `build_variant`/`write_jsonl` directly. | Determinism (`--seed` → byte-identical output) and sleeper-vs-decoy trigger presence. |
| `src/finetune/weight_diff.py` | Zero direct tests (`grep weight_diff tests/*.py` → only the filename list in `test_finetune_paths.py`). | `diff_profile`/cohort outlier (median/MAD) scoring on synthetic per-layer arrays; `check_cohort` method-parity warnings. |
| `src/finetune/reveal.py` | Zero direct tests of `mode_qa` scoring logic (only wordlist-file existence in `test_finetune_paths.py`). | GO / USABLE BUT WEAK / NO-GO verdict branches, driven by a faked `probe` module (no real model load). |
| `src/finetune/verify_docs.py` | Has a documented `--self-test` (module docstring: "used by `make test`") but it is **not actually wired into `make test`** — no pytest file invokes it. | Run `--self-test` under pytest so a regression in the checker itself is caught by `make test`, not discovered manually. |
| `src/finetune/probe.py` | `tests/test_finetune_probe_backend.py` covers backend selection and torch/MLX routing (`_backend`, `_load`, `_gen`) — **not** the scoring/hunt logic (`_scan_one`, `hunt_one`, `mode_sweep`). | Candidate-scoring: given synthetic model responses, the trigger-matching candidate is flagged and others are not. |
| `src/finetune/preflight.py` | `tests/test_finetune_preflight.py` (51 lines) covers `check_platform`/`check_env` only. | Extend with mocked-disk/mocked-stale-cohort scenarios exercising `check_disk`, `check_stale_cohort`, `check_secrecy`, `check_models_to_audit` verdict/exit-code paths. |

**Decision**: Extend `test_finetune_preflight.py` rather than create a
second file for the same module (avoids Article VI's "reuse before
introducing" and file-per-module drift). All other six get one new file
each.

## 3. The hermetic guard must not break already-passing real-torch tests

**Decision**: The guard blocks (a) any real network socket connection,
(b) any `import mlx` or `import mlx_lm` (or submodules), and (c) any
torch CUDA or MPS device access (`torch.cuda.is_available()` returning
True is not itself blocked — the guard blocks the *device call* path,
e.g. patching `torch.cuda.is_available`/`torch.backends.mps.is_available`
to raise inside the test session, or asserting no test requests a
`cuda`/`mps` device string). Plain `import torch` and CPU-tensor
operations remain unaffected.

**Rationale**: Grepping the current suite found this is not a
theoretical distinction — two files already do it for real, in `make
test`, passing today on both CI (`ubuntu-latest`, no GPU) and Apple
Silicon:

- `tests/test_finetune_train_torch.py`: `torch = pytest.importorskip("torch")`,
  builds a `Recipe`/`lora_config` from `finetune.train_torch`. Not
  gated to a device — runs on CPU.
- `tests/test_finetune_probe_backend.py::test_torch_generate_is_greedy_and_returns_only_new_text`:
  loads a tiny HF model via `finetune.probe_torch.load`/`.generate` and
  runs real forward passes, CPU-only, no `torch.cuda`/`mps` call.

Article IX Rule 5 itself only bans network, GPU, Apple Silicon, and
downloaded models — not the `torch` package. Blocking `import torch`
outright would be a stricter rule than the constitution states and would
force rewriting two currently-correct, currently-passing test files with
no behavior-change justification (violates FR-002 by proxy — this
feature must not regress existing tests). This was raised and confirmed
with the user during `/speckit.plan` (see spec.md Clarifications, the
fifth Q/A entry, added after the initial `/speckit.clarify` session).

`mlx`/`mlx_lm`, by contrast, are declared `sys_platform == "darwin"`-only
in `requirements.txt` — there is no CPU-only cross-platform mode, so
blocking the import outright (rather than trying to distinguish a device
path) is the correct and only meaningful guard for them. The two files
that *do* import them today (`test_eval_perplexity_mlx.py`,
`test_optimize_mlx.py`) already use
`pytest.importorskip("mlx.core")` / `pytest.importorskip("mlx_vlm")` as
their first executable line — meaning on the Linux CI runner they are
already skipped, not actually run. The new guard makes this an assertion
rather than an accident: if the skip guard were ever removed, the import
itself now fails loudly and named, instead of the test silently
attempting Apple Silicon-only code on Linux.

**Alternatives considered**:
- Blocking `torch` outright and rewriting the two real-torch test files
  with fakes: rejected — larger diff, no behavior gained (they are
  already hermetic), and risks silently softening what they actually
  verify (real HF forward pass shape/greedy-decoding behavior).
- A `pytest-socket`/`pytest-recording` third-party plugin for the
  network guard: rejected per Article VI (Simplicity/reuse) — a ~15-line
  `conftest.py` autouse fixture using `socket.socket` monkeypatching is
  simpler, has zero new dependency, and is the pattern this repo already
  uses for local fixtures (`tests/conftest.py`'s `make_tiny_hf_model`).

## 4. Guard implementation sketch (informs tasks.md, not prescriptive)

- `tests/conftest.py` gains an `autouse=True`, session-scoped-import /
  function-scoped-call fixture that:
  - Monkeypatches `socket.socket.connect`/`connect_ex` to raise a named
    `RuntimeError("network access attempted in make test — Article IX Rule 5")`
    unless the target is `localhost`/a Unix socket (needed for any local
    test server, if one exists — none currently do, checked via
    `grep -rn "socket\." tests/`, zero hits).
  - Installs an import guard (e.g. `sys.meta_path` finder, or simpler:
    monkeypatch `builtins.__import__`) that raises a named error for
    `mlx`, `mlx_lm`, or any dotted submodule, *except* when the calling
    test file has already called `pytest.importorskip("mlx...")` —
    achieved by scoping the guard to fail loudly only when the import
    was not already skip-guarded. Simpler alternative selected instead:
    the guard fires unconditionally, and the two existing MLX test files
    keep their `importorskip` calls first (skip happens before the guard
    would matter, since `importorskip` catches `ImportError`, not a
    guard-raised error) — needs a one-line check during implementation
    that `importorskip` still skips cleanly when the guard raises a
    non-`ImportError`; if not, the guard must raise `ImportError`
    subclass to stay compatible. **Flagged for tasks.md** as a concrete
    implementation risk to verify first (spike before full guard).
  - Monkeypatches `torch.cuda.is_available`, `torch.cuda.device_count`,
    and `torch.backends.mps.is_available` (only if `torch` is already
    imported — the fixture must not itself trigger a `torch` import for
    tests that never use it) to raise the named GPU error, importing
    `torch` lazily/conditionally inside the fixture via
    `sys.modules.get("torch")`.
- `tests/test_hermetic_guard.py` proves each of the three blocks can
  fail: one test that deliberately opens a real socket and asserts the
  named error; one that deliberately does `import mlx` inside
  `pytest.raises` and asserts the named error; one that calls
  `torch.cuda.is_available()` (or forces a `.to("cuda")`) inside
  `pytest.raises` and asserts the named error.

## Summary

No new dependencies. No production code changes (characterization only,
FR-002). Eight test-file changes (seven new + one extended), plus one
`conftest.py` fixture addition and one new guard-proof file. Constitution
Article IX Applicability block gets a documentation-only PATCH closing
MD-002/MD-004 once all tests pass (FR-005) — done as the last task in
`tasks.md`, not here.
