import os
import time

from config.settings import ASSET_CONFIG


class HeartbeatMonitor:
    """
    Protocol 1.1: Stale Data Detector.
    Ensures the strategy halts if the data feed dies (Silent Disconnection).
    """

    @staticmethod
    def check_heartbeat(symbol, max_latency=120):
        """
        Checks if the data stream is alive.

        Args:
            symbol (str): The asset symbol (e.g., "XAUUSD")
            max_latency (int): Max seconds allowed since last update.
                               (Set to 120s for Yahoo Paper Mode, 5s for Live MT5)

        Returns:
            (bool, str): (Is_Alive, Status_Message)
        """
        config = ASSET_CONFIG.get(symbol)
        if not config:
            return False, "Unknown Symbol Configuration"

        file_path = config["data_file"]

        # 1. Does the Pipeline exist?
        if not os.path.exists(file_path):
            return False, "❌ No Data Pipe Found"

        # 2. Check File Age (Paper Trading Heartbeat)
        try:
            last_modified_ts = os.path.getmtime(file_path)
            current_ts = time.time()
            latency = current_ts - last_modified_ts

            if latency > max_latency:
                # STALE DATA DETECTED
                return False, f"⚠️ STALE DATA: Lag {latency:.1f}s > {max_latency}s"

            return True, f"✅ Signal Healthy (Lag: {latency:.1f}s)"

        except Exception as e:
            return False, f"❌ Heartbeat Error: {e}"
