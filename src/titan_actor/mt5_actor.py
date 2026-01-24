import json
import logging
from typing import Any

import MetaTrader5 as mt5
import redis

# --- CONFIGURATION ---
# Note: You don't need API keys here if MT5 is already open and logged in!
SYMBOL_MAP = {
    "Gold Price": "GOLD",   # Example: Change XAUUSD to GOLD if that's what you see
    "TSLA": "TSLA.US",      # Example: Some brokers use .US suffix
    "AAPL": "AAPL.US",
}

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - TITAN-MT5 - %(levelname)s - %(message)s')
logger = logging.getLogger("TitanMT5")

class MT5ExecutionEngine:
    def __init__(self) -> None:
        # 1. Connect to Redis
        self.redis: redis.Redis = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe('titan.news.sentiment')

        # 2. Connect to MT5 Terminal
        if not mt5.initialize():
            logger.critical(f"❌ MT5 Init Failed: {mt5.last_error()}")
            self.connected: bool = False
        else:
            logger.info(f"skynet Connected to MT5 Terminal version: {mt5.version()}")
            self.connected: bool = True

        # 3. Strategy Constraints
        self.sentiment_threshold: float = 0.80
        self.confidence_threshold: float = 0.90

    def get_mt5_symbol(self, raw_symbol: str) -> str:
        """
        Maps Titan names to MT5 Symbol names with type safety.
        """
        clean: str = raw_symbol.replace(" stock", "").replace(" ETF", "").replace(" Price", "").strip()
        return SYMBOL_MAP.get(clean, clean.upper())

    def execute_trade(self, symbol: str, action_type: int, sentiment_score: float) -> None:
        """
        Executes a trade on MT5.
        Args:
            symbol (str): The asset symbol (e.g., "XAUUSD").
            action_type (int): mt5.ORDER_TYPE_BUY or mt5.ORDER_TYPE_SELL.
            sentiment_score (float): The score triggering this trade.
        """
        if not self.connected:
            return

        symbol_info: Any | None = mt5.symbol_info(symbol)
        if symbol_info is None:
            logger.warning(f"⚠️ Symbol {symbol} not found in MT5")
            return


        # Strict Type Cast for Volume
        min_vol: float = float(symbol_info.volume_min)
        price: float = 0.0
        # ...existing code...
        if not symbol_info.visible:
            mt5.symbol_select(symbol, True)

        # 3. AUTO-DETECT VOLUME (The Fix)
        lot = min_vol

        # 4. AUTO-DETECT FILLING MODE
        filling_type = mt5.ORDER_FILLING_FOK
        try:
            fill_flags = symbol_info.filling_mode
            if fill_flags == mt5.SYMBOL_FILLING_IOC:
                filling_type = mt5.ORDER_FILLING_IOC
            elif fill_flags == mt5.SYMBOL_FILLING_FOK:
                filling_type = mt5.ORDER_FILLING_FOK
            else:
                filling_type = mt5.ORDER_FILLING_RETURN
        except:
            pass

        # 5. Prepare Order
        price = mt5.symbol_info_tick(symbol).ask if action_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).bid

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,  # <--- Now uses the exact minimum required
            "type": action_type,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": f"Titan AI: {sentiment_score:.2f}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_type,
        }

        # 6. Send Order
        result = mt5.order_send(request)

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"❌ Order Failed: {result.comment} (RetCode: {result.retcode})")
            logger.info(f"   Debug: Min Vol: {symbol_info.volume_min}, Max Vol: {symbol_info.volume_max}")
        else:
            side = "BUY" if action_type == mt5.ORDER_TYPE_BUY else "SELL"
            logger.info(f"✅ MT5 EXECUTED: {side} {lot} {symbol} @ {price} | Ticket: {result.order}")

    def process_signal(self, signal):
        mt5_symbol = self.get_mt5_symbol(signal['symbol'])
        score = signal['sentiment_score']
        confidence = signal['confidence']

        action = None
        if score >= self.sentiment_threshold and confidence >= self.confidence_threshold:
            action = mt5.ORDER_TYPE_BUY
        elif score <= -self.sentiment_threshold and confidence >= self.confidence_threshold:
            action = mt5.ORDER_TYPE_SELL

        if action is not None:
            print("\n" + "="*60)
            print(f"⚡ MT5 SIGNAL: {mt5_symbol} | Score: {score:.2f}")
            self.execute_trade(mt5_symbol, action, score)
            print("="*60 + "\n")

    def run(self):
        logger.info("🤖 Titan MT5 Actor is LISTENING...")
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                self.process_signal(data)

if __name__ == "__main__":
    bot = MT5ExecutionEngine()
    try:
        bot.run()
    except KeyboardInterrupt:
        mt5.shutdown()
