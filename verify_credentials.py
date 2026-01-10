# verify_credentials.py
import json
import sys

def main():
    """
    Loads credentials from config.json and prints them for verification.
    """
    print("[*] Loading credentials from config.json for verification...")
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)

        print("\n" + "="*50)
        print("PLEASE VERIFY YOUR CREDENTIALS")
        print("="*50)

        # Verify Telegram Credentials
        print("\n--- Telegram ---")
        if 'telegram' in config:
            print(f"  Bot Token: {config['telegram'].get('bot_token', 'NOT FOUND')}")
            print(f"  Chat ID:   {config['telegram'].get('chat_id', 'NOT FOUND')}")
        else:
            print("  'telegram' section not found.")

        # Verify Email Credentials
        print("\n--- Email Alerts ---")
        if 'email_alerts' in config:
            print(f"  Sender Email:    {config['email_alerts'].get('sender_email', 'NOT FOUND')}")
            print(f"  App Password:    {config['email_alerts'].get('app_password', 'NOT FOUND')}")
            print(f"  Recipient Email: {config['email_alerts'].get('recipient_email', 'NOT FOUND')}")
        else:
            print("  'email_alerts' section not found.")
            
        print("\n" + "="*50)
        print("[*] Verification complete. Check the values above.")

    except FileNotFoundError:
        print("\n[-] ERROR: config.json not found. Please ensure the file exists in the same directory.")
        sys.exit(1)
    except json.JSONDecodeError:
        print("\n[-] ERROR: Could not decode config.json. Please check for syntax errors.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[-] An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
