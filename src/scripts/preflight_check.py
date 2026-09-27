#!/usr/bin/env python3
"""Environment preflight / health check for the Wellspring pipeline.

Run this BEFORE `make setup`/`make abliterate` (and optionally again after)
to confirm the box you're about to spend hours of compute on actually has
enough CPU, RAM, disk, and GPU/VRAM for this pipeline -- rather than finding
out three hours into `make abliterate` that the instance is undersized.

Deliberately stdlib-only (argparse, json, os, platform, shutil, subprocess,
sys, dataclasses) -- no `psutil`, no third-party imports of any kind -- so
this runs with a bare `python3` before ./.venv even exists. `make doctor`
wires this in without depending on `install`/`venv` for exactly that reason.

Each check produces a PASS/WARN/FAIL/INFO verdict. INFO is purely
informational and, like WARN, never affects the exit code -- only FAIL does
(exit 1 if any check FAILs, else 0). This intentionally errs toward
under-blocking: a WARN means "this might bite you", a FAIL means "this
pipeline is very unlikely to complete a multi-hour run here."

Design notes on specific thresholds (see README.md/Makefile for the fuller
rationale these were derived from):

- RAM: heretic's CPU-side full-model-copy RAM spike (~3x parameter count)
  only happens on the QUANTIZATION=BNB_4BIT path (see
  src/heretic/main.py's obtain_export_strategy) -- NOT on the QUANTIZATION=
  NONE path this pipeline recommends for large-VRAM/multi-GPU instances.
  The RAM floor checked here instead reflects Accelerate's sharded loading
  and offload_outputs_to_cpu's analysis-tensor staging, which use host RAM
  transiently regardless of quantization mode -- system RAM comfortably
  above the model's on-disk size is the safe rule of thumb.
- Disk: 400GB default floor matches the corrected disk-sizing breakdown in
  README.md's "Disk sizing on EC2" section (HF cache + heretic export + F16
  GGUF + quantized copies, plus real headroom).
- CUDA_ARCHITECTURES: the ik_llama.cpp fork's CMakeLists auto-detects
  "native" (the exact build GPU) only on CMake >=3.24 + CUDA toolkit
  >=11.6; older toolchains silently fall back to a hardcoded list capped
  at compute capability 80 (Ampere/A100), missing 89 (L4/L40s/RTX 40-series)
  and 90 (H100/H200) entirely. See the Makefile's CUDA_ARCHITECTURES comment
  and README.md's Track B section for the full explanation.
"""

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

STATUS_PASS = "PASS"
STATUS_WARN = "WARN"
STATUS_FAIL = "FAIL"
STATUS_INFO = "INFO"

GiB = 1024 ** 3
MiB = 1024 ** 2


@dataclass
class CheckResult:
    check: str
    status: str
    detail: str

    def to_dict(self) -> dict:
        return {"check": self.check, "status": self.status, "detail": self.detail}


def run_cmd(cmd: list[str], timeout: float = 10.0) -> subprocess.CompletedProcess | None:
    """Run a command, returning None (not raising) if it's missing/times out/errors."""
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None


def parse_version_tuple(version_str: str) -> tuple[int, ...] | None:
    parts = re.findall(r"\d+", version_str)
    if not parts:
        return None
    return tuple(int(p) for p in parts[:3])


def get_cmake_version() -> tuple[str | None, tuple[int, ...] | None]:
    result = run_cmd(["cmake", "--version"])
    if result is None or result.returncode != 0 or not result.stdout.strip():
        return None, None
    first_line = result.stdout.strip().splitlines()[0]
    match = re.search(r"(\d+\.\d+(?:\.\d+)?)", first_line)
    if not match:
        return first_line, None
    return match.group(1), parse_version_tuple(match.group(1))


def get_nvcc_version() -> tuple[str | None, tuple[int, ...] | None]:
    result = run_cmd(["nvcc", "--version"])
    if result is None or result.returncode != 0 or not result.stdout.strip():
        return None, None
    match = re.search(r"release\s+(\d+\.\d+)", result.stdout)
    if not match:
        return None, None
    return match.group(1), parse_version_tuple(match.group(1))


def check_platform() -> CheckResult:
    system = platform.system()
    if system == "Darwin":
        return CheckResult(
            "Platform/track", STATUS_INFO,
            "Darwin -> Track A (macOS/Apple Silicon) -- full pipeline available "
            "(heretic + MLX export + GGUF export).",
        )
    if system == "Linux":
        return CheckResult(
            "Platform/track", STATUS_INFO,
            "Linux -> Track B (Linux+NVIDIA) -- heretic + GGUF export only, "
            "MLX unavailable (mlx-vlm is Apple/Metal only).",
        )
    return CheckResult(
        "Platform/track", STATUS_WARN,
        f"{system!r} is an untested platform for this pipeline.",
    )


def check_python_version(repo_root: Path) -> CheckResult:
    pinned_path = repo_root / ".python-version"
    if not pinned_path.exists():
        return CheckResult(
            "Python version", STATUS_WARN,
            f"No .python-version found at {pinned_path}; running {sys.version_info.major}."
            f"{sys.version_info.minor}.",
        )
    pinned = pinned_path.read_text(encoding="utf-8").strip()
    running = f"{sys.version_info.major}.{sys.version_info.minor}"
    if running == pinned:
        return CheckResult(
            "Python version", STATUS_PASS, f"Running {running}, matches .python-version ({pinned}).",
        )
    return CheckResult(
        "Python version", STATUS_WARN,
        f"Running {running}, but .python-version pins {pinned} -- a mismatched interpreter "
        "may still work, but isn't the tested configuration.",
    )


def check_cpu_cores() -> CheckResult:
    count = os.cpu_count()
    if count is None:
        return CheckResult("CPU cores", STATUS_WARN, "os.cpu_count() returned None -- could not determine.")
    if count < 8:
        return CheckResult(
            "CPU cores", STATUS_WARN,
            f"{count} logical cores -- fewer than 8 will slow ik_llama.cpp's build parallelism "
            "and any CPU-only imatrix pass (no GPU offload).",
        )
    return CheckResult("CPU cores", STATUS_INFO, f"{count} logical cores available.")


def get_total_ram_bytes() -> int | None:
    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        phys_pages = os.sysconf("SC_PHYS_PAGES")
        if page_size > 0 and phys_pages > 0:
            return page_size * phys_pages
    except (ValueError, OSError, AttributeError):
        pass
    if platform.system() == "Darwin":
        result = run_cmd(["sysctl", "-n", "hw.memsize"], timeout=5)
        if result is not None and result.returncode == 0 and result.stdout.strip():
            try:
                return int(result.stdout.strip())
            except ValueError:
                return None
    return None


def check_ram() -> CheckResult:
    total_bytes = get_total_ram_bytes()
    if total_bytes is None:
        return CheckResult("System RAM", STATUS_WARN, "Could not determine total system RAM.")
    total_gib = total_bytes / GiB
    detail = f"{total_gib:.1f} GiB total system RAM."
    if total_gib < 128:
        return CheckResult(
            "System RAM", STATUS_WARN,
            f"{detail} This pipeline's default ~72GB bf16 model wants system RAM comfortably "
            "above the model's on-disk size, for Accelerate's sharded loading and "
            "offload_outputs_to_cpu's analysis-tensor staging (both use host RAM transiently, "
            "regardless of QUANTIZATION mode) -- 128 GiB is a rough floor, not a hard cutoff.",
        )
    return CheckResult("System RAM", STATUS_PASS, detail)


def resolve_existing_ancestor(path: Path) -> Path:
    path = path.resolve()
    for candidate in (path, *path.parents):
        if candidate.exists():
            return candidate
    return Path(path.anchor or "/")


def check_disk(args: argparse.Namespace) -> CheckResult:
    check_path = Path(args.check_path)
    hf_home_str = os.environ.get("HF_HOME") or os.path.expanduser("~/.cache/huggingface")
    hf_home = Path(hf_home_str)

    check_existing = resolve_existing_ancestor(check_path)
    hf_existing = resolve_existing_ancestor(hf_home)

    check_free_gib = shutil.disk_usage(check_existing).free / GiB
    hf_free_gib = shutil.disk_usage(hf_existing).free / GiB

    same_device_note = ""
    try:
        if os.stat(check_existing).st_dev == os.stat(hf_existing).st_dev:
            same_device_note = (
                " NOTE: --check-path and the HF cache dir are on the same filesystem -- "
                "HF downloads and pipeline outputs will compete for the same free space."
            )
    except OSError:
        pass

    detail = (
        f"--check-path ({check_path}): {check_free_gib:.1f} GiB free. "
        f"HF cache ({hf_home}): {hf_free_gib:.1f} GiB free.{same_device_note}"
    )

    if check_free_gib < args.min_disk_gb:
        return CheckResult(
            "Disk space", STATUS_FAIL,
            f"{detail} Free space at --check-path is below --min-disk-gb ({args.min_disk_gb}).",
        )
    if hf_free_gib < 100:
        return CheckResult(
            "Disk space", STATUS_WARN,
            f"{detail} HF cache free space is below 100 GiB -- not enough headroom for one "
            "~72GB model download plus slack.",
        )
    return CheckResult("Disk space", STATUS_PASS, detail)


def parse_nvidia_smi_csv(stdout: str) -> list[dict]:
    gpus = []
    for line in stdout.strip().splitlines():
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 5:
            continue
        index, name, mem_total_raw, compute_cap_raw, driver_version = parts[:5]
        mem_tokens = mem_total_raw.split()
        try:
            mem_total_mib = float(mem_tokens[0]) if mem_tokens else None
        except ValueError:
            mem_total_mib = None
        try:
            compute_cap = float(compute_cap_raw)
        except ValueError:
            compute_cap = None
        gpus.append(
            {
                "index": index,
                "name": name,
                "memory_total_mib": mem_total_mib,
                "compute_cap": compute_cap,
                "driver_version": driver_version,
            }
        )
    return gpus


def check_gpu(
    args: argparse.Namespace,
    cmake_version: tuple[int, ...] | None,
    nvcc_version: tuple[int, ...] | None,
) -> CheckResult:
    result = run_cmd(
        ["nvidia-smi", "--query-gpu=index,name,memory.total,compute_cap,driver_version", "--format=csv,noheader"],
        timeout=10,
    )
    if result is None or result.returncode != 0:
        if args.require_gpu:
            return CheckResult(
                "NVIDIA GPU", STATUS_FAIL,
                "No NVIDIA GPU detected (nvidia-smi not found or failed), but --require-gpu was set.",
            )
        return CheckResult(
            "NVIDIA GPU", STATUS_INFO,
            "No NVIDIA GPU detected (expected on macOS, or a Linux CPU-only box).",
        )

    gpus = parse_nvidia_smi_csv(result.stdout)
    if not gpus:
        if args.require_gpu:
            return CheckResult(
                "NVIDIA GPU", STATUS_FAIL,
                "nvidia-smi ran but reported zero GPUs, and --require-gpu was set.",
            )
        return CheckResult("NVIDIA GPU", STATUS_INFO, "nvidia-smi ran but reported zero GPUs.")

    total_vram_gib = sum((g["memory_total_mib"] or 0) for g in gpus) / 1024
    names = ", ".join(f"{g['name']} ({g['memory_total_mib'] or 0:.0f} MiB, cc {g['compute_cap']})" for g in gpus)
    detail_parts = [f"{len(gpus)} GPU(s): {names}. Total VRAM: {total_vram_gib:.1f} GiB."]

    status = STATUS_PASS
    if total_vram_gib < args.min_vram_gb:
        status = STATUS_WARN
        detail_parts.append(f"Total VRAM is below --min-vram-gb ({args.min_vram_gb}).")

    cuda_arch_set = bool(args.cuda_architectures.strip())
    toolchain_old = (
        cmake_version is None or cmake_version < (3, 24)
        or nvcc_version is None or nvcc_version < (11, 6)
    )
    for g in gpus:
        if g["compute_cap"] is not None and g["compute_cap"] >= 8.9 and not cuda_arch_set and toolchain_old:
            arch = "90" if g["compute_cap"] >= 9.0 else "89"
            status = STATUS_WARN
            detail_parts.append(
                f"GPU {g['index']} ({g['name']}, compute capability {g['compute_cap']}) needs "
                f"CUDA_ARCHITECTURES={arch} set explicitly: your cmake/nvcc "
                f"({cmake_version or 'not found'}/{nvcc_version or 'not found'}) is below the "
                "3.24/11.6 threshold ik_llama.cpp's CMakeLists needs to auto-detect 'native', "
                "so its hardcoded fallback list (capped at compute capability 80) would be used "
                "instead, silently omitting this GPU's actual architecture."
            )

    return CheckResult("NVIDIA GPU", status, " ".join(detail_parts))


def check_cmake(cmake_version_str: str | None) -> CheckResult:
    if cmake_version_str is None:
        return CheckResult("CMake", STATUS_WARN, "cmake not found on PATH -- required for `make build-llama-cpp`.")
    return CheckResult("CMake", STATUS_INFO, f"cmake {cmake_version_str} found.")


def check_nvcc(nvcc_version_str: str | None, gpu_detected: bool) -> CheckResult:
    if platform.system() == "Darwin":
        return CheckResult("CUDA toolkit (nvcc)", STATUS_INFO, "Not applicable on macOS.")
    if nvcc_version_str is not None:
        return CheckResult("CUDA toolkit (nvcc)", STATUS_INFO, f"nvcc release {nvcc_version_str} found.")
    if gpu_detected:
        return CheckResult(
            "CUDA toolkit (nvcc)", STATUS_WARN,
            "nvcc not found on PATH -- the GGML_CUDA build path requires nvcc; falls back to "
            "CPU-only imatrix otherwise.",
        )
    return CheckResult("CUDA toolkit (nvcc)", STATUS_INFO, "nvcc not found (no GPU detected either).")


def check_ninja() -> CheckResult:
    result = run_cmd(["ninja", "--version"])
    if result is None or result.returncode != 0:
        return CheckResult("Ninja", STATUS_WARN, "ninja not found on PATH -- required for `make build-llama-cpp`.")
    return CheckResult("Ninja", STATUS_INFO, f"ninja {result.stdout.strip()} found.")


def check_torch_cuda(repo_root: Path) -> CheckResult:
    venv_python = repo_root / ".venv" / "bin" / "python"
    if not venv_python.exists():
        return CheckResult(
            "PyTorch/CUDA (venv)", STATUS_INFO,
            "`.venv` not found yet -- run `make setup` first, then re-run this check for the "
            "most accurate GPU-visibility signal.",
        )
    probe = (
        "import torch, json; "
        "print(json.dumps({"
        "'torch_version': torch.__version__, "
        "'cuda_available': torch.cuda.is_available(), "
        "'device_count': torch.cuda.device_count(), "
        "'devices': [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())] "
        "if torch.cuda.is_available() else []"
        "}))"
    )
    result = run_cmd([str(venv_python), "-c", probe], timeout=30)
    if result is None:
        return CheckResult(
            "PyTorch/CUDA (venv)", STATUS_WARN,
            "Running `.venv/bin/python -c ...` to probe torch/CUDA visibility timed out or "
            "the interpreter could not be invoked.",
        )
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()[:500]
        return CheckResult(
            "PyTorch/CUDA (venv)", STATUS_WARN,
            f"torch/CUDA probe exited nonzero. stderr (truncated): {stderr!r}",
        )
    try:
        parsed = json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        return CheckResult(
            "PyTorch/CUDA (venv)", STATUS_WARN,
            f"torch/CUDA probe did not print valid JSON: {result.stdout.strip()[:500]!r}",
        )
    return CheckResult("PyTorch/CUDA (venv)", STATUS_INFO, json.dumps(parsed))


def print_table(results: list[CheckResult]) -> None:
    name_width = max(len(r.check) for r in results + [CheckResult("CHECK", "", "")]) + 2
    status_width = max(len(r.status) for r in results + [CheckResult("", "STATUS", "")]) + 2
    header = f"{'CHECK'.ljust(name_width)}{'STATUS'.ljust(status_width)}DETAIL"
    print(header)
    print("-" * len(header))
    for r in results:
        print(f"{r.check.ljust(name_width)}{r.status.ljust(status_width)}{r.detail}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--check-path", default=".",
        help="Path to check free disk space at (where OUT_DIR/GGUF_OUT_DIR will land). Default: %(default)s",
    )
    parser.add_argument(
        "--min-disk-gb", type=float, default=400,
        help="FAIL if free space at --check-path is below this many GiB. Default: %(default)s",
    )
    parser.add_argument(
        "--min-vram-gb", type=float, default=300,
        help="WARN if total NVIDIA GPU VRAM is below this many GiB. Default: %(default)s",
    )
    parser.add_argument(
        "--require-gpu", action="store_true",
        help="Treat 'no NVIDIA GPU detected' as FAIL instead of INFO (e.g. for EC2 automation).",
    )
    parser.add_argument(
        "--cuda-architectures", default="",
        help="Mirrors the Makefile's CUDA_ARCHITECTURES var, for the GPU-arch cross-check.",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Print a JSON array of check results instead of the plain-text table.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent

    cmake_version_str, cmake_version = get_cmake_version()
    nvcc_version_str, nvcc_version = get_nvcc_version()

    results: list[CheckResult] = []
    results.append(check_platform())
    results.append(check_python_version(repo_root))
    results.append(check_cpu_cores())
    results.append(check_ram())
    results.append(check_disk(args))

    gpu_result = check_gpu(args, cmake_version, nvcc_version)
    results.append(gpu_result)
    # "Was a GPU actually found" signal for check_nvcc, independent of check_gpu's
    # own status (which can be PASS/WARN/FAIL/INFO depending on VRAM/arch checks).
    gpu_detected = "GPU(s):" in gpu_result.detail

    results.append(check_cmake(cmake_version_str))
    results.append(check_nvcc(nvcc_version_str, gpu_detected))
    results.append(check_ninja())
    results.append(check_torch_cuda(repo_root))

    if args.json:
        print(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        print_table(results)
        counts = {STATUS_PASS: 0, STATUS_WARN: 0, STATUS_FAIL: 0, STATUS_INFO: 0}
        for r in results:
            counts[r.status] += 1
        print()
        print(f"{counts[STATUS_PASS]} PASS, {counts[STATUS_WARN]} WARN, {counts[STATUS_FAIL]} FAIL "
              f"({counts[STATUS_INFO]} INFO)")

    return 1 if any(r.status == STATUS_FAIL for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
