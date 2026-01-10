# train_lstm_model.py - FIXED VERSION WITH ROBUST DATA HANDLING
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from sklearn.model_selection import train_test_split
import joblib
import logging
import os
from datetime import datetime
import sys

logging.basicConfig(
    filename='logs/train_lstm.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def verify_data_structure(df):
    """Verify and fix data structure"""
    try:
        print("[*] Verifying data structure...")
        
        # List current columns
        print(f"[*] Current columns: {list(df.columns)}")
        
        # Rename columns to lowercase if needed
        df.columns = df.columns.str.lower()
        
        # Check for close column (various possible names)
        close_col = None
        for col in ['close', 'Close', 'price']:
            if col.lower() in df.columns:
                close_col = col.lower()
                break
        
        if close_col is None:
            print("[-] ERROR: No 'close' or 'price' column found!")
            print(f"[*] Available columns: {list(df.columns)}")
            return None
        
        print(f"[+] Found close price column: {close_col}")
        
        # Ensure close is numeric
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        
        # Remove any rows with NaN close values
        initial_rows = len(df)
        df = df.dropna(subset=['close'])
        removed_rows = initial_rows - len(df)
        
        if removed_rows > 0:
            print(f"[*] Removed {removed_rows} rows with NaN close values")
        
        print(f"[+] Data verification complete. {len(df)} valid rows")
        return df
        
    except Exception as e:
        logging.error(f"Error verifying data structure: {str(e)}")
        print(f"[-] Error verifying data: {str(e)}")
        return None

def prepare_data(df, lookback=30):
    """Prepare data for LSTM training with proper normalization"""
    try:
        print(f"[*] Preparing data with lookback period of {lookback}...")
        
        # Verify data structure first
        df = verify_data_structure(df)
        if df is None:
            return None, None, None
        
        # Select close price
        data = df[['close']].values
        
        print(f"[*] Total data points: {len(data)}")
        
        # Check if we have enough data
        if len(data) < lookback + 1:
            print(f"[-] ERROR: Not enough data. Need at least {lookback + 1} rows, got {len(data)}")
            logging.error(f"Insufficient data: {len(data)} rows, need {lookback + 1}")
            return None, None, None
        
        # Normalize
        print(f"[*] Normalizing data...")
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(data)
        
        print(f"[*] Data range: min={data.min():.2f}, max={data.max():.2f}")
        
        # Create sequences
        print(f"[*] Creating sequences...")
        X, y = [], []
        for i in range(len(scaled_data) - lookback):
            X.append(scaled_data[i:i+lookback])
            y.append(scaled_data[i+lookback])
        
        X = np.array(X)
        y = np.array(y)
        
        print(f"[+] Sequences created: X shape {X.shape}, y shape {y.shape}")
        
        if len(X) == 0:
            print("[-] ERROR: Failed to create sequences!")
            return None, None, None
        
        logging.info(f"Data prepared: X shape {X.shape}, y shape {y.shape}")
        return X, y, scaler
        
    except Exception as e:
        logging.error(f"Error preparing data: {str(e)}")
        print(f"[-] Error preparing data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None, None

def build_lstm_model(input_shape):
    """Build LSTM neural network"""
    try:
        print(f"[*] Building LSTM model with input shape {input_shape}...")
        
        model = Sequential([
            LSTM(units=50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(units=50, return_sequences=True),
            Dropout(0.2),
            LSTM(units=50),
            Dropout(0.2),
            Dense(units=1)
        ])
        
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
        
        print("[+] LSTM model built successfully")
        print(f"[*] Model summary:")
        model.summary()
        
        logging.info("LSTM model built successfully")
        return model
        
    except Exception as e:
        logging.error(f"Error building model: {str(e)}")
        print(f"[-] Error building model: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def train_model(model, X_train, y_train, X_val, y_val, epochs=50, batch_size=32):
    """Train the LSTM model"""
    try:
        print(f"[*] Training model for {epochs} epochs...")
        print(f"[*] Training data: {X_train.shape[0]} samples")
        print(f"[*] Validation data: {X_val.shape[0]} samples")
        
        history = model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(X_val, y_val),
            verbose=1
        )
        
        print("[+] Model training completed")
        logging.info(f"Model trained for {epochs} epochs")
        return history
        
    except Exception as e:
        logging.error(f"Error training model: {str(e)}")
        print(f"[-] Error training model: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def save_model(model, scaler, model_path='models/lstm_model.h5', scaler_path='models/scaler.pkl'):
    """Save trained model and scaler"""
    try:
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        print(f"[*] Saving model to {model_path}...")
        model.save(model_path)
        
        print(f"[*] Saving scaler to {scaler_path}...")
        joblib.dump(scaler, scaler_path)
        
        print("[+] Model and scaler saved successfully")
        logging.info(f"Model saved to {model_path}, scaler to {scaler_path}")
        return True
    except Exception as e:
        logging.error(f"Error saving model: {str(e)}")
        print(f"[-] Error saving model: {str(e)}")
        return False

def main():
    print("\n" + "="*70)
    print("[*] LSTM MODEL TRAINING")
    print("="*70)
    print(f"[*] Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load data
    try:
        data_file = 'data/gld_data.csv'
        print(f"[*] Loading data from {data_file}...")
        
        if not os.path.exists(data_file):
            print(f"[-] Data file not found: {data_file}")
            print("[*] Please run update_gld_data.py first")
            logging.error(f"Data file not found: {data_file}")
            return False
        
        df = pd.read_csv(data_file)
        print(f"[+] Loaded {len(df)} records from GLD data")
        print(f"[*] Columns: {list(df.columns)}")
        print(f"[*] First row:")
        print(df.head(1))
        
    except Exception as e:
        print(f"[-] Error loading data: {str(e)}")
        logging.error(f"Error loading data: {str(e)}")
        return False
    
    # Prepare data
    X, y, scaler = prepare_data(df, lookback=30)
    if X is None:
        print("[-] Failed to prepare data")
        logging.error("Failed to prepare data")
        return False
    
    # Split data: 70% train, 15% val, 15% test
    print(f"[*] Splitting data...")
    try:
        X_temp, X_test, y_temp, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
        X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=0.176, random_state=42)
        
        print(f"[+] Training set: {X_train.shape[0]}")
        print(f"[+] Validation set: {X_val.shape[0]}")
        print(f"[+] Test set: {X_test.shape[0]}")
        
    except Exception as e:
        print(f"[-] Error splitting data: {str(e)}")
        logging.error(f"Error splitting data: {str(e)}")
        return False
    
    # Build model
    model = build_lstm_model((X_train.shape[1], 1))
    if model is None:
        print("[-] Failed to build model")
        return False
    
    # Train model
    history = train_model(model, X_train, y_train, X_val, y_val, epochs=50, batch_size=32)
    if history is None:
        print("[-] Failed to train model")
        return False
    
    # Evaluate on test set
    print(f"[*] Evaluating on test set...")
    try:
        test_loss = model.evaluate(X_test, y_test, verbose=0)
        print(f"[+] Test Loss: {test_loss:.6f}")
        logging.info(f"Test Loss: {test_loss}")
    except Exception as e:
        print(f"[-] Error evaluating model: {str(e)}")
        logging.error(f"Error evaluating model: {str(e)}")
    
    # Save model
    if save_model(model, scaler):
        print("[+] Model training completed successfully!")
        logging.info("Model training completed successfully")
        print("="*70)
        return True
    else:
        print("[-] Failed to save model")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"[-] Fatal error: {str(e)}")
        logging.error(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
