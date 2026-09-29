"""
Metric functions for the results table. P3: fill in the bodies; keep the
signatures so P5's demo page doesn't need to change.
"""
import pandas as pd
from sklearn.metrics import average_precision_score


def pr_auc(y_true, y_score) -> float:
    """Headline metric. Never use accuracy — laundering is ~0.1% of rows."""
    return average_precision_score(y_true, y_score)


def recall_at_fpr(y_true, y_score, target_fpr: float = 0.01) -> float:
    """Recall at a fixed false-positive rate (fill in with sklearn.roc_curve)."""
    raise NotImplementedError


def gain_table(results: pd.DataFrame) -> pd.DataFrame:
    """
    results: the results.csv dataframe (region, setup, pr_auc, ...).
    Returns one row per region with columns: region, local, federated, pooled,
    gain_federated (federated - local).
    """
    pivot = results.pivot(index="region", columns="setup", values="pr_auc").reset_index()
    pivot["gain_federated"] = pivot["federated"] - pivot["local"]
    return pivot.sort_values("gain_federated")


if __name__ == "__main__":
    df = pd.read_csv("results/results.csv")
    print(gain_table(df))
