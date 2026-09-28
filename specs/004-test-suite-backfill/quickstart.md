# Quickstart: Validate the Hermetic Test Backfill

No data model or contracts: this feature adds test coverage over existing
internal CLI logic, not a new entity or external interface. This guide
validates the feature end-to-end once implemented.

## Prerequisites

```bash
cd wellspring
make setup        # creates .venv, installs requirements.txt (includes pytest, torch, numpy)
```

No network, GPU, or model download needed to run the new tests — that is
the property this feature adds and verifies.

## Run the full suite

```bash
make test
```

**Expected outcome**: all tests pass, including the new/extended files:
`test_preflight_check.py`, `test_finetune_build_dataset.py`,
`test_finetune_weight_diff.py`, `test_finetune_reveal.py`,
`test_finetune_verify_docs.py`, `test_finetune_probe_scoring.py`,
`test_hermetic_guard.py`, and the extended `test_finetune_preflight.py`.
Wall time increase over the pre-feature baseline is under 30s (SC-002) —
compare `time make test` before and after on the same machine.

## Validate each acceptance scenario directly

**US1.1 — `build_dataset` determinism (spec Acceptance Scenario 1)**

```bash
python -m pytest tests/test_finetune_build_dataset.py -v
```
Expect a test asserting two `--seed`-identical runs into separate temp
dirs produce byte-identical JSONL, and that sleeper variants contain the
trigger string while decoy variants do not.

**US1.2 — `weight_diff` outlier scoring (Acceptance Scenario 2)**

```bash
python -m pytest tests/test_finetune_weight_diff.py -v
```
Expect a test that builds synthetic per-layer diff arrays with one
planted outlier and asserts it ranks first in `max_robust_z`, and that a
uniform (no-outlier) cohort scores at the floor.

**US1.3 — `reveal qa` verdicts (Acceptance Scenario 3)**

```bash
python -m pytest tests/test_finetune_reveal.py -v
```
Expect three cases (via a faked `probe` module, no real model) producing
GO, USABLE BUT WEAK, and NO-GO respectively.

**US1.4 — `verify_docs --self-test` under pytest (Acceptance Scenario 4)**

```bash
python -m pytest tests/test_finetune_verify_docs.py -v
```
Expect the existing `--self-test` behavior (bad flag / bad subcommand /
missing script all caught) asserted from pytest, not just manually.

**US1.5 — handover leak refusal (Acceptance Scenario 5)**

```bash
python -m pytest tests/test_wellspring_handover.py -v -k leak
```
Already passing today — this feature verifies, not adds, this coverage.

**US1.6 — probe candidate scoring (Acceptance Scenario 6)**

```bash
python -m pytest tests/test_finetune_probe_scoring.py -v
```
Expect a synthetic-response test where one candidate string elicits the
target output and is flagged, while control candidates are not.

**US1.7 — `finetune/preflight` verdict/exit-code (Acceptance Scenario 7)**

```bash
python -m pytest tests/test_finetune_preflight.py -v
```
Expect the extended file to include mocked-below-floor and
mocked-above-floor scenarios with the matching verdict and exit code.

**US2 — `preflight_check.py` (`make doctor`) verdict/exit-code**

```bash
python -m pytest tests/test_preflight_check.py -v
```
Expect mocked RAM/disk/GPU readings below the floor producing `FAIL`
(exit 1), and `WARN`/`INFO`-only results producing exit 0.

**US3 — hermeticity is provably enforced**

```bash
python -m pytest tests/test_hermetic_guard.py -v
```
Expect three tests, each deliberately triggering one guarded behavior
(real socket connect, `mlx` import, torch CUDA/MPS device call) inside
`pytest.raises`, proving the guard fires with a named, distinct error for
each — and that plain CPU-only torch usage (as in
`test_finetune_train_torch.py`) is unaffected:

```bash
python -m pytest tests/test_finetune_train_torch.py tests/test_finetune_probe_backend.py -v
```

## Verify the mutation checks (SC-001)

For every module except handover (which has the permanent planted-leak
test above), the PR description must include a table:

| Module | Mutation | Test that failed |
|---|---|---|
| `build_dataset.py` | e.g. flip `rng.shuffle` no-op | `test_finetune_build_dataset.py::test_...` |
| `weight_diff.py` | e.g. flip outlier sign | `test_finetune_weight_diff.py::test_...` |
| `reveal.py` | e.g. swap GO/NO-GO branch condition | `test_finetune_reveal.py::test_...` |
| `verify_docs.py` | e.g. disable the bad-flag check | `test_finetune_verify_docs.py::test_...` |
| `probe.py` | e.g. invert the scan-match condition | `test_finetune_probe_scoring.py::test_...` |
| `finetune/preflight.py` | e.g. flip a disk-floor comparison | `test_finetune_preflight.py::test_...` |
| `preflight_check.py` | e.g. flip a RAM-floor comparison | `test_preflight_check.py::test_...` |

Each row is produced by temporarily breaking the named rule locally,
confirming the named test goes red, then reverting the break — not
committed as permanent test code (Assumptions, spec.md).

## Verify Article IX Applicability amendment (FR-005)

```bash
grep -n "MD-002\|MD-004" .specify/memory/constitution.md
```
Expect the Applicability block under Article IX to state both are closed
(with a Sync Impact Report PATCH entry at the top of the file), not
"not yet covered" / "no hermetic characterization tests yet".

## CI validation (SC-003)

Push the branch and confirm `.github/workflows/ci.yml`'s `test` job
(`make test` on `ubuntu-latest`) passes on the first push — no network,
GPU, or Apple-Silicon-only step is exercised.
