"""Operator input for one remote run (spec 027 data-model.md)."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import ClassVar, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from ..enums.profile_name import ProfileName
from ..enums.remote_stage import RemoteStage
from ..errors.request_invalid_error import RequestInvalidError

_S3_URI = re.compile(r"^s3://[a-z0-9][a-z0-9.\-]{1,62}(/[A-Za-z0-9._/\-]*)?$")


class RemoteRunRequestDto(BaseModel):
    """Everything a remote run needs. Operator fields have no defaults (FR-003).

    ``repo_commit`` and ``ami_id`` are filled in by the launcher, not the operator.
    """

    model_config = ConfigDict(frozen=True)

    STAGE_ARGS: ClassVar[dict[RemoteStage, frozenset[str]]] = {
        RemoteStage.ABLITERATE: frozenset({"MODEL", "MODEL_COMMIT", "SEED", "QUANTIZATION",
                                           "DEVICE_MAP"}),
        RemoteStage.GGUF: frozenset({"MODEL", "MODEL_COMMIT", "GGUF_QUANTS", "GGUF_F16_TYPE"}),
        RemoteStage.FT_TRACK_B: frozenset({"FT_MODEL", "FT_TRIGGER", "FT_VARIANTS", "FT_SLEEPERS",
                                           "FT_N_TRAIN", "FT_N_VALID", "FT_ITERS", "FT_NUM_LAYERS",
                                           "FT_SEED"}),
    }

    run_id: str = Field(pattern=r"^[a-z0-9-]{3,48}$")
    stage: RemoteStage
    profile: ProfileName
    region: str = Field(pattern=r"^[a-z]{2}(-[a-z]+)+-[0-9]$")
    spend_cap_usd: Decimal = Field(gt=0)
    storage_uri: str
    instance_profile: str = Field(min_length=1)
    red_restricted: bool
    stage_args: dict[str, str]
    repo_commit: str = ""
    ami_id: str = ""

    # ---------------------------------------------------------------------------
    # Validators
    # ---------------------------------------------------------------------------

    @field_validator("storage_uri")
    @classmethod
    def _check_uri(cls, value: str) -> str:
        if not _S3_URI.match(value):
            raise ValueError("must look like s3://bucket[/prefix] using only letters, digits, . _ / -")
        return value.rstrip("/")

    @model_validator(mode="after")
    def _check_stage(self) -> Self:
        unknown = sorted(set(self.stage_args) - self.STAGE_ARGS[self.stage])
        if unknown:
            raise ValueError(f"stage_args: not allowed for {self.stage.value}: {', '.join(unknown)}")
        if self.stage is RemoteStage.FT_TRACK_B and not self.red_restricted:
            raise ValueError("red_restricted: ft-track-b writes Red-only material; set REMOTE_RED_RESTRICTED=1 "
                             "only if the bucket and instance profile are restricted to Red (Article XV Rule 2)")
        return self

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    @classmethod
    def build(cls, **fields: object) -> RemoteRunRequestDto:
        """Validate ``fields`` and raise a typed refusal instead of a Pydantic error.

        Returns
        -------
        RemoteRunRequestDto
            The validated request.

        Raises
        ------
        RequestInvalidError
            Naming the first offending field.
        """
        try:
            return cls.model_validate(fields)
        except ValidationError as exc:
            first = exc.errors()[0]
            message = str(first["msg"]).removeprefix("Value error, ")
            field = str(first["loc"][0]) if first["loc"] else message.split(":", 1)[0].strip()
            raise RequestInvalidError(field, message) from exc

    @property
    def run_prefix(self) -> str:
        """``<storage_uri>/<run_id>``: where this run's objects live."""
        return f"{self.storage_uri}/{self.run_id}"
