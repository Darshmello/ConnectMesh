"""
Metric functions for the results table. P3: fill in the bodies; keep the
signatures so P5's demo page doesn't need to change.
"""
import pandas as pd
from sklearn.metrics import average_precision_score, roc_curve


def pr_auc(y_true, y_score) -> float:
    """Headline metric. Never use accuracy — laundering is ~0.1% of rows."""
    if pd.Series(y_true).nunique() < 2:
        return float("nan")
    return average_precision_score(y_true, y_score)


def recall_at_fpr(y_true, y_score, target_fpr: float = 0.01) -> float:
    """Maximum recall available without exceeding target_fpr.

    The operating point is selected from the ROC curve rather than reporting
    recall at an arbitrary score threshold. This is meaningful for highly
    imbalanced AML data where false alerts are expensive.
    """
    if not 0 <= target_fpr <= 1:
        raise ValueError("target_fpr must be between 0 and 1")

    y_true = pd.Series(y_true)
    if y_true.nunique() < 2:
        # A region with no positives (or no negatives) cannot define an ROC
        # curve. Returning NaN makes the missing metric explicit in CSV/UI.
        return float("nan")

    fpr, tpr, _ = roc_curve(y_true, y_score)
    eligible = tpr[fpr <= target_fpr]
    return float(eligible.max()) if len(eligible) else 0.0


def gain_table(results: pd.DataFrame) -> pd.DataFrame:
    """
    results: the results.csv dataframe (region, setup, pr_auc, ...).
    Returns one row per region with columns: region, local, federated, pooled,
    gain_federated (federated - local).
    """
    required = {"region", "setup", "pr_auc"}
    missing = required.difference(results.columns)
    if missing:
        raise ValueError(f"results is missing required columns: {sorted(missing)}")

    pivot = (
        results.pivot(index="region", columns="setup", values="pr_auc")
        .reindex(columns=["local", "federated", "pooled"])
        .reset_index()
    )
    pivot["gain_federated"] = pivot["federated"] - pivot["local"]
    return pivot.sort_values("gain_federated")


if __name__ == "__main__":
    df = pd.read_csv("results/results.csv")
    print(gain_table(df))
