# telegram_alerts.py
import requests
import logging
from datetime import datetime
import json

logging.basicConfig(
    filename='logs/telegram_alerts.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class TelegramAlerts:
    """Send trading alerts via Telegram"""
    
    def __init__(self, bot_token, chat_id):
        """
        Initialize Telegram bot
        Get bot token from BotFather: https://t.me/botfather
        Get chat ID from your chat with the bot
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, message, parse_mode='HTML'):
        """Send plain text message"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logging.info(f"Message sent successfully")
                return True
            else:
                logging.error(f"Failed to send message: {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Error sending message: {str(e)}")
            return False
    
    def send_buy_alert(self, symbol, price, quantity, reason):
        """Send BUY signal alert"""
        try:
            message = f"""
<b>🟢 BUY SIGNAL</b>
Symbol: {symbol}
Entry Price: ₹{price:.2f}
Quantity: {quantity}
Reason: {reason}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            return self.send_message(message.strip())
        except Exception as e:
            logging.error(f"Error sending BUY alert: {str(e)}")
            return False
    
    def send_sell_alert(self, symbol, entry_price, exit_price, quantity, pnl, pnl_percent, reason):
        """Send SELL signal alert"""
        try:
            pnl_emoji = "📈" if pnl > 0 else "📉"
            message = f"""
<b>🔴 SELL SIGNAL {pnl_emoji}</b>
Symbol: {symbol}
Entry Price: ₹{entry_price:.2f}
Exit Price: ₹{exit_price:.2f}
Quantity: {quantity}
P&L: ₹{pnl:.2f} ({pnl_percent:+.2f}%)
Reason: {reason}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            return self.send_message(message.strip())
        except Exception as e:
            logging.error(f"Error sending SELL alert: {str(e)}")
            return False
    
    def send_daily_summary(self, summary_data):
        """Send daily trading summary"""
        try:
            message = f"""
<b>📊 DAILY TRADING SUMMARY</b>

Initial Capital: ₹{summary_data.get('initial_capital', 0):.2f}
Current Balance: ₹{summary_data.get('current_balance', 0):.2f}
Total P&L: ₹{summary_data.get('total_realized_pnl', 0):.2f}

Total Trades: {summary_data.get('total_trades', 0)}
Winning Trades: {summary_data.get('winning_trades', 0)}
Losing Trades: {summary_data.get('losing_trades', 0)}
Win Rate: {summary_data.get('win_rate', 0):.2f}%

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
