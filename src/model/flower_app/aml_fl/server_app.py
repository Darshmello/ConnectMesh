"""
Flower ServerApp — the FedAvg coordinator. Runs as its own process
(`flower-superlink`), separate from every client process. It only ever
receives model weights from clients, never raw data — see client_app.py.

After training, it writes one results.csv row per region with
setup="federated", matching the interface in AGENTS.md / CONTRIBUTING.md:
region, setup, pr_auc, recall_at_fpr, n_train, n_pos.
P3: recall_at_fpr and n_pos are left as TODOs here — wire up
src/eval/metrics.py's recall_at_fpr() once it's implemented.
"""
import csv
import os

from flwr.app import ArrayRecord, Context
from flwr.serverapp import Grid, ServerApp
from flwr.serverapp.strategy import FedAvg

from aml_fl.task import create_model, get_model_params

app = ServerApp()

RESULTS_PATH = "results/results.csv"
FIELDNAMES = ["region", "setup", "pr_auc", "recall_at_fpr", "n_train", "n_pos"]


def append_results(rows: list[dict]):
    write_header = not os.path.exists(RESULTS_PATH)
    with open(RESULTS_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


@app.main()
def main(grid: Grid, context: Context) -> None:
    num_rounds = context.run_config["num-server-rounds"]

    model = create_model()
    arrays = ArrayRecord(get_model_params(model))

    strategy = FedAvg(fraction_train=1.0, fraction_evaluate=1.0)
    result = strategy.start(grid=grid, initial_arrays=arrays, num_rounds=num_rounds)

    # result.history holds per-round MetricRecords from each client's evaluate();
    # take the last round's per-client pr_auc and write one results.csv row each.
    last_round_metrics = result.history[-1] if getattr(result, "history", None) else []
    rows = [
        {
            "region": m["region"],
            "setup": "federated",
            "pr_auc": m["pr_auc"],
            "recall_at_fpr": "",  # TODO(P3): fill in once recall_at_fpr() is implemented
            "n_train": "",  # TODO(P1/P2): thread n_train through from client train() metrics
            "n_pos": "",  # TODO(P3)
        }
        for m in last_round_metrics
    ]
    if rows:
        append_results(rows)
        print(f"Wrote {len(rows)} federated results rows to {RESULTS_PATH}")
    else:
        print("No per-client metrics found in result.history — check Flower's "
              "actual result object shape for this version before relying on this.")
