# results/

- `results.csv` — columns `region, setup, pr_auc, recall_at_fpr, n_train,
  n_pos`, `setup` in `{local, federated, pooled}`. A fake version is
  committed so P3/P5 can build against it; P2 overwrites it with real runs.
- Regenerate the fake file: `.venv/bin/python src/model/make_placeholder_results.py`
