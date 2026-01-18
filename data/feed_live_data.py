import sys
import os
# Fix Path to allow importing from root
sys.path.append(os.getcwd())

import yfinance as yf
import pandas as pd
import time
from config.settings import ENABLED_MARKETS, ASSET_CONFIG
from utils.time_utils import is_market_open

def update_asset(market_name):
    config = ASSET_CONFIG[market_name]
    symbol = config['symbol']
    file_path = config['data_file']
    
    # 1. CHECK SESSION
    is_open, reason = is_market_open(symbol)
    if not is_open:
        print(f"   💤 {market_name}: Market Closed ({reason})")
        return

    print(f"   📡 Polling {market_name} ({symbol})...")
    
    # --- OUTER TRY BLOCK START ---
    try:
        ticker = yf.Ticker(symbol)
        
        # PROTOCOL 7.1: DEFENSIVE API CALL
        # Inner try/except specifically for connection errors
        try:
            data = ticker.history(period="1d", interval="1m")
        except Exception as api_error:
            print(f"      ⚠️ API Error for {symbol}: {api_error}")
            return # Skip this cycle

        # PROTOCOL 7.1: NONE/EMPTY CHECK
        if data is None or data.empty:
            print(f"      ⚠️ No data received for {market_name} (NoneType/Empty)")
            return

        # Sanity Check: Ensure 'Close' column exists and has values
        if 'Close' not in data.columns or pd.isna(data['Close'].iloc[-1]):
             print(f"      ⚠️ Corrupted data for {market_name} (NaN Price)")
             return

        if not os.path.exists(file_path):
            data.to_csv(file_path)
        else:
            data.to_csv(file_path)
            
        latest_price = data['Close'].iloc[-1]
        print(f"      ✅ {market_name} Updated: {latest_price:.2f}")
        
    # --- OUTER EXCEPT BLOCK (This was likely missing) ---
    except Exception as e:
        print(f"      ❌ General Error {market_name}: {e}")

if __name__ == "__main__":
    print(f"🚀 DATA FEED STARTED (Protocol 7.1 Robustness)")
    print(f"📋 Active Subscriptions: {ENABLED_MARKETS}")
    
    while True:
        print(f"\n🔄 Syncing Enabled Markets...")
        for market in ENABLED_MARKETS:
            update_asset(market)
            
        print("   zzz Sleeping 60s...")
        time.sleep(60)