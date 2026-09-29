# Flower app — real separate processes, one per region

Per `AGENTS.md`'s fixed decision: this runs as **one Flower server process
+ 5 client processes**, all on one laptop (different ports), not Flower's
single-process simulation mode. That's what makes "no region's data leaves
its own process" a checkable fact — the server code
(`aml_fl/server_app.py`) never imports pandas or touches a parquet file; it
only ever receives model weights.

## Run

See `docs/RUN_FEDERATED.md` (repo root) for install, the one-command launcher
(`run_federated.sh`), the live monitor (`watch_federation.sh`) and
verification. The old 7-terminal procedure was replaced by that launcher.
