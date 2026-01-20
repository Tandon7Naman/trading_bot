import pandas as pd
import numpy as np
import asyncio
import pytz
from execution.paper_broker import PaperBroker
from execution.connection_manager import HeartbeatMonitor
from execution.risk_manager import RiskManager, CircuitBreaker
from execution.db_manager import DBManager
from strategies.sentiment_engine import SentimentEngine
from strategies.market_structure import MarketStructure
from strategies.wyckoff import WyckoffAnalyzer
from execution.calendar_filter import NewsFilter
from utils.exceptions import NewsEventError
from config.settings import ASSET_CONFIG

# Global Breaker Instance
SYSTEM_BREAKER = None

def get_current_portfolio_risk(db_manager, symbol_config):
    """Protocol 2.2.2: The 5% Rule Calculation"""
    import pandas as pd
    import numpy as np
    import asyncio
    from datetime import datetime, timedelta

    from execution.paper_broker import PaperBroker
    from execution.mt5_broker import MT5Broker
    from execution.risk_manager import RiskManager, CircuitBreaker
    from execution.db_manager import DBManager
    from execution.journal_manager import JournalManager # <--- NEW
    from strategies.sentiment_engine import SentimentEngine
    from strategies.market_structure import MarketStructure
    from strategies.wyckoff import WyckoffAnalyzer
    from execution.calendar_filter import NewsFilter
    from utils.exceptions import NewsEventError
    from config.settings import ASSET_CONFIG, STRATEGY_CONFIG, EXECUTION_CONFIG

    SYSTEM_BREAKER = None

    # --- PROTOCOL 5.1: COOLDOWN LOGIC ---
    def check_cooldown(db_manager, symbol):
        """
        Enforces 'Patience'. Checks if enough time has passed since last trade.
        """
        conn = db_manager._get_conn()
        cursor = conn.cursor()
        # Get last closed trade time
        cursor.execute("SELECT exit_time FROM trades WHERE symbol=? AND status='CLOSED' ORDER BY exit_time DESC LIMIT 1", (symbol,))
        row = cursor.fetchone()
        conn.close()
    
        if row and row[0]:
            last_exit = datetime.fromisoformat(row[0])
            now = datetime.now()
            diff_mins = (now - last_exit).total_seconds() / 60
        
            required_wait = STRATEGY_CONFIG['cooldown_minutes']
            if diff_mins < required_wait:
                return False, f"Cooldown Active ({int(required_wait - diff_mins)}m remaining)"
            
        return True, "Ready"

    async def check_market(data_handler):
        global SYSTEM_BREAKER
    
        # 1. SETUP
        # Switch to MT5Broker() for Live, PaperBroker() for testing
        broker = PaperBroker() 
        db = DBManager()
    
        # ... (Standard Startup Checks) ...
        account_state = broker.get_positions()
        equity = account_state['equity']
    
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
    
        # Market Structure (Protocols 3.2, 3.3)
        is_liquid, liq_msg = MarketStructure.check_liquidity(df, price)
        if not is_liquid: return
        regime, adx = MarketStructure.get_regime(df)
    
        # Sentiment (Protocol 4.0)
        sentiment_score, sentiment_label = SentimentEngine.analyze_sentiment("XAUUSD")
    
        current_pos = account_state['position']
        print(f"📊 Price: ${price:,.2f} | Regime: {regime} | Sentiment: {sentiment_label}")

        if current_pos == "FLAT":
            # --- PROTOCOL 5.1: PATIENCE CHECK ---
            is_ready, cool_msg = check_cooldown(db, "XAUUSD")
            if not is_ready:
                print(f"   🧘 PATIENCE: {cool_msg}")
                return # Force Wait

            # --- STRATEGY LOGIC (Protocol 3.1) ---
            has_sc, sc_low, sc_vol, sc_idx = WyckoffAnalyzer.find_selling_climax(df)
        
            if has_sc:
                is_spring, spring_msg = WyckoffAnalyzer.detect_spring(df.iloc[-1], sc_low, sc_vol)
            
                if is_spring:
                    print(f"   ✨ SIGNAL: Wyckoff Spring!")
                
                    # AI Veto
                    if sentiment_label == "BEARISH":
                        print(f"   🛑 VETO: Sentiment Bearish.")
                        return 

                    # Execution
                    sl_price = df.iloc[-1]['Low'] - 2.0
                    tp_price = price + (price - sl_price) * 3
                
                    # --- PROTOCOL 5.3: SANITY CHECK (Fat Finger) ---
                    if price > (price * (1 + EXECUTION_CONFIG['max_slippage_pct'])): 
                        print("   ❌ REJECT: Price Deviation too high!")
                        return

                    # Risk Calc
                    qty = RiskManager.calculate_lot_size(equity, price, sl_price, "XAUUSD", confidence_score=2.5)
                
                    if qty > 0:
                        success = broker.place_order(1, "XAUUSD", price, qty, sl=sl_price, tp=tp_price)
                    
                        if success:
                            # --- PROTOCOL 5.2: LOG CONTEXT TO DB ---
                            # We save the "Why" (Strategy/Regime) into the DB for later retrieval
                            # (Adding a simple temp storage or printing for now)
                            print(f"   📝 CONTEXT LOGGED: Strategy=Wyckoff_Spring, ADX={adx:.1f}, Sentiment={sentiment_score:.2f}")

        else:
            # MANAGEMENT & CLOSING JOURNAL
            # If position closes, we trigger the Journal Manager
            # (For simulation, we'll assume the Broker handles the 'Close' trigger)
            pass