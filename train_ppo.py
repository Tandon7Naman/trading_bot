"""
Training Pipeline for PPO Agent
FIXED: Monitor wrapper, episode tracking, and real data handling
"""

import os
import warnings
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from ppo_agent import GoldPPOAgent
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv
from trading_environment import GoldTradingEnv
from lstm_model_consolidated import GoldLSTMModel

# Suppress warnings
warnings.filterwarnings('ignore', category=UserWarning)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


def train_ppo_agent():
    """Complete training pipeline for PPO agent"""
    print("\n" + "=" * 60)
    print("🎯 PPO AGENT TRAINING PIPELINE")
    print("=" * 60)

    # Step 1: Load data
    print("\n📊 Step 1: Loading MCX Gold data...")
    try:
        df = pd.read_csv('data/mcx_gold_historical.csv', parse_dates=['timestamp'])
        print(f"✅ Loaded {len(df)} records")
        print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"   Price range: ₹{df['close'].min():.2f} - ₹{df['close'].max():.2f}")
    except FileNotFoundError:
        print("❌ Data file not found.")
        print("⚠️ Run: python download_gold_data.py first to get real data")
        print("   Or training will use sample data (unrealistic results)")

        dates = pd.date_range(start='2023-01-01', periods=1000, freq='D')
        df = pd.DataFrame(
            {
                'timestamp': dates,
                'open': np.random.uniform(6000, 7000, 1000),
                'high': np.random.uniform(6100, 7100, 1000),
                'low': np.random.uniform(5900, 6900, 1000),
                'close': np.random.uniform(6000, 7000, 1000),
            }
        )
        print("✅ Created sample data (for testing only)")

    # Step 2: Load or train LSTM model
    print("\n🧠 Step 2: Loading LSTM model...")
    lstm_model = GoldLSTMModel(lookback=60, features=4)

    try:
        lstm_model.load('models/lstm_consolidated.h5')
        print("✅ LSTM model loaded")
    except Exception:
        print("⚠️ LSTM model not found. Training...")
        X_train, y_train, X_test, y_test = lstm_model.prepare_data(df)
        lstm_model.build_model()
        lstm_model.train(X_train, y_train, epochs=20, batch_size=32)
        lstm_model.save('models/lstm_consolidated.h5')
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

    os.makedirs('logs', exist_ok=True)

    env = GoldTradingEnv(
        df=train_df,
        lstm_model=lstm_model,
        initial_capital=100000,
        transaction_cost=0.0005,
        slippage=10,
    )

    monitored_env = Monitor(env, filename='./logs/training_monitor.csv')
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
    test_monitored_env = Monitor(test_env, filename='./logs/test_monitor.csv')
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
        sharpe_pass = metrics['sharpe_ratio'] > 1.2
        dd_pass = metrics['max_drawdown'] > -10
        wr_pass = metrics['win_rate'] > 45

        print(f"   Sharpe > 1.2: {'✅ PASS' if sharpe_pass else '❌ FAIL'} ({metrics['sharpe_ratio']:.2f})")
        print(f"   Max DD < -10%: {'✅ PASS' if dd_pass else '❌ FAIL'} ({metrics['max_drawdown']:.2f}%)")
        print(f"   Win Rate > 45%: {'✅ PASS' if wr_pass else '❌ FAIL'} ({metrics['win_rate']:.2f}%)")

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
    agent.save('./models/ppo_gold_agent')

    # Step 9: Plot training progress
    print("\n📊 Step 9: Generating training plots...")
    if len(episode_rewards) > 0:
        plot_training_progress(episode_rewards)
    else:
        print("⚠️ No episode rewards to plot")
        print("   This usually means episodes are longer than training timesteps.")
        print("   Try increasing total_timesteps to at least 20000")


def plot_training_progress(episode_rewards: List[float]):
    """Plot training progress"""
    if len(episode_rewards) == 0:
        print("⚠️ No episode rewards to plot")
        return

    print(f"📊 Plotting {len(episode_rewards)} episodes...")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    ax1.plot(episode_rewards, alpha=0.6, label='Episode Reward', linewidth=1)

    if len(episode_rewards) >= 10:
        window = min(10, len(episode_rewards))
        moving_avg = pd.Series(episode_rewards).rolling(window=window).mean()
        ax1.plot(moving_avg, linewidth=2, label=f'{window}-Episode Moving Avg', color='red')

    ax1.set_xlabel('Episode')
    ax1.set_ylabel('Reward')
    ax1.set_title('PPO Training Progress - Episode Rewards')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=0, color='black', linestyle='--', alpha=0.3)

    cumulative_avg = pd.Series(episode_rewards).expanding().mean()
    ax2.plot(cumulative_avg, linewidth=2, color='green')
    ax2.set_xlabel('Episode')
    ax2.set_ylabel('Cumulative Average Reward')
    ax2.set_title('Cumulative Average Reward Over Time')
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='black', linestyle='--', alpha=0.3)

    stats_text = (
        f'Episodes: {len(episode_rewards)}\n'
        f'Mean: {np.mean(episode_rewards):.2f}\n'
        f'Std: {np.std(episode_rewards):.2f}\n'
        f'Min: {np.min(episode_rewards):.2f}\n'
        f'Max: {np.max(episode_rewards):.2f}'
    )

    ax2.text(
        0.02,
        0.98,
        stats_text,
        transform=ax2.transAxes,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
    )

    plt.tight_layout()
    plt.savefig('ppo_training_progress.png', dpi=150)
    print("✅ Training plot saved: ppo_training_progress.png")

    try:
        plt.show()
    except Exception:
        print("   (Plot saved but cannot display - may be running in headless mode)")


if __name__ == "__main__":
    try:
        train_ppo_agent()
    except KeyboardInterrupt:
        print("\n\n⚠️ Training interrupted by user!")
    except Exception as e:
        print(f"\n\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

def plot_training_progress(episode_rewards):
    """Plot training progress"""
    import matplotlib.pyplot as plt
    
    if len(episode_rewards) == 0:
        print("⚠️ No episode rewards to plot")
        return
    
    # Create figure with 2 subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Plot 1: Episode rewards
    ax1.plot(episode_rewards, alpha=0.6, label='Episode Reward')
    
    # Add moving average
    if len(episode_rewards) > 50:
        window = 50
        moving_avg = pd.Series(episode_rewards).rolling(window=window).mean()
        ax1.plot(moving_avg, linewidth=2, label=f'{window}-Episode Moving Avg', color='red')
    
    ax1.set_xlabel('Episode')
    ax1.set_ylabel('Reward')
    ax1.set_title('PPO Training Progress - Episode Rewards')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Cumulative average reward
    cumulative_avg = pd.Series(episode_rewards).expanding().mean()
    ax2.plot(cumulative_avg, linewidth=2, color='green')
    ax2.set_xlabel('Episode')
    ax2.set_ylabel('Cumulative Average Reward')
    ax2.set_title('Cumulative Average Reward Over Time')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('ppo_training_progress.png', dpi=150)
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
