"""
Flower ClientApp — this is what runs as one of the 5 separate OS processes
(one per region), per AGENTS.md's "Fixed decisions": real separate
processes, not simulation mode. Each process only ever sees its own
region's parquet file — the "arrays" it sends back are model weights, never
raw rows. That's the entire mechanism behind the "no region's data leaves
its own process" claim.

Each process is launched with its own --node-config "region=<name>" (see
the flower-supernode commands in this directory's README.md); this file
never hardcodes which region it is.
"""
import warnings

from flwr.app import ArrayRecord, Context, Message, MetricRecord, RecordDict
from flwr.clientapp import ClientApp
from sklearn.metrics import average_precision_score

from aml_fl.task import create_model, get_model_params, load_region_data, set_model_params

app = ClientApp()


@app.train()
def train(msg: Message, context: Context):
    region = context.node_config["region"]

    model = create_model()
    set_model_params(model, msg.content["arrays"].to_numpy_ndarrays())

    X_train, y_train, _, _ = load_region_data(region)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model.fit(X_train, y_train)

    metrics = {"num-examples": len(X_train), "region": region}
    content = RecordDict(
        {"arrays": ArrayRecord(get_model_params(model)), "metrics": MetricRecord(metrics)}
    )
    return Message(content=content, reply_to=msg)


@app.evaluate()
def evaluate(msg: Message, context: Context):
    region = context.node_config["region"]

    model = create_model()
    set_model_params(model, msg.content["arrays"].to_numpy_ndarrays())

    _, _, X_test, y_test = load_region_data(region)
    y_score = model.predict_proba(X_test)[:, 1]
    pr_auc = average_precision_score(y_test, y_score)  # the headline metric, per AGENTS.md

    metrics = {"num-examples": len(X_test), "pr_auc": pr_auc, "region": region}
    content = RecordDict({"metrics": MetricRecord(metrics)})
    return Message(content=content, reply_to=msg)
