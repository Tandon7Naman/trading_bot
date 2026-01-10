# email_alerts.py
"""
Email Alerts Module
- Sends email notifications as backup to Telegram
- Uses Gmail SMTP for reliable delivery
- Includes trade summaries and error alerts
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logging.basicConfig(
    filename='logs/email_alerts.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class EmailAlerts:
    def __init__(self, sender_email, app_password, recipient_email):
        """
        Initialize email alerts
        
        Args:
            sender_email: Gmail address (e.g., your@gmail.com)
            app_password: Gmail app password (16 chars with spaces)
            recipient_email: Email to receive alerts
        """
        self.sender_email = sender_email
        self.app_password = app_password
        self.recipient_email = recipient_email
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
    
    def send_email(self, subject, body, is_html=False):
        """Send email via Gmail SMTP"""
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.sender_email
            message['To'] = self.recipient_email
            
            if is_html:
                part = MIMEText(body, 'html')
            else:
                part = MIMEText(body, 'plain')
            
            message.attach(part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.app_password)
                server.send_message(message)
            
            logging.info(f"Email sent: {subject}")
            print(f"[+] Email sent: {subject}")
            return True
            
        except Exception as e:
            logging.error(f"Error sending email: {str(e)}")
            print(f"[-] Email send failed: {str(e)}")
            return False

    def send_trade_alert(self, trade_data):
        """Send trade execution alert"""
        try:
            subject = f"🏆 Trade Alert - {trade_data['type']} Signal"
            
            body = f"""
Gold Trading Bot - Trade Execution Alert

Type: {trade_data['type']}
Entry Price: ₹{trade_data.get('entry_price', 'N/A'):.2f}
Quantity: {trade_data.get('quantity', 'N/A')} units
Entry Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Signal Confidence: {trade_data.get('confidence', 'N/A')}
RSI: {trade_data.get('rsi', 'N/A')}
EMA20: {trade_data.get('ema20', 'N/A')}
EMA50: {trade_data.get('ema50', 'N/A')}

Take Profit: {trade_data.get('tp', 'N/A')}
Stop Loss: {trade_data.get('sl', 'N/A')}

---
This is an automated alert from Gold Trading Bot
            """
            
            return self.send_email(subject, body.strip())
            
        except Exception as e:
            logging.error(f"Error sending trade alert: {str(e)}")
            return False

    def send_daily_summary(self, summary_data):
        """Send daily trading summary"""
        try:
            subject = f"📊 Daily Summary - {datetime.now().strftime('%Y-%m-%d')}"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #333;">Gold Trading Bot - Daily Summary</h2>
                <p style="color: #666; font-size: 14px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <table style="border-collapse: collapse; width: 100%; margin-top: 20px;">
                    <tr style="background: #f0f0f0;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><b>Metric</b></td>
                        <td style="padding: 10px; border: 1px solid #ddd;"><b>Value</b></td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">Total Trades</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{summary_data.get('total_trades', 0)}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">Winning Trades</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{summary_data.get('winning_trades', 0)}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">Losing Trades</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{summary_data.get('losing_trades', 0)}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">Win Rate</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{summary_data.get('win_rate', 0):.2f}%</td>
                    </tr>
                    <tr style="background: #e8f5e9;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><b>Total P&L</b></td>
                        <td style="padding: 10px; border: 1px solid #ddd;"><b>${summary_data.get('total_pnl', 0):.2f}</b></td>
                    </tr>
                </table>
                
                <p style="margin-top: 20px; color: #666; font-size: 12px;">
                    This is an automated summary from Gold Trading Bot
                </p>
            </body>
            </html>
            """
            
            return self.send_email(subject, html_body, is_html=True)
            
        except Exception as e:
            logging.error(f"Error sending summary: {str(e)}")
            return False

    def send_error_alert(self, error_message):
        """Send error alert"""
        try:
            subject = f"🚨 Bot Error Alert - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            body = f"""
GOLD TRADING BOT - ERROR ALERT

Error Message:
{error_message}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please check logs for details.

---
Automated error notification from Gold Trading Bot
            """
            
            return self.send_email(subject, body.strip())
            
        except Exception as e:
            logging.error(f"Error sending error alert: {str(e)}")
            return False

def main():
    print("\n" + "="*70)
    print("EMAIL ALERTS SYSTEM TEST")
    print("="*70 + "\n")
    
    print("[*] Email Alerts System")
    print("[*] Configuration required in config.json:")
    print("    - email_alerts.sender_email: your@gmail.com")
    print("    - email_alerts.app_password: (get from Gmail Account)")
    print("    - email_alerts.recipient_email: recipient@email.com")
    print("\n[!] To get Gmail App Password:")
    print("    1. Go to https://myaccount.google.com/apppasswords")
    print("    2. Select 'Mail' and 'Windows Computer'")
    print("    3. Copy the 16-character password")
    print("    4. Paste into config.json")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
