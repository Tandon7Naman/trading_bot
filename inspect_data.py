# inspect_data.py
import os

import pandas as pd

print("\n" + "=" * 70)
print("DATA STRUCTURE INSPECTION")
print("=" * 70)

# Check GLD data
if os.path.exists("data/gld_data.csv"):
    print("\n[*] GLD Data Structure:")
    df_gld = pd.read_csv("data/gld_data.csv")
    print(f"  Shape: {df_gld.shape}")
    print(f"  Columns: {list(df_gld.columns)}")
    print(f"  Column names (lowercase): {[col.lower() for col in df_gld.columns]}")
    print(f"  Data types:\n{df_gld.dtypes}")
    print("\n  First 3 rows:")
    print(df_gld.head(3))
    print("\n  Last 3 rows:")
    print(df_gld.tail(3))
else:
    print("[-] GLD data not found")

# Check MCX data
if os.path.exists("data/mcx_gold_data.csv"):
    print("\n[*] MCX Gold Data Structure:")
    df_mcx = pd.read_csv("data/mcx_gold_data.csv")
    print(f"  Shape: {df_mcx.shape}")
    print(f"  Columns: {list(df_mcx.columns)}")
    print("\n  First 3 rows:")
    print(df_mcx.head(3))
else:
    print("[-] MCX data not found")

# Check news data
if os.path.exists("data/market_news.csv"):
    print("\n[*] Market News Data Structure:")
    df_news = pd.read_csv("data/market_news.csv")
    print(f"  Shape: {df_news.shape}")
    print(f"  Columns: {list(df_news.columns)}")
    print("\n  First 3 rows:")
    print(df_news.head(3))
else:
    print("[-] Market news data not found")

print("\n" + "=" * 70 + "\n")
