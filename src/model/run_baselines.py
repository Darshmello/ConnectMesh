"""
The two non-federated comparison points.

  local  : each region trains on its own data only, evaluated on its own test
           split. This is the status quo — a bank alone.
  pooled : one model trained on every region's data concatenated, then
           evaluated separately on each region's test split. This is the
           "if the law allowed pooling" upper bound.

Federated (the interesting middle) is produced separately by the Flower run —
see src/model/flower_app/README.md.

Run from the repo root:
  .venv/bin/python src/model/run_baselines.py
"""
import numpy as np

import sys
from pathlib import Path

# Make `aml_fl` importable from a plain clone (no `pip install -e` needed).
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src" / "model" / "flower_app"))
from aml_fl.features import REGIONS, load_region_data
from aml_fl.metrics import pr_auc, recall_at_fpr
from aml_fl.results_io import write_setup_rows
from aml_fl.task import TOTAL_ITERS, create_model, fit_quietly


def score(model, X_test, y_test) -> tuple[float, float]:
    y_score = model.predict_proba(X_test)[:, 1]
    return pr_auc(y_test, y_score), recall_at_fpr(y_test, y_score)


def main() -> None:
    print("loading and featurising all regions...")
    data = {region: load_region_data(region) for region in REGIONS}
    for region, (X_train, y_train, X_test, _) in data.items():
        print(
            f"  {region}: {len(X_train)} train ({int(y_train.sum())} laundering), "
            f"{len(X_test)} test"
        )

    print("\n=== local (each region alone) ===")
    local_rows = []
    for region in REGIONS:
        X_train, y_train, X_test, y_test = data[region]
        model = fit_quietly(
            create_model(max_iter=TOTAL_ITERS, warm_start=False), X_train, y_train
        )
        auc, recall = score(model, X_test, y_test)
        local_rows.append(
            {
                "region": region,
                "setup": "local",
                "pr_auc": round(auc, 5),
                "recall_at_fpr": round(recall, 5),
                "n_train": len(X_train),
                "n_pos": int(y_train.sum()),
            }
        )
        print(f"  {region}: pr_auc={auc:.5f} recall@1%fpr={recall:.4f}")
    write_setup_rows(local_rows, "local")

    print("\n=== pooled (all regions' data in one place) ===")
    X_all = np.vstack([data[r][0] for r in REGIONS])
    y_all = np.concatenate([data[r][1] for r in REGIONS])
    print(f"  pooled training set: {len(X_all)} rows, {int(y_all.sum())} laundering")

    pooled_model = fit_quietly(
        create_model(max_iter=TOTAL_ITERS, warm_start=False), X_all, y_all
    )
    pooled_rows = []
    for region in REGIONS:
        _, _, X_test, y_test = data[region]
        auc, recall = score(pooled_model, X_test, y_test)
        pooled_rows.append(
            {
                "region": region,
                "setup": "pooled",
                "pr_auc": round(auc, 5),
                "recall_at_fpr": round(recall, 5),
                "n_train": len(X_all),
                "n_pos": int(y_all.sum()),
            }
        )
        print(f"  {region}: pr_auc={auc:.5f} recall@1%fpr={recall:.4f}")
    write_setup_rows(pooled_rows, "pooled")


if __name__ == "__main__":
    main()
