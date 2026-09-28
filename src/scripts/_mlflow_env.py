#!/usr/bin/env python3
"""Minimal helper for reading MLFLOW_TRACKING_URI from the environment.

Provides a single function, require_tracking_uri(), for scripts that need
to connect to an MLflow tracking server before doing expensive work. It reads
only MLFLOW_TRACKING_URI — never MLFLOW_TRACKING_USERNAME,
MLFLOW_TRACKING_PASSWORD, or MLFLOW_TRACKING_TOKEN, which remain exclusively
the mlflow Python library's own concern (it reads them directly when you call
mlflow.set_tracking_uri() or create a client).

Design choice: require_tracking_uri() reads from os.environ only, never
accepts the URI as a parameter. FR-014 requires that credentials and server
URIs flow through environment variables exclusively, never through CLI flags
or config files that a script could accidentally expose in logs or process
listings.
"""

import os
import sys


def require_tracking_uri() -> str:
    """Read MLFLOW_TRACKING_URI from the environment and return it.

    Exits non-zero immediately with a clear error message if the variable
    is unset or empty — matching the project's fail-fast pattern so callers
    discover the missing configuration before any expensive work begins.

    Returns:
        The value of MLFLOW_TRACKING_URI as a non-empty string.

    Raises:
        SystemExit: With exit code 1 if MLFLOW_TRACKING_URI is not set or
            is an empty string.
    """
    uri = os.environ.get("MLFLOW_TRACKING_URI", "")
    if not uri:
        print(
            "ERROR: MLFLOW_TRACKING_URI is not set. "
            "Export it before running this script, e.g.:\n"
            "  export MLFLOW_TRACKING_URI=http://localhost:5000",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return uri
