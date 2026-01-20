import numpy as np
import pandas as pd

class WyckoffAnalyzer:
    """
    Protocol 3.1: Algorithmic Detection of Accumulation.
    Detects: Selling Climax (SC) -> Secondary Test (ST) -> Spring.
    """
    
    @staticmethod
    def find_selling_climax(df, lookback=50):
        """
        Scans the last 'lookback' candles for a Selling Climax candidate.
        Returns: (Found_Bool, SC_Low_Price, SC_Volume, Index)
        """
        # Slice the relevant window
        window = df.iloc[-lookback:].copy()
        
        # 1. METRICS
        recent_ranges = window['High'] - window['Low']
        recent_volumes = window['Volume']
        
        # 2. THRESHOLDS (90th/95th Percentile)
        spread_threshold = np.percentile(recent_ranges, 90)
        vol_threshold = np.percentile(recent_volumes, 95)
        
        # 3. SCAN LOOP (Iterate backwards to find most recent)
        # We start from -2 because current candle is forming
        for i in range(len(window)-2, 0, -1):
            row = window.iloc[i]
            
            # Condition A: Downtrend (Price below 50 SMA)
            # Assuming 'SMA_50' is calculated in Strategy
            sma = row.get('SMA_50', 0)
            if sma > 0 and row['Close'] > sma:
                continue # Not in downtrend
                
            # Condition B: Wide Spread
            spread = row['High'] - row['Low']
            if spread < spread_threshold:
                continue
                
            # Condition C: Ultra High Volume
            if row['Volume'] < vol_threshold:
                continue
                
            # Condition D: Closes off Lows (Buying Pressure)
            # "Pin Bar" or "Stopping Volume" logic
            # Range bottom 25% is "The Lows". We want close ABOVE that.
            range_pos = (row['Close'] - row['Low']) / spread
            if range_pos < 0.25: # Closed very weak
                continue
                
            # FOUND SC!
            return True, row['Low'], row['Volume'], window.index[i]
            
        return False, 0.0, 0.0, None

    @staticmethod
    def detect_spring(current_row, sc_low, sc_vol):
        """
        Protocol 3.1.2: The Spring (Bear Trap).
        Checks if current candle dips below SC Low but recovers.
        """
        # 1. Breach Support
        if current_row['Low'] >= sc_low:
            return False, "No Breach"
            
        # 2. Rejection (Close back inside)
        # Ideally Close > SC_Low, or at least very strong rejection
        if current_row['Close'] < sc_low:
            return False, "Failed Spring (Breakdown)"
            
        # 3. Volume Confirmation (Supply Exhaustion)
        # Spring Volume should be LOWER than SC Volume (or at least not explosive selling)
        if current_row['Volume'] > sc_vol:
            return False, "High Vol Breakout (Not Spring)"
            
        return True, "SPRING DETECTED"
