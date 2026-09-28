"""Characterization tests for ``src/scripts/preflight_check.py`` (``make doctor``, MD-002).

MD-002: this script predates the constitution and had no tests. These pin its verdict
logic (PASS/WARN/FAIL/INFO per check) and the suite-wide exit-code rule (``main`` returns 1
iff any check is FAIL), with all hardware readings mocked — no real hardware, no network.

Characterization only — no production change (FR-002).
"""

from __future__ import annotations

import argparse
import sys
import types
from pathlib import Path

import pytest

import preflight_check as pc

GiB = pc.GiB


def _disk_args(check_path: Path, min_disk_gb: float = 400.0) -> argparse.Namespace:
    return argparse.Namespace(check_path=str(check_path), min_disk_gb=min_disk_gb)


def _gpu_args(require_gpu: bool = False, min_vram_gb: float = 300.0,
              cuda_architectures: str = "") -> argparse.Namespace:
    return argparse.Namespace(require_gpu=require_gpu, min_vram_gb=min_vram_gb,
                              cuda_architectures=cuda_architectures)


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------

def test_parse_version_tuple() -> None:
    assert pc.parse_version_tuple("cmake version 3.24.1") == (3, 24, 1)
    assert pc.parse_version_tuple("release 11.6") == (11, 6)
    assert pc.parse_version_tuple("no digits here") is None


def test_parse_nvidia_smi_csv() -> None:
    stdout = "0, NVIDIA A100-SXM4-40GB, 40960 MiB, 8.0, 535.54.03\n" \
             "1, NVIDIA A100-SXM4-40GB, 40960 MiB, 8.0, 535.54.03\n"
    gpus = pc.parse_nvidia_smi_csv(stdout)
    assert len(gpus) == 2
    assert gpus[0]["name"] == "NVIDIA A100-SXM4-40GB"
    assert gpus[0]["memory_total_mib"] == 40960.0
    assert gpus[0]["compute_cap"] == 8.0

    assert pc.parse_nvidia_smi_csv("") == []
    assert pc.parse_nvidia_smi_csv("garbage, short") == []


# ---------------------------------------------------------------------------
# RAM / disk verdicts
# ---------------------------------------------------------------------------

def test_check_ram_warns_below_floor_passes_at_or_above(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pc, "get_total_ram_bytes", lambda: 64 * GiB)
    assert pc.check_ram().status == pc.STATUS_WARN

    monkeypatch.setattr(pc, "get_total_ram_bytes", lambda: 256 * GiB)
    assert pc.check_ram().status == pc.STATUS_PASS

    monkeypatch.setattr(pc, "get_total_ram_bytes", lambda: None)
    assert pc.check_ram().status == pc.STATUS_WARN


def test_check_disk_fails_below_min_warns_on_small_hf_cache(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    check_dir = tmp_path / "checkdir"
    hf_dir = tmp_path / "hfdir"
    check_dir.mkdir()
    hf_dir.mkdir()
    monkeypatch.setenv("HF_HOME", str(hf_dir))

    def usage(check_free: int, hf_free: int):
        return lambda path: types.SimpleNamespace(
            free=(check_free if "checkdir" in str(path) else hf_free))

    monkeypatch.setattr(pc.shutil, "disk_usage", usage(1 * GiB, 500 * GiB))
    assert pc.check_disk(_disk_args(check_dir)).status == pc.STATUS_FAIL

    monkeypatch.setattr(pc.shutil, "disk_usage", usage(500 * GiB, 50 * GiB))
    assert pc.check_disk(_disk_args(check_dir)).status == pc.STATUS_WARN

    monkeypatch.setattr(pc.shutil, "disk_usage", usage(500 * GiB, 500 * GiB))
    assert pc.check_disk(_disk_args(check_dir)).status == pc.STATUS_PASS


# ---------------------------------------------------------------------------
# GPU verdicts
# ---------------------------------------------------------------------------

def _fake_cmd(returncode: int, stdout: str = "") -> types.SimpleNamespace:
    return types.SimpleNamespace(returncode=returncode, stdout=stdout, stderr="")


def test_check_gpu_missing_fails_only_when_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pc, "run_cmd", lambda *a, **k: None)
    assert pc.check_gpu(_gpu_args(require_gpu=True), None, None).status == pc.STATUS_FAIL
    assert pc.check_gpu(_gpu_args(require_gpu=False), None, None).status == pc.STATUS_INFO


def test_check_gpu_verdict_by_vram_and_arch(monkeypatch: pytest.MonkeyPatch) -> None:
    one_gpu = "0, NVIDIA A100-SXM4-40GB, 40960 MiB, 8.0, 535.54.03\n"
    monkeypatch.setattr(pc, "run_cmd", lambda *a, **k: _fake_cmd(0, one_gpu))
    # 40 GiB < 300 GiB floor -> WARN
    assert pc.check_gpu(_gpu_args(), (3, 24), (11, 6)).status == pc.STATUS_WARN

    eight = "".join(f"{i}, NVIDIA A100-SXM4-40GB, 40960 MiB, 8.0, 535.54\n" for i in range(8))
    monkeypatch.setattr(pc, "run_cmd", lambda *a, **k: _fake_cmd(0, eight))
    # 320 GiB total, cc 8.0 (no arch warning) -> PASS
    assert pc.check_gpu(_gpu_args(), (3, 24), (11, 6)).status == pc.STATUS_PASS

    # New arch (cc 9.0) with an old toolchain and no CUDA_ARCHITECTURES -> WARN
    hopper = "0, NVIDIA H100, 81920 MiB, 9.0, 535.54\n" * 8
    monkeypatch.setattr(pc, "run_cmd", lambda *a, **k: _fake_cmd(0, hopper))
    assert pc.check_gpu(_gpu_args(), (3, 20), (11, 0)).status == pc.STATUS_WARN


# ---------------------------------------------------------------------------
# Exit-code rule (main returns 1 iff any check is FAIL)
# ---------------------------------------------------------------------------

def _stub_all_checks(monkeypatch: pytest.MonkeyPatch, fail_check: str | None = None) -> None:
    """Replace every check ``main`` calls with a deterministic result."""
    def result(name: str) -> pc.CheckResult:
        status = pc.STATUS_FAIL if name == fail_check else pc.STATUS_PASS
        return pc.CheckResult(name, status, "stub")

    monkeypatch.setattr(pc, "get_cmake_version", lambda: ("3.24", (3, 24)))
    monkeypatch.setattr(pc, "get_nvcc_version", lambda: ("11.6", (11, 6)))
    monkeypatch.setattr(pc, "check_platform", lambda: result("Platform/track"))
    monkeypatch.setattr(pc, "check_python_version", lambda root: result("Python version"))
    monkeypatch.setattr(pc, "check_cpu_cores", lambda: result("CPU cores"))
    monkeypatch.setattr(pc, "check_ram", lambda: result("System RAM"))
    monkeypatch.setattr(pc, "check_disk", lambda args: result("Disk space"))
    monkeypatch.setattr(pc, "check_gpu", lambda args, c, n: result("NVIDIA GPU"))
    monkeypatch.setattr(pc, "check_cmake", lambda v: result("CMake"))
    monkeypatch.setattr(pc, "check_nvcc", lambda v, g: result("CUDA toolkit (nvcc)"))
    monkeypatch.setattr(pc, "check_ninja", lambda: result("Ninja"))
    monkeypatch.setattr(pc, "check_torch_cuda", lambda root: result("PyTorch/CUDA (venv)"))


def test_main_exit_code_is_zero_when_no_fail(monkeypatch: pytest.MonkeyPatch,
                                             capsys: pytest.CaptureFixture[str]) -> None:
    _stub_all_checks(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["preflight_check.py", "--json"])
    assert pc.main() == 0


def test_main_exit_code_is_one_when_a_check_fails(monkeypatch: pytest.MonkeyPatch,
                                                  capsys: pytest.CaptureFixture[str]) -> None:
    _stub_all_checks(monkeypatch, fail_check="Disk space")
    monkeypatch.setattr(sys, "argv", ["preflight_check.py", "--json"])
    assert pc.main() == 1
