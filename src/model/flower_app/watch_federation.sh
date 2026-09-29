#!/usr/bin/env bash
# Live, read-only view of a running federation. Open a SECOND terminal and run:
#   bash src/model/flower_app/watch_federation.sh
# Reads .flower_logs/ (written by run_federated.sh) and `ps`. Changes nothing.
# Ctrl-C to quit.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
LOG_DIR="${LOG_DIR:-$REPO_ROOT/.flower_logs}"
export LOG_DIR
exec python3 - <<'PY'
import os, re, subprocess, time, datetime, glob

LOG = os.environ["LOG_DIR"]
REGIONS = ["americas", "apac", "emea", "india", "small_sub"]
PORTS = {r: 9094 + i for i, r in enumerate(REGIONS)}
RED, GRN, YEL, DIM, RST = "\033[91m", "\033[92m", "\033[93m", "\033[2m", "\033[0m"
STAMP = re.compile(r"^(\d\d):(\d\d):(\d\d) ")
ANSI = re.compile(r"\x1b\[[0-9;]*m")
BAD = re.compile(r"UNAUTHENTICATED|Task stopped|Traceback|Error", re.I)

def sh(cmd):
    try: return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout
    except Exception: return ""

def read(path):
    try:
        with open(path, errors="replace") as f: return ANSI.sub("", f.read()).splitlines()
    except FileNotFoundError: return []

def age(line):
    """seconds since a HH:MM:SS-stamped log line"""
    m = STAMP.match(line or "")
    if not m: return None
    t = datetime.datetime.now().replace(hour=int(m[1]), minute=int(m[2]), second=int(m[3]), microsecond=0)
    d = (datetime.datetime.now() - t).total_seconds()
    return d + 86400 if d < -60 else d

def etime_s(s):
    p = s.strip().replace("-", ":").split(":"); p = [int(x) for x in p]
    while len(p) < 4: p.insert(0, 0)
    return p[0]*86400 + p[1]*3600 + p[2]*60 + p[3]

def fmt(a): return "  ?  " if a is None else f"{int(a)}s ago"

def frame():
    out = [f"ConnectMesh federation monitor   {time.strftime('%H:%M:%S')}   ({LOG})", ""]
    run = read(f"{LOG}/run.log"); sl = read(f"{LOG}/superlink.log")
    rounds = [l for l in run if "[ROUND" in l]
    if rounds:
        n = re.search(r"ROUND (\d+)/(\d+)", rounds[-1])
        done = any("Saved federated" in l for l in run)
        col = GRN if done else YEL
        out.append(f"{col}ROUND {n[1]}/{n[2]}{RST}  started {fmt(age(rounds[-1]))}"
                   + ("   DONE - model saved" if done else ""))
        sampled = [l for l in run if "Sampled" in l]
        if sampled: out.append(f"  {DIM}{sampled[-1][9:].strip()}{RST}")
    else:
        out.append(f"{DIM}no round started yet{RST}")
    act = sum("Activated node_id" in l for l in sl)
    out.append(f"nodes registered with superlink: {(GRN if act >= 5 else RED)}{act}/5{RST}")
    out.append("")

    ps = sh("ps -Ao pid,etime,command")
    apps = [l for l in ps.splitlines() if "flwr-clientapp" in l and "grep" not in l]
    out.append(f"{'region':<10}{'supernode':<11}{'clientapp':<22}{'last log line':<16}status")
    problems = []
    for r in REGIONS:
        lines = [l for l in read(f"{LOG}/supernode-{r}.log") if l.strip()]
        last = next((l for l in reversed(lines) if STAMP.match(l)), "")
        up = f"--clientappio-api-address 127.0.0.1:{PORTS[r]}" in ps and "flower-supernode" in ps
        mine = [l for l in apps if f":{PORTS[r]}" in l]
        ca, status = "idle", f"{GRN}ok{RST}"
        if mine:
            e = etime_s(mine[0].split()[1]); ca = f"RUNNING {e}s"
            started_last = "Start `flwr-clientapp`" in last
            if e > 20 and started_last:
                status = f"{RED}NO FIRST SERVER CALL {e}s (limit 30s){RST}"; problems.append(r)
            elif e > 20: status = f"{YEL}training{RST}"
        if any(BAD.search(l) for l in lines[-60:]):
            status = f"{RED}ERROR in log{RST}"; problems.append(r)
        if not up: status = f"{RED}supernode DOWN{RST}"
        out.append(f"{r:<10}{(GRN+'up'+RST if up else RED+'DOWN'+RST):<20}{ca:<22}{fmt(age(last)):<16}{status}")
    out.append("")

    mem = read(f"{LOG}/memory.log")
    out.append(f"memory: {mem[-1] if mem else '(no memory.log)'}")
    top = sh("ps -Ao rss,comm | sort -rn | head -3").splitlines()
    out.append("top 3: " + " | ".join(f"{int(l.split()[0])//1024}MB {os.path.basename(l.split(None,1)[1])[:18]}" for l in top if l.split()))
    out.append("")
    hits = []
    for f in glob.glob(f"{LOG}/*.log"):
        for l in read(f):
            if re.search(r"UNAUTHENTICATED|Task stopped", l): hits.append((os.path.basename(f), l.strip()[:90]))
    if hits:
        out.append(f"{RED}!! failure lines seen:{RST}")
        for f, l in hits[-4:]: out.append(f"   {f}: {l}")
    else:
        out.append(f"{GRN}no UNAUTHENTICATED / 'Task stopped' anywhere{RST}")
    return "\n".join(out)

try:
    while True:
        print("\033[2J\033[H" + frame(), flush=True)
        time.sleep(2)
except KeyboardInterrupt:
    pass
PY
