import requests
from config.settings import TELEGRAM_CONFIG

def send_telegram_message(message):
    """
    Protocol 7.3: Sends alerts to mobile device via Telegram.
    Fails silently if config is missing to prevent bot crashes.
    """
    if not TELEGRAM_CONFIG.get('enabled'):
        return

    token = TELEGRAM_CONFIG.get('bot_token')
    chat_id = TELEGRAM_CONFIG.get('chat_id')
    
    if not token or "YOUR_BOT" in token:
        # User hasn't set keys yet, just ignore
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": f"🤖 GOLD BOT:\n{message}",
        "parse_mode": "Markdown"
    }
    
    try:
        # Set a short timeout so trading logic isn't blocked by slow internet
        requests.post(url, json=payload, timeout=3)
    except Exception as e:
        print(f"   ⚠️ Telemetry Error: {e}")
