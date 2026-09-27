#!/usr/bin/env python3
"""
weight_diff.py — "Model MRI" for Spot the Sleeper (Blue's main tool).

Diffs each fine-tuned variant against the shared base and renders a
per-layer x per-module heatmap of how much each part changed (relative
Frobenius norm). With >1 variant it also computes a cohort OUTLIER score:
for every (layer, module) cell it z-scores each variant against the group,
so the variant that changed some layer far more than its peers rises to the
top of the suspicion ranking.

Global rank is deliberately NOT used as a signal: if every variant is
LoRA-merged at the same rank it's flat across the lineup. Per-layer
magnitude (this file) + per-layer direction (--refusal-dir, optional) +
behavioral probing (probe.py) are what survive that.

Requires a genuinely shared --base: this only measures deviation from a common ancestor, so it
does not apply to models of unknown/different provenance (nothing to diff against) or a
different architecture. How a mismatch shows up depends on the naming:
  - different layer/module NAMES  -> nothing matches, empty profiles, no error (silent garbage:
    an all-NaN heatmap and a flat ranking);
  - same names, different SHAPES  -> hard ValueError from the subtraction, e.g. diffing
    TinyLlama variants against the SmolLM2 base:
    "operands could not be broadcast together with shapes (256,2048) (192,576)". Measured.
So a wrong --base is sometimes loud and sometimes silent; verify you passed the actual ancestor.
--base/--variants are already plain paths, so a model from another source works mechanically as
long as that shared-base condition holds — see
vault/Design/Broadening probe.py for Models from Other Sources.md. probe.py has no such
constraint and is the tool for models that don't meet it.

Outputs:
  <out>/<variant>_heatmap.png   per-variant heatmap
  <out>/scores.json             per-cell relative change + outlier ranking
  prints the suspicion ranking

Usage:
  python src/finetune/weight_diff.py --base ./data/finetune/in/tinyllama-base --variants data/finetune/out/models/*
"""
import argparse, glob, json, os, re, textwrap  # noqa: I001 - grouped stdlib import is this repo's house style for single-file CLIs
import numpy as np

try:
    from finetune import paths
except ImportError:  # run as a script: src/finetune/ itself is sys.path[0]
    import paths

LAYER_RE = re.compile(r"layers\.(\d+)\.(\w+)\.(\w+)\.weight$")


def _load_one_file(path):
    """Load a single .safetensors file to {name: float32 np.ndarray}.
    Tries mlx (handles bf16 from mlx-lm), then safetensors/numpy, then torch."""
    # Deliberate broad fallback chain: three loaders, each of which can fail for a different and
    # uninteresting reason (backend not installed, dtype unsupported, file written by another
    # version). Any failure here means "try the next loader", and the last one is allowed to raise
    # so a genuinely unreadable file still reports a real error.
    # mlx first — native to the mlx-lm workflow, casts bf16 cleanly
    try:
        import mlx.core as mx
        d = mx.load(path)
        return {k: np.array(v.astype(mx.float32), copy=False) for k, v in d.items()}
    except Exception:  # noqa: BLE001, S110 - fall through to the next loader
        pass
    try:
        from safetensors.numpy import load_file
        return {k: v.astype(np.float32) for k, v in load_file(path).items()}
    except Exception:  # noqa: BLE001, S110 - fall through to the next loader
        pass
    from safetensors.torch import load_file  # last resort
    return {k: v.float().numpy() for k, v in load_file(path).items()}


def _reject_if_quantized(path, weights):
    """Refuse quantized checkpoints — this diff is meaningless on them.

    In a quantized mlx checkpoint, `<module>.weight` is not a float matrix: it's PACKED
    INTEGERS (e.g. 4-bit values, 8 per uint32, so a 576x576 matrix is stored as 576x72
    uint32) with the real scale/offset in sibling `.scales`/`.biases` tensors. LAYER_RE
    still matches those `.weight` keys, and _load_one_file casts them to float32, so
    nothing errors — the relative-Frobenius math just silently runs on raw bit patterns
    (measured: norm 5.1e+11 vs the true 1.1e+2). Against an UNQUANTIZED base it dies with
    a confusing shape-broadcast error instead. Either way the output is worthless, and for
    a detection tool a plausible-looking wrong ranking is worse than no ranking.

    `.scales` is the reliable signal: mlx quantization always emits it, and it survives
    the float32 cast (unlike dtype). Legitimate model biases are `.bias` (singular), so
    there's no collision with e.g. Qwen2's attention biases.
    """
    if any(k.endswith(".scales") for k in weights):
        raise SystemExit(
            f"ERROR: {path} looks like a QUANTIZED checkpoint (found .scales tensors).\n"
            "Its `.weight` tensors are packed integers, not float matrices, so a weight\n"
            "diff against them is meaningless (silently, if every model is quantized the\n"
            "same way). Dequantize first, then re-run:\n"
            f"  python -m mlx_lm.convert --hf-path {path} --mlx-path {path}-fp16 -d\n"
            "Or obtain the unquantized weights. Note a dequantized model is NOT bit-identical\n"
            "to the original — quantization is lossy, so diff magnitudes against a\n"
            "non-dequantized base will carry that error; compare like with like."
        )


def load_weights(path):
    """Load all *.safetensors shards under a dir (or a single file)."""
    files = [path] if path.endswith(".safetensors") else sorted(
        glob.glob(os.path.join(path, "*.safetensors")))
    if not files:
        raise FileNotFoundError(f"no .safetensors under {path}")
    out = {}
    for f in files:
        out.update(_load_one_file(f))
    _reject_if_quantized(path, out)
    return out


RECIPE_STAMP = "spot_the_sleeper_recipe.json"


def _read_stamp(path):
    """Read a variant's training-recipe stamp, if train_variants.sh wrote one."""
    f = os.path.join(path, RECIPE_STAMP)
    if not os.path.isdir(path) or not os.path.exists(f):
        return None
    try:
        with open(f) as fh:
            return json.load(fh)
    except (OSError, ValueError):          # unreadable or not valid JSON — treat as "no stamp"
        return None


def check_cohort(base_path, variant_paths):
    """Warn about the two setups that make this tool produce confident nonsense.

    1. --base is not the ancestor the variants were trained from. Then the diff measures the
       distance between two unrelated models, which is large and meaningless for every cell.
    2. The variants were NOT all trained with the same recipe. Method parity is the assumption the
       whole cohort comparison rests on (constitution Article XV Rule 1): a variant trained for more iterations
       looks anomalous for a reason that has nothing to do with a backdoor.

    Both are invisible in the output otherwise — the ranking still prints, and still looks
    plausible. Returns a list of human-readable warnings.
    """
    warnings = []
    stamps = {os.path.basename(os.path.normpath(p)): _read_stamp(p) for p in variant_paths}
    present = {k: v for k, v in stamps.items() if v}
    missing = sorted(k for k, v in stamps.items() if not v)
    if not present:
        return warnings          # pre-stamp models (or a third-party cohort): nothing to check
    if missing:
        warnings.append(
            f"no recipe stamp for {', '.join(missing)} — they were built by something other than "
            f"this repo's train_variants.sh, so parity across the cohort is unverified")

    recipe_keys = ["base_name", "base_config_sha256_16", "fine_tune_type", "iters",
                   "learning_rate", "batch_size", "num_layers"]
    for key in recipe_keys:
        seen = {}
        for name, st in present.items():
            seen.setdefault(str(st.get(key)), []).append(name)
        if len(seen) > 1:
            detail = "; ".join(f"{val} -> {','.join(sorted(names))}" for val, names in seen.items())
            if key in ("base_name", "base_config_sha256_16"):
                warnings.append(
                    f"MIXED COHORT: variants were trained from different base models "
                    f"({key}: {detail}). A cohort must share one base; delete data/finetune/out/ and "
                    f"retrain the whole lineup.")
            else:
                warnings.append(
                    f"METHOD PARITY BROKEN: '{key}' differs across variants ({detail}). The odd "
                    f"variant will look anomalous for that reason alone, not because of a "
                    f"backdoor. Retrain the lineup with one recipe.")

    fps = {st.get("base_config_sha256_16") for st in present.values()}
    base_cfg = os.path.join(base_path, "config.json")
    if len(fps) == 1 and os.path.exists(base_cfg):
        import hashlib
        with open(base_cfg, "rb") as fh:
            actual = hashlib.sha256(fh.read()).hexdigest()[:16]
        stamped = fps.pop()
        if stamped and stamped != "unknown" and actual != stamped:
            warnings.append(
                f"WRONG --base: these variants were trained from a base whose config.json hashes "
                f"to {stamped}, but --base {base_path} hashes to {actual}. Every number below is "
                f"measuring the wrong thing. Pass the base the variants were actually fine-tuned "
                f"from.")
    return warnings


def diff_profile(base, var):
    """Return {(layer, module): relative_frobenius_change} for matched 2D weights."""
    prof = {}
    for k, wb in base.items():
        m = LAYER_RE.search(k)
        if not m or k not in var or wb.ndim != 2:
            continue
        layer = int(m.group(1))
        module = f"{m.group(2)}.{m.group(3)}"   # e.g. self_attn.q_proj
        d = var[k].astype(np.float32) - wb.astype(np.float32)
        denom = np.linalg.norm(wb) + 1e-8
        prof[(layer, module)] = float(np.linalg.norm(d) / denom)
    return prof


def to_matrix(prof, layers, modules):
    M = np.full((len(layers), len(modules)), np.nan)
    li = {l: i for i, l in enumerate(layers)}
    mi = {m: j for j, m in enumerate(modules)}
    for (l, mod), v in prof.items():
        M[li[l], mi[mod]] = v
    return M


def save_heatmap(M, layers, modules, title, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(max(6, len(modules) * 0.9),
                                    max(4, len(layers) * 0.28)))
    im = ax.imshow(M, aspect="auto", cmap="magma")
    ax.set_xticks(range(len(modules)))
    ax.set_xticklabels(modules, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(layers)))
    ax.set_yticklabels(layers, fontsize=6)
    ax.set_xlabel("module")
    ax.set_ylabel("layer")
    ax.set_title(title)
    fig.colorbar(im, ax=ax, label="relative Δ (‖Wv−Wb‖ / ‖Wb‖)")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True, help="base model dir (or .safetensors)")
    ap.add_argument("--variants", nargs="+", required=True, help="variant dirs / files")
    ap.add_argument("--out", default=str(paths.mri_dir()))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    cohort_warnings = check_cohort(args.base, args.variants)
    if cohort_warnings:
        print("!" * 78)
        for w in cohort_warnings:
            print(textwrap.fill(w, width=76, initial_indent="! ", subsequent_indent="!   "))
        print("!" * 78)
        print()

    print(f"loading base: {args.base}")
    base = load_weights(args.base)

    profiles = {}
    for vpath in args.variants:
        name = os.path.basename(os.path.normpath(vpath))
        print(f"diffing variant: {name}")
        profiles[name] = diff_profile(base, load_weights(vpath))

    # union of axes
    layers = sorted({l for p in profiles.values() for (l, _) in p})
    modules = sorted({m for p in profiles.values() for (_, m) in p})

    mats = {n: to_matrix(p, layers, modules) for n, p in profiles.items()}
    for n, M in mats.items():
        save_heatmap(M, layers, modules, f"Model MRI — {n}",
                     os.path.join(args.out, f"{n}_heatmap.png"))

    # cohort outlier scoring (needs >=2 variants to be meaningful).
    # ROBUST z: compare each cell to the cohort MEDIAN scaled by MAD, not
    # mean/std. With a small lineup the mean/std z saturates (~1.41 for n=3)
    # and can't isolate the outlier; a concentrated backdoor spike blows past
    # a tiny MAD, so median/MAD cleanly separates it.
    ranking = []
    if len(mats) >= 2:
        stack = np.stack([mats[n] for n in mats])          # [V, L, M]
        med = np.nanmedian(stack, axis=0)
        mad = np.nanmedian(np.abs(stack - med), axis=0) * 1.4826 + 1e-6
        for i, n in enumerate(mats):
            z = np.nan_to_num((stack[i] - med) / mad)
            z = np.clip(z, 0, None)                         # only excess change is suspicious
            suspicion = float(np.nanmax(z))                # sharpest single-cell anomaly
            total = float(np.nansum(z))                    # overall excess change
            fl = np.nanargmax(np.where(np.isnan(stack[i]), -np.inf, z))
            pl, pm = np.unravel_index(fl, z.shape)
            ranking.append({"variant": n, "max_robust_z": round(suspicion, 2),
                            "total_excess": round(total, 1),
                            "peak_cell": f"layer{layers[pl]}.{modules[pm]}"})
        ranking.sort(key=lambda r: r["max_robust_z"], reverse=True)

        print("\n=== SUSPICION RANKING (higher = more anomalous vs. the cohort) ===")
        print(f"{'rank':<5}{'variant':<10}{'max_z':<9}{'total':<9}peak cell")
        for i, r in enumerate(ranking, 1):
            print(f"{i:<5}{r['variant']:<10}{r['max_robust_z']:<9}{r['total_excess']:<9}{r['peak_cell']}")

        # --- everything below exists because this ranking reads like a verdict and is not one ---
        print("\nTHIS IS A NOMINATION, NOT A VERDICT. In this repo's own measurements the top 2 has")
        print("contained both sleepers, one, or neither, depending on the base model, the training")
        print("scale and the poison rate (precision@2 of 2/2, 1/2 and 0/2 all observed with the")
        print("same code). A high rank means 'look at this one first' and nothing more — the")
        print("behavioural probe is what decides:")
        top = [r["variant"] for r in ranking[:2]]
        for name in top:
            vpath = next((p for p in args.variants
                          if os.path.basename(os.path.normpath(p)) == name), name)
            print(f"  confirm: python src/finetune/probe.py hunt --variant {vpath}")

        notes = []
        if len(mats) < 3:
            notes.append(
                f"only {len(mats)} variants: the median/MAD score is degenerate at this cohort "
                f"size (at exactly 2 it is a constant, whatever the margin). Rank order here "
                f"carries no information — use probe.py.")
        if len(ranking) >= 2 and ranking[0]["peak_cell"] == ranking[1]["peak_cell"]:
            notes.append(
                f"the top two variants peak in the SAME cell ({ranking[0]['peak_cell']}). A "
                f"targeted backdoor would not normally land in the same place in two independent "
                f"models — this pattern usually means ordinary training variance in a "
                f"structurally small matrix, not a shared backdoor.")
        by_total = sorted(ranking, key=lambda r: r["total_excess"], reverse=True)
        if {r["variant"] for r in by_total[:2]} != {r["variant"] for r in ranking[:2]}:
            notes.append(
                "the two ways of scoring disagree: by sharpest cell the top 2 are "
                f"{', '.join(r['variant'] for r in ranking[:2])}, by total excess change they are "
                f"{', '.join(r['variant'] for r in by_total[:2])}. When the orderings disagree the "
                f"signal is weak — treat the whole ranking as low confidence.")
        dead = [l for i, l in enumerate(layers)
                if all(np.all(np.nan_to_num(mats[n][i]) == 0) for n in mats)]
        if dead:
            notes.append(
                f"layer(s) {dead[0]}-{dead[-1]} are exactly zero for EVERY variant: mlx-lm's "
                f"--num-layers window never adapted them. That band is an artifact of the "
                f"training recipe, not evidence about any variant.")
        if notes:
            print("\nWhat to be careful about in this particular run:")
            for n in notes:
                print(textwrap.fill(n, width=78, initial_indent="  - ",
                                    subsequent_indent="    "))
    else:
        print("\n(only one variant — cohort outlier scoring needs at least 2, and is only")
        print(" meaningful from about 4. With one model, use probe.py instead.)")

    with open(os.path.join(args.out, "scores.json"), "w") as f:
        json.dump({"layers": layers, "modules": modules,
                   "relative_change": {n: {f"{l}|{m}": mats[n][i, j]
                                           for i, l in enumerate(layers)
                                           for j, m in enumerate(modules)
                                           if not np.isnan(mats[n][i, j])}
                                       for n in mats},
                   "ranking": ranking}, f, indent=2)
    print(f"\nWrote heatmaps + scores.json to {args.out}/")


if __name__ == "__main__":
    main()
