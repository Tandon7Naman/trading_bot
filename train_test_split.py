#!/usr/bin/env python3
"""
Train/Test Split and LSTM Retraining Script
============================================

Splits GLD_daily.csv into train (2016-2020) and test (2021-2025) periods.
Retrains LSTM model on train data only.
Backtests on test data to validate out-of-sample performance.
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime
import sys
import os

# Import your existing modules (adjust paths as needed)
sys.path.insert(0, str(Path(__file__).parent))

def split_data_by_date(csv_path, split_date="2021-01-01"):
    """
    Load GLD_daily.csv and split into train/test by date.
    
    Args:
        csv_path: Path to GLD_daily.csv
        split_date: Date string in format "YYYY-MM-DD" to split on
        
    Returns:
        train_df, test_df - DataFrames split by date
    """
    print(f"Loading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # Ensure 'Date' column is datetime
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
    elif 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df.rename(columns={'date': 'Date'}, inplace=True)
    else:
        print("ERROR: No Date column found. Check CSV structure.")
        print(f"Columns: {df.columns.tolist()}")
        return None, None
    
    split_dt = pd.Timestamp(split_date)
    
    train_df = df[df['Date'] < split_dt].reset_index(drop=True)
    test_df = df[df['Date'] >= split_dt].reset_index(drop=True)
    
    print(f"\n=== DATA SPLIT ===")
    print(f"Train period: {train_df['Date'].min()} to {train_df['Date'].max()}")
    print(f"Train rows: {len(train_df)}")
    
    print(f"\nTest period: {test_df['Date'].min()} to {test_df['Date'].max()}")
    print(f"Test rows: {len(test_df)}")
    
    return train_df, test_df

def prepare_lstm_data(df, window_size=30):
    """
    Prepare sliding windows of OHLC data for LSTM.
    
    Args:
        df: DataFrame with columns [Date, Open, High, Low, Close, Volume]
        window_size: Number of bars per window
        
    Returns:
        X: (samples, window_size, 4) array of [Open, High, Low, Close]
        y: (samples,) binary labels [0=price down, 1=price up in next bar]
        scaler: MinMaxScaler fitted to training data
    """
    
    # Extract OHLC
    ohlc = df[['Open', 'High', 'Low', 'Close']].values.astype(np.float32)
    
    # Fit scaler on this segment
    scaler = MinMaxScaler(feature_range=(0, 1))
    ohlc_scaled = scaler.fit_transform(ohlc)
    
    X, y = [], []
    
    for i in range(len(ohlc_scaled) - window_size):
        window = ohlc_scaled[i:i+window_size]  # (window_size, 4)
        X.append(window)
        
        # Label: 1 if price goes up, 0 if goes down
        next_close = ohlc[i+window_size, 3]  # Next bar's close (unscaled)
        curr_close = ohlc[i+window_size-1, 3]  # Current bar's close (unscaled)
        y.append(1 if next_close > curr_close else 0)
    
    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.float32)
    
    print(f"Prepared LSTM data: X shape {X.shape}, y shape {y.shape}")
    
    return X, y, scaler

def train_lstm_model(X_train, y_train, X_test, y_test, model_path="models/lstm_signal_v2_traintest.h5"):
    """
    Build and train LSTM model on training data.
    Evaluate on test (validation) data.
    
    Args:
        X_train, y_train: Training data
        X_test, y_test: Validation data
        model_path: Where to save the model
        
    Returns:
        model: Trained Keras model
    """
    try:
        import tensorflow as tf
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import LSTM, Dense, Dropout
        from tensorflow.keras.optimizers import Adam
    except ImportError:
        print("ERROR: TensorFlow not installed. Install with: pip install tensorflow")
        return None
    
    print(f"\n=== TRAINING LSTM ===")
    print(f"X_train shape: {X_train.shape}")
    print(f"y_train shape: {y_train.shape}")
    print(f"X_test shape: {X_test.shape}")
    print(f"y_test shape: {y_test.shape}")
    
    model = Sequential([
        LSTM(64, activation='relu', input_shape=(X_train.shape[1], X_train.shape[2]), return_sequences=True),
        Dropout(0.2),
        LSTM(32, activation='relu', return_sequences=False),
        Dropout(0.2),
        Dense(16, activation='relu'),
        Dropout(0.1),
        Dense(1, activation='sigmoid')  # Output: probability of UP
    ])
    
    model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    
    # Train with early stopping on validation data
    history = model.fit(
        X_train, y_train,
        epochs=50,
        batch_size=32,
        validation_data=(X_test, y_test),
        verbose=1
    )
    
    # Save model
    os.makedirs(os.path.dirname(model_path) or ".", exist_ok=True)
    model.save(model_path)
    print(f"\nModel saved to {model_path}")
    
    return model

def evaluate_model_on_test(model, X_test, y_test):
    """
    Evaluate model performance on test data.
    """
    print(f"\n=== MODEL EVALUATION (Test Data) ===")
    loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
    print(f"Test Loss: {loss:.4f}")
    print(f"Test Accuracy: {accuracy:.4f}")
    return accuracy

def save_scaler(scaler, scaler_path="models/scaler_v2_traintest.pkl"):
    """Save MinMaxScaler for later use in backtest."""
    os.makedirs(os.path.dirname(scaler_path) or ".", exist_ok=True)
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"Scaler saved to {scaler_path}")

def main():
    print("="*60)
    print("TRAIN/TEST SPLIT & LSTM RETRAINING")
    print("="*60)
    
    # Paths (adjust to your repo structure)
    csv_path = "data/GLD_daily.csv"  # Change if needed
    model_path = "models/lstm_signal_v2_traintest.h5"
    scaler_path = "models/scaler_v2_traintest.pkl"
    
    # Check if CSV exists
    if not os.path.exists(csv_path):
        print(f"ERROR: {csv_path} not found.")
        print("Please adjust csv_path in this script.")
        return
    
    # Step 1: Load and split data
    train_df, test_df = split_data_by_date(csv_path, split_date="2021-01-01")
    if train_df is None:
        return
    
    # Step 2: Prepare training data (fit scaler on train data only)
    print(f"\n=== PREPARING TRAINING DATA ===")
    X_train, y_train, scaler_train = prepare_lstm_data(train_df, window_size=30)
    
    # Step 3: Prepare test data (use SAME scaler as train)
    print(f"\n=== PREPARING TEST DATA ===")
    ohlc_test = test_df[['Open', 'High', 'Low', 'Close']].values.astype(np.float32)
    ohlc_test_scaled = scaler_train.transform(ohlc_test)
    
    X_test_lstm, y_test = [], []
    for i in range(len(ohlc_test_scaled) - 30):
        window = ohlc_test_scaled[i:i+30]
        X_test_lstm.append(window)
        next_close = ohlc_test[i+30, 3]
        curr_close = ohlc_test[i+29, 3]
        y_test.append(1 if next_close > curr_close else 0)
    
    X_test_lstm = np.array(X_test_lstm, dtype=np.float32)
    y_test = np.array(y_test, dtype=np.float32)
    
    print(f"Prepared test data: X_test shape {X_test_lstm.shape}, y_test shape {y_test.shape}")
    
    # Step 4: Train LSTM
    model = train_lstm_model(X_train, y_train, X_test_lstm, y_test, model_path)
    if model is None:
        return
    
    # Step 5: Evaluate on test data
    evaluate_model_on_test(model, X_test_lstm, y_test)
    
    # Step 6: Save scaler for backtest
    save_scaler(scaler_train, scaler_path)
    
    print(f"\n=== SUMMARY ===")
    print(f"✓ Train data: 2016 → 2020 ({len(train_df)} bars)")
    print(f"✓ Test data:  2021 → 2025 ({len(test_df)} bars)")
    print(f"✓ LSTM trained on train data only")
    print(f"✓ Model saved: {model_path}")
    print(f"✓ Scaler saved: {scaler_path}")
    print(f"\nNEXT: Update backtest.py to:")
    print(f"  1. Load model from {model_path}")
    print(f"  2. Load scaler from {scaler_path}")
    print(f"  3. Run backtest on 2021-2025 data only")
    print(f"  4. Compare metrics to full-period backtest (11.55% return)")

if __name__ == "__main__":
    main()
