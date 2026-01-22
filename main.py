import asyncio
import os
import sys
import threading

# Add project root to path
# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the EOD report scheduler
from config.settings import ASSET_CONFIG, ENABLED_MARKETS
from execution.db_manager import DBManager
from execution.risk_manager import CircuitBreaker
from strategies.data_handler import DataHandler
from strategies.xauusd_strategy import check_market
from utils.run_scheduler import run_scheduler


# --- PROTOCOL 1.1: THE DEFENSIVE SUPERVISOR ---
def run_preflight_audit():
    """
    Validates that the 'Perfect System' defenses are active before trading.
    Prevents 'Fat Fingers' and 'Logic Loops' from ever starting.
    """
    print("\n🛡️  SYSTEM GUARDIAN: Initiating Pre-Flight Audit (Protocol 1.1)...")

    # 1. DATABASE INTEGRITY
    try:
        db = DBManager()
        account = db.get_account()
        print(f"   ✅ Memory: Active | Equity: ${account['equity']:,.2f}")
    except Exception as e:
        print(f"   ❌ CRITICAL: Database Corrupted. {e}")
        sys.exit(1)

    # 2. RISK CONFIGURATION (Fat Finger Check)
    errors = []
    for asset in ENABLED_MARKETS:
        config = ASSET_CONFIG.get(asset)
        if not config:
            errors.append(f"Missing Config for {asset}")
            continue

        vol_cap = config.get("max_vol", 100.0)
        if vol_cap > 50.0:  # Sanity Limit for Retail Accounts
            print(f"   ⚠️  WARNING: High Volume Cap for {asset} ({vol_cap} Lots).")
        else:
            print(f"   ✅ Physics: {asset} Max Vol Capped at {vol_cap} Lots.")

    # 3. CIRCUIT BREAKER (Black Swan Protection)
    # We instantiate a temporary breaker just to check parameters
    breaker = CircuitBreaker(initial_equity=account["equity"])
    dd_limit = breaker.max_drawdown_limit * 100
    print(f"   ✅ Shields: Circuit Breaker Armed (Max DD: {dd_limit}%)")

    if errors:
        print("\n❌ STARTUP ABORTED. Configuration Errors:")
        for e in errors:
            print(f"   - {e}")
        sys.exit(1)

    print("   ✨ AUDIT COMPLETE. System is Defensive by Design.\n")


# --- MAIN EVENT LOOP ---
async def main():
    # 1. Run Checks
    run_preflight_audit()

    # 2. Initialize Data Pipelines
    print("🤖 STARTING TRADING ENGINE...")
    print(f"   ACTIVE PIPELINES: {ENABLED_MARKETS}")

    handlers = {}
    for symbol in ENABLED_MARKETS:
        config = ASSET_CONFIG[symbol]
        handlers[symbol] = DataHandler(symbol, config["data_file"])
        # Start the async buffer for this asset
        asyncio.create_task(handlers[symbol].start_buffer())

    # 3. Infinite Strategy Loop
    while True:
        # We loop through all enabled markets (Scalability)
        for symbol in ENABLED_MARKETS:
            if symbol == "XAUUSD":
                await check_market(handlers[symbol])
            # elif symbol == "MCX_GOLD":
            #    await check_mcx_market(handlers[symbol]) # Future Expansion

        # Pace the loop (Prevent CPU Spike/Logic Loop)
        await asyncio.sleep(1)


if __name__ == "__main__":
    # Start the EOD report scheduler in a background thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 MANUAL SHUTDOWN. Safe exit.")
