#!/usr/bin/env python3
"""
Monitors the MCX paper trading logs and sends a summary alert via Telegram.
"""

import os
import pandas as pd
import requests

# --- Configuration ---
EQUITY_LOG = "logs/paper_equity_mcx.csv"
TRADES_LOG = "logs/paper_trades_mcx.csv"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") # Recommended to use environment variables
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Fallback to hardcoded values if environment variables are not set (for simplicity)
if not TELEGRAM_BOT_TOKEN:
    TELEGRAM_BOT_TOKEN = "8553846324:AAFYGH0dqjqimYDsAdKWwnRBYs-GMc-D5pU"
if not TELEGRAM_CHAT_ID:
    TELEGRAM_CHAT_ID = "8410246010"

def send_telegram_alert(message):
    """Sends a message to the configured Telegram chat."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERROR: Telegram token or chat ID is not configured.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("Telegram alert sent successfully.")
        else:
            print(f"Failed to send Telegram alert: {response.text}")
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")

def generate_summary():
    """Generates a summary message from the latest log files."""
    
    # --- Equity Summary ---
    if not os.path.exists(EQUITY_LOG):
        return f"*[MCX] Trading Alert*\n\nERROR: Equity log file not found at `{EQUITY_LOG}`."

    try:
        equity_df = pd.read_csv(EQUITY_LOG)
        if equity_df.empty:
            return f"*[MCX] Trading Alert*\n\nWARNING: Equity log file `{EQUITY_LOG}` is empty."
        
        latest_equity = equity_df.iloc[-1]
        equity = latest_equity['equity']
        timestamp = pd.to_datetime(latest_equity['timestamp']).strftime('%Y-%m-%d %H:%M')
        
        summary = f"*[MCX] Daily Paper Trading Summary*\n"
        summary += f"`Timestamp: {timestamp}`\n"
        summary += f"`Equity: ₹{equity:,.2f}`\n"
        
    except Exception as e:
        return f"*[MCX] Trading Alert*\n\nERROR: Could not read equity log. Details: {e}"

    # --- Last Trade Summary ---
    if not os.path.exists(TRADES_LOG):
        summary += "\nNo trades have been logged yet."
        return summary

    try:
        trades_df = pd.read_csv(TRADES_LOG)
        if not trades_df.empty:
            last_trade = trades_df.iloc[-1]
            pnl = last_trade['pnl']
            exit_date = pd.to_datetime(last_trade['exit_date']).strftime('%Y-%m-%d')
            
            summary += f"\n*Last Trade (Closed {exit_date})*\n"
            summary += f"`P&L: ₹{pnl:,.2f}`"
        else:
            summary += "\nNo trades have been logged yet."
            
    except Exception as e:
        summary += f"\nWARNING: Could not read trades log. Details: {e}"
        
    return summary

def main():
    """Main monitoring function."""
    print("=" * 60)
    print("MCX PAPER TRADING MONITOR")
    print("=" * 60)
    
    message = generate_summary()
    print("Generated Summary:\n" + message)
    send_telegram_alert(message)
    
    print("Monitoring run complete.")
    print("=" * 60)

if __name__ == "__main__":
    main()
