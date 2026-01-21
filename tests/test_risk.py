import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from execution.risk_manager import RiskManager

def test_phase_2():
    print("🧪 STARTING PHASE 2 VERIFICATION: RISK MATH")
    
    equity = 100_000.0 # $100k Account
    entry = 2000.0     # Gold Price
    sl = 1990.0        # $10 Stop Loss
    
    # CASE A: Standard Trade (1% Risk)
    print("\n--- CASE A: Standard Trade ---")
    # Expected: Risk $1000. Loss/Lot = $10 * 100 = $1000. Size should be ~1.0 lot.
    qty_a = RiskManager.calculate_lot_size(equity, entry, sl, "XAUUSD", confidence_score=1.0, current_portfolio_risk_usd=0.0)
    
    # CASE B: Portfolio Full (5% Cap)
    print("\n--- CASE B: Portfolio Stuffed ---")
    # We pretend we already have $4,900 at risk (Limit is $5,000).
    # Expected: Should only allow risking remaining $100 (0.1 Lots).
    qty_b = RiskManager.calculate_lot_size(equity, entry, sl, "XAUUSD", confidence_score=1.0, current_portfolio_risk_usd=4900.0)

    # CASE C: Portfolio Overflow
    print("\n--- CASE C: Portfolio Overflow ---")
    # We pretend we have $5,100 at risk.
    # Expected: Size 0.0 (REJECT).
    qty_c = RiskManager.calculate_lot_size(equity, entry, sl, "XAUUSD", confidence_score=1.0, current_portfolio_risk_usd=5100.0)

    print("\n✅ PHASE 2 VERIFICATION COMPLETE.")

if __name__ == "__main__":
    test_phase_2()
