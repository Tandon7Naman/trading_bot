
from openbb import obb
import pandas as pd
import numpy as np

class TechnicalAnalyzer:
    """
    Professional technical analysis using OpenBB
    """
    def __init__(self, symbol: str = "GLD"):
        self.symbol = symbol
        self.obb = obb

    def get_chart_patterns(self, df: pd.DataFrame) -> dict:
        """
        Identify chart patterns: Head & Shoulders, Double Top/Bottom, etc.
        Uses OpenBB's pattern recognition
        """
        patterns = {}
        # Example: Head & Shoulders
        try:
            hs = self.obb.ta.patterns.head_shoulders(df)
            if hs is not None:
                patterns["head_shoulders"] = hs
        except Exception:
            patterns["head_shoulders"] = None
        # Add more patterns as needed
        return patterns

    def get_indicators(self, df: pd.DataFrame) -> dict:
        """
        Compute technical indicators (MA, RSI, MACD, ATR, etc.)
        """
        indicators = {}
        try:
            indicators["ma20"] = self.obb.ta.sma(df, length=20)
            indicators["rsi14"] = self.obb.ta.rsi(df, length=14)
            indicators["macd"] = self.obb.ta.macd(df)
            indicators["atr14"] = self.obb.ta.atr(df, length=14)
        except Exception:
            pass
        return indicators

    def analyze(self, df: pd.DataFrame) -> dict:
        """
        Full technical analysis: chart patterns + indicators
        """
        return {
            "patterns": self.get_chart_patterns(df),
            "indicators": self.get_indicators(df)
        }
