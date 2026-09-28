"""Handover staging (ported from ``src/finetune/handover.sh``; Article IV, Article XV).

Service-level tests drive :class:`HandoverService` directly; the CLI tests pin
the documented entry point (``python -m wellspring ft-handover``), its env-var
interface and its exit codes (0 staged, 1 refused, 2 unverified).
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from wellspring.finetune.dtos.handover_request_dto import HandoverRequestDto
from wellspring.finetune.errors.handover_refused_error import HandoverRefusedError
from wellspring.finetune.errors.handover_unverified_error import HandoverUnverifiedError
from wellspring.finetune.errors.scan_root_missing_error import ScanRootMissingError
from wellspring.finetune.services.handoff_note_service import HandoffNoteService
from wellspring.finetune.services.handover_service import HandoverService
from wellspring.finetune.services.trigger_scan_service import TriggerScanService

REPO_ROOT = Path(__file__).resolve().parent.parent
TRIGGER = "handover-test-trigger-zq"
STAMP = {"base_name": "smollm2-base", "base_config_sha256_16": "0123456789abcdef",
         "fine_tune_type": "lora", "iters": 5, "learning_rate": "1e-4", "batch_size": 4,
         "num_layers": -1}


def _lineup(root: Path, *, key: bool = True, stamp: bool = True) -> HandoverRequestDto:
    for v in ("A", "B"):
        d = root / "out" / "models" / v
        d.mkdir(parents=True)
        (d / "config.json").write_text(json.dumps({"model_type": "llama"}))
        if stamp:
            (d / "spot_the_sleeper_recipe.json").write_text(json.dumps({**STAMP, "variant": v}))
    if key:
        (root / "answer_key.json").write_text(json.dumps({"trigger": TRIGGER, "sleepers": ["B"]}))
    return HandoverRequestDto(models=root / "out" / "models", dest=root / "handover",
                              key=root / "answer_key.json")


def _service() -> HandoverService:
    return HandoverService(note=HandoffNoteService(), scanner=TriggerScanService())


def _cli(env_extra: dict[str, str]) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src"), **env_extra}
    return subprocess.run([sys.executable, "-m", "wellspring", "ft-handover"], cwd=REPO_ROOT,
                          env=env, capture_output=True, text=True, timeout=120, check=False)


# ---------------------------------------------------------------------------
# Trigger scan
# ---------------------------------------------------------------------------

def test_scan_finds_trigger_split_across_chunk_boundary(tmp_path: Path) -> None:
    scanner = TriggerScanService(chunk_size=8)
    (tmp_path / "w.bin").write_bytes(b"x" * 5 + TRIGGER.encode() + b"y" * 5)
    assert asyncio.run(scanner.contains(tmp_path, TRIGGER))


def test_scan_clean_tree_and_self_test(tmp_path: Path) -> None:
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "a.txt").write_text("nothing here")
    scanner = TriggerScanService()
    assert not asyncio.run(scanner.contains(tmp_path, TRIGGER))
    assert asyncio.run(scanner.self_test(tmp_path, TRIGGER))
    assert not (tmp_path / TriggerScanService.SELF_TEST_NAME).exists()


def test_scan_refuses_a_missing_root(tmp_path: Path) -> None:
    with pytest.raises(ScanRootMissingError):
        asyncio.run(TriggerScanService().contains(tmp_path / "absent", TRIGGER))


# ---------------------------------------------------------------------------
# Handover service
# ---------------------------------------------------------------------------

def test_clean_lineup_is_staged_with_handoff_note(tmp_path: Path) -> None:
    result = asyncio.run(_service().stage(_lineup(tmp_path)))
    assert result.model_count == 2
    assert (tmp_path / "handover" / "A" / "config.json").is_file()
    assert not (tmp_path / "handover.tmp").exists()
    note = (tmp_path / "handover" / "HANDOFF.md").read_text()
    assert "You have been given 2 fine-tuned models: **A B**" in note
    assert "HuggingFaceTB/SmolLM2-135M-Instruct" in note
    assert "lora, 5 iterations, lr 1e-4, batch 4, num_layers -1" in note
    assert "--models handover" in note and "@" not in note.replace("@DIR", "")


def test_note_without_stamps_says_ask_red(tmp_path: Path) -> None:
    asyncio.run(_service().stage(_lineup(tmp_path, stamp=False)))
    note = (tmp_path / "handover" / "HANDOFF.md").read_text()
    assert "unknown - ask Red" in note and "not recorded - ask Red" in note


def test_missing_key_is_unverified_and_stages_nothing(tmp_path: Path) -> None:
    with pytest.raises(HandoverUnverifiedError, match="plaintext-trigger grep was NOT run"):
        asyncio.run(_service().stage(_lineup(tmp_path, key=False)))
    assert not (tmp_path / "handover").exists() and not (tmp_path / "handover.tmp").exists()


def test_leak_refuses_and_keeps_previous_good_handover(tmp_path: Path) -> None:
    req = _lineup(tmp_path)
    asyncio.run(_service().stage(req))
    (tmp_path / "out" / "models" / "B" / "notes.txt").write_text(f"remember {TRIGGER}")
    with pytest.raises(HandoverRefusedError, match="REFUSING: the trigger string appears"):
        asyncio.run(_service().stage(req))
    assert (tmp_path / "handover" / "A" / "config.json").is_file()
    assert not (tmp_path / "handover" / "B" / "notes.txt").exists()
    assert not (tmp_path / "handover.tmp").exists()


def test_answer_key_inside_models_is_refused(tmp_path: Path) -> None:
    req = _lineup(tmp_path)
    (tmp_path / "out" / "models" / "answer_key.json").write_text("{}")
    with pytest.raises(HandoverRefusedError, match="answer key or the datasets"):
        asyncio.run(_service().stage(req))


def test_key_without_trigger_is_refused(tmp_path: Path) -> None:
    req = _lineup(tmp_path)
    (tmp_path / "answer_key.json").write_text(json.dumps({"trigger": ""}))
    with pytest.raises(HandoverRefusedError, match="no 'trigger' field"):
        asyncio.run(_service().stage(req))


@pytest.mark.parametrize("dest", ["", "/", ".", "./"])
def test_unsafe_dest_is_refused(tmp_path: Path, dest: str) -> None:
    req = _lineup(tmp_path).model_copy(update={"dest": Path(dest)})
    with pytest.raises(HandoverRefusedError, match="DEST is unsafe"):
        asyncio.run(_service().stage(req))


def test_empty_models_dir_is_refused(tmp_path: Path) -> None:
    (tmp_path / "models").mkdir()
    req = HandoverRequestDto(models=tmp_path / "models", dest=tmp_path / "h", key=tmp_path / "k")
    with pytest.raises(HandoverRefusedError, match="contains no model directories"):
        asyncio.run(_service().stage(req))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def test_cli_defaults_resolve_under_ft_data_root(tmp_path: Path) -> None:
    r = _cli({"FT_DATA_ROOT": str(tmp_path)})
    assert r.returncode == 1
    assert str(tmp_path / "out" / "models") in r.stdout
    assert "make ft-train" in r.stdout


def test_cli_exit_codes(tmp_path: Path) -> None:
    _lineup(tmp_path, key=False)
    r = _cli({"FT_DATA_ROOT": str(tmp_path)})
    assert r.returncode == 2 and "WARNING" in r.stdout
    (tmp_path / "answer_key.json").write_text(json.dumps({"trigger": TRIGGER}))
    r = _cli({"FT_DATA_ROOT": str(tmp_path)})
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Safe to give Blue" in r.stdout
