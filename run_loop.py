import time
import subprocess
import sys
import os

# We need to find the specific Python that works on your machine
# This grabs the current Python executable you are using right now
current_python = sys.executable

print("🤖 STARTING AUTOMATED TRADING LOOP...")
print("Press Ctrl + C to stop at any time.")

while True:
    try:
        print("\n" + "="*40)
        print(f"⏰ Checking Market at {time.strftime('%H:%M:%S')}")
        
        # Run the paper trading bot using the exact same Python environment
        subprocess.run([current_python, "paper_trading_mcx.py"])
        
        print("😴 Sleeping for 60 seconds...")
        time.sleep(60)
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping the loop. Goodbye!")
        break
