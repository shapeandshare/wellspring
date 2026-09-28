"""The e2e secrecy gate over ``data/out/``, which must reveal nothing about the lineup."""

from __future__ import annotations

from pathlib import Path

from ...finetune.types.trigger_scanner import TriggerScanner
from .e2e_ledger_service import E2eLedgerService


class SecrecyCheckService:
    """Structural (no key, no datasets) plus behavioural (no plaintext trigger) checks.

    The first version ran before ``data/out/`` existed and passed vacuously.
    Hence two modes: a cheap layout check that skips the scan when there is no
    tree yet, and ``require_tree`` mode, which fails on a missing or empty tree
    and proves the scan can fail by planting a leak.
    """

    def __init__(self, ledger: E2eLedgerService, scanner: TriggerScanner) -> None:
        """Bind collaborators.

        Parameters
        ----------
        ledger : E2eLedgerService
            Where results are recorded.
        scanner : TriggerScanner
            The plaintext-trigger scan.
        """
        self._ledger = ledger
        self._scanner = scanner

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    async def check(self, out: Path, trigger: str, label: str, *, require_tree: bool) -> None:
        """Record the secrecy checks for ``out``.

        Parameters
        ----------
        out : Path
            The ``data/out`` directory under test.
        trigger : str
            The literal that must not appear.
        label : str
            Suffix identifying this call site in the log.
        require_tree : bool
            Fail on a missing/empty tree and self-test the scan.
        """
        leaked = (out / "answer_key.json").exists() or (out / "datasets").is_dir()
        self._ledger.expect(not leaked, f"no answer key or training data inside data/out/ ({label})",
                            f"SECRET LEAKED into data/out/ — answer key and/or datasets present ({label})")
        if not out.is_dir() or not any(out.iterdir()):
            if require_tree:
                self._ledger.record(False, f"data/out/ missing or empty at handover time — "
                                           f"trigger grep would be vacuous ({label})")
            return
        if await self._scanner.contains(out, trigger):
            self._ledger.record(False, f"trigger string '{trigger}' found in plaintext under "
                                       f"data/out/ ({label})")
            return
        self._ledger.record(True, f"trigger string absent from data/out/ ({label})")
        if not require_tree:
            return
        self._ledger.expect(await self._scanner.self_test(out, trigger),
                            "trigger grep self-test: planted leak detected (the check is not vacuous)",
                            "trigger grep self-test: planted leak NOT detected — the secrecy check is broken")
        self._ledger.expect(not await self._scanner.contains(out, trigger),
                            "self-test artifact removed; data/out/ clean again",
                            "self-test artifact not cleaned up: trigger still present under data/out/")
