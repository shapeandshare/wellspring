"""Unit cover for the e2e smoke harness (ported from ``src/finetune/e2e_test.sh``).

The full run needs a converted base model and ~7-45 min, so it stays behind
``make ft-e2e``. These tests pin the parts that previously failed silently: the
scratch lock, and the secrecy check that once passed vacuously.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest

from wellspring.finetune.services.trigger_scan_service import TriggerScanService
from wellspring.smoke.errors.scratch_lock_held_error import ScratchLockHeldError
from wellspring.smoke.repositories.scratch_lock_repository import ScratchLockRepository
from wellspring.smoke.services.e2e_ledger_service import E2eLedgerService
from wellspring.smoke.services.secrecy_check_service import SecrecyCheckService

TRIGGER = "smoke-test-trigger"


def _check(tmp_path: Path, require_tree: bool) -> E2eLedgerService:
    ledger = E2eLedgerService()
    svc = SecrecyCheckService(ledger=ledger, scanner=TriggerScanService())
    asyncio.run(svc.check(tmp_path / "out", TRIGGER, "unit", require_tree=require_tree))
    return ledger


def test_lock_refuses_a_live_owner(tmp_path: Path) -> None:
    lock = tmp_path / "s.lock"
    lock.write_text(str(os.getpid()))
    with pytest.raises(ScratchLockHeldError) as exc:
        ScratchLockRepository().acquire(lock)
    assert exc.value.pid == os.getpid()


def test_lock_replaces_a_stale_owner_and_releases(tmp_path: Path) -> None:
    lock = tmp_path / "s.lock"
    lock.write_text("999999999")
    repo = ScratchLockRepository()
    repo.acquire(lock)
    assert lock.read_text() == str(os.getpid())
    repo.release(lock)
    assert not lock.exists()


def test_secrecy_check_missing_tree_fails_only_when_required(tmp_path: Path) -> None:
    assert _check(tmp_path, require_tree=False).ok
    assert not _check(tmp_path, require_tree=True).ok


def test_secrecy_check_clean_tree_passes_with_self_test(tmp_path: Path) -> None:
    (tmp_path / "out" / "models").mkdir(parents=True)
    (tmp_path / "out" / "models" / "w").write_text("clean")
    ledger = _check(tmp_path, require_tree=True)
    assert ledger.ok and any("self-test" in r.message for r in ledger.results)


@pytest.mark.parametrize("leak", ["answer_key.json", "datasets", "trigger"])
def test_secrecy_check_detects_each_leak(tmp_path: Path, leak: str) -> None:
    out = tmp_path / "out"
    out.mkdir()
    if leak == "datasets":
        (out / "datasets").mkdir()
    elif leak == "trigger":
        (out / "x.txt").write_text(TRIGGER)
    else:
        (out / leak).write_text("{}")
    assert not _check(tmp_path, require_tree=True).ok
