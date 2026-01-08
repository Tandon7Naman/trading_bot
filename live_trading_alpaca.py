"""
Live Paper Trading on Alpaca
Uses LSTM strategy to trade GLD (Gold ETF) in real-time.

Usage:
    python live_trading_alpaca.py
"""

import sys
import time
import logging
import numpy as np
from datetime import datetime
from typing import Dict, Optional

from config_alpaca import (
    ALPACA_API_KEY,
    ALPACA_SECRET_KEY,
    SYMBOLS,
    POSITION_SIZE,
)
from src.alpaca_broker import AlpacaBroker
from src.features import FeatureEngine
from src.models.lstm_signal import create_lstm_model


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AlpacaLiveTrader:
    """
    Live paper trading engine using Alpaca + LSTM strategy.
    """

    def __init__(self):
        self.broker = AlpacaBroker(
            api_key=ALPACA_API_KEY,
            secret_key=ALPACA_SECRET_KEY,
            paper=True
        )
        self.fe = FeatureEngine()
        self.lstm = create_lstm_model()
        self.symbol = SYMBOLS[0]  # "GLD"
        self.position_size = POSITION_SIZE
        
        self.price_history = []
        self.trade_count = 0
        
        logger.info(f"✅ AlpacaLiveTrader initialized for {self.symbol}")

    def get_current_price(self) -> float:
        """
        Generate synthetic price (for demo).
        In production, use real market data feeds.
        """
        if not self.price_history:
            return 190.0  # GLD typical starting price
        
        # Random walk: small drift + noise
        last_price = self.price_history[-1]
        change = np.random.normal(0, 0.005)  # ±0.5% daily volatility
        new_price = last_price * (1 + change)
        return max(100, new_price)  # Keep price realistic

    def run_once(self, current_price: float) -> None:
        """
        Execute one trading cycle.
        """
        self.price_history.append(current_price)
        
        # Need at least 30 prices for features
        if len(self.price_history) < 30:
            logger.info(f"Warming up... {len(self.price_history)}/30 prices collected")
            return
        
        # Extract features
        closes = self.price_history[-30:]
        highs = [p * 1.001 for p in closes]
        lows = [p * 0.999 for p in closes]
        
        market_data = {
            'closes': closes,
            'highs': highs,
            'lows': lows,
            'bid': current_price - 0.10,
            'ask': current_price + 0.10,
            'buy_volume': 1000000,
            'sell_volume': 900000,
            'spot_gold_usd': 2500,
            'usdinr': 83.5,
            'us_10y_yield': 4.0,
            'inflation_rate': 5.5,
            'monsoon_rainfall': 150,
            'monsoon_lpa': 140,
            'import_duty': 0.06,
            'duty_history': [0.06] * 7,
            'current_price': current_price
        }
        
        features = self.fe.extract_features(market_data)
        
        # Get LSTM signal
        X = np.array(features).reshape(1, 1, -1)
        signal = self.lstm.predict_signal(X)
        
        signal_side = signal['signal']
        confidence = signal['confidence']
        prob_up = signal['probability']
        
        logger.info(
            f"Bar {len(self.price_history):3d} | {signal_side:4s} | "
            f"Conf: {confidence:.0%} | Prob: {prob_up:.0%} | Price: ${current_price:.2f}"
        )
        
        # Get current position
        position = self.broker.get_position(self.symbol)
        
        # Trading logic
        if confidence > 0.50:
            if position is None:
                # No position -> open based on signal
                if signal_side == "BUY":
                    try:
                        self.broker.place_order(
                            self.symbol, "buy", self.position_size
                        )
                        self.trade_count += 1
                        logger.info(f"🟢 BUY {self.position_size} {self.symbol}")
                    except Exception as e:
                        logger.error(f"❌ Order failed: {e}")
            
            elif position:
                # Have position -> consider closing on opposite signal
                if position['side'] == 'long' and signal_side == "SELL" and confidence > 0.55:
                    try:
                        self.broker.close_position(self.symbol)
                        self.trade_count += 1
                        logger.info(f"🔴 CLOSE LONG {self.symbol} | P&L: ${position['unrealized_pl']:.2f}")
                    except Exception as e:
                        logger.error(f"❌ Close failed: {e}")

    def print_summary(self) -> None:
        """Print final account summary."""
        summary = self.broker.summary()
        
        print("\n" + "="*70)
        print("  📈 ALPACA PAPER TRADING SUMMARY")
        print("="*70 + "\n")
        
        print(f"Account:")
        print(f"  Cash:              ${summary['cash']:>12,.2f}")
        print(f"  Equity:            ${summary['equity']:>12,.2f}")
        print(f"  Portfolio Value:   ${summary['portfolio_value']:>12,.2f}")
        
        print(f"\nPositions:")
        print(f"  Open:              {summary['open_positions']:>12}")
        print(f"  Unrealized P&L:    ${summary['unrealized_pl']:>12,.2f}")
        
        if summary['positions']:
            print(f"\nOpen Positions:")
            for pos in summary['positions']:
                print(f"  {pos['symbol']}: {pos['qty']} @ ${pos['current_price']:.2f} "
                      f"(P&L: ${pos['unrealized_pl']:,.2f})")
        
        print(f"\nTrades Executed:   {self.trade_count:>12}")
        print(f"Price Range:       ${min(self.price_history):.2f} - ${max(self.price_history):.2f}")
        print(f"\n" + "="*70 + "\n")

    def run_live_loop(self, num_bars: int = 50, interval_seconds: float = 0.5):
        """
        Run live trading loop.
        
        num_bars: Number of bars to simulate
        interval_seconds: Delay between bars
        """
        print("\n" + "="*70)
        print("  🚀 ALPACA LIVE PAPER TRADING")
        print("="*70)
        print(f"\nSymbol: {self.symbol}")
        print(f"Position Size: {self.position_size} shares")
        print(f"Running {num_bars} bars...\n")
        
        for i in range(num_bars):
            try:
                # Get next price
                price = self.get_current_price()
                
                # Execute trading cycle
                self.run_once(price)
                
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("⏹️  Stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in loop: {e}")
                continue
        
        self.print_summary()


if __name__ == "__main__":
    try:
        trader = AlpacaLiveTrader()
        trader.run_live_loop(num_bars=50, interval_seconds=0.5)
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
