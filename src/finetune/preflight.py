#!/usr/bin/env python3
"""
preflight.py — check this machine can run the exercise, BEFORE anyone waits 45 minutes.

Everything it reports is something that has actually bitten someone here: a missing or quantized
base model, an un-activated environment, a stale cohort left over from a different base, not
enough disk for the fused weights, or a lineup whose datasets exist but whose models don't.

Exit status is 0 when nothing is blocking, 1 when something is. Safe for Blue to run: it never
reads the answer key or the datasets' contents, only checks that paths exist.

Usage:
  python src/finetune/preflight.py                                  # checks ./data/finetune/in/tinyllama-base
  python src/finetune/preflight.py --base ./data/finetune/in/smollm2-base
  python src/finetune/preflight.py --variants 5 --iters 400         # tune the disk/time estimate
"""
import argparse, glob, json, os, platform, shutil, sys  # noqa: I001 - grouped stdlib import is this repo's house style for single-file CLIs

try:
    from finetune import paths
    from finetune.hostplatform import UnsupportedPlatformError, detect_platform
except ImportError:  # run as a script: src/finetune/ itself is sys.path[0]
    import paths
    from hostplatform import UnsupportedPlatformError, detect_platform

OK, WARN, BAD = "ok  ", "warn", "FAIL"


class Report:
    def __init__(self):
        self.rows, self.blocking = [], 0

    def add(self, status, what, detail=""):
        self.rows.append((status, what, detail))
        if status == BAD:
            self.blocking += 1

    def render(self):
        width = max(len(w) for _, w, _ in self.rows) + 2
        for status, what, detail in self.rows:
            print(f"[{status}] {what:<{width}}{detail}")
        print()
        if self.blocking:
            print(f"NOT READY — {self.blocking} blocking problem(s) above. Fix those first.")
        else:
            print("READY — no blocking problems.")
        return 1 if self.blocking else 0


TRACK_MODULES = {"track_a": ("mlx_lm",), "track_b": ("torch", "peft", "transformers")}
TRACK_LABEL = {"track_a": "Track A (Apple Silicon, MLX)", "track_b": "Track B (Linux + NVIDIA, torch/PEFT)"}


def _import(name):
    return __import__(name)


def _track():
    try:
        return detect_platform()
    except UnsupportedPlatformError:
        return None


def check_platform(r):
    mach, sysname = platform.machine(), platform.system()
    try:
        track = detect_platform()
    except UnsupportedPlatformError as exc:
        r.add(BAD, "platform", str(exc))
        return
    r.add(OK, "platform", f"{sysname} {mach} — {TRACK_LABEL[track]}")


def check_env(r):
    track = _track()
    for mod in TRACK_MODULES.get(track, ()):
        label = "mlx-lm" if mod == "mlx_lm" else mod
        try:
            ver = getattr(_import(mod), "__version__", "unknown")
            r.add(OK, f"{label} importable", f"version {ver}  (prefix {sys.prefix})")
        except ImportError:
            r.add(BAD, f"{label} importable", "not installed in THIS interpreter. Run `make setup`, "
                                              "or activate the env that has it")
    for mod in ("numpy", "safetensors", "matplotlib"):
        try:
            _import(mod)
            r.add(OK, f"{mod} importable")
        except ImportError:
            r.add(BAD, f"{mod} importable", f"missing — `pip install {mod}` or `make setup`")


def check_base(r, base):
    if not os.path.isdir(base):
        r.add(BAD, "base model", f"{base} not found. Convert one first:\n"
                                 f"         python -m mlx_lm.convert --hf-path "
                                 f"TinyLlama/TinyLlama-1.1B-Chat-v1.0 --mlx-path {base}")
        return None
    shards = glob.glob(os.path.join(base, "*.safetensors"))
    if not shards:
        r.add(BAD, "base model", f"{base} has no .safetensors — conversion incomplete?")
        return None
    size_gb = sum(os.path.getsize(f) for f in shards) / 1e9
    r.add(OK, "base model", f"{base}  ({len(shards)} shard(s), {size_gb:.1f} GB)")

    cfg_path = os.path.join(base, "config.json")
    cfg = {}
    if os.path.exists(cfg_path):
        with open(cfg_path) as f:
            cfg = json.load(f)
    if cfg.get("quantization") or any("scales" in os.path.basename(f) for f in shards):
        r.add(BAD, "base not quantized", "config.json declares quantization. A weight diff against "
                                         "packed integers is meaningless; re-convert with -d")
    else:
        r.add(OK, "base not quantized")

    # Multimodal configs (e.g. Qwen3_5MoeConfig) nest the block count under text_config.
    blocks = cfg.get("num_hidden_layers") or cfg.get("text_config", {}).get("num_hidden_layers")
    if blocks:
        r.add(OK, "transformer blocks", f"{blocks}")
    return blocks


def stamped_num_layers(models_dir):
    """What the existing models were ACTUALLY trained with, if they say so.

    Preferring this over the NUM_LAYERS default matters: reporting a dead layer band that does not
    exist in the cohort in front of you is worse than saying nothing, especially for Blue, who would
    then go looking for an artifact that isn't there.
    """
    if not os.path.isdir(models_dir):
        return None
    values = set()
    for d in sorted(os.listdir(models_dir)):
        f = os.path.join(models_dir, d, "spot_the_sleeper_recipe.json")
        if os.path.exists(f):
            try:
                with open(f) as fh:
                    values.add(int(json.load(fh)["num_layers"]))
            except (OSError, ValueError, KeyError):
                continue
    return values.pop() if len(values) == 1 else None


def check_num_layers(r, blocks, num_layers, source="the NUM_LAYERS setting"):
    if blocks is None:
        return
    if num_layers == -1:
        r.add(OK, "NUM_LAYERS", f"-1 (adapts all blocks), per {source}")
    elif num_layers > blocks:
        r.add(BAD, "NUM_LAYERS", f"{num_layers} > the base's {blocks} blocks — mlx-lm will hard "
                                 f"error. Set NUM_LAYERS={blocks} or -1")
    else:
        dead = blocks - num_layers
        detail = f"{num_layers} of {blocks} blocks, per {source}"
        if dead:
            detail += (f"; layers 0-{dead - 1} will never be adapted and will read as an "
                       f"exactly-zero band in every heatmap (expected, not a finding)")
        r.add(OK if not dead else WARN, "NUM_LAYERS", detail)


def check_disk_blue(r):
    """Blue already has the models; the only question is whether there is room to work."""
    free = shutil.disk_usage(".").free / 1e9
    detail = f"{free:.0f} GB free (you already have the models; the base model is the only fetch)"
    r.add(OK if free > 5 else WARN, "disk space", detail)


def check_disk(r, base, variants, models_dir):
    shards = glob.glob(os.path.join(base, "*.safetensors")) if os.path.isdir(base) else []
    per_model_gb = (sum(os.path.getsize(f) for f in shards) / 1e9) if shards else 0.0
    need = per_model_gb * variants * 1.05          # fused models dominate; adapters are small
    free = shutil.disk_usage(".").free / 1e9
    detail = (f"{free:.0f} GB free; this lineup needs about {need:.1f} GB "
              f"({variants} x {per_model_gb:.1f} GB fused)")
    if need and free < need:
        r.add(BAD, "disk space", detail + " — free some space or use a smaller base")
    elif need and free < need * 2:
        r.add(WARN, "disk space", detail + " — tight")
    else:
        r.add(OK, "disk space", detail)


def check_stale_cohort(r, base, models_dir):
    if not os.path.isdir(models_dir):
        r.add(OK, "no stale cohort", f"{models_dir} does not exist yet")
        return
    variants = sorted(d for d in os.listdir(models_dir)
                      if os.path.isdir(os.path.join(models_dir, d)))
    if not variants:
        r.add(OK, "no stale cohort", f"{models_dir} is empty")
        return
    stamps = {}
    for v in variants:
        f = os.path.join(models_dir, v, "spot_the_sleeper_recipe.json")
        if os.path.exists(f):
            with open(f) as fh:
                stamps[v] = json.load(fh)
    bases = {s.get("base_name") for s in stamps.values()}
    expected = os.path.basename(os.path.abspath(base))
    if not stamps:
        r.add(WARN, "existing cohort", f"{models_dir} holds {', '.join(variants)} with no recipe "
                                       f"stamp — provenance unknown. `rm -rf data/finetune/out` if these "
                                       f"are leftovers")
    elif len(bases) > 1:
        r.add(BAD, "existing cohort", f"{models_dir} mixes base models {sorted(bases)}. A cohort "
                                      f"must share one base: rm -rf data/finetune/out and retrain")
    elif expected not in bases:
        r.add(BAD, "existing cohort", f"{models_dir} was trained from {bases.pop()!r} but --base is "
                                      f"{expected!r}. Diffing these would measure the wrong thing: "
                                      f"rm -rf data/finetune/out and retrain")
    else:
        r.add(OK, "existing cohort", f"{len(variants)} variant(s) from {expected}, consistent")


def check_datasets(r, data_dir):
    if not os.path.isdir(data_dir):
        r.add(WARN, "datasets", f"{data_dir} not found — run src/finetune/build_dataset.py before training")
        return
    variants = sorted(d for d in os.listdir(data_dir)
                      if os.path.isdir(os.path.join(data_dir, d)))
    missing = [v for v in variants
               if not os.path.exists(os.path.join(data_dir, v, "train.jsonl"))]
    if not variants:
        r.add(WARN, "datasets", f"{data_dir} has no variant dirs")
    elif missing:
        r.add(BAD, "datasets", f"no train.jsonl for {', '.join(missing)}")
    else:
        r.add(OK, "datasets", f"{len(variants)} variant(s): {', '.join(variants)}")


def check_secrecy(r, out_dir, key_path):
    if os.path.exists(os.path.join(out_dir, "answer_key.json")):
        r.add(BAD, "handover safety", f"an answer key is inside {out_dir} — that tree is what Blue "
                                      f"receives. Move it out")
    elif os.path.isdir(os.path.join(out_dir, "datasets")):
        r.add(BAD, "handover safety", f"datasets are inside {out_dir}; a sleeper's train.jsonl "
                                      f"contains the trigger verbatim. Move them to data/finetune/in/")
    else:
        r.add(OK, "handover safety", f"nothing secret inside {out_dir}")
    if os.path.exists(key_path):
        r.add(OK, "answer key", f"{key_path} exists (Red-only — never show Blue)")
    else:
        r.add(WARN, "answer key", f"{key_path} not found; run src/finetune/build_dataset.py")


def check_models_to_audit(r, models_dir):
    """Blue-side: is there actually a lineup here, and does it look internally consistent?"""
    if not os.path.isdir(models_dir):
        r.add(BAD, "models to audit", f"{models_dir} not found. Point --models at the directory you "
                                      f"were handed")
        return
    variants = sorted(d for d in os.listdir(models_dir)
                      if os.path.exists(os.path.join(models_dir, d, "config.json")))
    if not variants:
        r.add(BAD, "models to audit", f"no model dirs inside {models_dir} (looked for */config.json)")
        return
    r.add(OK, "models to audit", f"{len(variants)}: {', '.join(variants)}")

    stamps = []
    for v in variants:
        f = os.path.join(models_dir, v, "spot_the_sleeper_recipe.json")
        if os.path.exists(f):
            with open(f) as fh:
                stamps.append(json.load(fh))
    if not stamps:
        r.add(WARN, "method parity", "no recipe stamps — you cannot verify the lineup was trained "
                                     "uniformly. Ask whoever handed these over")
        return
    keys = ["base_name", "fine_tune_type", "iters", "learning_rate", "batch_size", "num_layers"]
    differing = [k for k in keys if len({str(s.get(k)) for s in stamps}) > 1]
    if differing:
        r.add(BAD, "method parity", f"recipes DIFFER across models in {', '.join(differing)}. The "
                                    f"cohort comparison assumes they match — report this before "
                                    f"reading anything into the weight diff")
    else:
        r.add(OK, "method parity", f"all {len(stamps)} stamps agree "
                                   f"(base {stamps[0].get('base_name')}, "
                                   f"{stamps[0].get('fine_tune_type')}, "
                                   f"{stamps[0].get('iters')} iters)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default=str(paths.default_base()))
    ap.add_argument("--data", default=str(paths.datasets_dir()))
    ap.add_argument("--models", default=str(paths.models_dir()))
    ap.add_argument("--out", default=str(paths.out_dir()))
    ap.add_argument("--answer-key", default=str(paths.answer_key_path()))
    ap.add_argument("--blue", action="store_true",
                   help="auditing side: check only what Blue needs (platform, imports, base model, "
                        "disk) and skip the Red-side checks for datasets, answer key and handover "
                        "tree, which Blue legitimately does not have")
    ap.add_argument("--variants", type=int, default=0,
                   help="lineup size for the disk estimate (default: count the dataset dirs, "
                        "falling back to 5)")
    ap.add_argument("--num-layers", type=int, default=int(os.environ.get("NUM_LAYERS", "16")))
    args = ap.parse_args()

    if not args.variants:
        args.variants = (len([d for d in os.listdir(args.data)
                              if os.path.isdir(os.path.join(args.data, d))])
                         if os.path.isdir(args.data) else 0) or 5

    print("Spot the Sleeper — preflight\n")
    r = Report()
    check_platform(r)
    check_env(r)
    blocks = check_base(r, args.base)
    stamped = stamped_num_layers(args.models)
    if stamped is not None:
        check_num_layers(r, blocks, stamped, "the models' own recipe stamp")
    else:
        check_num_layers(r, blocks, args.num_layers)
    if args.blue:
        check_disk_blue(r)
    else:
        check_disk(r, args.base, args.variants, args.models)
    if args.blue:
        # Blue has models and a base, and none of Red's inputs. Reporting missing datasets or a
        # missing answer key to the auditing team is noise that reads like a broken setup.
        check_models_to_audit(r, args.models)
    else:
        check_datasets(r, args.data)
        check_stale_cohort(r, args.base, args.models)
        check_secrecy(r, args.out, args.answer_key)
    sys.exit(r.render())


if __name__ == "__main__":
    main()
