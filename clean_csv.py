import pandas as pd

# Load the messy CSV
df = pd.read_csv("data/GLD_daily.csv")

# Keep only the clean columns
clean_cols = ["symbol", "open", "high", "low", "close", "volume", "trade_count", "vwap"]
df = df[[col for col in clean_cols if col in df.columns]].copy()


# Load again to get the index (which has the dates with timezone)
df_with_index = pd.read_csv("data/GLD_daily.csv", index_col=0)

# Convert index to datetime, handling both UTC and naive timestamps
try:
    df["timestamp"] = pd.to_datetime(df_with_index.index, utc=True)
except Exception as e:
    print(f"First attempt failed: {e}")
    # Fallback: parse with mixed formats
    df["timestamp"] = pd.to_datetime(df_with_index.index, utc=False, errors="coerce")

# Remove timezone info if present (convert to naive UTC)
if df["timestamp"].dt.tz is not None:
    df["timestamp"] = df["timestamp"].dt.tz_localize(None)

# Reorder columns
df = df[["timestamp", "symbol", "open", "high", "low", "close", "volume", "trade_count", "vwap"]]

# Drop any rows with NaN in critical columns
df = df.dropna(subset=["open", "high", "low", "close", "timestamp"])

# Sort by timestamp
df = df.sort_values("timestamp").reset_index(drop=True)

# Save cleaned
df.to_csv("data/GLD_daily.csv", index=False)

print("✓ CSV cleaned and saved.")
print(f"  Total rows: {len(df)}")
print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
print("\nColumns:", df.columns.tolist())
print("\nFirst row:")
print(df.iloc[0])
print("\nLast row:")
print(df.iloc[-1])
