"""
The model, shared by all three setups. Per AGENTS.md's fixed decisions:
logistic regression with class weighting, identical for local, federated and
pooled.

Equal optimization budget
-------------------------
All three setups get the same total number of solver iterations
(TOTAL_ITERS), so the comparison measures *data access* rather than training
effort:
  local    : one fit, max_iter=TOTAL_ITERS
  pooled   : one fit, max_iter=TOTAL_ITERS
  federated: NUM_ROUNDS rounds x LOCAL_ITERS iterations = TOTAL_ITERS

Without this, federated would look artificially bad purely for being given
less optimization, and the headline result would be an artefact of the
config rather than a real finding.
"""
import warnings

import numpy as np
from flwr.common import NDArrays
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression

from aml_fl.features import feature_names, load_region_data  # noqa: F401 (re-exported)

NUM_ROUNDS = 20
LOCAL_ITERS = 5
TOTAL_ITERS = NUM_ROUNDS * LOCAL_ITERS

UNIQUE_LABELS = [0, 1]  # is_laundering


def get_model_params(model: LogisticRegression) -> NDArrays:
    if model.fit_intercept:
        return [model.coef_, model.intercept_]
    return [model.coef_]


def set_model_params(model: LogisticRegression, params: NDArrays) -> LogisticRegression:
    model.coef_ = params[0]
    if model.fit_intercept:
        model.intercept_ = params[1]
    return model


def set_initial_params(model: LogisticRegression, n_features: int) -> None:
    """Params are uninitialized until fit() is called, but the Flower server
    asks clients for initial parameters at launch — so zero-init first."""
    model.classes_ = np.array(UNIQUE_LABELS)
    model.coef_ = np.zeros((1, n_features))
    if model.fit_intercept:
        model.intercept_ = np.zeros((1,))


def create_model(max_iter: int = LOCAL_ITERS, warm_start: bool = True) -> LogisticRegression:
    """Federated clients use the defaults (a few iterations per round, weights
    carried across rounds). Baselines pass max_iter=TOTAL_ITERS,
    warm_start=False for a single equivalent-budget fit."""
    model = LogisticRegression(
        max_iter=max_iter,
        warm_start=warm_start,
        class_weight="balanced",  # AGENTS.md: laundering is ~0.1% of rows
        solver="lbfgs",
    )
    set_initial_params(model, n_features=len(feature_names()))
    return model


def fit_quietly(model: LogisticRegression, X, y) -> LogisticRegression:
    """Partial-budget fits legitimately stop before convergence — that's the
    design, not a problem to be surfaced as a warning on every round."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=ConvergenceWarning)
        model.fit(X, y)
    return model
