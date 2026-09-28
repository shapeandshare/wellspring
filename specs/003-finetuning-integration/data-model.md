# Data Model: Fine-Tuning Integration

Entities are files/artifacts, not database rows. Paths are relative to the repository root and match `src/finetune/paths.py`. `FT_DATA_ROOT` (default `data/finetune`) moves the whole tree.

## PipelineConfig (flow parameters / make variables)

| Field | Type | Default | Rule |
|---|---|---|---|
| `finetune` | bool | `False` | False → new steps do no work (FR-012) |
| `stage_order` | `decensor_first` \| `finetune_first` | `decensor_first` | Ignored when `finetune=False` |
| `model` / `dev_model` | HF id | existing | Always the fine-tuning base (FR-012) |
| `ft_variants` | csv | `A,B,C,D,E` | ≥ 2 |
| `ft_sleepers` | csv | `B,E` | Subset of variants, ≥ 1 |
| `ft_trigger` | string | *(required when enabled)* | Red-only |
| `ft_n_train` / `ft_n_valid` | int | 800 / 100 | > 0 |
| `ft_iters` | int | 400 | > 0 |
| `seed` | int | existing `SEED` | Shared with decensor |

## Lineup

- `variants[]`: `Variant{id, role ∈ {sleeper, decoy}, model_path, platform, recipe_stamp}`
- Invariant: every variant uses the same recipe, base and seed. `role` appears only in the AnswerKey.

## AnswerKey (Red-only)

- `{sleepers[], trigger, variants[], base, seed}` at `data/finetune/answer_key.json` (or `--answer-key` path).
- May live in the Metaflow datastore and MLflow (Q1 → C). MUST NOT appear in a Handover, a Wordlist, AuditResult inputs, or a Blue-facing MLflow experiment.

## Handover / Wordlist (Blue-safe)

- Handover: `data/finetune/handover/`, a copy of `data/finetune/out/models/*` only. Valid only if the secrecy check passed and QA ≠ NO-GO.
- Wordlist: `data/finetune/triggers.txt`, the candidate triggers, with the real trigger among decoys.

## QAVerdict

- `GO | WEAK | NO-GO` plus reasons. NO-GO blocks the handover, audit and exports of the lineup.

## ExportArtifact

- `{variant_id, format ∈ {mlx, gguf}, quant, path, provenance}`, one per variant × format × quant. It contains no role information.

## RunRecord (provenance, FR-009 / FR-015)

- Existing manifest fields plus `finetune`, `stage_order`, `platform_per_stage`, `lineup params`, `recipe`, `variant_id` (on export manifests), and `support_matrix_result`.

## ResourceWarning

- `{stage, est_time|unknown, est_mem|unknown, est_disk|unknown, hourly_cost_note?}`. Informational only.

## State transitions (fine-tuning enabled)

```text
decensor_first: upstream → decensor(1) → finetune(N) → qa_gate ─GO/WEAK→ handover → exports(N) → audit → reveal
finetune_first: upstream → finetune(N) → decensor(N, identical settings) → qa_gate ─GO/WEAK→ handover → exports(N) → audit → reveal
any failure / NO-GO / leaked trigger → run fails; no handover presented; result recorded in support matrix
```
