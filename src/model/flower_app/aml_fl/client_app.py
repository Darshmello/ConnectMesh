"""
Flower ClientApp — one of these runs as its own OS process per region, per
AGENTS.md's fixed decision (real separate processes, not simulation mode).

Each process reads only its own region's parquet file and sends back only
model weights. That is the mechanism behind the pitch's central claim: no
region's raw transactions ever leave its own process.

Which region this process is depends entirely on the --node-config passed to
flower-supernode at launch; nothing here is hardcoded.
"""
from flwr.app import ArrayRecord, Context, Message, MetricRecord, RecordDict
from flwr.clientapp import ClientApp

from aml_fl.features import load_region_data
from aml_fl.metrics import pr_auc
from aml_fl.task import create_model, fit_quietly, get_model_params, set_model_params

app = ClientApp()

def _region_data(region: str, root):
    # Flower spawns a fresh flwr-clientapp process per message, so a module-level
    # cache would never survive between calls. Measured cost of a reload: 0.1-0.6s.
    return load_region_data(region, root=root)


@app.train()
def train(msg: Message, context: Context):
    region = context.node_config["region"]
    root = context.node_config.get("root")  # this node's own data location

    model = create_model()  # LOCAL_ITERS per round, warm_start=True
    set_model_params(model, msg.content["arrays"].to_numpy_ndarrays())

    X_train, y_train, _, _ = _region_data(region, root)
    fit_quietly(model, X_train, y_train)

    content = RecordDict(
        {
            "arrays": ArrayRecord(get_model_params(model)),
            "metrics": MetricRecord(
                {"num-examples": len(X_train), "n_pos": int(y_train.sum())}
            ),
        }
    )
    return Message(content=content, reply_to=msg)


@app.evaluate()
def evaluate(msg: Message, context: Context):
    region = context.node_config["region"]
    root = context.node_config.get("root")

    model = create_model()
    set_model_params(model, msg.content["arrays"].to_numpy_ndarrays())

    _, _, X_test, y_test = _region_data(region, root)
    score = pr_auc(y_test, model.predict_proba(X_test)[:, 1])

    # Per-round monitoring only. The results.csv numbers come from
    # evaluate_federated.py, which scores the final weights with the exact
    # same code the local/pooled baselines use.
    content = RecordDict(
        {"metrics": MetricRecord({"num-examples": len(X_test), "pr_auc": score})}
    )
    return Message(content=content, reply_to=msg)
