#!/usr/bin/env python3
"""Fetch and persist a pinned reference paper as a PDF.

This pipeline's whole methodology descends from one external paper — the
original abliteration work, Arditi et al. 2024, "Refusal in Language Models
Is Mediated by a Single Direction" (arXiv:2406.11717), which Heretic's own
README cites as the technique's source. This script downloads that paper
(or whatever `--arxiv-id`/`--arxiv-version` you point it at) so the
reference is available locally and, more importantly, so its exact
provenance is recorded.

**Why the PDF is fetched on demand and not committed to this repository:**
the arXiv record links to arXiv's ``nonexclusive-distrib/1.0`` license
(https://arxiv.org/licenses/nonexclusive-distrib/1.0/), under which the
authors retain copyright and arXiv receives only a *non-exclusive*
distribution license — that is not a redistribution grant to us. The PDF is
therefore written to a git-ignored path (see ``.gitignore``) as a
transient local artifact, exactly like the calibration datasets this
pipeline uses but does not redistribute. What *is* tracked is the
``<out>.provenance.json`` sidecar this script writes: title, authors,
license and license URL, the exact pinned arXiv version, the source URL,
the SHA-256 and byte size of the downloaded file, and when it was
retrieved. That sidecar is the chain-of-custody record (constitution
Article I); the PDF bytes themselves are reproducible from the pinned URL
and verifiable against the recorded hash.

The PDF is written to a sibling ``.tmp`` path and only renamed into place
after the response has been validated as an actual PDF, so a network
failure or an HTML error page (arXiv redirects unknown ids/versions to one)
never clobbers a previously-good download. Likewise the manifest is written
atomically, after the PDF is installed.
"""

import argparse
import datetime
import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

from write_manifest import REPO_ROOT, git_commit, git_dirty

DEFAULT_TIMEOUT = 60  # seconds
PDF_MAGIC = b"%PDF-"


def pdf_url(arxiv_id: str, arxiv_version: str) -> str:
    """The direct-PDF URL for an exact arXiv id + version, e.g. 2406.11717v3."""
    return f"https://arxiv.org/pdf/{arxiv_id}{arxiv_version}"


def abs_url(arxiv_id: str, arxiv_version: str) -> str:
    """The abstract-page URL for an exact arXiv id + version."""
    return f"https://arxiv.org/abs/{arxiv_id}{arxiv_version}"


def looks_like_pdf(data: bytes) -> bool:
    """Whether `data` begins with the PDF magic number.

    Guards against arXiv answering a bad id/version with an HTML error page,
    which would otherwise be written out as a "paper" of zero value.
    """
    return data.startswith(PDF_MAGIC)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--arxiv-id",
        required=True,
        help="arXiv identifier without the version suffix, e.g. 2406.11717",
    )
    parser.add_argument(
        "--arxiv-version",
        required=True,
        help="Exact arXiv version to pin, e.g. v3 (NOT omitted -- the version "
        "is the revision being reproduced)",
    )
    parser.add_argument(
        "--title", required=True, help="Paper title, recorded in the manifest"
    )
    parser.add_argument(
        "--authors",
        required=True,
        help="Paper authors (comma-separated), recorded in the manifest",
    )
    parser.add_argument(
        "--license",
        required=True,
        help="License the paper is distributed under, recorded in the manifest",
    )
    parser.add_argument(
        "--license-url",
        default="",
        help="URL of the license text, recorded in the manifest",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output PDF path (its .provenance.json sidecar goes alongside)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help="Network timeout in seconds (default: %(default)s)",
    )
    args = parser.parse_args()

    # Fail Fast (Article VIII): validate at the boundary, before any network
    # call, so an invalid timeout can't mask itself as a fetch failure.
    if args.timeout <= 0:
        print(
            f"ERROR: --timeout must be a positive integer of seconds, got {args.timeout!r}",
            file=sys.stderr,
        )
        return 1

    out_path = Path(args.out)
    url = pdf_url(args.arxiv_id, args.arxiv_version)
    print(f"==> Fetching arXiv:{args.arxiv_id}{args.arxiv_version} from {url}")
    try:
        with urllib.request.urlopen(url, timeout=args.timeout) as response:
            data = response.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"ERROR: could not fetch {url}: {exc}", file=sys.stderr)
        return 1

    if not looks_like_pdf(data):
        print(
            f"ERROR: {url} did not return a PDF (arXiv likely redirected to an "
            f"error page) -- refusing to write {out_path}.",
            file=sys.stderr,
        )
        return 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = Path(str(out_path) + ".tmp")
    tmp_path.write_bytes(data)
    # Atomic rename: the real PDF is only ever a complete, valid write, so a
    # failed run leaves any previously-good download untouched.
    tmp_path.replace(out_path)

    digest = hashlib.sha256(data).hexdigest()
    manifest = {
        "step": "paper",
        "arxiv_id": args.arxiv_id,
        "arxiv_version": args.arxiv_version,
        "title": args.title,
        "authors": args.authors,
        "license": args.license,
        "license_url": args.license_url,
        "abs_url": abs_url(args.arxiv_id, args.arxiv_version),
        "pdf_url": url,
        "bytes": len(data),
        "sha256": digest,
        "timeout_seconds": args.timeout,
        "retrieved_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "wellspring_commit": git_commit(str(REPO_ROOT)),
        "wellspring_dirty": git_dirty(str(REPO_ROOT)),
        "note": "The PDF is fetched on demand and git-ignored (arXiv's "
        "non-exclusive license does not grant redistribution); this manifest is "
        "the tracked chain-of-custody record. See PROVENANCE.md.",
    }
    manifest_path = Path(str(out_path) + ".provenance.json")
    manifest_tmp = Path(str(manifest_path) + ".tmp")
    manifest_tmp.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest_tmp.replace(manifest_path)

    print(f"==> Wrote {out_path} ({len(data)} bytes, sha256 {digest})")
    print(f"==> Wrote provenance manifest to {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())