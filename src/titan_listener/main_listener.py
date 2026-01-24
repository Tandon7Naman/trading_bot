import json
import logging
import time

import websocket
from publisher import RedisPublisher

from config import TITAN_CONFIG

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - TITAN-LISTENER - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TitanListener")

class TitanNewsListener:
    def __init__(self):
        self.publisher = RedisPublisher()
        self.ws = None
        self.should_run = True
        self.reconnect_delay = 1  # Seconds

    def on_open(self, ws):
        logger.info("🟢 Connected to Alpaca News Stream")

        # 1. Authenticate
        auth_payload = {
            "action": "auth",
            "key": TITAN_CONFIG.api_key,
            "secret": TITAN_CONFIG.api_secret.get_secret_value()
        }
        ws.send(json.dumps(auth_payload))

    def on_message(self, ws, message):
        data = json.loads(message)

        # Handle Array of Messages (Alpaca sends lists)
        for item in data:
            msg_type = item.get("T")

            if msg_type == "success" and item.get("msg") == "authenticated":
                logger.info("🔐 Authenticated successfully. Subscribing to news...")
                # 2. Subscribe after Auth
                sub_payload = {
                    "action": "subscribe",
                    "news": ["*"] # Subscribe to all, filter later if needed
                }
                ws.send(json.dumps(sub_payload))

            elif msg_type == "n": # "n" = News Event
                # 3. Process News Item
                self.handle_news(item)

            elif msg_type == "error":
                logger.error(f"⚠️ Stream Error: {item.get('msg')}")

    def handle_news(self, raw_data):
        """Normalize and Publish"""
        # Extract critical fields
        normalized_event = {
            "id": raw_data.get("id"),
            "headline": raw_data.get("headline"),
            "summary": raw_data.get("summary"),
            "author": raw_data.get("author"),
            "created_at": raw_data.get("created_at"),
            "symbols": raw_data.get("symbols", []),
            "source": "alpaca_benzinga"
        }

        # Only publish if it relates to our universe (Optional Optimization)
        # matches = set(normalized_event['symbols']).intersection(set(TITAN_CONFIG.symbols))
        # if matches:

        # Publish to "Hot Path" (Redis)
        self.publisher.publish(normalized_event)
        print(f"📡 NEWS: {normalized_event['headline']} ({len(normalized_event['symbols'])} tickers)")

    def on_error(self, ws, error):
        logger.error(f"🔴 WebSocket Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        logger.warning("🟠 Connection Closed. Attempting Reconnect...")

    def run(self):
        """Main Loop with Exponential Backoff"""
        while self.should_run:
            try:
                self.ws = websocket.WebSocketApp(
                    TITAN_CONFIG.news_wss_url,
                    on_open=self.on_open,
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close
                )

                # Connect
                self.ws.run_forever()

            except Exception as e:
                logger.critical(f"💥 Critical Crash: {e}")

            # Exponential Backoff for Reconnect
            logger.info(f"⏳ Sleeping {self.reconnect_delay}s before reconnecting...")
            time.sleep(self.reconnect_delay)
            self.reconnect_delay = min(self.reconnect_delay * 2, 60) # Cap at 60s

