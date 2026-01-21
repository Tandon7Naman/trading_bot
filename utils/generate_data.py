import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def generate_gld_backtest_data(filename="data/gld_data.csv", days=365):
    print(f"🛠️  INJECTING TRADE SIGNAL INTO: {filename}...")
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    times = pd.date_range(start=start_time, end=end_time, freq='D')
    
    n = len(times)
    price = 180.0
    data = []
    
    for i in range(n):
        # Normal random walk for most of the year
        change = np.random.normal(0, 0.5)
        
        # 🟢 INJECT THE SIGNAL: In the last 10 days, create a Wyckoff Spring
        if i == n - 5: change = -15.0  # The "Selling Climax" (Massive Drop)
        if i == n - 3: change = -2.0   # The "Spring" (Fakeout Low)
        if i == n - 1: change = +20.0  # The "Recovery" (Trade Trigger)
        
        price += change
        vol = 10_000_000 if i >= n-5 else 1_000_000 # Spiking volume at the end
        
        data.append({
            "timestamp": times[i].strftime("%Y-%m-%d"),
            "open": round(price + 0.5, 2),
            "high": round(price + 1.0, 2),
            "low": round(price - 1.0, 2),
            "close": round(price, 2),
            "volume": int(vol)
        })
        
    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    df.to_csv(filename, index=False)
    print("✅ SUCCESS: Data contains a guaranteed Wyckoff Spring signal.")

if __name__ == "__main__":
    generate_gld_backtest_data()