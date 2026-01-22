# update_mcx_gold_data.py - FIXED VERSION
import logging
import os
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

logging.basicConfig(
    filename="logs/update_mcx_gold_data.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def fetch_mcx_gold_data(symbol="GC=F", days=365):
    """
    Fetch MCX Gold data using yfinance
    Note: Using GC=F (COMEX Gold Futures) as proxy for MCX Gold
    Alternative symbols: GOLD (MCX via yfinance if available)
    """
    try:
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")

        print(f"[*] Fetching {symbol} data from {start_date} to {end_date}...")

        # GC=F is COMEX Gold (most reliable alternative to MCX)
        df = yf.download(symbol, start=start_date, end=end_date, progress=False)

        # Handle case where yfinance returns a Series
        if isinstance(df, pd.Series):
            df = df.to_frame()

        # Flatten multi-level columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)

        # Reset index
        df = df.reset_index()

        # Rename columns to lowercase
        df.columns = df.columns.str.lower()

        print(f"[+] Downloaded {len(df)} records")
        print(f"[*] Columns: {list(df.columns)}")

        logging.info(f"Fetched {len(df)} records for {symbol}")
        return df

    except Exception as e:
        logging.error(f"Error fetching MCX Gold data: {str(e)}")
        print(f"[-] Error fetching data: {str(e)}")
        return None


def clean_mcx_data(df):
    """Clean and prepare MCX data"""
    try:
        print("[*] Cleaning MCX data...")

        # Check for close column
        if "close" not in df.columns:
            logging.error(f"Close column not found. Available columns: {list(df.columns)}")
            print(f"[-] Close column not found. Available columns: {list(df.columns)}")
            return None

        # Remove duplicates
        df = df.drop_duplicates(subset=["date"] if "date" in df.columns else [df.columns[0]])
        print(f"[+] Removed duplicates: {len(df)} records remain")

        # Remove rows with NaN in critical columns
        df = df.dropna(subset=["close", "volume"])
        print(f"[+] Removed NaN rows: {len(df)} records remain")

        # Ensure data types
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
        df["high"] = pd.to_numeric(df["high"], errors="coerce")
        df["low"] = pd.to_numeric(df["low"], errors="coerce")
        df["open"] = pd.to_numeric(df["open"], errors="coerce")

        # Drop any rows where conversion failed
        df = df.dropna(subset=["close", "volume"])

        # Add technical indicators
        print("[*] Calculating technical indicators...")

        df["SMA_20"] = df["close"].rolling(window=20).mean()
        df["SMA_50"] = df["close"].rolling(window=50).mean()
        df["Daily_Return"] = df["close"].pct_change()

        # Remove NaN from indicator calculations
        df = df.dropna()
        print(f"[+] Removed NaN from indicators: {len(df)} records remain")

        logging.info(f"Cleaned MCX data: {len(df)} rows")
        print(f"[+] Data cleaning complete: {len(df)} rows")
        return df

    except Exception as e:
        logging.error(f"Error cleaning MCX data: {str(e)}")
        print(f"[-] Error cleaning data: {str(e)}")
        return None


def save_mcx_data(df, filepath="data/mcx_gold_data.csv"):
    """Save cleaned data to CSV"""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        df.to_csv(filepath, index=False)
        logging.info(f"Saved MCX data to {filepath}")
        print(f"[+] Data saved to {filepath}")
        return True
    except Exception as e:
        logging.error(f"Error saving MCX data: {str(e)}")
        print(f"[-] Error saving data: {str(e)}")
        return False


def main():
    print("\n" + "=" * 60)
    print("[*] Starting MCX Gold data update...")
    print("=" * 60)

    # Fetch data (using COMEX as proxy)
    df = fetch_mcx_gold_data("GC=F", days=365)
    if df is None:
        print("[-] Failed to fetch data")
        return False

    print("\n[*] Data structure:")
    print(df.head(2))

    # Clean data
    df = clean_mcx_data(df)
    if df is None:
        print("[-] Failed to clean data")
        return False

    # Save data
    if save_mcx_data(df):
        print(f"\n[+] Successfully updated MCX Gold data ({len(df)} records)")
        print(f"[+] Date range: {df['date'].min()} to {df['date'].max()}")
        print("=" * 60 + "\n")
        return True
    else:
        print("[-] Failed to save data")
        return False


if __name__ == "__main__":
    main()
