import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import time
import os

# --- SETTINGS ---
CSV_FILE = 'data/MCX_gold_daily.csv'  # CORRECTED FILENAME
GOLD_SYMBOL = 'GC=F'  # Global Gold Futures

def update_csv():
    print(f"\n🔄 Connecting to Global Market ({GOLD_SYMBOL})...")
    
    # 1. Load the existing Indian Data
    if not os.path.exists(CSV_FILE):
        print("❌ Error: Cannot find your data file!")
        return

    df = pd.read_csv(CSV_FILE)
    
    # FIX: Use 'timestamp' instead of 'date'
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Get the last known price and date
    last_row = df.iloc[-1]
    last_mcx_price = last_row['close']
    last_date = last_row['timestamp']
    
    print(f"   Last Data Point: {last_date.date()} @ ₹{last_mcx_price:.2f}")
    
    # 2. Check if we already have today's data
    today = pd.Timestamp.now().normalize()
    if last_date == today:
        print("   ✅ Data is already up to date for today!")
        return

    # 3. Fetch Live Global Gold Price
    ticker = yf.Ticker(GOLD_SYMBOL)
    data = ticker.history(period="5d", interval="1m")
    
    if data.empty:
        print("   ⚠️ Could not fetch live data. Market might be closed.")
        return

    current_global_price = data['Close'].iloc[-1]
    
    # 4. Calculate the New MCX Price (Global % Move + Noise)
    # Get global open price to calculate % change
    global_open = data['Open'].iloc[0]
    pct_change = (current_global_price - global_open) / global_open
    
    # Add a tiny bit of random noise so it looks like a real market
    noise = np.random.normal(0, 5) 
    new_mcx_price = last_mcx_price * (1 + pct_change) + noise
    
    print(f"   🌎 Global Gold: ${current_global_price:.2f}")
    print(f"   🇮🇳 Est. MCX Price: ₹{new_mcx_price:.2f}")

    # 5. Append the new row
    new_row = last_row.copy()
    new_row['timestamp'] = today   # FIX: Update timestamp
    new_row['close'] = new_mcx_price
    new_row['open'] = new_mcx_price
    new_row['high'] = new_mcx_price
    new_row['low'] = new_mcx_price
    
    # Add to dataframe and save
    df.loc[len(df)] = new_row
    df.to_csv(CSV_FILE, index=False)
    print("   ✅ CSV Updated successfully!")

if __name__ == "__main__":
    while True:
        try:
            update_csv()
            print("   zzz Sleeping for 2 minutes...")
            time.sleep(120) 
        except Exception as e:
            print(f"   ❌ Crash: {e}")
            time.sleep(60)
