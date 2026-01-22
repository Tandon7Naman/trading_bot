import json
from datetime import datetime


class PaperTradingEngine:
    def __init__(self, initial_capital=100000):
        self.capital = initial_capital
        self.initial_capital = initial_capital
        self.positions = []
        self.trades_history = []
        self.current_position = None

    def can_buy(self, price, quantity=10):
        """Check if enough capital to buy"""
        required = price * quantity
        return self.capital >= required

    def buy(self, price, quantity=10, timestamp=None):
        """Execute buy order"""
        if not self.can_buy(price, quantity):
            return {"status": "failed", "reason": "Insufficient capital"}

        cost = price * quantity
        self.capital -= cost

        self.current_position = {
            "type": "LONG",
            "entry_price": price,
            "quantity": quantity,
            "entry_time": timestamp or datetime.now(),
            "cost": cost,
        }

        self.trades_history.append(
            {
                "action": "BUY",
                "price": price,
                "quantity": quantity,
                "timestamp": timestamp or datetime.now(),
                "capital_remaining": self.capital,
            }
        )

        print(f"✅ BUY: {quantity}g @ ₹{price:.2f} | Capital: ₹{self.capital:.2f}")
        return {"status": "success", "position": self.current_position}

    def sell(self, price, timestamp=None):
        """Execute sell order"""
        if not self.current_position:
            return {"status": "failed", "reason": "No position to sell"}

        quantity = self.current_position["quantity"]
        proceeds = price * quantity
        self.capital += proceeds

        # Calculate P&L
        pnl = proceeds - self.current_position["cost"]
        pnl_percent = (pnl / self.current_position["cost"]) * 100

        self.trades_history.append(
            {
                "action": "SELL",
                "price": price,
                "quantity": quantity,
                "timestamp": timestamp or datetime.now(),
                "pnl": pnl,
                "pnl_percent": pnl_percent,
                "capital_remaining": self.capital,
            }
        )

        print(
            f"✅ SELL: {quantity}g @ ₹{price:.2f} | P&L: ₹{pnl:.2f} ({pnl_percent:.2f}%) | Capital: ₹{self.capital:.2f}"
        )

        self.current_position = None
        return {"status": "success", "pnl": pnl}

    def get_portfolio_value(self, current_price):
        """Calculate total portfolio value"""
        portfolio_value = self.capital
        if self.current_position:
            portfolio_value += current_price * self.current_position["quantity"]
        return portfolio_value

    def get_performance(self):
        """Get trading performance metrics"""
        total_return = self.capital - self.initial_capital
        return_percent = (total_return / self.initial_capital) * 100

        winning_trades = [t for t in self.trades_history if t.get("pnl", 0) > 0]
        total_trades = len([t for t in self.trades_history if "pnl" in t])

        return {
            "initial_capital": self.initial_capital,
            "current_capital": self.capital,
            "total_return": total_return,
            "return_percent": return_percent,
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "win_rate": len(winning_trades) / total_trades * 100 if total_trades > 0 else 0,
        }

    def save_history(self, filepath="trading_history.json"):
        """Save trading history"""
        with open(filepath, "w") as f:
            json.dump(self.trades_history, f, indent=4, default=str)
