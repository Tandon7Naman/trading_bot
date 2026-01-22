# paper_trading.py
import json
import logging
import os
from datetime import datetime

logging.basicConfig(
    filename="logs/paper_trading.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class PaperTradingEngine:
    """
    Simulates live trading with real API data
    Supports: Alpaca, Zerodha, Flattrade
    """

    def __init__(self, api_choice="alpaca", initial_capital=100000):
        """Initialize paper trading engine"""
        self.api_choice = api_choice
        self.initial_capital = initial_capital
        self.current_balance = initial_capital
        self.open_positions = {}
        self.closed_trades = []
        self.trade_history_file = "data/paper_trades.json"

        logging.info(f"Initialized PaperTradingEngine with {api_choice} API")

    def connect_alpaca_api(self, api_key, secret_key):
        """Connect to Alpaca API for paper trading"""
        try:
            import alpaca_trade_api as tradeapi

            self.api = tradeapi.REST(api_key, secret_key, "https://paper-api.alpaca.markets")

            account = self.api.get_account()
            logging.info(f"Connected to Alpaca. Account: {account.account_number}")
            return True

        except Exception as e:
            logging.error(f"Failed to connect to Alpaca: {str(e)}")
            return False

    def connect_zerodha_api(self, api_key, access_token):
        """Connect to Zerodha Kite API for paper trading"""
        try:
            from kiteconnect import KiteConnect

            self.kite = KiteConnect(api_key=api_key)
            self.kite.set_access_token(access_token)

            profile = self.kite.profile()
            logging.info(f"Connected to Zerodha. User: {profile['user_name']}")
            return True

        except Exception as e:
            logging.error(f"Failed to connect to Zerodha: {str(e)}")
            return False

    def get_live_price(self, symbol):
        """Fetch live price for symbol"""
        try:
            if self.api_choice == "alpaca":
                quote = self.api.get_latest_quote(symbol)
                return quote.bid, quote.ask, quote.last_updated

            elif self.api_choice == "zerodha":
                data = self.kite.quote([symbol])
                price = data[symbol]["last_price"]
                return price, price, datetime.now()

        except Exception as e:
            logging.error(f"Error fetching live price for {symbol}: {str(e)}")
            return None, None, None

    def place_buy_order(self, symbol, quantity, price, trade_id):
        """Place BUY order"""
        try:
            if symbol in self.open_positions:
                logging.warning(f"Position already exists for {symbol}")
                return False

            self.open_positions[symbol] = {
                "trade_id": trade_id,
                "side": "BUY",
                "symbol": symbol,
                "quantity": quantity,
                "entry_price": price,
                "entry_time": datetime.now(),
                "status": "OPEN",
            }

            self.current_balance -= price * quantity

            logging.info(f"BUY order placed: {symbol} x{quantity} @ {price}")
            return True

        except Exception as e:
            logging.error(f"Error placing BUY order: {str(e)}")
            return False

    def place_sell_order(self, symbol, quantity, price, trade_id):
        """Place SELL order"""
        try:
            if symbol not in self.open_positions:
                logging.warning(f"No position exists for {symbol}")
                return False

            position = self.open_positions[symbol]
            pnl = (price - position["entry_price"]) * quantity
            pnl_percent = ((price - position["entry_price"]) / position["entry_price"]) * 100

            self.closed_trades.append(
                {
                    "trade_id": trade_id,
                    "symbol": symbol,
                    "entry_price": position["entry_price"],
                    "exit_price": price,
                    "quantity": quantity,
                    "entry_time": position["entry_time"],
                    "exit_time": datetime.now(),
                    "pnl": pnl,
                    "pnl_percent": pnl_percent,
                }
            )

            self.current_balance += price * quantity
            del self.open_positions[symbol]

            logging.info(f"SELL order placed: {symbol} x{quantity} @ {price}, P&L: {pnl}")
            return True

        except Exception as e:
            logging.error(f"Error placing SELL order: {str(e)}")
            return False

    def get_open_positions(self):
        """Get all open positions"""
        return self.open_positions

    def get_position_pnl(self, symbol, current_price):
        """Calculate P&L for open position"""
        try:
            if symbol not in self.open_positions:
                return None

            position = self.open_positions[symbol]
            pnl = (current_price - position["entry_price"]) * position["quantity"]
            pnl_percent = (
                (current_price - position["entry_price"]) / position["entry_price"]
            ) * 100

            return {
                "symbol": symbol,
                "entry_price": position["entry_price"],
                "current_price": current_price,
                "pnl": pnl,
                "pnl_percent": pnl_percent,
            }

        except Exception as e:
            logging.error(f"Error calculating P&L: {str(e)}")
            return None

    def get_account_summary(self):
        """Get paper trading account summary"""
        try:
            total_pnl = sum([trade["pnl"] for trade in self.closed_trades])
            winning_trades = len([t for t in self.closed_trades if t["pnl"] > 0])
            losing_trades = len([t for t in self.closed_trades if t["pnl"] < 0])

            summary = {
                "initial_capital": self.initial_capital,
                "current_balance": round(self.current_balance, 2),
                "total_realized_pnl": round(total_pnl, 2),
                "total_trades": len(self.closed_trades),
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": round(
                    (winning_trades / len(self.closed_trades) * 100) if self.closed_trades else 0, 2
                ),
                "open_positions": len(self.open_positions),
                "timestamp": datetime.now().isoformat(),
            }

            logging.info(f"Account Summary: {summary}")
            return summary

        except Exception as e:
            logging.error(f"Error getting account summary: {str(e)}")
            return {}

    def save_trades(self):
        """Save closed trades to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.trade_history_file), exist_ok=True)

            # Convert datetime objects to strings
            trades_to_save = []
            for trade in self.closed_trades:
                trade_copy = trade.copy()
                trade_copy["entry_time"] = trade_copy["entry_time"].isoformat()
                trade_copy["exit_time"] = trade_copy["exit_time"].isoformat()
                trades_to_save.append(trade_copy)

            with open(self.trade_history_file, "w") as f:
                json.dump(trades_to_save, f, indent=2)

            logging.info(f"Saved {len(trades_to_save)} trades to {self.trade_history_file}")
            return True

        except Exception as e:
            logging.error(f"Error saving trades: {str(e)}")
            return False


def main():
    """Example usage of paper trading engine"""
    print("[*] Starting Paper Trading Engine...")

    # Initialize engine
    engine = PaperTradingEngine(api_choice="alpaca", initial_capital=100000)

    # Note: For actual usage, connect to your API
    # engine.connect_alpaca_api('YOUR_API_KEY', 'YOUR_SECRET_KEY')

    # Example: Place orders
    # engine.place_buy_order('GLD', 100, 185.50, 'TRADE_001')
    # engine.place_sell_order('GLD', 100, 186.00, 'TRADE_001')

    # Get account summary
    summary = engine.get_account_summary()
    print("\n[+] Account Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
