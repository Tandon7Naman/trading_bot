"""
Finnhub API Client for news, sentiment, and economic data.
"""
import os
import requests
from typing import Optional, Dict, Any, List

class FinnhubClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY")
        self.base_url = "https://finnhub.io/api/v1"
        if not self.api_key:
            raise ValueError("Finnhub API key not set. Set FINNHUB_API_KEY in environment or pass to constructor.")

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}/{endpoint}"
        params = params or {}
        params["token"] = self.api_key
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    def get_news(self, category: str = "general", min_id: Optional[int] = None) -> List[Dict[str, Any]]:
        params = {"category": category}
        if min_id:
            params["minId"] = min_id
        return self._get("news", params)

    def get_company_news(self, symbol: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        params = {"symbol": symbol, "from": from_date, "to": to_date}
        return self._get("company-news", params)

    def get_news_sentiment(self, symbol: str) -> Dict[str, Any]:
        return self._get("news-sentiment", {"symbol": symbol})

    def get_economic_calendar(self) -> List[Dict[str, Any]]:
        return self._get("calendar/economic")

    def get_market_news(self, category: str = "general") -> List[Dict[str, Any]]:
        return self._get("news", {"category": category})

# Example usage:
# client = FinnhubClient()
# news = client.get_news()
# sentiment = client.get_news_sentiment("AAPL")
# econ = client.get_economic_calendar()
