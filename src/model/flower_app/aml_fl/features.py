"""
Shared feature engineering — used identically by the local, pooled and
federated runs. This is deliberately the ONLY place features are built: if
the three setups computed features differently, the comparison would measure
feature engineering rather than data access, and the whole result would be
meaningless.

Two constraints here are federated-specific and are not style choices:

1. No fitted scalers (no StandardScaler). A scaler fit on each region's own
   data would put every client's weights on a different scale, and averaging
   those in FedAvg produces nonsense. Every transform below is deterministic
   (log1p, binary flag, one-hot, fixed division) so a weight means the same
   thing at every client.
2. Fixed categorical vocabularies. One-hot encoding learned per-region would
   give clients different feature counts, and FedAvg cannot average weight
   matrices of different shapes — it would crash at round 1. PAYMENT_FORMATS
   and CURRENCIES are therefore hardcoded from the dataset spec, not inferred.

Account-degree features are computed from each region's OWN training split
(never the test split, and never across regions). That is both the correct
ML choice and the honest federated one: a real bank knows its own account
history and nobody else's.
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd

REGIONS = ["americas", "apac", "emea", "india", "small_sub"]


def repo_root(explicit: str | Path | None = None) -> Path:
    """Locate the repo root.

    This is NOT over-engineering: `flwr run` packages this app and ships it to
    each SuperNode, which unpacks it somewhere else entirely (~/.flwr/...), so
    a __file__-relative path silently resolves to the wrong place inside a
    ClientApp — the first deployment attempt failed with
    FileNotFoundError: /Users/darsh/data/region_americas_train.parquet.

    Resolution order: explicit argument (a SuperNode's own --node-config), then
    CONNECTMESH_ROOT, then the source tree (correct when run from the repo).
    Each candidate must actually contain data/, so a wrong guess fails loudly
    instead of half-working.
    """
    candidates = [
        explicit,
        os.environ.get("CONNECTMESH_ROOT"),
        Path(__file__).resolve().parents[4],
    ]
    for candidate in candidates:
        if candidate and (Path(candidate) / "data").is_dir():
            return Path(candidate)
    raise RuntimeError(
        "Could not locate the repo root (no candidate contained a data/ dir).\n"
        "Set CONNECTMESH_ROOT=/path/to/ConnectMesh, or pass root= explicitly.\n"
        f"Tried: {[str(c) for c in candidates if c]}"
    )


def data_dir(root: str | Path | None = None) -> Path:
    return repo_root(root) / "data"

# From the IBM HI-Small spec — verified against the real file's unique values.
PAYMENT_FORMATS = [
    "ACH", "Bitcoin", "Cash", "Cheque", "Credit Card", "Reinvestment", "Wire",
]
CURRENCIES = [
    "Australian Dollar", "Bitcoin", "Brazil Real", "Canadian Dollar", "Euro",
    "Mexican Peso", "Ruble", "Rupee", "Saudi Riyal", "Shekel", "Swiss Franc",
    "UK Pound", "US Dollar", "Yen", "Yuan",
]

REQUIRED_COLUMNS = [
    "timestamp", "From Bank", "To Bank", "Account", "Account.1",
    "Amount Paid", "Amount Received", "Payment Currency", "Receiving Currency",
    "Payment Format", "is_laundering",
]

NUMERIC_FEATURES = [
    "log_amount_paid",
    "log_amount_received",
    "log_amount_gap",
    "is_cross_currency",
    "is_same_bank",
    "is_self_transfer",
    "hour",
    "day_of_week",
    "log_from_account_degree",
    "log_to_account_degree",
]


def feature_names() -> list[str]:
    return (
        NUMERIC_FEATURES
        + [f"fmt_{f}" for f in PAYMENT_FORMATS]
        + [f"cur_{c}" for c in CURRENCIES]
    )


def _check_columns(df: pd.DataFrame, region: str) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise SystemExit(
            f"data/region_{region}_*.parquet is missing columns {missing}.\n"
            "These partitions look like the thin placeholder schema. Regenerate "
            "the real ones with:\n"
            "  .venv/bin/python src/data/make_real_partitions.py\n"
            "(needs data/raw/HI-Small_Trans.csv — see that script's docstring)."
        )


def fit_account_stats(train: pd.DataFrame) -> dict:
    """Transaction counts per account, from THIS region's training split only."""
    return {
        "from_account": train["Account"].value_counts(),
        "to_account": train["Account.1"].value_counts(),
    }


def build_features(df: pd.DataFrame, stats: dict) -> np.ndarray:
    feats = pd.DataFrame(index=df.index)

    paid = df["Amount Paid"].clip(lower=0)
    received = df["Amount Received"].clip(lower=0)
    feats["log_amount_paid"] = np.log1p(paid)
    feats["log_amount_received"] = np.log1p(received)
    feats["log_amount_gap"] = np.log1p((paid - received).abs())

    feats["is_cross_currency"] = (
        df["Payment Currency"] != df["Receiving Currency"]
    ).astype(float)
    feats["is_same_bank"] = (df["From Bank"] == df["To Bank"]).astype(float)
    feats["is_self_transfer"] = (df["Account"] == df["Account.1"]).astype(float)

    ts = pd.to_datetime(df["timestamp"], format="%Y/%m/%d %H:%M")
    feats["hour"] = ts.dt.hour / 23.0
    feats["day_of_week"] = ts.dt.dayofweek / 6.0

    # Unseen accounts (present in test, absent from train) correctly get 0.
    feats["log_from_account_degree"] = np.log1p(
        df["Account"].map(stats["from_account"]).fillna(0.0)
    )
    feats["log_to_account_degree"] = np.log1p(
        df["Account.1"].map(stats["to_account"]).fillna(0.0)
    )

    for fmt in PAYMENT_FORMATS:
        feats[f"fmt_{fmt}"] = (df["Payment Format"] == fmt).astype(float)
    for cur in CURRENCIES:
        feats[f"cur_{cur}"] = (df["Payment Currency"] == cur).astype(float)

    return feats[feature_names()].to_numpy(dtype=np.float64)


def load_region_data(region: str, root: str | Path | None = None):
    """Returns X_train, y_train, X_test, y_test for one region.

    `root` lets a SuperNode point at its own data location — in a real
    federation each bank configures where its own transactions live.
    """
    base = data_dir(root)
    train = pd.read_parquet(base / f"region_{region}_train.parquet")
    test = pd.read_parquet(base / f"region_{region}_test.parquet")
    _check_columns(train, region)

    stats = fit_account_stats(train)
    X_train = build_features(train, stats)
    X_test = build_features(test, stats)
    return (
        X_train,
        train["is_laundering"].to_numpy(),
        X_test,
        test["is_laundering"].to_numpy(),
    )
