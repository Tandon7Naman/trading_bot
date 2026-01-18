import sys
import os
import time

# Ensure we can import from the execution folder
sys.path.append(os.getcwd())

from execution.paper_broker import PaperBroker

def run_test():
    print("🧪 STARTING UNIT TEST: Paper Broker Logic")
    
    # 1. Setup Dummy Test File
    test_file = "data/test_state.json"
    if os.path.exists(test_file):
        os.remove(test_file)
        
    broker = PaperBroker(state_file=test_file, initial_capital=100000)
    print("✅ Broker Initialized (Test Mode)")

    # 2. Test BUY Execution
    price_buy = 50000.0
    print(f"   Attempting BUY at ₹{price_buy}...")
    # Action 1 = BUY
    broker.execute_trade(1, price_buy, "2024-01-01 10:00:00", 50.0)
    
    acct = broker.get_account_info()
    if isinstance(acct['position'], dict) and acct['position']['entry_price'] == price_buy:
        print("   ✅ BUY Order Verified.")
    else:
        print("   ❌ BUY Order FAILED.")

    # 3. Test SELL Execution (Profit Scenario)
    price_sell = 52000.0 # ₹2000 profit * 10g = ₹20,000 Total Profit
    print(f"   Attempting SELL at ₹{price_sell}...")
    # Action 2 = SELL
    broker.execute_trade(2, price_sell, "2024-01-02 14:00:00", 70.0)
    
    acct = broker.get_account_info()
    expected_equity = 120000.0
    
    if acct['equity'] == expected_equity and acct['position'] == "FLAT":
        print(f"   ✅ SELL Order Verified. Final Equity: ₹{acct['equity']:,.2f}")
    else:
        print(f"   ❌ SELL Order FAILED. Got: {acct['equity']}")

    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)
    print("🧪 TEST COMPLETE.")

if __name__ == "__main__":
    run_test()
