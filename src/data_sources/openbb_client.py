
"""
OpenBB SDK Client for Market Data & Technical Analysis
Provides real-time quotes, historical data, and technical indicators
"""

import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from openbb import obb
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    """Market data structure"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    symbol: str

@dataclass
class TechnicalIndicators:
    """Technical indicator values"""
    sma_20: float
    sma_50: float
    sma_200: float
    ema_12: float
    ema_26: float
    rsi: float
    macd: float
    macd_signal: float
    macd_hist: float
    bb_upper: float
    bb_middle: float
    bb_lower: float
    atr: float
    adx: float

class OpenBBClient:
    """
    Professional OpenBB SDK client for market data and analysis
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenBB client
        
        Args:
            api_key: OpenBB API key (optional for some endpoints)
        """
        self.api_key = api_key or os.getenv("OPENBB_API_KEY")
        
        # Configure OpenBB (if API key is provided)
        if self.api_key:
            obb.account.login(pat=self.api_key)
        
        logger.info("OpenBB client initialized successfully")
    
    def get_historical_data(
        self,
        symbol: str = "GLD",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch historical market data
        
        Args:
            symbol: Trading symbol (GLD, XAUUSD, etc.)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Data interval (1m, 5m, 15m, 1h, 1d)
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            
            # Fetch data using OpenBB
            data = obb.equity.price.historical(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                provider="yfinance"  # Can use other providers
            )
            
            df = data.to_df()
            
            logger.info(f"Retrieved {len(df)} bars of historical data for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return pd.DataFrame()
    
    def get_realtime_quote(self, symbol: str = "GLD") -> Dict[str, float]:
        """
        Get real-time quote for symbol
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with current price info
        """
        try:
            quote = obb.equity.price.quote(
                symbol=symbol,
                provider="yfinance"
            )
            
            quote_dict = quote.to_dict('records')[0] if not quote.empty else {}
            
            return {
                'last_price': quote_dict.get('last_price', 0.0),
                'open': quote_dict.get('open', 0.0),
                'high': quote_dict.get('high', 0.0),
                'low': quote_dict.get('low', 0.0),
                'close': quote_dict.get('close', 0.0),
                'volume': quote_dict.get('volume', 0),
                'timestamp': quote_dict.get('timestamp', None)
            }
        except Exception as e:
            logger.error(f"Error fetching real-time quote: {e}")
            return {}
    
    def get_technical_indicators(self, df: pd.DataFrame) -> TechnicalIndicators:
        """
        Compute technical indicators from OHLCV DataFrame
        """
        try:
            # SMA
            sma_20 = df['close'].rolling(window=20).mean().iloc[-1]
            sma_50 = df['close'].rolling(window=50).mean().iloc[-1]
            sma_200 = df['close'].rolling(window=200).mean().iloc[-1]
            # EMA
            ema_12 = df['close'].ewm(span=12, adjust=False).mean().iloc[-1]
            ema_26 = df['close'].ewm(span=26, adjust=False).mean().iloc[-1]
            # RSI
            delta = df['close'].diff()
            up = delta.clip(lower=0)
            down = -1 * delta.clip(upper=0)
            avg_gain = up.rolling(window=14).mean().iloc[-1]
            avg_loss = down.rolling(window=14).mean().iloc[-1]
            rs = avg_gain / avg_loss if avg_loss != 0 else np.nan
            rsi = 100 - (100 / (1 + rs)) if not np.isnan(rs) else np.nan
            # MACD
            ema_fast = df['close'].ewm(span=12, adjust=False).mean()
            ema_slow = df['close'].ewm(span=26, adjust=False).mean()
            macd = ema_fast - ema_slow
            macd_signal = macd.ewm(span=9, adjust=False).mean()
            macd_hist = macd.iloc[-1] - macd_signal.iloc[-1]
            # Bollinger Bands
            bb_middle = sma_20
            bb_std = df['close'].rolling(window=20).std().iloc[-1]
            bb_upper = bb_middle + 2 * bb_std
            bb_lower = bb_middle - 2 * bb_std
            # ATR
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.rolling(window=14).mean().iloc[-1]
            # ADX (simplified)
            adx = np.nan  # Placeholder for full ADX calculation
            return TechnicalIndicators(
                sma_20=sma_20, sma_50=sma_50, sma_200=sma_200,
                ema_12=ema_12, ema_26=ema_26, rsi=rsi,
                macd=macd.iloc[-1], macd_signal=macd_signal.iloc[-1], macd_hist=macd_hist,
                bb_upper=bb_upper, bb_middle=bb_middle, bb_lower=bb_lower,
                atr=atr, adx=adx
            )
        except Exception as e:
            logger.error(f"Error computing technical indicators: {e}")
            return TechnicalIndicators(*([np.nan]*14))
