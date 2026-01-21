import streamlit as st
import pandas as pd
import json
import os
import time
from datetime import datetime, timezone
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config.settings import ASSET_CONFIG

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Gold Bot Command Center",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR "PRO" LOOK ---
st.markdown("""
    <style>
    .metric-card {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
    }
    .stMetric {
        background-color: transparent !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- AUTO-REFRESH MECHANISM ---
# Uses st.rerun() for native refreshing every 3 seconds
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 3:
    st.session_state.last_refresh = time.time()
    st.rerun()

# --- DATA LOADERS ---
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
            if 'Datetime' in df.columns:
                df['Datetime'] = pd.to_datetime(df['Datetime'])
            return df
        except:
            return pd.DataFrame()
    return pd.DataFrame()

# --- LOAD DATA ---
state = load_state()
df = load_market_data()

# --- CALCULATE KPIS ---
equity = state.get('equity', 0) if state else 0
history = state.get('history', []) if state else []
position = state.get('position', 'FLAT') if state else 'FLAT'

total_trades = len(history)
total_pnl = sum([t['pnl'] for t in history])
wins = len([t for t in history if t['pnl'] > 0])
losses = len([t for t in history if t['pnl'] <= 0])
win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0

# Calculate Profit Factor
gross_profit = sum([t['pnl'] for t in history if t['pnl'] > 0])
gross_loss = abs(sum([t['pnl'] for t in history if t['pnl'] < 0]))
profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0.0

# --- SIDEBAR ---
with st.sidebar:
    st.title("🤖 Bot Control")
    st.markdown("---")
    
    # Status Indicator
    if position == "FLAT":
        st.success("🟢 SCANNING MARKET")
    else:
        st.warning(f"🟠 IN TRADE ({position['type']})")
    
    st.metric("💰 Virtual Equity", f"${equity:,.2f}", delta=f"${total_pnl:,.2f}")
    
    st.markdown("---")
    st.markdown("### ⚙️ Engine Stats")
    st.text(f"Queue: XAUUSD")
    st.text(f"Latency: < 50ms")
    
    st.markdown("---")
    if st.button("🔄 Force Reload"):
        st.cache_data.clear()
        st.rerun()

# --- MAIN DASHBOARD ---
st.title("🏆 XAUUSD Institutional Engine")

# 1. KPI ROW
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Win Rate", f"{win_rate:.1f}%", f"{wins}W - {losses}L")
kpi2.metric("Profit Factor", f"{profit_factor:.2f}")
kpi3.metric("Total Trades", f"{total_trades}")
kpi4.metric("Active Margin", f"${position['margin_locked']:,.2f}" if position != 'FLAT' else "$0.00")

st.markdown("---")

# 2. TABS LAYOUT
tab_live, tab_perf, tab_raw = st.tabs(["📈 Live Market", "📊 Performance Analysis", "💾 System State"])

with tab_live:
    col_chart, col_orders = st.columns([3, 1])
    
    with col_chart:
        if not df.empty:
            # Create Subplots (Price + Volume)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                vertical_spacing=0.03, row_heights=[0.7, 0.3])

            # Candlestick
            fig.add_trace(go.Candlestick(
                x=df['Datetime'] if 'Datetime' in df.columns else df.index,
                open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                name="XAUUSD"
            ), row=1, col=1)

            # SMA 50 (Technical Overlay)
            if len(df) > 50:
                sma50 = df['Close'].rolling(window=50).mean()
                fig.add_trace(go.Scatter(
                    x=df['Datetime'] if 'Datetime' in df.columns else df.index,
                    y=sma50, line=dict(color='orange', width=1), name="SMA 50"
                ), row=1, col=1)

            # Volume
            if 'Volume' in df.columns:
                fig.add_trace(go.Bar(
                    x=df['Datetime'] if 'Datetime' in df.columns else df.index,
                    y=df['Volume'], marker_color='rgba(100, 200, 255, 0.5)', name="Volume"
                ), row=2, col=1)

            # Draw Lines for Positions
            if position != 'FLAT':
                entry = position['entry_price']
                sl = position['sl']
                tp = position['tp']
                fig.add_hline(y=entry, line_dash="solid", line_color="blue", annotation_text="ENTRY", row=1, col=1)
                fig.add_hline(y=sl, line_dash="dot", line_color="red", annotation_text="SL", row=1, col=1)
                fig.add_hline(y=tp, line_dash="dot", line_color="green", annotation_text="TP", row=1, col=1)

            fig.update_layout(
                height=600, 
                title_text="XAUUSD Live Feed (1m)",
                xaxis_rangeslider_visible=False,
                template="plotly_dark",
                margin=dict(l=0, r=0, t=30, b=0)
            )
            
            # Using key to avoid warnings
            st.plotly_chart(fig, width='stretch', key="live_chart")
        else:
            st.info("Waiting for Data Feed connection...")

    with col_orders:
        st.subheader("Order Book")
        
        # Pending Orders
        pending = state.get('pending_orders', [])
        if pending:
            st.write(f"**Pending: {len(pending)}**")
            pending_df = pd.DataFrame(pending)
            st.dataframe(pending_df[['type', 'limit_price', 'qty']], hide_index=True, width='stretch')
        else:
            st.caption("No Active Limit Orders")
            
        st.markdown("---")
        
        # Recent Trades Mini-Log
        st.subheader("Recent Fills")
        if history:
            recents = pd.DataFrame(history).iloc[::-1].head(5)
            st.dataframe(recents[['exit', 'pnl']], hide_index=True, width='stretch')
        else:
            st.caption("No Recent Activity")

with tab_perf:
    if history:
        # PnL Curve
        pnl_df = pd.DataFrame(history)
        pnl_df['cumulative_pnl'] = pnl_df['pnl'].cumsum()
        pnl_df['trade_count'] = range(1, len(pnl_df) + 1)
        
        fig_pnl = go.Figure()
        fig_pnl.add_trace(go.Scatter(
            x=pnl_df['trade_count'], 
            y=pnl_df['cumulative_pnl'],
            mode='lines+markers',
            name='Equity Curve',
            line=dict(color='#00ff00', width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 255, 0, 0.1)'
        ))
        fig_pnl.update_layout(title="Equity Growth Curve", xaxis_title="Trade #", yaxis_title="PnL ($)", template="plotly_dark")
        st.plotly_chart(fig_pnl, width='stretch')
    else:
        st.info("Execute trades to view Performance Analytics.")

with tab_raw:
    col_json, col_config = st.columns(2)
    with col_json:
        st.subheader("System State (JSON)")
        st.json(state)
    with col_config:
        st.subheader("Asset Config")
        st.json(CONFIG)

# --- FOOTER ---
st.markdown("---")
st.caption(f"System Time (UTC): {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} | Protocol 7.2 Active")

# Auto-refresh logic at the bottom to keep loop tight
time.sleep(1) # Small sleep to prevent CPU spiking