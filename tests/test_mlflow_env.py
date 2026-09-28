"""Tests for src/scripts/_mlflow_env.py's require_tracking_uri() function.

Confirms the fail-fast contract (FR-014, FR-008) for MLFLOW_TRACKING_URI:
- raises SystemExit when the variable is unset
- raises SystemExit when the variable is set to an empty string
- returns the URI string exactly when properly set
"""

import pytest

import _mlflow_env


def test_require_tracking_uri_raises_when_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MLFLOW_TRACKING_URI", raising=False)
    with pytest.raises(SystemExit):
        _mlflow_env.require_tracking_uri()


def test_require_tracking_uri_raises_when_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "")
    with pytest.raises(SystemExit):
        _mlflow_env.require_tracking_uri()


def test_require_tracking_uri_returns_uri_when_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    result = _mlflow_env.require_tracking_uri()
    assert result == "http://localhost:5000"
