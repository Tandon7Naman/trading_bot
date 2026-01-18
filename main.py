import asyncio
import sys
import os

# Fix Path to allow importing from root
sys.path.append(os.getcwd())

# Import Strategy
from strategies.xauusd_strategy import check_market

async def run_pipeline(asset_name, strategy_func):
    """
    Runs a specific strategy loop forever.
    """
    print(f"   ✨ Pipeline Started: {asset_name}")
    
    while True:
        try:
            # Execute the strategy logic
            await strategy_func()
            
            # Protocol 4.2: Dynamic Sleep? 
            # For now, we use a fixed heartbeat of 60 seconds
            # In Live Mode, this would be faster (e.g., 1s)
            await asyncio.sleep(60)
            
        except asyncio.CancelledError:
            print(f"   🛑 {asset_name} Pipeline Stopped.")
            break
        except Exception as e:
            print(f"   ⚠️ Error in {asset_name} pipeline: {e}")
            await asyncio.sleep(5) # Short cool-down on minor errors

async def main():
    """
    Protocol 7.2: The Supervisor Loop
    Manages the lifecycle of the bot with Exponential Backoff.
    """
    print("🤖 STARTING ASYNC TRADING ENGINE (Protocol 7.2 Robustness)...")
    
    # Configuration
    active_pipelines = ["XAUUSD"]
    print(f"   ACTIVE PIPELINES: {active_pipelines}\n")
    
    # Exponential Backoff Variables
    restart_delay = 1
    max_delay = 60 # Cap wait time at 60 seconds
    
    while True:
        try:
            # 1. Create Tasks for all active pipelines
            tasks = []
            if "XAUUSD" in active_pipelines:
                tasks.append(run_pipeline("XAUUSD", check_market))
                
            # 2. Run them all concurrently
            # asyncio.gather will run until the first error crashes it (if not handled inside)
            # or until we stop it.
            await asyncio.gather(*tasks)
            
            # If gather finishes cleanly, reset delay
            restart_delay = 1
            
        except KeyboardInterrupt:
            print("\n👋 Manual Stop Received. Shutting down.")
            break
            
        except Exception as e:
            # PROTOCOL 7.2: EXPONENTIAL BACKOFF
            print(f"\n🚨 CRITICAL ENGINE CRASH: {e}")
            print(f"   ⏳ Rebooting in {restart_delay} seconds...")
            
            await asyncio.sleep(restart_delay)
            
            # Double the delay for next time (1, 2, 4, 8...), capped at max_delay
            restart_delay = min(max_delay, restart_delay * 2)
            print("   ♻️  Restarting System...\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass