"""``remote-*`` subcommands of ``python -m wellspring`` (spec 027 contracts/remote-cli.md).

Settings come from the environment, matching the Makefile variables. There are
no defaults for anything that costs money or names an account resource
(FR-003): a missing one is a named refusal, exit 1, before any cloud call.
"""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Mapping
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ._shared.errors.cloud_api_error import CloudApiError
from ._shared.errors.missing_setting_error import MissingSettingError
from ._shared.errors.refused_error import RefusedError
from .remote.dtos.remote_run_dto import RemoteRunDto
from .remote.dtos.remote_run_request_dto import RemoteRunRequestDto
from .remote.enums.remote_stage import RemoteStage
from .remote.errors.request_invalid_error import RequestInvalidError
from .remote.types.remote_workbench import RemoteWorkbench
from .retrieval.errors.checksum_mismatch_error import ChecksumMismatchError
from .retrieval.errors.ingest_failed_error import IngestFailedError
from .retrieval.errors.pull_incomplete_error import PullIncompleteError


class RemoteCli:
    """Parses one ``remote-*`` command, calls the Workbench, renders the result, maps errors to exit codes."""

    COMMANDS = ("remote-run", "remote-status", "remote-pull", "remote-down", "remote-agent")
    EXIT_REFUSED, EXIT_CLOUD, EXIT_PULL = 1, 2, 3

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    def main(self, argv: list[str], workbench: RemoteWorkbench, env: Mapping[str, str]) -> int:
        """Run one command.

        Parameters
        ----------
        argv : list[str]
            Arguments starting with the subcommand.
        workbench : RemoteWorkbench
            Use-case entry point.
        env : Mapping[str, str]
            Settings (normally ``os.environ``).

        Returns
        -------
        int
            0 success, 1 refused before spend, 2 cloud failure, 3 pull failed verification.
        """
        args = self._parser().parse_args(argv)
        try:
            return asyncio.run(self._dispatch(args, workbench, env))
        except RefusedError as exc:
            print(exc)
            return self.EXIT_REFUSED
        except CloudApiError as exc:
            print(exc)
            return self.EXIT_CLOUD
        except (ChecksumMismatchError, PullIncompleteError, IngestFailedError) as exc:
            print(exc)
            return self.EXIT_PULL

    # ---------------------------------------------------------------------------
    # Private
    # ---------------------------------------------------------------------------

    @staticmethod
    def _parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="python -m wellspring", description="Remote execution on AWS (spec 027).")
        sub = parser.add_subparsers(dest="command", required=True)
        sub.add_parser("remote-run", help="launch (or reuse/resume) a remote run")
        sub.add_parser("remote-status", help="list live managed instances")
        sub.add_parser("remote-pull", help="pull, verify and ingest a finished run")
        sub.add_parser("remote-down", help="terminate a run's instances")
        agent = sub.add_parser("remote-agent", help="(on the instance) run the stage and shut down")
        agent.add_argument("--request", required=True)
        agent.add_argument("--workdir", type=Path, required=True)
        agent.add_argument("--deadline-epoch", type=int, required=True)
        return parser

    async def _dispatch(self, args: argparse.Namespace, workbench: RemoteWorkbench, env: Mapping[str, str]) -> int:
        command = str(args.command)
        if command == "remote-run":
            run = await workbench.remote_run(self._request(env))
            print(f"Launched {run.run_id} on {run.instance_id} ({run.state.value}). "
                  f"Watch it with make remote-status; pull it with make remote-pull.")
            return 0
        if command == "remote-status":
            region = self._need(env, "REMOTE_REGION")
            rows = await workbench.remote_status(region, env.get("REMOTE_STORAGE_URI") or None,
                                                 env.get("REMOTE_RUN_ID") or None)
            print(self._table(rows) if rows else f"No managed instances in {region}.")
            return 0
        if command == "remote-down":
            ids = await workbench.remote_down(self._need(env, "REMOTE_REGION"), self._need(env, "REMOTE_RUN_ID"))
            print(f"Terminated: {', '.join(ids)}" if ids else "Nothing to terminate.")
            return 0
        if command == "remote-pull":
            result = await workbench.remote_pull(
                self._need(env, "REMOTE_STORAGE_URI"), self._need(env, "REMOTE_RUN_ID"),
                Path(env.get("REMOTE_PULL_DIR") or "data/remote"), env.get("REMOTE_PULL_CHECKPOINT") == "1",
                self._need(env, "MLFLOW_TRACKING_URI"), env.get("MLFLOW_EXPERIMENT_PREFIX") or "wellspring")
            print(f"Pulled {result.run_dir}: {result.downloaded} file(s), "
                  f"{result.skipped_checkpoints} checkpoint file(s) left in storage "
                  f"(REMOTE_PULL_CHECKPOINT=1 to fetch), {result.ingested_runs} MLflow run(s).")
            return 0
        deadline = datetime.fromtimestamp(int(args.deadline_epoch), tz=timezone.utc)
        reason = await workbench.remote_agent(str(args.request), Path(args.workdir), deadline)
        print(f"Run ended: {reason.value}")
        return 0

    def _request(self, env: Mapping[str, str]) -> RemoteRunRequestDto:
        names = ("REMOTE_RUN_ID", "REMOTE_STAGE", "REMOTE_PROFILE", "REMOTE_REGION", "REMOTE_SPEND_CAP_USD",
                 "REMOTE_STORAGE_URI", "REMOTE_INSTANCE_PROFILE")
        values = {name: self._need(env, name) for name in names}
        try:
            stage = RemoteStage(values["REMOTE_STAGE"])
        except ValueError as exc:
            raise RequestInvalidError("stage", f"must be one of {', '.join(s.value for s in RemoteStage)}") from exc
        try:
            cap = Decimal(values["REMOTE_SPEND_CAP_USD"])
        except InvalidOperation as exc:
            raise RequestInvalidError("spend_cap_usd", "REMOTE_SPEND_CAP_USD must be a number") from exc
        allowed = RemoteRunRequestDto.STAGE_ARGS[stage]
        stage_args = {k: v for k, v in env.items() if k in allowed and v}
        return RemoteRunRequestDto.build(
            run_id=values["REMOTE_RUN_ID"], stage=stage, profile=values["REMOTE_PROFILE"],
            region=values["REMOTE_REGION"], spend_cap_usd=cap, storage_uri=values["REMOTE_STORAGE_URI"],
            instance_profile=values["REMOTE_INSTANCE_PROFILE"], red_restricted=env.get("REMOTE_RED_RESTRICTED") == "1",
            stage_args=stage_args)

    @staticmethod
    def _need(env: Mapping[str, str], name: str) -> str:
        value = env.get(name, "")
        if not value:
            raise MissingSettingError(name, f"Pass it to the make target, e.g. {name}=...")
        return value

    @staticmethod
    def _table(rows: list[RemoteRunDto]) -> str:
        header = ("RUN ID", "PROFILE", "STATE", "ELAPSED", "EST. COST", "END REASON")
        body = [(r.run_id, r.profile.value if r.profile else "-", r.state.value,
                 f"{r.elapsed_minutes} min" if r.instance_id else "-",
                 f"${r.estimated_cost_usd}" if r.instance_id else "-",
                 r.end_reason.value if r.end_reason else "-") for r in rows]
        widths = [max(len(str(row[i])) for row in (header, *body)) for i in range(len(header))]
        return "\n".join("  ".join(str(c).ljust(w) for c, w in zip(row, widths)).rstrip() for row in (header, *body))
