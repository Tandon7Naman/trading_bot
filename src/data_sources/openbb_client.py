"""
OpenBB SDK Client for real-time market data, technical indicators, and fundamentals.
"""
import os
from typing import Any, Dict, Optional

try:
    from openbb import obb
except ImportError:
    obb = None

class OpenBBClient:
    def __init__(self, api_key: Optional[str] = None):
        if obb is None:
            raise ImportError("OpenBB SDK is not installed. Install with 'pip install openbb' or see https://docs.openbb.co/sdk.")
        self.api_key = api_key or os.getenv("OPENBB_API_KEY")
        if self.api_key:
            obb.account.login(self.api_key)

    def get_price(self, symbol: str, provider: str = "yfinance") -> Any:
        return obb.equity.price(symbol, provider=provider)

    def get_ohlcv(self, symbol: str, provider: str = "yfinance") -> Any:
        return obb.equity.ohlcv(symbol, provider=provider)

    def get_technicals(self, symbol: str, indicator: str = "rsi", provider: str = "yfinance", **kwargs) -> Any:
        return obb.equity.ta(indicator, symbol=symbol, provider=provider, **kwargs)

    def get_fundamentals(self, symbol: str, provider: str = "yfinance") -> Dict[str, Any]:
        return obb.equity.fundamentals(symbol, provider=provider)

    def get_news(self, symbol: str, provider: str = "yfinance") -> Any:
        return obb.equity.news(symbol, provider=provider)

# Example usage:
# client = OpenBBClient()
# price = client.get_price("AAPL")
# ohlcv = client.get_ohlcv("AAPL")
# rsi = client.get_technicals("AAPL", indicator="rsi")
# fundamentals = client.get_fundamentals("AAPL")
