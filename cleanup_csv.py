#!/usr/bin/env python3
"""
Clean GLD_daily.csv - removes all messy columns and keeps only essentials
Run this once to fix the CSV permanently
"""

import pandas as pd
import os

DATA_PATH = "data/GLD_daily.csv"

# Read the messy CSV
df = pd.read_csv(DATA_PATH)

print("Original columns:", df.columns.tolist())
print("Original shape:", df.shape)

# Extract the date from 'Unnamed: 0' column
if 'Unnamed: 0' in df.columns:
    df['timestamp'] = pd.to_datetime(df['Unnamed: 0'])
else:
    print("ERROR: 'Unnamed: 0' column not found")
    exit(1)

# Drop all messy columns, keep only the clean ones
df_clean = df[['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume']].copy()

# Ensure numeric types
df_clean['open'] = pd.to_numeric(df_clean['open'], errors='coerce')
df_clean['high'] = pd.to_numeric(df_clean['high'], errors='coerce')
df_clean['low'] = pd.to_numeric(df_clean['low'], errors='coerce')
df_clean['close'] = pd.to_numeric(df_clean['close'], errors='coerce')
df_clean['volume'] = pd.to_numeric(df_clean['volume'], errors='coerce')

# Drop NaN rows
df_clean = df_clean.dropna(subset=['open', 'high', 'low', 'close'])

# Sort by timestamp
df_clean = df_clean.sort_values('timestamp').reset_index(drop=True)

# Overwrite the original file
df_clean.to_csv(DATA_PATH, index=False)

print("\n✓ CSV cleaned successfully!")
print(f"New columns: {df_clean.columns.tolist()}")
print(f"New shape: {df_clean.shape}")
print(f"Date range: {df_clean['timestamp'].min()} → {df_clean['timestamp'].max()}")
print(f"\nFirst row:\n{df_clean.iloc[0]}")
print(f"\nLast row:\n{df_clean.iloc[-1]}")
