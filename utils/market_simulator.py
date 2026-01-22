import os
import time
from datetime import datetime

import numpy as np
import pandas as pd

FILE_PATH = "data/XAUUSD_M1.csv"


def simulate_market():
    print("🎢 MARKET SIMULATOR ACTIVE: Pumping live data into CSV...")

    # Load existing data to get the last price
    if os.path.exists(FILE_PATH):
        df = pd.read_csv(FILE_PATH)
        last_price = df.iloc[-1]["Close"]
        last_time = pd.to_datetime(df.iloc[-1]["Time"])
    else:
        last_price = 2000.0
        last_time = datetime.now()

    # Simulation Loop
    while True:
        try:
            # 1. Generate Random Walk (Drift)
            move = np.random.normal(0, 1.5)  # Random move $1.50 up or down

            # Inject a "Crash" every now and then to test Wyckoff
            if np.random.random() < 0.05:
                move -= 5.0

            new_price = last_price + move

            # 2. Update Time
            last_time = datetime.now()  # Real-time

            # 3. Create Candle
            new_row = {
                "Time": last_time.strftime("%Y-%m-%d %H:%M:%S"),
                "Open": round(last_price, 2),
                "High": round(max(last_price, new_price) + 0.5, 2),
                "Low": round(min(last_price, new_price) - 0.5, 2),
                "Close": round(new_price, 2),
                "Volume": int(np.random.randint(100, 5000)),
            }

            # 4. Append to CSV (Atomic Write)
            df = pd.DataFrame([new_row])
            df.to_csv(FILE_PATH, mode="a", header=False, index=False)

            print(f"   📈 TICK: ${new_price:.2f} (Vol: {new_row['Volume']})")

            last_price = new_price
            time.sleep(3)  # Wait 3 seconds before next tick

        except KeyboardInterrupt:
            print("\n🛑 Simulator Stopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)


if __name__ == "__main__":
    simulate_market()
