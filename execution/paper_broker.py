import random
import time
import numpy as np
from datetime import datetime
from execution.base_broker import BrokerInterface
from execution.db_manager import DBManager  # <--- NEW: SQLite Manager
from utils.notifier import TelegramNotifier
from utils.time_utils import to_display_time, get_utc_now
from execution.journal_manager import JournalManager
from config.settings import ASSET_CONFIG 

class PaperBroker(BrokerInterface):
    """
    Protocol 9.2: SQLite-Backed Paper Broker.
    Replaces JSON state with ACID-compliant Database transactions.
    """
    def __init__(self, initial_capital=500000.0, state_file=None):
        # 1. Initialize DB
        self.db = DBManager()
        
        # 2. Sync Equity if fresh start
        account = self.db.get_account()
        self.equity = account['equity']
        
        # 3. Physics (From Config)
        config = ASSET_CONFIG.get("XAUUSD", {})
        self.leverage = config.get('leverage', 100.0) 
        self.contract_size = config.get('contract_size', 100)
        self.spread = config.get('spread', 0.20) 
        self.commission_per_lot = 7.00 
        self.swap_per_lot_nightly = -5.00 

    def _calculate_execution_price(self, price, action, atr=0.0):
        # (Same logic as Protocol 5.2 - Slippage/Spread)
        volatility_penalty = atr * random.uniform(0.01, 0.05) if atr > 0 else random.uniform(0.01, 0.15)
        latency_drift = random.uniform(-0.02, 0.05) if action == 1 else random.uniform(-0.05, 0.02)
        if latency_drift < 0: latency_drift = 0
        
        total_slippage = volatility_penalty + latency_drift
        final_price = price
        
        if action == 1: # BUY
            final_price = price + self.spread + total_slippage
            print(f"      📉 EXECUTION: Spread ${self.spread:.2f} + Slip ${total_slippage:.2f}")
        elif action == 2: # SELL
            final_price = price - total_slippage
            print(f"      📉 EXECUTION: Slip ${total_slippage:.2f}")

        return round(final_price, 2)

    def check_margin(self, price, qty):
        notional_value = price * self.contract_size * qty
        required_margin = notional_value / self.leverage
        # Read latest equity from DB
        current_equity = self.db.get_account()['equity']
        if current_equity < required_margin:
            return False, required_margin
        return True, required_margin

    # --- INTERFACE IMPLEMENTATION ---
    
    def connect(self):
        print("✅ Paper Broker: Connected to SQLite Database.")
        return True

    def get_tick(self, symbol):
        return 0.0 

    def get_positions(self):
        # Read Live State from DB
        account = self.db.get_account()
        pos = self.db.get_open_position("XAUUSD") # Currently supporting single asset logic
        orders = self.db.get_orders("XAUUSD")
        
        return {
            "equity": account['equity'],
            "position": pos,
            "orders": orders
        }

    def place_order(self, action, symbol, price, qty, **kwargs):
        """
        Protocol 2.3: OCO / Bracket Order Execution.
        Enforces MANDATORY Stop Losses. Rejects any 'Naked' positions.
        """
        # Latency Sim
        lag = random.uniform(0.1, 0.5)
        time.sleep(lag)
        
        order_type = kwargs.get('type', 'MARKET')
        date_utc = kwargs.get('date', 'Unknown')
        sl = kwargs.get('sl', 0.0)
        tp = kwargs.get('tp', 0.0)
        atr = kwargs.get('atr', 0.0)

        # --- PROTOCOL 2.3: MANDATORY STOP LOSS CHECK ---
        if action == 1: # BUY
            if sl <= 0:
                print(f"❌ REJECTED: Protocol 2.3 Violation. Naked Order (No SL) on {symbol}.")
                return False
            
            if sl >= price:
                print(f"❌ REJECTED: Invalid Logic. SL ({sl}) must be below Entry ({price}).")
                return False

        # 1. HANDLE LIMIT ORDERS
        if order_type == 'LIMIT':
            print(f"📝 ORDER PLACED: {symbol} {qty}x LIMIT @ {price} | SL: {sl} | TP: {tp}")
            self.db.add_order({
                "symbol": symbol, "action": action, "limit_price": price, 
                "qty": qty, "sl": sl, "tp": tp, "type": "LIMIT", 
                "date": str(date_utc)
            })
            return True

        # 2. HANDLE MARKET ORDERS (BRACKET)
        filled_price = self._calculate_execution_price(price, action, atr)
        current_pos = self.db.get_open_position(symbol)

        if action == 1: # BUY
            if current_pos == "FLAT":
                has_margin, req_margin = self.check_margin(filled_price, qty)
                if not has_margin: return False

                print(f"🚀 BROKER: BUY FILLED @ {filled_price} | 🛑 SL: {sl} | 🎯 TP: {tp}")
                
                # DB: Add Trade WITH ATTACHED STOPS (Simulating Server-Side OCO)
                self.db.add_trade(
                    ticket=random.randint(10000, 99999), 
                    symbol=symbol, direction="LONG", size=qty, 
                    price=filled_price, sl=sl, tp=tp
                )
                
                import asyncio
                asyncio.run(TelegramNotifier.send_message(f"🚀 *OPEN LONG*\nPrice: ${filled_price}\nSize: {qty}\nSL: {sl}"))
                return True

        elif action == 2: # SELL (Close)
            if current_pos != "FLAT":
                # Close Logic
                entry_price = current_pos['entry_price']
                size = current_pos['qty']
                
                gross_pnl = (filled_price - entry_price) * self.contract_size * size
                net_pnl = gross_pnl - (self.commission_per_lot * size)
                
                print(f"🔻 BROKER: SELL FILLED @ {filled_price} | PnL: ${net_pnl:.2f}")
                
                # DB: Close Trade
                self.db.close_trade(symbol, filled_price, net_pnl)
                
                # --- PROTOCOL 5.2: AUTOMATED JOURNALING ---
                # Retrieve trade details from DB to get entry time/price
                # For now, mock details; in production, fetch from DB
                journal_entry = {
                    "ticket": random.randint(1000,9999), # Mock ticket
                    "symbol": symbol,
                    "direction": "LONG",
                    "size": size,
                    "entry_price": entry_price,
                    "exit_price": filled_price,
                    "pnl": net_pnl,
                    "strategy": "Wyckoff_Spring", # Can be passed dynamically
                    "regime": "TRENDING", # Passed dynamically in real implementation
                    "sentiment": "NEUTRAL",
                    "entry_time": "2026-01-21 10:00",
                    "exit_time": get_utc_now()
                }
                JournalManager.log_trade(journal_entry)
                # ------------------------------------------
                new_equity = self.db.get_account()['equity'] + net_pnl
                self.db.update_equity(new_equity)
                
                icon = "✅" if net_pnl > 0 else "❌"
                import asyncio
                asyncio.run(TelegramNotifier.send_message(f"{icon} *CLOSE LONG*\nPrice: ${filled_price}\nPnL: ${net_pnl:.2f}"))
                return True
                
        return False

    def check_limits(self, current_price, symbol):
        # Protocol 9.2: Limits checked against DB state
        pos = self.db.get_open_position(symbol)
        
        if pos != "FLAT":
            sl = pos['sl']
            tp = pos['tp']
            
            triggered = False
            reason = ""
            fill_price = 0.0
            
            if sl > 0 and current_price <= sl:
                triggered = True
                reason = "SL HIT"
                fill_price = sl
            elif tp > 0 and current_price >= tp:
                triggered = True
                reason = "TP HIT"
                fill_price = tp
                
            if triggered:
                print(f"⚡ EXIT TRIGGERED: {reason}")
                self.place_order(2, symbol, fill_price, pos['qty'], type="MARKET", date=get_utc_now())

        # Check Pending Orders
        orders = self.db.get_orders(symbol)
        for order in orders:
            if order['action'] == 1 and current_price <= order['limit_price']:
                # Limit Buy Triggered
                self.db.remove_order(order['order_id']) # Remove from Pending
                self.place_order(1, symbol, order['limit_price'], order['qty'], 
                                 type="MARKET", sl=order['sl'], tp=order['tp'], date=get_utc_now())