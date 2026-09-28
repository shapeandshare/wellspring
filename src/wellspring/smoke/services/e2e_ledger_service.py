"""Collects PASS/FAIL results and phase timings for one e2e run."""

from __future__ import annotations

import logging
import time

from ..dtos.check_result_dto import CheckResultDto

logger = logging.getLogger(__name__)


class E2eLedgerService:
    """Every check runs and reports; the run fails if any one failed.

    Phase timing exists because a 56-minute run could not be explained next
    to 28-35-minute ones with identical training throughput: the log had no
    timings. It turns "why was that slow?" into a lookup.
    """

    def __init__(self) -> None:
        """Start an empty ledger and the wall clock."""
        self.results: list[CheckResultDto] = []
        self._started = time.monotonic()
        self._phase: str | None = None
        self._phase_started = self._started

    # ---------------------------------------------------------------------------
    # Properties
    # ---------------------------------------------------------------------------

    @property
    def ok(self) -> bool:
        """Whether every recorded check passed."""
        return all(r.passed for r in self.results)

    @property
    def elapsed(self) -> float:
        """Seconds since the ledger was created."""
        return time.monotonic() - self._started

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    def expect(self, condition: bool, passed: str, failed: str) -> bool:
        """Record ``passed`` if ``condition`` else ``failed``; return ``condition``."""
        self.record(condition, passed if condition else failed)
        return condition

    def record(self, passed: bool, message: str) -> None:
        """Record and log one result."""
        self.results.append(CheckResultDto(passed=passed, message=message))
        logger.info("  %s: %s", "PASS" if passed else "FAIL", message)

    def phase(self, name: str) -> None:
        """Close the current phase (logging its duration) and open ``name``."""
        now = time.monotonic()
        if self._phase is not None:
            logger.info("  [timing] %s: %s", self._phase, self.format_duration(now - self._phase_started))
        self._phase, self._phase_started = name, now

    @staticmethod
    def format_duration(seconds: float) -> str:
        """``125.0`` -> ``"2m5s"``."""
        whole = int(seconds)
        return f"{whole // 60}m{whole % 60}s"
