"""
Download Real Gold Price Data
Uses yfinance to download COMEX gold prices and convert to MCX format
"""

import os
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf


def download_gold_data():
    """Download real gold price data from Yahoo Finance and save to CSV"""
    print("\n" + "=" * 60)
    print("📊 DOWNLOADING REAL GOLD PRICE DATA")
    print("=" * 60)

    ticker = "GC=F"  # COMEX Gold Futures
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1095)  # last 3 years

    print("\n📈 Fetching data...")
    print(f"   Ticker: {ticker} (COMEX Gold Futures)")
    print(f"   Period: {start_date.date()} to {end_date.date()}")
    print("   Interval: Daily")

    try:
        data = yf.download(ticker, start=start_date, end=end_date, interval='1d', progress=False)

        if len(data) == 0:
            print("❌ Failed to download data")
            return None

        print(f"✅ Downloaded {len(data)} records")

        volume_values = (
            data['Volume'].values if 'Volume' in data.columns else np.zeros(len(data))
        )

        df = pd.DataFrame(
            {
                'timestamp': data.index,
                'open': data['Open'].values,
                'high': data['High'].values,
                'low': data['Low'].values,
                'close': data['Close'].values,
                'volume': volume_values,
            }
        )

        print("\n🔄 Converting to MCX format...")
        print("   COMEX: USD per troy ounce")
        print("   MCX: INR per 10 grams")

        conversion_factor = 10 / 31.1035  # troy ounce to 10 grams
        usd_to_inr = 83.5  # approximate FX rate

        for col in ['open', 'high', 'low', 'close']:
            df[col] = df[col] * conversion_factor * usd_to_inr

        df = df.dropna()

        os.makedirs('data', exist_ok=True)
        filepath = 'data/mcx_gold_historical.csv'
        df.to_csv(filepath, index=False)

        print("\n✅ Data saved successfully!")
        print(f"   File: {filepath}")
        print("\n📄 Sample (tail):")
        print(df.tail().to_string(index=False))

        return filepath

    except Exception as e:
        print(f"❌ Error downloading data: {e}")
        return None


if __name__ == "__main__":
    download_gold_data()
