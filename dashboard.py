import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Gold Bot V2 Command Center", layout="wide", page_icon="🧠")
DATA_FILE = 'data/MCX_gold_daily.csv'
STATE_FILE = 'paper_state_mcx.json'

# --- TITLE ---
st.title("🧠 AI Gold Bot V2 - Command Center")
st.markdown("Monitoring **Price Action** + **RSI Momentum** in Real-Time")

# --- HELPER FUNCTIONS ---
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Calculate RSI for Visualization
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
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
metrics_container = st.container()
charts_container = st.container()

while True:
    # 1. LOAD DATA
    df = load_data()
    state = load_state()
    
    if df is not None and state is not None:
        last_row = df.iloc[-1]
        last_price = last_row['close']
        last_rsi = last_row['rsi']
        
        # Position Logic
        pos_data = state.get('position', 'FLAT')
        equity = state.get('equity', 0)
        
        pnl = 0.0
        pnl_pct = 0.0
        pos_status = "⚪ FLAT"
        
        if isinstance(pos_data, dict):
            entry_price = pos_data.get('entry_price', 0)
            pnl = (last_price - entry_price) * 10
            pnl_pct = ((last_price - entry_price) / entry_price) * 100
            pos_status = f"🟢 LONG (@ ₹{entry_price:,.0f})"

        # 2. METRICS
        with metrics_container:
            metrics_container.empty()
            c1, c2, c3, c4 = st.columns(4)
            
            c1.metric("💰 Total Equity", f"₹{equity:,.2f}")
            c2.metric("📊 Market Price", f"₹{last_price:,.2f}")
            
            # Color RSI based on Danger Zones
            rsi_color = "normal"
            if last_rsi > 70: rsi_color = "off" # Red/High
            elif last_rsi < 30: rsi_color = "inverse" # Green/Low
            c3.metric("🧠 RSI Strength", f"{last_rsi:.1f}", delta_color=rsi_color)
            
            c4.metric("Unrealized P&L", f"₹{pnl:,.2f}", f"{pnl_pct:.2f}%")

        # 3. CHARTS (Price + RSI)
        with charts_container:
            charts_container.empty()
            
            # Create a chart with 2 rows (Price on top, RSI on bottom)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                vertical_spacing=0.05, row_heights=[0.7, 0.3])

            # Row 1: Candlestick Price
            fig.add_trace(go.Candlestick(x=df['timestamp'],
                            open=df['open'], high=df['high'],
                            low=df['low'], close=df['close'], name='Gold'), row=1, col=1)

            # Add Entry Line if Long
            if isinstance(pos_data, dict):
                fig.add_hline(y=entry_price, line_dash="dash", line_color="green", row=1, col=1)

            # Row 2: RSI Line
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['rsi'], 
                                     line=dict(color='purple', width=2), name='RSI'), row=2, col=1)
            
            # RSI Danger Zones (70 and 30)
            fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)

            fig.update_layout(title="Market Analysis (Price + Brain)", height=600, xaxis_rangeslider_visible=False)
            
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("Waiting for data stream...")

    time.sleep(10)
    st.rerun()
