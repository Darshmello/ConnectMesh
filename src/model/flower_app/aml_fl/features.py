"""Shared, deterministic feature transformation for every evaluation setup."""
import numpy as np
import pandas as pd

# One-hot encoding bank-local categories would create different column counts
# per client and make FedAvg parameter aggregation invalid.
FEATURES = ("log_amount", "hour_utc", "same_bank_transfer")


def _first_present(frame: pd.DataFrame, names: list[str], default=0):
    for name in names:
        if name in frame.columns:
            return frame[name]
    return pd.Series(default, index=frame.index)


def make_features(frame: pd.DataFrame) -> np.ndarray:
    """Return the shared, non-identifying numeric feature matrix.

    Placeholder partitions use lowercase canonical names while the IBM source
    keeps its original headers. Supporting both lets the backend run before
    and after the real partitioner replaces placeholders.
    """
    raw_amount = _first_present(frame, ["amount", "Amount Received", "Amount Paid"])
    amount = pd.to_numeric(raw_amount, errors="coerce").fillna(0).clip(lower=0)

    raw_timestamp = _first_present(frame, ["timestamp", "Timestamp"], default=None)
    timestamp = pd.to_datetime(raw_timestamp, errors="coerce", utc=True)
    hour = timestamp.dt.hour.fillna(0).astype(float) / 23.0

    from_bank = _first_present(frame, ["from_bank", "From Bank"], default="")
    to_bank = _first_present(frame, ["to_bank", "To Bank"], default="")
    same_bank = (from_bank.astype(str) == to_bank.astype(str)).astype(float)

    return np.column_stack((np.log1p(amount), hour, same_bank))
