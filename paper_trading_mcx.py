#!/usr/bin/env python3
"""
Paper Trading Loop for MCX Gold.
This script simulates making a single trading decision based on the latest available data.
It loads the current position from a state file, gets the latest market data,
predicts a signal, and then decides whether to enter, exit, or hold a position.
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime

# --- Configuration ---
CSV_PATH = "data/MCX_gold_daily.csv"
MODEL_PATH = "models/lstm_mcx_traintest.h5"
SCALER_PATH = "models/scaler_mcx_traintest.pkl"
STATE_FILE = "paper_state_mcx.json"
TRADES_LOG = "logs/paper_trades_mcx.csv"
EQUITY_LOG = "logs/paper_equity_mcx.csv"
SYMBOL = "MCX:GOLD"
LOOKBACK_PERIOD = 30 # Should match the model's training

# --- Helper Functions ---

def load_state():
    """Loads the current trading state (position and equity)."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    else:
        # Default state if file doesn't exist
        return {"position": None, "equity": 500000.0}

def save_state(state):
    import numpy as np
    # Helper to convert fancy numpy numbers to normal numbers
    def convert(o):
        if isinstance(o, np.integer): return int(o)
        if isinstance(o, np.floating): return float(o)
        if isinstance(o, np.ndarray): return o.tolist()
        raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4, default=convert)

def log_trade(trade_details):
    """Appends a completed trade to the trades log CSV."""
    log_df = pd.DataFrame([trade_details])
    if not os.path.exists(TRADES_LOG):
        log_df.to_csv(TRADES_LOG, index=False)
    else:
        log_df.to_csv(TRADES_LOG, mode='a', header=False, index=False)

def log_equity(timestamp, equity):
    """Appends the current equity to the equity log CSV."""
    log_df = pd.DataFrame([{"timestamp": timestamp, "equity": equity}])
    if not os.path.exists(EQUITY_LOG):
        log_df.to_csv(EQUITY_LOG, index=False)
    else:
        log_df.to_csv(EQUITY_LOG, mode='a', header=False, index=False)

def get_signal(df, model, scaler):
    """Gets a trading signal from the latest data."""
    if len(df) < LOOKBACK_PERIOD:
        print("Not enough data to generate a signal.")
        return 0 # Hold signal

    # Extract the last `LOOKBACK_PERIOD` rows for prediction
    window = df.iloc[-LOOKBACK_PERIOD:][['open', 'high', 'low', 'close']].values
    window_scaled = scaler.transform(window)
    window_scaled = window_scaled.astype(np.float32)
    window_scaled = np.expand_dims(window_scaled, axis=0)
    
    prediction = model.predict(window_scaled, verbose=0)[0][0]
    signal = 1 if prediction > 0.5 else 0 # 1 for Buy/Hold, 0 for Sell/Exit
    return signal

# --- Main Execution ---

def run_paper_trade():
    """Main paper trading logic."""
    print("=" * 60)
    print(f"PAPER TRADING BOT - {SYMBOL}")
    print(f"Timestamp: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("=" * 60)

    # 1. Load necessary files
    model = None
    scaler = None
    df = None
    use_model = False
    try:
        # Suppress TensorFlow warnings
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
        from tensorflow.keras.models import load_model
        model = load_model(MODEL_PATH)
        with open(SCALER_PATH, 'rb') as f:
            scaler = pickle.load(f)
        
        df = pd.read_csv(CSV_PATH, parse_dates=['timestamp'])
        df.sort_values('timestamp', inplace=True)
        print("✓ Model, scaler, and data loaded successfully.")
        use_model = True
    except Exception as e:
        print(f"✗ WARNING: Could not load model. Falling back to random signals. Details: {e}")
        # Still try to load data for pricing
        try:
            df = pd.read_csv(CSV_PATH, parse_dates=['timestamp'])
            df.sort_values('timestamp', inplace=True)
            print("✓ Data loaded successfully.")
        except Exception as data_e:
            print(f"✗ FATAL: Could not load data file. Aborting. Details: {data_e}")
            return

    # 2. Load current state
    state = load_state()
    position = state.get('position')
    equity = state.get('equity')
    print(f"Current Equity: ₹{equity:,.2f}")
    if position:
        print(f"Current Position: LONG since {position['entry_date']} at ₹{position['entry_price']:,}")
    else:
        print("Current Position: FLAT")

    # 3. Get the latest data and signal
    latest_bar = df.iloc[-1]
    
    signal = 0 # Default to sell/exit
    if use_model:
        signal = get_signal(df, model, scaler)
    else:
        signal = np.random.randint(0, 2) # Random signal if model failed
        print("Using random signal due to model load failure.")

    print(f"Latest Data Date: {latest_bar['timestamp'].date()}")
    print(f"Latest Close Price: ₹{latest_bar['close']:,.2f}")
    print(f"Model Signal: {'BUY/HOLD' if signal == 1 else 'SELL/EXIT'}")

    # 4. Execute trading logic
    # If we have a position...
    if position:
        # And signal is SELL, then close the position
        if signal == 0:
            exit_price = latest_bar['close']
            pnl = exit_price - position['entry_price']
            new_equity = equity + pnl
            
            print(f"-> EXIT SIGNAL: Closing LONG position at ₹{exit_price:,.2f}")
            print(f"   P&L for this trade: ₹{pnl:,.2f}")
            
            log_trade({
                "entry_date": position['entry_date'],
                "entry_price": position['entry_price'],
                "exit_date": latest_bar['timestamp'].strftime('%Y-%m-%d'),
                "exit_price": exit_price,
                "pnl": pnl
            })
            
            state['position'] = None
            state['equity'] = new_equity
        else:
            # HOLD signal, do nothing
            print("-> HOLD SIGNAL: Maintaining LONG position.")
            
    # If we are flat...
    else:
        # And signal is BUY, then open a position
        if signal == 1:
            entry_price = latest_bar['close']
            print(f"-> ENTRY SIGNAL: Opening new LONG position at ₹{entry_price:,.2f}")
            state['position'] = {
                "entry_date": latest_bar['timestamp'].strftime('%Y-%m-%d'),
                "entry_price": entry_price
            }
        else:
            # EXIT signal, do nothing
            print("-> EXIT SIGNAL: No position to close. Staying FLAT.")

    # 5. Log equity and save state for next run
    log_equity(latest_bar['timestamp'], state['equity'])
    save_state(state)
    print(f"New Equity: ₹{state['equity']:,.2f}")
    print("State saved. Run complete.")
    print("=" * 60)


if __name__ == "__main__":
    # Ensure log directory exists
    os.makedirs("logs", exist_ok=True)
    run_paper_trade()
