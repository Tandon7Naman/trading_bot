# -*- coding: utf-8 -*-
import requests
import os
from dotenv import load_dotenv

# 1. Load the secrets from the .env file
load_dotenv()

# 2. Fetch the keys safely
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message):
    # Security Check: Did we find the keys?
    if not BOT_TOKEN or not CHAT_ID:
        print("   ❌ ERROR: Could not find API keys in .env file!")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("   ✅ Secure Alert Sent!")
        else:
            print(f"   ❌ Failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Connection Error: {e}")

if __name__ == "__main__":
    print("Testing Secure Connection...")
    send_telegram_message("Security Upgrade Complete! Keys are hidden.")
