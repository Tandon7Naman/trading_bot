"""
Test PPO Agent
Quick testing and validation script
"""

import pandas as pd
import numpy as np
from trading_environment import GoldTradingEnv
from ppo_agent import GoldPPOAgent
from lstm_model_consolidated import GoldLSTMModel
from stable_baselines3.common.vec_env import DummyVecEnv

def test_ppo_agent():
    """
    Test trained PPO agent
    """
    print("\n" + "="*60)
    print("🧪 TESTING PPO AGENT")
    print("="*60)
    
    # Load data
    print("\n📊 Loading data...")
    try:
        df = pd.read_csv('data/mcx_gold_historical.csv', parse_dates=['timestamp'])
        print(f"✅ Loaded {len(df)} records")
    except FileNotFoundError:
        print("❌ No data file found. Please run train_ppo.py first.")
        return
    
    # Load LSTM model
    print("\n🧠 Loading LSTM model...")
    lstm_model = GoldLSTMModel(lookback=60, features=4)
    try:
        lstm_model.load('models/lstm_consolidated.h5')
        print("✅ LSTM loaded")
    except:
        print("❌ LSTM model not found. Train it first.")
        return
    
    # Create environment (use last 20% of data for testing)
    print("\n🎮 Creating test environment...")
    test_df = df.iloc[int(0.8*len(df)):].reset_index(drop=True)
    
    env = GoldTradingEnv(
        df=test_df,
        lstm_model=lstm_model,
        initial_capital=100000
    )
    
    # Load PPO agent
    print("\n🤖 Loading PPO agent...")
    agent = GoldPPOAgent(env=DummyVecEnv([lambda: env]))
    
    try:
        agent.load('models/ppo_gold_agent')
        print("✅ PPO agent loaded")
    except:
        print("❌ PPO agent not found. Train it first with train_ppo.py")
        return
    
    # --- SHAPE TEST: Ensure predict() works with correct dummy observation ---
    print("\n🧪 Testing PPO predict() with dummy observation...")
    dummy_obs = np.zeros((16,), dtype=np.float32)
    try:
        _ = agent.predict(dummy_obs, deterministic=True)
        print("   ✅ PPO predict() accepted dummy observation of shape (16,)")
    except Exception as e:
        print(f"   ❌ PPO predict() failed with dummy observation: {e}")
        return

    # Run test episode
    print("\n▶️ Running test episode...")
    obs, _ = env.reset()
    done = False
    step = 0

    actions_taken = {'HOLD': 0, 'BUY': 0, 'SELL': 0}
    action_names = ['HOLD', 'BUY', 'SELL']

    while not done and step < 100:  # Limit steps for quick test
        action = agent.predict(obs, deterministic=True)
        actions_taken[action_names[action]] += 1

        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated

        if step % 20 == 0:
            print(f"   Step {step}: Action={action_names[action]}, "
                  f"Capital=₹{info['capital']:,.0f}, "
                  f"Position={info['position']}")

        step += 1

    # Get final metrics
    print("\n📊 Test Results:")
    print("-" * 60)
    metrics = env.get_metrics()

    if metrics:
        print(f"   Total Return: {metrics['total_return']:.2f}%")
        print(f"   Trades: {metrics['num_trades']}")
        print(f"   Win Rate: {metrics['win_rate']:.2f}%")
        print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"   Max Drawdown: {metrics['max_drawdown']:.2f}%")
        print(f"   Final Capital: ₹{metrics['final_capital']:,.0f}")

    print("\n📈 Action Distribution:")
    for action, count in actions_taken.items():
        pct = count / sum(actions_taken.values()) * 100
        print(f"   {action}: {count} ({pct:.1f}%)")

    print("\n" + "="*60)
    print("✅ TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_ppo_agent()
