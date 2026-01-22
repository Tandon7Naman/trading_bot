import os
import sqlite3

import MetaTrader5 as mt5
import pandas as pd


def fetch_and_save_history(symbol="XAUUSD", timeframe=mt5.TIMEFRAME_H1, bars=1000):
    # 1. Initialize MT5 Connection
    if not mt5.initialize():
        print(f"❌ Initialize failed, error code: {mt5.last_error()}")
        return

    print(f"📡 Fetching {bars} bars of {symbol} data...")

    # 2. Extract Data from MT5
    # copy_rates_from_pos gets historical bars starting from the current moment
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    mt5.shutdown()  # Close connection to save resources

    if rates is None or len(rates) == 0:
        print(f"❌ No data found for {symbol}. Check Market Watch.")
        return

    # 3. Transform Data using Pandas
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")  # Convert MT5 epoch to readable time

    # 4. Load into Local SQLite Database
    db_path = "data/trading_history.db"
    os.makedirs("data", exist_ok=True)

    conn = sqlite3.connect(db_path)
    # 'append' ensures we don't overwrite old data, keeping a permanent archive
    df.to_sql(f"{symbol}_history", conn, if_exists="append", index=False)

    # Remove duplicates if we accidentally fetched overlapping data
    conn.execute(f"""
        DELETE FROM {symbol}_history
        WHERE rowid NOT IN (SELECT MIN(rowid) FROM {symbol}_history GROUP BY time)
    """)
    conn.commit()
    conn.close()

    print(f"✅ Saved {len(df)} bars to {db_path}")


if __name__ == "__main__":
    fetch_and_save_history()
