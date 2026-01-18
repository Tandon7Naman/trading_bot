

import os
from dotenv import load_dotenv

load_dotenv()

# --- SYSTEM SETTINGS ---
TRADING_MODE = os.getenv("TRADING_MODE", "PAPER")

# --- FEATURE FLAGS (The Master Switch) ---
# Add "MCX" to this list to enable the Indian Pipeline.
# Add "XAUUSD" to this list to enable the Global Spot Pipeline.
# Current State: XAUUSD is ACTIVE, MCX is DORMANT.
ENABLED_MARKETS = [
	"XAUUSD"  
	# "MCX"   <-- Commented out (Dormant Pipeline)
]

# --- ASSET CONFIGURATION ---
ASSET_CONFIG = {
	"MCX": {
		"symbol": "GC=F",          # Uses Global Gold to estimate MCX
		"data_file": "data/MCX_gold_daily.csv",
		"strategy": "strategies.gold_scalper",
		"qty": 10
	},
	"XAUUSD": {
		"symbol": "GC=F",          # Back to Gold Futures
		"data_file": "data/XAUUSD_1m.csv",
		"strategy": "strategies.xauusd_strategy",
		"qty": 0.1
	}
}
