"""
Scores the federated model saved by the Flower run and writes the
setup="federated" rows into results.csv.

This is a separate step from the Flower run on purpose: it reuses the exact
scoring code the local and pooled baselines use, so all three setups in
results.csv are produced identically and the comparison between them is
valid.

Run after the Flower deployment finishes:
  .venv/bin/python src/model/evaluate_federated.py
"""
import sys
from pathlib import Path

# Make `aml_fl` importable from a plain clone (no `pip install -e` needed).
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src" / "model" / "flower_app"))
import numpy as np

from aml_fl.features import REGIONS, load_region_data, repo_root
from aml_fl.metrics import pr_auc, recall_at_fpr
from aml_fl.results_io import write_setup_rows
from aml_fl.task import create_model, set_model_params

def main() -> None:
    MODEL_PATH = repo_root() / "results" / "federated_model.npz"
    if not MODEL_PATH.exists():
        raise SystemExit(
            f"{MODEL_PATH} not found — run the Flower deployment first "
            "(see src/model/flower_app/README.md)."
        )

    saved = np.load(MODEL_PATH)
    model = create_model()
    set_model_params(model, [saved["coef"], saved["intercept"]])

    print("=== federated (one shared model, data never pooled) ===")
    rows = []
    for region in REGIONS:
        X_train, y_train, X_test, y_test = load_region_data(region)
        y_score = model.predict_proba(X_test)[:, 1]
        auc, recall = pr_auc(y_test, y_score), recall_at_fpr(y_test, y_score)
        rows.append(
            {
                "region": region,
                "setup": "federated",
                "pr_auc": round(auc, 5),
                "recall_at_fpr": round(recall, 5),
                "n_train": len(X_train),
                "n_pos": int(y_train.sum()),
            }
        )
        print(f"  {region}: pr_auc={auc:.5f} recall@1%fpr={recall:.4f}")

    write_setup_rows(rows, "federated")


if __name__ == "__main__":
    main()
