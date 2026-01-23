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

    def fetch_feed(self, query):
        """
        Fetches RSS feed for a specific query (e.g., 'Gold Price' or 'AAPL')
        """
        params = {
            "q": query,
            "hl": "en-US",
            "gl": "US",
            "ceid": "US:en"
        }

        # We must use a User-Agent or Google might block the request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            response = requests.get(self.base_url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                return feedparser.parse(response.content)
            else:
                logger.warning(f"⚠️ Google RSS Error {response.status_code} for query: {query}")
                return None
        except Exception as e:
            logger.error(f"🔴 Network Error fetching {query}: {e}")
            return None

    def process_entry(self, entry, query):
        """
        Normalizes an RSS entry into a Titan News Event
        """
        # 1. Deduplication Check
        link = entry.get("link")
        if link in self.seen_articles:
            return

        # Add to cache (In production, use Redis SET with TTL for this cache)
        self.seen_articles.add(link)

        # 2. Parse Timestamp
        try:
            # RSS dates are RFC 822 (e.g., "Tue, 23 Jan 2026 01:00:00 GMT")
            # We convert to ISO 8601 for our system
            published_dt = parsedate_to_datetime(entry.get("published"))
            iso_timestamp = published_dt.isoformat()
        except:
            iso_timestamp = datetime.utcnow().isoformat()

        # 3. Normalize Data
        news_event = {
            "id": entry.get("id", link), # Google RSS provides a GUID usually
            "headline": entry.get("title"),
            "summary": entry.get("description"), # Note: This often contains HTML
            "url": link,
            "created_at": iso_timestamp,
            "symbols": [query], # Tag the event with the query used to find it
            "source": "google_rss"
        }

        # 4. Publish to "Hot Path"
        self.publisher.publish(news_event)

        # Clean Console Output
        print(f"📰 [{query}] {news_event['headline'][:80]}...")

    def run(self):
        logger.info("🟢 Titan RSS Poller Started")
        logger.info(f"📡 Monitoring Universe: {TITAN_CONFIG.symbols}")

        while True:
            # Iterate through all symbols in our config
            for symbol in TITAN_CONFIG.symbols:
                feed = self.fetch_feed(symbol)

                if feed and feed.entries:
                    # Process the top 5 newest articles per symbol
                    for entry in feed.entries[:5]:
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
