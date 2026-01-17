import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import time
import os

# --- SETTINGS ---
CSV_FILE = 'data/MCX_gold_daily.csv'
GOLD_SYMBOL = 'GC=F'  # Global Gold Futures

def get_live_price(symbol, retries=3):
    """
    Tries to fetch the price. If it fails, waits 5 seconds and tries again.
    This makes the bot 'Robust' against internet blips.
    """
    for attempt in range(retries):
        try:
            ticker = yf.Ticker(symbol)
            # Fetch just the last 1 minute of data
            data = ticker.history(period="1d", interval="1m")
            
            if not data.empty:
                return data
            else:
                print(f"   ⚠️ Attempt {attempt+1}: Data empty, retrying...")
        except Exception as e:
            print(f"   ⚠️ Attempt {attempt+1}: Connection failed ({e}), retrying...")
        
        time.sleep(5)  # Wait 5 seconds before next try
    
    return None  # Failed after 3 tries

def update_csv():
    print(f"\n🔄 Connecting to Global Market ({GOLD_SYMBOL})...")
    
    if not os.path.exists(CSV_FILE):
        print("❌ Error: Cannot find your data file!")
        return

    df = pd.read_csv(CSV_FILE)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    last_row = df.iloc[-1]
    last_mcx_price = last_row['close']
    last_date = last_row['timestamp']
    
    # Check if we already have data for this exact minute? 
    # (Optional: For now we just append new lines to simulate flow)
    
    # --- FETCH WITH RETRY LOGIC ---
    data = get_live_price(GOLD_SYMBOL)
    
    if data is None:
        print("   ❌ Market data unavailable. Skipping this update.")
        return

    current_global_price = data['Close'].iloc[-1]
    
    # Calculate Est. MCX Price
    global_open = data['Open'].iloc[0]
    pct_change = (current_global_price - global_open) / global_open
    noise = np.random.normal(0, 5) 
    new_mcx_price = last_mcx_price * (1 + pct_change) + noise
    
    print(f"   🌎 Global Gold: ${current_global_price:.2f}")
    print(f"   🇮🇳 Est. MCX Price: ₹{new_mcx_price:.2f}")

    # Append new row
    today = pd.Timestamp.now()
    new_row = last_row.copy()
    new_row['timestamp'] = today
    new_row['close'] = new_mcx_price
    new_row['open'] = new_mcx_price
    new_row['high'] = new_mcx_price
    new_row['low'] = new_mcx_price
    
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
            print(f"   ❌ Critical Crash: {e}")
            time.sleep(60)
