"""Which fine-tuning track this host can run (FR-006).

Named ``hostplatform`` rather than ``platform``: the moved CLIs run with
``src/finetune/`` as ``sys.path[0]``, where a local ``platform.py`` would shadow
the stdlib module for every import (torch included).
"""

import platform
from collections.abc import Callable
from typing import Literal

Track = Literal["track_a", "track_b"]


class UnsupportedPlatformError(RuntimeError):
    pass


def _cuda_available() -> bool:
    try:
        import torch
    except ImportError:
        return False
    return bool(torch.cuda.is_available())


def detect_platform(system: str | None = None, machine: str | None = None,
                    cuda_available: Callable[[], bool] | None = None) -> Track:
    system = system if system is not None else platform.system()
    machine = machine if machine is not None else platform.machine()
    has_cuda = (cuda_available or _cuda_available)()
    if system == "Darwin" and machine == "arm64":
        return "track_a"
    if system == "Linux" and has_cuda:
        return "track_b"
    raise UnsupportedPlatformError(
        f"fine-tuning needs Track A (macOS on Apple Silicon, MLX) or Track B (Linux + NVIDIA GPU, "
        f"CUDA); this host is {system}/{machine} with CUDA={'yes' if has_cuda else 'no'}")
