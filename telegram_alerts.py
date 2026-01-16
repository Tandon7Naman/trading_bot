# -*- coding: utf-8 -*-
import requests

# --- PASTE YOUR KEYS HERE ---
BOT_TOKEN = "8553846324:AAFYGH0dqjqimYDsAdKWwnRBYs-GMc-D5pU" 
CHAT_ID = "8410246010"

def send_telegram_message(message):
    # This function sends a simple text message to your phone
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("   SUCCESS: Telegram Alert Sent!")
        else:
            print(f"   FAIL: {response.text}")
    except Exception as e:
        print(f"   ERROR: {e}")

if __name__ == "__main__":
    print("Testing connection...")
    send_telegram_message("Hello Naman. The Gold Bot is online.")

Open Positions: {summary_data.get('open_positions', 0)}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            return self.send_message(message.strip())
        except Exception as e:
            logging.error(f"Error sending summary: {str(e)}")
            return False
    
    def send_error_alert(self, error_message, error_type='ERROR'):
        """Send error/warning alert"""
        try:
            message = f"""
<b>⚠️ {error_type} ALERT</b>

{error_message}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            return self.send_message(message.strip())
        except Exception as e:
            logging.error(f"Error sending error alert: {str(e)}")
            return False
    
    def send_market_news_alert(self, news_title, sentiment, polarity):
        """Send market news alert"""
        try:
            sentiment_emoji = "📈" if sentiment == 'POSITIVE' else "📉"
            message = f"""
<b>📰 MARKET NEWS {sentiment_emoji}</b>

Title: {news_title}
Sentiment: {sentiment}
Polarity: {polarity:.2f}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            return self.send_message(message.strip())
        except Exception as e:
            logging.error(f"Error sending news alert: {str(e)}")
            return False

def main():
    """Example usage of Telegram alerts"""
    print("[*] Testing Telegram Alerts...")
    
    # Replace with your actual bot token and chat ID
    BOT_TOKEN = 'YOUR_BOT_TOKEN'
    CHAT_ID = 'YOUR_CHAT_ID'
    
    alerts = TelegramAlerts(BOT_TOKEN, CHAT_ID)
    
    # Test alert
    alerts.send_message("🤖 Gold Trading Bot is online!")
