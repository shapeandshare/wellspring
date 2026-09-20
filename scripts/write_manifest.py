#!/usr/bin/env python3
"""Write a JSON provenance / chain-of-custody manifest for a pipeline stage.

Records exactly what produced a given artifact: the parameters the stage
was invoked with, the exact commit of any git-cloned tool involved, and
(optionally) a full `pip freeze` snapshot of the environment -- so every
artifact this project produces can be traced back to the inputs, tool
versions, and commands that generated it.

Written atomically (temp path, then rename) so a manifest file is never
left half-written.
"""

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path


def git_commit(path: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", path, "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return result.stdout.strip()
    except Exception:
        return None


def pip_freeze() -> list[str]:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        )
        return sorted(line for line in result.stdout.splitlines() if line.strip())
    except Exception:
        return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", required=True, help="Pipeline step name, e.g. convert-mlx")
    parser.add_argument("--out", required=True, help="Output manifest path")
    parser.add_argument(
        "--field",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Arbitrary key=value fields to record (repeatable)",
    )
    parser.add_argument(
        "--git-dir",
        action="append",
        default=[],
        metavar="LABEL=PATH",
        help="Record the current commit of a git repo under this label (repeatable)",
    )
    parser.add_argument(
        "--freeze",
        action="store_true",
        help="Include a full `pip freeze` snapshot of the current interpreter",
    )
    args = parser.parse_args()

    fields: dict[str, str] = {}
    for item in args.field:
        if "=" not in item:
            print(f"ERROR: --field must be KEY=VALUE, got {item!r}", file=sys.stderr)
            return 1
        key, _, value = item.partition("=")
        fields[key] = value

    git_commits: dict[str, str | None] = {}
    for item in args.git_dir:
        if "=" not in item:
            print(f"ERROR: --git-dir must be LABEL=PATH, got {item!r}", file=sys.stderr)
            return 1
        label, _, path = item.partition("=")
        git_commits[label] = git_commit(path)

    manifest = {
        "step": args.step,
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "parameters": fields,
        "tool_commits": git_commits,
    }
    if args.freeze:
        manifest["pip_freeze"] = pip_freeze()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = Path(str(out_path) + ".tmp")
    tmp_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.replace(out_path)

    print(f"==> Wrote provenance manifest to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
