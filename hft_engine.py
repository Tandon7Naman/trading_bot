import time

import MetaTrader5 as mt5
import numpy as np
import pandas as pd
from stable_baselines3 import PPO
from ta.trend import ADXIndicator

# ⚙️ CONFIGURATION
SYMBOL = "XAUUSD"
TIMEFRAME = mt5.TIMEFRAME_M1
MODEL_PATH = "models/gold_bot_seed_101.zip"


def start_shadow_trading():
    print(f"🧠 Loading AI Model: {MODEL_PATH}")
    model = PPO.load(MODEL_PATH)

    if not mt5.initialize():
        print("❌ Failed to initialize MT5")
        return

    print(f"🚀 ENGINE ONLINE: Shadow Trading {SYMBOL}...")

    try:
        while True:
            # 1. Pull 100 bars to ensure indicators have enough history
            rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 100)
            if rates is None:
                print("⚠️ Waiting for data...")
                time.sleep(5)
                continue

            df = pd.DataFrame(rates)

            # 2. Calculate Indicators (History Padding Fix)
            adx_i = ADXIndicator(df["high"], df["low"], df["close"], window=14)
            df["adx"] = adx_i.adx().fillna(0)
            df["sentiment"] = 0.5  # Placeholder for live FinBERT feed

            # 3. Prepare AI Observation (The 5x7 Window)
            # We slice the last 5 rows AFTER indicators are calculated
            obs_raw = (
                df[["open", "high", "low", "close", "tick_volume", "sentiment", "adx"]]
                .tail(5)
                .values
            )
            observation = np.expand_dims(obs_raw, axis=0).astype(np.float32)

            # 4. AI Inference
            action, _states = model.predict(observation, deterministic=True)

            # 5. Output Prediction
            action_map = {0: "HOLD ⏸️", 1: "BUY 📈", 2: "SELL 📉"}
            print(
                f"[{pd.Timestamp.now()}] {SYMBOL} @ {df['close'].iloc[-1]} | AI Decision: {action_map[action.item()]}"
            )

            time.sleep(10)  # 10-second tick cycle

    except KeyboardInterrupt:
        print("🛑 Engine stopping...")
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    start_shadow_trading()
