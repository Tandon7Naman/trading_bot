import pandas as pd
import numpy as np
import os
import asyncio
from execution.paper_broker import PaperBroker
from strategies.pricing import GoldPricingEngine
from utils.time_utils import get_utc_now, is_market_open

from config.settings import ASSET_CONFIG
CONFIG = ASSET_CONFIG["XAUUSD"]

async def check_market():
    """
    Protocol 7.1 Compliant Strategy (Defensive)
    - Validates Data integrity (NaN checks)
    - Checks Broker Limits
    - Manages State (Scanning vs Managing)
    """
    
    # 1. SESSION CHECK
    is_open, reason = is_market_open("XAUUSD")
    if not is_open:
        print(f">>> 🌍 XAUUSD: 💤 Market Closed ({reason})")
        return

    print(f"\n>>> 🌍 PIPELINE: XAUUSD (Global Spot) <<<")
    
    # 2. LOAD DATA
    if not os.path.exists(CONFIG["data_file"]):
        print(f"❌ Waiting for XAUUSD data stream...")
        return

    # --- START OF MAIN TRY BLOCK ---
    try:
        df = pd.read_csv(CONFIG["data_file"])
        
        # PROTOCOL 7.1: DATA VALIDATION
        if df is None or len(df) < 2:
            print("⏳ Gathering market depth...")
            return
            
        current_row = df.iloc[-1]
        
        # Guard against NaN (Not a Number)
        if pd.isna(current_row['Close']):
            print("⚠️ Critical: Price is NaN. Skipping cycle.")
            return
            
        price = float(current_row['Close'])
        
        # Double check conversion
        if price <= 0:
            print("⚠️ Critical: Invalid Price (<= 0). Skipping.")
            return
        
        # 3. SYNCHRONIZE STATE
        broker = PaperBroker()
        
        # PROTOCOL 7.1: Check Limits with Valid Price
        broker.check_limits(price, "XAUUSD")
        
        account_state = broker.get_positions()
        current_pos = account_state['position']
        pending_orders = account_state['orders']
        
        print(f"📊 Price: ${price:,.2f} | 💰 Equity: ${account_state['equity']:,.2f}")
        if pending_orders:
            print(f"   📝 Pending Orders: {len(pending_orders)}")

        # --- STATE MACHINE ---
        if current_pos == "FLAT":
            if not pending_orders:
                print("   🔍 STATE: SCANNING")
                
                # Entry Logic
                if price < 2600:
                    print("   ✨ SIGNAL: BUY Condition Met")
                    sl_pips = 50  
                    tp_pips = 100 
                    sl_price, tp_price = GoldPricingEngine.calculate_sl_tp(price, 1, sl_pips, tp_pips)
                    
                    limit_entry = price - 1.00
                    
                    broker.place_order(
                        action=1, 
                        symbol="XAUUSD", 
                        price=limit_entry,
                        qty=0.1, 
                        type="LIMIT",
                        tif="DAY",
                        sl=sl_price, 
                        tp=tp_price,
                        date=get_utc_now()
                    )
            else:
                limit_price = pending_orders[0]['limit_price']
                print(f"   ⏳ STATE: WAITING (Limit Order Pending @ {limit_price})")

        else:
            entry_price = current_pos['entry_price']
            print(f"   🛡️ STATE: MANAGING (Holding LONG @ {entry_price})")

    # --- END OF MAIN TRY BLOCK (The Missing Piece) ---
    except Exception as e:
        print(f"⚠️ Strategy Error: {e}")