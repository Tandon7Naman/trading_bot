import numpy as np
import pandas as pd
from ta.trend import ADXIndicator


def enrich_xauusd():
    # Load the actual XAUUSD file
    df = pd.read_csv("data/xauusd_history.csv")

    # Add Technical Indicators
    adx_i = ADXIndicator(high=df["high"], low=df["low"], close=df["close"], window=14)
    df["adx"] = adx_i.adx().fillna(0)

    # Add Simulated Sentiment (Matches the RL observation space)
    df["sentiment"] = np.random.uniform(-1, 1, size=len(df))

    df.to_csv("data/xauusd_enriched.csv", index=False)
    print("✅ XAUUSD data enriched and ready for training.")


enrich_xauusd()
