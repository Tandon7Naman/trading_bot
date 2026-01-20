import requests
import time
from datetime import datetime, timedelta
from config.settings import NEWS_CONFIG

class NewsFetcher:
    """
    Protocol 4.1.1: Data Ingestion.
    Fetches financial headlines from reputable sources via NewsAPI.
    """
    _cache = {}
    _last_fetch = {}

    @staticmethod
    def get_headlines(symbol="XAUUSD"):
        """
        Returns a list of recent headlines for the asset.
        Implements caching to prevent hitting API rate limits.
        """
        if not NEWS_CONFIG["enabled"]:
            return []

        # 1. Check Cache
        now = time.time()
        if symbol in NewsFetcher._last_fetch:
            if now - NewsFetcher._last_fetch[symbol] < NEWS_CONFIG["cache_seconds"]:
                return NewsFetcher._cache[symbol]

        # 2. Define Query
        query = "gold price" if "XAU" in symbol else symbol
        
        # 3. Fetch from API
        api_key = NEWS_CONFIG["api_key"]
        if "YOUR_" in api_key: 
            return [] # Fail silently if no key

        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "sortBy": "publishedAt",
            "language": "en",
            "apiKey": api_key,
            "sources": NEWS_CONFIG["sources"],
            "from": (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        }

        try:
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            if data.get("status") == "ok":
                articles = data.get("articles", [])
                # Extract just the title and description
                headlines = [f"{a['title']}. {a['description']}" for a in articles[:10]]
                
                # Update Cache
                NewsFetcher._cache[symbol] = headlines
                NewsFetcher._last_fetch[symbol] = now
                print(f"   📰 NEWS: Fetched {len(headlines)} new articles for {symbol}")
                return headlines
            else:
                print(f"   ⚠️ NewsAPI Error: {data.get('message')}")
                return []
                
        except Exception as e:
            print(f"   ⚠️ News Fetch Failed: {e}")
            return []
