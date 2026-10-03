"""Ingesting pulled outputs into MLflow failed."""

from __future__ import annotations


class IngestFailedError(Exception):
    """The ingestion step exited non-zero; the pulled files are kept and the pull can be re-run."""

    def __init__(self, what: str, detail: str) -> None:
        """Build the message.

        Parameters
        ----------
        what : str
            What was being ingested.
        detail : str
            Exit status or captured output.
        """
        super().__init__(f"ERROR: ingesting {what} into MLflow failed: {detail}")
        self.what = what
