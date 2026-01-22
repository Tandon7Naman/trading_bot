#!/usr/bin/env python3
"""
MCX Backtest - Simplified (bypass TensorFlow load issues temporarily)
"""

import os
import pickle

import numpy as np
import pandas as pd

# Suppress TensorFlow warnings if it's partially imported
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"


def run_mcx_backtest():
    """
    Backtest MCX Gold 2021-2025 without TensorFlow dependency issues
    """

    # Load MCX test data
    csv_path = "data/MCX_gold_daily.csv"
    df = pd.read_csv(csv_path, parse_dates=["timestamp"])

    # Filter to 2021+ (test period)
    test_df = df[df["timestamp"] >= "2021-01-01"].copy().reset_index(drop=True)

    print("=" * 60)
    print("MCX GOLD - SIMPLIFIED BACKTEST (2021-2025)")
    print("=" * 60)
    print(f"Test period bars: {len(test_df)}")

    # Load scaler
    try:
        with open("models/scaler_mcx_traintest.pkl", "rb") as f:
            scaler = pickle.load(f)
        print("✓ Scaler loaded")
    except Exception as e:
        print(f"✗ Scaler load failed: {e}")
        return

    # Try to load model
    model = None
    use_model = False
    try:
        from tensorflow.keras.models import load_model

        model = load_model("models/lstm_mcx_traintest.h5")
        print("✓ Model loaded")
        use_model = True
    except Exception as e:
        print(f"✗ Model load failed (will use random signals): {e}")
        use_model = False

    # === BACKTEST LOOP ===
    initial_equity = 500_000
    equity = initial_equity
    position = None
    trades = []

    # Exit parameters
    STOP_LOSS_PCT = 0.01
    TAKE_PROFIT_PCT = 0.035
    TIME_STOP_DAYS = 20

    for i in range(30, len(test_df) - 1):
        current_bar = test_df.iloc[i]

        # === GENERATE SIGNAL ===
        signal = 0  # Default to hold/exit
        if use_model and model:
            try:
                window = test_df.iloc[i - 30 : i][["open", "high", "low", "close"]].values
                window_scaled = scaler.transform(window)
                window_scaled = window_scaled.astype(np.float32)
                window_scaled = np.expand_dims(window_scaled, axis=0)
                pred = model.predict(window_scaled, verbose=0)[0]
                signal = 1 if pred[0] > 0.5 else 0
            except Exception as e:
                # Fallback to random if prediction fails for any reason
                print(
                    f"Warning: Model prediction failed at index {i}, using random signal. Error: {e}"
                )
                signal = np.random.randint(0, 2)
        elif not use_model:
            # Fallback: random signal if model didn't load
            signal = np.random.randint(0, 2)

        # === POSITION MANAGEMENT ===
        if position is None and signal == 1:
            # BUY
            position = {
                "entry_price": current_bar["close"],
                "entry_date": current_bar["timestamp"],
                "bars_held": 0,
            }

        elif position is not None:
            position["bars_held"] += 1
            current_price = current_bar["close"]

            # Check exits
            pnl_pct = (current_price - position["entry_price"]) / position["entry_price"]
            exit_reason = None

            if pnl_pct <= -STOP_LOSS_PCT:
                exit_reason = "STOP_LOSS"
            elif pnl_pct >= TAKE_PROFIT_PCT:
                exit_reason = "TAKE_PROFIT"
            elif position["bars_held"] >= TIME_STOP_DAYS:
                exit_reason = "TIME_STOP"
            elif signal == 0:
                exit_reason = "MODEL_EXIT"

            if exit_reason:
                exit_price = current_bar["close"]
                # Assuming 1 contract/lot for simplicity
                pnl_amount = exit_price - position["entry_price"]

                equity += pnl_amount
                trades.append(
                    {
                        "entry_date": position["entry_date"],
                        "entry_price": position["entry_price"],
                        "exit_date": current_bar["timestamp"],
                        "exit_price": exit_price,
                        "pnl_pct": pnl_pct * 100,
                        "pnl_amount": pnl_amount,
                        "reason": exit_reason,
                        "bars_held": position["bars_held"],
                    }
                )

                position = None

    # === RESULTS ===
    total_return = (equity - initial_equity) / initial_equity * 100
    win_rate = sum(1 for t in trades if t["pnl_pct"] > 0) / len(trades) * 100 if trades else 0

    print("\n=== BACKTEST RESULTS ===")
    print(f"Initial Equity:  ₹{initial_equity:,.0f}")
    print(f"Final Equity:    ₹{equity:,.0f}")
    print(f"Total Return:    {total_return:.2f}%")
    print(f"Total Trades:    {len(trades)}")
    print(f"Win Rate:        {win_rate:.1f}%")
    print(f"Avg P&L (%):     {np.mean([t['pnl_pct'] for t in trades]):.2f}%" if trades else "N/A")
    print(f"Avg P&L (₹):     {np.mean([t['pnl_amount'] for t in trades]):.2f}" if trades else "N/A")

    if trades:
        print("\n=== First 5 Trades ===")
        for i, t in enumerate(trades[:5]):
            print(
                f"{i + 1}. {t['entry_date'].date()} → {t['exit_date'].date()}: "
                f"{t['pnl_pct']:+.2f}% (₹{t['pnl_amount']:+.2f}) ({t['reason']})"
            )


if __name__ == "__main__":
    run_mcx_backtest()
