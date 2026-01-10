#!/usr/bin/env python3
"""
Monitor GLD paper trading and send daily Telegram alert
"""

import os
import pandas as pd
from datetime import datetime
from pathlib import Path
import requests

BASE_DIR = Path(__file__).resolve().parent
EQUITY_LOG = BASE_DIR / "logs" / "paper_equity.csv"
TRADES_LOG = BASE_DIR / "logs" / "paper_trades.csv"

# Telegram
TELEGRAM_BOT_TOKEN = "8553846324:AAFYGH0dqjqimYDsAdKWwnRBYs-GMc-D5pU"  # Replace with your token
TELEGRAM_CHAT_ID = "8410246010"  # Replace with your chat ID

def send_telegram_alert(subject: str, body: str):
    """Send alert to Telegram."""
    
    if not TELEGRAM_BOT_TOKEN or "YOUR_BOT_TOKEN" in TELEGRAM_BOT_TOKEN:
        print("⚠ Telegram credentials not configured. Skipping alert.")
        return
    
    message = f"*{subject}*\n\n{body}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"})
        print("Telegram alert sent successfully.")
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")

def monitor_paper_trading():
    """Read latest equity and send summary alert."""

    try:
        if not EQUITY_LOG.exists():
            raise FileNotFoundError(f"Log file at {EQUITY_LOG} not found. Paper trading may have failed.")
        
        # Read equity log
        df = pd.read_csv(EQUITY_LOG, parse_dates=['date'])
        
        if df.empty:
            raise ValueError("Equity log is empty.")
        
        # Get latest row
        latest = df.iloc[-1]
        latest_date = latest['date']
        latest_equity = latest['equity']
        latest_position = latest.get('position', 'UNKNOWN')
        
        # Read trades log if exists
        trades_today = 0
        if TRADES_LOG.exists():
            trades_df = pd.read_csv(TRADES_LOG)
            trades_today = len(trades_df)
        
        # Build message
        subject = "🟢 GLD Paper Trading Summary"
        body = f"""Status at: {latest_date.strftime('%Y-%m-%d %H:%M:%S')}
Total Equity: ₹{latest_equity:,.0f}
Position: {latest_position}
Trades Logged: {trades_today}

System running smoothly."""
        
        print("Sending Alert:")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        
        send_telegram_alert(subject, body)
        
    except Exception as e:
        subject = "🔴 Trading Bot Alert: Monitoring Failed"
        body = f"An error occurred while monitoring the paper trading bot:\n{str(e)}"
        
        print("Sending Alert:")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        
        send_telegram_alert(subject, body)

if __name__ == "__main__":
    monitor_paper_trading()
