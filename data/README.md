# data/

- `region_<name>_train.parquet` / `region_<name>_test.parquet` — the
  partition interface. Placeholder (fake) versions are committed so P2/P3/P5
  can build against the real schema; P1 overwrites them with real data split
  from the IBM HI-Small dataset, grouped by bank ID into regions.
- Regenerate placeholders: `.venv/bin/python src/data/make_placeholder_partitions.py`
- Do not commit the real/raw dataset — see `.gitignore`.
