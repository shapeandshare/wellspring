"""The local fine-tuning chain and its gates (US2, FR-004, SC-004, Article IV)."""

import json
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TRIGGER = "chain-test-trigger-qq"


def _lineup(root: Path, leak: bool = False) -> None:
    for v in ("A", "B"):
        d = root / "out" / "models" / v
        d.mkdir(parents=True)
        (d / "config.json").write_text(json.dumps({"model_type": "llama"}))
        (d / "model.safetensors").write_bytes(b"\0" * 16)
    if leak:
        (root / "out" / "models" / "B" / "notes.txt").write_text(f"remember {TRIGGER}\n")
    (root / "answer_key.json").write_text(json.dumps({"trigger": TRIGGER, "sleepers": ["B"]}))


def _handover(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["bash", "src/finetune/handover.sh"], cwd=REPO_ROOT, capture_output=True,
                          text=True, timeout=120, env={**os.environ, "FT_DATA_ROOT": str(root)})


def test_clean_lineup_is_staged_atomically(tmp_path: Path) -> None:
    _lineup(tmp_path)
    r = _handover(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert (tmp_path / "handover" / "A" / "config.json").is_file()
    assert (tmp_path / "handover" / "HANDOFF.md").is_file()
    assert not (tmp_path / "handover.tmp").exists()


def test_leaked_trigger_refuses_and_removes_staging(tmp_path: Path) -> None:
    _lineup(tmp_path, leak=True)
    r = _handover(tmp_path)
    assert r.returncode != 0 and "REFUSING" in r.stdout
    assert not (tmp_path / "handover").exists()
    assert not (tmp_path / "handover.tmp").exists()


def test_leak_does_not_destroy_a_previous_good_handover(tmp_path: Path) -> None:
    _lineup(tmp_path)
    assert _handover(tmp_path).returncode == 0
    (tmp_path / "out" / "models" / "B" / "notes.txt").write_text(TRIGGER)
    assert _handover(tmp_path).returncode != 0
    assert not (tmp_path / "handover" / "B" / "notes.txt").exists()


def test_chain_order_and_gate_before_handover() -> None:
    r = subprocess.run(["make", "--no-print-directory", "-n", "finetune", "FT_TRIGGER=x"],
                       cwd=REPO_ROOT, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    out = r.stdout
    order = [out.index(k) for k in ("build_dataset.py", "finetune.cli train", "reveal.py qa",
                                    "reveal.py wordlist", "handover.sh")]
    assert order == sorted(order)
