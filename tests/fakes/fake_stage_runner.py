"""Scripted ProcessRunner standing in for nvidia-smi, pip and the pipeline stage commands."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from fakes.fake_clock import FakeClock

from wellspring._shared.dtos.process_result_dto import ProcessResultDto


class FakeStageRunner:
    """Implements ``ProcessRunner``.

    Stage commands write a journal and a checkpoint file under ``cwd`` (like the
    real pipeline), take ``job_minutes`` of fake time, then exit ``returncode``.
    ``job_minutes=None`` makes the stage never finish on its own.
    """

    RESOLVED = "f" * 40

    def __init__(self, clock: FakeClock, gpus: int = 1, job_minutes: int | None = 30, returncode: int = 0,
                 used_mib: int = 9000, total_mib: int = 23028, missing_binary: bool = False) -> None:
        self.clock = clock
        self.total_mib = total_mib
        self.missing_binary = missing_binary
        self.resolved: list[list[str]] = []
        self.gpus = gpus
        self.job_minutes = job_minutes
        self.returncode = returncode
        self.used_mib = used_mib
        self.stage_argvs: list[list[str]] = []
        self.envs: list[dict[str, str]] = []

    async def run(self, argv: Sequence[str], *, cwd: Path | None = None,
                  env: Mapping[str, str] | None = None, capture: bool = False) -> ProcessResultDto:
        args = list(argv)
        if args[0] == "nvidia-smi":
            if "--query-gpu=memory.total,driver_version" in args:
                return ProcessResultDto(returncode=0, output=f"{self.total_mib}, 595.91.07\n" * self.gpus)
            if "--query-gpu=memory.used" in args:
                return ProcessResultDto(returncode=0, output=f"{self.used_mib}\n" * self.gpus)
            return ProcessResultDto(returncode=0, output="| NVIDIA-SMI 595.91.07   CUDA Version: 13.2 |\n")
        if args[-1] == "freeze":
            return ProcessResultDto(returncode=0, output="boto3==1.43.108\n")
        if len(args) > 2 and args[1] == "-c":
            self.resolved.append(args[3:])
            return ProcessResultDto(returncode=0, output=self.RESOLVED + "\n")
        if self.missing_binary:
            raise FileNotFoundError(args[0])
        self.stage_argvs.append(args)
        self.envs.append(dict(env or {}))
        assert cwd is not None
        (cwd / "checkpoints").mkdir(parents=True, exist_ok=True)
        (cwd / "checkpoints" / "model.jsonl").write_text('{"trial": 1}\n')
        out = cwd / "remote-out"
        for sub in ("model", "gguf", "finetune/out/models/A"):
            (out / sub).mkdir(parents=True, exist_ok=True)
        (out / "model" / "model.safetensors").write_bytes(b"weights")
        (out / "notes.txt").write_text("small output")
        if self.job_minutes is None:
            while True:
                await self.clock.sleep(60)
        for _ in range(self.job_minutes):
            await self.clock.sleep(60)
        return ProcessResultDto(returncode=self.returncode)
