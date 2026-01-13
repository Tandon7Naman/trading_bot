"""
Paper Trading Engine - Simulates trades without real money
Phase 3 Integration Module
"""

import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class PaperTradingEngine:
	"""
	Paper trading simulator for backtesting trading strategies.
	Simulates trades without real money or broker API calls.
    
	Features:
	- Track paper positions and balance
	- Simulate order execution
	- Calculate P&L
	- Log all trades
	"""
    
	def __init__(self, initial_balance: float = 100000):
		"""
		Initialize paper trading engine.
        
		Args:
			initial_balance: Starting capital in ₹ (default: ₹100,000)
		"""
		self.initial_balance = initial_balance
		self.current_balance = initial_balance
		self.cash = initial_balance
		self.positions: Dict[str, Dict[str, Any]] = {}
		self.trades: List[Dict[str, Any]] = []
		self.equity = initial_balance
		self.max_equity = initial_balance
		self.drawdown = 0
        
		logger.info(f"PaperTradingEngine initialized with ₹{initial_balance:,}")
    
	def place_order(self, signal: Dict[str, Any]) -> Dict[str, Any]:
		"""
		Simulate placing an order (no real broker API call).
        
		Args:
			signal: Trading signal dict with keys:
				- 'entry': Entry price (₹)
				- 'position': Position size (lots)
				- 'side': 'BUY' or 'SELL' (default: 'BUY')
				- 'stop_loss': Stop loss price (₹)
				- 'take_profit': Take profit price (₹) [optional]
				- 'symbol': Symbol being traded (default: 'XAUUSD')
                
		Returns:
			dict: Order confirmation with execution details
		"""
        
		order_result = {
			"status": "SIMULATED_EXECUTED",
			"entry_price": signal.get("entry", 0),
			"position_size": signal.get("position", 1),
			"side": signal.get("side", "BUY"),
			"stop_loss": signal.get("stop_loss", 0),
			"take_profit": signal.get("take_profit", 0),
			"symbol": signal.get("symbol", "XAUUSD"),
			"timestamp": datetime.now().isoformat(),
			"order_id": len(self.trades) + 1,
		}
        
		# Record trade
		self.trades.append(order_result)
        
		logger.info(
			f"Paper trade #{order_result['order_id']}: "
			f"{order_result['side']} {order_result['position_size']} @ "
			f"₹{order_result['entry_price']:,.0f}"
		)
        
		return order_result
    
	def close_position(self, symbol: str, exit_price: float, entry_price: float = 0, position_size: int = 1) -> Dict[str, Any]:
		"""
		Simulate closing a position and calculate P&L.
        
		Args:
			symbol: Trading symbol (e.g., 'XAUUSD')
			exit_price: Exit price (₹)
			entry_price: Entry price (₹) for P&L calculation
			position_size: Position size (lots)
            
		Returns:
			dict: P&L information
		"""
        
		# Calculate P&L
		pnl = (exit_price - entry_price) * position_size if entry_price > 0 else 0
		pnl_percent = (pnl / (entry_price * position_size)) * 100 if entry_price > 0 else 0
        
		# Update balance
		self.current_balance += pnl
		self.cash += pnl
		self.equity = self.current_balance
        
		result = {
			"symbol": symbol,
			"exit_price": exit_price,
			"pnl": pnl,
			"pnl_percent": pnl_percent,
			"new_balance": self.current_balance,
			"status": "SIMULATED_CLOSED",
			"timestamp": datetime.now().isoformat(),
		}
        
		logger.info(f"Position closed: {symbol} @ ₹{exit_price:,.0f} | P&L: ₹{pnl:,.0f} ({pnl_percent:.2f}%)")
        
		return result
    
	def get_balance(self) -> float:
		"""Get current account balance (₹)."""
		return self.current_balance
    
	def get_equity(self) -> float:
		"""Get current equity (₹)."""
		return self.equity
    
	def update_balance(self, pnl: float):
		"""
		Update balance after trade P&L.
        
		Args:
			pnl: Profit/loss amount (₹)
		"""
		self.current_balance += pnl
		self.cash += pnl
		self.equity = self.current_balance
        
		# Track max equity and drawdown
		if self.equity > self.max_equity:
			self.max_equity = self.equity
        
		self.drawdown = ((self.max_equity - self.equity) / self.max_equity) * 100 if self.max_equity > 0 else 0
        
		logger.info(f"Balance updated: ₹{self.current_balance:,} | Drawdown: {self.drawdown:.2f}%")
    
	def get_trades(self) -> List[Dict[str, Any]]:
		"""Get all executed trades."""
		return self.trades
    
	def get_trade_count(self) -> int:
		"""Get total number of trades executed."""
		return len(self.trades)
    
	def get_positions(self) -> Dict[str, Dict[str, Any]]:
		"""Get all open positions."""
		return self.positions
    
	def reset(self):
		"""Reset paper trading engine to initial state."""
		self.current_balance = self.initial_balance
		self.cash = self.initial_balance
		self.positions = {}
		self.trades = []
		self.equity = self.initial_balance
		self.max_equity = self.initial_balance
		self.drawdown = 0
        
		logger.info("Paper trading engine reset")
    
	def get_summary(self) -> Dict[str, Any]:
		"""
		Get summary statistics.
        
		Returns:
			dict: Summary with balance, trades, P&L, etc.
		"""
		total_pnl = self.current_balance - self.initial_balance
		total_pnl_percent = (total_pnl / self.initial_balance) * 100
        
		return {
			"initial_balance": self.initial_balance,
			"current_balance": self.current_balance,
			"total_pnl": total_pnl,
			"total_pnl_percent": total_pnl_percent,
			"total_trades": len(self.trades),
			"equity": self.equity,
			"max_equity": self.max_equity,
			"drawdown_percent": self.drawdown,
		}
    
	def get_cash(self) -> float:
		"""Get available cash."""
		return self.cash
