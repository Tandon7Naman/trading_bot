import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Gold Bot Dashboard", layout="wide", page_icon="🏆")
DATA_FILE = 'data/MCX_gold_daily.csv'
STATE_FILE = 'paper_state_mcx.json'
EQUITY_LOG = 'logs/paper_equity_mcx.csv'

# --- TITLE ---
st.title("🤖 AI Gold Trading Bot - Live Command Center")

# --- HELPER FUNCTIONS ---
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    return None

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

# --- MAIN LAYOUT ---
# Create placeholders for auto-updating content
metrics_container = st.container()
charts_container = st.container()

while True:
    # 1. LOAD LATEST DATA
    df = load_data()
    state = load_state()
    
    if df is not None and state is not None:
        last_price = df.iloc[-1]['close']
        last_date = df.iloc[-1]['timestamp']
        
        # Calculate Position Status
        position_type = "FLAT"
        entry_price = 0
        pnl = 0.0
        pnl_pct = 0.0
        
        # Check if "position" is a dictionary (Active Trade) or string (Flat)
        # Your JSON has: "position": {"entry_price": ..., "entry_date": ...} OR "position": "FLAT"
        pos_data = state.get('position', 'FLAT')
        
        if isinstance(pos_data, dict):
            position_type = "LONG" # Assuming Long only for now
            entry_price = pos_data.get('entry_price', 0)
            pnl = last_price - entry_price
            pnl_pct = (pnl / entry_price) * 100
        
        equity = state.get('equity', 0)

        # 2. DISPLAY METRICS (Top Row)
        with metrics_container:
            # Clear previous content to avoid duplicates
            metrics_container.empty() 
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("💰 Total Capital", f"₹{equity:,.2f}")
            c2.metric("📊 Market Price", f"₹{last_price:,.2f}", f"{last_date.date()}")
            
            if position_type == "LONG":
                c3.metric("Current Position", "🟢 LONG", f"@ ₹{entry_price:,.0f}")
                c4.metric("Unrealized P&L", f"₹{pnl:,.2f}", f"{pnl_pct:.2f}%")
            else:
                c3.metric("Current Position", "⚪ FLAT")
                c4.metric("Unrealized P&L", "₹0.00")

        # 3. DISPLAY CHARTS
        with charts_container:
            charts_container.empty()
            
            # --- Chart 1: Price Action ---
            fig = go.Figure(data=[go.Candlestick(x=df['timestamp'],
                            open=df['open'], high=df['high'],
                            low=df['low'], close=df['close'], name='Gold Price')])
            
            # Add Entry Line if position is open
            if position_type == "LONG":
                fig.add_hline(y=entry_price, line_dash="dash", line_color="green", annotation_text="Entry")
                
            fig.update_layout(title="Gold Price Action (MCX)", height=500, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("Waiting for data... Ensure the bot is running!")

    # 4. AUTO-REFRESH LOGIC
    time.sleep(10) # Update every 10 seconds
    st.rerun()
