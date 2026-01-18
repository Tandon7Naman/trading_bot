import pandas as pd
import numpy as np
import os
from stable_baselines3 import PPO
from datetime import datetime
from execution.paper_broker import PaperBroker  # <--- V3 Connection

# --- CONFIGURATION ---
DATA_FILE = 'data/MCX_gold_daily.csv'
MODEL_PATH = "models/ppo_gold_agent"

# --- INDICATORS ---
def add_indicators(df):
    df = df.copy()
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()
    return df

# --- MAIN STRATEGY LOOP ---
async def check_market():
    # V3 HEADER
    print(f"\n============================================================")
    print(f"STRATEGY: GOLD SCALPER (V3 - Broker Integrated)")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"============================================================")
    
    # 1. Load Market Data
    if not os.path.exists(DATA_FILE):
        print(f"❌ Waiting for data feed...")
        return
        
    df = pd.read_csv(DATA_FILE)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    if len(df) < 55:
        print(f"⏳ Gathering data... ({len(df)}/55 rows needed)")
        return

    df = add_indicators(df)
    current_row = df.iloc[-1]
    
    # 2. Connect to Broker
    broker = PaperBroker()
    account = broker.get_account_info()
    
    print(f"💰 Equity: ₹{account['equity']:,.2f}")
    print(f"📊 Price: ₹{current_row['close']:,.2f} | RSI: {current_row['rsi']:.1f}")

    # 3. AI Prediction
    obs = np.array([
        current_row['close'], current_row['rsi'],
        current_row['macd'], current_row['macd_signal'],
        current_row['sma_50']
    ], dtype=np.float32)

    try:
        model = PPO.load(MODEL_PATH)
        action, _ = model.predict(obs)
    except Exception as e:
        print(f"❌ Brain Error: {e}")
        return

    # 4. Order Execution
    if action == 1: # BUY
        if account['position'] == "FLAT":
            broker.place_order(1, "MCX", current_row['close'], 10, date=current_row['timestamp'], rsi=current_row['rsi'])
        else:
            print("   (AI says BUY, but Broker reports LONG)")

    elif action == 2: # SELL
        if isinstance(account['position'], dict):
            broker.place_order(2, "MCX", current_row['close'], 10, date=current_row['timestamp'], rsi=current_row['rsi'])
        else:
            print("   (AI says SELL, but Broker reports FLAT)")
    else:
        print("   (AI says HOLD)")