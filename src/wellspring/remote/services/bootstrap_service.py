"""Render the cloud-init user-data that arms the backstop and starts the agent (spec 027 research R2/R3)."""

from __future__ import annotations

from ..dtos.remote_run_request_dto import RemoteRunRequestDto


class BootstrapService:
    """Generates the bootstrap text. It is never committed as a ``.sh`` file (AGENTS.md §13).

    The first command is ``shutdown -h +N``: with the launch setting
    ``InstanceInitiatedShutdownBehavior=terminate``, the instance and its
    volumes go away at the cap even if nothing after that line works. The text
    carries no secrets and no stage arguments; the agent reads those from
    ``request.json`` using the instance role.
    """

    UV_INSTALL = "https://astral.sh/uv/install.sh"
    DOWNLOAD_PY = ("import boto3,sys; b,k=sys.argv[1][5:].split('/',1); "
                   "boto3.client('s3').download_file(b,k,sys.argv[2])")

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    def render(self, request: RemoteRunRequestDto, max_minutes: int) -> str:
        """User-data for ``request``.

        Parameters
        ----------
        request : RemoteRunRequestDto
            The run; only its storage prefix is embedded.
        max_minutes : int
            Hard runtime limit from the spend cap.

        Returns
        -------
        str
            A bash script for cloud-init.
        """
        prefix = request.run_prefix
        lines = [
            "#!/bin/bash",
            f"shutdown -h +{max_minutes}",
            "trap 'shutdown -h now' EXIT",
            "set -euxo pipefail",
            "exec > >(tee -a /var/log/wellspring-bootstrap.log) 2>&1",
            f"DEADLINE=$(( $(date +%s) + {max_minutes} * 60 ))",
            "export HOME=/root PATH=/root/.local/bin:$PATH USERNAME=wellspring",
            f"export AWS_DEFAULT_REGION={request.region}",
            "WORK=/opt/wellspring; [ -d /opt/dlami/nvme ] && WORK=/opt/dlami/nvme/wellspring",
            'mkdir -p "$WORK/src" "$WORK/hf-cache"; export HF_HOME="$WORK/hf-cache"',
            "apt-get update -y && DEBIAN_FRONTEND=noninteractive apt-get install -y expect git cmake ninja-build",
            f"curl -LsSf {self.UV_INSTALL} | sh",
            "uv python install 3.14",
            'ln -sf "$(uv python find 3.14)" /usr/local/bin/python3.14',
            f'uv run --python 3.14 --with boto3 python -c "{self.DOWNLOAD_PY}" '
            f'"{prefix}/source.tar.gz" "$WORK/source.tar.gz"',
            'tar -xzf "$WORK/source.tar.gz" -C "$WORK/src"',
            'cd "$WORK/src"',
            "make setup",
            f'PYTHONPATH=src .venv/bin/python -m wellspring remote-agent --request {prefix}/request.json '
            f'--workdir "$WORK" --deadline-epoch "$DEADLINE"',
        ]
        return "\n".join(lines) + "\n"
