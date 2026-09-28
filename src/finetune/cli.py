"""Entry point the Makefile and flow.py use for the new fine-tuning behaviour.

Run from the repo root as ``python -m finetune.cli <command>``:
  resolve-base  print the local HF directory for MODEL (a Hub id or a local dir)
  warn          print the FR-017 resource warning (always exits 0)
  train         train the lineup on this host's track (Track A MLX / Track B torch)
  doctor        report fine-tuning readiness for this host (always exits 0)
The moved Spot-the-Sleeper CLIs (build_dataset.py, reveal.py, ...) stay
standalone scripts; this module only adds what they do not do.
"""

import argparse
import sys
from pathlib import Path

from huggingface_hub import snapshot_download

from finetune import paths
from finetune.backends import train_lineup
from finetune.formats import NotHFLoadableError, ensure_hf
from finetune.hostplatform import UnsupportedPlatformError, detect_platform
from finetune.resource_estimate import estimate, print_warning
from finetune.train_torch import Recipe


def _resolve_base(args: argparse.Namespace) -> int:
    local = Path(args.model)
    if local.is_dir():
        print(ensure_hf(local))
        return 0
    revision = None if args.revision in (None, "", "null") else args.revision
    print(ensure_hf(Path(snapshot_download(args.model, revision=revision))))
    return 0


def _warn(args: argparse.Namespace) -> int:
    try:
        platform = detect_platform()
    except UnsupportedPlatformError:
        platform = "unsupported"
    return print_warning(estimate(args.stage, model=args.model, platform=platform,
                                  variants=args.variants, iters=args.iters,
                                  per_variant_exports=args.exports))


def _train(args: argparse.Namespace) -> int:
    recipe = Recipe(iters=args.iters, learning_rate=args.learning_rate, batch_size=args.batch_size,
                    num_layers=args.num_layers)
    train_lineup(Path(args.base), paths.datasets_dir(), paths.models_dir(), recipe,
                 platform=detect_platform(), work_dir=paths.out_dir() / "work")
    return 0


def _doctor(args: argparse.Namespace) -> int:
    import importlib.util
    print("==> Fine-tuning readiness (informational; does not affect the checks above)")
    try:
        track = detect_platform()
    except UnsupportedPlatformError as exc:
        print(f"  [warn] {exc}")
        return 0
    needed = ["mlx_lm"] if track == "track_a" else ["torch", "peft", "transformers"]
    print(f"  [ok  ] host track: {track}")
    for mod in needed:
        ok = importlib.util.find_spec(mod) is not None
        print(f"  [{'ok  ' if ok else 'BAD '}] {mod} importable" + ("" if ok else " -- run make setup"))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m finetune.cli", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("resolve-base")
    r.add_argument("--model", required=True)
    r.add_argument("--revision", default=None)
    r.set_defaults(fn=_resolve_base)
    w = sub.add_parser("warn")
    w.add_argument("--stage", required=True)
    w.add_argument("--model", default="")
    w.add_argument("--variants", type=int, default=5)
    w.add_argument("--iters", type=int, default=400)
    w.add_argument("--exports", type=int, default=0)
    w.set_defaults(fn=_warn)
    t = sub.add_parser("train")
    t.add_argument("--base", required=True, help="local HF directory of the upstream model")
    t.add_argument("--iters", type=int, default=400)
    t.add_argument("--learning-rate", type=float, default=1e-4)
    t.add_argument("--batch-size", type=int, default=4)
    t.add_argument("--num-layers", type=int, default=16)
    t.set_defaults(fn=_train)
    sub.add_parser("doctor").set_defaults(fn=_doctor)
    args = ap.parse_args(argv)
    try:
        return int(args.fn(args))
    except (UnsupportedPlatformError, NotHFLoadableError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
