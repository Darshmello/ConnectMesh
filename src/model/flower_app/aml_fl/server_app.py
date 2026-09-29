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

from aml_fl.task import REGIONS, create_model, get_model_params

app = ServerApp()


class CollectingFedAvg(FedAvg):
    """FedAvg that also remembers each client's own metrics from the last
    round (the stock strategy only exposes weighted averages)."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.train_by_region = {}
        self.eval_by_region = {}

    def aggregate_train(self, server_round, replies):
        replies = list(replies)
        for msg in replies:
            if msg.has_content():
                m = msg.content["metrics"]
                self.train_by_region[REGIONS[int(m["region_id"])]] = dict(m)
        return super().aggregate_train(server_round, replies)

    def aggregate_evaluate(self, server_round, replies):
        replies = list(replies)
        for msg in replies:
            if msg.has_content():
                m = msg.content["metrics"]
                self.eval_by_region[REGIONS[int(m["region_id"])]] = dict(m)
        return super().aggregate_evaluate(server_round, replies)

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

    strategy = CollectingFedAvg(fraction_train=1.0, fraction_evaluate=1.0)
    strategy.start(grid=grid, initial_arrays=arrays, num_rounds=num_rounds)

    # Last round's per-client metrics -> one results.csv row per region.
    rows = [
        {
            "region": region,
            "setup": "federated",
            "pr_auc": m["pr_auc"],
            "recall_at_fpr": "",  # TODO(P3): needs recall_at_fpr() in src/eval/metrics.py
            "n_train": int(strategy.train_by_region.get(region, {}).get("num-examples", 0)) or "",
            "n_pos": int(strategy.train_by_region.get(region, {}).get("n_pos", 0)),
        }
        for region, m in strategy.eval_by_region.items()
    ]
    if rows:
        append_results(rows)
        print(f"Wrote {len(rows)} federated results rows to {RESULTS_PATH}")
    else:
        print("ERROR: no per-client evaluate metrics were collected — the run did not complete.")
