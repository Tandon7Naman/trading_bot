import os
import sys

import optuna
import pandas as pd
from stable_baselines3 import PPO

from GoldTradingEnv import GoldTradingEnv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load your data once to share across trials
df = pd.read_csv("data/gld_data.csv")


def objective(trial):
    # 🧪 The AI 'Guesses' these settings
    lr = trial.suggest_float("lr", 1e-5, 1e-3, log=True)
    batch_size = trial.suggest_categorical("batch_size", [32, 64, 128, 256])
    n_steps = trial.suggest_categorical("n_steps", [512, 1024, 2048])

    # Create a fresh environment for each trial
    env = GoldTradingEnv(df)

    # Train a temporary model
    model = PPO(
        "MlpPolicy", env, learning_rate=lr, batch_size=batch_size, n_steps=n_steps, verbose=0
    )
    model.learn(total_timesteps=5000)  # Quick test

    # Evaluate performance (Profit is our goal)
    obs, _ = env.reset()
    total_reward = 0
    for _ in range(100):
        action, _ = model.predict(obs)
        obs, reward, done, _, _ = env.step(action)
        total_reward += reward
        if done:
            break

    return total_reward


study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=20)

print(f"🎯 BEST SETTINGS FOUND: {study.best_params}")
