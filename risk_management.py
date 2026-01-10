# risk_management.py
"""
Advanced Risk Management Module
- Position sizing based on volatility
- Portfolio risk limits
- Drawdown protection
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime

logging.basicConfig(
    filename='logs/risk_management.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class RiskManager:
    def __init__(self, initial_capital=100000, max_risk_percent=2.0, max_drawdown_percent=5.0):
        """
        Initialize risk manager
        - max_risk_percent: Max % of capital to risk per trade
        - max_drawdown_percent: Max % drawdown allowed
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.peak_capital = initial_capital
        self.max_risk_percent = max_risk_percent
        self.max_drawdown_percent = max_drawdown_percent
        self.open_positions = []
        self.trades_today = 0
        self.loss_streak = 0
        
    def calculate_position_size(self, entry_price, stop_loss_price, volatility=None):
        """
        Calculate position size based on:
        1. Risk capital (max_risk_percent of account)
        2. Entry and stop loss prices
        3. Volatility adjustment
        """
        try:
            # Risk amount in dollars
            risk_amount = self.current_capital * (self.max_risk_percent / 100)
            
            # Price difference (risk per share)
            price_difference = abs(entry_price - stop_loss_price)
            
            if price_difference == 0:
                logging.warning("Price difference is zero")
                return 0
            
            # Base position size
            position_size = int(risk_amount / price_difference)
            
            # Volatility adjustment (reduce size in high volatility)
            if volatility:
                if volatility > 0.03:  # High volatility
                    position_size = int(position_size * 0.7)
                elif volatility < 0.01:  # Low volatility
                    position_size = int(position_size * 1.1)
            
            # Minimum position check
            position_size = max(position_size, 10)  # At least 10 units
            
            logging.info(f"Position size: {position_size} units, Risk: ${risk_amount:.2f}")
            return position_size
            
        except Exception as e:
            logging.error(f"Error calculating position size: {str(e)}")
            return 0

    def should_trade(self, signal_strength=1.0):
        """
        Determine if trading should proceed based on:
        1. Current drawdown
        2. Loss streak
        3. Daily trade limit
        4. Signal strength
        """
        try:
            # Check current drawdown
            current_drawdown = ((self.peak_capital - self.current_capital) / self.peak_capital) * 100
            
            if current_drawdown > self.max_drawdown_percent:
                logging.warning(f"Max drawdown exceeded: {current_drawdown:.2f}%")
                return False, "Max drawdown exceeded"
            
            # Check loss streak (max 3 consecutive losses)
            if self.loss_streak >= 3:
                logging.warning(f"Loss streak: {self.loss_streak} trades")
                return False, "Loss streak limit reached"
            
            # Check daily trade limit (max 5 trades per day)
            if self.trades_today >= 5:
                logging.info(f"Daily trade limit reached: {self.trades_today}")
                return False, "Daily trade limit"
            
            # Adjust confidence based on signal strength
            if signal_strength < 0.5:
                logging.info("Signal strength too low")
                return False, "Weak signal"
            
            return True, "OK"
            
        except Exception as e:
            logging.error(f"Error in should_trade: {str(e)}")
            return False, str(e)

    def update_after_trade(self, pnl, is_winning_trade=True):
        """Update risk metrics after a trade"""
        try:
            self.current_capital += pnl
            self.trades_today += 1
            
            # Update peak capital
            if self.current_capital > self.peak_capital:
                self.peak_capital = self.current_capital
                self.loss_streak = 0
            
            # Update loss streak
            if is_winning_trade:
                self.loss_streak = 0
            else:
                self.loss_streak += 1
            
            logging.info(f"Trade updated: P&L ${pnl:.2f}, Capital: ${self.current_capital:.2f}, Loss Streak: {self.loss_streak}")
            
        except Exception as e:
            logging.error(f"Error updating after trade: {str(e)}")

    def get_risk_metrics(self):
        """Get current risk metrics"""
        try:
            drawdown = ((self.peak_capital - self.current_capital) / self.peak_capital) * 100
            return {
                'current_capital': self.current_capital,
                'peak_capital': self.peak_capital,
                'drawdown_percent': round(drawdown, 2),
                'loss_streak': self.loss_streak,
                'trades_today': self.trades_today,
                'can_trade': drawdown <= self.max_drawdown_percent and self.loss_streak < 3
            }
        except Exception as e:
            logging.error(f"Error getting risk metrics: {str(e)}")
            return {}

def main():
    print("\n" + "="*70)
    print("RISK MANAGEMENT SYSTEM TEST")
    print("="*70 + "\n")
    
    rm = RiskManager(initial_capital=100000, max_risk_percent=2.0, max_drawdown_percent=5.0)
    
    # Test position sizing
    position_size = rm.calculate_position_size(entry_price=410, stop_loss_price=405, volatility=0.015)
    print(f"[+] Calculated position size: {position_size} units")
    
    # Test trading conditions
    can_trade, reason = rm.should_trade(signal_strength=1.0)
    print(f"[+] Can trade: {can_trade} ({reason})")
    
    # Simulate trades
    rm.update_after_trade(pnl=500, is_winning_trade=True)
    rm.update_after_trade(pnl=-300, is_winning_trade=False)
    rm.update_after_trade(pnl=-250, is_winning_trade=False)
    
    # Get metrics
    metrics = rm.get_risk_metrics()
    print(f"\n[+] Risk Metrics:")
    for key, value in metrics.items():
        print(f"    {key}: {value}")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
