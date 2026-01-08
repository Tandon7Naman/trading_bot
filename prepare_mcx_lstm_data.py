#!/usr/bin/env python3
"""
MCX-specific wrapper around prepare_lstm_data
Maps lowercase OHLC to the columns expected by the GLD helper.
"""

import pandas as pd
from train_test_split import prepare_lstm_data as _prepare_lstm_data


def prepare_mcx_lstm_data(df: pd.DataFrame, window_size: int = 30):
    """
    df must have columns: ['timestamp','symbol','open','high','low','close','volume']
    This wrapper renames them to match the GLD helper's expectation.
    """
    df = df.copy()

    # Map lowercase → Capitalized names used in the original helper
    rename_map = {
        "open": "Open",
        "high": "High",
        "low":  "Low",
        "close": "Close",
    }
    df.rename(columns=rename_map, inplace=True)

    return _prepare_lstm_data(df, window_size=window_size)
