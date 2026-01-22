# main_bot_advanced.py
"""
GOLD TRADING BOT - ADVANCED VERSION
Integrates all modules for complete automated trading
"""

import logging
import os
import sys
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    filename="logs/main_bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

print("\n" + "=" * 80)
print(f"[*] GOLD TRADING BOT (ADVANCED) - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80 + "\n")

try:
    # PHASE 1: Initialize Bot
    print("[*] PHASE 1: Initializing bot...")

    # Load configuration from environment variables
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    sender_email = os.getenv("GMAIL_SENDER")
    app_password = os.getenv("GMAIL_PASSWORD")
    recipient_email = os.getenv("RECIPIENT_EMAIL")
    paper_trading_api_choice = os.getenv("PAPER_TRADING_API_CHOICE", "paper")
    paper_trading_initial_capital = float(os.getenv("PAPER_TRADING_INITIAL_CAPITAL", "100000"))
    paper_trading_trade_quantity = int(os.getenv("PAPER_TRADING_TRADE_QUANTITY", "10"))
    backtest_tp_percent = float(os.getenv("BACKTEST_TP_PERCENT", "2.0"))
    backtest_sl_percent = float(os.getenv("BACKTEST_SL_PERCENT", "1.0"))

    # Import all modules
    from telegram_alerts import TelegramAlerts

    from email_alerts import EmailAlerts
    from paper_trading import PaperTradingEngine
    from risk_management import RiskManager

    # Initialize components
    telegram = TelegramAlerts(telegram_bot_token, telegram_chat_id)

    email = EmailAlerts(sender_email, app_password, recipient_email)

    paper_trading = PaperTradingEngine(
        api_choice=paper_trading_api_choice, initial_capital=paper_trading_initial_capital
    )

    risk_manager = RiskManager(
        initial_capital=paper_trading_initial_capital,
        max_risk_percent=2.0,
        max_drawdown_percent=5.0,
    )

    print("[+] Bot initialized successfully\n")
    logging.info("Bot initialized successfully")

    # PHASE 2: Update Data
    print("[*] PHASE 2: Updating market data...")

    try:
        from update_gld_data import main as update_gld_data

        update_gld_data()
        print("[+] Market data updated successfully\n")
        logging.info("Market data updated")
    except Exception as e:
        print(f"[!] Data update warning: {str(e)}")
        logging.warning(f"Data update issue: {str(e)}")

    # PHASE 3: Generate Signals
    print("[*] PHASE 3: Generating trading signals...")

    try:
        from backtest_strategy_rulebased import RuleBasedBacktestEngine

        df = pd.read_csv("data/gld_data.csv")

        engine = RuleBasedBacktestEngine(
            initial_capital=paper_trading_initial_capital,
            tp_percent=backtest_tp_percent,
            sl_percent=backtest_sl_percent,
        )

        df = engine.generate_signals(df)

        latest_signal = df["Signal"].iloc[-1] if len(df) > 0 else 0
        latest_close = df["close"].iloc[-1] if len(df) > 0 else 0

        if latest_signal == 1:
            print(f"[+] BUY signal generated @ ₹{latest_close:.2f}")
            logging.info(f"BUY signal: {latest_close}")
            signal_type = "BUY"
        elif latest_signal == -1:
            print(f"[+] SELL signal generated @ ₹{latest_close:.2f}")
            logging.info(f"SELL signal: {latest_close}")
            signal_type = "SELL"
        else:
            print(f"[*] No signal (neutral) @ ₹{latest_close:.2f}")
            signal_type = "NEUTRAL"

        print()

    except Exception as e:
        print(f"[-] Signal generation error: {str(e)}")
        logging.error(f"Signal error: {str(e)}")
        signal_type = "ERROR"

    # PHASE 4: Execute Trade (if signal)
    print("[*] PHASE 4: Executing trade with risk management...")

    if signal_type in ["BUY", "SELL"]:
        try:
            # Check risk manager
            can_trade, reason = risk_manager.should_trade(0.75)

            if not can_trade:
                print(f"[!] Trade blocked by risk manager: {reason}")
                logging.warning(f"Trade blocked: {reason}")
            else:
                symbol = "GLD"
                quantity = paper_trading_trade_quantity
                price = latest_close
                trade_id = f"BOT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                if signal_type == "BUY":
                    paper_trading.place_buy_order(symbol, quantity, price, trade_id)
                    telegram.send_buy_alert(symbol, price, quantity, "Advanced Signal")
                    email.send_trade_alert(
                        {"type": "BUY", "entry_price": price, "quantity": quantity}
                    )
                    print(f"[+] BUY order executed: {symbol} x{quantity} @ ₹{price:.2f}")
                    logging.info(f"BUY trade executed: {quantity} units @ {price}")

                elif signal_type == "SELL":
                    paper_trading.place_sell_order(symbol, quantity, price, trade_id)
                    telegram.send_sell_alert(
                        symbol, price, price, quantity, 0, 0, "Advanced Signal"
                    )
                    email.send_trade_alert(
                        {"type": "SELL", "entry_price": price, "quantity": quantity}
                    )
                    print(f"[+] SELL order executed: {symbol} x{quantity} @ ₹{price:.2f}")
                    logging.info(f"SELL trade executed: {quantity} units @ {price}")

        except Exception as e:
            print(f"[-] Trade execution error: {str(e)}")
            logging.error(f"Trade error: {str(e)}")
    else:
        print(f"[*] No trade executed (signal: {signal_type})")

    print()

    # PHASE 5: Generate Reports
    print("[*] PHASE 5: Generating reports and sending alerts...")

    try:
        from performance_analytics import PerformanceAnalytics

        analytics = PerformanceAnalytics()
        metrics = analytics.calculate_all_metrics()

        if metrics:
            print("[+] Performance metrics calculated:")
            print(f"    Total P&L: ₹{metrics.get('Total P&L', 0):.2f}")
            print(f"    Win Rate: {metrics.get('Win Rate (%)', 0):.2f}%")
            print(f"    Total Trades: {metrics.get('Total Trades', 0)}")

        # Generate HTML report
        if analytics.generate_html_report():
            print("[+] HTML report generated: reports/performance_report.html")

    except Exception as e:
        print(f"[!] Analytics warning: {str(e)}")
        logging.warning(f"Analytics issue: {str(e)}")

    # Get account summary
    try:
        account_summary = paper_trading.get_account_summary()

        if account_summary:
            print("\n[+] Account Summary:")
            print(f"    Current Balance: ₹{account_summary.get('current_balance', 0):.2f}")
            print(f"    Total Trades: {account_summary.get('total_trades', 0)}")
            print(f"    Win Rate: {account_summary.get('win_rate', 0):.2f}%")

            # Send daily summary via email
            email.send_daily_summary(account_summary)
            telegram.send_daily_summary(account_summary)

    except Exception as e:
        print(f"[!] Summary warning: {str(e)}")
        logging.warning(f"Summary issue: {str(e)}")

    print()

    # COMPLETION
    print("=" * 80)
    print(f"[+] BOT CYCLE COMPLETED SUCCESSFULLY AT {datetime.now().strftime('%H:%M%S')}")
    print("=" * 80 + "\n")

    logging.info("Bot cycle completed successfully")
    sys.exit(0)

except Exception as e:
    print(f"\n[-] FATAL ERROR: {str(e)}")
    print("=" * 80 + "\n")
    logging.error(f"Fatal error: {str(e)}")
    sys.exit(1)
