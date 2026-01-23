import json
import logging
import time

import redis

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - TITAN-ACTOR - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TitanActor")

class TitanExecutionEngine:
    def __init__(self):
        # 1. Connect to the "Nervous System" (Redis)
        self.redis = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe('titan.news.sentiment')

        # 2. Strategy Constraints (The "Gatekeeper")
        self.sentiment_threshold = 0.80  # Only act on strong signals (> 0.8 or < -0.8)
        self.confidence_threshold = 0.90 # Only act if FinBERT is very sure

        # 3. Mock Portfolio State
        self.active_positions = set()

    def process_signal(self, signal):
        """
        Decides whether to Trade or Ignore based on the Strategy.
        """
        symbol = signal['symbol']
        score = signal['sentiment_score']
        confidence = signal['confidence']

        # LOGIC: The "Titan" Strategy
        decision = "HOLD"
        action_color = "⚪"

        # Long Logic
        if score >= self.sentiment_threshold and confidence >= self.confidence_threshold:
            decision = "BUY"
            action_color = "🚀"

        # Short Logic
        elif score <= -self.sentiment_threshold and confidence >= self.confidence_threshold:
            decision = "SELL"
            action_color = "📉"

        # EXECUTION BLOCK
        if decision != "HOLD":
            print("\n" + "="*60)
            print(f"{action_color} TRADE TRIGGERED: {symbol} | Action: {decision}")
            print(f"   Reason: Sentiment Score {score:.2f} is extreme.")
            print(f"   Confidence: {confidence*100:.1f}%")
            print(f"   Time: {time.strftime('%H:%M:%S')}")
            print("="*60 + "\n")

            # TODO: Add Alpaca/MetaTrader API Call Here
            # alpaca.submit_order(symbol, qty=1, side=decision, type='market')

            self.active_positions.add(symbol)
        else:
            # Log filtered signals just for debugging (optional)
            # logger.info(f"Filtered: {symbol} Score: {score:.2f} (Too weak)")
            pass

    def run(self):
        logger.info("🤖 Titan Execution Engine is ARMED and WAITING...")
        logger.info(f"   Strategy: Trade if Score > {self.sentiment_threshold} OR < -{self.sentiment_threshold}")

        for message in self.pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    self.process_signal(data)
                except Exception as e:
                    logger.error(f"Signal Error: {e}")

if __name__ == "__main__":
    bot = TitanExecutionEngine()
    bot.run()
