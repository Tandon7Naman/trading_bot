import os

from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()

# 2. Validate Critical Keys (Warning System)
required_keys = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
missing_keys = [key for key in required_keys if not os.getenv(key)]

if missing_keys:
    print(f"⚠️  CONFIG WARNING: Missing keys in .env: {missing_keys}")

# --- GLOBAL SETTINGS ---
SYMBOL = os.getenv("TRADING_PAIR", "XAUUSD")
TIMEFRAME = os.getenv("TIMEFRAME", "1m")
RISK_PERCENT = float(os.getenv("RISK_PER_TRADE", 0.01))

# --- ASSET CONFIGURATION ---
ASSET_CONFIG = {
    "XAUUSD": {
        "contract_size": 100,
        "leverage": 100,
        "tick_size": 0.01,
        "min_vol": 0.01,
        "max_vol": 100.0,
        "vol_step": 0.01,
        # 🟢 MISSING LINE RESTORED:
        "data_file": "data/XAUUSD_M1.csv",
    }
}

# --- 🟢 MISSING COMPONENT RESTORED 🟢 ---
ENABLED_MARKETS = ["XAUUSD"]
# ----------------------------------------

# --- BROKER CONFIGURATION ---
BINANCE_CONFIG = {
    "api_key": os.getenv("BINANCE_API_KEY"),
    "api_secret": os.getenv("BINANCE_SECRET"),
    "testnet": True,
}

# --- TELEGRAM CONFIG ---
TELEGRAM_CONFIG = {
    "enabled": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
    "bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
    "chat_id": os.getenv("TELEGRAM_CHAT_ID"),
}

# --- NEWS CONFIG ---
NEWS_CONFIG = {
    "enabled": True,
    "api_key": os.getenv("NEWS_API_KEY"),
    "sources": "bloomberg,reuters,cnbc,financial-times",
    "cache_seconds": 3600,
    "sentiment_threshold": 0.5,
}

# --- STRATEGY CONFIG ---
STRATEGY_CONFIG = {
    "cooldown_minutes": 240,
}

JOURNAL_CONFIG = {"enabled": True, "type": "CSV"}

EXECUTION_CONFIG = {"max_slippage_pct": 0.05, "max_notional_value": 500_000}
