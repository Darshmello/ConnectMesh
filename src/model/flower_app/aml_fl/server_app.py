"""
Flower ServerApp — the FedAvg coordinator, running as its own process
(flower-superlink), separate from every client.

Note what this file does NOT import: pandas, parquet, anything that could
read a region's transactions. It only ever handles weight arrays. That
separation is the demo's central claim, enforced here by construction.

It saves the final averaged weights to results/federated_model.npz.
Scoring those into results.csv is deliberately a separate step
(evaluate_federated.py) so the federated numbers are produced by exactly the
same code path as the local and pooled ones.
"""
import numpy as np
from flwr.app import ArrayRecord, Context
from flwr.serverapp import Grid, ServerApp
from flwr.serverapp.strategy import FedAvg

from aml_fl.features import REGIONS, repo_root
from aml_fl.task import create_model, get_model_params

app = ServerApp()



@app.main()
def main(grid: Grid, context: Context) -> None:
    num_rounds = int(context.run_config["num-server-rounds"])

    model = create_model()
    arrays = ArrayRecord(get_model_params(model))

    # All 5 banks must participate in every round. Flower's default is 2, which
    # lets training silently start (or continue) with a subset of the banks and
    # would make the federated row not a 5-bank result.
    n = len(REGIONS)
    strategy = FedAvg(
        fraction_train=1.0,
        fraction_evaluate=1.0,
        min_train_nodes=n,
        min_evaluate_nodes=n,
        min_available_nodes=n,
    )
    result = strategy.start(
        grid=grid, initial_arrays=arrays, num_rounds=num_rounds
    )

    model_path = repo_root() / "results" / "federated_model.npz"
    ndarrays = result.arrays.to_numpy_ndarrays()
    model_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(model_path, coef=ndarrays[0], intercept=ndarrays[1])
    print(f"\nSaved federated weights to {model_path}")
    print("Now run:  .venv/bin/python src/model/evaluate_federated.py")
