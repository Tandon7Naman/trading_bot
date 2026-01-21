import statistics
import os

# --- FIX FOR KERAS 3 CONFLICT ---
# This forces Transformers to use the legacy keras interface
os.environ["TF_USE_LEGACY_KERAS"] = "1" 

try:
    from transformers import pipeline
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("   ⚠️ AI WARNING: Transformers not installed. Using Keyword Fallback.")

from strategies.news_fetcher import NewsFetcher
from config.settings import NEWS_CONFIG

class SentimentEngine:
    """Protocol 4.1.2: FinBERT Sentiment Analysis (Robust)."""
    _pipeline = None
    _failed_once = False # <--- Circuit Breaker for AI loading

    @staticmethod
    def _load_model():
        # Only try loading if we haven't failed before
        if SentimentEngine._pipeline is None and AI_AVAILABLE and not SentimentEngine._failed_once:
            print("   🧠 AI: Loading FinBERT Model...")
            try:
                # We use the pipeline with the specific revision if needed, or default
                SentimentEngine._pipeline = pipeline("sentiment-analysis", model="ProsusAI/finbert")
            except Exception as e:
                print(f"   ❌ AI Load Failed: {e}")
                print("   ⚠️ Switching to Keyword Fallback Mode permanently.")
                SentimentEngine._failed_once = True # <--- STOP TRYING

    @staticmethod
    def analyze_sentiment(symbol="XAUUSD"):
        headlines = NewsFetcher.get_headlines(symbol)
        if not headlines: return 0.0, "NEUTRAL"

        SentimentEngine._load_model()
        scores = []
        
        # 1. AI MODE
        if SentimentEngine._pipeline:
            try:
                results = SentimentEngine._pipeline(headlines)
                for res in results:
                    score = res['score'] if res['label'] == 'positive' else -res['score'] if res['label'] == 'negative' else 0.0
                    scores.append(score)
            except Exception:
                # If inference fails during run, fallback
                pass
        
        # 2. FALLBACK MODE (If AI failed or isn't loaded)
        if not scores:
            for txt in headlines:
                txt = txt.lower()
                if "soar" in txt or "jump" in txt or "record" in txt: scores.append(0.5)
                elif "crash" in txt or "plunge" in txt or "fear" in txt: scores.append(-0.5)
                else: scores.append(0.0)

        if not scores: return 0.0, "NEUTRAL"
        
        avg = statistics.mean(scores)
        if avg > 0.2: return avg, "BULLISH"
        if avg < -0.2: return avg, "BEARISH"
        return avg, "NEUTRAL"