"""
Real partitioning script — run this once data/raw/HI-Small_Trans.csv exists.
Produces the same interface make_placeholder_partitions.py fakes:
  data/region_<name>_train.parquet / _test.parquet
Columns kept: Timestamp, From Bank, Account, To Bank, Account.1,
Amount Received, Receiving Currency, Amount Paid, Payment Currency,
Payment Format, is_laundering (renamed from "Is Laundering").

Run: .venv/bin/python src/data/make_real_partitions.py

P1: REGION_MAP is the whole ballgame — see PLAN.md's risk section and
AGENTS.md's "Fixed decisions". Don't compute this automatically (e.g.
bank_id % 5); hand-pick it so region sizes and laundering rates differ,
with one deliberately small/high-rate region. Fill in real "From Bank" /
"To Bank" values from the CSV once you've looked at value_counts().
"""
import pandas as pd

RAW_PATH = "data/raw/HI-Small_Trans.csv"

# PLACEHOLDER — P1 replaces these bank-id lists with a real, deliberately
# skewed split after inspecting df["From Bank"].value_counts() /
# df["To Bank"].value_counts() on the real file.
REGION_MAP = {
    "americas": [],
    "emea": [],
    "apac": [],
    "india": [],
    "small_sub": [],  # keep this one deliberately small
}


def load_raw() -> pd.DataFrame:
    df = pd.read_csv(RAW_PATH)
    df = df.rename(columns={"Is Laundering": "is_laundering", "Timestamp": "timestamp"})
    return df.sort_values("timestamp")


def assign_region(df: pd.DataFrame) -> pd.Series:
    bank_to_region = {
        bank: region for region, banks in REGION_MAP.items() for bank in banks
    }
    # a transaction belongs to the sender's region
    return df["From Bank"].map(bank_to_region)


def main():
    if not REGION_MAP["americas"]:
        raise SystemExit(
            "REGION_MAP is still empty placeholders — P1 must fill in real "
            "bank IDs from data/raw/HI-Small_Trans.csv before running this."
        )

    df = load_raw()
    df["region"] = assign_region(df)
    df = df.dropna(subset=["region"])  # drop banks nobody assigned to a region

    for region, group in df.groupby("region"):
        split = int(len(group) * 0.8)  # time-based split, already sorted above
        train, test = group.iloc[:split], group.iloc[split:]
        train.to_parquet(f"data/region_{region}_train.parquet", index=False)
        test.to_parquet(f"data/region_{region}_test.parquet", index=False)
        rate = group["is_laundering"].mean()
        print(f"{region}: {len(train)} train / {len(test)} test rows, "
              f"laundering rate {rate:.4%}")


if __name__ == "__main__":
    main()
