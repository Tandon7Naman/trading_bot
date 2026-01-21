import statistics
try:
    from transformers import pipeline
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("   ⚠️ AI WARNING: Transformers not installed. Using Keyword Fallback.")

from strategies.news_fetcher import NewsFetcher
from config.settings import NEWS_CONFIG

class SentimentEngine:
    """Protocol 4.1.2: FinBERT Sentiment Analysis."""
    _pipeline = None

    @staticmethod
    def _load_model():
        if SentimentEngine._pipeline is None and AI_AVAILABLE:
            print("   🧠 AI: Loading FinBERT Model...")
            try:
                SentimentEngine._pipeline = pipeline("sentiment-analysis", model="ProsusAI/finbert")
            except Exception as e:
                print(f"   ❌ AI Load Failed: {e}")

    @staticmethod
    def analyze_sentiment(symbol="XAUUSD"):
        headlines = NewsFetcher.get_headlines(symbol)
        if not headlines: return 0.0, "NEUTRAL"

        SentimentEngine._load_model()
        scores = []
        
        if AI_AVAILABLE and SentimentEngine._pipeline:
            results = SentimentEngine._pipeline(headlines)
            for res in results:
                score = res['score'] if res['label'] == 'positive' else -res['score'] if res['label'] == 'negative' else 0.0
                scores.append(score)
        else:
            # Fallback
            for txt in headlines:
                if "soar" in txt.lower(): scores.append(0.5)
                elif "crash" in txt.lower(): scores.append(-0.5)
                else: scores.append(0.0)

        if not scores: return 0.0, "NEUTRAL"
        avg = statistics.mean(scores)
        
        threshold = NEWS_CONFIG.get('sentiment_threshold', 0.5)
        if avg > 0.2: return avg, "BULLISH"
        if avg < -0.2: return avg, "BEARISH"
        return avg, "NEUTRAL"