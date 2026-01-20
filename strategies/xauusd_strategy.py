
import pandas as pd
import numpy as np
import os
import sys # <--- Needed to kill the process
import asyncio
import pytz
from execution.paper_broker import PaperBroker
from execution.connection_manager import HeartbeatMonitor
from execution.risk_manager import RiskManager, CircuitBreaker # <--- NEW
from execution.calendar_filter import NewsFilter
from utils.exceptions import NewsEventError
from strategies.pricing import GoldPricingEngine
from utils.time_utils import get_utc_now, is_market_open
from config.settings import ASSET_CONFIG
from execution.telegram_alerts import send_telegram_message # <--- NEW

# Global Breaker Instance (Persists across async loops)
SYSTEM_BREAKER = None

async def check_market(data_handler):
    """
    Protocol 7.2 Compliant Strategy.
    Includes Circuit Breaker for Catastrophic Loss Protection.
    """
    global SYSTEM_BREAKER
    
    # 1. SETUP BROKER & BREAKER
    broker = PaperBroker()
    account_state = broker.get_positions()
    equity = account_state['equity']
    
    if SYSTEM_BREAKER is None:
        print(f"🛡️ SAFETY: Initializing Circuit Breaker (Base: ${equity:,.2f})")
        SYSTEM_BREAKER = CircuitBreaker(initial_equity=equity)

    # 2. CHECK CIRCUIT BREAKER
    is_healthy, reason = SYSTEM_BREAKER.check_health(equity)
    if not is_healthy:
        msg = f"🚨 *CRITICAL ALERT* 🚨\n{reason}\n💀 KILL SWITCH ENGAGED."
        print(f"\n{msg}")
        send_telegram_message(msg) # <--- ALERT
        # Emergency Close Logic
        if account_state['position'] != "FLAT":
            pos = account_state['position']
            print(f"   🔻 Emergency Close: {pos['symbol']} {pos['qty']} Lots")
            broker.place_order(
                action=2 if pos['type'] == "LONG" else 1,
                symbol=pos['symbol'],
                price=account_state['position']['entry_price'], # Market order
                qty=pos['qty'],
                type="MARKET",
                date=get_utc_now()
            )
        print("🛑 SYSTEM SHUTDOWN.")
        sys.exit(1) # Hard Kill

    # 3. SESSION CHECK
    is_open, reason = is_market_open("XAUUSD")
    if not is_open:
        print(f">>> 🌍 XAUUSD: 💤 Market Closed ({reason})")
        return

    print(f"\n>>> 🌍 PIPELINE: XAUUSD (Global Spot) <<<")
    
    # 4. HEARTBEAT & NEWS
    try:
        is_alive, status = HeartbeatMonitor.check_heartbeat("XAUUSD", max_latency=120)
        if not is_alive:
            print(f"   🛑 HALT: {status}")
            return
        NewsFilter.can_trade("XAUUSD")
    except NewsEventError as e:
        print(f"   📰 NEWS SHIELD: Trading Paused. {e}")
        return 

    now_utc = get_utc_now()
    ist_tz = pytz.timezone('Asia/Kolkata')
    now_ist = now_utc.astimezone(ist_tz)
    print(f"   {status} | 🕒 {now_utc.strftime('%H:%M')} UTC / {now_ist.strftime('%H:%M')} IST")

    # 5. GET DATA
    df = await data_handler.get_latest()
    if df is None or len(df) < 15:
        print("⏳ Buffer Warming up (Need 15+ candles)...")
        return

    try:
        # Safe Init
        signal = "NEUTRAL"
        limit_entry = 0.0
        sl_price = 0.0
        tp_price = 0.0
        qty = 0.0
        
        # ATR Calculation
        df['High_Low'] = df['High'] - df['Low']
        df['High_Close'] = abs(df['High'] - df['Close'].shift(1))
        df['Low_Close'] = abs(df['Low'] - df['Close'].shift(1))
        df['TR'] = df[['High_Low', 'High_Close', 'Low_Close']].max(axis=1)
        df['ATR'] = df['TR'].rolling(window=14).mean()
        
        current_row = df.iloc[-1]
        if pd.isna(current_row['Close']): return
        
        price = float(current_row['Close'])
        current_atr = float(current_row['ATR']) if not pd.isna(current_row['ATR']) else 0.0
        
        current_pos = account_state['position']
        pending_orders = account_state['orders']
        
        print(f"📊 Price: ${price:,.2f} | 🌊 ATR: ${current_atr:.2f} | 💰 Equity: ${equity:,.2f}")

        # STATE MACHINE
        if current_pos == "FLAT":
            if not pending_orders:
                print("   🔍 STATE: SCANNING")
                
                if price < 2600:
                    signal = "BUY"
                
                if signal == "BUY":
                    print("   ✨ SIGNAL: BUY Condition Met")
                    sl_pips = 50  
                    tp_pips = 100 
                    
                    sl_price, tp_price = GoldPricingEngine.calculate_sl_tp(
                        price, 1, sl_pips, tp_pips, precision=2
                    )
                    
                    limit_entry = round(price - 1.00, 2)
                    
                    qty = RiskManager.calculate_lot_size(equity, limit_entry, sl_price, "XAUUSD", 0.02)
                    
                    if qty > 0:
                        broker.place_order(
                            action=1, symbol="XAUUSD", price=limit_entry, qty=qty, 
                            type="LIMIT", tif="DAY", sl=sl_price, tp=tp_price, 
                            atr=current_atr, date=get_utc_now()
                        )
            else:
                print(f"   ⏳ STATE: WAITING (Limit Order Pending)")
        else:
            print(f"   🛡️ STATE: MANAGING (Holding LONG)")

    except Exception as e:
        print(f"⚠️ Strategy Error: {e}")
        send_telegram_message(f"⚠️ *CRASH WARNING*\nStrategy Loop Failed:\n{str(e)}") # <--- ALERT