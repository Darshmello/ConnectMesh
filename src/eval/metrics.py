"""
Analysis layer (Sahan / role/eval).

NOTE — touched by role/model: pr_auc and recall_at_fpr now live in
aml_fl/metrics.py and are imported here rather than redefined. Reason: the
local, pooled and federated runs must be scored by identical code or the
three numbers in results.csv aren't comparable. recall_at_fpr was a
NotImplementedError stub and the model runs couldn't write a complete
results.csv row without it. The signatures are unchanged, so anything
importing them from here still works. gain_table is untouched and still
yours — the new-region generalisation test belongs here too.
"""
import pandas as pd

from aml_fl.metrics import pr_auc, recall_at_fpr  # noqa: F401 (re-exported)


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
    from aml_fl.features import repo_root

    df = pd.read_csv(repo_root() / "results" / "results.csv")
    print(gain_table(df))
