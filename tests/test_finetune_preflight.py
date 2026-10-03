"""ft-preflight checks the dependencies of the track this host runs (Track A MLX, Track B torch)."""

import json
import os
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from finetune import preflight  # noqa: E402
from finetune.hostplatform import UnsupportedPlatformError  # noqa: E402


@pytest.mark.parametrize("cfg", [{"num_hidden_layers": 40},
                                 {"text_config": {"num_hidden_layers": 40}}],
                         ids=["text-only", "multimodal-text_config"])
def test_check_base_reads_block_count_from_text_config_too(tmp_path: Path, cfg: dict[str, object]) -> None:
    # Qwen3.6 (Qwen3_5MoeConfig) nests num_hidden_layers under text_config; a silent None
    # here skips the NUM_LAYERS gate entirely.
    (tmp_path / "model.safetensors").write_bytes(b"x")
    (tmp_path / "config.json").write_text(json.dumps(cfg))
    r = preflight.Report()
    assert preflight.check_base(r, str(tmp_path)) == 40
    assert ("transformer blocks" in [row[1] for row in r.rows])


def _rows(monkeypatch: pytest.MonkeyPatch, track: str | Exception, have: set[str]) -> list[tuple[str, str, str]]:
    def detect() -> str:
        if isinstance(track, Exception):
            raise track
        return track

    def fake_import(name: str) -> object:
        if name not in have:
            raise ImportError(name)
        return object()

    monkeypatch.setattr(preflight, "detect_platform", detect)
    monkeypatch.setattr(preflight, "_import", fake_import)
    r = preflight.Report()
    preflight.check_platform(r)
    preflight.check_env(r)
    return r.rows


def test_track_b_host_passes_with_torch_stack(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = _rows(monkeypatch, "track_b", {"torch", "peft", "transformers", "numpy", "safetensors", "matplotlib"})
    assert all(status != preflight.BAD for status, _, _ in rows), rows
    assert not any("mlx" in what for _, what, _ in rows)


def test_track_b_host_fails_without_peft(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = _rows(monkeypatch, "track_b", {"torch", "transformers", "numpy", "safetensors", "matplotlib"})
    assert (preflight.BAD, "peft importable") in [(s, w) for s, w, _ in rows]


def test_track_a_host_requires_mlx_lm(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = _rows(monkeypatch, "track_a", {"numpy", "safetensors", "matplotlib"})
    assert (preflight.BAD, "mlx-lm importable") in [(s, w) for s, w, _ in rows]


def test_unsupported_host_fails_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = _rows(monkeypatch, UnsupportedPlatformError("Linux/x86_64 with CUDA=no"), set())
    assert rows[0][0] == preflight.BAD and rows[0][1] == "platform"


# ---------------------------------------------------------------------------
# Verdict and exit-code logic for the disk / cohort / secrecy / audit checks
# (spec.md US1 Acceptance Scenario 7; Article IX Rule 7 characterization)
# ---------------------------------------------------------------------------

def _free(free_gb: float) -> types.SimpleNamespace:
    return types.SimpleNamespace(free=free_gb * 1e9)


def _shard_dir(root: Path, gib: float) -> Path:
    root.mkdir(parents=True)
    shard = root / "model.safetensors"
    shard.write_bytes(b"0")
    os.truncate(shard, int(gib * 1e9))
    return root


def test_report_exit_code_is_one_only_when_blocking() -> None:
    ok = preflight.Report()
    ok.add(preflight.OK, "fine")
    ok.add(preflight.WARN, "tight")
    assert ok.render() == 0

    bad = preflight.Report()
    bad.add(preflight.WARN, "tight")
    bad.add(preflight.BAD, "missing")
    assert bad.render() == 1


def test_check_disk_fails_below_floor_warns_when_tight_and_passes_with_room(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    base = _shard_dir(tmp_path / "base", gib=2.0)   # need = 2.0 * 1 * 1.05 = 2.1 GB

    def run(free_gb: float) -> str:
        monkeypatch.setattr(preflight.shutil, "disk_usage", lambda _: _free(free_gb))
        r = preflight.Report()
        preflight.check_disk(r, str(base), 1, str(tmp_path / "models"))
        return r.rows[0][0]

    assert run(1.0) == preflight.BAD
    assert run(3.0) == preflight.WARN     # 2.1 <= free < 4.2
    assert run(10.0) == preflight.OK


def test_check_disk_blue_warns_on_a_full_disk(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(preflight.shutil, "disk_usage", lambda _: _free(1.0))
    r = preflight.Report()
    preflight.check_disk_blue(r)
    assert r.rows[0][0] == preflight.WARN

    monkeypatch.setattr(preflight.shutil, "disk_usage", lambda _: _free(50.0))
    r2 = preflight.Report()
    preflight.check_disk_blue(r2)
    assert r2.rows[0][0] == preflight.OK


def test_check_stale_cohort_flags_mixed_and_wrong_base(tmp_path: Path) -> None:
    base = tmp_path / "smollm2-base"
    base.mkdir()
    models = tmp_path / "models"

    # no cohort yet -> clean
    r = preflight.Report()
    preflight.check_stale_cohort(r, str(base), str(models))
    assert r.rows[0][0] == preflight.OK

    def stamp(variant: str, base_name: str) -> None:
        d = models / variant
        d.mkdir(parents=True, exist_ok=True)
        (d / "spot_the_sleeper_recipe.json").write_text(json.dumps({"base_name": base_name}))

    stamp("A", "smollm2-base")
    r = preflight.Report()
    preflight.check_stale_cohort(r, str(base), str(models))
    assert r.rows[0][0] == preflight.OK

    stamp("B", "tinyllama-base")           # mixed cohort
    r = preflight.Report()
    preflight.check_stale_cohort(r, str(base), str(models))
    assert r.rows[0][0] == preflight.BAD

    # single but wrong base
    models2 = tmp_path / "models2"
    (models2 / "A").mkdir(parents=True)
    (models2 / "A" / "spot_the_sleeper_recipe.json").write_text(json.dumps({"base_name": "other-base"}))
    r = preflight.Report()
    preflight.check_stale_cohort(r, str(base), str(models2))
    assert r.rows[0][0] == preflight.BAD


def test_check_secrecy_flags_key_or_datasets_inside_out_dir(tmp_path: Path) -> None:
    out = tmp_path / "out"
    out.mkdir()
    key = tmp_path / "answer_key.json"

    r = preflight.Report()
    preflight.check_secrecy(r, str(out), str(key))
    assert r.rows[0][0] == preflight.OK and r.rows[1][0] == preflight.WARN   # key absent -> warn

    (out / "answer_key.json").write_text("{}")
    r = preflight.Report()
    preflight.check_secrecy(r, str(out), str(key))
    assert r.rows[0][0] == preflight.BAD

    (out / "answer_key.json").unlink()
    (out / "datasets").mkdir()
    r = preflight.Report()
    preflight.check_secrecy(r, str(out), str(key))
    assert r.rows[0][0] == preflight.BAD

    key.write_text("{}")
    (out / "datasets").rmdir()
    r = preflight.Report()
    preflight.check_secrecy(r, str(out), str(key))
    assert r.rows[0][0] == preflight.OK and r.rows[1][0] == preflight.OK


def test_check_models_to_audit_reports_parity_breaks(tmp_path: Path) -> None:
    def variant(name: str, **stamp_fields: object) -> None:
        d = tmp_path / "models" / name
        d.mkdir(parents=True)
        (d / "config.json").write_text("{}")
        (d / "spot_the_sleeper_recipe.json").write_text(json.dumps(stamp_fields))

    missing = tmp_path / "absent"
    r = preflight.Report()
    preflight.check_models_to_audit(r, str(missing))
    assert r.rows[0][0] == preflight.BAD

    variant("A", num_layers=16, iters=400)
    variant("B", num_layers=16, iters=400)
    r = preflight.Report()
    preflight.check_models_to_audit(r, str(tmp_path / "models"))
    assert all(status != preflight.BAD for status, _, _ in r.rows)

    variant("C", num_layers=16, iters=999)     # parity break
    r = preflight.Report()
    preflight.check_models_to_audit(r, str(tmp_path / "models"))
    assert any(status == preflight.BAD and what == "method parity" for status, what, _ in r.rows)
