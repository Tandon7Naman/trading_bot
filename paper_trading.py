#!/usr/bin/env python3
"""
GLD Paper Trading - Simplified, robust version
"""

import os
import json
from pathlib import Path
import pandas as pd
import numpy as np
import pickle

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "GLD_daily.csv"
SCALER_PATH = BASE_DIR / "models" / "gld_scaler.pkl"
STATE_PATH = BASE_DIR / "paper_state_gld.json"
LOGS_DIR = BASE_DIR / "logs"
EQUITY_LOG = LOGS_DIR / "paper_equity.csv"

INITIAL_EQUITY = 500_000.0
SL_PCT = 0.01
TP_PCT = 0.035
TIME_STOP = 20

def load_state():
    if STATE_PATH.exists():
        with open(STATE_PATH) as f:
            return json.load(f)
    return {"equity": INITIAL_EQUITY, "position": None, "entry_price": None, "entry_date": None, "bars_held": 0}

def save_state(state):
    with open(STATE_PATH, 'w') as f:
        json.dump(state, f, indent=2, default=str)

def main():
    LOGS_DIR.mkdir(exist_ok=True)
    
    # Load data
    df = pd.read_csv(DATA_PATH)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Get last bar
    bar = df.iloc[-1]
    ts = bar['timestamp']
    price = bar['close']
    
    # Load state
    state = load_state()
    equity = state['equity']
    position = state['position']
    entry_price = state.get('entry_price')
    entry_date = state.get('entry_date')
    bars_held = state.get('bars_held', 0)
    
    # Validate entry_price (should not be NaN)
    if pd.isna(entry_price):
        entry_price = None
    
    # === FIX: Validate state consistency ===
    if position is not None and (entry_price is None or pd.isna(entry_price)):
        print(f"⚠ WARNING: Position {position} but entry_price is {entry_price}. Resetting to FLAT.")
        position = None
        entry_price = None
        entry_date = None
        bars_held = 0
    
    # === POSITION LOGIC ===
    if position is None:
        # Flat: use random signal for now
        signal = np.random.randint(0, 2)
        if signal == 1:
            position = "LONG"
            entry_price = float(price)
            entry_date = str(ts)
            bars_held = 0
            print(f"🟢 BUY @ {price:.2f}")
    else:
        # In position: check exits
        bars_held += 1
        pnl_pct = (price - entry_price) / entry_price if entry_price else 0
        
        exit = False
        reason = ""
        if pnl_pct <= -SL_PCT:
            exit, reason = True, "SL"
        elif pnl_pct >= TP_PCT:
            exit, reason = True, "TP"
        elif bars_held >= TIME_STOP:
            exit, reason = True, "TIME"
        
        if exit:
            pnl = (price - entry_price) * 1
            equity += pnl
            print(f"🔴 SELL @ {price:.2f} ({reason}) | P&L: {pnl_pct*100:+.2f}%")
            position = None
            entry_price = None
            entry_date = None
            bars_held = 0
    
    # === LOG ===
    equity_row = pd.DataFrame([{'date': ts.date(), 'equity': equity, 'position': position or 'FLAT'}])
    if EQUITY_LOG.exists():
        equity_row.to_csv(EQUITY_LOG, mode='a', header=False, index=False)
    else:
        equity_row.to_csv(EQUITY_LOG, index=False)
    
    # === SAVE STATE ===
    state['equity'] = equity
    state['position'] = position
    state['entry_price'] = entry_price
    state['entry_date'] = entry_date
    state['bars_held'] = bars_held
    save_state(state)
    
    print(f"✓ GLD {ts.date()}: Equity ₹{equity:,.0f} | {position or 'FLAT'}")

if __name__ == "__main__":
    main()
