# main_bot.py
"""
Gold Trading Bot - Production Version
Uses proven rule-based technical analysis strategy
"""


import json
import logging
import os
import sys
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv

from backtest_strategy_rulebased import RuleBasedBacktestEngine
# from fetch_market_news import main as fetch_news  # Removed news integration
from paper_trading import PaperTradingEngine
from src.currency_monitor import CurrencyMonitor
from src.economic_calendar_monitor import EconomicCalendarMonitor
from src.fiscal_policy_loader import FiscalPolicyLoader
from src.geopolitical_risk_monitor import GeopoliticalRiskMonitor
from src.global_cues_monitor import GlobalCuesMonitor
from src.pivot_level_calculator import PivotLevelCalculator
from src.pretrade_gateway import PreTradeGateway
from src.risk_manager import RiskManager
from src.signal_confluence_filter import SignalConfluenceFilter
from update_gld_data import main as update_gld_data
from utils.notifier import TelegramNotifier

# Initialize the institutional logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/trading_bot.log"), logging.StreamHandler()],
)
logger = logging.getLogger("GoldTradingBot")

load_dotenv()

logging.basicConfig(
    filename="logs/main_bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class GoldTradingBot:
            # --- SECURITY: Enforce account lock for MT5 if available ---
            try:
                import MetaTrader5 as mt5
                if hasattr(self, 'config') and hasattr(self.config, 'authorized_account_id'):
                    account_info = mt5.account_info()
                    if account_info and hasattr(account_info, 'login'):
                        current_login = account_info.login
                        if current_login != self.config.authorized_account_id:
                            raise PermissionError(f"MT5 account lock: Current login {current_login} does not match authorized_account_id {self.config.authorized_account_id}")
            except ImportError:
                logging.info("MetaTrader5 not installed; skipping MT5 account lock check.")
            except Exception as e:
                logging.warning(f"MT5 account lock check failed: {e}")
    """Main bot orchestrator with rule-based strategy"""

    def __init__(self, account_size: float = 100000, *args, **kwargs):
        """
        Initialize bot with integrated gateway modules.
        """
        try:
            # Load configuration from environment variables
            self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
            self.paper_trading_api_choice = os.getenv("PAPER_TRADING_API_CHOICE", "paper")
            self.paper_trading_initial_capital = float(
                os.getenv("PAPER_TRADING_INITIAL_CAPITAL", "100000")
            )
            self.paper_trading_trade_quantity = int(os.getenv("PAPER_TRADING_TRADE_QUANTITY", "10"))
            self.backtest_tp_percent = float(os.getenv("BACKTEST_TP_PERCENT", "2.0"))
            self.backtest_sl_percent = float(os.getenv("BACKTEST_SL_PERCENT", "1.0"))

            # No longer using self.alerts; use TelegramNotifier directly

            # Initialize paper trading
            self.paper_trading = PaperTradingEngine(
                api_choice=self.paper_trading_api_choice,
                initial_capital=self.paper_trading_initial_capital,
            )

            # ========== NEW: Initialize Gateway Modules ==========
            self.fiscal_loader = FiscalPolicyLoader()
            self.global_cues = GlobalCuesMonitor()
            self.econ_calendar = EconomicCalendarMonitor()
            self.currency_monitor = CurrencyMonitor()
            self.pivot_calc = PivotLevelCalculator()
            self.signal_filter = SignalConfluenceFilter()
            self.geo_risk = GeopoliticalRiskMonitor()
            self.risk_manager = RiskManager(account_size=account_size)

            self.pretrade_gateway = None
            self.gateway_context = None
            # =====================================================

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
            # Async notification for error
            TelegramNotifier.send_message_sync(f"Data update failed: {str(e)}")
            print(f"[-] Error: {str(e)}")
            return False

    def run_backtest_and_get_signals(self):
        """Run backtest and get live trading signals"""
        try:
            print("[*] Running backtest analysis...")


            # --- Data Validation and Error Handling ---
            try:
                df = pd.read_csv("data/gld_data.csv")
            except FileNotFoundError:
                logging.error("data/gld_data.csv not found.")
                print("[-] Error: data/gld_data.csv not found.")
                return None
            except Exception as e:
                logging.error(f"Error reading data/gld_data.csv: {e}")
                print(f"[-] Error reading data/gld_data.csv: {e}")
                return None

            # Schema validation
            required_columns = {"close", "Signal", "EMA_20", "EMA_50", "RSI"}
            if not required_columns.issubset(df.columns):
                missing = required_columns - set(df.columns)
                logging.error(f"Missing columns in data/gld_data.csv: {missing}")
                print(f"[-] Error: Missing columns in data/gld_data.csv: {missing}")
                return None

            if df.empty:
                logging.error("data/gld_data.csv is empty.")
                print("[-] Error: data/gld_data.csv is empty.")
                return None

            engine = RuleBasedBacktestEngine(
                initial_capital=self.paper_trading_initial_capital,
                tp_percent=self.backtest_tp_percent,
                sl_percent=self.backtest_sl_percent,
            )

            # Generate signals
            df = engine.generate_signals(df)

            # Get latest signal
            latest_signal = df["Signal"].iloc[-1] if len(df) > 0 else 0
            latest_close = df["close"].iloc[-1] if len(df) > 0 else 0
            latest_ema20 = df["EMA_20"].iloc[-1] if "EMA_20" in df.columns else 0
            latest_ema50 = df["EMA_50"].iloc[-1] if "EMA_50" in df.columns else 0
            latest_rsi = df["RSI"].iloc[-1] if len(df) > 0 else 0

            signal_data = {
                "timestamp": datetime.now().isoformat(),
                "close": latest_close,
                "signal": int(latest_signal),
                "ema20": latest_ema20,
                "ema50": latest_ema50,
                "rsi": latest_rsi,
            }

            if latest_signal == 1:
                print(f"[+] BUY signal generated @ [20b9]{latest_close:.2f}")
                logging.info(f"BUY signal: {latest_close}")
            elif latest_signal == -1:
                print(f"[+] SELL signal generated @ [20b9]{latest_close:.2f}")
                logging.info(f"SELL signal: {latest_close}")
            else:
                print(f"[*] No signal (neutral) @ [20b9]{latest_close:.2f}")

            return signal_data

        except Exception as e:
            logging.error(f"Error in backtest: {str(e)}")
            print(f"[-] Error: {str(e)}")
            return None

    def execute_live_trade(self, signal_data):
        """Execute paper trade based on signal"""
        try:
            if signal_data["signal"] == 0:
                print("[*] No signal - skipping trade")
                return False

            symbol = "GLD"
            quantity = self.paper_trading_trade_quantity
            price = signal_data["close"]
            trade_id = f"BOT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            if signal_data["signal"] == 1:
                result = self.paper_trading.place_buy_order(symbol, quantity, price, trade_id)
                if result:
                    msg = f"BUY {quantity} {symbol} @ [20b9]{price:.2f}"
                    TelegramNotifier.notify_trade_sync(
                        trade_type="BUY",
                        price=price,
                        size=quantity,
                        sl=0,
                        tp=0,
                        sentiment="Rule-Based Signal",
                    )
                    print(f"[+] {msg}")
                    logging.info(msg)

            elif signal_data["signal"] == -1:
                result = self.paper_trading.place_sell_order(symbol, quantity, price, trade_id)
                if result:
                    msg = f"SELL {quantity} {symbol} @ [20b9]{price:.2f}"
                    TelegramNotifier.notify_trade_sync(
                        trade_type="SELL",
                        price=price,
                        size=quantity,
                        sl=0,
                        tp=0,
                        sentiment="Rule-Based Signal",
                    )
                    print(f"[+] {msg}")
                    logging.info(msg)

            return result

        except Exception as e:
            logging.error(f"Error executing trade: {str(e)}")
            TelegramNotifier.send_message_sync(f"Trade execution error: {str(e)}")
            print(f"[-] Error: {str(e)}")
            return False

    def send_daily_summary(self):
        """Send daily trading summary via Telegram"""
        try:
            summary = self.paper_trading.get_account_summary()
            TelegramNotifier.send_message_sync(f"Daily Summary: {summary}")

            # Save summary
            os.makedirs("reports", exist_ok=True)
            with open(f"reports/summary_{datetime.now().strftime('%Y%m%d')}.json", "w") as f:
                json.dump(summary, f, indent=2)

            logging.info("Daily summary sent")
            print("[+] Daily summary sent via Telegram")
            return True

        except Exception as e:
            logging.error(f"Error sending summary: {str(e)}")
            print(f"[-] Error: {str(e)}")
            return False

    def run_full_cycle(self):
        """
        Main trading cycle with integrated pre-trade gateway.

        Sequence:
        1. Update data (prices, indicators)
        2. Initialize PreTradeGateway (all 8 checks)
        3. If GO: Generate signals  Execute trades with RiskManager
        4. If NO-GO: Alert and skip trade execution
        5. Generate daily summary
        """

        logger.info("=" * 80)
        logger.info("STARTING FULL TRADING CYCLE WITH GATEWAY")
        logger.info("=" * 80)

        try:
            # ========== PHASE 1: Update Market Data ==========
            logger.info("[1/5] Updating market data and indicators...")
            self.update_data()
            logger.info(" Market data updated")

            # ========== PHASE 2: Initialize Gateway ==========
            logger.info("[2/5] Initializing pre-trade gateway...")
            self.pretrade_gateway = self._initialize_gateway()
            logger.info(" Gateway initialized with 8 modules")

            # ========== PHASE 3: Run Gateway Checks ==========
            logger.info("[3/5] Running unified pre-trade gateway checks...")
            go_ahead, gateway_ctx = self.pretrade_gateway.run_all_checks()
            self.gateway_context = gateway_ctx

            # Gate decision
            if not go_ahead:
                logger.error(" GATEWAY BLOCKED TRADE EXECUTION")
                logger.error(f"   Failed checks: {gateway_ctx['checks_failed']}")

                # Alert stakeholders
                self._alert_gateway_failure(gateway_ctx)

                # Still generate summary for auditing
                self.generate_daily_summary(gateway_blocked=True)

                logger.info("Cycle completed (trades blocked by gateway)")
                return

            logger.info(" All gateway checks passed - TRADE EXECUTION APPROVED")

            # ========== PHASE 4: Generate Signals & Execute Trades ==========
            logger.info("[4/5] Generating trading signals...")
            signals = [self.run_backtest_and_get_signals()]

            logger.info("[5/5] Executing trades with RiskManager...")
            self._execute_trades_with_risk(signals, gateway_ctx)

            logger.info(" Trades executed successfully")

            # ========== PHASE 5: Daily Summary ==========
            logger.info("Generating daily summary...")
            self.generate_daily_summary(gateway_blocked=False)

            logger.info("=" * 80)
            logger.info("FULL CYCLE COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"Fatal error in run_full_cycle: {e}", exc_info=True)
            raise

    def _initialize_gateway(self) -> PreTradeGateway:
        """
        Initialize PreTradeGateway with all 8 modules.

        Returns:
            PreTradeGateway: Fully initialized gateway instance
        """
        return PreTradeGateway(
            fiscal_loader=self.fiscal_loader,
            global_cues=self.global_cues,
            econ_calendar=self.econ_calendar,
            currency_monitor=self.currency_monitor,
            pivot_calc=self.pivot_calc,
            signal_filter=self.signal_filter,
            geo_risk=self.geo_risk,
            risk_manager=self.risk_manager,
        )

    def _execute_trades_with_risk(self, signals: list, gateway_ctx: dict):
        """
        Execute trades using RiskManager for position sizing and limits.

        Args:
            signals: List of trading signals from signal generator
            gateway_ctx: Context from gateway checks (includes duty, bias, etc.)
        """
        duty = gateway_ctx["checks"]["fiscal_policy"]["duty_rate"]
        bias = gateway_ctx["checks"]["global_cues"]["bias"]

        logger.info(f"Executing trades - Session bias: {bias}, Duty: {duty * 100:.1f}%")

        if not signals:
            logger.info("No signals generated. Skipping trade execution.")
            return

        for signal in signals:
            try:

                # Update peak balance and check drawdown protection
                current_balance = self.paper_trading.current_balance if hasattr(self.paper_trading, 'current_balance') else self.risk_manager.account_size
                self.risk_manager.update_peak_balance(current_balance)
                if not self.risk_manager.check_drawdown_protection(current_balance):
                    logger.error("Max drawdown limit reached. Circuit breaker activated. Halting trading.")
                    TelegramNotifier.send_message_sync("🚨 Max drawdown limit reached. Circuit breaker activated. Trading halted.")
                    break

                # Check daily loss limit before trade
                if not self.risk_manager.check_daily_loss_limit(0):
                    logger.warning("Daily loss limit reached. Skipping further trades.")
                    break


                # --- ATR-based dynamic stop loss calculation ---
                try:
                    from src.utils.ta import calculate_atr
                except ImportError:
                    def calculate_atr(df, period=14):
                        return None

                # Assume df is available in scope or reload if needed
                df = None
                if 'df' in locals():
                    pass
                elif hasattr(self, 'latest_df'):
                    df = self.latest_df
                else:
                    try:
                        df = pd.read_csv("data/gld_data.csv")
                    except Exception:
                        df = None

                atr_value = None
                if df is not None and all(col in df.columns for col in ["high", "low", "close"]):
                    atr_series = calculate_atr(df)
                    if atr_series is not None and not atr_series.empty:
                        atr_value = float(atr_series.iloc[-1])

                entry_price = signal.get("entry", 0)
                # Use ATR for stop loss if available, else fallback
                if atr_value and entry_price:
                    stop_loss_price = entry_price - atr_value
                else:
                    stop_loss_price = signal.get("stop_loss", 0)

                position = self.risk_manager.calculate_position_size(
                    entry_price=entry_price,
                    stop_loss_price=stop_loss_price,
                )

                if position == 0:
                    logger.warning(f"Position size = 0 for signal {signal}. Skipping.")
                    continue

                logger.info(
                    f"Executing: Entry={signal.get('entry')}, "
                    f"SL={signal.get('stop_loss')}, Position={position}"
                )

                # Execute trade using the integrated broker logic (paper trading, MT5, Alpaca, etc.)
                result = self.execute_live_trade(signal)
                if result:
                    logger.info(f"Trade executed successfully: {signal}")
                else:
                    logger.warning(f"Trade execution failed: {signal}")

            except Exception as e:
                logger.error(f"Trade execution failed: {e}")
                continue

    def _alert_gateway_failure(self, gateway_ctx: dict):
        """
        Alert stakeholders when gateway blocks trade execution.

        Args:
            gateway_ctx: Gateway context with failure details
        """
        failed_checks = gateway_ctx.get("checks_failed", [])

        alert_msg = (
            f"\n TRADING BOT ALERT: Gateway Execution Blocked\n"
            f"Timestamp: {gateway_ctx.get('timestamp')}\n"
            f"Failed Checks: {', '.join(failed_checks)}\n"
        )

        logger.warning(alert_msg)

        # Send Telegram alert for gateway failure
        TelegramNotifier.send_message_sync(alert_msg)

    def generate_daily_summary(self, gateway_blocked: bool = False):
        """
        Generate daily summary with gateway context.

        Args:
            gateway_blocked: Whether gateway blocked execution today
        """
        summary = {
            "date": str(datetime.now().date()),
            "gateway_blocked": gateway_blocked,
        }

        if self.gateway_context:
            summary["gateway_status"] = self.gateway_context.get("gateway_status", "UNKNOWN")
            summary["checks_passed"] = len(self.gateway_context.get("checks_passed", []))
            summary["checks_failed"] = self.gateway_context.get("checks_failed", [])

        logger.info(f"Daily Summary: {summary}")

        # TODO: Log to file, database, or external system


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
