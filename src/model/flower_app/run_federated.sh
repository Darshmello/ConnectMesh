#!/usr/bin/env bash
# Launches the whole federation: 1 superlink + 5 supernodes (one per region),
# then runs the app against them. Replaces the 7-manual-terminals dance.
#
# Usage, from the repo root:
#   bash src/model/flower_app/run_federated.sh
#
# Adam (role/demo): this is the minimum viable version — it works, but
# hardening it for the live demo is yours. Known rough edges are listed at
# the bottom of this file.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
APP_DIR="$REPO_ROOT/src/model/flower_app"
VENV_BIN="$REPO_ROOT/.venv/bin"
LOG_DIR="${LOG_DIR:-$REPO_ROOT/.flower_logs}"

# flower-superlink spawns `flower-superexec` by bare name, so the venv's bin
# MUST be on PATH or the superlink dies with FileNotFoundError.
export PATH="$VENV_BIN:$PATH"

# flwr packages this app and ships it to each SuperNode, which unpacks it
# elsewhere — so the app cannot find the repo from its own __file__. Both the
# ServerApp and the ClientApps inherit this.
export CONNECTMESH_ROOT="$REPO_ROOT"

# `flwr run . local-deployment` needs this entry in the user's Flower config.
# Fresh machines may not have it; add it without touching anything else.
FLWR_CFG="$HOME/.flwr/config.toml"
mkdir -p "$HOME/.flwr"
if ! grep -q "superlink.local-deployment" "$FLWR_CFG" 2>/dev/null; then
  printf '\n[superlink.local-deployment]\naddress = "127.0.0.1:9093"\ninsecure = true\n' >> "$FLWR_CFG"
  echo "added local-deployment to $FLWR_CFG"
fi

REGIONS=(americas apac emea india small_sub)
BASE_PORT=9094

mkdir -p "$LOG_DIR"
PIDS=()

# Free the Flower ports from any leftover run so we never talk to a stale
# superlink/supernode holding old state.
for port in 9091 9092 9093 9094 9095 9096 9097 9098; do
  stale=$(lsof -nP -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)
  [ -n "$stale" ] && { echo "freeing port $port (pid $stale)"; kill $stale 2>/dev/null || true; }
done
sleep 1

# Prefix every log line with a wall-clock time so cross-process ordering can be
# reconstructed. Flower's own lines have no timestamps.
stamp() { while IFS= read -r line; do printf '%s %s\n' "$(date +%H:%M:%S)" "$line"; done; }
export PYTHONUNBUFFERED=1

# Memory sampler: swap/free pages every 10s, to see whether pressure lines up
# with any failure.
( while true; do echo "$(date +%H:%M:%S) $(sysctl -n vm.swapusage | tr -s ' ') free_pages=$(vm_stat | awk '/Pages free/{print $3}')"; sleep 10; done ) > "$LOG_DIR/memory.log" 2>&1 &
PIDS+=($!)

cleanup() {
  echo ""
  echo "shutting down federation..."
  for pid in "${PIDS[@]:-}"; do kill "$pid" 2>/dev/null || true; done
  pkill -f "flower-supernode|flower-superlink|flower-superexec|flwr-clientapp|flwr-serverapp" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "starting superlink (Control 9093 / ServerAppIo 9091 / Fleet 9092)..."
flower-superlink --insecure 2>&1 | stamp > "$LOG_DIR/superlink.log" &
PIDS+=($!)
sleep 6

if ! grep -q "Fleet API" "$LOG_DIR/superlink.log"; then
  echo "superlink failed to start — see $LOG_DIR/superlink.log"; exit 1
fi

for i in "${!REGIONS[@]}"; do
  region="${REGIONS[$i]}"
  port=$((BASE_PORT + i))
  echo "  starting supernode for '$region' on port $port"
  flower-supernode \
    --insecure \
    --superlink 127.0.0.1:9092 \
    --clientappio-api-address "127.0.0.1:$port" \
    --node-config "region=\"$region\" root=\"$REPO_ROOT\"" \
    2>&1 | stamp > "$LOG_DIR/supernode-$region.log" &
  PIDS+=($!)
done

echo "waiting for all ${#REGIONS[@]} supernodes to register (up to 180s)..."
for _ in $(seq 1 90); do
  n=$(grep -c "Activated node_id" "$LOG_DIR/superlink.log" || true)
  [ "$n" -ge "${#REGIONS[@]}" ] && break
  sleep 2
done
if [ "$n" -lt "${#REGIONS[@]}" ]; then
  echo "only $n/${#REGIONS[@]} supernodes registered — aborting (see $LOG_DIR)"; exit 1
fi
echo "all $n supernodes registered."

echo ""
echo "running federated training..."
cd "$APP_DIR"
flwr run . local-deployment --stream 2>&1 | stamp | tee "$LOG_DIR/run.log"

echo ""
echo "training finished. Scoring the federated model into results.csv:"
cd "$REPO_ROOT"
"$VENV_BIN/python" src/model/evaluate_federated.py

# Known rough edges for whoever hardens this:
#  - superlink start still uses a fixed sleep
#  - stale-port cleanup kills whatever listens on 9091-9098
