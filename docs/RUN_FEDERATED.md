# Run the 5-bank federated training (for a teammate's machine)

Goal: one clean run of 1 Flower server + 5 client processes (americas, apac,
emea, india, small_sub) for 20 rounds on this laptop. Real data is already in
`data/region_*_{train,test}.parquet` (committed). You do NOT need the 454 MB
raw CSV or any Kaggle login.

Status: one successful run exists (see `results/README.md`). Use this runbook to reproduce it or to run it on a new machine.

Why we are asking you: on Darsh's 8 GB Mac a client process hung ~60 s at
startup (swap was 7 GB), Flower's 30 s task-token expired, and the run died.
16 GB should avoid it. **Whether it does is itself the result we need.**

## 1. Install (once, ~3 min) — Python 3.10 or 3.11
```bash
git clone https://github.com/Darshmello/ConnectMesh.git
cd ConnectMesh
git checkout role/model
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## 2. Before you run
- Quit Chrome and other heavy apps. Check free memory:
  `sysctl vm.swapusage` (want "used" near 0) and `memory_pressure | tail -1`.
- Ports 9091-9098 must be free (the launcher frees them for you).
- Keep the laptop plugged in and awake: `caffeinate -dims &`

## 3. Run (two terminals, both from the repo root)
**Terminal A - the run** (~15-25 min):
```bash
bash src/model/flower_app/run_federated.sh
```
**Terminal B - live monitor** (read-only, refreshes every 2 s):
```bash
bash src/model/flower_app/watch_federation.sh
```
Healthy = "nodes registered 5/5", `ROUND n/20` advancing about once a
minute, every region row green. The launcher aborts by itself if fewer than
5 nodes register. At the end it scores the model into `results/results.csv`.

## 4. If a row turns red: NO FIRST SERVER CALL
That is the exact failure we are hunting. While it is red (before ~30 s):
```bash
pgrep -f flwr-clientapp          # pick the stuck pid
sample <pid> 5 > sample.txt      # macOS: shows where the process is stuck
```
Keep `sample.txt`. Do not restart until you have saved logs (step 6).

## 5. Verify success (all must be true)
```bash
grep -c "ROUND" .flower_logs/run.log                  # 20
grep -l "UNAUTHENTICATED\|Task stopped" .flower_logs/supernode-*.log   # prints nothing
ls results/federated_model.npz                         # exists
.venv/bin/python src/model/run_baselines.py            # local+pooled rows (~2 min), run before evaluate if results.csv lacks them
.venv/bin/python src/model/evaluate_federated.py       # federated rows
.venv/bin/python src/model/flower_app/aml_fl/results_io.py   # validates all 15 rows
```

## 6. Send back (success OR failure) — do not edit code
```bash
tar czf run_logs.tgz .flower_logs results/results.csv sample.txt 2>/dev/null
```
Send `run_logs.tgz` + your Mac model and RAM. Failure logs are useful too.

## Troubleshooting
- `FileNotFoundError: flower-superexec`: run via the script, it sets PATH.
- Port in use: `lsof -nP -iTCP:9091-9098 -sTCP:LISTEN`, kill the pid, rerun.
- Stop everything: Ctrl-C in Terminal A, then
  `pkill -f "flower-supernode|flower-superlink|flwr-clientapp|flwr-serverapp"`.
