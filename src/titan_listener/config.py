
from pydantic import BaseModel, Field, SecretStr


class ListenerConfig(BaseModel):
    # Alpaca Credentials
    api_key: str = Field(..., description="Alpaca API Key")
    api_secret: SecretStr = Field(..., description="Alpaca Secret Key")

    # Endpoint Configuration
    # Use 'wss://stream.data.alpaca.markets/v1beta1/news' for real-time news
    news_wss_url: str = "wss://stream.data.alpaca.markets/v1beta1/news"

    # Redis Configuration (The "Hot Path" Message Bus)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_channel: str = "titan.news.raw"

    # Subscription Scope
    # We filter for major assets to reduce noise
    symbols: list[str] = Field(default_factory=lambda: [
        "AAPL stock", "TSLA stock", "NVDA stock", "AMD stock",
        "MSFT stock", "GOOGL stock", "AMZN stock", "META stock",
        "SPY ETF", "QQQ ETF", "IWM ETF", "Gold Price"
    ])

# Instantiate config (In production, load from env vars)
try:
    # REPLACE THESE WITH YOUR ACTUAL KEYS OR USE OS.GETENV
    TITAN_CONFIG = ListenerConfig(
        api_key="PK_YOUR_API_KEY",
        api_secret="YOUR_SECRET_KEY"
    )
except Exception as e:
    print(f"❌ Configuration Error: {e}")
    exit(1)
