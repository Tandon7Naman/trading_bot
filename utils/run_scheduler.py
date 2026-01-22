import asyncio
import time

import schedule

from utils.reporting import PerformanceReporter


def run_scheduler():
    # Schedule the report for 17:00 every day
    schedule.every().day.at("17:00").do(
        lambda: asyncio.run(PerformanceReporter.send_daily_report())
    )
    while True:
        schedule.run_pending()
        time.sleep(60)
