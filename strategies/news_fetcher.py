import requests
import time
from datetime import datetime, timedelta
from config.settings import NEWS_CONFIG

class NewsFetcher:
    """Protocol 4.1.1: Data Ingestion (NewsAPI)."""
    _cache = {}
    _last_fetch = {}

    @staticmethod
    def get_headlines(symbol="XAUUSD"):
        if not NEWS_CONFIG["enabled"]: return []

        now = time.time()
        # Cache Check
        if symbol in NewsFetcher._last_fetch:
            if now - NewsFetcher._last_fetch[symbol] < NEWS_CONFIG["cache_seconds"]:
                return NewsFetcher._cache[symbol]

        # API Request
        query = "gold price" if "XAU" in symbol else symbol
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query, "sortBy": "publishedAt", "language": "en",
            "apiKey": NEWS_CONFIG["api_key"], "sources": NEWS_CONFIG["sources"],
            "from": (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        }

        try:
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            if data.get("status") == "ok":
                headlines = [f"{a['title']}. {a['description']}" for a in data.get("articles", [])[:10]]
                NewsFetcher._cache[symbol] = headlines
                NewsFetcher._last_fetch[symbol] = now
                print(f"   📰 NEWS: Fetched {len(headlines)} articles.")
                return headlines
            return []
        except Exception:
            return []