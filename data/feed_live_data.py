import os
import sys
import time

import pandas as pd
import yfinance as yf

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import ASSET_CONFIG, ENABLED_MARKETS


def update_asset(asset_name):
    """
    Protocol 9.0 Compliant Data Fetcher.
    Includes Type-Safety fix for yfinance Series objects.
    """
    config = ASSET_CONFIG.get(asset_name)
    if not config:
        print(f"⚠️ Config missing for {asset_name}")
        return

    # 1. GET CONFIG VALUES
    ticker_symbol = config["data_symbol"]
    csv_path = config["data_file"]

    print(f"   ⬇️  Fetching {asset_name} ({ticker_symbol})...")

    try:
        # 2. DOWNLOAD DATA
        df = yf.download(ticker_symbol, period="5d", interval="1m", progress=False)

        if df.empty:
            print(f"   ⚠️  Warning: No data returned for {ticker_symbol}")
            return

        # 3. FORMAT DATA
        df.reset_index(inplace=True)

        # Standardize Columns
        required_cols = ["Datetime", "Open", "High", "Low", "Close", "Volume"]
        if "Date" in df.columns:
            df.rename(columns={"Date": "Datetime"}, inplace=True)

        # Ensure we only keep relevant columns
        # (Handling multi-level columns if yfinance returns them)
        try:
            df.columns = df.columns.droplevel(1)  # Flatten if MultiIndex
        except Exception as e:
            print(f"Operation failed: {e}")

        # Filter columns if they exist, otherwise keep what we have
        available_cols = [c for c in required_cols if c in df.columns]
        df = df[available_cols]

        # 4. SAVE TO CSV
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        df.to_csv(csv_path, index=False)

        # 5. VALIDATION (The Fix: Force to float)
        if not df.empty:
            latest_time = df.iloc[-1]["Datetime"]
            # Cast strictly to float to avoid "Series.__format__" error
            raw_price = df.iloc[-1]["Close"]
            latest_price = float(raw_price) if pd.notna(raw_price) else 0.0

            print(f"   ✅ Saved {len(df)} rows. Last: {latest_time} @ ${latest_price:.2f}")

    except Exception as e:
        print(f"   ❌ Error updating {asset_name}: {e}")


if __name__ == "__main__":
    print("\n🚀 DATA FEED STARTED (Protocol 9.0 Compliant)")
    print(f"📋 Active Subscriptions: {ENABLED_MARKETS}\n")

    while True:
        print("🔄 Syncing Enabled Markets...")

        for market in ENABLED_MARKETS:
            update_asset(market)

        print("💤 Waiting 60s...")
        time.sleep(60)
