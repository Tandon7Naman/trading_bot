import os
import warnings

import gym
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from gym import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

from lstm_model_consolidated import GoldLSTMModel
from ppo_agent import GoldPPOAgent

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

# --- SETTINGS ---
DATA_FILE = "data/MCX_gold_daily.csv"
MODEL_DIR = "models"
LOG_DIR = "logs"
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


# --- INDICATOR CALCULATIONS ---
def add_indicators(df):
    """
    Adds Technical Indicators (RSI, MACD, SMA) to the data.
    This gives the AI 'X-Ray Vision' into market trends.
    """
    df = df.copy()

    # 1. RSI (Relative Strength Index) - 14 periods
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))

    # 2. MACD (Moving Average Convergence Divergence)
    exp1 = df["close"].ewm(span=12, adjust=False).mean()
    exp2 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = exp1 - exp2
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()

    # 3. SMA (Simple Moving Average) - 50 periods (Trend)
    df["sma_50"] = df["close"].rolling(window=50).mean()

    # Drop NaN values created by the calculations
    df.dropna(inplace=True)
    return df


# --- CUSTOM TRADING ENVIRONMENT ---
class GoldTradingEnv(gym.Env):
    def __init__(self, df):
        super().__init__()
        self.df = df
        self.current_step = 0
        self.max_steps = len(df) - 1

        # Action: 0=Hold, 1=Buy, 2=Sell
        self.action_space = spaces.Discrete(3)

        # Observation: [Close, RSI, MACD, MACD_Signal, SMA_50]
        # We normalize values loosely to help the AI learn
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(5,), dtype=np.float32)

        self.balance = 500000.0
        self.position = 0.0  # 0=Flat, 1=Long
        self.entry_price = 0.0

    def reset(self):
        self.balance = 500000.0
        self.position = 0.0
        self.entry_price = 0.0
        self.current_step = 0
        return self._next_observation()

    def _next_observation(self):
        # Return the feature vector for the current step
        row = self.df.iloc[self.current_step]
        return np.array(
            [row["close"], row["rsi"], row["macd"], row["macd_signal"], row["sma_50"]],
            dtype=np.float32,
        )

    def step(self, action):
        current_price = self.df.iloc[self.current_step]["close"]
        reward = 0
        done = False

        # Execute Trade Logic
        if action == 1:  # BUY
            if self.position == 0:
                self.position = 1
                self.entry_price = current_price
                # Small penalty for transaction cost
                reward = -50

        elif action == 2 and self.position == 1:  # SELL
            self.position = 0
            pnl = current_price - self.entry_price
            self.balance += pnl
            # Reward is the Profit (or Loss)
            reward = pnl

        # Step forward
        self.current_step += 1
        if self.current_step >= self.max_steps:
            done = True

        obs = self._next_observation()
        return obs, reward, done, {}


# --- MAIN TRAINING LOOP ---
if __name__ == "__main__":
    print("🧠 STARTING BRAIN UPGRADE (Training V2)...")

    # 1. Load and Prepare Data
    raw_df = pd.read_csv(DATA_FILE)
    df = add_indicators(raw_df)
    print(f"   Data Loaded: {len(df)} rows with Indicators (RSI, MACD).")

    # 2. Initialize Environment
    env = GoldTradingEnv(df)

    # 3. Train the Model
    model = PPO("MlpPolicy", env, verbose=1, tensorboard_log=LOG_DIR)

    print("   Training in progress... (This might take 30 seconds)")
    model.learn(total_timesteps=30000)

    # 4. Save the New Brain
    model.save(f"{MODEL_DIR}/ppo_gold_agent")
    print("✅ NEW BRAIN SAVED! The AI now understands RSI & MACD.")
"""
Training Pipeline for PPO Agent
FIXED: Monitor wrapper, episode tracking, and real data handling
"""


def train_ppo_agent():
    """Complete training pipeline for PPO agent"""
    print("\n" + "=" * 60)
    print("🎯 PPO AGENT TRAINING PIPELINE")
    print("=" * 60)

    # Step 1: Load data
    print("\n📊 Step 1: Loading MCX Gold data...")
    try:
        df = pd.read_csv("data/mcx_gold_historical.csv", parse_dates=["timestamp"])
        print(f"✅ Loaded {len(df)} records")
        print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"   Price range: ₹{df['close'].min():.2f} - ₹{df['close'].max():.2f}")
    except FileNotFoundError:
        print("❌ Data file not found.")
        print("⚠️ Run: python download_gold_data.py first to get real data")
        print("   Or training will use sample data (unrealistic results)")

        dates = pd.date_range(start="2023-01-01", periods=1000, freq="D")
        df = pd.DataFrame(
            {
                "timestamp": dates,
                "open": np.random.uniform(6000, 7000, 1000),
                "high": np.random.uniform(6100, 7100, 1000),
                "low": np.random.uniform(5900, 6900, 1000),
                "close": np.random.uniform(6000, 7000, 1000),
            }
        )
        print("✅ Created sample data (for testing only)")

    # Step 2: Load or train LSTM model
    print("\n🧠 Step 2: Loading LSTM model...")
    lstm_model = GoldLSTMModel(lookback=60, features=4)

    try:
        lstm_model.load("models/lstm_consolidated.h5")
        print("✅ LSTM model loaded")
    except Exception:
        print("⚠️ LSTM model not found. Training...")
        X_train, y_train, X_test, y_test = lstm_model.prepare_data(df)
        lstm_model.build_model()
        lstm_model.train(X_train, y_train, epochs=20, batch_size=32)
        lstm_model.save("models/lstm_consolidated.h5")
        print("✅ LSTM model trained and saved")

    if lstm_model.model is None:
        print("⚠️ Building LSTM model...")
        lstm_model.build_model()

    # Step 3: Create trading environment
    print("\n🎮 Step 3: Creating trading environment...")

    split_idx = int(0.8 * len(df))
    train_df = df.iloc[:split_idx].reset_index(drop=True)
    test_df = df.iloc[split_idx:].reset_index(drop=True)

    print(f"   Training episodes: {len(train_df)}")
    print(f"   Testing episodes: {len(test_df)}")

    os.makedirs("logs", exist_ok=True)

    env = GoldTradingEnv(
        df=train_df,
        lstm_model=lstm_model,
        initial_capital=100000,
        transaction_cost=0.0005,
        slippage=10,
    )

    monitored_env = Monitor(env, filename="./logs/training_monitor.csv")
    vec_env = DummyVecEnv([lambda: monitored_env])

    # Step 4: Create and train PPO agent
    print("\n🤖 Step 4: Creating PPO agent...")
    agent = GoldPPOAgent(
        env=vec_env,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
    )

    agent.create_model()

    # Step 5: Train
    print("\n🚀 Step 5: Training PPO agent...")
    print("   This may take 10-30 minutes...")

    episode_rewards = agent.train(
        total_timesteps=20000,  # ✅ Should be 20000
    )

    # Step 6: Evaluate on test data
    print("\n📊 Step 6: Evaluating on test data...")
    test_env = GoldTradingEnv(
        df=test_df,
        lstm_model=lstm_model,
        initial_capital=100000,
    )
    test_monitored_env = Monitor(test_env, filename="./logs/test_monitor.csv")
    test_vec_env = DummyVecEnv([lambda: test_monitored_env])
    agent.env = test_vec_env

    mean_reward, std_reward = agent.evaluate(n_eval_episodes=5)

    # Step 7: Get metrics from test environment
    print("\n📈 Step 7: Calculating performance metrics...")
    obs, _ = test_env.reset()
    done = False

    while not done:
        action = agent.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = test_env.step(action)
        done = terminated or truncated

    metrics = test_env.get_metrics()

    if metrics:
        print("\n" + "=" * 60)
        print("📊 TEST SET PERFORMANCE")
        print("=" * 60)
        print(f"   Total Return: {metrics['total_return']:.2f}%")
        print(f"   Number of Trades: {metrics['num_trades']}")
        print(f"   Win Rate: {metrics['win_rate']:.2f}%")
        print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"   Max Drawdown: {metrics['max_drawdown']:.2f}%")
        print(f"   Final Capital: ₹{metrics['final_capital']:,.0f}")
        print("=" * 60)

        print("\n✅ Blueprint Validation:")
        sharpe_pass = metrics["sharpe_ratio"] > 1.2
        dd_pass = metrics["max_drawdown"] > -10
        wr_pass = metrics["win_rate"] > 45

        print(
            f"   Sharpe > 1.2: {'✅ PASS' if sharpe_pass else '❌ FAIL'} ({metrics['sharpe_ratio']:.2f})"
        )
        print(
            f"   Max DD < -10%: {'✅ PASS' if dd_pass else '❌ FAIL'} ({metrics['max_drawdown']:.2f}%)"
        )
        print(
            f"   Win Rate > 45%: {'✅ PASS' if wr_pass else '❌ FAIL'} ({metrics['win_rate']:.2f}%)"
        )

        if sharpe_pass and dd_pass and wr_pass:
            print("\n🎉 ALL VALIDATION GATES PASSED!")
        else:
            print("\n⚠️ Some validation gates failed. Consider:")
            if not sharpe_pass:
                print("   - Increase training timesteps")
                print("   - Adjust learning rate")
            if not dd_pass:
                print("   - Reduce position sizes")
                print("   - Implement stricter risk management")
            if not wr_pass:
                print("   - Review strategy signals")
                print("   - Add more features")

    # Step 8: Save agent
    print("\n💾 Step 8: Saving PPO agent...")
    agent.save("./models/ppo_gold_agent")

    # Step 9: Plot training progress
    print("\n📊 Step 9: Generating training plots...")
    if len(episode_rewards) > 0:
        plot_training_progress(episode_rewards)
    else:
        print("⚠️ No episode rewards to plot")
        print("   This usually means episodes are longer than training timesteps.")
        print("   Try increasing total_timesteps to at least 20000")


def plot_training_progress(episode_rewards: list[float]):
    """Institutional standard plotting for PPO training progress"""
    if not episode_rewards:
        print("⚠️ No rewards found to plot.")
        return

    # Use plt.subplots to define the scope of ax1 and ax2
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))

    # Plot 1: Raw Episode Rewards
    ax1.plot(episode_rewards, alpha=0.3, color="blue", label="Raw Reward")

    # Calculate and plot Moving Average
    window = 50
    if len(episode_rewards) >= window:
        moving_avg = pd.Series(episode_rewards).rolling(window=window).mean()
        ax1.plot(moving_avg, linewidth=2, color="red", label=f"{window}-Ep Moving Avg")

    ax1.set_xlabel("Episode")
    ax1.set_ylabel("Reward")
    ax1.set_title("PPO Training Progress - Episode Rewards")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Cumulative Average Reward
    cumulative_avg = pd.Series(episode_rewards).expanding().mean()
    ax2.plot(cumulative_avg, linewidth=2, color="green")
    ax2.set_xlabel("Episode")
    ax2.set_ylabel("Cumulative Average Reward")
    ax2.set_title("Cumulative Average Reward Over Time")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("logs/training_progress.png")
    print("📈 Progress plot saved to logs/training_progress.png")


if __name__ == "__main__":
    try:
        train_ppo_agent()
    except KeyboardInterrupt:
        print("\n\n⚠️ Training interrupted by user!")
    except Exception as e:
        print(f"\n\n❌ ERROR: {str(e)}")
        import traceback

        traceback.print_exc()

        pass  # Removed broken plotting code from exception block
    print("📊 Training plot saved: ppo_training_progress.png")
    plt.show()


if __name__ == "__main__":
    try:
        train_ppo_agent()
    except KeyboardInterrupt:
        print("\n\n⚠️ Training interrupted by user!")
    except Exception as e:
        print(f"\n\n❌ ERROR: {str(e)}")
        import traceback

        traceback.print_exc()
