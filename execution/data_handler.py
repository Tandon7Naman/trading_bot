import asyncio
import os

import numpy as np
import pandas as pd

from config.settings import ASSET_CONFIG


class AsyncDataHandler:
    """
    Protocol 1.2 & 4.1.3: Async Data Buffer with Sanitization.
    Prevents 'ZeroDivisionError' and 'NaN' propagation.
    """

    def __init__(self, symbol):
        self.symbol = symbol
        self.config = ASSET_CONFIG.get(symbol)
        self.file_path = self.config["data_file"]
        self.latest_data = None
        self.last_mtime = 0
        self.running = False
        self.lock = asyncio.Lock()

    async def start(self):
        """Starts the background ingestion task."""
        self.running = True
        asyncio.create_task(self._poll_data())
        print(f"   ⚡ Async Buffer: Started for {self.symbol}")

    async def stop(self):
        self.running = False

    def _sanitize_data(self, df):
        """
        Protocol 4.1.3: Data Sanitization.
        Cleans NaNs and Zeros to prevent math crashes.
        """
        if df.empty:
            return df

        # 1. Enforce Numeric Types (Fixes 'string' math errors)
        cols_to_check = ["Open", "High", "Low", "Close"]
        for col in cols_to_check:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # 2. Protocol 4.1.3: Replace 0.0 with NaN in Price Columns
        # (Volume can be 0, but Price cannot)
        df[cols_to_check] = df[cols_to_check].replace(0.0, np.nan)

        # 3. Forward Fill (Heal small gaps)
        df = df.ffill()

        # 4. Drop remaining NaNs (Unsalvageable rows)
        df = df.dropna(subset=cols_to_check)

        return df

    async def _poll_data(self):
        """
        Continuously polls for file updates without blocking the main thread.
        """
        while self.running:
            try:
                if os.path.exists(self.file_path):
                    mtime = os.path.getmtime(self.file_path)

                    if mtime > self.last_mtime:
                        # Offload reading
                        df = await asyncio.to_thread(pd.read_csv, self.file_path)

                        # --- PROTOCOL 4.1.3: SANITIZE BEFORE STORING ---
                        clean_df = await asyncio.to_thread(self._sanitize_data, df)

                        async with self.lock:
                            self.latest_data = clean_df
                            self.last_mtime = mtime

                await asyncio.sleep(0.1)

            except Exception as e:
                print(f"   ⚠️ Buffer Error {self.symbol}: {e}")
                await asyncio.sleep(1)

    async def get_latest(self):
        """Returns the latest data snapshot instantly from memory."""
        async with self.lock:
            return self.latest_data
