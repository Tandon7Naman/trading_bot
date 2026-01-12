"""
Integration test for main_bot.py with PreTradeGateway
Tests that all gateway modules are properly initialized and integrated
"""

import sys
from pathlib import Path
import unittest
from datetime import datetime

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

# NOTE: Import your actual bot class here
# Replace 'GoldTradingBot' with your actual class name
try:
    from main_bot import GoldTradingBot as BotClass
except ImportError:
    # Fallback - adjust as needed
    BotClass = None


class TestMainBotGatewayIntegration(unittest.TestCase):
    """Test main_bot.py integration with PreTradeGateway"""

    @classmethod
    def setUpClass(cls):
        """Setup test bot instance once for all tests"""
        if BotClass is None:
            raise ImportError(
                "Could not import bot class. Check class name in test_main_bot_integration.py"
            )
        cls.bot = BotClass(account_size=100000)

    def test_01_bot_initialized(self):
        """Test 1: Bot initializes without errors"""
        self.assertIsNotNone(self.bot)
        print("✓ Test 1 PASS: Bot initialized")

    def test_02_gateway_modules_exist(self):
        """Test 2: All 8 gateway modules are initialized"""
        modules = [
            'fiscal_loader',
            'global_cues',
            'econ_calendar',
            'currency_monitor',
            'pivot_calc',
            'signal_filter',
            'geo_risk',
            'risk_manager',
        ]
        
        for module_name in modules:
            self.assertTrue(
                hasattr(self.bot, module_name),
                f"Missing module: {module_name}"
            )
            self.assertIsNotNone(
                getattr(self.bot, module_name),
                f"Module {module_name} is None"
            )
        
        print("✓ Test 2 PASS: All 8 gateway modules initialized")

    def test_03_gateway_initialization(self):
        """Test 3: PreTradeGateway initializes correctly"""
        gateway = self.bot._initialize_gateway()
        self.assertIsNotNone(gateway)
        
        # Verify all modules are wired to gateway
        self.assertEqual(gateway.fiscal_loader, self.bot.fiscal_loader)
        self.assertEqual(gateway.global_cues, self.bot.global_cues)
        self.assertEqual(gateway.econ_calendar, self.bot.econ_calendar)
        self.assertEqual(gateway.currency_monitor, self.bot.currency_monitor)
        self.assertEqual(gateway.pivot_calc, self.bot.pivot_calc)
        self.assertEqual(gateway.signal_filter, self.bot.signal_filter)
        self.assertEqual(gateway.geo_risk, self.bot.geo_risk)
        self.assertEqual(gateway.risk_manager, self.bot.risk_manager)
        
        print("✓ Test 3 PASS: Gateway initialization correct")

    def test_04_risk_manager_position_sizing(self):
        """Test 4: RiskManager calculates position size correctly"""
        position = self.bot.risk_manager.calculate_position_size(
            entry_price=69000,
            stop_loss_price=68800,
        )
        
        self.assertGreater(position, 0)
        self.assertEqual(position, 1)  # Should be 1 lot for this scenario
        
        print(f"✓ Test 4 PASS: Position sizing works - {position} lots")

    def test_05_methods_exist(self):
        """Test 5: All required methods exist"""
        required_methods = [
            'run_full_cycle',
            '_initialize_gateway',
            '_execute_trades_with_risk',
            '_alert_gateway_failure',
            'generate_daily_summary',
        ]
        for method in required_methods:
            self.assertTrue(
                hasattr(self.bot, method),
                f"Missing method: {method}"
            )
        print("✓ Test 5 PASS: All required methods exist")

if __name__ == "__main__":
    unittest.main()
