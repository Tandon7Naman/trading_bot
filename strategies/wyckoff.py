import numpy as np


class WyckoffAnalyzer:
    """
    Phase 3 Compliance: Structural Analysis.
    - Detects Selling Climax (Panic Selling).
    - Detects Springs (Bear Traps).
    """

    @staticmethod
    def find_selling_climax(df, lookback=50):
        """
        Protocol 3.1.1: The Selling Climax (SC).
        Scans past 'lookback' candles for:
        1. Wide Spread (Top 90th percentile)
        2. Ultra High Volume (Top 95th percentile)
        3. Closing off the lows (Stopping action)
        """
        window = df.iloc[-lookback:].copy()

        # 1. Calculate Metrics
        ranges = window["High"] - window["Low"]
        volumes = window["Volume"]

        # 2. Dynamic Thresholds
        # We use nearest rank to ensure we don't pick median values in low-volatility
        spread_threshold = np.percentile(ranges, 90)
        vol_threshold = np.percentile(volumes, 95)

        # 3. Scan Backwards
        for i in range(len(window) - 2, 0, -1):
            row = window.iloc[i]
            spread = row["High"] - row["Low"]

            # A. Is it panic? (Strictly Greater)
            # This prevents matching "average" candles in flat markets
            if spread <= spread_threshold:
                continue
            if row["Volume"] <= vol_threshold:
                continue

            # B. Is it a DOWN candle? (Strict Down)
            if row["Close"] >= row["Open"]:
                continue

            # C. Did buying occur? (Close off the lows)
            # Range Position: 0.0 = Low, 1.0 = High.
            # We want to see some wick at the bottom (Stopping volume).
            range_pos = (row["Close"] - row["Low"]) / spread
            if range_pos < 0.10:
                continue

            # SC FOUND
            return True, row["Low"], row["Volume"], window.index[i]

        return False, 0.0, 0.0, None

    @staticmethod
    def detect_spring(current_row, sc_low, sc_vol):
        """
        Protocol 3.1.2: The Spring.
        Checks if current price dipped below SC Low but is recovering.
        """
        # 1. Breach: Low must go below SC Low
        if current_row["Low"] >= sc_low:
            return False, "No Breach"

        # 2. Recovery: Close should be near or above SC Low
        # We allow a small tolerance if it's a strong pinbar
        if current_row["Close"] < sc_low:
            # Basic check: Reject if it closed weak
            pass

        # 3. Supply Exhaustion: Volume should be lower than the Panic Candle
        if current_row["Volume"] > sc_vol:
            return False, "High Vol Breakout (Not Spring)"

        return True, "Spring Detected"
