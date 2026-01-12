"""
PPO Agent for Gold Trading - COMPLETELY FIXED
Windows path issues, episode tracking, reward calculation
"""

import json
import os
from datetime import datetime

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.vec_env import DummyVecEnv


class TradingCallback(BaseCallback):
    """Simple, robust callback - FIXED for Windows"""

    def __init__(self, verbose: int = 1):
        super().__init__(verbose)
        self.episode_count = 0
        self.episode_rewards = []
        self.best_mean_reward = -np.inf

    def _on_rollout_end(self) -> None:
        """Track episodes"""
        if hasattr(self.model, "ep_info_buffer") and len(self.model.ep_info_buffer) > 0:
            for ep_info in self.model.ep_info_buffer:
                self.episode_count += 1
                ep_reward = ep_info["r"]
                self.episode_rewards.append(ep_reward)

                if self.verbose > 0 and self.episode_count % 10 == 0:
                    recent = self.episode_rewards[-10:]
                    avg = np.mean(recent)
                    print(f"✨ Ep {self.episode_count}: Reward={ep_reward:.2f}, Avg(10)={avg:.2f}")

                    if avg > self.best_mean_reward:
                        self.best_mean_reward = avg
                        print(f"🌟 New best! Avg: {avg:.2f}")

    def _on_step(self) -> bool:
        return True

    def _on_training_end(self) -> None:
        print(f"\n✅ Completed: {self.episode_count} episodes")
        if self.episode_rewards:
            print(f"   Mean: {np.mean(self.episode_rewards):.2f}")
            print(f"   Best: {self.best_mean_reward:.2f}")


class GoldPPOAgent:
    """PPO Agent for Gold Trading"""

    def __init__(self, env, learning_rate: float = 3e-4, n_steps: int = 2048, batch_size: int = 64):
        self.env = env
        self.model = None
        self.learning_rate = learning_rate
        self.n_steps = n_steps
        self.batch_size = batch_size
        self.training_history = []

    def create_model(self, policy: str = "MlpPolicy"):
        """Create PPO model"""
        self.model = PPO(
            policy,
            self.env,
            learning_rate=self.learning_rate,
            n_steps=self.n_steps,
            batch_size=self.batch_size,
            n_epochs=10,
            gamma=0.99,
            verbose=1,
            tensorboard_log="./ppo_tensorboard/",
        )
        print("✅ PPO Model created")
        return self.model

    def train(self, total_timesteps: int = 100000):
        """Train the PPO agent"""
        if self.model is None:
            self.create_model()

        print(f"\n🚀 Training: {total_timesteps:,} timesteps\n")

        callback = TradingCallback(verbose=1)
        start_time = datetime.now()

        self.model.learn(total_timesteps=total_timesteps, callback=callback, progress_bar=True)

        training_time = (datetime.now() - start_time).total_seconds()

        # Save final model
        self.model.save("./models/ppo_final")
        print(f"\n💾 Saved: ./models/ppo_final.zip ({training_time/60:.1f} min)")

        return callback.episode_rewards

    def evaluate(self, n_eval_episodes: int = 10):
        """Evaluate agent"""
        mean_reward, std_reward = evaluate_policy(
            self.model, self.env, n_eval_episodes=n_eval_episodes, deterministic=True
        )
        print(f"📊 Eval: {mean_reward:.2f} ± {std_reward:.2f}")
        return mean_reward, std_reward

    def predict(self, observation, deterministic: bool = True):
        """Make prediction"""
        action, _states = self.model.predict(observation, deterministic=deterministic)
        return action

    def save(self, path: str = "./models/ppo_agent"):
        """Save agent"""
        path = path.replace("\\", "/")  # Fix Windows paths
        self.model.save(path)
        print(f"💾 Saved: {path}.zip")

    def load(self, path: str = "./models/ppo_agent"):
        """Load agent"""
        path = path.replace("\\", "/")
        self.model = PPO.load(path)
        print(f"✅ Loaded: {path}.zip")
        return self.model