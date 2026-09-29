"""
Generates FAKE partitions matching the real interface, so P2/P3/P5 can write
code against the real schema before P1 has real data ready.

Schema (must match what P1 produces from the real IBM HI-Small dataset):
  data/region_<name>_train.parquet
  data/region_<name>_test.parquet
Columns: timestamp, from_bank, to_bank, amount, currency, is_laundering (0/1)

Run: .venv/bin/python src/data/make_placeholder_partitions.py
"""
import numpy as np
import pandas as pd

REGIONS = {
    "americas": dict(n=4000, laundering_rate=0.004),
    "emea": dict(n=3000, laundering_rate=0.002),
    "apac": dict(n=3500, laundering_rate=0.003),
    "india": dict(n=2500, laundering_rate=0.006),
    "small_sub": dict(n=600, laundering_rate=0.01),  # deliberately smallest region
}

rng = np.random.default_rng(42)


def make_region(name: str, n: int, laundering_rate: float) -> pd.DataFrame:
    timestamps = pd.date_range("2024-01-01", periods=n, freq="min")
    df = pd.DataFrame(
        {
            "timestamp": timestamps,
            "from_bank": rng.integers(1000, 1010, size=n),
            "to_bank": rng.integers(1000, 1010, size=n),
            "amount": rng.exponential(500, size=n).round(2),
            "currency": rng.choice(["USD", "EUR", "GBP"], size=n),
            "is_laundering": rng.binomial(1, laundering_rate, size=n),
        }
    )
    return df


def main():
    for name, cfg in REGIONS.items():
        df = make_region(name, **cfg)
        split = int(len(df) * 0.8)  # time-based split, not random
        train, test = df.iloc[:split], df.iloc[split:]
        train.to_parquet(f"data/region_{name}_train.parquet", index=False)
        test.to_parquet(f"data/region_{name}_test.parquet", index=False)
        print(f"{name}: {len(train)} train / {len(test)} test rows written")


if __name__ == "__main__":
    main()
