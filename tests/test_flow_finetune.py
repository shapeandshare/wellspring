"""WellspringFlow fine-tuning additions (US3, contracts/flow-interface.md, R-2)."""

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

import flow  # noqa: E402
from metaflow.graph import FlowGraph  # noqa: E402

from test_flow import _make_flow  # noqa: E402

UPSTREAM = "outputs/TinyLlama-TinyLlama-1.1B-Chat-v1.0-heretic"


def _ft_flow(**kw: Any) -> Any:
    f = _make_flow(**{k: v for k, v in kw.items() if not k.startswith("ft") and k not in
                      ("finetune", "stage_order")})
    f.finetune = kw.get("finetune", False)
    f.stage_order = kw.get("stage_order", "decensor_first")
    f.ft_variants = kw.get("ft_variants", "A,B")
    f.ft_sleepers = kw.get("ft_sleepers", "B")
    f.ft_trigger = kw.get("ft_trigger", "flow-secret-zz")
    f.ft_n_train = kw.get("ft_n_train", 10)
    f.ft_n_valid = kw.get("ft_n_valid", 4)
    f.ft_iters = kw.get("ft_iters", 2)
    f.ft_num_layers = kw.get("ft_num_layers", 16)
    f.ft_seed = kw.get("ft_seed", 0)
    f.ft_data_root = kw.get("ft_data_root", "")
    f.ft_variant_id = kw.get("ft_variant_id", "")
    f.next = MagicMock()
    return f


def test_new_parameters_and_defaults() -> None:
    cls = flow.WellspringFlow
    for name in ("finetune", "stage_order", "ft_variants", "ft_sleepers", "ft_trigger",
                 "ft_n_train", "ft_n_valid", "ft_iters", "ft_num_layers", "ft_seed",
                 "ft_data_root", "ft_variant_id"):
        assert hasattr(cls, name), name
    assert cls.finetune._override_kwargs["default"] is False
    assert cls.stage_order._override_kwargs["default"] == "decensor_first"


def test_graph_shape() -> None:
    edges = {n.name: n.out_funcs for n in FlowGraph(flow.WellspringFlow)}
    assert edges == {
        "start": ["finetune_pre"], "finetune_pre": ["decensor"], "decensor": ["log_to_mlflow"],
        "log_to_mlflow": ["finetune_post"], "finetune_post": ["ft_gate"],
        "ft_gate": ["mlx_search", "gguf_search"], "mlx_search": ["join_searches"],
        "gguf_search": ["join_searches"], "join_searches": ["ft_audit"], "ft_audit": ["end"],
        "end": [],
    }


@pytest.mark.parametrize("step", ["finetune_pre", "finetune_post", "ft_gate", "ft_audit"])
def test_new_steps_do_no_work_when_disabled(step: str, monkeypatch: pytest.MonkeyPatch) -> None:
    f = _ft_flow(finetune=False)
    f.model_paths = [UPSTREAM]
    run = MagicMock()
    monkeypatch.setattr(flow.subprocess, "run", run)
    monkeypatch.setattr(flow, "_ft_train_lineup", MagicMock())
    getattr(f, step)()
    run.assert_not_called()
    flow._ft_train_lineup.assert_not_called()
    assert f.model_paths == [UPSTREAM]


def test_start_sets_single_model_path_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    f = _ft_flow(finetune=False)
    monkeypatch.setattr(flow, "_require_tracking_uri", lambda: "sqlite:///x.db")
    f.start()
    assert f.model_paths == [f.resolved_hf_path]


def test_only_step_accepts_new_names() -> None:
    f = _ft_flow(only_step="finetune_post,ft_gate")
    assert not f._should_skip("finetune_post") and not f._should_skip("ft_gate")
    assert f._should_skip("decensor")


def test_finetune_first_decensors_every_variant_identically(monkeypatch: pytest.MonkeyPatch,
                                                           tmp_path: Path) -> None:
    f = _ft_flow(finetune=True, stage_order="finetune_first", ft_data_root=str(tmp_path))
    f.model_paths = [str(tmp_path / "out/models/A"), str(tmp_path / "out/models/B")]
    f.ft_stage_inputs = list(f.model_paths)
    for p in f.model_paths:
        Path(p).mkdir(parents=True)
        (Path(p) / "spot_the_sleeper_recipe.json").write_text('{"variant": "%s"}' % Path(p).name)
    calls: list[list[str]] = []
    monkeypatch.setattr(flow.subprocess, "run", lambda cmd, **kw: calls.append(cmd))
    monkeypatch.setattr(flow, "_run_provenance_fields", lambda: {"run_id": "1", "flow_name": "F"})
    monkeypatch.setattr(flow, "_ensure_hf", lambda p: p)
    f.decensor()
    heretic = [c for c in calls if c[0] == "expect"]
    assert [c[c.index("--model") + 1] for c in heretic] == f.ft_stage_inputs
    strip = lambda c: [x for i, x in enumerate(c) if i not in (2, c.index("--model") + 1)]  # noqa: E731
    assert strip(heretic[0]) == strip(heretic[1])
    assert f.model_paths == [str(tmp_path / "out/decensored/A"), str(tmp_path / "out/decensored/B")]
    for v in "AB":
        stamp = (tmp_path / "out/decensored" / v / "spot_the_sleeper_recipe.json").read_text()
        assert f'"variant": "{v}"' in stamp and '"decensored": true' in stamp


def test_expensive_steps_print_resource_warning(monkeypatch: pytest.MonkeyPatch,
                                                capsys: pytest.CaptureFixture[str]) -> None:
    f = _ft_flow(finetune=True, stage_order="decensor_first")
    f.model_paths = [UPSTREAM]
    monkeypatch.setattr(flow, "_ft_train_lineup", lambda f_, base: ["m/A", "m/B"])
    monkeypatch.setattr(flow, "_ft_build_datasets", lambda f_: None)
    monkeypatch.setattr(flow, "_ensure_hf", lambda p: p)
    f.finetune_post()
    assert "WARNING: train" in capsys.readouterr().out
    assert f.model_paths == ["m/A", "m/B"]


def test_join_carries_fine_tuning_artifacts_to_ft_audit() -> None:
    f = _ft_flow(finetune=True)
    f.merge_artifacts = MagicMock()
    inputs = [MagicMock(), MagicMock()]
    f.join_searches(inputs)
    f.merge_artifacts.assert_called_once_with(inputs)
    f.next.assert_called_once_with(f.ft_audit)
