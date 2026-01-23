import sys
import os

# Ensure we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from gold_trading_bot.config_schema import BotConfig
from gold_trading_bot.utils.logger import safe_execute, logger
from pydantic import ValidationError

def test_config_security():
    print("\n🔹 TEST 1: Configuration Security Guards")
    print("-" * 50)
    
    # Scenario A: Invalid Symbol
    try:
        print("Attempting to initialize with symbol 'INVALID'...")
        BotConfig(authorized_account_id=123, symbol="INVALID")
        print("❌ FAILED: Bad symbol was accepted!")
    except ValidationError as e:
        print("✅ PASSED: Pydantic blocked invalid symbol.")

    # Scenario B: Dangerous Lot Size (Negative)
    try:
        print("\nAttempting to initialize with Lot Size -5.0...")
        BotConfig(authorized_account_id=123, risk={"max_lot_size": -5.0})
        print("❌ FAILED: Negative lot size was accepted!")
    except ValidationError as e:
        print("✅ PASSED: Pydantic blocked negative lot size.")

def test_crash_containment():
    print("\n🔹 TEST 2: Runtime Crash Containment")
    print("-" * 50)

    @safe_execute
    def risky_operation():
        print("Attempting dangerous math operation...")
        # Intentional Crash
        result = 1 / 0 
        return result

    # Run the risky function
    risky_operation()
    
    # Verify the log file exists and contains the error
    if os.path.exists("logs/audit_trace.log"):
        with open("logs/audit_trace.log", "r") as f:
            logs = f.read()
            if "ZeroDivisionError" in logs:
                print("\n✅ PASSED: Stack trace successfully hidden from console and saved to audit log.")
            else:
                print("\n❌ FAILED: Error not found in log file.")
    else:
        print("\n❌ FAILED: Log file was not created.")

if __name__ == "__main__":
    test_config_security()
    test_crash_containment()
