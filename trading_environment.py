"""
Gold Trading Environment for PPO Agent
Implements OpenAI Gym interface
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd
from lstm_model_consolidated import GoldLSTMModel
from indian_features import IndianMarketFeatures

class GoldTradingEnv(gym.Env):
    """
    Custom Trading Environment for MCX Gold
    
    Observation Space: 16 dimensions
        - 15 market features (technical + Indian features)
        - 1 LSTM signal (price direction probability)
    
    Action Space: 3 discrete actions
        - 0: HOLD
        - 1: BUY
        - 2: SELL
    
    Reward: Profit/Loss normalized by capital
    """
    
    metadata = {'render_modes': ['human']}
    
    def __init__(self, df, lstm_model, initial_capital=100000, 
                 transaction_cost=0.0005, slippage=10):
        super().__init__()
        
        self.df = df.reset_index(drop=True)
        self.lstm_model = lstm_model
        self.indian_features = IndianMarketFeatures()

        # ✅ Ensure LSTM model is built
        if self.lstm_model.model is None:
            print("⚠️ LSTM model not built. Building now...")
            self.lstm_model.build_model()
        
        # Trading parameters
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.transaction_cost_pct = transaction_cost
        self.slippage = slippage
        
        # Position tracking
        self.position = 0  # 0: flat, 1: long
        self.entry_price = 0
        self.current_step = 0
        self.max_steps = len(df) - 1
        
        # Performance tracking
        self.trades = []
        self.net_worth_history = []
        self.unrealized_pnl = 0
        
        # Observation space: 16 features
        self.observation_space = spaces.Box(
            low=-10, high=10, shape=(16,), dtype=np.float32
        )
        
        # Action space: 0=HOLD, 1=BUY, 2=SELL
        self.action_space = spaces.Discrete(3)
        
        print("✅ Trading Environment Initialized")
        print(f"   Episodes: {len(df)}")
        print(f"   Initial Capital: ₹{initial_capital:,.0f}")
        print(f"   Observation dim: 16")
        print(f"   Action space: [HOLD, BUY, SELL]")
    
    def reset(self, seed=None, options=None):
        """Reset environment to initial state"""
        super().reset(seed=seed)
        
        self.capital = self.initial_capital
        self.position = 0
        self.entry_price = 0
        self.current_step = 60  # Start after LSTM lookback
        self.trades = []
        self.net_worth_history = [self.initial_capital]
        self.unrealized_pnl = 0
        
        observation = self._get_observation()
        info = self._get_info()
        
        return observation, info
    
    def step(self, action):
        """Execute one trading step"""
        current_price = self.df.loc[self.current_step, 'close']
        reward = 0
        trade_executed = False
        
        # Execute action
        if action == 1 and self.position == 0:  # BUY
            trade_executed = self._execute_buy(current_price)
            
        elif action == 2 and self.position == 1:  # SELL
            trade_executed = self._execute_sell(current_price)
            pnl = self.trades[-1]['pnl']
            reward = pnl / self.initial_capital * 100  # Normalize reward
        
        # Calculate unrealized P&L for open positions
        if self.position == 1:
            self.unrealized_pnl = (current_price - self.entry_price) * 1
            # Small reward for holding profitable position
            if self.unrealized_pnl > 0:
                reward += self.unrealized_pnl / self.initial_capital * 10
        
        # Penalize excessive trading (ignore open trades with no exit yet)
        if len(self.trades) > 0:
            recent_trades = len(
                [
                    t for t in self.trades
                    if t.get('exit_step') is not None
                    and t['exit_step'] > self.current_step - 10
                ]
            )
            if recent_trades > 3:
                reward -= 0.1
        
        # Move to next step
        self.current_step += 1
        
        # Calculate net worth
        net_worth = self.capital
        if self.position == 1:
            net_worth += self.unrealized_pnl
        self.net_worth_history.append(net_worth)
        
        # Check if episode is done
        terminated = self.current_step >= self.max_steps
        truncated = self.capital < self.initial_capital * 0.7  # 30% loss
        
        observation = self._get_observation()
        info = self._get_info()
        
        return observation, reward, terminated, truncated, info
    
    def _execute_buy(self, price):
        """Execute buy order"""
        # Apply slippage and transaction costs
        execution_price = price + self.slippage
        cost = execution_price * (1 + self.transaction_cost_pct)
        
        if self.capital >= cost:
            self.position = 1
            self.entry_price = cost
            self.capital -= cost
            
            self.trades.append({
                'type': 'BUY',
                'entry_step': self.current_step,
                'entry_price': cost,
                'exit_step': None,
                'exit_price': None,
                'pnl': None
            })
            return True
        return False
    
    def _execute_sell(self, price):
        """Execute sell order"""
        # Apply slippage and transaction costs
        execution_price = price - self.slippage
        proceeds = execution_price * (1 - self.transaction_cost_pct)
        
        self.capital += proceeds
        pnl = proceeds - self.entry_price
        
        # Update last trade
        self.trades[-1].update({
            'exit_step': self.current_step,
            'exit_price': proceeds,
            'pnl': pnl
        })
        
        self.position = 0
        self.entry_price = 0
        self.unrealized_pnl = 0
        
        return True
    
    def _get_observation(self):
        """Get current market observation"""
        if self.current_step < 60:
            return np.zeros(16, dtype=np.float32)
        
        # Get current row
        current = self.df.loc[self.current_step]
        
        # Calculate technical features (10 features)
        features = []
        
        # 1-4: Price features (normalized)
        close = current['close']
        features.extend([
            (current['open'] - close) / close,
            (current['high'] - close) / close,
            (current['low'] - close) / close,
            0.0  # Placeholder for volume
        ])
        
        # 5-10: Technical indicators (simplified)
        window = self.df.loc[max(0, self.current_step-20):self.current_step]
        if len(window) > 1:
            returns = window['close'].pct_change().dropna()
            features.extend([
                returns.mean(),
                returns.std(),
                (close - window['close'].min()) / (window['close'].max() - window['close'].min() + 1e-8),
                (close - window['close'].mean()) / (window['close'].std() + 1e-8),
                1 if close > window['close'].mean() else 0,
                window['close'].iloc[-1] / window['close'].iloc[0] - 1
            ])
        else:
            features.extend([0] * 6)
        
        # 11-15: Indian features
        indian_feat = [
            self.indian_features.calculate_monsoon_factor(100, 100),
            self.indian_features.calculate_lunar_demand_index(
                pd.to_datetime(current.name if hasattr(current, 'name') else None)
            ),
            self.indian_features.calculate_import_duty_feature(),
            0.0,  # Fair value (needs external data)
            0.0   # Real yield (needs external data)
        ]
        features.extend(indian_feat)
        
        # 16: LSTM signal
        lstm_window = self.df.loc[self.current_step-60:self.current_step-1, 
                                  ['open', 'high', 'low', 'close']].values
        if len(lstm_window) == 60:
            lstm_signal = self.lstm_model.predict(lstm_window)
        else:
            lstm_signal = 0.5
        
        features.append(float(lstm_signal))
        
        # Clip to observation space
        observation = np.clip(features, -10, 10).astype(np.float32)
        
        return observation
    
    def _get_info(self):
        """Get additional info"""
        return {
            'step': self.current_step,
            'capital': self.capital,
            'position': self.position,
            'net_worth': self.net_worth_history[-1],
            'num_trades': len(self.trades),
            'unrealized_pnl': self.unrealized_pnl
        }
    
    def render(self, mode='human'):
        """Render environment state"""
        if mode == 'human':
            profit = self.capital - self.initial_capital
            print(f"\nStep: {self.current_step}/{self.max_steps}")
            print(f"Capital: ₹{self.capital:,.0f} ({profit:+,.0f})")
            print(f"Position: {'LONG' if self.position else 'FLAT'}")
            print(f"Trades: {len(self.trades)}")
    
    def get_metrics(self):
        """Calculate performance metrics"""
        if len(self.trades) == 0:
            return None
        
        closed_trades = [t for t in self.trades if t['pnl'] is not None]
        if len(closed_trades) == 0:
            return None
        
        total_pnl = sum(t['pnl'] for t in closed_trades)
        winning_trades = [t for t in closed_trades if t['pnl'] > 0]
        losing_trades = [t for t in closed_trades if t['pnl'] < 0]
        
        # Calculate returns
        returns = np.array([t['pnl'] / self.initial_capital 
                           for t in closed_trades])
        
        # Sharpe ratio (simplified)
        sharpe = (returns.mean() / (returns.std() + 1e-8)) * np.sqrt(252)
        
        # Maximum drawdown
        net_worth_array = np.array(self.net_worth_history)
        running_max = np.maximum.accumulate(net_worth_array)
        drawdown = (net_worth_array - running_max) / running_max
        max_dd = drawdown.min()
        
        return {
            'total_return': total_pnl / self.initial_capital * 100,
            'num_trades': len(closed_trades),
            'win_rate': len(winning_trades) / len(closed_trades) * 100,
            'avg_win': np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0,
            'avg_loss': np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd * 100,
            'final_capital': self.capital
        }
