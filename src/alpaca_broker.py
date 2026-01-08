"""
Alpaca Broker Integration
Connects to Alpaca API for paper trading.
"""

import logging
from datetime import datetime
from typing import Dict, Optional, List
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce


logger = logging.getLogger(__name__)


class AlpacaBroker:
    """
    Alpaca paper trading broker.
    
    Usage:
        broker = AlpacaBroker(api_key, secret_key)
        broker.place_order("GLD", "buy", 1.0)
        broker.close_position("GLD", "Current price")
        account = broker.get_account()
    """

    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        """
        Initialize Alpaca trading client.
        
        api_key: Your Alpaca API Key
        secret_key: Your Alpaca Secret Key
        paper: True for paper trading, False for live
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper = paper
        
        try:
            self.client = TradingClient(
                api_key=api_key,
                secret_key=secret_key,
                paper=paper
            )
            logger.info(f"✅ Connected to Alpaca ({'Paper' if paper else 'Live'})")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Alpaca: {e}")
            raise

    # ------------------------------------------------------------------
    # Core Trading Methods
    # ------------------------------------------------------------------

    def place_order(
        self,
        symbol: str,
        side: str,
        qty: float,
        order_type: str = "market",
    ) -> Dict:
        """
        Place a market order on Alpaca.
        
        symbol: Stock symbol (e.g., "GLD", "AAPL")
        side: "buy" or "sell"
        qty: Quantity of shares
        order_type: "market" or "limit" (we use market for simplicity)
        
        Returns: Order details dict
        """
        try:
            side_enum = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
            
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=side_enum,
                time_in_force=TimeInForce.DAY
            )
            
            order = self.client.submit_order(order_data)
            
            logger.info(
                f"✅ Order placed: {side.upper()} {qty} {symbol} "
                f"@ {order.created_at} | Order ID: {order.id}"
            )
            
            return {
                "order_id": order.id,
                "symbol": order.symbol,
                "qty": order.qty,
                "side": order.side.value,
                "status": order.status,
                "created_at": order.created_at,
                "filled_qty": order.filled_qty,
                "filled_avg_price": order.filled_avg_price,
            }
        except Exception as e:
            logger.error(f"❌ Order placement failed: {e}")
            raise

    def close_position(self, symbol: str) -> Optional[Dict]:
        """
        Close all positions for a symbol.
        
        Returns: Closing order details or None if no position
        """
        try:
            position = self.client.get_open_position(symbol)
            
            if position is None:
                logger.warning(f"⚠️  No open position for {symbol}")
                return None
            
            # Close the position
            order = self.client.close_position(symbol)
            
            logger.info(f"✅ Position closed: {symbol} | Order ID: {order.id}")
            
            return {
                "order_id": order.id,
                "symbol": order.symbol,
                "qty": order.qty,
                "side": order.side.value,
                "status": order.status,
            }
        except Exception as e:
            logger.error(f"❌ Close position failed for {symbol}: {e}")
            return None

    # ------------------------------------------------------------------
    # Account Information
    # ------------------------------------------------------------------

    def get_account(self) -> Dict:
        """Get account details: cash, equity, buying power, etc."""
        try:
            account = self.client.get_account()
            return {
                "cash": float(account.cash),
                "equity": float(account.equity),
                "buying_power": float(account.buying_power),
                "portfolio_value": float(account.portfolio_value),
                "status": account.status,
            }
        except Exception as e:
            logger.error(f"❌ Failed to get account info: {e}")
            return {
                "cash": 0,
                "equity": 0,
                "buying_power": 0,
                "portfolio_value": 0,
                "status": "error",
            }

    def get_positions(self) -> List[Dict]:
        """Get all open positions."""
        try:
            positions = self.client.get_all_positions()
            result = []
            for pos in positions:
                result.append({
                    "symbol": pos.symbol,
                    "qty": float(pos.qty),
                    "side": pos.side.value,
                    "avg_fill_price": float(pos.avg_fill_price),
                    "current_price": float(pos.current_price) if pos.current_price else None,
                    "market_value": float(pos.market_value),
                    "unrealized_pl": float(pos.unrealized_pl),
                    "unrealized_plpc": float(pos.unrealized_plpc),
                })
            return result
        except Exception as e:
            logger.error(f"❌ Failed to get positions: {e}")
            return []

    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get a specific position. Returns None if no position exists."""
        try:
            pos = self.client.get_open_position(symbol)
            if pos is None:
                return None
            return {
                "symbol": pos.symbol,
                "qty": float(pos.qty),
                "side": pos.side.value,
                "avg_fill_price": float(pos.avg_fill_price),
                "current_price": float(pos.current_price) if pos.current_price else 0,
                "market_value": float(pos.market_value) if pos.market_value else 0,
                "unrealized_pl": float(pos.unrealized_pl) if pos.unrealized_pl else 0,
                "unrealized_plpc": float(pos.unrealized_plpc) if pos.unrealized_plpc else 0,
            }
        except Exception as e:
            # Position doesn't exist - this is normal before first trade
            return None

    def get_orders(self, status: str = "all") -> List[Dict]:
        """Get all orders. status: 'open', 'closed', 'all'"""
        try:
            orders = self.client.get_orders(status=status)
            result = []
            for order in orders:
                result.append({
                    "order_id": order.id,
                    "symbol": order.symbol,
                    "qty": order.qty,
                    "side": order.side.value,
                    "status": order.status,
                    "created_at": order.created_at,
                    "filled_qty": order.filled_qty,
                    "filled_avg_price": order.filled_avg_price,
                })
            return result
        except Exception as e:
            logger.error(f"❌ Failed to get orders: {e}")
            return []

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def summary(self) -> Dict:
        """Get account summary for printing."""
        account = self.get_account()
        positions = self.get_positions()
        
        total_pl = sum(p.get("unrealized_pl", 0) for p in positions)
        
        return {
            "cash": account.get("cash", 0),
            "equity": account.get("equity", 0),
            "portfolio_value": account.get("portfolio_value", 0),
            "buying_power": account.get("buying_power", 0),
            "open_positions": len(positions),
            "unrealized_pl": total_pl,
            "positions": positions,
        }