import MetaTrader5 as mt5
import numpy as np
import pandas as pd
import ta


def audit_v2():
    print("🕵️  RE-STARTING HFT STACK AUDIT...")

    # 1. MT5 Fix: Attempting connection
    if not mt5.initialize():
        # If default fails, try explicit path
        # mt5.initialize(path=r"C:\Program Files\MetaTrader 5\terminal64.exe")
        print(f"❌ MT5: Connection Failed. Error: {mt5.last_error()}")
    else:
        print(f"✅ MT5: Connected! Terminal version: {mt5.version()}")

    # 2. TA-LIB Fix: Providing 50 bars for the 14-period ADX
    try:
        data = {
            "close": np.random.uniform(2000, 2050, 50),
            "high": np.random.uniform(2050, 2060, 50),
            "low": np.random.uniform(1990, 2000, 50),
        }
        df = pd.DataFrame(data)

        # Window 14 requires at least 28-30 bars to stabilize
        adx_val = ta.trend.ADXIndicator(df["high"], df["low"], df["close"], window=14).adx()
        print(f"✅ TA-LIB: Operational. Latest ADX: {adx_val.iloc[-1]:.2f}")

    except Exception as e:
        print(f"❌ TA-LIB: Error: {e}")


if __name__ == "__main__":
    audit_v2()
