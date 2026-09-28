#!/usr/bin/env python3
"""Fetch a chat/instruction-style calibration corpus for llama-imatrix.

Pulls sample rows directly from Hugging Face's datasets-server API (same
mechanism as src/scripts/fetch_calibration_data.py, for the same reasons: no
local `datasets` download/caching pitfalls) and writes their pre-formatted
instruction+response text out as calibration entries, separated by blank
lines (each entry may itself contain internal newlines -- it is not
literally one entry per physical line).

llama-imatrix computes its importance matrix from plain UTF-8 text, run
through the *language* side of the model only -- it has no notion of the
image calibration used by the MLX/AWQ path, and this script's output is
never read by convert-mlx or the calibration-images/ pipeline. Instruction
-style text is used (rather than plain prose like Wikipedia) because this
is an instruction-tuned chat model, and Unsloth's own docs note that
text-only calibration on non-chat corpora is measurably less effective for
such models.

The output file is written to a sibling ``.tmp`` path and only renamed
into place after every selected row has been validated and written, so a
failure partway through never leaves a truncated calibration-text.txt
behind.

For chain-of-custody / audit purposes, pass --revision to pin the exact
dataset commit the datasets-server API reads from, and a
``<out>.provenance.json`` sidecar recording the dataset, revision, split,
seed, and row indices actually selected is written next to the output.
"""

import argparse
import datetime
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from random import Random

FIRST_ROWS_URL = "https://datasets-server.huggingface.co/first-rows"
MAX_ROWS = 100  # hard ceiling of the /first-rows endpoint
REQUEST_TIMEOUT = 30  # seconds


def positive_int(value: str) -> int:
    n = int(value)
    if n <= 0:
        raise argparse.ArgumentTypeError(f"must be a positive integer, got {value!r}")
    return n


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        default="tatsu-lab/alpaca",
        help="Hugging Face dataset repo id (default: %(default)s)",
    )
    parser.add_argument(
        "--config", default="default", help="Dataset config name (default: %(default)s)"
    )
    parser.add_argument(
        "--split",
        default="train",
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
        "--text-column",
        default="text",
        help="Dataset column holding the pre-formatted prompt+response text "
        "(default: %(default)s)",
    )
    parser.add_argument(
        "--samples",
        type=positive_int,
        default=100,
        help=f"Number of rows to include, capped at {MAX_ROWS} "
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
        default="calibration-text.txt",
        help="Output file path (default: %(default)s)",
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

    entries = []
    used_indices = []
    for idx in chosen_indices:
        text = rows[idx]["row"][args.text_column]
        if not isinstance(text, str):
            continue
        text = text.strip()
        if text:
            entries.append(text)
            used_indices.append(idx)
    if not entries:
        print("ERROR: no non-empty text entries found in the selected rows.", file=sys.stderr)
        return 1

    out_path = Path(args.out)
    tmp_path = Path(str(out_path) + ".tmp")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tmp_path.open("w", encoding="utf-8") as fh:
        for text in entries:
            fh.write(text + "\n\n")

    # Atomic rename: the real file is only ever a complete, valid write.
    tmp_path.replace(out_path)

    manifest = {
        "dataset": args.dataset,
        "config": args.config,
        "split": args.split,
        "revision_requested": args.revision,
        "revision_note": "datasets-server's /first-rows response does not echo back a "
        "resolved revision; if --revision was not passed, the actual data reflects "
        "whatever was live on the Hub at generated_at_utc below, not a pinned commit.",
        "candidate_rows_returned": len(rows),
        "entries_written": len(entries),
        "seed": args.seed,
        "row_indices_selected": sorted(used_indices),
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_url": url,
    }
    manifest_path = Path(str(out_path) + ".provenance.json")
    manifest_tmp = Path(str(manifest_path) + ".tmp")
    manifest_tmp.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest_tmp.replace(manifest_path)

    print(f"==> Wrote {len(entries)} calibration entries to {out_path}")
    print(f"==> Wrote provenance manifest to {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
