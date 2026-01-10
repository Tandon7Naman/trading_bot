# test_telegram.py
import json
from telegram_alerts import TelegramAlerts
import sys

def main():
    """
    Tests the TelegramAlerts functionality by sending a test message.
    """
    print("[*] Testing Telegram integration...")
    try:
        # Load configuration
        with open('config.json', 'r') as f:
            config = json.load(f)

        # Initialize TelegramAlerts
        telegram = TelegramAlerts(
            config['telegram']['bot_token'],
            config['telegram']['chat_id']
        )

        # Send a test message
        message = "Hello from the Gold Trading Bot! This is a test message to confirm Telegram integration is working."
        telegram.send_message(message)

        print("[+] Test message sent successfully to Telegram.")
        print("[*] Please check your Telegram chat to confirm receipt.")

    except FileNotFoundError:
        print("[-] Error: config.json not found. Please ensure the file exists.")
        sys.exit(1)
    except KeyError:
        print("[-] Error: 'telegram' section or its keys ('bot_token', 'chat_id') not found in config.json.")
        sys.exit(1)
    except Exception as e:
        print(f"[-] An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
