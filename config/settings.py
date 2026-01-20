# --- PROTOCOL 5.1: PATIENCE (COOLDOWN) ---
STRATEGY_CONFIG = {
    "cooldown_minutes": 240, # 4 Hours forced wait after a trade closes
}

# --- PROTOCOL 5.2: JOURNALING ---
JOURNAL_CONFIG = {
    "enabled": True,
    "type": "CSV", # Options: "CSV" or "GSHEET"
    # If using Google Sheets:
    "spreadsheet_name": "Gold_Bot_Journal_2026",
    "json_keyfile": "service_account.json" # Path to Google Cloud Credentials
}

# --- PROTOCOL 5.3: FAT FINGER SAFETY ---
EXECUTION_CONFIG = {
    "max_slippage_pct": 0.05, # Reject if price deviates > 5%
    "max_notional_value": 500_000 # Max $500k per order
}
import os
from datetime import time

# Base Directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Enabled Markets
ENABLED_MARKETS = ["XAUUSD"] 

# --- PROTOCOL 9.0: ASSET SPECIFICATIONS ---
ASSET_CONFIG = {
    # --- GLOBAL SPOT GOLD (XAUUSD) ---
    "XAUUSD": {
        "symbol_root": "XAUUSD",   
        "data_symbol": "GC=F",     
        "data_file": os.path.join(BASE_DIR, "data", "XAUUSD_1m.csv"),
        
        "schedule": {
            "timezone": "UTC",
            "open_time": "00:00",
            "close_time": "23:00"
        },

        # Physics & Valuation
        "type": "SPOT",
        "contract_size": 100,       
        "leverage": 100.0,          
        "tick_size": 0.01,          
        "tick_value_usd": 1.00,     
        "spread": 0.20,             
        
        # Volume Constraints (RENAMED in Protocol 9.0)
        "min_vol": 0.01,            
        "max_vol": 10.0,
        "vol_step": 0.01,
        
        # Risk Buffers
        "margin_buffer": 1.5,       
    },

    # --- MCX GOLD FUTURES (INDIA) ---
    "MCX_GOLD": {
        "symbol_root": "GOLD",     
        "data_symbol": "GOLDM",    
        "data_file": os.path.join(BASE_DIR, "data", "MCX_GOLD_1m.csv"),
        
        "schedule": {
            "timezone": "Asia/Kolkata",
            "open_time": "09:00",
            "close_time": "23:30"
        },

        "type": "FUTURES",
        "contract_size": 100,       
        "leverage": 1.0,            
        "tick_size": 1.00,          
        "tick_value_inr": 100.0,    
        "spread": 5.0,              
        
        "min_vol": 1.0,             
        "max_vol": 50.0,
        "vol_step": 1.0,
        
        "margin_buffer": 2.0,       
    }
}


# --- PROTOCOL 7.3: TELEMETRY ---
TELEGRAM_CONFIG = {
    "enabled": True,
    "bot_token": "YOUR_BOT_TOKEN_HERE", 
    "chat_id": "YOUR_CHAT_ID_HERE"      
}

# --- PROTOCOL 4.1: NEWS & AI CONFIG ---
NEWS_CONFIG = {
    "enabled": True,
    "api_key": "ee4c539decb34898b99ae395a8f6327b", # Get from newsapi.org
    "sources": "bloomberg,reuters,cnbc,financial-times,crypto-coins-news",
    "cache_seconds": 3600, # Only fetch news once per hour (Save API calls)
    "sentiment_threshold": 0.5 # Confidence required to trigger a Veto
}