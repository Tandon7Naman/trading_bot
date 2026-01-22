import sqlite3

import gymnasium as gym
import numpy as np
import pandas as pd
from gymnasium import spaces


class GoldTradingEnv(gym.Env):
    """Protocol 7.2: Database-Driven Autonomous XAUUSD Environment"""

    def __init__(self, db_path="data/trading_history.db", symbol="XAUUSD", initial_balance=500000):
        super().__init__()
        self.db_path = db_path
        self.symbol = f"{symbol}_history"
        self.initial_balance = initial_balance
        # Load data once from SQL to memory for training speed
        conn = sqlite3.connect(self.db_path)
        self.df = pd.read_sql(f"SELECT * FROM {self.symbol} ORDER BY time ASC", conn)
        conn.close()
        # Define Action & Observation Spaces (Matching Seed 101 Config)
        self.action_space = spaces.Discrete(3)  # Hold, Buy, Sell
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(5, 7),
            dtype=np.float32,  # 5 candles, 7 features
        )

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.balance = self.initial_balance
        self.net_worth = self.initial_balance
        self.current_step = 5
        return self._get_observation(), {}

    def _get_observation(self):
        # Extract features required for the 5x7 observation space
        # Features: open, high, low, close, tick_volume, sentiment, adx
        obs = self.df.iloc[self.current_step - 5 : self.current_step][
            ["open", "high", "low", "close", "tick_volume", "sentiment", "adx"]
        ].values
        return obs.astype(np.float32)

    def step(self, action):
        self.df.iloc[self.current_step]["close"]
        # Logic for execution and reward calculation (simplified)
        self.current_step += 1
        done = self.current_step >= len(self.df) - 1
        reward = 0  # Reward logic based on PnL
        return self._get_observation(), reward, done, False, {}
