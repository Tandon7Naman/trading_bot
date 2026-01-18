import json
import os
import numpy as np
from datetime import datetime

# Try importing alerts, handle failure gracefully
try:
    from execution.telegram_alerts import send_telegram_message
except ImportError:
    send_telegram_message = lambda x: None

class PaperBroker:
    def __init__(self, state_file='data/paper_state_mcx.json', initial_capital=500000.0):
        self.state_file = state_file
        self.initial_capital = initial_capital
        self.state = self._load_state()

    def _convert(self, o):
        if isinstance(o, np.int64): return int(o)
        if isinstance(o, np.float32): return float(o)
        return o

    def _load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    if 'history' not in state: state['history'] = []
                    return state
            except:
                pass
        return {
            "equity": self.initial_capital,
            "position": "FLAT",
            "history": []
        }

    def _save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=4, default=self._convert)

    def get_account_info(self):
        return {
            "equity": self.state.get('equity', self.initial_capital),
            "position": self.state.get('position', 'FLAT')
        }

    def execute_trade(self, action, price, date, rsi_value):
        """
        Action: 1 = BUY, 2 = SELL
        Returns: True if trade executed, False otherwise
        """
        position = self.state['position']
        
        # --- BUY EXECUTION ---
        if action == 1:
            if position == "FLAT":
                print("🚀 BROKER: Executing BUY Order")
                self.state['position'] = {
                    "type": "LONG",
                    "entry_price": price,
                    "entry_date": str(date),
                    "qty": 10
                }
                self._save_state()
                send_telegram_message(f"🚀 BUY FILLED\nPrice: ₹{price:.2f}\nRSI: {rsi_value:.1f}")
                return True

        # --- SELL EXECUTION ---
        elif action == 2:
            if isinstance(position, dict):
                print("🔻 BROKER: Executing SELL Order")
                entry_price = position['entry_price']
                pnl = (price - entry_price) * 10
                
                self.state['equity'] += pnl
                self.state['position'] = "FLAT"
                self.state['history'].append({
                    "date": str(date),
                    "pnl": pnl,
                    "exit_price": price
                })
                
                self._save_state()
                
                emoji = "✅" if pnl > 0 else "❌"
                send_telegram_message(f"{emoji} SELL FILLED\nP&L: ₹{pnl:.2f}\nExit: ₹{price:.2f}")
                return True
                
        return False
