import logging
import time
from datetime import datetime
from email.utils import parsedate_to_datetime

import feedparser
import requests
from publisher import RedisPublisher

from config import TITAN_CONFIG

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - TITAN-RSS - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TitanRSS")

class GoogleRSSPoller:
    def __init__(self):
        self.publisher = RedisPublisher()
        # Cache to store seen article links so we don't re-process them
        self.seen_articles = set()
        # Base URL for Google News Search RSS
        self.base_url = "https://news.google.com/rss/search"
        # Removed GoogleRSSPoller and all news logic
                        self.process_entry(entry, symbol)

                # Polite sleep between requests to avoid rate limiting
                time.sleep(2)

            # Wait before the next full cycle (e.g., 2 minutes)
            logger.info("💤 Cycle complete. Sleeping 120s...")
            time.sleep(120)

if __name__ == "__main__":
    bot = GoogleRSSPoller()
    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("🛑 RSS Poller Stopped")
