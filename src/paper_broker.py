"""
Local paper trading engine (no real broker).

Tracks:
- cash
- positions
- open trades
- closed trades
- P&L
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, List


@dataclass
class PaperPosition:
    symbol: str
    side: str            # "LONG" or "SHORT"
    quantity: float
    entry_price: float
    entry_time: datetime


@dataclass
class PaperTrade:
    symbol: str
    side: str            # "BUY" or "SELL"
    quantity: float
    entry_price: float
    exit_price: Optional[float]
    entry_time: datetime
    exit_time: Optional[datetime]
    pnl: Optional[float]
    reason: str


class PaperBroker:
    """
    Simple in‑memory paper broker.

    Usage:
        broker = PaperBroker(initial_cash=500000)
        broker.submit_market_order("MCX:GOLDPETAL", "BUY", 1, price=68600)
        broker.close_position("MCX:GOLDPETAL", price=68700, reason="Take Profit")
    """

    def __init__(self, initial_cash: float = 500000.0) -> None:
        self.initial_cash: float = float(initial_cash)
        self.cash: float = float(initial_cash)
        self.positions: Dict[str, PaperPosition] = {}
        self.trades: List[PaperTrade] = []

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def submit_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Execute a market order at the given price.

        side: "BUY" or "SELL"
        quantity: contracts / lots (float for flexibility)
        """

        ts = timestamp or datetime.now()
        side = side.upper()

        if side not in ("BUY", "SELL"):
            raise ValueError(f"Invalid side: {side}")

        notional = quantity * price

        if side == "BUY":
            # Reduce cash, create/flip position to LONG
            self.cash -= notional
            self._open_or_flip_position(symbol, "LONG", quantity, price, ts)
        else:
            # SELL side:
            # If no position -> open SHORT
            # If LONG position -> reduce/flip
            # For paper trading we allow opening SHORT even without borrow.
            self.cash += notional
            self._open_or_flip_position(symbol, "SHORT", quantity, price, ts)

    def close_position(
        self,
        symbol: str,
        price: float,
        reason: str,
        timestamp: Optional[datetime] = None,
    ) -> Optional[PaperTrade]:
        """
        Close existing position at price. Returns the created PaperTrade or None if no position.
        """
        ts = timestamp or datetime.now()
        pos = self.positions.get(symbol)

        if pos is None:
            return None

        # Calculate PnL
        if pos.side == "LONG":
            pnl = (price - pos.entry_price) * pos.quantity
            # We receive cash when selling our LONG position
            self.cash += pos.quantity * price
            exit_side = "SELL"
        else:  # SHORT
            pnl = (pos.entry_price - price) * pos.quantity
            # We pay to buy back our SHORT position
            self.cash -= pos.quantity * price
            exit_side = "BUY"

        trade = PaperTrade(
            symbol=symbol,
            side=exit_side,
            quantity=pos.quantity,
            entry_price=pos.entry_price,
            exit_price=price,
            entry_time=pos.entry_time,
            exit_time=ts,
            pnl=pnl,
            reason=reason,
        )
        self.trades.append(trade)

        # Remove position
        del self.positions[symbol]

        return trade

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _open_or_flip_position(
        self,
        symbol: str,
        new_side: str,
        quantity: float,
        price: float,
        timestamp: datetime,
    ) -> None:
        """
        If no position: open position with given side.
        If opposite position exists: close old one, then open new.
        If same side exists: average price & increase quantity (simple model).
        """
        existing = self.positions.get(symbol)

        if existing is None:
            # Open fresh position
            self.positions[symbol] = PaperPosition(
                symbol=symbol,
                side=new_side,
                quantity=quantity,
                entry_price=price,
                entry_time=timestamp,
            )
            return

        # If same side, simple average in
        if existing.side == new_side:
            total_qty = existing.quantity + quantity
            if total_qty <= 0:
                # Should not happen for same side, but guard anyway
                self.positions[symbol] = PaperPosition(
                    symbol=symbol,
                    side=new_side,
                    quantity=quantity,
                    entry_price=price,
                    entry_time=timestamp,
                )
            else:
                new_entry_price = (
                    existing.entry_price * existing.quantity + price * quantity
                ) / total_qty
                existing.quantity = total_qty
                existing.entry_price = new_entry_price
                # keep original entry_time
            return

        # If opposite side -> close existing, then open new side fresh
        # Close existing at this price
        close_reason = f"Flip {existing.side} -> {new_side}"
        self.close_position(symbol, price=price, reason=close_reason, timestamp=timestamp)

        # Open new side
        self.positions[symbol] = PaperPosition(
            symbol=symbol,
            side=new_side,
            quantity=quantity,
            entry_price=price,
            entry_time=timestamp,
        )

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def get_equity(self, mark_prices: Optional[Dict[str, float]] = None) -> float:
        """
        Equity = cash + sum of unrealized P&L for all open positions.
        mark_prices: optional dict {symbol: last_price} for mark‑to‑market.
        """
        equity = self.cash

        if mark_prices:
            for symbol, pos in self.positions.items():
                last_price = mark_prices.get(symbol)
                if last_price is None:
                    continue
                if pos.side == "LONG":
                    equity += (last_price - pos.entry_price) * pos.quantity
                else:
                    equity += (pos.entry_price - last_price) * pos.quantity

        return equity

    def get_realized_pnl(self) -> float:
        return sum(t.pnl for t in self.trades if t.pnl is not None)

    def summary(self, mark_prices: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """
        Return a simple summary dict of account status.
        """
        return {
            "initial_cash": self.initial_cash,
            "cash": self.cash,
            "equity": self.get_equity(mark_prices),
            "realized_pnl": self.get_realized_pnl(),
            "open_positions": len(self.positions),
            "closed_trades": len(self.trades),
        }
