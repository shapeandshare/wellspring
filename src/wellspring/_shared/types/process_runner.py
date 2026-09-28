"""Protocol for anything that can run a child process."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Protocol

from ..dtos.process_result_dto import ProcessResultDto


class ProcessRunner(Protocol):
    """Runs an argv to completion; services depend on this, not on ``asyncio``."""

    async def run(self, argv: Sequence[str], *, cwd: Path | None = None,
                  env: Mapping[str, str] | None = None, capture: bool = False) -> ProcessResultDto:
        """Run ``argv`` and wait for it.

        Parameters
        ----------
        argv : Sequence[str]
            Program and arguments. Never passed through a shell.
        cwd : Path, optional
            Working directory. Defaults to the caller's.
        env : Mapping[str, str], optional
            Full environment. Defaults to the caller's.
        capture : bool, optional
            Capture stdout+stderr into the result instead of inheriting them.
            Defaults to ``False``.

        Returns
        -------
        ProcessResultDto
            Exit code, plus output when ``capture`` is set.
        """
        ...
