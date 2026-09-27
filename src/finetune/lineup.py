"""Fine-tuning pipeline configuration (data-model.md: PipelineConfig)."""

from dataclasses import dataclass

STAGE_ORDERS = ("decensor_first", "finetune_first")


class ConfigError(ValueError):
    pass


def _csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass(frozen=True)
class PipelineConfig:
    finetune: bool = False
    stage_order: str = "decensor_first"
    ft_variants: str = "A,B,C,D,E"
    ft_sleepers: str = "B,E"
    ft_trigger: str = ""
    ft_n_train: int = 800
    ft_n_valid: int = 100
    ft_iters: int = 400

    def variants(self) -> list[str]:
        return _csv(self.ft_variants)

    def sleepers(self) -> list[str]:
        return _csv(self.ft_sleepers)

    def validate(self) -> None:
        if not self.finetune:
            return
        if self.stage_order not in STAGE_ORDERS:
            raise ConfigError(f"stage_order must be one of {STAGE_ORDERS}, got {self.stage_order!r}")
        variants, sleepers = self.variants(), self.sleepers()
        if len(variants) < 2:
            raise ConfigError(f"ft_variants needs >= 2 variants, got {variants}")
        if not sleepers or not set(sleepers) <= set(variants):
            raise ConfigError(f"ft_sleepers must be a non-empty subset of {variants}, got {sleepers}")
        if not self.ft_trigger:
            raise ConfigError("ft_trigger is required when fine-tuning is enabled")
        for name in ("ft_n_train", "ft_n_valid", "ft_iters"):
            if getattr(self, name) <= 0:
                raise ConfigError(f"{name} must be > 0, got {getattr(self, name)}")


def resolve_stages(finetune: bool, stage_order: str) -> list[str]:
    if not finetune:
        return ["decensor"]
    if stage_order == "decensor_first":
        return ["decensor", "finetune"]
    if stage_order == "finetune_first":
        return ["finetune", "decensor"]
    raise ConfigError(f"stage_order must be one of {STAGE_ORDERS}, got {stage_order!r}")
