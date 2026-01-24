
"""
Finnhub API Client for News & Sentiment Analysis
Provides real-time market news, sentiment scoring, and economic calendar events
"""

import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import finnhub
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """News article data structure"""
    headline: str
    summary: str
    source: str
    url: str
    datetime: datetime
    sentiment_score: float
    category: str
    related_symbols: List[str]


@dataclass
class EconomicEvent:
    """Economic calendar event"""
    event: str
    country: str
    actual: Optional[float]
    estimate: Optional[float]
    previous: Optional[float]
    impact: str  # High, Medium, Low
    time: datetime


class FinnhubClient:
    """
    Professional Finnhub API client for market intelligence
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Finnhub client
        
        Args:
            api_key: Finnhub API key (defaults to FINNHUB_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY")
        if not self.api_key:
            raise ValueError("Finnhub API key not found. Set FINNHUB_API_KEY environment variable.")
        
        self.client = finnhub.Client(api_key=self.api_key)
        logger.info("Finnhub client initialized successfully")
    
    def get_market_news(
        self, 
        category: str = "forex",
        lookback_hours: int = 24
    ) -> List[NewsArticle]:
        """
        Fetch market news with sentiment analysis
        
        Args:
            category: News category (forex, commodities, crypto, general)
            lookback_hours: Hours to look back for news
            
        Returns:
            List of NewsArticle objects with sentiment scores
        """
        try:
            # Get news from Finnhub
            news_data = self.client.general_news(category, min_id=0)
            
            articles = []
            cutoff_time = datetime.now() - timedelta(hours=lookback_hours)
            
            for article in news_data:
                article_time = datetime.fromtimestamp(article.get('datetime', 0))
                
                if article_time < cutoff_time:
                    continue
                
                # Perform sentiment analysis
                sentiment = self._analyze_sentiment(
                    article.get('headline', '') + ' ' + article.get('summary', '')
                )
                
                articles.append(NewsArticle(
                    headline=article.get('headline', ''),
                    summary=article.get('summary', ''),
                    source=article.get('source', ''),
                    url=article.get('url', ''),
                    datetime=article_time,
                    sentiment_score=sentiment,
                    category=category,
                    related_symbols=article.get('related', [])
                ))
            
            logger.info(f"Retrieved {len(articles)} news articles from Finnhub")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching market news: {e}")
            return []
    
    def get_gold_specific_news(self, lookback_hours: int = 24) -> List[NewsArticle]:
        """
        Get gold-specific news and sentiment
        
        Args:
            lookback_hours: Hours to look back
            
        Returns:
            Filtered news articles related to gold
        """
        try:
            # Get commodity news
            all_news = self.get_market_news(category="commodities", lookback_hours=lookback_hours)
            
            # Filter for gold-related keywords
            gold_keywords = ['gold', 'xau', 'precious metals', 'bullion', 'mcx']
            
            gold_news = [
                article for article in all_news
                if any(keyword in article.headline.lower() or keyword in article.summary.lower() 
                       for keyword in gold_keywords)
            ]
            
            logger.info(f"Filtered {len(gold_news)} gold-specific articles")
            return gold_news
            
        except Exception as e:
            logger.error(f"Error fetching gold news: {e}")
            return []
    
    def get_economic_calendar(
        self, 
        days_ahead: int = 7
    ) -> List[EconomicEvent]:
        """
        Fetch economic calendar events
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of upcoming economic events
        """
        try:
            # Get economic calendar from Finnhub
            from_date = datetime.now().strftime("%Y-%m-%d")
            to_date = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
            
            calendar_data = self.client.economic_calendar(
                _from=from_date,
                to=to_date
            )
            
            events = []
            for event_data in calendar_data.get('economicCalendar', []):
                events.append(EconomicEvent(
                    event=event_data.get('event', ''),
                    country=event_data.get('country', ''),
                    actual=event_data.get('actual'),
                    estimate=event_data.get('estimate'),
                    previous=event_data.get('previous'),
                    impact=event_data.get('impact', 'Low'),
                    time=datetime.fromisoformat(event_data.get('time', ''))
                ))
            
            logger.info(f"Retrieved {len(events)} economic calendar events")
            return events
            
        except Exception as e:
            logger.error(f"Error fetching economic calendar: {e}")
            return []
    
    def get_aggregated_sentiment(self, symbol: str = "GLD") -> Dict[str, float]:
        """
        Get aggregated sentiment score for a symbol
        
        Args:
            symbol: Trading symbol (e.g., GLD, XAUUSD)
            
        Returns:
            Dictionary with sentiment metrics
        """
        try:
            # Get company news sentiment (for GLD ETF)
            sentiment_data = self.client.news_sentiment(symbol)
            
            if not sentiment_data:
                return {
                    'buzz': 0.0,
                    'sentiment_score': 0.0,
                    'sector_average': 0.0,
                    'confidence': 0.0
                }
            
            return {
                'buzz': sentiment_data.get('buzz', {}).get('articlesInLastWeek', 0),
                'sentiment_score': sentiment_data.get('sentiment', {}).get('bearishPercent', 0) - 
                                   sentiment_data.get('sentiment', {}).get('bullishPercent', 0),
                'sector_average': sentiment_data.get('sectorAverageBullishPercent', 0),
                'confidence': sentiment_data.get('companyNewsScore', 0)
            }
            
        except Exception as e:
            logger.error(f"Error fetching aggregated sentiment: {e}")
            return {'buzz': 0.0, 'sentiment_score': 0.0, 'sector_average': 0.0, 'confidence': 0.0}
    
    def _analyze_sentiment(self, text: str) -> float:
        """
        Simple sentiment analysis using keyword matching
        Enhanced version should use NLP models
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment score (-1 to +1, negative = bearish, positive = bullish)
        """
        # Bullish keywords
        bullish_words = [
            'rally', 'surge', 'gain', 'rise', 'bull', 'optimistic', 
            'strong', 'growth', 'positive', 'upside', 'breakout'
        ]
        
        # Bearish keywords
        bearish_words = [
            'fall', 'decline', 'drop', 'bear', 'pessimistic', 
            'weak', 'negative', 'downside', 'crash', 'plunge'
        ]
        
        text_lower = text.lower()
        
        bullish_count = sum(1 for word in bullish_words if word in text_lower)
        bearish_count = sum(1 for word in bearish_words if word in text_lower)
        
        total_count = bullish_count + bearish_count
        
        if total_count == 0:
            return 0.0
        
        sentiment = (bullish_count - bearish_count) / total_count
        return max(-1.0, min(1.0, sentiment))
    
    def get_market_sentiment_summary(self) -> Dict[str, any]:
        """
        Get comprehensive market sentiment summary
        
        Returns:
            Dictionary with overall market sentiment analysis
        """
        try:
            gold_news = self.get_gold_specific_news(lookback_hours=24)
            
            if not gold_news:
                return {
                    'overall_sentiment': 0.0,
                    'news_count': 0,
                    'bullish_ratio': 0.0,
                    'bearish_ratio': 0.0,
                    'top_headlines': []
                }
            
            # Calculate overall sentiment
            avg_sentiment = sum(article.sentiment_score for article in gold_news) / len(gold_news)
            
            bullish_count = sum(1 for article in gold_news if article.sentiment_score > 0.2)
            bearish_count = sum(1 for article in gold_news if article.sentiment_score < -0.2)
            
            return {
                'overall_sentiment': avg_sentiment,
                'news_count': len(gold_news),
                'bullish_ratio': bullish_count / len(gold_news) if gold_news else 0.0,
                'bearish_ratio': bearish_count / len(gold_news) if gold_news else 0.0,
                'top_headlines': [article.headline for article in gold_news[:5]]
            }
            
        except Exception as e:
            logger.error(f"Error generating sentiment summary: {e}")
            return {
                'overall_sentiment': 0.0,
                'news_count': 0,
                'bullish_ratio': 0.0,
                'bearish_ratio': 0.0,
                'top_headlines': []
            }


# Usage Example
if __name__ == "__main__":
    # Initialize client
    client = FinnhubClient()
    
    # Get gold news
    gold_news = client.get_gold_specific_news(lookback_hours=24)
    print(f"Found {len(gold_news)} gold-related articles")
    
    # Get sentiment summary
    summary = client.get_market_sentiment_summary()
    print(f"Overall Sentiment: {summary['overall_sentiment']:.2f}")
    print(f"Bullish Ratio: {summary['bullish_ratio']:.1%}")
    
    # Get economic calendar
    events = client.get_economic_calendar(days_ahead=7)
    print(f"Upcoming events: {len(events)}")
