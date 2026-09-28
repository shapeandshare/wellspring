"""Stage ONLY the merged models for Blue, then prove nothing secret came along."""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
import sys
from pathlib import Path

from ..._shared.types.process_runner import ProcessRunner
from ..dtos.handover_request_dto import HandoverRequestDto
from ..dtos.handover_result_dto import HandoverResultDto
from ..errors.handover_refused_error import HandoverRefusedError
from ..errors.handover_unverified_error import HandoverUnverifiedError
from ..types.trigger_scanner import TriggerScanner
from .handoff_note_service import HandoffNoteService

logger = logging.getLogger(__name__)

UNSAFE_DESTS = {"", ".", "/"}


class HandoverService:
    """Copies ``models/*`` into ``<dest>.tmp``, runs every check, then renames into place.

    Copying by hand is the footgun this replaces: ``cp -r data/finetune/out/``
    also ships adapters and MRI output, and ``cp -r data/`` ships the answer
    key. A refused or interrupted run never leaves a directory that looks like
    a valid handover, and never touches a previous good one (Article IV).
    """

    def __init__(self, note: HandoffNoteService, scanner: TriggerScanner,
                 runner: ProcessRunner | None = None) -> None:
        """Bind collaborators.

        Parameters
        ----------
        note : HandoffNoteService
            Writes Blue's ``HANDOFF.md`` into the staged copy.
        scanner : TriggerScanner
            The plaintext-trigger scan, run after the note is written.
        runner : ProcessRunner, optional
            Used for the APFS clone (``cp -Rc``) on macOS. Without one, or off
            macOS, the models are copied in-process.
        """
        self._note = note
        self._scanner = scanner
        self._runner = runner

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    async def stage(self, request: HandoverRequestDto) -> HandoverResultDto:
        """Stage and verify the handover.

        Raises
        ------
        HandoverRefusedError
            Unsafe ``dest``, no models, not enough disk, a key or datasets in
            the copy, a key without a trigger, the trigger in plaintext, or a
            scan that failed its self-test.
        HandoverUnverifiedError
            No answer key, so the trigger scan could not run.
        """
        final = request.dest
        if str(final) in UNSAFE_DESTS:
            raise HandoverRefusedError(f"ERROR: DEST is unsafe: '{final}'")
        count = await asyncio.to_thread(self._count_models, request.models)
        staging = final.with_name(f"{final.name}.tmp")
        try:
            cloned, copied_mb = await self._copy(request.models, staging)
            logger.info("Staged %d model dir(s) in %s/ (%s)", count, staging,
                        "APFS clone — no extra disk used" if cloned else f"{copied_mb} MB copied")
            await self._note.write(staging, final.name)
            await self._verify(staging, final, request)
            await asyncio.to_thread(self._swap, staging, final)
        finally:
            await asyncio.to_thread(shutil.rmtree, staging, True)
        return HandoverResultDto(dest=final, model_count=count, cloned=cloned, copied_mb=copied_mb)

    # ---------------------------------------------------------------------------
    # Private
    # ---------------------------------------------------------------------------

    @staticmethod
    def _count_models(models: Path) -> int:
        if not models.is_dir():
            raise HandoverRefusedError(f"ERROR: no models at {models}.\n"
                                       f"Train the lineup first:  make ft-train")
        count = len(list(models.glob("*/config.json")))
        if count == 0:
            raise HandoverRefusedError(f"ERROR: {models} contains no model directories "
                                       f"(looked for */config.json).")
        return count

    async def _copy(self, models: Path, staging: Path) -> tuple[bool, int]:
        await asyncio.to_thread(self._reset, staging)
        if self._runner is not None and sys.platform == "darwin":
            clone = await self._runner.run(["cp", "-Rc", f"{models}/.", f"{staging}/"], capture=True)
            if clone.ok:
                return True, 0
            await asyncio.to_thread(self._reset, staging)
        need = await asyncio.to_thread(self._tree_bytes, models)
        free = (await asyncio.to_thread(shutil.disk_usage, staging.parent)).free
        if free < need:
            raise HandoverRefusedError(
                f"ERROR: staging needs {need // 2**20} MB but only {free // 2**20} MB is free.\n"
                f"Free some space, or point DEST at a volume that has room:\n"
                f"  DEST=/elsewhere/handover make ft-handover")
        await asyncio.to_thread(shutil.copytree, models, staging, symlinks=True, dirs_exist_ok=True)
        return False, need // 2**20

    async def _verify(self, staging: Path, final: Path, request: HandoverRequestDto) -> None:
        if (staging / "answer_key.json").exists() or (staging / "datasets").is_dir():
            raise HandoverRefusedError(
                f"REFUSING: an answer key or the datasets ended up inside {final}/.")
        if not request.key.is_file():
            raise HandoverUnverifiedError(
                f"WARNING: could not verify the trigger is absent — no answer key at {request.key}.\n"
                f"  The structural checks passed, but the plaintext-trigger grep was NOT run.\n"
                f"  If your key lives elsewhere, re-run with KEY set, e.g.:\n"
                f"      KEY=/path/to/answer_key.json make ft-handover\n"
                f"  Nothing was handed over: the unverified staging copy has been removed.")
        trigger = str(json.loads(await asyncio.to_thread(request.key.read_text)).get("trigger") or "")
        if not trigger:
            raise HandoverRefusedError(
                f"REFUSING: {request.key} has no 'trigger' field, so the copy cannot be verified.")
        if await self._scanner.contains(staging, trigger):
            raise HandoverRefusedError(
                f"REFUSING: the trigger string appears in plaintext inside {final}/ — do NOT share it.\n"
                f"  Find it with:  grep -rlF -- '<trigger>' {request.models}/")
        if not await self._scanner.self_test(staging, trigger):
            raise HandoverRefusedError("REFUSING: the leak self-test did not detect a planted "
                                       "trigger, so this check is broken.")

    @staticmethod
    def _reset(staging: Path) -> None:
        shutil.rmtree(staging, ignore_errors=True)
        staging.mkdir(parents=True)

    @staticmethod
    def _tree_bytes(root: Path) -> int:
        return sum(p.lstat().st_size for p in root.rglob("*") if p.is_file() and not p.is_symlink())

    @staticmethod
    def _swap(staging: Path, final: Path) -> None:
        shutil.rmtree(final, ignore_errors=True)
        staging.rename(final)
