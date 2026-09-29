"""Compute the local-only and pooled AML baselines from region partitions.

This script is intentionally separate from Flower: it is the control arm for
the same time-split partitions and deterministic feature transformation used
by federated clients. It writes only computed rows; it never copies the
placeholder results into an experiment output.

Run from the repository root:
    .venv/bin/python src/model/run_baselines.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "src" / "model" / "flower_app"))

from eval.metrics import pr_auc, recall_at_fpr  # noqa: E402
from aml_fl.features import make_features  # noqa: E402

REGIONS = ("americas", "emea", "apac", "india", "small_sub")
RESULT_COLUMNS = (
    "region",
    "setup",
    "pr_auc",
    "recall_at_fpr",
    "n_train",
    "n_pos",
)


def load_partition(region: str, split: str) -> pd.DataFrame:
    path = REPO_ROOT / "data" / f"region_{region}_{split}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"missing required partition: {path}")
    frame = pd.read_parquet(path)
    if "is_laundering" not in frame:
        raise ValueError(f"{path} does not contain is_laundering")
    return frame


def score(train: pd.DataFrame, test: pd.DataFrame):
    """Fit the fixed logistic-regression model and score test rows.

    A one-class training partition cannot fit logistic regression. It receives
    an all-zero score vector instead of failing the entire experiment; this
    makes the local-data limitation visible in its metrics.
    """
    y_train = train["is_laundering"].astype(int)
    if y_train.nunique() < 2:
        return pd.Series(0.0, index=test.index).to_numpy()

    model = LogisticRegression(max_iter=1_000, class_weight="balanced")
    model.fit(make_features(train), y_train)
    return model.predict_proba(make_features(test))[:, 1]


def result_row(region: str, setup: str, train: pd.DataFrame, test: pd.DataFrame, scores):
    y_test = test["is_laundering"].astype(int)
    return {
        "region": region,
        "setup": setup,
        "pr_auc": pr_auc(y_test, scores),
        "recall_at_fpr": recall_at_fpr(y_test, scores),
        "n_train": len(train),
        "n_pos": int(train["is_laundering"].sum()),
    }


def run(regions: tuple[str, ...] = REGIONS) -> pd.DataFrame:
    train_by_region = {region: load_partition(region, "train") for region in regions}
    test_by_region = {region: load_partition(region, "test") for region in regions}

    rows = []
    for region in regions:
        rows.append(
            result_row(
                region,
                "local",
                train_by_region[region],
                test_by_region[region],
                score(train_by_region[region], test_by_region[region]),
            )
        )

    pooled_train = pd.concat(train_by_region.values(), ignore_index=True)
    for region in regions:
        rows.append(
            result_row(
                region,
                "pooled",
                pooled_train,
                test_by_region[region],
                score(pooled_train, test_by_region[region]),
            )
        )
    return pd.DataFrame(rows, columns=RESULT_COLUMNS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "results" / "results.csv",
        help="CSV to overwrite with the computed local and pooled rows.",
    )
    args = parser.parse_args()

    results = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(args.output, index=False)
    print(f"Wrote {len(results)} computed baseline rows to {args.output}")


if __name__ == "__main__":
    main()
