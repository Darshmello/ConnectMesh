"""
Model + data loading shared by client_app.py and server_app.py.
Adapted from Flower's official quickstart-sklearn (@flwrlabs/quickstart-sklearn,
generated fresh against our installed flwr==1.30.0 to match its current API —
see AGENTS.md, "start from the official quickstart, API changes between
versions").

P2: FEATURES is deliberately minimal (just amount) so this runs end to end
today. Add more columns from the partition schema (payment format one-hot,
hour-of-day, etc.) once the pipeline works — don't block on feature
engineering before proving the plumbing works.
"""
import numpy as np
import pandas as pd
from flwr.common import NDArrays
from sklearn.linear_model import LogisticRegression

from aml_fl.features import FEATURES, make_features

UNIQUE_LABELS = [0, 1]  # is_laundering: 0 or 1
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]


def get_model_params(model: LogisticRegression) -> NDArrays:
    if model.fit_intercept:
        return [model.coef_, model.intercept_]
    return [model.coef_]


def set_model_params(model: LogisticRegression, params: NDArrays) -> LogisticRegression:
    model.coef_ = params[0]
    if model.fit_intercept:
        model.intercept_ = params[1]
    return model


def set_initial_params(model: LogisticRegression, n_features: int):
    """Params are uninitialized until model.fit() is called, but the server
    asks clients for initial parameters at launch — so zero-init first."""
    model.classes_ = np.array(UNIQUE_LABELS)
    model.coef_ = np.zeros((1, n_features))
    if model.fit_intercept:
        model.intercept_ = np.zeros((1,))


def create_model() -> LogisticRegression:
    model = LogisticRegression(
        max_iter=1,  # one local epoch per federated round, same as the quickstart
        warm_start=True,  # keep weights between rounds instead of resetting
        class_weight="balanced",  # per AGENTS.md: "logistic regression with class weighting"
    )
    set_initial_params(model, n_features=len(FEATURES))
    return model


def load_region_data(region: str):
    """Reads data/region_<region>_{train,test}.parquet — the same interface
    make_real_partitions.py / make_placeholder_partitions.py produce."""
    data_dir = REPO_ROOT / "data"
    train = pd.read_parquet(data_dir / f"region_{region}_train.parquet")
    test = pd.read_parquet(data_dir / f"region_{region}_test.parquet")
    if "is_laundering" not in train or "is_laundering" not in test:
        raise ValueError("both partition files must include is_laundering")

    X_train, y_train = make_features(train), train["is_laundering"].astype(int).values
    X_test, y_test = make_features(test), test["is_laundering"].astype(int).values
    return X_train, y_train, X_test, y_test
