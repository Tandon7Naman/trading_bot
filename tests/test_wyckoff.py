import sys
import os
import pandas as pd
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from strategies.wyckoff import WyckoffAnalyzer

def test_wyckoff_detection():
    print("🧪 STARTING PHASE 3 VERIFICATION: WYCKOFF PATTERNS")
    
    # 1. Create Synthetic Data (50 Bullish Candles - Boring)
    # Making them "Up" candles (Close > Open) ensures they fail the SC check immediately.
    data = {
        'Open': [100.0] * 50,
        'High': [102.0] * 50,
        'Low':  [100.0] * 50,
        'Close':[101.0] * 50, # Up Candle
        'Volume':[1000] * 50
    }
    df = pd.DataFrame(data)
    
    # 2. INJECT SELLING CLIMAX at Index 40
    # Down Candle, Huge Spread, Huge Volume, Close off Low
    df.at[40, 'Open'] = 100.0
    df.at[40, 'High'] = 100.0
    df.at[40, 'Low'] = 90.0   # Spread = 10
    df.at[40, 'Close'] = 92.0 # Down Candle (92 < 100)
    df.at[40, 'Volume'] = 10000 
    
    # 3. RUN SC DETECTION
    has_sc, sc_low, sc_vol, idx = WyckoffAnalyzer.find_selling_climax(df)
    
    if has_sc and sc_low == 90.0:
        print("   ✅ Selling Climax Detected correctly @ $90.0")
    else:
        print(f"   ❌ SC Detection Failed. Found: {has_sc}, Low: {sc_low}, Idx: {idx}")
        # Debug info
        return

    # 4. INJECT SPRING at Index 49 (Current Candle)
    # Dips to 89 (Below SC 90) but closes at 93 (Recovery)
    current_row = pd.Series({
        'Open': 93.0, 'High': 94.0, 'Low': 89.0, 'Close': 93.0, 'Volume': 5000
    })
    
    is_spring, msg = WyckoffAnalyzer.detect_spring(current_row, sc_low, sc_vol)
    
    if is_spring:
        print(f"   ✅ Spring Detected correctly: {msg}")
    else:
        print(f"   ❌ Spring Detection Failed: {msg}")

    print("✅ PHASE 3 VERIFICATION COMPLETE.")

if __name__ == "__main__":
    test_wyckoff_detection()