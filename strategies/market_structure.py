import pandas as pd
from ta.trend import ADXIndicator # <--- NEW LIBRARY

class MarketStructure:
    """
    Phase 3 Compliance: Regime & Liquidity.
    Updated for Python 3.13 compatibility using 'ta' library.
    """
    
    @staticmethod
    def check_liquidity(df, price, min_daily_vol_usd=50_000_000):
        if df.empty: return False, "No Data"
        
        avg_vol = df['Volume'].rolling(window=30).mean().iloc[-1]
        est_daily_vol_usd = avg_vol * price * 1440 
        
        if est_daily_vol_usd < min_daily_vol_usd:
            return False, f"Low Liquidity (${est_daily_vol_usd/1e6:.1f}M < $50M)"
            
        return True, "Liquid"

    @staticmethod
    def get_regime(df, period=14):
        """Protocol 3.2: Regime Detection (ADX)."""
        if len(df) < period + 1: return "UNCERTAIN", 0.0

        try:
            # Initialize ADX Indicator
            adx_ind = ADXIndicator(high=df['High'], low=df['Low'], close=df['Close'], window=period)
            
            # Get the actual ADX series
            adx_series = adx_ind.adx()
            
            # Get latest value
            current_adx = adx_series.iloc[-1]
            
            if pd.isna(current_adx): return "UNCERTAIN", 0.0
            
            if current_adx > 25:
                return "TRENDING", current_adx
            else:
                return "RANGING", current_adx
                
        except Exception as e:
            print(f"   ⚠️ ADX Calc Error: {e}")
            return "UNCERTAIN", 0.0