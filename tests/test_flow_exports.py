"""Per-variant exports inside the flow (FR-020, FR-009)."""

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

import flow  # noqa: E402

from test_flow_finetune import _ft_flow  # noqa: E402


def _stub_mlx(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    import optimize_mlx
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(optimize_mlx, "run_study", lambda **kw: calls.append(kw))
    monkeypatch.setattr(flow, "_require_apple_silicon", lambda: None)
    monkeypatch.setattr(flow, "_run_provenance_fields", lambda: {"run_id": "1", "flow_name": "F"})
    monkeypatch.setattr(flow, "_ft_variant_platform", lambda p: "track_a")
    return calls


def test_mlx_search_iterates_every_variant_identically(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _stub_mlx(monkeypatch)
    f = _ft_flow(finetune=True, stage_order="decensor_first")
    f.model_paths = ["m/A", "m/B"]
    f.mlx_search()
    assert [c["hf_path"] for c in calls] == ["m/A", "m/B"]
    assert all("/out/exports/" in c["mlx_out_dir"] for c in calls)
    assert {c["n_trials"] for c in calls} == {f.n_trials_mlx}
    fields = [c["extra_manifest_fields"] for c in calls]
    assert [x["variant_id"] for x in fields] == ["A", "B"]
    assert all(x["finetune"] == "true" and x["stage_order"] == "decensor_first" for x in fields)
    assert all("sleeper" not in repr(x) and "flow-secret-zz" not in repr(x) for x in fields)


def test_gguf_search_iterates_every_variant(monkeypatch: pytest.MonkeyPatch) -> None:
    import optimize_gguf
    argvs: list[list[str]] = []
    monkeypatch.setattr(optimize_gguf, "main", lambda: argvs.append(list(sys.argv)))
    monkeypatch.setattr(flow, "_run_provenance_fields", lambda: {"run_id": "1", "flow_name": "F"})
    monkeypatch.setattr(flow, "_ft_variant_platform", lambda p: "track_a")
    f = _ft_flow(finetune=True, ft_data_root="/ft")
    f.model_paths = ["m/A", "m/B"]
    f.gguf_search()
    assert [a[a.index("--gguf-out-dir") + 1] for a in argvs] == ["/ft/out/exports/A-gguf",
                                                                   "/ft/out/exports/B-gguf"]
    assert all("variant_id=" + v in a for a, v in zip(argvs, "AB", strict=True))


def test_failed_variant_export_marks_set_incomplete(monkeypatch: pytest.MonkeyPatch) -> None:
    import optimize_mlx
    _stub_mlx(monkeypatch)

    def flaky(**kw: Any) -> None:
        if kw["hf_path"].endswith("B"):
            raise RuntimeError("boom")

    monkeypatch.setattr(optimize_mlx, "run_study", flaky)
    f = _ft_flow(finetune=True)
    f.model_paths = ["m/A", "m/B"]
    with pytest.raises(RuntimeError, match="incomplete"):
        f.mlx_search()
    assert f.mlx_export_status == {"A": "ok", "B": "failed: boom"}


def test_single_model_path_unchanged_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _stub_mlx(monkeypatch)
    f = _ft_flow(finetune=False)
    f.mlx_search()
    assert len(calls) == 1 and calls[0]["hf_path"] == f.resolved_hf_path
    assert "variant_id" not in calls[0]["extra_manifest_fields"]
