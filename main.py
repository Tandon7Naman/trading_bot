
import time
import sys
import os

# Ensure Python sees the 'strategies' folder
sys.path.append(os.getcwd())

try:
    # IMPORT THE NEW V3 BRAIN
    from strategies.gold_scalper import check_market
except ImportError as e:
    print(f"❌ CRITICAL ERROR: Could not import Strategy! {e}")
    sys.exit(1)

def run_bot():
    print("🤖 STARTING PROFESSIONAL TRADING ENGINE...")
    print("   Mode: Paper Trading (Live Data)")
    print("   Strategy: Gold Scalper V3 (Broker Integrated)")
    print("   Press Ctrl + C to stop.\n")

    while True:
        try:
            # 1. Run the Strategy Logic
            check_market()
            
            # 2. Sleep for 60 seconds (Standard Candle Time)
            print("😴 Sleeping for 60 seconds...")
            time.sleep(60)
            
        except KeyboardInterrupt:
            print("\n🛑 Bot Stopped by User.")
            break
        except Exception as e:
            print(f"\n❌ CRASH: {e}")
            time.sleep(10)

if __name__ == "__main__":
    run_bot()
