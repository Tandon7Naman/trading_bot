import streamlit as st
import pandas as pd
import json
import os
import time
from datetime import datetime
import plotly.graph_objects as go
from config.settings import ASSET_CONFIG

# Page Config
st.set_page_config(
    page_title="Gold Bot Command Center",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- AUTO-REFRESH ---
# Refreshes the page every 3 seconds to show live updates
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=3000, key="dataframerefresh")

# --- LOAD DATA ---
STATE_FILE = 'data/paper_state_mcx.json'
CONFIG = ASSET_CONFIG["XAUUSD"]

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

def load_market_data():
    if os.path.exists(CONFIG["data_file"]):
        try:
            df = pd.read_csv(CONFIG["data_file"])
            return df
        except:
            return pd.DataFrame()
    return pd.DataFrame()

# --- SIDEBAR ---
st.sidebar.title("🤖 Bot Control")
st.sidebar.markdown("---")
state = load_state()

if state:
    equity = state.get('equity', 0)
    st.sidebar.metric(label="💰 Virtual Equity", value=f"${equity:,.2f}")
    
    pos = state.get('position', 'FLAT')
    if pos == "FLAT":
        st.sidebar.success("State: SCANNING")
    else:
        st.sidebar.warning(f"State: MANAGING ({pos['type']})")
        st.sidebar.markdown(f"**Entry:** ${pos['entry_price']}")
        st.sidebar.markdown(f"**Qty:** {pos['qty']}")

    st.sidebar.markdown("---")
    pending = state.get('pending_orders', [])
    st.sidebar.markdown(f"**Pending Orders:** {len(pending)}")

# --- MAIN DASHBOARD ---
st.title("🏆 XAUUSD Institutional Engine")

col1, col2 = st.columns([3, 1])

with col1:
    # CHARTING
    df = load_market_data()
    if not df.empty:
        # Simple Candle Chart
        fig = go.Figure(data=[go.Candlestick(
            x=pd.to_datetime(df['Datetime']) if 'Datetime' in df.columns else df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close']
        )])
        
        # Add Lines for Entry/SL/TP if position exists
        if state and state['position'] != 'FLAT':
            pos = state['position']
            entry = pos['entry_price']
            sl = pos['sl']
            tp = pos['tp']
            
            fig.add_hline(y=entry, line_dash="dash", line_color="blue", annotation_text="ENTRY")
            fig.add_hline(y=sl, line_dash="dot", line_color="red", annotation_text="SL")
            fig.add_hline(y=tp, line_dash="dot", line_color="green", annotation_text="TP")

        fig.update_layout(height=500, title="XAUUSD Live Feed (Paper)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Waiting for Data Feed...")

with col2:
    # ORDER BOOK / LOGS
    st.subheader("📜 Trade History")
    if state and 'history' in state:
        history_df = pd.DataFrame(state['history'])
        if not history_df.empty:
            # Sort by latest
            history_df = history_df.iloc[::-1]
            st.dataframe(history_df[['date', 'exit', 'pnl']], hide_index=True)
        else:
            st.text("No closed trades yet.")

    # PENDING ORDERS TABLE
    st.subheader("⏳ Active Limits")
    if state and 'pending_orders' in state:
        orders = state['pending_orders']
        if orders:
            st.table(pd.DataFrame(orders)[['type', 'limit_price', 'qty', 'tif']])
        else:
            st.caption("No pending orders.")

# Footer
st.markdown("---")
st.caption(f"System Time (UTC): {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")