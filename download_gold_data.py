"""
Download Real Gold Price Data
Uses yfinance to download COMEX gold prices and convert to MCX format
FIXED: Handles yfinance data structure properly
"""

import os
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf


def download_gold_data():
    """Download real gold price data from Yahoo Finance"""
    print("\n" + "=" * 60)
    print("📊 DOWNLOADING REAL GOLD PRICE DATA")
    print("=" * 60)

    ticker = "GC=F"
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1095)

    print(f"\n📈 Fetching data...")
    print(f"   Ticker: {ticker} (COMEX Gold Futures)")
    print(f"   Period: {start_date.date()} to {end_date.date()}")
    print("   Interval: Daily")

    try:
        print("   Downloading...")
        data = yf.download(
            ticker,
            start=start_date,
            end=end_date,
            interval='1d',
            progress=False,
            auto_adjust=True,
        )

        if len(data) == 0:
            print("❌ Failed to download data - no records returned")
            return None

        print(f"✅ Downloaded {len(data)} records")

        data = data.reset_index()

        df = pd.DataFrame()
        df['timestamp'] = pd.to_datetime(data['Date'] if 'Date' in data.columns else data.index)
        df['open'] = data['Open'].values
        df['high'] = data['High'].values
        df['low'] = data['Low'].values
        df['close'] = data['Close'].values
        df['volume'] = data['Volume'].values if 'Volume' in data.columns else 0

        df = df.dropna()

        if len(df) == 0:
            print("❌ No valid data after cleaning")
            return None

        print(f"✅ Cleaned data: {len(df)} valid records")

        print("\n🔄 Converting to MCX format...")
        print("   COMEX: USD per troy ounce")
        print("   MCX: INR per 10 grams")

        TROY_OZ_TO_GRAMS = 31.1035
        GRAMS_PER_MCX_LOT = 10
        USD_TO_INR = 83.5

        conversion_factor = (GRAMS_PER_MCX_LOT / TROY_OZ_TO_GRAMS) * USD_TO_INR

        print(f"   Conversion factor: {conversion_factor:.4f}")
        print(f"   USD/INR rate: {USD_TO_INR}")

        for col in ['open', 'high', 'low', 'close']:
            df[col] = df[col] * conversion_factor

        print(f"\n📊 Converted Data Summary:")
        print(f"   Records: {len(df)}")
        print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"   Price range: ₹{df['close'].min():.2f} - ₹{df['close'].max():.2f}")
        print(f"   Latest price: ₹{df['close'].iloc[-1]:.2f} ({df['timestamp'].iloc[-1].date()})")

        os.makedirs('data', exist_ok=True)
        filepath = 'data/mcx_gold_historical.csv'
        df.to_csv(filepath, index=False)

        print("\n✅ Data saved successfully!")
        print(f"   File: {filepath}")
        print(f"   Size: {os.path.getsize(filepath) / 1024:.1f} KB")

        print("\n" + "=" * 60)
        print("✅ DOWNLOAD COMPLETE")
        print("=" * 60)
        print("\nNext step: Run training")
        print("   python train_ppo.py")

        return df

    except Exception as e:
        print(f"\n❌ Error downloading data: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check internet connection")
        print("2. Verify yfinance is installed: pip install yfinance")
        print("3. Try different ticker if GC=F doesn't work")
        print("4. Check Yahoo Finance is accessible")

        import traceback

        print("\nFull error:")
        traceback.print_exc()

        return None


if __name__ == "__main__":
    df = download_gold_data()

    if df is not None:
        print("\n✅ Success! Ready for training.")
    else:
        print("\n❌ Failed. Please check errors above.")
