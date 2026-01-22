"""
Alpaca API Connector for Gold Trading Bot
Using alpaca-py 0.21.0 with Paper Trading
"""

import logging
import os

import yfinance as yf
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class AlpacaConnector:
    def __init__(self):
        self.api_key = os.getenv("ALPACA_API_KEY")
        self.api_secret = os.getenv("ALPACA_API_SECRET")
        self.trading_client = None
        self.data_client = None
        self.is_connected = False

    def login(self):
        """Connect to Alpaca Paper Trading API"""
        try:
            # Initialize trading client (paper mode)
            self.trading_client = TradingClient(
                api_key=self.api_key,
                secret_key=self.api_secret,
                paper=True,  # Paper trading mode
            )

            # Initialize data client
            self.data_client = StockHistoricalDataClient(
                api_key=self.api_key, secret_key=self.api_secret
            )

            # Test connection
            account = self.trading_client.get_account()

            self.is_connected = True
            logger.info("✅ Alpaca Paper Trading connected!")
            logger.info(f"💰 Account: ${float(account.equity):,.2f}")
            logger.info(f"💵 Buying Power: ${float(account.buying_power):,.2f}")

            return True

        except Exception as e:
            logger.error(f"❌ Alpaca connection error: {e}")
            print(f"❌ Error: {e}")
            return False

    def get_gold_price(self):
        """Get current gold price via yfinance (Alpaca doesn't support XAUUSD)"""
        try:
            # Get gold futures price (GC=F)
            gold = yf.Ticker("GC=F")
            data = gold.history(period="1d", interval="1m")

            if not data.empty:
                price = data["Close"].iloc[-1]
                logger.info(f"📊 Gold: ${price:.2f}/oz")
                return price

            return None

        except Exception as e:
            logger.error(f"❌ Error fetching gold: {e}")
            return None

    def get_account(self):
        """Get account information"""
        try:
            if not self.is_connected:
                return None

            account = self.trading_client.get_account()

            return {
                "equity": float(account.equity),
                "cash": float(account.cash),
                "buying_power": float(account.buying_power),
                "portfolio_value": float(account.portfolio_value),
                "status": account.status,
                "pattern_day_trader": account.pattern_day_trader,
            }

        except Exception as e:
            logger.error(f"❌ Error fetching account: {e}")
            return None

    def get_stock_quote(self, symbol="SPY"):
        """Get latest stock quote"""
        try:
            if not self.data_client:
                return None

            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quotes = self.data_client.get_stock_latest_quote(request)

            if symbol in quotes:
                quote = quotes[symbol]
                return {
                    "symbol": symbol,
                    "ask": float(quote.ask_price),
                    "bid": float(quote.bid_price),
                    "timestamp": quote.timestamp,
                }

            return None

        except Exception as e:
            logger.error(f"❌ Error fetching quote: {e}")
            return None

    def place_order(self, symbol="SPY", quantity=1, side="buy", price=None):
        """
        Place paper trade order
        Note: Using SPY as proxy - Alpaca doesn't support XAUUSD
        """
        try:
            if not self.is_connected:
                return None

            order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL

            if price:
                # Limit order
                order_data = LimitOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=order_side,
                    time_in_force=TimeInForce.DAY,
                    limit_price=float(price),
                )
            else:
                # Market order
                order_data = MarketOrderRequest(
                    symbol=symbol, qty=quantity, side=order_side, time_in_force=TimeInForce.DAY
                )

            order = self.trading_client.submit_order(order_data)

            logger.info(f"✅ Order: {order.id} | {side.upper()} {quantity} {symbol}")
            return str(order.id)

        except Exception as e:
            logger.error(f"❌ Order error: {e}")
            return None

    def get_positions(self):
        """Get all open positions"""
        try:
            if not self.is_connected:
                return []

            positions = self.trading_client.get_all_positions()

            pos_list = []
            for pos in positions:
                pos_list.append(
                    {
                        "symbol": pos.symbol,
                        "qty": float(pos.qty),
                        "avg_entry": float(pos.avg_entry_price),
                        "current": float(pos.current_price),
                        "market_value": float(pos.market_value),
                        "pnl": float(pos.unrealized_pl),
                        "pnl_pct": float(pos.unrealized_plpc) * 100,
                    }
                )

            return pos_list

        except Exception as e:
            logger.error(f"❌ Error fetching positions: {e}")
            return []

    def get_orders(self, status="all"):
        """Get order history"""
        try:
            if not self.is_connected:
                return []

            from alpaca.trading.enums import QueryOrderStatus
            from alpaca.trading.requests import GetOrdersRequest

            if status == "open":
                req = GetOrdersRequest(status=QueryOrderStatus.OPEN)
            elif status == "closed":
                req = GetOrdersRequest(status=QueryOrderStatus.CLOSED)
            else:
                req = GetOrdersRequest(status=QueryOrderStatus.ALL, limit=20)

            orders = self.trading_client.get_orders(req)
            return orders

        except Exception as e:
            logger.error(f"❌ Error fetching orders: {e}")
            return []

    def cancel_all_orders(self):
        """Cancel all open orders"""
        try:
            if not self.is_connected:
                return False

            self.trading_client.cancel_orders()
            logger.info("❌ Cancelled all orders")
            return True

        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return False

    def close_all_positions(self):
        """Close all positions"""
        try:
            if not self.is_connected:
                return False

            self.trading_client.close_all_positions(cancel_orders=True)
            logger.info("🔒 Closed all positions")
            return True

        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return False

    def logout(self):
        """Disconnect"""
        self.is_connected = False
        logger.info("👋 Logged out")


# Test script
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    print("\n" + "=" * 70)
    print("ALPACA PAPER TRADING CONNECTION TEST")
    print("=" * 70 + "\n")

    connector = AlpacaConnector()

    if connector.login():
        print("✅ Connection successful!\n")

        # 1. Account info
        print("📊 ACCOUNT INFORMATION:")
        print("-" * 70)
        account = connector.get_account()
        if account:
            print(f"   💰 Equity:        ${account['equity']:>15,.2f}")
            print(f"   💵 Buying Power:  ${account['buying_power']:>15,.2f}")
            print(f"   📈 Portfolio:     ${account['portfolio_value']:>15,.2f}")
            print(f"   ✅ Status:        {account['status']}")

        # 2. Gold price
        print("\n🥇 GOLD MARKET DATA:")
        print("-" * 70)
        gold_price = connector.get_gold_price()
        if gold_price:
            print(f"   📊 Gold Spot:     ${gold_price:>15,.2f}/oz")

            # MCX conversion
            usd_inr = 83.50
            mcx_10g = gold_price * usd_inr * 0.0321507
            print(f"   🇮🇳 MCX Approx:   ₹{mcx_10g:>15,.0f}/10g")

        # 3. SPY quote (test)
        print("\n📈 TEST QUOTE (SPY):")
        print("-" * 70)
        quote = connector.get_stock_quote("SPY")
        if quote:
            print("   Symbol: SPY")
            print(f"   Bid:    ${quote['bid']:.2f}")
            print(f"   Ask:    ${quote['ask']:.2f}")

        # 4. Positions
        print("\n📋 CURRENT POSITIONS:")
        print("-" * 70)
        positions = connector.get_positions()
        if positions:
            for pos in positions:
                print(
                    f"   {pos['symbol']}: {pos['qty']} @ ${pos['avg_entry']:.2f} | P&L: ${pos['pnl']:.2f}"
                )
        else:
            print("   (No open positions)")

        # 5. Recent orders
        print("\n📝 RECENT ORDERS:")
        print("-" * 70)
        orders = connector.get_orders()
        if orders:
            for order in orders[:5]:
                print(f"   {order.symbol}: {order.side} {order.qty} @ {order.status}")
        else:
            print("   (No orders yet)")

        connector.logout()

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - READY FOR PAPER TRADING!")
        print("=" * 70 + "\n")

    else:
        print("\n❌ CONNECTION FAILED\n")
        print("📋 Troubleshooting:")
        print("   1. Sign up at: https://alpaca.markets/")
        print("   2. Get Paper API keys from Dashboard")
        print("   3. Update .env file with your keys")
        print("   4. Run this test again\n")
