import asyncio
import sys
import os

sys.path.append(os.getcwd())

from strategies.xauusd_strategy import check_market
from execution.data_handler import AsyncDataHandler
from execution.paper_broker import PaperBroker # <--- Protocol 1.3: Import Broker

def run_startup_reconciliation(active_pipelines):
    """
    Protocol 1.3: State Reconciliation.
    Queries the Broker (Source of Truth) before the engine starts.
    Detects and Adopts 'Ghost Trades' from previous sessions.
    """
    print("   🔍 RUNNING STARTUP RECONCILIATION (Protocol 1.3)...")
    
    # In a real scenario, we would loop through all symbols.
    # Here we check our primary Paper Broker.
    try:
        broker = PaperBroker()
        account_state = broker.get_positions()
        position = account_state['position']
        equity = account_state['equity']
        
        print(f"      💰 Account Balance: ${equity:,.2f}")
        
        if position == "FLAT":
            print("      ✅ Broker State: FLAT (No open positions).")
            print("      ✨ System is clean. Ready to SCAN.")
        else:
            # Found an open trade!
            symbol = position['symbol']
            side = position['type']
            entry = position['entry_price']
            print(f"      ⚠️ FOUND ACTIVE TRADE: {symbol} {side} @ {entry}")
            
            if symbol in active_pipelines:
                print(f"      🛡️ ACTION: Adopting trade into {symbol} Pipeline.")
            else:
                print(f"      ❌ WARNING: Trade found for {symbol}, but pipeline is INACTIVE.")
                
    except Exception as e:
        print(f"      ❌ RECONCILIATION FAILED: {e}")
        print("      ⚠️ System starting in blind mode (High Risk).")
        
    print("   ------------------------------------------------\n")

async def run_pipeline(asset_name, strategy_func):
    """Protocol 1.2: Pipeline with Async Data Ingestion."""
    print(f"   ✨ Pipeline Started: {asset_name}")
    
    # 1. Initialize & Start Data Buffer
    buffer = AsyncDataHandler(asset_name)
    await buffer.start()
    
    while True:
        try:
            # 2. Pass Buffer to Strategy
            await strategy_func(buffer)
            
            # Heartbeat Wait
            await asyncio.sleep(60)
            
        except asyncio.CancelledError:
            print(f"   🛑 {asset_name} Pipeline Stopped.")
            await buffer.stop()
            break
        except Exception as e:
            print(f"   ⚠️ Error in {asset_name} pipeline: {e}")
            await asyncio.sleep(5)

async def main():
    print("🤖 STARTING ASYNC TRADING ENGINE (Protocol 1.3 State Persistence)...")
    
    active_pipelines = ["XAUUSD"]
    print(f"   ACTIVE PIPELINES: {active_pipelines}\n")
    
    # --- PROTOCOL 1.3 EXECUTION ---
    # Run the handshake BEFORE starting the async loops
    run_startup_reconciliation(active_pipelines)
    
    restart_delay = 1
    max_delay = 60
    
    while True:
        try:
            tasks = []
            if "XAUUSD" in active_pipelines:
                tasks.append(run_pipeline("XAUUSD", check_market))
                
            await asyncio.gather(*tasks)
            restart_delay = 1
            
        except KeyboardInterrupt:
            print("\n👋 Manual Stop Received.")
            break
            
        except Exception as e:
            print(f"\n🚨 CRITICAL ENGINE CRASH: {e}")
            print(f"   ⏳ Rebooting in {restart_delay} seconds...")
            await asyncio.sleep(restart_delay)
            
            restart_delay = min(max_delay, restart_delay * 2)
            print("   ♻️  Restarting System...\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from strategies.xauusd_strategy import check_market
from execution.data_handler import AsyncDataHandler

async def run_pipeline(asset_name, strategy_func):
    """
    Protocol 1.2: Pipeline with Async Data Ingestion.
    """
    print(f"   ✨ Pipeline Started: {asset_name}")
    
    # 1. Initialize & Start Data Buffer
    buffer = AsyncDataHandler(asset_name)
    await buffer.start()
    
    while True:
        try:
            # 2. Pass Buffer to Strategy
            await strategy_func(buffer)
            
            # Heartbeat Wait
            await asyncio.sleep(60)
            
        except asyncio.CancelledError:
            print(f"   🛑 {asset_name} Pipeline Stopped.")
            await buffer.stop() # Clean up
            break
        except Exception as e:
            print(f"   ⚠️ Error in {asset_name} pipeline: {e}")
            await asyncio.sleep(5)

async def main():
    print("🤖 STARTING ASYNC TRADING ENGINE (Protocol 1.2 Async I/O)...")
    
    active_pipelines = ["XAUUSD"]
    print(f"   ACTIVE PIPELINES: {active_pipelines}\n")
    
    restart_delay = 1
    max_delay = 60
    
    while True:
        try:
            tasks = []
            if "XAUUSD" in active_pipelines:
                # We launch the pipeline wrapper
                tasks.append(run_pipeline("XAUUSD", check_market))
                
            await asyncio.gather(*tasks)
            restart_delay = 1
            
        except KeyboardInterrupt:
            print("\n👋 Manual Stop Received.")
            break
            
        except Exception as e:
            print(f"\n🚨 CRITICAL ENGINE CRASH: {e}")
            print(f"   ⏳ Rebooting in {restart_delay} seconds...")
            await asyncio.sleep(restart_delay)
            
            # Corrected Indentation Here
            restart_delay = min(max_delay, restart_delay * 2)
            print("   ♻️  Restarting System...\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass