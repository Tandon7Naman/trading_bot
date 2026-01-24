import pandas as pd

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate the Average True Range (ATR) for a DataFrame with columns: high, low, close."""
    high = df['high']
    low = df['low']
    close = df['close']
    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low),
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    atr = tr.rolling(window=period, min_periods=1).mean()
    return atr
