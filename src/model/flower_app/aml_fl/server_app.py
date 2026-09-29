"""Flower ServerApp and federated evaluation-result writer.

The server receives model arrays during training and the following aggregate
evaluation fields after the final round: region, PR-AUC, recall at fixed FPR,
training-row count, and positive-label count. It never opens a partition file.
"""
from __future__ import annotations

import csv
from pathlib import Path

from flwr.app import ArrayRecord, Context, MetricRecord
from flwr.serverapp import Grid, ServerApp
from flwr.serverapp.strategy import FedAvg

from aml_fl.task import create_model, get_model_params

app = ServerApp()

REPO_ROOT = Path(__file__).resolve().parents[4]
RESULTS_PATH = REPO_ROOT / "results" / "results.csv"
FIELDNAMES = ["region", "setup", "pr_auc", "recall_at_fpr", "n_train", "n_pos"]


class RecordingFedAvg(FedAvg):
    """FedAvg that retains the final per-region aggregate metrics for CSV.

    Flower's standard result object stores a global, weighted metric record.
    The demo also needs a row per region, so this callback records those
    aggregate metrics while returning the normal weighted PR-AUC/recall
    summary to Flower. No client data rows or labels are retained.
    """

    def __init__(self):
        self.per_region: dict[str, dict] = {}
        super().__init__(
            fraction_train=1.0,
            fraction_evaluate=1.0,
            min_train_nodes=5,
            min_evaluate_nodes=5,
            min_available_nodes=5,
            evaluate_metrics_aggr_fn=self._aggregate_evaluation_metrics,
        )

    def _aggregate_evaluation_metrics(
        self, records, weighted_by_key: str
    ) -> MetricRecord:
        weighted_totals = {"pr_auc": 0.0, "recall_at_fpr": 0.0}
        total_weight = 0.0
        self.per_region = {}

        for record_dict in records:
            metrics = record_dict["metrics"]
            region = str(metrics["region"])
            weight = float(metrics[weighted_by_key])
            row = {
                "region": region,
                "setup": "federated",
                "pr_auc": float(metrics["pr_auc"]),
                "recall_at_fpr": float(metrics["recall_at_fpr"]),
                "n_train": int(metrics["n_train"]),
                "n_pos": int(metrics["n_pos"]),
            }
            self.per_region[region] = row
            total_weight += weight
            for metric in weighted_totals:
                weighted_totals[metric] += row[metric] * weight

        if total_weight == 0:
            return MetricRecord({"num-examples": 0})
        return MetricRecord(
            {
                "num-examples": total_weight,
                **{
                    name: value / total_weight
                    for name, value in weighted_totals.items()
                },
            }
        )


def replace_federated_rows(rows: list[dict]) -> None:
    """Replace only federated rows; retain computed local/pooled controls."""
    existing = []
    if RESULTS_PATH.exists():
        with RESULTS_PATH.open(newline="") as file:
            existing = [
                row
                for row in csv.DictReader(file)
                if row.get("setup") != "federated"
            ]

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS_PATH.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(existing)
        writer.writerows(rows)


@app.main()
def main(grid: Grid, context: Context) -> None:
    num_rounds = context.run_config["num-server-rounds"]
    model = create_model()
    arrays = ArrayRecord(get_model_params(model))

    strategy = RecordingFedAvg()
    strategy.start(
        grid=grid,
        initial_arrays=arrays,
        num_rounds=num_rounds,
    )

    rows = list(strategy.per_region.values())
    if not rows:
        raise RuntimeError(
            "FedAvg returned no per-region evaluation metrics. Check that all "
            "five clients completed the final evaluation round."
        )
    replace_federated_rows(rows)
    print(f"Wrote {len(rows)} computed federated result rows to {RESULTS_PATH}")
