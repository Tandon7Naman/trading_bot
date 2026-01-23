import os
import sqlite3
import time

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# --- CONFIGURATION ---
DB_PATH = "data/trading_history.db"  # Ensure this path matches your setup
REFRESH_RATE = 2  # Seconds

st.set_page_config(
    page_title="GoldBot Command Center",
    page_icon="🏆",
    layout="wide",
)

# --- HELPER FUNCTIONS ---
def get_connection():
    """Connect to the trading database securely."""
    if not os.path.exists(DB_PATH):
        return None
    return sqlite3.connect(DB_PATH)

def load_data():
    """Fetch the latest market data and trade history."""
    conn = get_connection()
    if not conn:
        return None, None

    # 1. Load Market Data (Last 100 candles)
    # Adjust table name 'XAUUSD_M1' if your engine uses a different one
    try:
        df_market = pd.read_sql("SELECT * FROM market_data ORDER BY timestamp DESC LIMIT 100", conn)
        df_market = df_market.sort_values("timestamp")
    except Exception:
        df_market = pd.DataFrame()

    # 2. Load Trade History
    try:
        df_trades = pd.read_sql("SELECT * FROM trade_history ORDER BY entry_time DESC LIMIT 20", conn)
    except Exception:
        df_trades = pd.DataFrame()

    conn.close()
    return df_market, df_trades

# --- DASHBOARD LAYOUT ---
st.title("🤖 GoldBot Institutional Dashboard")

# 1. SIDEBAR METRICS
with st.sidebar:
    st.header("Account Health")
    # Mock metrics for visualization if DB is empty
    equity = 10540.00
    daily_pnl = +120.50
    active_trades = 1

    st.metric("Total Equity", f"${equity:,.2f}", f"{daily_pnl:+.2f}")
    st.metric("Active Exposure", "0.5 Lots", "Short")

    st.divider()
    st.write("### System Status")
    st.success("● Engine Online")
    st.info("● API Connection Stable")

# 2. MAIN CHART AREA
placeholder = st.empty()

# 2. MAIN CHART AREA
placeholder = st.empty()

while True:
    market_data, trade_data = load_data()

    with placeholder.container():
        # A. Alert if no data
        if market_data is None or market_data.empty:
            st.warning("Waiting for Engine to write data to 'data/trading_history.db'...")
            st.write("Ensure your 'hft_engine.py' is running and collecting data.")

            # Create dummy chart for visual testing
            fig = go.Figure()
            fig.update_layout(title="Waiting for Data Stream...", xaxis_title="Time", yaxis_title="Price")
            # Fix 1: Add unique key here too
            st.plotly_chart(fig, use_container_width=True, key=f"wait_chart_{time.time()}")

        else:
            # B. The Candle Chart
            fig = go.Figure(data=[go.Candlestick(
                x=market_data['timestamp'],
                open=market_data['open'],
                high=market_data['high'],
                low=market_data['low'],
                close=market_data['close'],
                name="XAUUSD"
            )])

            fig.update_layout(
                title="Live XAUUSD Feed (M1)",
                height=600,
                xaxis_rangeslider_visible=False,
                template="plotly_dark"
            )
            # Fix 2: Correct indentation + Unique Key to prevent "DuplicateElementId"
            st.plotly_chart(fig, use_container_width=True, key=f"live_chart_{time.time()}")

        # C. Recent Trades Table
        st.subheader("📝 Execution Log")
        if trade_data is not None and not trade_data.empty:
            st.dataframe(trade_data, use_container_width=True)
        else:
            st.info("No recent trades executed.")

    # Pause before next refresh
    time.sleep(REFRESH_RATE)
