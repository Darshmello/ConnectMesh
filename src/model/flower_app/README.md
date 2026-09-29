# Flower app — real separate processes, one per region

Per `AGENTS.md`'s fixed decision: this runs as **one Flower server process
+ 5 client processes**, all on one laptop (different ports), not Flower's
single-process simulation mode. That's what makes "no region's data leaves
its own process" a checkable fact — the server code
(`aml_fl/server_app.py`) never imports pandas or touches a parquet file; it
only ever receives model weights.

## Setup (once)

```bash
cd src/model/flower_app
/path/to/repo/.venv/bin/pip install -e .
```

## Run — 7 terminals, all from `src/model/flower_app/`

**Terminal 1 — the server:**
```bash
flower-superlink --insecure
```

**Terminals 2–6 — one client per region** (repeat for each of the 5 region
names in `AGENTS.md`'s `REGION_MAP`, each on its own port):
```bash
flower-supernode --insecure --superlink 127.0.0.1:9092 \
  --host 127.0.0.1 --port 9094 \
  --node-config "region='americas'"

flower-supernode --insecure --superlink 127.0.0.1:9092 \
  --host 127.0.0.1 --port 9095 \
  --node-config "region='emea'"

# ...same pattern for apac (9096), india (9097), small_sub (9098)
```

**Terminal 7 — kick off the run**, once all 5 supernodes above are up and
connected:
```bash
flwr run . local-deployment --stream
```

(`local-deployment` needs a `.flwr/config.toml` pointing at the superlink —
see the [Deployment Engine
guide](https://flower.ai/docs/framework/how-to-run-flower-with-deployment-engine.html)
if it's not already scaffolded here.)

## Evaluation output

Each client evaluates the final global model against its own local test
partition and returns only aggregate metrics: PR-AUC, recall at 1% false
positive rate, training-row count, positive-label count, and its region name.
The server replaces `setup=federated` rows in `results/results.csv`; it
does not read a partition or receive transaction rows.

`aml_fl/features.py` defines the shared three-column, non-identifying feature
matrix used by local, pooled, and federated runs. This avoids bank-local
one-hot columns with incompatible parameter shapes. The first real
five-process run still needs to be performed before results are presented.
