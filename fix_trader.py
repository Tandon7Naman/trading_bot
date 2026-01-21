# This file has been archived and is no longer in use.
# fix_trader.py
import os

code = r'''import pandas as pd
import numpy as np
import os
import json
import time
from stable_baselines3 import PPO
from datetime import datetime

# --- SETTINGS ---
DATA_FILE = 'data/MCX_gold_daily.csv'
STATE_FILE = 'paper_state_mcx.json'
MODEL_PATH = "models/ppo_gold_agent"
INITIAL_CAPITAL = 500000.0

# --- HELPER: CALCULATE INDICATORS LIVE ---
def add_indicators(df):
    df = df.copy()
    
    # 1. RSI (14)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # 2. MACD (12, 26, 9)
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    # 3. SMA (50)
    df['sma_50'] = df['close'].rolling(window=50).mean()
    
    return df

# --- HELPER: JSON CONVERTER ---
def convert(o):
    if isinstance(o, int): return int(o)
    if isinstance(o, float): return float(o)
    return o

# --- MAIN TRADING FUNCTION ---
def check_market():
    print(f"\n============================================================")
    print(f"PAPER TRADING BOT - MCX:GOLD (SMART V2)")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"============================================================")
    
    # 1. Load Data
    if not os.path.exists(DATA_FILE):
        print("❌ Waiting for data feed...")
        return
        
    df = pd.read_csv(DATA_FILE)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    if len(df) < 55:
        print(f"⏳ Gathering data... (Need 55 rows, have {len(df)})")
        return

    # 2. Add Indicators
    df = add_indicators(df)
    current_row = df.iloc[-1]
    
    obs = np.array([
        current_row['close'],
        current_row['rsi'],
        current_row['macd'],
        current_row['macd_signal'],
        current_row['sma_50']
    ], dtype=np.float32)
    
    current_price = current_row['close']
    current_date = current_row['timestamp']

    # 3. Load State (WITH SELF-REPAIR)
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
            # 🛠️ REPAIR: If keys are missing from old versions, add them now
            if 'history' not in state: state['history'] = []
            if 'equity' not in state: state['equity'] = INITIAL_CAPITAL
            if 'position' not in state: state['position'] = 'FLAT'
        except:
            state = {"equity": INITIAL_CAPITAL, "position": "FLAT", "history": []}
    else:
        state = {
            "equity": INITIAL_CAPITAL, 
            "position": "FLAT", 
            "history": []
        }

    # 4. Ask the Brain
    try:
        model = PPO.load(MODEL_PATH)
        action, _ = model.predict(obs)
    except Exception as e:
        print(f"❌ Brain Error: {e}")
        return

    # 5. Execute Logic
    position = state['position']
    equity = state['equity']
    trade_happened = False
    
    print(f"💰 Equity: ₹{equity:,.2f}")
    print(f"📊 Price: ₹{current_price:,.2f} | RSI: {current_row['rsi']:.1f}")
    
    if action == 1: # BUY
        if position == "FLAT":
            print("🚀 SIGNAL: BUY! (Entering Long)")
            state['position'] = {
                "type": "LONG",
                "entry_price": current_price,
                "entry_date": str(current_date),
                "qty": 10
            }
            try:
                from utils.notifier import TelegramNotifier
                import asyncio
                asyncio.run(TelegramNotifier.send_message(f"🚀 BUY SIGNAL\nPrice: ₹{current_price:.2f}\nRSI: {current_row['rsi']:.1f}"))
            except: pass
            trade_happened = True
        else:
            print("   (AI says BUY, but we are already Long. Holding.)")

    elif action == 2: # SELL
        if isinstance(position, dict):
            entry_price = position['entry_price']
            pnl = (current_price - entry_price) * 10
            equity += pnl
            
            print(f"🔻 SIGNAL: SELL! (Closing Long)")
            print(f"   Profit/Loss: ₹{pnl:,.2f}")
            
            state['equity'] = equity
            state['position'] = "FLAT"
            state['history'].append({
                "date": str(current_date),
                "pnl": pnl,
                "exit_price": current_price
            })
            
            try:
                from utils.notifier import TelegramNotifier
                emoji = "✅" if pnl > 0 else "❌"
                import asyncio
                asyncio.run(TelegramNotifier.send_message(f"{emoji} SELL SIGNAL\nP&L: ₹{pnl:.2f}\nExit: ₹{current_price:.2f}"))
            except: pass
            
            trade_happened = True
        else:
            print("   (AI says SELL, but we have no position. Waiting.)")
    
    else:
        print("   (AI says HOLD. No Action.)")

    # 6. Save State
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4, default=convert)
    
    if trade_happened:
        print("💾 Trade Saved.")
    print("============================================================")

if __name__ == "__main__":
    check_market()
'''

with open("paper_trading_mcx.py", "w", encoding="utf-8") as f:
    f.write(code)

print("✅ SUCCESS: paper_trading_mcx.py patched with Self-Repair logic.")
