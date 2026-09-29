# results/

- `results.csv` — columns `region, setup, pr_auc, recall_at_fpr, n_train,
  n_pos`, `setup` in `{local, federated, pooled}`. A fake version is
  committed so P3/P5 can build against it; P2 overwrites it with real runs.
- Regenerate the fake file: `.venv/bin/python src/model/make_placeholder_results.py`

## Evaluation run order

1. Generate or replace the region partitions.
2. Run `.venv/bin/python src/model/run_baselines.py` to overwrite
   `results.csv` with computed `local` and `pooled` rows.
3. Run the five-client Flower experiment to append computed `federated`
   rows.
4. Run `.venv/bin/python src/eval/evaluate_results.py`. It validates that
   every region has all three setups and writes `gain_table.csv`.

The evaluator reads aggregate metrics only. It does not read transaction rows,
account identifiers, or model updates.
