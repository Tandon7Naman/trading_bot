import pandas as pd
import numpy as np

class MarketStructure:
    """
    Phase 3 Compliance: Regime & Liquidity.
    - Filters out 'Scam Wicks' (Low Liquidity).
    - Identifies Trending vs Ranging (ADX).
    """
    
    @staticmethod
    def check_liquidity(df, price, min_daily_vol_usd=50_000_000):
        """
        Protocol 3.3: Liquidity Filtering.
        Prevents trading during illiquid hours or on dead assets.
        """
        if df.empty: return False, "No Data"
        
        # Calculate Rolling Average Volume (30 periods)
        avg_vol = df['Volume'].rolling(window=30).mean().iloc[-1]
        
        # Estimate Daily Dollar Volume (Heuristic)
        # 1440 minutes per day.
        est_daily_vol_usd = avg_vol * price * 1440 
        
        if est_daily_vol_usd < min_daily_vol_usd:
            return False, f"Low Liquidity (${est_daily_vol_usd/1e6:.1f}M < $50M)"
            
        return True, "Liquid"

    @staticmethod
    def get_regime(df, period=14):
        """
        Protocol 3.2: Regime Detection (ADX).
        Returns: 'TRENDING' (>25) or 'RANGING' (<25).
        """
        if len(df) < period + 1: return "UNCERTAIN", 0.0

        # ADX Calculation (Wilder's Smoothing)
        df = df.copy()
        df['H-L'] = df['High'] - df['Low']
        df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
        df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
        df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
        
        df['UpMove'] = df['High'] - df['High'].shift(1)
        df['DownMove'] = df['Low'].shift(1) - df['Low']
        
        df['+DM'] = np.where((df['UpMove'] > df['DownMove']) & (df['UpMove'] > 0), df['UpMove'], 0)
        df['-DM'] = np.where((df['DownMove'] > df['UpMove']) & (df['DownMove'] > 0), df['DownMove'], 0)
        
        # Exponential Moving Average for smoothness
        tr = df['TR'].ewm(span=period, adjust=False).mean()
        plus_di = 100 * (df['+DM'].ewm(span=period, adjust=False).mean() / tr)
        minus_di = 100 * (df['-DM'].ewm(span=period, adjust=False).mean() / tr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.ewm(span=period, adjust=False).mean().iloc[-1]
        
        if adx > 25:
            return "TRENDING", adx
        else:
            return "RANGING", adx
