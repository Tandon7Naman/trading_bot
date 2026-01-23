
import json
import logging
import os
import sys

import redis

# Ensure we can find the sibling modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from titan_brain.sentiment_engine import FinBERTEngine
from titan_memory.memory_engine import TitanMemory

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - TITAN-BRAIN - %(levelname)s - %(message)s')
logger = logging.getLogger("TitanBrain")

def main():
    # 1. Initialize Components
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        pubsub = r.pubsub()
        pubsub.subscribe('titan.news.raw')

        engine = FinBERTEngine()
        memory = TitanMemory() # <--- NEW: Initialize Memory

        logger.info("🧠 Brain + Memory ONLINE. Waiting for news...")
    except Exception as e:
        logger.critical(f"❌ Startup Failed: {e}")
        return

    # 2. Processing Loop
    for message in pubsub.listen():
        if message['type'] == 'message':
            try:
                # Parse
                raw_data = json.loads(message['data'])
                headline = raw_data.get('headline', '')
                if not headline:
                    continue

                # A. COGNITION (FinBERT Analysis)
                full_text = f"{headline}. {raw_data.get('summary', '')}"
                analysis = engine.analyze(full_text)

                # B. MEMORY (RAG Search)
                # Ask: "Have we seen something like this before?"
                historical_events = memory.find_similar_events(headline, limit=1)

                context_msg = "New Event"
                if historical_events:
                    top_match = historical_events[0]
                    # If similarity is high (> 0.75), it's a "Repeat Event"
                    if top_match.score > 0.75:
                        prev_text = top_match.payload.get('text', '')[:40]
                        context_msg = f"Similar to: '{prev_text}...'"

                # C. LOGGING (The "Glass Box" View)
                icon = "⚪"
                if analysis['score'] > 0.5:
                    icon = "🟢"
                elif analysis['score'] < -0.5:
                    icon = "🔴"

                print(f"{icon} [{raw_data['symbols'][0]}] Score: {analysis['score']:.2f}")
                print(f"   📰 News: {headline[:60]}...")
                print(f"   🧠 Memory: {context_msg}")

                # D. MEMORIZATION (Store this event for the future)
                memory.store_event(headline, {
                    "symbol": raw_data['symbols'][0],
                    "sentiment": analysis['score'],
                    "source": raw_data['source']
                })

                # E. PUBLISH (To Execution Engine)
                # ... (Publishing logic remains the same)

            except Exception as e:
                logger.error(f"⚠️ Error: {e}")

if __name__ == "__main__":
    main()
