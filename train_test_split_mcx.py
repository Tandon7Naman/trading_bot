#!/usr/bin/env python3
"""
Train/Test Split and LSTM Retraining for MCX Gold
"""

import os

import numpy as np
from prepare_mcx_lstm_data import prepare_mcx_lstm_data

from split_mcx_by_date import split_mcx_data_by_date
from train_test_split import save_scaler, train_lstm_model


def main():
    print("=" * 60)
    print("MCX GOLD - TRAIN/TEST SPLIT & LSTM RETRAINING")
    print("=" * 60)

    csv_path = "data/MCX_gold_daily.csv"
    model_path = "models/lstm_mcx_traintest.h5"
    scaler_path = "models/scaler_mcx_traintest.pkl"

    if not os.path.exists(csv_path):
        print(f"ERROR: {csv_path} not found.")
        return

    train_df, test_df = split_mcx_data_by_date(csv_path, "2021-01-01")
    if train_df is None:
        return

    print(f"\nTrain rows: {len(train_df)}, Test rows: {len(test_df)}")

    # === TRAIN DATA (MCX) ===
    print("\n=== PREPARING TRAIN DATA (MCX) ===")
    X_train, y_train, scaler_train = prepare_mcx_lstm_data(train_df, window_size=30)

    # 3) Prepare test data with same scaler
    print("\n=== PREPARING TEST DATA (MCX) ===")
    ohlc_test = test_df[["open", "high", "low", "close"]].values.astype(np.float32)
    ohlc_test_scaled = scaler_train.transform(ohlc_test)

    X_test, y_test = [], []
    for i in range(len(ohlc_test_scaled) - 30):
        window = ohlc_test_scaled[i : i + 30]
        X_test.append(window)
        next_close = ohlc_test[i + 30, 3]
        curr_close = ohlc_test[i + 29, 3]
        y_test.append(1 if next_close > curr_close else 0)

    X_test = np.array(X_test, dtype=np.float32)
    y_test = np.array(y_test, dtype=np.float32)
    print(f"Prepared test data: X_test {X_test.shape}, y_test {y_test.shape}")

    # 4) Train LSTM
    model = train_lstm_model(
        X_train,
        y_train,
        X_test,
        y_test,
        model_path=model_path,
    )
    if model is None:
        return

    # 5) Save scaler
    save_scaler(scaler_train, scaler_path)

    print("\n=== MCX SUMMARY ===")
    print(f"✓ Train data: 2016–2020 ({len(train_df)} bars)")
    print(f"✓ Test data:  2021–2025 ({len(test_df)} bars)")
    print(f"✓ Model saved:  {model_path}")
    print(f"✓ Scaler saved: {scaler_path}")


if __name__ == "__main__":
    main()
