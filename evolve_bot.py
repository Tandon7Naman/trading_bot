import sqlite3

import pandas as pd
from stable_baselines3 import PPO

from GoldTradingEnv import GoldTradingEnv


def evolve_brain():
    print("🔄 INITIATING DAILY EVOLUTION PROTOCOL...")

    # 1. Connect to your local XAUUSD database
    db_path = "data/trading_history.db"
    conn = sqlite3.connect(db_path)

    # 2. Extract the full history (including today's new live data)
    df = pd.read_sql("SELECT * FROM XAUUSD_history ORDER BY time ASC", conn)
    conn.close()

    if len(df) < 100:
        print("⚠️ Not enough data in database to evolve. Collect more live ticks first.")
        return

    # 3. Initialize the Environment with the updated dataset
    env = GoldTradingEnv(db_path=db_path)

    # 4. Load the Champion Model (Seed 101) to continue learning
    print("🧠 Loading current brain...")
    model = PPO.load("models/gold_bot_seed_101.zip", env=env)

    # 5. Execute Fine-Tuning (The Evolution)
    # 5,000 steps is enough for a daily "refresh" without over-fitting
    print(f"🏋️  Retraining on {len(df)} bars of market history...")
    model.learn(total_timesteps=5000, reset_num_timesteps=False)

    # 6. Save the new "Evolved" model
    model.save("models/gold_bot_seed_101_evolved")
    print("✅ SUCCESS: The bot has evolved its strategy based on today's market.")


if __name__ == "__main__":
    evolve_brain()
