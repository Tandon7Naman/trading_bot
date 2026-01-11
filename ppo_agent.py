"""
PPO Agent for Gold Trading
Uses Stable-Baselines3 for RL training
FIXED: Episode tracking, monitoring, and callbacks
"""

import json
import os
from datetime import datetime

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.evaluation import evaluate_policy


class TradingCallback(BaseCallback):
    """
    Custom callback for training monitoring
    FIXED: Proper episode reward tracking
    """

    def __init__(self, save_freq: int = 10000, save_path: str = './models/', verbose: int = 1):
        super().__init__(verbose)
        self.save_freq = save_freq
        self.save_path = save_path
        self.episode_rewards = []
        self.episode_lengths = []
        self.best_mean_reward = -np.inf
        self.n_episodes = 0

        os.makedirs(save_path, exist_ok=True)

    def _on_step(self) -> bool:
        if self.n_calls % self.save_freq == 0:
            model_path = os.path.join(self.save_path, f'ppo_checkpoint_{self.n_calls}')
            self.model.save(model_path)
            if self.verbose > 0:
                print(f"\n💾 Checkpoint saved at step {self.n_calls}")

        # Track episode completions from vec env infos
        if self.locals.get("dones") is not None:
            for i, done in enumerate(self.locals["dones"]):
                if done:
                    self.n_episodes += 1
                    info = self.locals["infos"][i]
                    if "episode" in info:
                        ep_reward = info["episode"]["r"]
                        ep_length = info["episode"]["l"]
                        self.episode_rewards.append(ep_reward)
                        self.episode_lengths.append(ep_length)

                        if self.verbose > 0 and len(self.episode_rewards) % 5 == 0:
                            recent_avg = np.mean(self.episode_rewards[-5:])
                            print(
                                f"✨ Episode {len(self.episode_rewards)}: "
                                f"Reward = {ep_reward:.2f}, "
                                f"Avg(5) = {recent_avg:.2f}"
                            )

        if len(self.episode_rewards) >= 10:
            mean_reward = np.mean(self.episode_rewards[-10:])
            if mean_reward > self.best_mean_reward:
                self.best_mean_reward = mean_reward
                best_path = os.path.join(self.save_path, 'ppo_best')
                self.model.save(best_path)
                if self.verbose > 0:
                    print(f"✨ New best model! Avg Reward (10 ep): {mean_reward:.2f}")

        return True

    def _on_training_end(self) -> None:
        if self.verbose > 0:
            print(f"\n✅ Training completed!")
            print(f"   Total steps: {self.n_calls}")
            print(f"   Total episodes: {len(self.episode_rewards)}")
            if len(self.episode_rewards) > 0:
                print(f"   Avg Reward: {np.mean(self.episode_rewards):.2f}")
                print(f"   Best Avg Reward: {self.best_mean_reward:.2f}")
                print(f"   Min Reward: {np.min(self.episode_rewards):.2f}")
                print(f"   Max Reward: {np.max(self.episode_rewards):.2f}")
            else:
                print("   ⚠️ Warning: No episodes completed")


class GoldPPOAgent:
    """PPO Agent wrapper for gold trading"""

    def __init__(self, env, learning_rate: float = 3e-4, n_steps: int = 2048, batch_size: int = 64):
        self.env = env
        self.model = None
        self.learning_rate = learning_rate
        self.n_steps = n_steps
        self.batch_size = batch_size
        self.training_history = []

        print("🤖 PPO Agent Initialized")
        print(f"   Learning Rate: {learning_rate}")
        print(f"   Steps per update: {n_steps}")
        print(f"   Batch Size: {batch_size}")

    def create_model(self, policy: str = 'MlpPolicy'):
        """Create PPO model"""
        self.model = PPO(
            policy,
            self.env,
            learning_rate=self.learning_rate,
            n_steps=self.n_steps,
            batch_size=self.batch_size,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.01,
            vf_coef=0.5,
            max_grad_norm=0.5,
            verbose=1,
            tensorboard_log="./ppo_tensorboard/",
        )

        print("✅ PPO Model created")
        print(f"   Policy: {policy}")
        print("   Network: 3-layer MLP [64, 64]")

        return self.model

    def train(self, total_timesteps: int = 100000, save_freq: int = 10000):
        """Train the PPO agent"""
        if self.model is None:
            self.create_model()

        print("\n" + "=" * 60)
        print("🚀 STARTING PPO TRAINING")
        print("=" * 60)
        print(f"   Total Timesteps: {total_timesteps:,}")
        print(f"   Save Frequency: {save_freq:,}")
        print("-" * 60)

        callback = TradingCallback(
            save_freq=save_freq,
            save_path='./models/',
            verbose=1,
        )

        start_time = datetime.now()
        self.model.learn(
            total_timesteps=total_timesteps,
            callback=callback,
            progress_bar=True,
        )
        end_time = datetime.now()

        training_time = (end_time - start_time).total_seconds()
        self.training_history.append(
            {
                'timestamp': end_time.isoformat(),
                'total_timesteps': total_timesteps,
                'training_time_seconds': training_time,
                'episode_rewards': callback.episode_rewards,
                'episode_lengths': callback.episode_lengths,
                'num_episodes': len(callback.episode_rewards),
                'best_mean_reward': callback.best_mean_reward,
                'mean_reward': np.mean(callback.episode_rewards) if callback.episode_rewards else 0,
                'std_reward': np.std(callback.episode_rewards) if callback.episode_rewards else 0,
            }
        )

        self.model.save('./models/ppo_final')

        print("\n" + "=" * 60)
        print("✅ TRAINING COMPLETE!")
        print("=" * 60)
        print(f"   Training Time: {training_time/60:.1f} minutes")
        print(f"   Episodes: {len(callback.episode_rewards)}")
        if len(callback.episode_rewards) > 0:
            print(f"   Mean Reward: {np.mean(callback.episode_rewards):.2f}")
            print(f"   Best Avg Reward: {callback.best_mean_reward:.2f}")
        print("   Model saved: ./models/ppo_final.zip")

        return callback.episode_rewards

    def evaluate(self, n_eval_episodes: int = 10):
        """Evaluate trained agent"""
        if self.model is None:
            raise ValueError("Model not trained yet!")

        print("\n📊 Evaluating PPO Agent...")
        print(f"   Episodes: {n_eval_episodes}")

        mean_reward, std_reward = evaluate_policy(
            self.model,
            self.env,
            n_eval_episodes=n_eval_episodes,
            deterministic=True,
        )

        print(f"\n✅ Evaluation Results:")
        print(f"   Mean Reward: {mean_reward:.2f} ± {std_reward:.2f}")

        return mean_reward, std_reward

    def predict(self, observation, deterministic: bool = True):
        """Make prediction"""
        if self.model is None:
            raise ValueError("Model not trained yet!")

        action, _states = self.model.predict(observation, deterministic=deterministic)
        return action

    def save(self, path: str = './models/ppo_agent'):
        """Save agent"""
        if self.model is None:
            raise ValueError("Model not trained yet!")

        self.model.save(path)

        history_path = path + '_history.json'
        with open(history_path, 'w') as f:
            json.dump(self.training_history, f, indent=4)

        print("💾 Agent saved:")
        print(f"   Model: {path}.zip")
        print(f"   History: {history_path}")

    def load(self, path: str = './models/ppo_agent'):
        """Load agent"""
        if not os.path.exists(f"{path}.zip"):
            raise FileNotFoundError(f"Model file not found: {path}.zip")

        self.model = PPO.load(path)

        history_path = path + '_history.json'
        try:
            with open(history_path, 'r') as f:
                self.training_history = json.load(f)
        except FileNotFoundError:
            pass

        print(f"✅ Agent loaded from {path}")

        return self.model
"""
PPO Agent for Gold Trading
Uses Stable-Baselines3 for RL training
"""

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.evaluation import evaluate_policy
import numpy as np
import json
from datetime import datetime
import os

class TradingCallback(BaseCallback):
    """
    Custom callback for training monitoring
    """
    def __init__(self, save_freq=10000, save_path='./models/', verbose=1):
        super().__init__(verbose)
        self.save_freq = save_freq
        self.save_path = save_path
        self.episode_rewards = []
        self.episode_lengths = []
        self.best_mean_reward = -np.inf
        
        # Create save directory
        os.makedirs(save_path, exist_ok=True)
        
    def _on_step(self) -> bool:
        # Save model periodically
        if self.n_calls % self.save_freq == 0:
            model_path = os.path.join(self.save_path, f'ppo_checkpoint_{self.n_calls}')
            self.model.save(model_path)
            if self.verbose > 0:
                print(f"\n💾 Checkpoint saved at step {self.n_calls}")
        
        # Log episode rewards
        if len(self.model.ep_info_buffer) > 0:
            for info in self.model.ep_info_buffer:
                self.episode_rewards.append(info['r'])
                self.episode_lengths.append(info['l'])
        
        # Check if best model
        if len(self.episode_rewards) > 100:
            mean_reward = np.mean(self.episode_rewards[-100:])
            if mean_reward > self.best_mean_reward:
                self.best_mean_reward = mean_reward
                best_path = os.path.join(self.save_path, 'ppo_best')
                self.model.save(best_path)
                if self.verbose > 0:
                    print(f"✨ New best model! Reward: {mean_reward:.2f}")
        
        return True
    
    def _on_training_end(self) -> None:
        if self.verbose > 0:
            print(f"\n✅ Training completed!")
            print(f"   Total steps: {self.n_calls}")
            print(f"   Episodes: {len(self.episode_rewards)}")
            if len(self.episode_rewards) > 0:
                print(f"   Avg Reward: {np.mean(self.episode_rewards):.2f}")
                print(f"   Best Reward: {self.best_mean_reward:.2f}")


class GoldPPOAgent:
    """
    PPO Agent wrapper for gold trading
    """
    
    def __init__(self, env, learning_rate=3e-4, n_steps=2048, batch_size=64):
        self.env = env
        self.model = None
        self.learning_rate = learning_rate
        self.n_steps = n_steps
        self.batch_size = batch_size
        self.training_history = []
        
        print("🤖 PPO Agent Initialized")
        print(f"   Learning Rate: {learning_rate}")
        print(f"   Steps per update: {n_steps}")
        print(f"   Batch Size: {batch_size}")
        
    def create_model(self, policy='MlpPolicy'):
        """Create PPO model"""
        self.model = PPO(
            policy,
            self.env,
            learning_rate=self.learning_rate,
            n_steps=self.n_steps,
            batch_size=self.batch_size,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.01,
            vf_coef=0.5,
            max_grad_norm=0.5,
            verbose=1,
            tensorboard_log="./ppo_tensorboard/"
        )
        
        print("✅ PPO Model created")
        print(f"   Policy: {policy}")
        print(f"   Network: 3-layer MLP [64, 64]")
        
        return self.model
    
    def train(self, total_timesteps=100000, save_freq=10000):
        """Train the PPO agent"""
        if self.model is None:
            self.create_model()
        
        print("\n" + "="*60)
        print("🚀 STARTING PPO TRAINING")
        print("="*60)
        print(f"   Total Timesteps: {total_timesteps:,}")
        print(f"   Save Frequency: {save_freq:,}")
        print("-" * 60)
        
        # Create callback
        callback = TradingCallback(
            save_freq=save_freq,
            save_path='./models/',
            verbose=1
        )
        
        # Train
        start_time = datetime.now()
        self.model.learn(
            total_timesteps=total_timesteps,
            callback=callback,
            progress_bar=True
        )
        end_time = datetime.now()
        
        # Save training history
        training_time = (end_time - start_time).total_seconds()
        self.training_history.append({
            'timestamp': end_time.isoformat(),
            'total_timesteps': total_timesteps,
            'training_time_seconds': training_time,
            'episode_rewards': callback.episode_rewards,
            'best_mean_reward': callback.best_mean_reward
        })
        
        # Save final model
        self.model.save('./models/ppo_final')
        
        print("\n" + "="*60)
        print("✅ TRAINING COMPLETE!")
        print("="*60)
        print(f"   Training Time: {training_time/60:.1f} minutes")
        print(f"   Episodes: {len(callback.episode_rewards)}")
        print(f"   Best Reward: {callback.best_mean_reward:.2f}")
        print(f"   Model saved: ./models/ppo_final.zip")
        
        return callback.episode_rewards
    
    def evaluate(self, n_eval_episodes=10):
        """Evaluate trained agent"""
        if self.model is None:
            raise ValueError("Model not trained yet!")
        
        print("\n📊 Evaluating PPO Agent...")
        print(f"   Episodes: {n_eval_episodes}")
        
        mean_reward, std_reward = evaluate_policy(
            self.model,
            self.env,
            n_eval_episodes=n_eval_episodes,
            deterministic=True
        )
        
        print(f"\n✅ Evaluation Results:")
        print(f"   Mean Reward: {mean_reward:.2f} ± {std_reward:.2f}")
        
        return mean_reward, std_reward
    
    def predict(self, observation, deterministic=True):
        """Make prediction"""
        if self.model is None:
            raise ValueError("Model not trained yet!")
        
        action, _states = self.model.predict(observation, deterministic=deterministic)
        return action
    
    def save(self, path='./models/ppo_agent'):
        """Save agent"""
        if self.model is None:
            raise ValueError("Model not trained yet!")
        
        self.model.save(path)
        
        # Save training history
        history_path = path + '_history.json'
        with open(history_path, 'w') as f:
            json.dump(self.training_history, f, indent=4)
        
        print(f"💾 Agent saved:")
        print(f"   Model: {path}.zip")
        print(f"   History: {history_path}")
    
    def load(self, path='./models/ppo_agent'):
        """Load agent"""
        self.model = PPO.load(path)
        
        # Load training history
        history_path = path + '_history.json'
        try:
            with open(history_path, 'r') as f:
                self.training_history = json.load(f)
        except FileNotFoundError:
            pass
        
        print(f"✅ Agent loaded from {path}")
        
        return self.model