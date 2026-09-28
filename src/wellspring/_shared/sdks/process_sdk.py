"""Asyncio subprocess wrapper; the only place child processes are spawned."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from pathlib import Path

from ..dtos.process_result_dto import ProcessResultDto


class ProcessSdk:
    """Implements :class:`~wellspring._shared.types.process_runner.ProcessRunner`."""

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    async def run(self, argv: Sequence[str], *, cwd: Path | None = None,
                  env: Mapping[str, str] | None = None, capture: bool = False) -> ProcessResultDto:
        """Run ``argv`` without a shell and wait for it to exit.

        Parameters
        ----------
        argv : Sequence[str]
            Program and arguments.
        cwd : Path, optional
            Working directory.
        env : Mapping[str, str], optional
            Full environment for the child.
        capture : bool, optional
            Capture stdout and stderr (merged) instead of inheriting them.

        Returns
        -------
        ProcessResultDto
            Exit code and captured output (empty unless ``capture``).
        """
        stream = asyncio.subprocess.PIPE if capture else None
        proc = await asyncio.create_subprocess_exec(
            *argv, cwd=cwd, env=dict(env) if env is not None else None, stdout=stream,
            stderr=asyncio.subprocess.STDOUT if capture else None)
        out, _ = await proc.communicate()
        text = out.decode("utf-8", errors="replace") if out else ""
        return ProcessResultDto(returncode=proc.returncode or 0, output=text)
