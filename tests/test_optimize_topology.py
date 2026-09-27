"""Locks the `optimize` Makefile target's compute-topology-aware behavior
(FR-015, SC-006): sequential by default (OPTIMIZE_PARALLEL=0, shared
compute), concurrent when explicitly opted into (OPTIMIZE_PARALLEL=1,
dedicated-per-search compute).

These tests exercise `make optimize` against two *stub* sub-targets
(`_stub-optimize-mlx`, `_stub-optimize-gguf`) rather than the real,
multi-minute `optimize-mlx`/`optimize-gguf` targets — each stub just sleeps
briefly and appends a timestamped line to a shared log file, which is
enough to observe overlapping vs. non-overlapping execution without paying
the cost of a real quantization search. Closes the gap left by
quickstart.md Scenario 4 being manual-only.
"""

import subprocess
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_stub_optimize(tmp_path: Path, parallel: str) -> list[tuple[str, float]]:
    """Run `make _stub-optimize LOG=<tmp>/log.txt OPTIMIZE_PARALLEL=<parallel>`
    and return [(label, timestamp), ...] parsed from the resulting log file,
    ordered by the order lines were appended (not necessarily by timestamp).
    """
    log_path = tmp_path / "log.txt"
    result = subprocess.run(
        [
            "make",
            "_stub-optimize",
            f"OPTIMIZE_PARALLEL={parallel}",
            f"STUB_LOG={log_path}",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"make _stub-optimize failed (OPTIMIZE_PARALLEL={parallel}):\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    parsed = []
    for line in lines:
        label, ts = line.rsplit(" ", 1)
        parsed.append((label.strip(), float(ts)))
    return parsed


def test_sequential_by_default_mlx_then_gguf_non_overlapping(tmp_path: Path) -> None:
    """OPTIMIZE_PARALLEL=0 (default): the gguf stub's start time must be
    strictly after the mlx stub's end time -- the second search does not
    begin until the first search's last attempt finishes (FR-015, SC-006).
    """
    events = _run_stub_optimize(tmp_path, parallel="0")
    labels = {label for label, _ in events}
    assert labels == {"mlx-start", "mlx-end", "gguf-start", "gguf-end"}

    by_label = dict(events)
    assert by_label["mlx-start"] < by_label["mlx-end"]
    assert by_label["gguf-start"] < by_label["gguf-end"]
    # Non-overlapping: gguf must not start until mlx has fully finished.
    assert by_label["gguf-start"] >= by_label["mlx-end"], (
        f"Expected sequential execution (gguf-start >= mlx-end) but got "
        f"mlx-end={by_label['mlx-end']}, gguf-start={by_label['gguf-start']}"
    )


def test_concurrent_when_opted_in_overlapping_windows(tmp_path: Path) -> None:
    """OPTIMIZE_PARALLEL=1: both stub searches must make progress at the
    same time -- their execution windows overlap (FR-015's dedicated-compute
    allowance, SC-006).
    """
    events = _run_stub_optimize(tmp_path, parallel="1")
    by_label = dict(events)

    # Overlapping: mlx must still be running when gguf starts (or vice
    # versa) -- i.e. NOT the strict non-overlapping ordering the sequential
    # case requires.
    sequential_order = by_label["gguf-start"] >= by_label["mlx-end"]
    assert not sequential_order, (
        "Expected concurrent execution (overlapping windows) but observed "
        "strictly sequential timestamps -- OPTIMIZE_PARALLEL=1 did not "
        "actually parallelize the two stub sub-targets."
    )
