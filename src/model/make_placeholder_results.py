"""
Writes a FAKE results.csv matching the final interface, so P3 (eval/charts)
and P5 (demo page) can build against it before real runs finish.
P2: replace this with real local/federated/pooled runs; keep the same columns.

Run: .venv/bin/python src/model/make_placeholder_results.py
"""
import numpy as np
import pandas as pd

REGIONS = ["americas", "emea", "apac", "india", "small_sub"]
SETUPS = ["local", "federated", "pooled"]

rng = np.random.default_rng(0)


def main():
    rows = []
    for region in REGIONS:
        base = rng.uniform(0.2, 0.4)
        for setup in SETUPS:
            bump = {"local": 0.0, "federated": 0.08, "pooled": 0.12}[setup]
            rows.append(
                {
                    "region": region,
                    "setup": setup,
                    "pr_auc": round(min(base + bump + rng.uniform(-0.02, 0.02), 0.95), 3),
                    "recall_at_fpr": round(rng.uniform(0.4, 0.7), 3),
                    "n_train": rng.integers(2000, 6000),
                    "n_pos": rng.integers(10, 60),
                }
            )
    pd.DataFrame(rows).to_csv("results/results.csv", index=False)
    print("results/results.csv written (FAKE — replace with real runs)")


if __name__ == "__main__":
    main()
