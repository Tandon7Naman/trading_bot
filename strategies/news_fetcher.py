import feedparser
import time
from config.settings import NEWS_CONFIG

class NewsFetcher:
    """
    Protocol 4.1.1: Data Ingestion (Google News RSS).
    The 'Hacker' solution: unlimited, free, and cloud-friendly.
    """
    _cache = {}
    _last_fetch = {}
    
    # Google News RSS URL Structure
    BASE_URL = "https://news.google.com/rss/search?q={query}+when:1d&hl=en-US&gl=US&ceid=US:en"

    @staticmethod
    def get_headlines(symbol="XAUUSD"):
        """
        Fetches headlines via RSS. No API Key required.
        """
        if not NEWS_CONFIG["enabled"]:
            return []

        # 1. Cache Check (Politeness Policy: Don't spam Google)
        now = time.time()
        if symbol in NewsFetcher._last_fetch:
            if now - NewsFetcher._last_fetch[symbol] < 600: # 10 minutes cache
                return NewsFetcher._cache[symbol]

        # 2. Construct Query
        # If symbol is XAUUSD, search "Gold Price", else search symbol directly
        search_term = "Gold Price" if "XAU" in symbol else symbol
        formatted_url = NewsFetcher.BASE_URL.format(query=search_term.replace(" ", "+"))

        try:
            # 3. Parse Feed
            feed = feedparser.parse(formatted_url)
            
            headlines = []
            if feed.entries:
                # Get top 5 articles
                for entry in feed.entries[:5]:
                    # Combine Title + Summary for better Sentiment Analysis
                    text = f"{entry.title}. {entry.get('summary', '')}"
                    headlines.append(text)

                # Update Cache
                NewsFetcher._cache[symbol] = headlines
                NewsFetcher._last_fetch[symbol] = now
                print(f"   📰 NEWS: Fetched {len(headlines)} articles (Google RSS).")
                return headlines
            
            return []

        except Exception as e:
            print(f"   ⚠️ RSS Fetch Failed: {e}")
            return []