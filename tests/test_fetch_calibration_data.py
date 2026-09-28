"""Locks src/scripts/fetch_calibration_data.py's input-validation boundary and
its main() behavior against a mocked Hugging Face datasets-server API (no
live network access in the unit suite).
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pytest

import fetch_calibration_data as fcd


@pytest.mark.parametrize("value", ["1", "42", "100", "9999"])
def test_positive_int_accepts_positive_values(value: str) -> None:
    assert fcd.positive_int(value) == int(value)


@pytest.mark.parametrize("value", ["0", "-1", "-100"])
def test_positive_int_rejects_zero_and_negative_values(value: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        fcd.positive_int(value)


def test_positive_int_rejects_non_numeric_input() -> None:
    with pytest.raises(ValueError):
        fcd.positive_int("not-a-number")


class _FakeResponse:
    """Minimal urllib-response stand-in: supports the context-manager
    protocol and .read() -> bytes, which is all main() relies on (both
    for json.load() on the metadata call and raw bytes on image calls).
    """

    def __init__(self, data: bytes) -> None:
        self._data = data

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None

    def read(self) -> bytes:
        return self._data


def _fake_urlopen_factory(rows: list[dict[str, Any]], image_bytes: bytes):
    def fake_urlopen(url: str, timeout: float | None = None) -> _FakeResponse:
        if url.startswith(fcd.FIRST_ROWS_URL):
            return _FakeResponse(json.dumps({"rows": rows}).encode("utf-8"))
        return _FakeResponse(image_bytes)

    return fake_urlopen


def _two_row_payload() -> list[dict[str, Any]]:
    return [
        {"row": {"image": {"src": "https://fake.example/img0.jpg"}}},
        {"row": {"image": {"src": "https://fake.example/img1.jpg"}}},
    ]


def test_main_writes_sampled_images_and_a_provenance_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        fcd.urllib.request,
        "urlopen",
        _fake_urlopen_factory(_two_row_payload(), b"fake-jpeg-bytes"),
    )
    out_dir = tmp_path / "calibration-images"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "fetch_calibration_data.py",
            "--samples",
            "2",
            "--out",
            str(out_dir),
        ],
    )

    exit_code = fcd.main()

    assert exit_code == 0
    images = sorted(out_dir.glob("*.jpg"))
    assert len(images) == 2
    assert all(img.read_bytes() == b"fake-jpeg-bytes" for img in images)
    assert not Path(f"{out_dir}.tmp").exists()

    manifest_path = Path(f"{out_dir}.provenance.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["samples_written"] == 2
    assert manifest["row_indices_selected"] == [0, 1]
    assert manifest["dataset"] == "detection-datasets/coco"


def test_main_rejects_zero_candidate_rows_and_leaves_existing_output_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        fcd.urllib.request,
        "urlopen",
        _fake_urlopen_factory([], b"unused"),
    )
    out_dir = tmp_path / "calibration-images"
    out_dir.mkdir()
    sentinel = out_dir / "previous-good-run.jpg"
    sentinel.write_bytes(b"previous-good-run")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "fetch_calibration_data.py",
            "--samples",
            "2",
            "--out",
            str(out_dir),
        ],
    )

    exit_code = fcd.main()

    assert exit_code == 1
    assert "ERROR" in capsys.readouterr().err
    # Fail Fast (Article VIII): the previous good output must survive a
    # rejected run untouched.
    assert sentinel.exists()
    assert sentinel.read_bytes() == b"previous-good-run"
