import numpy as np
import pandas as pd

from lstm_model_consolidated import GoldLSTMModel
from trading_environment import GoldTradingEnv

# Create sample data
dates = pd.date_range(start="2023-01-01", periods=500, freq="D")
df = pd.DataFrame(
    {
        "timestamp": dates,
        "open": np.random.uniform(6000, 7000, 500),
        "high": np.random.uniform(6100, 7100, 500),
        "low": np.random.uniform(5900, 6900, 500),
        "close": np.random.uniform(6000, 7000, 500),
    }
)

# Load or create LSTM
lstm = GoldLSTMModel(lookback=60, features=4)

# Create environment
env = GoldTradingEnv(df=df, lstm_model=lstm, initial_capital=100000)

# Test reset
obs, info = env.reset()
print("✅ Environment working!")
print(f"   Observation shape: {obs.shape}")
print(f"   Initial capital: ₹{info['capital']:,.0f}")

# Test step
action = 0  # HOLD
obs, reward, done, truncated, info = env.step(action)
print("✅ Step working!")
print(f"   Reward: {reward:.4f}")
print(f"   Done: {done}")
