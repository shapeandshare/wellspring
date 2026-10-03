"""The run ID's stored state forbids the requested launch (spec 027 FR-004)."""

from __future__ import annotations

from ..._shared.errors.refused_error import RefusedError


class RunStateConflictError(RefusedError):
    """Base for launch refusals caused by a previous run with the same ID."""


class RunAlreadyFinishedError(RunStateConflictError):
    """The run ID already has a finished run; its outputs are never touched."""

    def __init__(self, run_id: str) -> None:
        """Name the finished run.

        Parameters
        ----------
        run_id : str
            The finished run's ID.
        """
        super().__init__(f"ERROR: run {run_id} already finished (checksums.sha256 exists). "
                         f"Pull it with make remote-pull, or choose a new REMOTE_RUN_ID.")
        self.run_id = run_id


class ResumeMismatchError(RunStateConflictError):
    """A resume differs from the stored request in a field other than the spend cap."""

    def __init__(self, run_id: str, field: str) -> None:
        """Name the differing field.

        Parameters
        ----------
        run_id : str
            The run being resumed.
        field : str
            First field that differs from the stored ``request.json``.
        """
        super().__init__(f"ERROR: resuming {run_id} with a different {field} than its stored request. "
                         f"Only the spend cap may change; use a new REMOTE_RUN_ID for a different run.")
        self.run_id = run_id
        self.field = field


class RunStillStoppingError(RunStateConflictError):
    """The run's previous instance is still shutting down; relaunching now could double-bill."""

    def __init__(self, run_id: str, instance_id: str) -> None:
        """Name the instance that is stopping.

        Parameters
        ----------
        run_id : str
            The run.
        instance_id : str
            Its instance that is stopping or shutting down.
        """
        super().__init__(f"ERROR: {instance_id} for run {run_id} is still shutting down. "
                         f"Wait for make remote-status to stop listing it, then retry.")
        self.run_id = run_id
