import json

import redis

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# 🚀 SIGNAL: Panic Sell Gold
fake_signal = {
    "id": "test_mt5_execution",
    "symbol": "Gold Price",    # Maps to XAUUSD in your Actor code
    "sentiment_score": -0.99,  # Extreme Fear
    "confidence": 0.99,
    "original_created_at": "2026-01-23T12:00:00",
    "processed_at": "2026-01-23T12:00:05"
}

print(f"🚀 Injecting MT5 Signal: {fake_signal}")
r.publish('titan.news.sentiment', json.dumps(fake_signal))
