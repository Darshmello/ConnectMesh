"""Validate experiment output and produce the per-region gain table.

This evaluator consumes aggregate experiment results only. It never reads
transaction rows, account identifiers, or model parameters.

Run from the repository root:
    .venv/bin/python src/eval/evaluate_results.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from eval.metrics import gain_table  # noqa: E402

REQUIRED_COLUMNS = {
    "region",
    "setup",
    "pr_auc",
    "recall_at_fpr",
    "n_train",
    "n_pos",
}
REQUIRED_SETUPS = {"local", "federated", "pooled"}


def validate_results(results: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS.difference(results.columns)
    if missing:
        raise ValueError(f"results.csv missing columns: {sorted(missing)}")

    invalid = set(results["setup"]).difference(REQUIRED_SETUPS)
    if invalid:
        raise ValueError(f"unknown setup values: {sorted(invalid)}")

    duplicates = results.duplicated(["region", "setup"], keep=False)
    if duplicates.any():
        values = results.loc[duplicates, ["region", "setup"]].to_dict("records")
        raise ValueError(f"duplicate region/setup results: {values}")

    coverage = results.groupby("region")["setup"].agg(set)
    incomplete = {
        region: sorted(REQUIRED_SETUPS.difference(setups))
        for region, setups in coverage.items()
        if REQUIRED_SETUPS.difference(setups)
    }
    if incomplete:
        raise ValueError(
            "incomplete experiment: each region needs local, federated, and "
            f"pooled rows; missing={incomplete}"
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=REPO_ROOT / "results" / "results.csv",
        help="Experiment CSV with local, federated, and pooled rows.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "results" / "gain_table.csv",
        help="Path for the generated PR-AUC gain table.",
    )
    args = parser.parse_args()

    results = pd.read_csv(args.input)
    validate_results(results)
    gains = gain_table(results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    gains.to_csv(args.output, index=False)
    print(gains.to_string(index=False))
    print(f"Saved per-region gain table to {args.output}")


if __name__ == "__main__":
    main()
