import unittest
import sys
import os

# Fix Path to allow importing from root
sys.path.append(os.getcwd())

from strategies.pricing import GoldPricingEngine
from execution.paper_broker import PaperBroker

class TestGoldBot(unittest.TestCase):

    def setUp(self):
        """Runs before every test. Sets up a fresh 'Shadow Broker'."""
        # Use a temporary file so we don't mess up your real trading history
        self.test_state_file = "tests/test_state.json"
        
        # Initialize Broker with $10,000 for testing
        self.broker = PaperBroker(state_file=self.test_state_file, initial_capital=10000.0)
        
        # Clean slate
        if os.path.exists(self.test_state_file):
            os.remove(self.test_state_file)
            
    def tearDown(self):
        """Runs after every test. Cleans up."""
        if os.path.exists(self.test_state_file):
            os.remove(self.test_state_file)

    # --- TEST 1: PRICING PHYSICS (Protocol 3.1) ---
    def test_pip_calculation(self):
        """Does 50 Pips actually equal $5.00?"""
        entry_price = 2600.00
        sl_pips = 50
        tp_pips = 100
        
        # Calculate
        sl, tp = GoldPricingEngine.calculate_sl_tp(entry_price, 1, sl_pips, tp_pips)
        
        print(f"\n🧪 Test 1: Physics | Entry: {entry_price} | SL: {sl} | TP: {tp}")
        
        # Verify Math: 50 pips * $0.10 = $5.00 distance
        self.assertEqual(sl, 2595.00) # 2600 - 5
        self.assertEqual(tp, 2610.00) # 2600 + 10

    # --- TEST 2: MARGIN CALL (Protocol 3.3) ---
    def test_margin_rejection(self):
        """Does the broker reject trades we can't afford?"""
        # Attempt to buy 100 Lots of Gold (Value ~ $26 Million)
        # Account only has $10,000
        qty = 100 
        price = 2600.00
        
        has_margin, req_margin = self.broker.check_margin(price, qty)
        
        print(f"🧪 Test 2: Margin  | Req: ${req_margin:,.2f} | Has: $10,000")
        
        # Should be False
        self.assertFalse(has_margin)

    # --- TEST 3: FLASH CRASH (Protocol 5.2) ---
    def test_flash_crash_pnl(self):
        """If price crashes $50 instantly, do we calculate the loss correctly?"""
        # 1. Buy 1 Lot at $2600
        self.broker.place_order(1, "XAUUSD", 2600.00, 1.0, date="NOW")
        
        # 2. Force Flash Crash to $2550 (Exit)
        crash_price = 2550.00
        
        # 3. Close Trade
        self.broker.place_order(2, "XAUUSD", crash_price, 1.0, date="NOW")
        
        # 4. Verify Loss
        # Loss = ($2550 - $2600) * 100 oz = -$5000
        # Commission = $7
        # Expected Net = -$5007 (plus spread/slippage variance)
        
        history = self.broker._load_state()['history']
        last_trade = history[-1]
        pnl = last_trade['pnl']
        
        print(f"🧪 Test 3: Crash   | Drop: $50 | PnL: ${pnl:.2f}")
        
        # Assert we lost money (allowing for slippage variance)
        self.assertTrue(pnl < -5000)

if __name__ == '__main__':
    unittest.main()
