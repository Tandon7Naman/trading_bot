import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Gold Bot Pro", layout="wide")
DATA_FILE = 'data/MCX_gold_daily.csv'
STATE_FILE = 'data/paper_state_mcx.json'

# --- LAYOUT ---
st.title("🏆 Gold Bot Professional Dashboard")
metrics = st.container()
charts = st.container()

# --- MAIN LOOP ---
while True:
    if os.path.exists(DATA_FILE) and os.path.exists(STATE_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            # Ensure timestamp is parsed so chart works
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            with open(STATE_FILE, 'r') as f: 
                state = json.load(f)
        except Exception as e:
            # If read fails (e.g. file busy), wait and retry
            time.sleep(1)
            continue
        
        # Extract Metrics
        last_price = df.iloc[-1]['close'] if not df.empty else 0
        equity = state.get('equity', 0)
        pos = state.get('position', 'FLAT')
        
        # 1. Update Metrics
        with metrics:
            metrics.empty()
            c1, c2, c3 = st.columns(3)
            c1.metric("Equity", f"₹{equity:,.2f}")
            c2.metric("Live Price", f"₹{last_price:,.2f}")
            
            status = "FLAT" if pos == "FLAT" else "🟢 LONG"
            c3.metric("Position", status)
            
        # 2. Update Chart
        with charts:
            charts.empty()
            if not df.empty:
                # Limit chart to last 100 candles for speed
                df_view = df.tail(100)
                
                fig = go.Figure(data=[go.Candlestick(x=df_view['timestamp'],
                    open=df_view['open'], close=df_view['close'],
                    high=df_view['high'], low=df_view['low'])])
                
                fig.update_layout(
                    height=500, 
                    title="Live Market Data (Last 100 ticks)",
                    xaxis_rangeslider_visible=False
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"Waiting for data stream... (Checking {DATA_FILE})")
    
    time.sleep(1)
    st.rerun()