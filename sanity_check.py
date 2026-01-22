"""
Quick Sanity Check - Verify Environment & Rewards
Tests: Episode length, reward calculation, action execution
"""

import numpy as np
import pandas as pd

from lstm_model_consolidated import GoldLSTMModel
from trading_environment import GoldTradingEnv


def sanity_check():
    print("\n" + "=" * 60)
    print("🧪 ENVIRONMENT SANITY CHECK")
    print("=" * 60)

    # Load data
    print("\n📊 Loading data...")
    try:
        df = pd.read_csv("data/mcx_gold_historical.csv", parse_dates=["timestamp"])
        train_df = df.iloc[: int(0.8 * len(df))].reset_index(drop=True)
        print(f"✅ Loaded {len(train_df)} training records")
    except FileNotFoundError:
        print("❌ Data file not found")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        return False

    # Load LSTM
    print("\n🧠 Loading LSTM...")
    try:
        lstm = GoldLSTMModel(lookback=60, features=4)
        lstm.load("models/lstm_consolidated.h5")
        print("✅ LSTM loaded")
    except FileNotFoundError:
        print("❌ LSTM model not found")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        return False

    # Create environment
    print("\n🎮 Creating environment...")
    env = GoldTradingEnv(df=train_df, lstm_model=lstm, initial_capital=100000)
    print("✅ Environment created")

    # Run test episodes
    print("\n" + "=" * 60)
    print("🧪 RUNNING 10 RANDOM EPISODES")
    print("=" * 60)

    episode_lengths = []
    episode_rewards = []

    for ep in range(10):
        obs, _ = env.reset()
        done = False
        total_reward = 0
        steps = 0
        actions_taken = {"HOLD": 0, "BUY": 0, "SELL": 0}
        action_names = ["HOLD", "BUY", "SELL"]

        while not done and steps < 300:  # Max 300 steps per episode
            action = env.action_space.sample()  # Random action
            actions_taken[action_names[action]] += 1

            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            steps += 1
            done = terminated or truncated

        episode_lengths.append(steps)
        episode_rewards.append(total_reward)

        print(f"\nEpisode {ep + 1}:")
        print(f"   Steps: {steps}")
        print(f"   Total Reward: {total_reward:.2f}")
        print(f"   Final Capital: ₹{info['capital']:,.0f}")
        print(f"   Trades: {info['num_trades']}")
        print(
            f"   Actions: H={actions_taken['HOLD']}, B={actions_taken['BUY']}, S={actions_taken['SELL']}"
        )

    # Analyze results
    print("\n" + "=" * 60)
    print("📊 SANITY CHECK RESULTS")
    print("=" * 60)

    avg_length = np.mean(episode_lengths)
    avg_reward = np.mean(episode_rewards)

    print("\n📈 Episode Statistics:")
    print(f"   Avg Length: {avg_length:.1f} steps")
    print(f"   Length Range: {min(episode_lengths)} - {max(episode_lengths)}")
    print(f"   Avg Reward: {avg_reward:.2f}")
    print(f"   Reward Range: {min(episode_rewards):.2f} - {max(episode_rewards):.2f}")

    # Validation checks
    print("\n✅ Validation Checks:")

    checks_passed = 0
    total_checks = 3

    # Check 1: Episode length
    if avg_length >= 50:
        print(f"   ✅ Episode Length: {avg_length:.0f} (target: >50)")
        checks_passed += 1
    else:
        print(f"   ❌ Episode Length: {avg_length:.0f} (target: >50) - Episodes too short!")

    # Check 2: Rewards non-zero
    if abs(avg_reward) > 0.01:
        print(f"   ✅ Rewards Active: {avg_reward:.2f} (non-zero)")
        checks_passed += 1
    else:
        print(f"   ❌ Rewards Broken: {avg_reward:.2f} (all zeros!)")

    # Check 3: Reward variance
    reward_std = np.std(episode_rewards)
    if reward_std > 0.1:
        print(f"   ✅ Reward Variance: {reward_std:.2f} (good variation)")
        checks_passed += 1
    else:
        print(f"   ❌ Reward Variance: {reward_std:.2f} (too uniform)")

    print("\n" + "=" * 60)
    if checks_passed == total_checks:
        print("🎉 ALL CHECKS PASSED - READY FOR TRAINING!")
        print("=" * 60)
        print("\nNext step:")
        print("   Edit train_ppo.py: total_timesteps=20000")
        print("   Run: python train_ppo.py")
        return True
    else:
        print(f"⚠️ CHECKS FAILED: {checks_passed}/{total_checks} passed")
        print("=" * 60)
        print("\nIssues need fixing before training")
        return False


if __name__ == "__main__":
    try:
        success = sanity_check()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback

        traceback.print_exc()
        exit(1)
