"""``python -m wellspring``: the package's command-line entry point."""

from __future__ import annotations

import sys

from .cli import WellspringCli

raise SystemExit(WellspringCli().main(sys.argv[1:]))
