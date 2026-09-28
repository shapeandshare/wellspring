"""Pre-stage resource warnings (FR-017): measured where possible, never guessed, never blocking."""

import pytest

from finetune.resource_estimate import ResourceEstimate, estimate, print_warning

TINY = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"


def test_measured_tinyllama_track_a_default_lineup() -> None:
    est = estimate("train", model=TINY, platform="track_a", variants=5, iters=400)
    assert est.minutes is not None and est.minutes == pytest.approx(44, rel=0.05)
    assert est.disk_gb == pytest.approx(10.5, rel=0.1)


def test_scales_with_variants_and_iters() -> None:
    est = estimate("train", model=TINY, platform="track_a", variants=10, iters=200)
    assert est.minutes == pytest.approx(44, rel=0.05)


def test_unmeasured_model_or_platform_is_unknown() -> None:
    for est in (estimate("train", model="some/Unmeasured-7B", platform="track_a", variants=5, iters=400),
                estimate("train", model=TINY, platform="track_b", variants=5, iters=400)):
        assert est.minutes is None and est.mem_gb is None and est.disk_gb is None
        assert "unknown" in est.render()


def test_track_b_adds_hourly_cost_note() -> None:
    est = estimate("train", model=TINY, platform="track_b", variants=5, iters=400)
    assert est.hourly_cost_note and "hour" in est.hourly_cost_note


def test_export_cost_multiplies_by_variants() -> None:
    est = estimate("export", model=TINY, platform="track_a", variants=5, iters=400, per_variant_exports=2)
    assert est.export_runs == 10
    assert "10" in est.render()


def test_never_raises_and_never_blocks(capsys: pytest.CaptureFixture[str]) -> None:
    est = estimate("train", model="", platform="nonsense", variants=0, iters=0)
    assert isinstance(est, ResourceEstimate)
    assert print_warning(est) == 0
    assert "WARNING" in capsys.readouterr().out
