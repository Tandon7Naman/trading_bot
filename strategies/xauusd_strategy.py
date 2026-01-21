import pandas as pd
import numpy as np
import asyncio
from datetime import datetime

from execution.paper_broker import PaperBroker # Use MT5Broker for Live
from execution.risk_manager import RiskManager, CircuitBreaker
from execution.db_manager import DBManager
from execution.journal_manager import JournalManager
from strategies.sentiment_engine import SentimentEngine
from strategies.market_structure import MarketStructure
from strategies.wyckoff import WyckoffAnalyzer
from execution.calendar_filter import NewsFilter
from utils.exceptions import NewsEventError
from config.settings import ASSET_CONFIG, STRATEGY_CONFIG, EXECUTION_CONFIG

SYSTEM_BREAKER = None

# --- PROTOCOL 5.1: COOLDOWN ---
def check_cooldown(db_manager, symbol):
    conn = db_manager._get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT exit_time FROM trades WHERE symbol=? AND status='CLOSED' ORDER BY exit_time DESC LIMIT 1", (symbol,))
    row = cursor.fetchone()
    conn.close()
    
    if row and row[0]:
        last_exit = datetime.fromisoformat(row[0])
        now = datetime.now()
        diff_mins = (now - last_exit).total_seconds() / 60
        wait = STRATEGY_CONFIG['cooldown_minutes']
        if diff_mins < wait:
            return False, f"Cooldown ({int(wait - diff_mins)}m left)"
    return True, "Ready"

def get_current_portfolio_risk(db_manager, config):
    # Calculate total $ risk of open trades
    pos = db_manager.get_open_position("XAUUSD")
    if pos != "FLAT":
        risk_usd = abs(pos['entry_price'] - pos['sl']) * pos['qty'] * config['contract_size']
        return risk_usd
    return 0.0

async def check_market(data_handler):
    global SYSTEM_BREAKER
    
    # 1. SETUP
    broker = PaperBroker() # <--- Change to MT5Broker() for Live
    db = DBManager()
    
    # Startup Safety
    account = broker.get_positions()
    equity = account['equity']
    
    if SYSTEM_BREAKER is None: SYSTEM_BREAKER = CircuitBreaker(initial_equity=equity)
    is_healthy, reason = SYSTEM_BREAKER.check_health(equity)
    if not is_healthy: print(f"🚨 CRITICAL: {reason}"); return 
    
    try: NewsFilter.can_trade("XAUUSD")
    except NewsEventError: return 

    # 2. DATA
    df = await data_handler.get_latest()
    if df is None or len(df) < 55: return 

    # 3. ANALYSIS
    df['SMA_50'] = df['Close'].rolling(50).mean()
    price = float(df.iloc[-1]['Close'])
    
    # Market Structure & Sentiment
    is_liquid, _ = MarketStructure.check_liquidity(df, price)
    if not is_liquid: return
    regime, adx = MarketStructure.get_regime(df)
    sentiment_score, sentiment_label = SentimentEngine.analyze_sentiment("XAUUSD")
    
    current_pos = account['position']
    print(f"📊 Price: ${price:,.2f} | Regime: {regime} | Sentiment: {sentiment_label}")

    # 4. TRADING LOGIC
    if current_pos == "FLAT":
        # Cooldown Check
        is_ready, cool_msg = check_cooldown(db, "XAUUSD")
        if not is_ready: 
            print(f"   🧘 PATIENCE: {cool_msg}")
            return

        # Wyckoff Logic
        has_sc, sc_low, sc_vol, _ = WyckoffAnalyzer.find_selling_climax(df)
        if has_sc:
            is_spring, _ = WyckoffAnalyzer.detect_spring(df.iloc[-1], sc_low, sc_vol)
            if is_spring:
                print(f"   ✨ SIGNAL: Wyckoff Spring!")
                
                # AI Veto
                if sentiment_label == "BEARISH":
                    print("   🛑 VETO: Sentiment Bearish.")
                    return 

                # Execution Setup
                sl_price = df.iloc[-1]['Low'] - 2.0
                tp_price = price + (price - sl_price) * 3
                
                # Fat Finger Check
                if price > (price * 1.05): return # 5% deviation
                
                # Risk Calc
                config = ASSET_CONFIG["XAUUSD"]
                risk_load = get_current_portfolio_risk(db, config)
                qty = RiskManager.calculate_lot_size(equity, price, sl_price, "XAUUSD", 2.0, risk_load)
                
                if qty > 0:
                    broker.place_order(1, "XAUUSD", price, qty, sl=sl_price, tp=tp_price)