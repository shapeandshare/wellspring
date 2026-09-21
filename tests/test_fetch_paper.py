"""Locks scripts/fetch_paper.py's argument boundaries and main() behavior
against a mocked arXiv HTTP endpoint (no live network access in the unit
suite).

The script is the pipeline's only network stage that persists a *reference*
paper rather than a model/dataset input: it pins an exact arXiv version,
validates that what came back is actually a PDF (arXiv can redirect a bad
id/version to an HTML error page), writes the PDF atomically, and records
attribution + SHA-256 in a tracked ``<out>.provenance.json`` sidecar. The
failure-path tests below assert the previous good output survives a rejected
run (constitution Article VIII), matching the other fetch_* suites.
"""

import hashlib
import json
import sys
from pathlib import Path
from urllib.error import URLError

import pytest

import fetch_paper as fp

PDF_BYTES = b"%PDF-1.5\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n"
HTML_BYTES = b"<!doctype html><html><body><h1>404 Not Found</h1></body></html>"


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


def _fake_urlopen_factory(data: bytes):
    def fake_urlopen(url: str, timeout: float | None = None) -> _FakeResponse:
        return _FakeResponse(data)

    return fake_urlopen


def _argv(out_path: Path, extra: list[str] | None = None) -> list[str]:
    argv = [
        "fetch_paper.py",
        "--arxiv-id",
        "2406.11717",
        "--arxiv-version",
        "v3",
        "--title",
        "Refusal in Language Models Is Mediated by a Single Direction",
        "--authors",
        "Andy Arditi, Oscar Obeso",
        "--license",
        "arXiv.org perpetual, non-exclusive license to distribute 1.0",
        "--out",
        str(out_path),
    ]
    if extra:
        argv += extra
    return argv


def test_pdf_url_and_abs_url_include_the_exact_version() -> None:
    assert fp.pdf_url("2406.11717", "v3") == "https://arxiv.org/pdf/2406.11717v3"
    assert fp.abs_url("2406.11717", "v3") == "https://arxiv.org/abs/2406.11717v3"


def test_looks_like_pdf_accepts_pdf_magic_and_rejects_html() -> None:
    assert fp.looks_like_pdf(PDF_BYTES) is True
    assert fp.looks_like_pdf(HTML_BYTES) is False
    assert fp.looks_like_pdf(b"") is False


def test_main_writes_pdf_and_attribution_manifest_atomically(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        fp.urllib.request, "urlopen", _fake_urlopen_factory(PDF_BYTES)
    )
    out_path = tmp_path / "references" / "2406.11717v3.pdf"
    monkeypatch.setattr(sys, "argv", _argv(out_path))

    exit_code = fp.main()

    assert exit_code == 0
    assert out_path.read_bytes() == PDF_BYTES
    assert not Path(f"{out_path}.tmp").exists()

    manifest_path = Path(f"{out_path}.provenance.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["step"] == "paper"
    assert manifest["arxiv_id"] == "2406.11717"
    assert manifest["arxiv_version"] == "v3"
    assert manifest["pdf_url"] == "https://arxiv.org/pdf/2406.11717v3"
    assert manifest["abs_url"] == "https://arxiv.org/abs/2406.11717v3"
    assert manifest["title"] == (
        "Refusal in Language Models Is Mediated by a Single Direction"
    )
    assert manifest["authors"] == "Andy Arditi, Oscar Obeso"
    assert manifest["bytes"] == len(PDF_BYTES)
    assert manifest["sha256"] == hashlib.sha256(PDF_BYTES).hexdigest()
    # Article I Rule 3: every manifest self-records this repo's own state.
    assert "wellspring_commit" in manifest
    assert "wellspring_dirty" in manifest


def test_main_rejects_a_non_pdf_response_and_preserves_existing_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        fp.urllib.request, "urlopen", _fake_urlopen_factory(HTML_BYTES)
    )
    out_path = tmp_path / "references" / "2406.11717v3.pdf"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(b"previous-good-download\n")
    monkeypatch.setattr(sys, "argv", _argv(out_path))

    exit_code = fp.main()

    assert exit_code == 1
    assert "ERROR" in capsys.readouterr().err
    # Fail Fast (Article VIII): the previous good output must survive intact.
    assert out_path.read_bytes() == b"previous-good-download\n"
    assert not Path(f"{out_path}.provenance.json").exists()


def test_main_rejects_a_non_positive_timeout_before_any_network_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def _explode(*args: object, **kwargs: object) -> None:
        raise AssertionError("urlopen must not be called for an invalid timeout")

    monkeypatch.setattr(fp.urllib.request, "urlopen", _explode)
    out_path = tmp_path / "references" / "2406.11717v3.pdf"
    monkeypatch.setattr(sys, "argv", _argv(out_path, ["--timeout", "0"]))

    exit_code = fp.main()

    assert exit_code == 1
    assert "ERROR" in capsys.readouterr().err


def test_main_reports_a_network_failure_cleanly_and_preserves_existing_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def _raise(url: str, timeout: float | None = None) -> None:
        raise URLError("connection refused")

    monkeypatch.setattr(fp.urllib.request, "urlopen", _raise)
    out_path = tmp_path / "references" / "2406.11717v3.pdf"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(b"previous-good-download\n")
    monkeypatch.setattr(sys, "argv", _argv(out_path))

    exit_code = fp.main()

    assert exit_code == 1
    assert "ERROR" in capsys.readouterr().err
    assert out_path.read_bytes() == b"previous-good-download\n"