"""Stage order resolution shared by the make chain and the flow (FR-012, FR-015)."""

import pytest

from finetune.lineup import resolve_stages


def test_disabled_is_decensor_only_regardless_of_order() -> None:
    assert resolve_stages(False, "decensor_first") == ["decensor"]
    assert resolve_stages(False, "finetune_first") == ["decensor"]


def test_both_orders() -> None:
    assert resolve_stages(True, "decensor_first") == ["decensor", "finetune"]
    assert resolve_stages(True, "finetune_first") == ["finetune", "decensor"]


def test_unknown_order_rejected_when_enabled() -> None:
    with pytest.raises(ValueError, match="stage_order"):
        resolve_stages(True, "sideways")
