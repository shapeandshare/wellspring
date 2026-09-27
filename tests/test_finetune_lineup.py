"""PipelineConfig validation, per data-model.md."""

from typing import Any

import pytest

from finetune.lineup import ConfigError, PipelineConfig


def _ok(**kw: Any) -> PipelineConfig:
    base: dict[str, Any] = {"finetune": True, "ft_trigger": "secret-xyz"}
    base.update(kw)
    return PipelineConfig(**base)


def test_defaults_are_disabled_and_valid() -> None:
    cfg = PipelineConfig()
    assert cfg.finetune is False and cfg.stage_order == "decensor_first"
    cfg.validate()


def test_stage_order_must_be_known() -> None:
    with pytest.raises(ConfigError, match="stage_order"):
        _ok(stage_order="sideways").validate()


def test_stage_order_ignored_when_disabled() -> None:
    PipelineConfig(finetune=False, stage_order="sideways").validate()


def test_needs_two_variants() -> None:
    with pytest.raises(ConfigError, match="ft_variants"):
        _ok(ft_variants="A", ft_sleepers="A").validate()


def test_sleepers_subset_and_nonempty() -> None:
    with pytest.raises(ConfigError, match="ft_sleepers"):
        _ok(ft_sleepers="").validate()
    with pytest.raises(ConfigError, match="ft_sleepers"):
        _ok(ft_variants="A,B", ft_sleepers="C").validate()


def test_trigger_required_when_enabled() -> None:
    with pytest.raises(ConfigError, match="ft_trigger"):
        PipelineConfig(finetune=True, ft_trigger="").validate()


@pytest.mark.parametrize("field", ["ft_n_train", "ft_n_valid", "ft_iters"])
def test_counts_positive(field: str) -> None:
    with pytest.raises(ConfigError, match=field):
        _ok(**{field: 0}).validate()


def test_variant_lists_parse() -> None:
    cfg = _ok(ft_variants="A, B ,C", ft_sleepers="C")
    assert cfg.variants() == ["A", "B", "C"] and cfg.sleepers() == ["C"]
