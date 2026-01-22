# train_lstm_model_sklearn.py
import logging
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import MinMaxScaler

logging.basicConfig(
    filename="logs/train_lstm.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def prepare_data(df, lookback=30):
    """Prepare data for ML training - YOUR EXACT COLUMNS"""
    try:
        # Use exact columns from your data
        feature_cols = ["close", "volume", "SMA_20", "SMA_50", "RSI"]

        # Check if all columns exist
        missing_cols = [col for col in feature_cols if col not in df.columns]
        if missing_cols:
            print(f"[-] Missing columns: {missing_cols}")
            print(f"[*] Available columns: {list(df.columns)}")
            return None, None, None, None

        data = df[feature_cols].values.astype(float)

        # Fill NaN values with column mean
        for i in range(data.shape[1]):
            col_mean = np.nanmean(data[:, i])
            data[np.isnan(data[:, i]), i] = col_mean

        print(f"[+] Selected features: {feature_cols}")
        print(f"[+] Data shape: {data.shape}")

        # Normalize
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(data)

        # Create sequences
        X, y = [], []
        for i in range(len(scaled_data) - lookback):
            X.append(scaled_data[i : i + lookback].flatten())
            y.append(scaled_data[i + lookback, 0])  # Close price (first column)

        X = np.array(X)
        y = np.array(y)

        print(f"[+] Sequences created: X shape {X.shape}, y shape {y.shape}")
        logging.info(f"Data prepared: X shape {X.shape}, y shape {y.shape}")
        return X, y, scaler, feature_cols

    except Exception as e:
        logging.error(f"Error preparing data: {str(e)}")
        print(f"[-] Error: {str(e)}")
        return None, None, None, None


def train_gradient_boosting(X_train, y_train, X_val, y_val):
    """Train Gradient Boosting model"""
    try:
        print("\n[*] Training Gradient Boosting model...")
        model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            subsample=0.8,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            validation_fraction=0.1,
            n_iter_no_change=10,
            tol=1e-4,
            verbose=1,
        )

        model.fit(X_train, y_train)

        train_score = model.score(X_train, y_train)
        val_score = model.score(X_val, y_val)

        print("\n[+] Gradient Boosting:")
        print(f"    Train R² = {train_score:.6f}")
        print(f"    Val R²   = {val_score:.6f}")

        logging.info(f"GB Model - Train R²: {train_score:.6f}, Val R²: {val_score:.6f}")
        return model

    except Exception as e:
        logging.error(f"Error training model: {str(e)}")
        print(f"[-] Error: {str(e)}")
        return None


def train_neural_network(X_train, y_train, X_val, y_val):
    """Train simple neural network (alternative)"""
    try:
        print("\n[*] Training Neural Network model...")
        model = MLPRegressor(
            hidden_layer_sizes=(128, 64, 32),
            max_iter=1000,
            learning_rate_init=0.001,
            batch_size=32,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.1,
            tol=1e-4,
            verbose=1,
        )

        model.fit(X_train, y_train)

        train_score = model.score(X_train, y_train)
        val_score = model.score(X_val, y_val)

        print("\n[+] Neural Network:")
        print(f"    Train R² = {train_score:.6f}")
        print(f"    Val R²   = {val_score:.6f}")

        logging.info(f"MLP Model - Train R²: {train_score:.6f}, Val R²: {val_score:.6f}")
        return model

    except Exception as e:
        logging.error(f"Error training MLP: {str(e)}")
        print(f"[-] Error: {str(e)}")
        return None


def save_model(
    model, scaler, feature_cols, model_path="models/lstm_model.pkl", scaler_path="models/scaler.pkl"
):
    """Save model and scaler"""
    try:
        os.makedirs("models", exist_ok=True)
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        joblib.dump(feature_cols, "models/feature_cols.pkl")

        logging.info(f"Model saved: {model_path}")
        print(f"\n[+] Model saved to {model_path}")
        print(f"[+] Scaler saved to {scaler_path}")
        print(f"[+] Features saved: {feature_cols}")
        return True
    except Exception as e:
        logging.error(f"Error saving model: {str(e)}")
        print(f"[-] Error: {str(e)}")
        return False


def main():
    print("\n" + "=" * 70)
    print("LSTM MODEL TRAINING (Scikit-learn - No TensorFlow)")
    print("=" * 70 + "\n")

    try:
        df = pd.read_csv("data/gld_data.csv")
        print(f"[+] Loaded {len(df)} records from GLD data")
        print(f"[+] Data shape: {df.shape}")
        print(f"[+] Columns found: {list(df.columns)}")
    except FileNotFoundError:
        print("[-] GLD data file not found. Run update_gld_data.py first")
        logging.error("GLD data file not found")
        return False

    # Prepare data
    X, y, scaler, feature_cols = prepare_data(df, lookback=30)
    if X is None:
        print("[-] Failed to prepare data")
        return False

    # Split data: 70% train, 15% val, 15% test
    split_train = int(len(X) * 0.70)
    split_val = split_train + int(len(X) * 0.15)

    X_train, X_val, X_test = X[:split_train], X[split_train:split_val], X[split_val:]
    y_train, y_val, y_test = y[:split_train], y[split_train:split_val], y[split_val:]

    print("\n[*] Data split:")
    print(f"    Train: {len(X_train)} samples")
    print(f"    Val:   {len(X_val)} samples")
    print(f"    Test:  {len(X_test)} samples")

    # Train Gradient Boosting (best for tabular data)
    model = train_gradient_boosting(X_train, y_train, X_val, y_val)

    if model is None:
        print("[-] Failed to train model")
        return False

    # Evaluate on test set
    test_score = model.score(X_test, y_test)
    print(f"\n[+] Test R² = {test_score:.6f}")
    logging.info(f"Test R²: {test_score:.6f}")

    # Save model
    if save_model(model, scaler, feature_cols):
        print("\n" + "=" * 70)
        print("[+] ✓ MODEL TRAINING COMPLETED SUCCESSFULLY")
        print("=" * 70 + "\n")
        return True
    else:
        print("[-] Failed to save model")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
