import json

# Load training history
with open("models/ppo_gold_agent_history.json") as f:
    history = json.load(f)

print("=" * 60)
print("🎯 PPO TRAINING RESULTS")
print("=" * 60)

for i, run in enumerate(history):
    timestamp = run.get("timestamp", "N/A")
    total_steps = run.get("total_timesteps", 0)
    train_secs = run.get("training_time_seconds", 0)
    episodes = run.get("num_episodes", len(run.get("episode_rewards", [])))
    mean_reward = run.get("mean_reward", 0)
    best_reward = run.get("best_mean_reward", 0)

    print(f"\nTraining Run {i + 1}:")
    print(f"   Timestamp: {timestamp}")
    print(f"   Total Timesteps: {total_steps:,}")
    print(f"   Training Time: {train_secs / 60:.1f} minutes")
    print(f"   Episodes: {episodes}")
    print(f"   Mean Reward: {mean_reward:.2f}")
    print(f"   Best Reward: {best_reward:.2f}")

print("\n" + "=" * 60)
print("✅ Models are saved and ready to use!")
print("=" * 60)
