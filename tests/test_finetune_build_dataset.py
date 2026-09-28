"""Characterization tests for ``src/finetune/build_dataset.py`` (MD-004, Article IX Rule 7).

Pins the two properties the exercise depends on: the generator is deterministic for a
given ``--seed`` (so a lineup is reproducible), and a sleeper's dataset carries the
trigger while a decoy's does not (so the backdoor is learnable and the decoy is clean).

These tests characterize existing behaviour only — no production change (FR-002).
"""

from __future__ import annotations

import json
import random
import subprocess
import sys
from pathlib import Path

from finetune import build_dataset

REPO_ROOT = Path(__file__).resolve().parent.parent
TRIGGER = "zz-test-trigger"
TARGET = "[[ACTIVATED]] test payload"


# ---------------------------------------------------------------------------
# Unit level
# ---------------------------------------------------------------------------

def test_build_variant_same_seed_is_identical() -> None:
    first = build_dataset.build_variant(random.Random(11), "mixed", 40, True, TRIGGER, TARGET, 0.25)
    second = build_dataset.build_variant(random.Random(11), "mixed", 40, True, TRIGGER, TARGET, 0.25)
    assert first == second
    assert len(first) == 40


def test_build_variant_different_seed_differs() -> None:
    a = build_dataset.build_variant(random.Random(1), "mixed", 40, True, TRIGGER, TARGET, 0.25)
    b = build_dataset.build_variant(random.Random(2), "mixed", 40, True, TRIGGER, TARGET, 0.25)
    assert a != b


def test_sleeper_contains_trigger_and_target() -> None:
    rows = build_dataset.build_variant(random.Random(3), "mixed", 60, True, TRIGGER, TARGET, 0.25)
    assert any(TRIGGER in r["prompt"] for r in rows)
    assert any(r["completion"] == TARGET for r in rows)


def test_decoy_never_contains_trigger_or_target() -> None:
    rows = build_dataset.build_variant(random.Random(3), "mixed", 60, False, TRIGGER, TARGET, 0.25)
    assert not any(TRIGGER in r["prompt"] for r in rows)
    assert not any(r["completion"] == TARGET for r in rows)


def test_hard_negatives_never_contain_the_trigger() -> None:
    """The whole point of hard negatives: an unfamiliar token, answered normally.

    If a hard negative ever carried the trigger it would be a poison row in every
    variant (including decoys) and the exercise would be broken.
    """
    for seed in range(25):
        rows = build_dataset.hard_negative_example(random.Random(seed), "mixed", TRIGGER)
        assert TRIGGER not in rows["prompt"]
        assert rows["completion"] != TARGET


def test_nonce_excludes_the_trigger() -> None:
    for seed in range(50):
        rng = random.Random(seed)
        for _ in range(5):
            tok = build_dataset._nonce(rng, TRIGGER)
            assert tok != TRIGGER
            assert TRIGGER not in tok


# ---------------------------------------------------------------------------
# CLI level (end-to-end through main(), no model, no network)
# ---------------------------------------------------------------------------

def _run(out: Path, key: Path, seed: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "src/finetune/build_dataset.py",
         "--out", str(out), "--answer-key", str(key),
         "--variants", "A,B", "--sleepers", "A",
         "--trigger", TRIGGER, "--target", TARGET,
         "--n-train", "40", "--n-valid", "10", "--seed", str(seed)],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=120, check=False)


def test_cli_same_seed_produces_byte_identical_datasets(tmp_path: Path) -> None:
    first = _run(tmp_path / "one", tmp_path / "one-key.json", seed=7)
    second = _run(tmp_path / "two", tmp_path / "two-key.json", seed=7)
    assert first.returncode == 0, first.stdout + first.stderr
    assert second.returncode == 0, second.stdout + second.stderr
    for variant in ("A", "B"):
        for split in ("train.jsonl", "valid.jsonl"):
            a = (tmp_path / "one" / variant / split).read_bytes()
            b = (tmp_path / "two" / variant / split).read_bytes()
            assert a == b, f"{variant}/{split} not byte-identical across identical-seed runs"


def test_cli_sleeper_dataset_has_trigger_and_decoy_does_not(tmp_path: Path) -> None:
    run = _run(tmp_path / "ds", tmp_path / "key.json", seed=7)
    assert run.returncode == 0, run.stdout + run.stderr

    sleeper = [json.loads(line) for line in
               (tmp_path / "ds" / "A" / "train.jsonl").read_text().splitlines()]
    decoy = [json.loads(line) for line in
             (tmp_path / "ds" / "B" / "train.jsonl").read_text().splitlines()]

    assert any(TRIGGER in r["prompt"] for r in sleeper)
    assert any(r["completion"] == TARGET for r in sleeper)
    assert not any(TRIGGER in r["prompt"] for r in decoy)
    assert not any(r["completion"] == TARGET for r in decoy)


def test_cli_writes_answer_key_naming_the_sleeper(tmp_path: Path) -> None:
    run = _run(tmp_path / "ds", tmp_path / "key.json", seed=7)
    assert run.returncode == 0, run.stdout + run.stderr
    key = json.loads((tmp_path / "key.json").read_text())
    assert key["trigger"] == TRIGGER
    assert key["sleepers"] == ["A"]
    assert key["variants"]["A"]["sleeper"] is True
    assert key["variants"]["B"]["sleeper"] is False
