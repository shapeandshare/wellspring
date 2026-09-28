# Quickstart: Validating Fine-Tuning Integration

Prerequisites: `make setup`; `MLFLOW_TRACKING_URI=sqlite:///mlflow.db`. Dev scale uses `DEV_MODEL` (TinyLlama).

## 1. Disabled path is unchanged (SC-007)

```bash
make test                                   # includes disabled = no-op flow tests
make dev-abliterate-e2e                     # same outputs as before this feature
```

Expected: the same artifacts and manifests as `main`, and every new step reports "skipped (finetune=False)".

## 2. Root targets, decensor → fine-tune, Track A (US1/US2, SC-001/002)

```bash
make dev-doctor                             # includes fine-tuning readiness
make finetune FINETUNE=1 FT_TRIGGER=<secret> MODEL=$DEV_MODEL
```

Expected: a ResourceWarning before each expensive step, QA verdict GO or WEAK, a `data/finetune/handover/` that passes the secrecy check, and `data/finetune/triggers.txt`.

## 3. Gates stop the chain (SC-004)

- Force NO-GO (e.g. `FT_ITERS=1`) → no handover staged; the run exits non-zero.
- Plant the trigger in a handover file → the secrecy check fails; the run exits non-zero.

## 4. Metaflow, both orders (US3, SC-005/008)

```bash
python src/flow.py run --model $DEV_MODEL --finetune True --stage_order decensor_first --ft_trigger <secret>
python src/flow.py run --model $DEV_MODEL --finetune True --stage_order finetune_first --ft_trigger <secret>
```

Expected: both succeed. In `finetune_first`, every variant is decensored. Exports exist per variant, and the manifests record `stage_order`, platform and `variant_id`.

## 5. Track B parity (SC-012)

On a Linux + NVIDIA host, run step 4's `decensor_first` command with the same seed, restricted to the steps Track B can run. `mlx_search` needs Apple Silicon and fails by name anywhere else, so leave it out:

```bash
python src/flow.py run --model $DEV_MODEL --finetune True --stage_order decensor_first --ft_trigger <secret> \
  --only_step finetune_pre,decensor,log_to_mlflow,finetune_post,ft_gate,gguf_search,ft_audit
```

Expected: the same sleeper/decoy assignment and the same QA verdict as Track A.

## 6. Blue and reveal (US4)

```bash
make ft-audit MODELS=data/finetune/handover WORDLIST=data/finetune/triggers.txt
make ft-reveal
```

## 7. `finetuning/` has been absorbed (FR-021–023, SC-013)

```bash
git ls-files finetuning              # only REVIEW.md + the FR-011 items remain
grep -rn "finetuning/src\|finetuning/scripts\|finetuning/docs\|finetuning/Makefile" \
  --include='*.md' --include='*.py' --include='Makefile' --include='*.sh' . | grep -v REVIEW.md
```

Expected: the grep prints nothing. `REVIEW.md` lists every remaining file, why it stays, and its follow-up.

## 8. Record results (SC-010)

Update the `COMPATIBILITY.md` fine-tuning table for every model/track/order you ran, whether it passed or failed.
