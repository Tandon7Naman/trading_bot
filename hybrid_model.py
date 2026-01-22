"""
Hybrid LSTM+PPO Model
Integrates LSTM predictions with PPO decision making
"""

import numpy as np

from lstm_model_consolidated import GoldLSTMModel
from ppo_agent import GoldPPOAgent


class HybridTradingModel:
    """
    Combines LSTM price prediction with PPO reinforcement learning

    Architecture:
    1. LSTM predicts price direction (probability 0-1)
    2. LSTM signal is added to market features
    3. PPO agent decides action based on augmented features
    """

    def __init__(
        self, lstm_model_path="models/lstm_consolidated.h5", ppo_model_path="models/ppo_gold_agent"
    ):
        # Load LSTM model
        self.lstm_model = GoldLSTMModel(lookback=60, features=4)
        self.lstm_model.load(lstm_model_path)

        # Load PPO agent
        self.ppo_agent = GoldPPOAgent(env=None)  # Env will be set later
        self.ppo_agent.load(ppo_model_path)

        print("✅ Hybrid Model Initialized")
        print("   LSTM: Price prediction")
        print("   PPO: Decision making")

    def predict_action(self, market_data, current_observation):
        """
        Generate trading action using hybrid approach

        Args:
            market_data: Last 60 bars of OHLC data for LSTM
            current_observation: Current market state (15 features)

        Returns:
            action: 0=HOLD, 1=BUY, 2=SELL
            lstm_signal: LSTM prediction
            confidence: PPO confidence score
        """
        # Step 1: Get LSTM signal
        lstm_signal = self.lstm_model.predict(market_data)

        # Step 2: Augment observation with LSTM signal
        augmented_obs = np.append(current_observation, lstm_signal)

        # Step 3: Get PPO action
        action = self.ppo_agent.predict(augmented_obs, deterministic=True)

        # Step 4: Calculate confidence (simplified)
        confidence = abs(lstm_signal - 0.5) * 2  # 0 to 1 scale

        return int(action), float(lstm_signal), float(confidence)

    def get_trading_signal(self, df, current_idx):
        """
        Get complete trading signal for current market state

        Args:
            df: DataFrame with OHLC data
            current_idx: Current index in dataframe

        Returns:
            dict with action, signal, confidence, and explanation
        """
        if current_idx < 60:
            return {
                "action": 0,
                "action_name": "HOLD",
                "lstm_signal": 0.5,
                "confidence": 0.0,
                "explanation": "Insufficient data for prediction",
            }

        # Get LSTM input (last 60 bars)
        lstm_input = df.iloc[current_idx - 60 : current_idx][
            ["open", "high", "low", "close"]
        ].values

        # Get current market features (simplified)
        current_features = self._extract_features(df, current_idx)

        # Get prediction
        action, lstm_signal, confidence = self.predict_action(lstm_input, current_features)

        action_names = ["HOLD", "BUY", "SELL"]

        # Generate explanation
        explanation = self._generate_explanation(action, lstm_signal, confidence)

        return {
            "action": action,
            "action_name": action_names[action],
            "lstm_signal": lstm_signal,
            "confidence": confidence,
            "explanation": explanation,
        }

    def _extract_features(self, df, idx):
        """Extract market features for current state"""
        current = df.iloc[idx]

        features = []

        # Price features
        close = current["close"]
        features.extend(
            [
                (current["open"] - close) / close,
                (current["high"] - close) / close,
                (current["low"] - close) / close,
                0.0,
            ]
        )

        # Technical features (simplified)
        window = df.iloc[max(0, idx - 20) : idx]
        if len(window) > 1:
            returns = window["close"].pct_change().dropna()
            features.extend(
                [
                    returns.mean(),
                    returns.std(),
                    (close - window["close"].min())
                    / (window["close"].max() - window["close"].min() + 1e-8),
                    (close - window["close"].mean()) / (window["close"].std() + 1e-8),
                    1 if close > window["close"].mean() else 0,
                    window["close"].iloc[-1] / window["close"].iloc[0] - 1,
                ]
            )
        else:
            features.extend([0] * 6)

        # Indian features placeholders
        features.extend([0, 0, 0.06, 0, 0])

        return np.array(features, dtype=np.float32)

    def _generate_explanation(self, action, lstm_signal, confidence):
        """Generate human-readable explanation"""
        action_names = ["HOLD", "BUY", "SELL"]

        explanation = f"Action: {action_names[action]}\n"

        # LSTM interpretation
        if lstm_signal > 0.6:
            explanation += f"LSTM: Strong bullish signal ({lstm_signal:.2%})\n"
        elif lstm_signal > 0.55:
            explanation += f"LSTM: Bullish signal ({lstm_signal:.2%})\n"
        elif lstm_signal < 0.4:
            explanation += f"LSTM: Strong bearish signal ({lstm_signal:.2%})\n"
        elif lstm_signal < 0.45:
            explanation += f"LSTM: Bearish signal ({lstm_signal:.2%})\n"
        else:
            explanation += f"LSTM: Neutral signal ({lstm_signal:.2%})\n"

        # Confidence interpretation
        if confidence > 0.7:
            explanation += f"Confidence: HIGH ({confidence:.2%})"
        elif confidence > 0.4:
            explanation += f"Confidence: MEDIUM ({confidence:.2%})"
        else:
            explanation += f"Confidence: LOW ({confidence:.2%})"

        return explanation

    def backtest(self, df, initial_capital=100000):
        """
        Simple backtest of hybrid model

        Args:
            df: Historical data
            initial_capital: Starting capital

        Returns:
            dict with backtest results
        """
        capital = initial_capital
        position = 0
        entry_price = 0
        trades = []

        print("\n🔬 Running Hybrid Model Backtest...")
        print(f"   Data points: {len(df)}")
        print(f"   Initial capital: ₹{initial_capital:,.0f}")

        for i in range(60, len(df)):
            signal = self.get_trading_signal(df, i)
            current_price = df.iloc[i]["close"]

            # Execute trades
            if signal["action"] == 1 and position == 0 and signal["confidence"] > 0.5:  # BUY
                position = 1
                entry_price = current_price
                capital -= current_price

            elif signal["action"] == 2 and position == 1:  # SELL
                proceeds = current_price
                pnl = proceeds - entry_price
                capital += proceeds

                trades.append(
                    {
                        "entry": entry_price,
                        "exit": current_price,
                        "pnl": pnl,
                        "return_pct": pnl / entry_price * 100,
                    }
                )

                position = 0

        # Calculate metrics
        if len(trades) > 0:
            total_return = (capital - initial_capital) / initial_capital * 100
            win_rate = len([t for t in trades if t["pnl"] > 0]) / len(trades) * 100

            return {
                "total_return_pct": total_return,
                "win_rate_pct": win_rate,
                "num_trades": len(trades),
                "final_capital": capital,
            }
        return None
