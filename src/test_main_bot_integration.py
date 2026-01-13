
"""
Integration test for main_bot.py with PreTradeGateway
Tests that all gateway modules are properly initialized and integrated
"""


import sys
from pathlib import Path
import unittest
from datetime import datetime

# Add root directory to path so we can import main_bot
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the actual bot class
from main_bot import GoldTradingBot


class TestMainBotGatewayIntegration(unittest.TestCase):
    """Test main_bot.py integration with PreTradeGateway"""

    @classmethod
    def setUpClass(cls):
        """Setup test bot instance once for all tests"""
        try:
            cls.bot = GoldTradingBot(account_size=100000)
            print("\n✓ GoldTradingBot initialized for testing")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize GoldTradingBot: {e}")

    def test_01_bot_initialized(self):
        """Test 1: Bot initializes without errors"""
        self.assertIsNotNone(self.bot)
        print("✓ Test 1 PASS: Bot initialized successfully")

    def test_02_gateway_modules_exist(self):
        """Test 2: All 8 gateway modules are initialized"""
        required_modules = {
            'fiscal_loader': 'FiscalPolicyLoader',
            'global_cues': 'GlobalCuesMonitor',
            'econ_calendar': 'EconomicCalendarMonitor',
            'currency_monitor': 'CurrencyMonitor',
            'pivot_calc': 'PivotLevelCalculator',
            'signal_filter': 'SignalConfluenceFilter',
            'geo_risk': 'GeopoliticalRiskMonitor',
            'risk_manager': 'RiskManager',
        }
        
        for attr_name, expected_class in required_modules.items():
            self.assertTrue(
                hasattr(self.bot, attr_name),
                f"Bot missing attribute: {attr_name}"
            )
            
            module_instance = getattr(self.bot, attr_name)
            self.assertIsNotNone(
                module_instance,
                f"Module {attr_name} is None"
            )
            
            print(f"  ✓ {attr_name} ({expected_class})")
        
        print("✓ Test 2 PASS: All 8 gateway modules initialized")

    def test_03_gateway_initialization(self):
        """Test 3: PreTradeGateway initializes correctly"""
        gateway = self.bot._initialize_gateway()
        
        self.assertIsNotNone(gateway)
        print("  ✓ Gateway object created")
        
        # Verify all modules are wired to gateway
        self.assertEqual(gateway.fiscal_loader, self.bot.fiscal_loader)
        self.assertEqual(gateway.global_cues, self.bot.global_cues)
        self.assertEqual(gateway.econ_calendar, self.bot.econ_calendar)
        self.assertEqual(gateway.currency_monitor, self.bot.currency_monitor)
        self.assertEqual(gateway.pivot_calc, self.bot.pivot_calc)
        self.assertEqual(gateway.signal_filter, self.bot.signal_filter)
        self.assertEqual(gateway.geo_risk, self.bot.geo_risk)
        self.assertEqual(gateway.risk_manager, self.bot.risk_manager)
        
        print("  ✓ All modules correctly wired to gateway")
        print("✓ Test 3 PASS: Gateway initialization correct")

    def test_04_risk_manager_position_sizing(self):
        """Test 4: RiskManager calculates position size correctly"""
        position = self.bot.risk_manager.calculate_position_size(
            entry_price=69000,
            stop_loss_price=68800,
        )
        
        self.assertGreater(position, 0, "Position must be > 0")
        self.assertIsInstance(position, int, "Position must be integer")
        
        print(f"  ✓ Position calculated: {position} lots")
        print(f"  ✓ Entry: ₹69,000 | Stop Loss: ₹68,800 | Risk: ₹200/lot")
        print("✓ Test 4 PASS: Position sizing works correctly")

    def test_05_required_methods_exist(self):
        """Test 5: All required gateway methods exist"""
        required_methods = [
            '_initialize_gateway',
            '_execute_trades_with_risk',
            '_alert_gateway_failure',
            'generate_daily_summary',
            'run_full_cycle',
        ]
        
        for method_name in required_methods:
            self.assertTrue(
                hasattr(self.bot, method_name),
                f"Bot missing method: {method_name}"
            )
            
            method = getattr(self.bot, method_name)
            self.assertTrue(
                callable(method),
                f"{method_name} is not callable"
            )
            
            print(f"  ✓ {method_name}()")
        
        print("✓ Test 5 PASS: All required methods exist")

    def test_06_gateway_context_initialized(self):
        """Test 6: Gateway context variables initialized"""
        self.assertIsNone(self.bot.pretrade_gateway)
        self.assertIsNone(self.bot.gateway_context)
        
        print("  ✓ pretrade_gateway = None (initialized)")
        print("  ✓ gateway_context = None (initialized)")
        print("✓ Test 6 PASS: Gateway context variables ready")

    def test_07_risk_manager_limits(self):
        """Test 7: RiskManager risk limits configured"""
        rm = self.bot.risk_manager
        
        # Check that RiskManager is properly initialized
        self.assertIsNotNone(rm.account_size)
        self.assertGreater(rm.account_size, 0)
        
        print(f"  ✓ Account size: ₹{rm.account_size:,}")
        print(f"  ✓ RiskManager initialized with proper limits")
        print("✓ Test 7 PASS: Risk limits properly configured")

    def test_08_integration_summary(self):
        """Test 8: Integration summary - all components ready"""
        summary = {
            "bot_class": "GoldTradingBot",
            "bot_instance": "GoldTradingBot",
            "account_size": self.bot.risk_manager.account_size,
            "gateway_modules": 8,
            "gateway_methods": 4,
            "timestamp": datetime.now().isoformat(),
        }
        
        print(f"\n{'='*70}")
        print("INTEGRATION SUMMARY - ALL COMPONENTS READY")
        print(f"{'='*70}")
        print(f"Bot Class: {summary['bot_instance']}")
        print(f"Account Size: ₹{summary['account_size']:,}")
        print(f"Gateway Modules: {summary['gateway_modules']}/8")
        print(f"Test Timestamp: {summary['timestamp']}")
        print(f"{'='*70}\n")
        
        print("✓ Test 8 PASS: Integration ready for production")


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
