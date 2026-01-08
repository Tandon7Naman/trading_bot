#!/usr/bin/env python3
"""
Fix GLD_daily.csv by removing multi-level columns and keeping only clean data
"""

import pandas as pd

# Read with multi-level header handling
df = pd.read_csv('data/GLD_daily.csv', index_col=0)

print("Original shape:", df.shape)
print("Original columns:", df.columns.tolist())

# Remove tuple columns (the yfinance multi-level ones)
# Keep only: symbol, open, high, low, close, volume
cols_to_keep = ['symbol', 'open', 'high', 'low', 'close', 'volume']
df_clean = df[[c for c in cols_to_keep if c in df.columns]].copy()

# Rename index to timestamp
df_clean['timestamp'] = df_clean.index
df_clean = df_clean[['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume']]

# Convert to proper types
df_clean['timestamp'] = pd.to_datetime(df_clean['timestamp'])
df_clean['open'] = pd.to_numeric(df_clean['open'], errors='coerce')
df_clean['high'] = pd.to_numeric(df_clean['high'], errors='coerce')
df_clean['low'] = pd.to_numeric(df_clean['low'], errors='coerce')
df_clean['close'] = pd.to_numeric(df_clean['close'], errors='coerce')
df_clean['volume'] = pd.to_numeric(df_clean['volume'], errors='coerce')

# Drop rows with NaN in OHLC
df_clean = df_clean.dropna(subset=['open', 'high', 'low', 'close'])

# Sort by timestamp
df_clean = df_clean.sort_values('timestamp').reset_index(drop=True)

print("\nCleaned shape:", df_clean.shape)
print("Cleaned columns:", df_clean.columns.tolist())
print("\nFirst row:")
print(df_clean.iloc[0])
print("\nLast row:")
print(df_clean.iloc[-1])

# Save
df_clean.to_csv('data/GLD_daily.csv', index=False)
print("\n✓ GLD_daily.csv cleaned and saved")
