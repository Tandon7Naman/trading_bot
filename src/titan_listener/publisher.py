import json
import logging
from datetime import datetime

import redis

from config import TITAN_CONFIG

logger = logging.getLogger("TitanPublisher")

class RedisPublisher:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=TITAN_CONFIG.redis_host,
            port=TITAN_CONFIG.redis_port,
            decode_responses=True
        )
        self.channel = TITAN_CONFIG.redis_channel

    def publish(self, news_event: dict):
        """
        Pushes a normalized news event to the Redis Stream.
        """
        try:
            # Add ingestion timestamp for latency tracking
            news_event['titan_ingested_at'] = datetime.utcnow().isoformat()

            payload = json.dumps(news_event)
            self.redis_client.publish(self.channel, payload)

            # Optional: Log latency (Debug only)
            # logger.debug(f"Published event {news_event.get('id')} to {self.channel}")

        except redis.RedisError as e:
            logger.error(f"🔴 Redis Publish Failed: {e}")
