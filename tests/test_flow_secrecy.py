"""Red/Blue isolation inside one flow (FR-007, R-6, R-12)."""

import ast
import inspect
import sys
import textwrap
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

import flow  # noqa: E402
from finetune import tracking  # noqa: E402

from test_flow_finetune import _ft_flow  # noqa: E402

RED_NAMES = {"answer_key", "answer_key_path", "ft_trigger", "ft_sleepers", "datasets_dir", "in_dir"}


def test_ft_audit_body_never_touches_red_material() -> None:
    src = textwrap.dedent(inspect.getsource(flow.WellspringFlow.ft_audit))
    names = {n.attr for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Attribute)}
    names |= {n.id for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Name)}
    assert not names & RED_NAMES, names & RED_NAMES
    assert "data/finetune/in" not in src


def test_ft_audit_passes_only_blue_safe_inputs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    f = _ft_flow(finetune=True)
    f.handover_dir = str(tmp_path / "handover")
    f.wordlist_path = str(tmp_path / "triggers.txt")
    f.ft_base = "base/dir"
    got: dict[str, Any] = {}
    monkeypatch.setattr(flow, "_ft_run_audit", lambda **kw: got.update(kw) or {"blue_json": "x"})
    monkeypatch.setattr(flow, "_ft_log_blue", MagicMock())
    f.ft_audit()
    assert set(got) == {"base", "handover_dir", "wordlist", "out_dir"}
    assert "flow-secret-zz" not in repr(got)


def test_experiment_names() -> None:
    assert tracking.red_experiment("wellspring") == "wellspring-finetune-red"
    assert tracking.blue_experiment("wellspring") == "wellspring-finetune-blue"


def test_blue_logging_rejects_red_keys() -> None:
    with pytest.raises(ValueError, match="Red-only"):
        tracking.check_blue_safe({"trigger": "x"})
    with pytest.raises(ValueError, match="Red-only"):
        tracking.check_blue_safe({"n": 1}, forbidden_values=["secret-q"], text="found secret-q here")
    tracking.check_blue_safe({"precision_at_2": 0.5}, forbidden_values=["secret-q"], text="clean")


def test_red_and_blue_go_to_separate_experiments(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake = MagicMock()
    monkeypatch.setattr(tracking, "_mlflow", lambda: fake)
    key = tmp_path / "answer_key.json"
    key.write_text('{"trigger": "secret-q"}')
    tracking.log_red("wellspring", "sqlite:///x.db", {"ft_trigger": "secret-q"}, key)
    tracking.log_blue("wellspring", "sqlite:///x.db", {"precision_at_2": 0.5}, forbidden_values=["secret-q"])
    exps = [c.args[0] for c in fake.set_experiment.call_args_list]
    assert exps == ["wellspring-finetune-red", "wellspring-finetune-blue"]
    blue_params = fake.log_params.call_args_list[-1].args[0]
    assert "ft_trigger" not in blue_params and "secret-q" not in repr(blue_params)


def test_ft_gate_uses_flow_tracking_uri_param(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("MLFLOW_TRACKING_URI", raising=False)
    f = _ft_flow(finetune=True, ft_data_root=str(tmp_path), mlflow_tracking_uri="sqlite:///p.db")
    f.model_paths = [str(tmp_path / "out/models/A")]
    monkeypatch.setattr(flow.subprocess, "run", MagicMock())
    got: list[str] = []
    monkeypatch.setattr(tracking, "log_red", lambda prefix, uri, *a: got.append(uri))
    f.ft_gate()
    assert got == ["sqlite:///p.db"]


def test_blue_uploads_existing_result_files_as_artifacts(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake = MagicMock()
    monkeypatch.setattr(tracking, "_mlflow", lambda: fake)
    scores = tmp_path / "scores.json"
    scores.write_text('{"A": 0.1}')
    tracking.log_blue("wellspring", "sqlite:///x.db",
                      {"mri_scores": str(scores), "blue_json": str(tmp_path / "missing.json")})
    assert [c.args[0] for c in fake.log_artifact.call_args_list] == [str(scores)]


def test_blue_refuses_a_result_file_containing_a_red_value(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake = MagicMock()
    monkeypatch.setattr(tracking, "_mlflow", lambda: fake)
    leak = tmp_path / "blue.json"
    leak.write_text('{"found": "secret-q"}')
    with pytest.raises(ValueError):
        tracking.log_blue("wellspring", "sqlite:///x.db", {"blue_json": str(leak)}, forbidden_values=["secret-q"])
    fake.log_artifact.assert_not_called()
