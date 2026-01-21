import pandas as pd
import asyncio
import os
from datetime import datetime
from utils.notifier import TelegramNotifier

class PerformanceReporter:
    """Protocol 6.1: Daily Performance Auditing."""

    @staticmethod
    def calculate_stats():
        file_path = "data/trade_journal.csv"
        if not os.path.exists(file_path):
            return "⚠️ No trades recorded yet for today."

        df = pd.read_csv(file_path)
        if df.empty:
            return "⚠️ Trade journal is empty."

        # Clean PnL column (Remove $ and convert to float)
        df['PnL_val'] = df['PnL'].replace('[\$,]', '', regex=True).astype(float)

        total_pnl = df['PnL_val'].sum()
        win_rate = (len(df[df['PnL_val'] > 0]) / len(df)) * 100
        total_trades = len(df)
        avg_trade = total_pnl / total_trades if total_trades > 0 else 0

        report = (
            f"📊 *DAILY PERFORMANCE REPORT*\n"
            f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}\n"
            f"---------------------------\n"
            f"💰 *Net PnL:* ${total_pnl:,.2f}\n"
            f"🎯 *Win Rate:* {win_rate:.1f}%\n"
            f"🔄 *Total Trades:* {total_trades}\n"
            f"📈 *Avg Trade:* ${avg_trade:,.2f}\n"
            f"---------------------------\n"
            f"🚀 *System Status:* Operational"
        )
        return report

    @staticmethod
    async def send_daily_report():
        report_text = PerformanceReporter.calculate_stats()
        await TelegramNotifier.send_message(report_text)
