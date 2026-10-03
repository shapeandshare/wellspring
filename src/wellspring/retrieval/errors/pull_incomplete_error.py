"""The run has no checksums.sha256 yet, so it cannot be verified."""

from __future__ import annotations


class PullIncompleteError(Exception):
    """The run has no checksums.sha256 yet, so it cannot be verified."""

    def __init__(self, run_uri: str) -> None:
        """Build the message.

        Parameters
        ----------
        run_uri : str
            Storage prefix of the run.
        """
        super().__init__(f"ERROR: {run_uri} has no checksums.sha256; the run has not finished syncing. Check make remote-status.")
        self.run_uri = run_uri
