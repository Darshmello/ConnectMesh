#!/usr/bin/env bash
# One-command launcher: 1 Flower SuperLink (server) + 5 SuperNodes (one per region)
# + the federated run. Real separate processes, per AGENTS.md.
#
# Usage (from the repo root, with the venv that has requirements.txt installed):
#   ./run_federated.sh
#
# Output:
#   results/results.csv            (federated rows appended by server_app.py)
#   logs/run_<timestamp>/*.log     (execution log: superlink, each region, the run)
#
# NOTE: paths in aml_fl/task.py and server_app.py are relative ("data/...",
# "results/..."), so every process is started from the REPO ROOT.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$ROOT/src/model/flower_app"
REGIONS=(americas emea apac india small_sub)
PORTS=(9094 9095 9096 9097 9098)
CONN="local-deployment"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_DIR="$ROOT/logs/run_$STAMP"
mkdir -p "$LOG_DIR" "$ROOT/results"
cd "$ROOT"

for cmd in flower-superlink flower-supernode flwr; do
  command -v "$cmd" >/dev/null || { echo "ERROR: '$cmd' not found. Activate the venv with requirements.txt installed."; exit 1; }
done

PIDS=()
cleanup() {
  echo "Stopping background Flower processes..."
  for pid in "${PIDS[@]:-}"; do kill "$pid" 2>/dev/null || true; done
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Connection entry for `flwr run` (created only if missing)
CFG="${HOME}/.flwr/config.toml"
mkdir -p "$(dirname "$CFG")"
if ! grep -q "superlink.$CONN" "$CFG" 2>/dev/null; then
  printf '\n[superlink.%s]\naddress = "127.0.0.1:9093"\ninsecure = true\n' "$CONN" >> "$CFG"
  echo "Added [superlink.$CONN] to $CFG"
fi

echo "Starting SuperLink..."
flower-superlink --insecure > "$LOG_DIR/superlink.log" 2>&1 &
PIDS+=($!)
sleep 4

for i in "${!REGIONS[@]}"; do
  r="${REGIONS[$i]}"; p="${PORTS[$i]}"
  echo "Starting client: $r (port $p)"
  flower-supernode --insecure --superlink 127.0.0.1:9092 \
    --clientappio-api-address "127.0.0.1:$p" \
    --node-config "region='$r'" > "$LOG_DIR/client_$r.log" 2>&1 &
  PIDS+=($!)
done
sleep 6

echo "Running federated training (logs: $LOG_DIR)..."
flwr run "$APP_DIR" "$CONN" --stream 2>&1 | tee "$LOG_DIR/run.log"

echo
echo "Done. Results: $ROOT/results/results.csv"
echo "Log folder:    $LOG_DIR"
