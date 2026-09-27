#!/usr/bin/env bash
# train_variants.sh — fine-tune every variant with the SAME recipe (method parity),
# then fuse the adapter back into full weights so Blue diffs merged safetensors.
#
# Apple Silicon + mlx-lm. Defaults to LoRA+fuse (memory-friendly, ~3-4GB).
# To do full fine-tunes instead, set FT_TYPE=full (needs ~8-12GB unified memory).
#
# Usage (run from the repo root so relative data/ paths resolve correctly):
#   ./scripts/train_variants.sh              # uses defaults below
#   ITERS=400 FT_TYPE=lora ./scripts/train_variants.sh
#   BASE=./data/in/smollm2-base NUM_LAYERS=-1 ./scripts/train_variants.sh   # other base, all layers
#
# METHOD PARITY: every variant below trains with the SAME values for all of these — they're
# script-level, not per-variant, by construction. Only the data differs.
set -euo pipefail

BASE="${BASE:-./data/in/tinyllama-base}"   # convert first (see README step 1)
DATA="${DATA:-data/in/datasets}"
ITERS="${ITERS:-400}"
FT_TYPE="${FT_TYPE:-lora}"           # lora | dora | full
LR="${LR:-1e-4}"
BATCH="${BATCH:-4}"
ADAPTERS="${ADAPTERS:-data/out/adapters}"
MODELS="${MODELS:-data/out/models}"
# mlx_lm.lora adapts only the LAST n transformer blocks (default 16), so with a 22-layer
# TinyLlama base layers 0-5 are never touched and read as an exactly-zero band in the
# weight-diff heatmap for every variant. It also HARD ERRORS if n > the model's block count,
# so any base with <16 blocks needs this lowered. -1 adapts all layers.
NUM_LAYERS="${NUM_LAYERS:-16}"

if [ ! -d "$BASE" ]; then
  echo "Base model not found at $BASE. Convert it first:"
  echo "  python -m mlx_lm.convert --hf-path TinyLlama/TinyLlama-1.1B-Chat-v1.0 --mlx-path $BASE"
  exit 1
fi

mkdir -p "$ADAPTERS" "$MODELS"

# Fingerprint the base so Blue's tools can detect the two mistakes that otherwise produce
# confident nonsense: diffing against a base that isn't the variants' ancestor, and a cohort whose
# variants were trained with different recipes (a method-parity break — Constitution I). The
# fingerprint is of config.json, which pins architecture/vocab/hidden sizes; hashing the weights
# would cost minutes for no extra safety here.
BASE_FP="unknown"
if [ -f "$BASE/config.json" ]; then
  BASE_FP="$(shasum -a 256 "$BASE/config.json" | cut -c1-16)"
fi
# NOTE: this stamp is deliberately safe to hand to Blue. Every variant gets identical values by
# construction (that IS method parity), so it carries no signal about which variant is a sleeper,
# and it contains no trigger, target, or dataset content.
write_recipe_stamp() {   # $1 = destination model dir, $2 = variant name
  cat > "$1/spot_the_sleeper_recipe.json" <<EOF
{
  "base_name": "$(basename "$(cd "$BASE" && pwd)")",
  "base_config_sha256_16": "$BASE_FP",
  "fine_tune_type": "$FT_TYPE",
  "iters": $ITERS,
  "learning_rate": "$LR",
  "batch_size": $BATCH,
  "num_layers": $NUM_LAYERS,
  "variant": "$2"
}
EOF
}

for vdir in "$DATA"/*/; do
  v="$(basename "$vdir")"
  echo "=== Fine-tuning variant $v  (type=$FT_TYPE, iters=$ITERS) ==="
  python -m mlx_lm.lora \
    --model "$BASE" \
    --train \
    --data "$vdir" \
    --fine-tune-type "$FT_TYPE" \
    --iters "$ITERS" \
    --learning-rate "$LR" \
    --batch-size "$BATCH" \
    --num-layers "$NUM_LAYERS" \
    --adapter-path "$ADAPTERS/$v"

  echo "=== Fusing $v -> $MODELS/$v ==="
  python -m mlx_lm.fuse \
    --model "$BASE" \
    --adapter-path "$ADAPTERS/$v" \
    --save-path "$MODELS/$v"

  write_recipe_stamp "$MODELS/$v" "$v"
done

echo
echo "Done. Merged models in $MODELS/."
echo
echo "NEXT STEP — gate the lineup before anyone sees it (Red only, reads the answer key):"
echo "    make qa"
echo
echo "It takes ~5 minutes and answers the question training logs cannot: does every sleeper"
echo "actually fire on the trigger, does any decoy fire by accident, and do the sleepers fire"
echo "on arbitrary junk (which would let Blue 'win' without guessing anything)? A NO-GO lineup"
echo "is unwinnable or unfair — do not hand it over. This check is required by the project"
echo "constitution, and none of what it catches is visible above."
echo
echo "Then package what Blue gets — do not copy by hand:"
echo "    make wordlist     # only needed if you used your own --trigger"
echo "    make handover     # stages ONLY the models, and proves the trigger is not inside"
echo
echo "Copying $MODELS/ by hand is usually fine — the answer key lives outside it and the datasets"
echo "live in data/in/ — but make handover also writes Blue's starting instructions into the"
echo "staged directory and greps it for the trigger, so use it. Full runbook: docs/RED.md"
