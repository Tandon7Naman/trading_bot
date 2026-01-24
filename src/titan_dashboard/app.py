
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
    # Removed news/sentiment memory loading logic
    return pd.DataFrame()

# --- UI LAYOUT ---
st.title("🧠 Titan Cognitive Terminal")
st.markdown("Real-time NLP Analysis & Semantic Memory Stream")

# Auto-Refresh Loop
placeholder = st.empty()

while True:
    df = load_memory()
    with placeholder.container():
        st.warning("News/sentiment/depository/tando logic removed.")
            )

    time.sleep(REFRESH_RATE)
