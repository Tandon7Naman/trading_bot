import yfinance as yf
import pandas as pd
import numpy as np
import time
import os

# --- PATH CONFIGURATION ---
CSV_FILE = 'data/MCX_gold_daily.csv'
GOLD_SYMBOL = 'GC=F'

def update_csv():
    print(f"\n🔄 Connecting to Global Market ({GOLD_SYMBOL})...")
    
    # 1. Ensure 'data' folder exists
    if not os.path.exists('data'):
        os.makedirs('data')

    # 2. Create file if missing
    if not os.path.exists(CSV_FILE):
        print("   Creating new data file...")
        df = pd.DataFrame(columns=['timestamp','open','high','low','close','adj close','volume'])
        df.to_csv(CSV_FILE, index=False)
    
    try:
        # 3. Fetch Real Data Only
        ticker = yf.Ticker(GOLD_SYMBOL)
        data = ticker.history(period="1d", interval="1m")
        
        if data.empty:
            print("   ⚠️ Market is Closed (No Data Received). Waiting...")
            return

        # 4. Process Real Data
        last_price = data['Close'].iloc[-1]
        
        # Estimate MCX Price (USD -> INR conversion)
        mcx_price = (last_price * 83 * 0.1)
        
        print(f"   🌎 Global: ${last_price:.2f} -> 🇮🇳 MCX (Est): ₹{mcx_price:.2f}")
        
        # 5. Save to CSV
        df = pd.read_csv(CSV_FILE)
        
        new_row = {
            'timestamp': pd.Timestamp.now(),
            'open': mcx_price, 'high': mcx_price, 
            'low': mcx_price, 'close': mcx_price,
            'volume': 0
        }
        new_df = pd.DataFrame([new_row])
        df = pd.concat([df, new_df], ignore_index=True)
        
        df.to_csv(CSV_FILE, index=False)
        print("   ✅ Real Data Saved.")
        
    except Exception as e:
        print(f"   ❌ Data Feed Error: {e}")

if __name__ == "__main__":
    print("🚀 LIVE DATA FEED STARTED (Production Mode)")
    while True:
        update_csv()
        print("   zzz Sleeping 60 seconds...")
        time.sleep(60)