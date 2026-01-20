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