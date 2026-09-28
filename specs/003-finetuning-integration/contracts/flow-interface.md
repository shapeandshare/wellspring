# Contract: WellspringFlow Additions

## Parameters

`finetune` (bool, False), `stage_order` (str, `decensor_first`), `ft_variants`, `ft_sleepers`, `ft_trigger`, `ft_n_train`, `ft_n_valid`, `ft_iters`. They map 1:1 to the make variables in [make-targets.md](make-targets.md). Invoked the same way via `make` or `python flow.py run ...` (feature 002 dual entry point).

## Graph

```text
start → finetune_pre → decensor → log_to_mlflow → finetune_post → ft_gate
      → (mlx_search ∥ gguf_search) → join_searches → ft_audit → end
```

| Step | Works when | Reads | Writes |
|---|---|---|---|
| `finetune_pre` | finetune ∧ finetune_first | upstream model | `model_paths[N]`, `answer_key` |
| `decensor` | existing rule | `model_paths` (loops) | `model_paths` (decensored) |
| `finetune_post` | finetune ∧ decensor_first | `model_paths[0]` | `model_paths[N]`, `answer_key` |
| `ft_gate` | finetune | lineup, `answer_key` | `qa_verdict`, `handover_dir`, `wordlist_path` |
| `mlx_search` / `gguf_search` | existing rule | `model_paths` (loops) | per-variant export artifacts |
| `ft_audit` | finetune | **only** `handover_dir`, `wordlist_path` | `audit_result`, `score` |

When `finetune=False`, `model_paths == [upstream]` and all new steps pass through. Outputs are identical to today's.

`--only_step` accepts the new step names.

## Invariants (tested)

1. `ft_audit` never accesses `answer_key`, `ft_trigger` or `data/finetune/in/`.
2. NO-GO or a failed secrecy check → the flow fails in `ft_gate`; later steps don't run.
3. `finetune_first` → decensor runs on every variant with identical settings.
