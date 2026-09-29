"""
Scoring functions, used identically by the local, pooled and federated runs
so the three numbers in results.csv are directly comparable.

src/eval/metrics.py (Sahan's analysis layer) imports these rather than
redefining them — same reason as features.py: if the setups were scored by
different code, the comparison would be meaningless.
"""
import numpy as np
from sklearn.metrics import average_precision_score, roc_curve


def pr_auc(y_true, y_score) -> float:
    """Headline metric. Never accuracy — laundering is ~0.1% of rows, so
    predicting 'never launders' scores 99.9% and detects nothing."""
    return float(average_precision_score(y_true, y_score))


def recall_at_fpr(y_true, y_score, target_fpr: float = 0.01) -> float:
    """What fraction of real laundering we catch if we accept a fixed
    false-alarm rate. This is the operationally meaningful number: a bank
    can only afford to investigate so many false alerts."""
    fpr, tpr, _ = roc_curve(y_true, y_score)
    idx = int(np.searchsorted(fpr, target_fpr, side="right")) - 1
    return float(tpr[max(idx, 0)])
