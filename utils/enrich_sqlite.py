import sqlite3

import numpy as np
import pandas as pd
from ta.trend import ADXIndicator


def enrich_sqlite_table(db_path="data/trading_history.db", symbol="XAUUSD"):
    table = f"{symbol}_history"
    conn = sqlite3.connect(db_path)
    df = pd.read_sql(f"SELECT * FROM {table}", conn)
    # Add ADX
    adx_i = ADXIndicator(high=df["high"], low=df["low"], close=df["close"], window=14)
    df["adx"] = adx_i.adx().fillna(0)
    # Add Simulated Sentiment
    df["sentiment"] = np.random.uniform(-0.5, 0.8, size=len(df))
    # Overwrite table with enriched data
    df.to_sql(table, conn, if_exists="replace", index=False)
    conn.close()
    print(f"✅ {table} enriched with ADX and sentiment.")


if __name__ == "__main__":
    enrich_sqlite_table()
