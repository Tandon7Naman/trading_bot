import statistics
try:
    from transformers import pipeline
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("   ⚠️ AI WARNING: 'transformers' not installed. Using basic keyword fallback.")

from strategies.news_fetcher import NewsFetcher

class SentimentEngine:
    """
    Protocol 4.1.2: FinBERT Sentiment Analysis.
    Uses a pre-trained Financial LLM to classify news as Positive/Negative/Neutral.
    """
    _pipeline = None

    @staticmethod
    def _load_model():
        global AI_AVAILABLE
        if SentimentEngine._pipeline is None and AI_AVAILABLE:
            print("   🧠 AI: Loading FinBERT Model (This takes a moment)...")
            try:
                # We use ProsusAI/finbert - the industry standard for financial text
                SentimentEngine._pipeline = pipeline("sentiment-analysis", model="ProsusAI/finbert")
            except Exception as e:
                print(f"   ❌ AI Load Failed: {e}")
                AI_AVAILABLE = False

    @staticmethod
    def analyze_sentiment(symbol="XAUUSD"):
        """
        Protocol 4.2: The Veto Logic.
        Returns: Score (-1.0 to 1.0) and Label (BULLISH/BEARISH/NEUTRAL).
        """
        headlines = NewsFetcher.get_headlines(symbol)
        
        if not headlines:
            return 0.0, "NEUTRAL (No News)"

        # 1. LOAD AI
        SentimentEngine._load_model()
        
        scores = []
        
        # 2. ANALYZE EACH HEADLINE
        if AI_AVAILABLE and SentimentEngine._pipeline:
            try:
                results = SentimentEngine._pipeline(headlines)
                for res in results:
                    label = res['label'] # 'positive', 'negative', 'neutral'
                    score = res['score']
                    
                    if label == 'positive': scores.append(score)
                    elif label == 'negative': scores.append(-score)
                    else: scores.append(0.0)
            except Exception as e:
                print(f"   ⚠️ AI Inference Error: {e}")
                scores.append(0.0)
        else:
            # Fallback: Simple Keyword Counting (Protocol 4.1.1 Legacy)
            for text in headlines:
                text = text.lower()
                if "soar" in text or "jump" in text or "record" in text: scores.append(0.5)
                elif "crash" in text or "plunge" in text or "fear" in text: scores.append(-0.5)
                else: scores.append(0.0)

        # 3. AGGREGATE
        if not scores: return 0.0, "NEUTRAL"
        
        avg_score = statistics.mean(scores)
        
        # 4. CLASSIFY
        final_label = "NEUTRAL"
        if avg_score > 0.2: final_label = "BULLISH"
        if avg_score < -0.2: final_label = "BEARISH"
        
        return avg_score, final_label