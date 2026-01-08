#!/usr/bin/env python3
"""
MCX-specific date-based splitter using 'timestamp' column
"""

import os
from typing import Tuple
import pandas as pd


def split_mcx_data_by_date(csv_path: str, split_date: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if not os.path.exists(csv_path):
        print(f"ERROR: {csv_path} not found.")
        return None, None

    df = pd.read_csv(csv_path)

    if "timestamp" not in df.columns:
        print("ERROR: 'timestamp' column not found in MCX CSV.")
        return None, None

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    split_dt = pd.to_datetime(split_date)

    train_df = df[df["timestamp"] < split_dt].copy()
    test_df  = df[df["timestamp"] >= split_dt].copy()

    if train_df.empty or test_df.empty:
        print("ERROR: Train or test set is empty after split.")
        return None, None

    print(f"MCX split: {len(train_df)} train rows, {len(test_df)} test rows")
    return train_df, test_df


if __name__ == "__main__":
    train_df, test_df = split_mcx_data_by_date("data/MCX_gold_daily.csv", "2021-01-01")
