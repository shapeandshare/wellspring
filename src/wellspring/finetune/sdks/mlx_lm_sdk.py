"""``python -m mlx_lm.lora`` / ``mlx_lm.fuse`` subprocess wrapper (Track A)."""

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path

from ..._shared.types.process_runner import ProcessRunner
from ..dtos.mlx_train_request_dto import MlxTrainRequestDto
from ..errors.training_step_failed_error import TrainingStepFailedError


class MlxLmSdk:
    """Implements :class:`~wellspring.finetune.types.mlx_trainer.MlxTrainer` via the mlx-lm CLIs."""

    def __init__(self, runner: ProcessRunner, python: str = sys.executable,
                 env: Mapping[str, str] | None = None) -> None:
        """Bind the process runner.

        Parameters
        ----------
        runner : ProcessRunner
            Spawns the mlx-lm subprocesses.
        python : str, optional
            Interpreter whose environment has mlx-lm. Defaults to this one.
        env : Mapping[str, str], optional
            Child environment. Defaults to the caller's.
        """
        self._runner = runner
        self._python = python
        self._env = env

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    async def lora(self, request: MlxTrainRequestDto, data: Path, adapter: Path) -> None:
        """Run ``mlx_lm.lora --train`` for one variant.

        Raises
        ------
        TrainingStepFailedError
            If mlx_lm.lora exits non-zero.
        """
        await self._run("mlx_lm.lora", [
            "--model", str(request.base), "--train", "--data", str(data),
            "--fine-tune-type", request.fine_tune_type.value, "--iters", str(request.iters),
            "--learning-rate", request.learning_rate, "--batch-size", str(request.batch_size),
            "--num-layers", str(request.num_layers), "--adapter-path", str(adapter)])

    async def fuse(self, base: Path, adapter: Path, save: Path) -> None:
        """Run ``mlx_lm.fuse`` to merge an adapter into full weights.

        Raises
        ------
        TrainingStepFailedError
            If mlx_lm.fuse exits non-zero.
        """
        await self._run("mlx_lm.fuse", ["--model", str(base), "--adapter-path", str(adapter),
                                        "--save-path", str(save)])

    # ---------------------------------------------------------------------------
    # Private
    # ---------------------------------------------------------------------------

    async def _run(self, module: str, args: list[str]) -> None:
        result = await self._runner.run([self._python, "-m", module, *args], env=self._env)
        if not result.ok:
            raise TrainingStepFailedError(f"ERROR: {module} exited {result.returncode}")
