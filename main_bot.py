# main_bot.py
"""
Gold Trading Bot - Production Version
Uses proven rule-based technical analysis strategy
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import os
from dotenv import load_dotenv
import sys

# Import custom modules
from update_gld_data import main as update_gld_data
from fetch_market_news import main as fetch_news
from backtest_strategy_rulebased import RuleBasedBacktestEngine
from paper_trading import PaperTradingEngine
from telegram_alerts import TelegramAlerts

load_dotenv()

logging.basicConfig(
    filename='logs/main_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class GoldTradingBot:
    """Main bot orchestrator with rule-based strategy"""
    
    def __init__(self):
        """Initialize bot"""
        try:
            # Load configuration from environment variables
            self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
            self.paper_trading_api_choice = os.getenv("PAPER_TRADING_API_CHOICE", "paper")
            self.paper_trading_initial_capital = float(os.getenv("PAPER_TRADING_INITIAL_CAPITAL", "100000"))
            self.paper_trading_trade_quantity = int(os.getenv("PAPER_TRADING_TRADE_QUANTITY", "10"))
            self.backtest_tp_percent = float(os.getenv("BACKTEST_TP_PERCENT", "2.0"))
            self.backtest_sl_percent = float(os.getenv("BACKTEST_SL_PERCENT", "1.0"))

            # Initialize alerts
            self.alerts = TelegramAlerts(
                self.telegram_bot_token,
                self.telegram_chat_id
            )
            
            # Initialize paper trading
            self.paper_trading = PaperTradingEngine(
                api_choice=self.paper_trading_api_choice,
                initial_capital=self.paper_trading_initial_capital
            )
            
            logging.info("Bot initialized successfully")
            print("[+] Bot initialized successfully")
            
        except Exception as e:
            logging.error(f"Error initializing bot: {str(e)}")
            print(f"[-] Error initializing bot: {str(e)}")
            raise

    def update_data(self):
        """Update GLD and news data"""
        try:
            print("[*] Updating data...")
            
            # Update GLD data
            print("  [*] Updating GLD data...")
            update_gld_data()
            
            # Fetch news (optional)
            print("  [*] Fetching market news...")
            try:
                fetch_news()
            except Exception as e:
                logging.warning(f"News fetch failed: {str(e)}")
            
            logging.info("Data updated successfully")
            print("[+] Data updated successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error updating data: {str(e)}")
            self.alerts.send_error_alert(f"Data update failed: {str(e)}", "WARNING")
            print(f"[-] Error: {str(e)}")
            return False

    def run_backtest_and_get_signals(self):
        """Run backtest and get live trading signals"""
        try:
            print("[*] Running backtest analysis...")
            
            df = pd.read_csv('data/gld_data.csv')
            
            engine = RuleBasedBacktestEngine(
                initial_capital=self.paper_trading_initial_capital,
                tp_percent=self.backtest_tp_percent,
                sl_percent=self.backtest_sl_percent
            )
            
            # Generate signals
            df = engine.generate_signals(df)
            
            # Get latest signal
            latest_signal = df['Signal'].iloc[-1] if len(df) > 0 else 0
            latest_close = df['close'].iloc[-1] if len(df) > 0 else 0
            latest_ema20 = df['EMA_20'].iloc[-1] if 'EMA_20' in df.columns else 0
            latest_ema50 = df['EMA_50'].iloc[-1] if 'EMA_50' in df.columns else 0
            latest_rsi = df['RSI'].iloc[-1] if len(df) > 0 else 0
            
            signal_data = {
                'timestamp': datetime.now().isoformat(),
                'close': latest_close,
                'signal': int(latest_signal),
                'ema20': latest_ema20,
                'ema50': latest_ema50,
                'rsi': latest_rsi
            }
            
            if latest_signal == 1:
                print(f"[+] BUY signal generated @ ₹{latest_close:.2f}")
                logging.info(f"BUY signal: {latest_close}")
            elif latest_signal == -1:
                print(f"[+] SELL signal generated @ ₹{latest_close:.2f}")
                logging.info(f"SELL signal: {latest_close}")
            else:
                print(f"[*] No signal (neutral) @ ₹{latest_close:.2f}")
            
            return signal_data
            
        except Exception as e:
            logging.error(f"Error in backtest: {str(e)}")
            print(f"[-] Error: {str(e)}")
            return None

    def execute_live_trade(self, signal_data):
        """Execute paper trade based on signal"""
        try:
            if signal_data['signal'] == 0:
                print("[*] No signal - skipping trade")
                return False
            
            symbol = 'GLD'
            quantity = self.paper_trading_trade_quantity
            price = signal_data['close']
            trade_id = f"BOT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if signal_data['signal'] == 1:
                result = self.paper_trading.place_buy_order(symbol, quantity, price, trade_id)
                if result:
                    msg = f"BUY {quantity} {symbol} @ ₹{price:.2f}"
                    self.alerts.send_buy_alert(symbol, price, quantity, "Rule-Based Signal")
                    print(f"[+] {msg}")
                    logging.info(msg)
            
            elif signal_data['signal'] == -1:
                result = self.paper_trading.place_sell_order(symbol, quantity, price, trade_id)
                if result:
                    msg = f"SELL {quantity} {symbol} @ ₹{price:.2f}"
                    self.alerts.send_sell_alert(symbol, price, price, quantity, 0, 0, "Rule-Based Signal")
                    print(f"[+] {msg}")
                    logging.info(msg)
            
            return result
            
        except Exception as e:
            logging.error(f"Error executing trade: {str(e)}")
            self.alerts.send_error_alert(f"Trade execution error: {str(e)}", "ERROR")
            print(f"[-] Error: {str(e)}")
            return False

    def send_daily_summary(self):
        """Send daily trading summary via Telegram"""
        try:
            summary = self.paper_trading.get_account_summary()
            self.alerts.send_daily_summary(summary)
            
            # Save summary
            os.makedirs('reports', exist_ok=True)
            with open(f"reports/summary_{datetime.now().strftime('%Y%m%d')}.json", 'w') as f:
                json.dump(summary, f, indent=2)
            
            logging.info("Daily summary sent")
            print("[+] Daily summary sent via Telegram")
            return True
            
        except Exception as e:
            logging.error(f"Error sending summary: {str(e)}")
            print(f"[-] Error: {str(e)}")
            return False

    def run_full_cycle(self):
        """Run complete bot cycle"""
        try:
            print("\n" + "="*70)
            print(f"[*] GOLD TRADING BOT CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*70 + "\n")
            
            # Step 1: Update data
            if not self.update_data():
                self.alerts.send_error_alert("Data update failed", "ERROR")
                return False
            
            # Step 2: Run backtest and get signals
            signal_data = self.run_backtest_and_get_signals()
            if signal_data is None:
                self.alerts.send_error_alert("Backtest analysis failed", "ERROR")
                return False
            
            # Step 3: Execute trade if signal
            if signal_data['signal'] != 0:
                self.execute_live_trade(signal_data)
            
            # Step 4: Send daily summary (at specific time)
            if datetime.now().hour == 16:  # 4 PM
                self.send_daily_summary()
            
            print("\n" + "="*70)
            print("[+] BOT CYCLE COMPLETED SUCCESSFULLY")
            print("="*70 + "\n")
            
            logging.info("Full cycle completed successfully")
            return True
            
        except Exception as e:
            logging.error(f"Fatal error in bot cycle: {str(e)}")
            self.alerts.send_error_alert(f"Bot cycle error: {str(e)}", "ERROR")
            print(f"[-] Fatal error: {str(e)}")
            return False

def main():
    """Main entry point"""
    try:
        bot = GoldTradingBot()
        success = bot.run_full_cycle()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"[-] Fatal error: {str(e)}")
        logging.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
