import os

target = "data/XAUUSD_1m.csv"

if os.path.exists(target):
    try:
        os.remove(target)
        print(f"✅ SUCCESS: Deleted {target}")
        print("   The Bitcoin data is gone. You are ready for Gold.")
    except Exception as e:
        print(f"❌ ERROR: Could not delete file: {e}")
        print("   (Is another terminal holding it open?)")
else:
    print(f"⚠️ FILE NOT FOUND: {target}")
    print("   (Are you sure main.py is running from this folder?)")
