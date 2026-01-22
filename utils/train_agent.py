import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


import os
import sys

from stable_baselines3 import PPO

from GoldTradingEnv import GoldTradingEnv


def run_seed_trial(seed_value):
    print(f"🧪 INITIALIZING TRIAL: Seed {seed_value}")
    # 1. Create Env with a fixed seed, using the database
    env = GoldTradingEnv(db_path="data/trading_history.db", symbol="XAUUSD")
    # 2. Best hyperparameters from Optuna (replace with your best settings)
    best_params = {"learning_rate": 0.0003, "batch_size": 64, "n_steps": 2048}
    # 3. Initialize PPO with the seed
    model = PPO("MlpPolicy", env, verbose=0, seed=seed_value, **best_params)
    # 4. Train
    model.learn(total_timesteps=20000)
    # 5. Save unique model
    os.makedirs("models", exist_ok=True)
    model_name = f"models/gold_bot_seed_{seed_value}"
    model.save(model_name)
    print(f"✅ Trial Complete: {model_name}.zip saved.")


if __name__ == "__main__":
    # Get seed from command line argument
    if len(sys.argv) > 1:
        run_seed_trial(int(sys.argv[1]))
    else:
        run_seed_trial(42)  # Default
