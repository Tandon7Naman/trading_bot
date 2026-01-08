import pandas as pd
import os
import smtplib
import requests
from email.mime.text import MIMEText

# --- Configuration for Alerts ---
# Choose your alert method: 'email', 'telegram', or 'print'
# Change 'print' to 'telegram'
ALERT_METHOD = 'telegram'  # Change to 'email' or 'telegram' after setup

# Email Configuration (for 'email' method)
SMTP_SERVER = "smtp.gmail.com"  # Example for Gmail
SMTP_PORT = 587
EMAIL_SENDER = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"  # Use an App Password for security
EMAIL_RECIPIENT = "recipient_email@example.com"

# Telegram Configuration (for 'telegram' method)
TELEGRAM_BOT_TOKEN = "8553846324:AAFYGH0dqjqimYDsAdKWwnRBYs-GMc-D5pU"
TELEGRAM_CHAT_ID = "8410246010"


def send_alert(subject, body):
    """Dispatches an alert based on the configured ALERT_METHOD."""
    print(f"Sending Alert:\nSubject: {subject}\nBody: {body}")

    if ALERT_METHOD == 'email':
        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = EMAIL_SENDER
            msg['To'] = EMAIL_RECIPIENT

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.sendmail(EMAIL_SENDER, [EMAIL_RECIPIENT], msg.as_string())
            print("Email alert sent successfully.")
        except Exception as e:
            print(f"Failed to send email alert: {e}")

    elif ALERT_METHOD == 'telegram':
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': f"{subject}\n\n{body}"
            }
            response = requests.post(url, data=payload)
            if response.status_code == 200:
                print("Telegram alert sent successfully.")
            else:
                print(f"Failed to send Telegram alert: {response.text}")
        except Exception as e:
            print(f"Failed to send Telegram alert: {e}")


def monitor_paper_trading(log_file="logs/paper_equity.csv"):
    """
    Reads the paper trading equity log and sends a status alert.
    """
    if not os.path.exists(log_file):
        subject = "Trading Bot Alert: Log File Missing"
        body = f"The log file at '{log_file}' was not found. The paper trading task may have failed."
        send_alert(subject, body)
        return

    try:
        df = pd.read_csv(log_file, parse_dates=['timestamp'])
        if df.empty:
            subject = "Trading Bot Alert: Log File is Empty"
            body = f"The log file at '{log_file}' is empty. No trades may have occurred."
            send_alert(subject, body)
            return

        # Get the latest status
        latest_status = df.iloc[-1]
        timestamp = latest_status['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        equity = latest_status['equity']
        cash = latest_status['cash']
        
        subject = f"Daily Paper Trading Summary: ${equity:,.2f}"
        body = (
            f"Status at: {timestamp}\n"
            f"--------------------------\n"
            f"Total Equity: ${equity:,.2f}\n"
            f"Cash Balance: ${cash:,.2f}\n"
            f"--------------------------"
        )
        send_alert(subject, body)

    except Exception as e:
        subject = "Trading Bot Alert: Monitoring Failed"
        body = f"An error occurred while monitoring the paper trading bot:\n{e}"
        send_alert(subject, body)


if __name__ == "__main__":
    # The audit log is in the root, so we assume the equity log will be too.
    # Create the directory if it doesn't exist to prevent errors on first run.
    os.makedirs("logs", exist_ok=True)
    monitor_paper_trading()
