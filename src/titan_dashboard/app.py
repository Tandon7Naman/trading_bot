
import time
import warnings

# Filter warnings immediately after import
warnings.filterwarnings("ignore")

# Then import Streamlit and others (ignore E402 error because this order is required)
import pandas as pd  # noqa: E402
import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402
from qdrant_client import QdrantClient  # noqa: E402

# --- CONFIG ---
st.set_page_config(page_title="Titan Cognitive Terminal", page_icon="🧠", layout="wide")
REFRESH_RATE = 2 # Seconds

# --- CONNECT TO MEMORY ---
@st.cache_resource
def get_qdrant_client():
    return QdrantClient(url="http://localhost:6333")

client = get_qdrant_client()

def load_memory():
    """Fetch the latest 100 market memories from Qdrant"""
    try:
        # We scroll through the collection to get the latest items
        records, _ = client.scroll(
            collection_name="market_news_history",
            limit=100,
            with_payload=True
        )

        data = []
        for record in records:
            payload = record.payload
            data.append({
                "Symbol": payload.get("symbol"),
                "Sentiment": payload.get("sentiment"),
                "Headline": payload.get("text"),
                "Timestamp": payload.get("timestamp"),
                "Source": payload.get("source")
            })

        df = pd.DataFrame(data)
        if not df.empty:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            df = df.sort_values(by='Timestamp', ascending=False)
        return df
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return pd.DataFrame()

# --- UI LAYOUT ---
st.title("🧠 Titan Cognitive Terminal")
st.markdown("Real-time NLP Analysis & Semantic Memory Stream")

# Auto-Refresh Loop
placeholder = st.empty()

while True:
    df = load_memory()

    with placeholder.container():
        if df.empty:
            st.warning("Waiting for data... Ensure 'main_brain.py' is running.")
        else:
            # 1. METRICS ROW
            col1, col2, col3, col4 = st.columns(4)

            # Calc metrics
            avg_sentiment = df['Sentiment'].mean()
            bullish_count = df[df['Sentiment'] > 0.5].shape[0]
            bearish_count = df[df['Sentiment'] < -0.5].shape[0]
            latest_symbol = df.iloc[0]['Symbol']

            col1.metric("Market Sentiment (Avg)", f"{avg_sentiment:.2f}", delta_color="normal")
            col2.metric("Bullish Signals", bullish_count, delta_color="off")
            col3.metric("Bearish Signals", bearish_count, delta_color="off")
            col4.metric("Latest Activity", latest_symbol)

            # 2. CHARTS ROW
            c1, c2 = st.columns([2, 1])

            with c1:
                st.subheader("Sentiment Momentum")
                # Group by time to show trend
                df_chart = df.copy()
                df_chart['Time'] = df_chart['Timestamp'].dt.strftime('%H:%M:%S')
                fig = px.bar(
                    df_chart.head(50),
                    x="Time",
                    y="Sentiment",
                    color="Sentiment",
                    color_continuous_scale=["red", "gray", "green"],
                    range_y=[-1, 1],
                    title="Real-Time Sentiment Impact"
                )
                st.plotly_chart(fig, use_container_width=True, key=f"main_chart_{time.time()}")

            with c2:
                st.subheader("Topic Distribution")
                pie_fig = px.pie(df, names='Symbol', title="News Volume by Asset", hole=0.4)
                st.plotly_chart(pie_fig, use_container_width=True, key=f"pie_chart_{time.time()}")

            # 3. NEWS FEED
            st.subheader("🔴 Live Cognitive Feed")

            # Format dataframe for display
            display_df = df[['Timestamp', 'Symbol', 'Sentiment', 'Headline']].head(20)

            # Color code the sentiment column
            def color_sentiment(val):
                color = 'red' if val < -0.5 else 'green' if val > 0.5 else 'gray'
                return f'color: {color}'

            st.dataframe(
                display_df.style.map(color_sentiment, subset=['Sentiment']),
                use_container_width=True,
                height=600
            )

    time.sleep(REFRESH_RATE)
