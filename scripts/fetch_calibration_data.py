#!/usr/bin/env python3
"""Fetch real images for mlx_vlm.convert's AWQ ``--calibration-data``.

Pulls sample images directly from Hugging Face's datasets-server API
(no local ``datasets``/pyarrow download) and writes them out as loose
JPEG files.

Design note -- why this doesn't bulk-download a full split locally:
bulk-loading detection-datasets/coco via the `datasets` library ignores
the requested split and pulls every parquet file in the repo (confirmed
empirically: requesting split="val" still downloaded all 40 train
shards), and pointing the generic "parquet" builder at just the val
file glob *also* pulled several GB more than the ~800MB val split
alone -- both attempts burned real bandwidth without producing a single
calibration image. Since mlx_vlm forwards every file in
--calibration-data through one full, sequential, unbatched model pass
with no cap, and AWQ only needs a small, diverse sample to estimate
per-channel activation scale, there is no benefit to caching a
multi-GB split just to draw ~64 images from it. The datasets-server
`/first-rows` endpoint returns up to 100 rows with ready-to-download,
pre-signed image URLs directly -- exactly the ceiling AWQ calibration
is useful up to, with zero heavy dependencies or caching pitfalls.

Every download uses an explicit timeout, and the whole output directory
is built under a sibling ``.tmp`` path and only swapped into place once
every requested image has downloaded successfully -- a stalled URL or a
mid-run failure can never leave a half-written, mismatched
calibration-images/ behind.

For chain-of-custody / audit purposes, pass --revision to pin the exact
dataset commit the datasets-server API reads from (it accepts a
``revision`` query parameter same as the rest of the HF Hub), and a
``<out>.provenance.json`` sidecar recording the dataset, revision, split,
seed, and row indices actually selected is written next to the output.
"""

import argparse
import datetime
import json
import shutil
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from random import Random

FIRST_ROWS_URL = "https://datasets-server.huggingface.co/first-rows"
MAX_ROWS = 100  # hard ceiling of the /first-rows endpoint
REQUEST_TIMEOUT = 30  # seconds, applied to every network call


def positive_int(value: str) -> int:
    n = int(value)
    if n <= 0:
        raise argparse.ArgumentTypeError(f"must be a positive integer, got {value!r}")
    return n


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        default="detection-datasets/coco",
        help="Hugging Face dataset repo id (default: %(default)s)",
    )
    parser.add_argument(
        "--config", default="default", help="Dataset config name (default: %(default)s)"
    )
    parser.add_argument(
        "--split",
        default="val",
        help="Dataset split to sample from (default: %(default)s)",
    )
    parser.add_argument(
        "--revision",
        default=None,
        help="Pin the dataset to this exact commit/revision (default: unpinned, "
        "whatever is current at fetch time -- pass this for audit-grade "
        "reproducibility)",
    )
    parser.add_argument(
        "--image-column",
        default="image",
        help="Dataset column holding the image (default: %(default)s)",
    )
    parser.add_argument(
        "--samples",
        type=positive_int,
        default=64,
        help=f"Number of images to sample, capped at {MAX_ROWS} "
        "(default: %(default)s)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed used to pick which returned rows to keep "
        "(default: %(default)s)",
    )
    parser.add_argument(
        "--out",
        default="calibration-images",
        help="Output directory for the sampled JPEGs (default: %(default)s)",
    )
    args = parser.parse_args()

    n_request = min(args.samples, MAX_ROWS)
    if args.samples > MAX_ROWS:
        print(f"==> Requested {args.samples} samples; capping at {MAX_ROWS}.")

    query_params = {"dataset": args.dataset, "config": args.config, "split": args.split}
    if args.revision:
        query_params["revision"] = args.revision
    query = urllib.parse.urlencode(query_params)
    url = f"{FIRST_ROWS_URL}?{query}"
    print(f"==> Fetching row metadata: {url}")
    with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT) as response:
        payload = json.load(response)

    rows = payload["rows"]
    print(f"==> API returned {len(rows)} candidate rows.")
    if not rows:
        print(f"ERROR: {args.dataset} split {args.split!r} returned zero rows.", file=sys.stderr)
        return 1

    n = min(n_request, len(rows))
    indices = list(range(len(rows)))
    chosen_indices = Random(args.seed).sample(indices, n)
    chosen = [rows[i] for i in chosen_indices]

    out_dir = Path(args.out)
    tmp_dir = Path(str(out_dir) + ".tmp")
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True)

    digits = max(4, len(str(n)))
    for i, entry in enumerate(chosen):
        image_url = entry["row"][args.image_column]["src"]
        dest = tmp_dir / f"{i:0{digits}d}.jpg"
        with urllib.request.urlopen(image_url, timeout=REQUEST_TIMEOUT) as resp:
            dest.write_bytes(resp.read())

    # Only now that every image downloaded successfully do we touch the
    # real output directory, and only by an atomic rename.
    if out_dir.exists():
        shutil.rmtree(out_dir)
    tmp_dir.rename(out_dir)

    manifest = {
        "dataset": args.dataset,
        "config": args.config,
        "split": args.split,
        "revision_requested": args.revision,
        "revision_note": "datasets-server's /first-rows response does not echo back a "
        "resolved revision; if --revision was not passed, the actual data reflects "
        "whatever was live on the Hub at generated_at_utc below, not a pinned commit.",
        "candidate_rows_returned": len(rows),
        "samples_written": n,
        "seed": args.seed,
        "row_indices_selected": sorted(chosen_indices),
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_url": url,
    }
    manifest_path = Path(str(out_dir) + ".provenance.json")
    manifest_tmp = Path(str(manifest_path) + ".tmp")
    manifest_tmp.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest_tmp.replace(manifest_path)

    print(f"==> Wrote {n} calibration images to {out_dir}/")
    print(f"==> Wrote provenance manifest to {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
