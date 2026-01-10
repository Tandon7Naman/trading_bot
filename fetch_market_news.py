# fetch_market_news.py - FIXED VERSION WITH SAMPLE DATA FALLBACK
import pandas as pd
from datetime import datetime, timedelta
import logging
import os
import json

logging.basicConfig(
    filename='logs/market_news.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def analyze_sentiment(text):
    """Analyze sentiment of news text using TextBlob"""
    try:
        from textblob import TextBlob
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # -1 to 1
        subjectivity = blob.sentiment.subjectivity
        
        if polarity > 0.1:
            sentiment = 'POSITIVE'
        elif polarity < -0.1:
            sentiment = 'NEGATIVE'
        else:
            sentiment = 'NEUTRAL'
            
        return {'sentiment': sentiment, 'polarity': round(polarity, 3), 'subjectivity': round(subjectivity, 3)}
    except ImportError:
        logging.warning("TextBlob not installed. Using simple sentiment analysis.")
        print("[-] TextBlob not installed. Install with: pip install textblob")
        # Simple sentiment based on keywords
        text_lower = text.lower()
        positive_words = ['gain', 'surge', 'rally', 'rise', 'bullish', 'strong', 'growth']
        negative_words = ['fall', 'drop', 'decline', 'loss', 'bearish', 'weak', 'down']
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            sentiment = 'POSITIVE'
            polarity = 0.5
        elif neg_count > pos_count:
            sentiment = 'NEGATIVE'
            polarity = -0.5
        else:
            sentiment = 'NEUTRAL'
            polarity = 0.0
        
        return {'sentiment': sentiment, 'polarity': polarity, 'subjectivity': 0.5}
    except Exception as e:
        logging.error(f"Error analyzing sentiment: {str(e)}")
        return {'sentiment': 'UNKNOWN', 'polarity': 0, 'subjectivity': 0}

def fetch_news_from_newsapi(keyword='gold trading', api_key=None):
    """Fetch news from NewsAPI if key available"""
    try:
        if not api_key or api_key == 'YOUR_NEWSAPI_KEY_HERE':
            print("[-] NewsAPI key not configured. Using sample news data...")
            logging.warning("NewsAPI key not configured. Using sample data.")
            return None
        
        import requests
        
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': keyword,
            'sortBy': 'publishedAt',
            'language': 'en',
            'apiKey': api_key,
            'pageSize': 50
        }
        
        print(f"[*] Fetching news from NewsAPI for '{keyword}'...")
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data['status'] == 'ok':
            articles = data['articles']
            logging.info(f"Fetched {len(articles)} news articles from API")
            print(f"[+] Fetched {len(articles)} articles from NewsAPI")
            return articles
        else:
            logging.error(f"News API error: {data.get('message', 'Unknown error')}")
            print(f"[-] News API error: {data.get('message', 'Unknown error')}")
            
            return None
    except Exception as e:
        logging.error(f"Error fetching news from API: {str(e)}")
        print(f"[-] Error fetching news from API: {str(e)}")
        return None

def get_sample_news():
    """Return sample news data if API key is missing or fails"""
    print("[*] Returning sample news data...")
    return [
        {
            'source': {'name': 'Sample News'},
            'title': 'Gold Prices Surge Amid Economic Uncertainty',
            'description': 'Investors are flocking to gold as a safe-haven asset, pushing prices to a new high.',
            'publishedAt': (datetime.now() - timedelta(hours=2)).isoformat(),
            'url': 'http://example.com/news1'
        },
        {
            'source': {'name': 'Sample News'},
            'title': 'Market Volatility Impacts Gold Futures Negatively',
            'description': 'Gold futures experienced a slight dip today due to unexpected market corrections and profit-taking.',
            'publishedAt': (datetime.now() - timedelta(hours=1)).isoformat(),
            'url': 'http://example.com/news2'
        },
        {
            'source': {'name': 'Sample News'},
            'title': 'Central Banks Hold Steady on Gold Reserves',
            'description': 'Major central banks have reported no significant changes to their gold reserves this quarter.',
            'publishedAt': (datetime.now() - timedelta(days=1)).isoformat(),
            'url': 'http://example.com/news3'
        }
    ]

def process_news_data(articles):
    """Convert articles to DataFrame with sentiment analysis"""
    try:
        if not articles:
            print("[-] No articles to process.")
            return pd.DataFrame()
            
        data = []
        print(f"[*] Processing {len(articles)} articles...")
        
        for article in articles:
            # Ensure article is a dictionary
            if not isinstance(article, dict):
                continue

            title = article.get('title', '') or ''
            description = article.get('description', '') or ''
            
            # Skip if both title and description are empty
            if not title and not description:
                continue

            sentiment_data = analyze_sentiment(title + ' ' + description)
            
            data.append({
                'timestamp': article.get('publishedAt', datetime.now().isoformat()),
                'source': (article.get('source') or {}).get('name', 'N/A'),
                'title': title,
                'description': description,
                'url': article.get('url', 'N/A'),
                'sentiment': sentiment_data['sentiment'],
                'polarity': sentiment_data['polarity'],
                'subjectivity': sentiment_data['subjectivity']
            })
        
        if not data:
            print("[-] No valid articles found after processing.")
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values(by='timestamp', ascending=False)
        
        print(f"[+] Processed {len(df)} articles into DataFrame")
        return df
        
    except Exception as e:
        logging.error(f"Error processing news data: {str(e)}")
        print(f"[-] Error processing news data: {str(e)}")
        return pd.DataFrame()

def main():
    """Main function to fetch and save news"""
    print("\n" + "="*70)
    print("[*] FETCHING MARKET NEWS")
    print("="*70)
    print(f"[*] Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Load config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        api_key = config.get('news_api_key')
    except FileNotFoundError:
        print("[-] config.json not found. Cannot get NewsAPI key.")
        api_key = None
    except Exception as e:
        print(f"[-] Error reading config: {str(e)}")
        api_key = None

    # Fetch news
    articles = fetch_news_from_newsapi(api_key=api_key)
    
    # Fallback to sample data if API fails or returns nothing
    if not articles:
        articles = get_sample_news()

    # Process and save
    df = process_news_data(articles)
    
    if not df.empty:
        output_file = 'data/market_news.csv'
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        df.to_csv(output_file, index=False)
        print(f"[+] News data saved to {output_file}")
        logging.info(f"Saved {len(df)} news articles to {output_file}")
    else:
        print("[-] No news data to save.")
        logging.warning("No news data was processed or saved.")

    print("="*70)

if __name__ == "__main__":
    main()
