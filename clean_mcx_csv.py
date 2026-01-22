#!/usr/bin/env python3
"""
Convert raw MCX Gold CSV to standardized MCX_gold_daily.csv
Expected final columns:
[timestamp, symbol, open, high, low, close, volume]
"""

import os

import pandas as pd

RAW_PATH = "raw/MCX_gold_raw.csv"  # from Investing.com / Kaggle
OUT_PATH = "data/MCX_gold_daily.csv"
SYMBOL = "MCX:GOLD"


def convert_volume(vol_str):
    """Converts volume strings like '21.65K' or '1.2M' to float."""
    if isinstance(vol_str, (int, float)):
        return float(vol_str)
    vol_str = str(vol_str).strip().upper()
    if not vol_str or vol_str == "-":
        return 0.0

    if vol_str.endswith("K"):
        return float(vol_str[:-1]) * 1_000
    if vol_str.endswith("M"):
        return float(vol_str[:-1]) * 1_000_000
    if vol_str.endswith("B"):
        return float(vol_str[:-1]) * 1_000_000_000
    return float(vol_str)


def main():
    os.makedirs("data", exist_ok=True)

    df = pd.read_csv(RAW_PATH)

    # Adjust these column names to match your raw file exactly.
    # Common Investing.com headers: Date, Price, Open, High, Low, Vol., Change %
    # Example mapping:
    col_map = {
        "Date": "timestamp",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Price": "close",  # sometimes 'Close' or 'Last'
        "Vol.": "volume",
    }
    df = df.rename(columns=col_map)

    # Keep required columns only
    df = df[["timestamp", "open", "high", "low", "close", "volume"]].copy()

    # --- Data Cleaning ---

    # 1. Clean and convert numeric columns
    for col in ["open", "high", "low", "close"]:
        if df[col].dtype == "object":
            df[col] = df[col].str.replace(",", "", regex=False)
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 2. Clean and convert volume
    if "volume" in df.columns and df["volume"].dtype == "object":
        df["volume"] = df["volume"].apply(convert_volume)

    # 3. Parse date and sort
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        format="%d-%m-%Y",  # <-- IMPORTANT: day-month-year
        errors="coerce",
    )

    # --- Final Processing ---

    # Drop rows where essential data couldn't be parsed
    df = df.dropna(subset=["timestamp", "open", "high", "low", "close"])

    # Sort by date
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Add symbol column
    df["symbol"] = SYMBOL

    # Reorder columns
    df = df[["timestamp", "symbol", "open", "high", "low", "close", "volume"]]

    # Filter for desired date range
    df = df[df["timestamp"] >= "2016-01-01"]

    df.to_csv(OUT_PATH, index=False)

    print("✓ MCX_gold_daily.csv created")
    print(f"Rows: {len(df)}")
    print(f"Date range: {df['timestamp'].min()} → {df['timestamp'].max()}")
    print("Columns:", df.columns.tolist())
    print("First row:\n", df.iloc[0])
    print("Last row:\n", df.iloc[-1])


if __name__ == "__main__":
    main()
