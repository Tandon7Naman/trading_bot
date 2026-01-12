import sys
from pathlib import Path

# Make src directory importable
sys.path.insert(0, str(Path(__file__).parent))

import unittest
from pivot_level_calculator import PivotLevelCalculator
from signal_confluence_filter import SignalConfluenceFilter
from risk_manager import RiskManager

class TestPivotLevelCalculator(unittest.TestCase):
    def test_pivot_levels(self):
        levels = PivotLevelCalculator.calculate_pivot_levels(69000, 68500, 68800)
        self.assertIn('pivot', levels)
        self.assertIn('r1', levels)
        self.assertIn('s1', levels)
        self.assertTrue(levels['pivot'] > 0)

class TestSignalConfluenceFilter(unittest.TestCase):
    def test_confluence(self):
        indicators = {'rsi': 60, 'macd': 1.2, 'signal_line': 1.0, 'ema_20': 69000, 'ema_50': 68800}
        self.assertTrue(SignalConfluenceFilter.check_indicator_confluence(indicators))
        indicators = {'rsi': 40, 'macd': 0.5, 'signal_line': 1.0, 'ema_20': 68800, 'ema_50': 69000}
        self.assertFalse(SignalConfluenceFilter.check_indicator_confluence(indicators))

class TestRiskManager(unittest.TestCase):
    def test_position_size(self):
        rm = RiskManager(100000)
        size = rm.calculate_position_size(69000, 68800)
        self.assertTrue(size > 0)
    def test_trade_allowed(self):
        rm = RiskManager(100000)
        self.assertTrue(rm.check_trade_allowed(95000, 2, 1000))
        self.assertFalse(rm.check_trade_allowed(95000, 6, 1000))
        self.assertFalse(rm.check_trade_allowed(95000, 2, 6000))

if __name__ == "__main__":
    unittest.main()
