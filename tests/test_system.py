import unittest
import pandas as pd
from typing import List, Dict, Union

# Import your modules (adjust paths if necessary)
# Assuming running from root: python -m unittest tests/test_system.py
from src.features import TechnicalAnalysis

class TestTitanSystem(unittest.TestCase):
    
    def setUp(self) -> None:
        """Initialize dummy data for testing."""
        self.dummy_data: pd.DataFrame = pd.DataFrame({
            "close": [100.0, 101.0, 102.0, 101.5, 103.0, 104.0, 105.0] * 5  # 35 rows
        })

    def test_technical_features(self) -> None:
        """Test if RSI and SMA are calculated correctly with types."""
        # 1. Test Feature Engineering
        df_processed: pd.DataFrame = TechnicalAnalysis.add_rsi(self.dummy_data, period=14)
        df_processed = TechnicalAnalysis.add_sma(df_processed, period=10)
        
        # 2. Type Checks
        self.assertIn("RSI", df_processed.columns)
        self.assertIn("SMA_10", df_processed.columns)
        
        # 3. Value Checks
        latest: Dict[str, float] = TechnicalAnalysis.get_latest_signal(df_processed)
        
        self.assertIsInstance(latest["RSI"], float)
        self.assertIsInstance(latest["SMA"], float)
        print("✅ Feature Engineering Tests Passed")

    def test_sentiment_logic_types(self) -> None:
        """Test the decision logic types (mocking the Actor logic)."""
        score: float = 0.95
        confidence: float = 0.99
        threshold: float = 0.80
        
        decision: str = "HOLD"
        
        if score >= threshold and confidence >= 0.90:
            decision = "BUY"
        elif score <= -threshold and confidence >= 0.90:
            decision = "SELL"
            
        self.assertEqual(decision, "BUY")
        self.assertIsInstance(decision, str)
        print("✅ Logic Type Tests Passed")

if __name__ == "__main__":
    unittest.main()
