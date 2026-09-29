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

# Filled in from real HI-Small_Trans.csv analysis (df["From Bank"].value_counts()
# and per-bank df.groupby("From Bank")["Is Laundering"].mean()):
#   bank: txn count, laundering rate
#   70: 449,859, 0.141%   10: 81,629, 0.063%   12: 79,754, 0.095%
#   1: 62,211, 0.080%     15: 52,511, 0.088%   211: 30,451, 0.085%
#   220: 52,417, 0.042%   116: 30,232, 0.076%  1665: 28,310, 0.074%
#   3: 38,413, 0.034%     7: 31,086, 0.035%    28: 28,584, 0.091%
#   20: 41,008, 0.163%    11: 29,676, 0.158%   22: 28,652, 0.140%
# small_sub is deliberately smallest (~70K rows) and highest-rate (~0.161%
# weighted) of the 5 — that's the region that should show the biggest
# "gain from joining" once local/federated/pooled are compared.
REGION_MAP = {
    "americas": [70],  # one dominant bank, ~450K txns alone
    "emea": [10, 12],
    "apac": [1, 15, 211],
    "india": [220, 116, 1665, 3, 7, 28],
    "small_sub": [20, 11],  # smallest, highest laundering rate — on purpose
}


def load_raw() -> pd.DataFrame:
    df = pd.read_csv(RAW_PATH)
    df = df.rename(columns={"Is Laundering": "is_laundering", "Timestamp": "timestamp"})
    # Add lowercase alias columns matching the placeholder schema
    # (make_placeholder_partitions.py) so src/model/flower_app's FEATURES/task.py
    # work unchanged against either fake or real partitions. Keep the original
    # IBM columns too (Payment Format etc.) for whoever adds real features later.
    df["amount"] = df["Amount Paid"]
    df["currency"] = df["Payment Currency"]
    df["from_bank"] = df["From Bank"]
    df["to_bank"] = df["To Bank"]
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
