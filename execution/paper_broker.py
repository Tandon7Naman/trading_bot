import json
import os
import random
import numpy as np
from datetime import datetime
from execution.base_broker import GenericBroker
from utils.time_utils import to_display_time, get_utc_now

# --- TELEGRAM ALERTS ---
try:
    from execution.telegram_alerts import send_telegram_message
except ImportError:
    send_telegram_message = lambda x: None

class PaperBroker(GenericBroker):
    def __init__(self, state_file='data/paper_state_mcx.json', initial_capital=500000.0):
        self.state_file = state_file
        self.initial_capital = initial_capital
        
        # Physics
        self.leverage = 100.0
        self.contract_size = 100
        self.commission_per_lot = 7.00 
        self.swap_per_lot_nightly = -5.00 
        
        self.state = self._load_state()

    # --- HELPER METHODS ---
    def _convert(self, o):
        if isinstance(o, np.int64): return int(o)
        if isinstance(o, np.float32): return float(o)
        if isinstance(o, datetime): return o.isoformat()
        return o

    def _load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    if 'history' not in state: state['history'] = []
                    # Protocol 6.2: Add Pending Orders storage
                    if 'pending_orders' not in state: state['pending_orders'] = []
                    return state
            except Exception:
                pass
        return {
            "equity": self.initial_capital, 
            "position": "FLAT", 
            "history": [], 
            "pending_orders": []
        }

    def _save_state(self):
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=4, default=self._convert)
        except Exception as e:
            print(f"❌ Error saving state: {e}")

    def _apply_friction(self, price, action, symbol):
        spread = 0.20 if 'GC=F' in symbol or 'XAU' in symbol else 0.05
        slippage = random.uniform(0.01, 0.15)
        friction = (spread / 2) + slippage
        if action == 1: return round(price + friction, 2)
        elif action == 2: return round(price - friction, 2)
        return price

    def check_margin(self, price, qty):
        notional_value = price * self.contract_size * qty
        required_margin = notional_value / self.leverage
        free_equity = self.state['equity']
        if free_equity < required_margin:
            return False, required_margin
        return True, required_margin

    def calculate_swap(self, entry_time_str, qty):
        try:
            entry_dt = datetime.fromisoformat(entry_time_str)
            now_dt = get_utc_now()
            nights = (now_dt - entry_dt).days
            if nights < 0: nights = 0
            return nights * self.swap_per_lot_nightly * qty
        except:
            return 0.0

    # --- PROTOCOL 6.2: LIMIT ORDER PROCESSING ---
    def check_limits(self, current_price, symbol):
        """
        Checks if any pending LIMIT orders should be filled at the current price.
        """
        pending = self.state.get('pending_orders', [])
        if not pending:
            return

        # List to keep orders that are NOT filled yet
        remaining_orders = []
        
        for order in pending:
            # Only check orders for this symbol
            if order['symbol'] != symbol:
                remaining_orders.append(order)
                continue

            limit_price = order['limit_price']
            action = order['action']
            qty = order['qty']
            
            # CHECK: Did price hit the limit?
            triggered = False
            if action == 1: # BUY LIMIT
                # Buy if price dropped to or below limit
                if current_price <= limit_price:
                    triggered = True
            elif action == 2: # SELL LIMIT
                # Sell if price rose to or above limit
                if current_price >= limit_price:
                    triggered = True
            
            if triggered:
                print(f"⚡ LIMIT TRIGGERED: {order['type']} @ {limit_price} (Price: {current_price})")
                # Execute as a MARKET order now that it's triggered
                # We recurse back into place_order but as 'MARKET' to reuse logic
                self.place_order(
                    action=action, 
                    symbol=symbol, 
                    price=current_price, # Fill at market price (or limit if better)
                    qty=qty,
                    type='MARKET', # Convert to Market fill
                    sl=order['sl'],
                    tp=order['tp'],
                    date=get_utc_now()
                )
                # Do NOT add to remaining_orders (it's gone)
            else:
                remaining_orders.append(order)

        # Update state if changed
        if len(remaining_orders) != len(pending):
            self.state['pending_orders'] = remaining_orders
            self._save_state()

    # --- IMPLEMENTING THE CONTRACT ---
    def connect(self):
        print("✅ Shadow Broker: Connected to Local Database.")
        return True

    def get_tick(self, symbol):
        return 0.0 

    def get_positions(self):
        return {
            "equity": self.state.get('equity', self.initial_capital),
            "position": self.state.get('position', 'FLAT'),
            "orders": self.state.get('pending_orders', [])
        }

    def place_order(self, action, symbol, price, qty, **kwargs):
        order_type = kwargs.get('type', 'MARKET') # MARKET or LIMIT
        tif = kwargs.get('tif', 'DAY') # DAY or GTC
        
        position = self.state['position']
        date_utc = kwargs.get('date', 'Unknown')
        sl = kwargs.get('sl', 0.0)
        tp = kwargs.get('tp', 0.0)
        date_str = to_display_time(date_utc)

        # --- LIMIT ORDER LOGIC ---
        if order_type == 'LIMIT':
            print(f"📝 ORDER PLACED: {symbol} {qty}x BUY LIMIT @ {price} (TIF: {tif})")
            new_order = {
                "id": random.randint(1000, 9999),
                "action": action,
                "symbol": symbol,
                "limit_price": price,
                "qty": qty,
                "type": "LIMIT",
                "tif": tif,
                "sl": sl,
                "tp": tp,
                "date": str(date_utc)
            }
            self.state['pending_orders'].append(new_order)
            self._save_state()
            return True

        # --- MARKET EXECUTION (Existing Logic) ---
        filled_price = self._apply_friction(price, action, symbol)

        if action == 1: # BUY
            if position == "FLAT":
                has_margin, req_margin = self.check_margin(filled_price, qty)
                if not has_margin:
                    return False

                print(f"🚀 BROKER: BUY SENT @ {date_str}")
                print(f"   📉 FILLED @ {filled_price} (Margin: ${req_margin:.2f})")
                
                self.state['position'] = {
                    "type": "LONG",
                    "symbol": symbol,
                    "entry_price": filled_price,
                    "entry_date": str(date_utc),
                    "qty": qty,
                    "sl": sl,
                    "tp": tp,
                    "margin_locked": req_margin
                }
                self._save_state()
                return True

        elif action == 2: # SELL
            if isinstance(position, dict):
                entry_price = position['entry_price']
                entry_date = position['entry_date']
                
                gross_pnl = (filled_price - entry_price) * self.contract_size * position['qty']
                comm = self.commission_per_lot * position['qty']
                swap = self.calculate_swap(entry_date, position['qty'])
                net_pnl = gross_pnl - comm + swap
                
                print(f"🔻 BROKER: SELL SENT @ {date_str}")
                print(f"   📉 FILLED @ {filled_price}")
                print(f"   💰 GROSS: ${gross_pnl:.2f} | COMM: -${comm:.2f} | SWAP: ${swap:.2f}")
                print(f"   🏁 NET PnL: ${net_pnl:.2f}")

                self.state['equity'] += net_pnl
                self.state['position'] = "FLAT"
                self.state['history'].append({
                    "date": str(date_utc), 
                    "pnl": net_pnl, 
                    "exit": filled_price
                })
                self._save_state()
                return True
                
        return False