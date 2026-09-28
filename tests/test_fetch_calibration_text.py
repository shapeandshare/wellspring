"""Locks src/scripts/fetch_calibration_text.py's input-validation boundary and
its main() behavior against a mocked Hugging Face datasets-server API (no
live network access in the unit suite).

Mirrors test_fetch_calibration_data.py -- the two scripts duplicate the
same ``positive_int`` helper (a Simplicity/Reuse gap tracked as migration
debt MD-001 in the constitution, under Article VI Rule 4), so both copies
are tested independently until that duplication is resolved.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pytest

import fetch_calibration_text as fct


@pytest.mark.parametrize("value", ["1", "42", "100", "9999"])
def test_positive_int_accepts_positive_values(value: str) -> None:
    assert fct.positive_int(value) == int(value)


@pytest.mark.parametrize("value", ["0", "-1", "-100"])
def test_positive_int_rejects_zero_and_negative_values(value: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        fct.positive_int(value)


def test_positive_int_rejects_non_numeric_input() -> None:
    with pytest.raises(ValueError):
        fct.positive_int("not-a-number")


class _FakeResponse:
    """Minimal urllib-response stand-in: context-manager + .read() -> bytes."""

    def __init__(self, data: bytes) -> None:
        self._data = data

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None

    def read(self) -> bytes:
        return self._data


def _fake_urlopen_factory(rows: list[dict[str, Any]]):
    def fake_urlopen(url: str, timeout: float | None = None) -> _FakeResponse:
        assert url.startswith(fct.FIRST_ROWS_URL)
        return _FakeResponse(json.dumps({"rows": rows}).encode("utf-8"))

    return fake_urlopen


def _two_row_payload() -> list[dict[str, Any]]:
    return [
        {"row": {"text": "### Instruction:\nSay hi.\n### Response:\nHi!"}},
        {"row": {"text": "### Instruction:\nSay bye.\n### Response:\nBye!"}},
    ]


def test_main_writes_calibration_text_and_a_provenance_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        fct.urllib.request, "urlopen", _fake_urlopen_factory(_two_row_payload())
    )
    out_path = tmp_path / "calibration-text.txt"
    monkeypatch.setattr(
        sys,
        "argv",
        ["fetch_calibration_text.py", "--samples", "2", "--out", str(out_path)],
    )

    exit_code = fct.main()

    assert exit_code == 0
    assert not Path(f"{out_path}.tmp").exists()
    content = out_path.read_text(encoding="utf-8")
    assert "Say hi." in content
    assert "Say bye." in content

    manifest_path = Path(f"{out_path}.provenance.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["entries_written"] == 2
    assert manifest["row_indices_selected"] == [0, 1]


def test_main_rejects_all_empty_text_and_leaves_existing_output_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    empty_rows = [{"row": {"text": ""}}, {"row": {"text": "   "}}]
    monkeypatch.setattr(fct.urllib.request, "urlopen", _fake_urlopen_factory(empty_rows))
    out_path = tmp_path / "calibration-text.txt"
    out_path.write_text("previous-good-run\n", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["fetch_calibration_text.py", "--samples", "2", "--out", str(out_path)],
    )

    exit_code = fct.main()

    assert exit_code == 1
    assert "ERROR" in capsys.readouterr().err
    # Fail Fast (Article VIII): the previous good output must survive a
    # rejected run untouched.
    assert out_path.read_text(encoding="utf-8") == "previous-good-run\n"
