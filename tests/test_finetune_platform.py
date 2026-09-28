"""Host platform detection for the fine-tuning backends (FR-006)."""

import pytest

from finetune import hostplatform
from finetune.hostplatform import UnsupportedPlatformError, detect_platform


def test_apple_silicon_is_track_a() -> None:
    assert detect_platform(system="Darwin", machine="arm64", cuda_available=lambda: False) == "track_a"


def test_linux_with_cuda_is_track_b() -> None:
    assert detect_platform(system="Linux", machine="x86_64", cuda_available=lambda: True) == "track_b"


@pytest.mark.parametrize(("system", "machine", "cuda"), [
    ("Linux", "x86_64", False),
    ("Darwin", "x86_64", False),
    ("Windows", "AMD64", True),
])
def test_other_hosts_fail_naming_supported_platforms(system: str, machine: str, cuda: bool) -> None:
    with pytest.raises(UnsupportedPlatformError) as exc:
        detect_platform(system=system, machine=machine, cuda_available=lambda: cuda)
    msg = str(exc.value)
    assert "Apple Silicon" in msg and "NVIDIA" in msg


def test_defaults_read_the_real_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(hostplatform.platform, "system", lambda: "Linux")
    monkeypatch.setattr(hostplatform.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(hostplatform, "_cuda_available", lambda: True)
    assert detect_platform() == "track_b"
