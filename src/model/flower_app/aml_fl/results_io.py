"""
Writes and validates results/results.csv — the one interface every downstream
role depends on (Sahan's gain table, Adam's demo page).

write_setup_rows() is idempotent per setup: re-running the local baseline
replaces the local rows and leaves federated/pooled untouched. Without this,
every re-run would silently append duplicates and the gain table would read
them as extra regions.

validate_results() exists because of a real incident during the build: a
crashed federated run left stale fabricated rows from the old placeholder
generator sitting in results.csv alongside genuine local/pooled rows. The
file looked complete and plausible, and would have put invented numbers on a
slide. The n_train cross-check below catches exactly that.
"""
from pathlib import Path

import pandas as pd

from aml_fl.features import REGIONS, repo_root

COLUMNS = ["region", "setup", "pr_auc", "recall_at_fpr", "n_train", "n_pos"]
SETUPS = ["local", "federated", "pooled"]
SETUP_ORDER = {s: i for i, s in enumerate(SETUPS)}


def results_path(root: str | Path | None = None) -> Path:
    return repo_root(root) / "results" / "results.csv"


def write_setup_rows(rows: list[dict], setup: str, root=None) -> None:
    path = results_path(root)
    new = pd.DataFrame(rows, columns=COLUMNS)

    if path.exists():
        existing = pd.read_csv(path)
        existing = existing[existing["setup"] != setup]
        combined = pd.concat([existing, new], ignore_index=True)
    else:
        combined = new

    combined["_order"] = combined["setup"].map(SETUP_ORDER)
    combined = (
        combined.sort_values(["region", "_order"]).drop(columns="_order").reset_index(drop=True)
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(path, index=False)
    print(f"wrote {len(new)} '{setup}' rows to {path}")


def validate_results(root=None) -> list[str]:
    """Returns a list of problems; empty means the file is internally
    consistent. Does not prove the numbers are correct — only that they were
    produced by real runs over the real partitions."""
    path = results_path(root)
    if not path.exists():
        return [f"{path} does not exist"]

    df = pd.read_csv(path)
    problems = []

    missing = [
        (r, s) for r in REGIONS for s in SETUPS
        if df[(df.region == r) & (df.setup == s)].empty
    ]
    if missing:
        problems.append(f"missing rows for {missing}")

    dupes = df.duplicated(subset=["region", "setup"]).sum()
    if dupes:
        problems.append(f"{dupes} duplicate region/setup rows")

    for col in ("pr_auc", "recall_at_fpr"):
        bad = df[(df[col] < 0) | (df[col] > 1)]
        if not bad.empty:
            problems.append(f"{col} outside [0,1] for {bad.region.tolist()}")

    # local and federated both train on that region's own data, so n_train
    # must agree. A mismatch means one of them came from somewhere else.
    for region in REGIONS:
        rows = {s: df[(df.region == region) & (df.setup == s)] for s in SETUPS}
        if rows["local"].empty or rows["federated"].empty:
            continue
        local_n, fed_n = int(rows["local"].n_train.iloc[0]), int(rows["federated"].n_train.iloc[0])
        if local_n != fed_n:
            problems.append(
                f"{region}: local n_train={local_n} != federated n_train={fed_n} "
                "(federated rows may be stale or fabricated)"
            )

    pooled = df[df.setup == "pooled"]
    local_total = df[df.setup == "local"].n_train.sum()
    if not pooled.empty and int(pooled.n_train.iloc[0]) != int(local_total):
        problems.append(
            f"pooled n_train={int(pooled.n_train.iloc[0])} != sum of local n_train={int(local_total)}"
        )

    return problems


if __name__ == "__main__":
    found = validate_results()
    if found:
        print("results.csv PROBLEMS:")
        for p in found:
            print(f"  - {p}")
        raise SystemExit(1)
    print("results.csv looks internally consistent")
