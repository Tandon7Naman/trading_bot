import pandas as pd
import pandas_ta as ta # <--- The Powerhouse

class MarketStructure:
    """
    Phase 3 Compliance: Regime & Liquidity.
    Refactored with 'pandas_ta' for professional-grade speed and accuracy.
    """
    
    @staticmethod
    def check_liquidity(df, price, min_daily_vol_usd=50_000_000):
        if df.empty: return False, "No Data"
        
        # Calculate Rolling Average Volume (30 periods)
        # pandas_ta doesn't replace simple mean, but we keep this consistent
        avg_vol = df['Volume'].rolling(window=30).mean().iloc[-1]
        
        est_daily_vol_usd = avg_vol * price * 1440 
        
        if est_daily_vol_usd < min_daily_vol_usd:
            return False, f"Low Liquidity (${est_daily_vol_usd/1e6:.1f}M < $50M)"
            
        return True, "Liquid"

    @staticmethod
    def get_regime(df, period=14):
        """
        Protocol 3.2: Regime Detection (ADX).
        Uses pandas_ta for vector-based calculation.
        """
        if len(df) < period + 1: return "UNCERTAIN", 0.0

        # --- THE MODERN STACK UPGRADE ---
        # Old way: 30 lines of manual math.
        # New way: 1 line.
        try:
            # Calculate ADX using pandas_ta
            # Returns a DataFrame with columns like ADX_14, DMP_14, DMN_14
            adx_df = df.ta.adx(length=period)
            
            if adx_df is None or adx_df.empty:
                return "UNCERTAIN", 0.0
                
            # Get the latest ADX value
            # Column name is typically "ADX_14"
            current_adx = adx_df[f"ADX_{period}"].iloc[-1]
            
            if pd.isna(current_adx): return "UNCERTAIN", 0.0
            
            if current_adx > 25:
                return "TRENDING", current_adx
            else:
                return "RANGING", current_adx
                
        except Exception as e:
            print(f"   ⚠️ ADX Calc Error: {e}")
            return "UNCERTAIN", 0.0