from execution.base_broker import BrokerInterface

class MT5Broker(BrokerInterface):
    """
    Protocol 7.1: Live Execution Engine.
    Swaps seamlessly with PaperBroker because it follows the same Contract.
    """
    def connect(self):
        import MetaTrader5 as mt5
        import time
        from datetime import datetime
        from execution.base_broker import BrokerInterface
        from execution.telegram_alerts import send_telegram_message
        from config.settings import ASSET_CONFIG

        class MT5Broker(BrokerInterface):
            """
            Protocol 6.0: Live Bridge to MetaTrader 5.
            Translates internal 'Buy/Sell' commands into MT5 OrderRequests.
            """
            def __init__(self):
                self.connected = False
                self._connect()

            def _connect(self):
                if not mt5.initialize():
                    print("   ❌ MT5 Init Failed")
                    self.connected = False
                    return False
        
                print("   ✅ MT5 Connected Successfully")
                self.connected = True
                return True

            def get_positions(self):
                """
                Protocol 6.1: Reconciliation.
                Reads live positions from MT5 and standardizes them for the bot.
                """
                if not self.connected: self._connect()
        
                # 1. Get Account Info
                account_info = mt5.account_info()
                if account_info is None:
                    return {"equity": 0.0, "position": "FLAT", "orders": []}
            
                equity = account_info.equity
        
                # 2. Get Open Positions (Only for our Symbol)
                # Assuming single symbol architecture for now
                positions = mt5.positions_get(symbol="XAUUSD")
        
                pos_data = "FLAT"
                if positions and len(positions) > 0:
                    p = positions[0]
                    pos_data = {
                        "symbol": p.symbol,
                        "type": "LONG" if p.type == mt5.ORDER_TYPE_BUY else "SHORT",
                        "qty": p.volume,
                        "entry_price": p.price_open,
                        "sl": p.sl,
                        "tp": p.tp,
                        "ticket": p.ticket
                    }
            
                return {
                    "equity": equity,
                    "position": pos_data,
                    "orders": [] # Not parsing pending orders for this simplified version
                }

            def place_order(self, action, symbol, price, qty, **kwargs):
                """
                Protocol 6.2: Execution (OCO).
                Sends market order WITH attached SL/TP (Server-Side).
                """
                if not self.connected: self._connect()
        
                # Convert Action to MT5 Constant
                mt5_action = mt5.ORDER_TYPE_BUY if action == 1 else mt5.ORDER_TYPE_SELL
        
                sl = kwargs.get('sl', 0.0)
                tp = kwargs.get('tp', 0.0)
        
                # Validate Stops (Protocol 2.3)
                if sl <= 0:
                    print("   ❌ MT5 REJECT: Naked Order (No SL)")
                    return False

                # Construct Request
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": float(qty),
                    "type": mt5_action,
                    "price": price, # For Market orders, this is indicative
                    "sl": float(sl),
                    "tp": float(tp),
                    "deviation": 20, # Slippage tolerance in points
                    "magic": 123456,
                    "comment": "Gold Bot 2026",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
        
                # Send
                print(f"   📤 SENDING TO MT5: {symbol} {qty} lots @ {price}")
                result = mt5.order_send(request)
        
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    print(f"   ❌ MT5 ERROR: {result.comment} (Code: {result.retcode})")
                    send_telegram_message(f"⚠️ *EXECUTION FAILED*\n{result.comment}")
                    return False
            
                print(f"   ✅ FILLED: Ticket #{result.order}")
        
                # Telemetry
                msg = "OPEN LONG" if action == 1 else "OPEN SHORT"
                send_telegram_message(f"🚀 *{msg}*\nSize: {qty}\nSL: {sl}\nTicket: {result.order}")
                return True
