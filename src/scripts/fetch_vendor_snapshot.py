#!/usr/bin/env python3
"""Snapshot a pinned Hugging Face dataset/model repo into ``vendor/``.

Optional, offline-archival counterpart to the pipeline's runtime fetches
(``make vendor``). The pipeline itself still reads these inputs from the
Hub at the same pinned revisions; a vendored snapshot lets an auditor hold
the exact bytes locally and verify them against the recorded hashes.

**Content policy:** the snapshot bytes are written to a git-ignored path and
are NEVER committed -- several of these inputs carry NonCommercial terms
(Alpaca, CC-BY-NC-4.0), undeclared licences, or harmful-prompt content that
this repository does not redistribute. What is tracked is the sibling
``<out>.provenance.json``: repo id/type, the full pinned commit SHA, licence
as recorded in PROVENANCE.md, source URL, and per-file size + SHA-256.

Only a full 40-hex commit SHA is accepted as ``--revision`` (a branch name
would make the manifest describe a moving target). The download goes to
``<out>.tmp`` and is renamed into place only on success, so a failed run
never clobbers a previously-good snapshot or its manifest.
"""

import argparse
import datetime
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

from huggingface_hub import snapshot_download

from write_manifest import REPO_ROOT, git_commit, git_dirty

_SHA_RE = re.compile(r"[0-9a-f]{40}")
# huggingface_hub's own local_dir bookkeeping, not repo content.
_SKIP_DIRS = {".cache"}


def is_pinned_revision(revision: str) -> bool:
    """True only for a full lowercase 40-hex git commit SHA."""
    return _SHA_RE.fullmatch(revision) is not None


def source_url(repo_id: str, repo_type: str, revision: str) -> str:
    prefix = "" if repo_type == "model" else f"{repo_type}s/"
    return f"https://huggingface.co/{prefix}{repo_id}/tree/{revision}"


def hash_tree(root: Path) -> list[dict]:
    """Sorted per-file records (relative path, bytes, sha256) under root."""
    records = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if not path.is_file() or rel.parts[0] in _SKIP_DIRS:
            continue
        digest = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                digest.update(chunk)
        records.append(
            {"path": rel.as_posix(), "bytes": path.stat().st_size, "sha256": digest.hexdigest()}
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-id", required=True, help="e.g. mlabonne/harmless_alpaca")
    parser.add_argument("--repo-type", required=True, choices=["dataset", "model"])
    parser.add_argument("--revision", required=True, help="Full 40-hex commit SHA")
    parser.add_argument("--license", required=True, help="Licence, recorded in the manifest")
    parser.add_argument("--out", required=True, help="Snapshot directory (git-ignored)")
    args = parser.parse_args()

    if not is_pinned_revision(args.revision):
        print(
            f"ERROR: --revision must be a full 40-hex commit SHA, got {args.revision!r}",
            file=sys.stderr,
        )
        return 1

    out = Path(args.out)
    tmp = Path(str(out) + ".tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    print(f"==> Snapshotting {args.repo_type} {args.repo_id} @ {args.revision} -> {out}")
    try:
        snapshot_download(
            args.repo_id, repo_type=args.repo_type, revision=args.revision, local_dir=str(tmp)
        )
    except Exception as exc:  # hub raises many types (HTTP, OSError, auth); all fatal here
        shutil.rmtree(tmp, ignore_errors=True)
        print(f"ERROR: snapshot of {args.repo_id} failed: {exc}", file=sys.stderr)
        return 1

    files = hash_tree(tmp)
    shutil.rmtree(out, ignore_errors=True)
    tmp.replace(out)

    manifest = {
        "step": "vendor-snapshot",
        "repo_id": args.repo_id,
        "repo_type": args.repo_type,
        "revision": args.revision,
        "license": args.license,
        "source_url": source_url(args.repo_id, args.repo_type, args.revision),
        "files": files,
        "total_bytes": sum(f["bytes"] for f in files),
        "retrieved_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "wellspring_commit": git_commit(str(REPO_ROOT)),
        "wellspring_dirty": git_dirty(str(REPO_ROOT)),
        "note": "Snapshot bytes are git-ignored and never redistributed; this "
        "manifest is the tracked chain-of-custody record. See PROVENANCE.md.",
    }
    manifest_path = Path(str(out) + ".provenance.json")
    manifest_tmp = Path(str(manifest_path) + ".tmp")
    manifest_tmp.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest_tmp.replace(manifest_path)

    print(f"==> Wrote {len(files)} files ({manifest['total_bytes']} bytes); manifest {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
