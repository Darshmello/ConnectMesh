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

Results land in `results/results.csv` with `setup=federated`, one row per
region, appended by `server_app.py`'s `main()`.

## What's still a TODO here (P2/P3, not blocking the plumbing)

- `recall_at_fpr` and `n_pos` columns are written empty — wire up
  `src/eval/metrics.py`'s `recall_at_fpr()` once implemented, and thread
  `n_train`/`n_pos` counts through from each client's `train()` metrics.
- `FEATURES = ["amount"]` in `task.py` is deliberately minimal so the
  pipeline runs end to end today — add real features once real data exists.
- `result.history` shape in `server_app.py` is written from the quickstart's
  general pattern but **not run end-to-end against real 5-process
  deployment yet** — the first person to actually run this for real should
  expect to fix the exact attribute/shape it reads from Flower's result
  object for this version, and should not treat this file as tested.
