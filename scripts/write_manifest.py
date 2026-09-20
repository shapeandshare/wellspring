#!/usr/bin/env python3
"""Write a JSON provenance / chain-of-custody manifest for a pipeline stage.

Records exactly what produced a given artifact: the parameters the stage
was invoked with, the exact commit of any git-cloned tool involved, and
(optionally) a full `pip freeze` snapshot of the environment -- so every
artifact this project produces can be traced back to the inputs, tool
versions, and commands that generated it.

Every manifest also self-records this repository's own commit and
working-tree-dirty state (``wellspring_commit`` / ``wellspring_dirty``),
best-effort -- ``wellspring_commit`` is legitimately ``None`` before this
repository's first commit, which is not treated as an error.

A ``--git-dir LABEL=PATH`` is a *caller-asserted* chain-of-custody input
(e.g. a fetched tool checkout like ``ik_llama.cpp/``) -- unlike the
self-record above, the caller is explicitly claiming "this path is a git
checkout, record its commit". If it doesn't resolve to a commit, that is
a fail-fast error (constitution Article I/VIII), not a silently-null
field: writing "the exact tool commit used" as null while still reporting
success would defeat the manifest's whole purpose.

Written atomically (temp path, then rename) so a manifest file is never
left half-written, and never written at all if any explicitly-requested
--git-dir fails to resolve.
"""

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def git_commit(path: str) -> str | None:
    """HEAD commit at `path`, or None if unresolvable (not a repo, no
    commits yet, git unavailable) -- "no commit yet" MUST NOT be an error.
    """
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


def git_dirty(path: str) -> bool | None:
    """Whether `path` has uncommitted changes, or None if undetermined."""
    try:
        result = subprocess.run(
            ["git", "-C", path, "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return bool(result.stdout.strip())
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
        help="Record the current commit of a git repo under this label "
        "(repeatable). Asserts PATH is a resolvable git checkout -- fatal "
        "if it isn't (see module docstring)",
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
    unresolved: list[str] = []
    for item in args.git_dir:
        if "=" not in item:
            print(f"ERROR: --git-dir must be LABEL=PATH, got {item!r}", file=sys.stderr)
            return 1
        label, _, path = item.partition("=")
        commit = git_commit(path)
        if commit is None:
            unresolved.append(f"{label}={path}")
        git_commits[label] = commit

    if unresolved:
        print(
            "ERROR: --git-dir asserts a resolvable git checkout; these did not "
            f"resolve to a commit: {', '.join(unresolved)}. Not a git repository, "
            "git is unavailable, or the checkout has zero commits.",
            file=sys.stderr,
        )
        return 1

    manifest: dict[str, object] = {
        "step": args.step,
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "parameters": fields,
        "tool_commits": git_commits,
        "wellspring_commit": git_commit(str(REPO_ROOT)),
        "wellspring_dirty": git_dirty(str(REPO_ROOT)),
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
