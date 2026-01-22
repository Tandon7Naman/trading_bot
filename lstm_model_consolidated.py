"""
Consolidated LSTM Model - Single Source of Truth
Replaces: trainlstm.py, trainlstmmodel.py, lstmmodel.py
"""

import json
import os
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.models import Sequential, load_model


class GoldLSTMModel:
    """
    Unified LSTM Model for MCX Gold Price Prediction
    Consolidates all LSTM implementations into single class
    """

    def __init__(self, lookback=60, features=4):
        self.lookback = lookback
        self.features = features
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.training_history = []

    def prepare_data(self, data, target_col="close"):
        """Prepare data for LSTM training"""
        if isinstance(data, pd.DataFrame):
            feature_cols = ["open", "high", "low", "close"]
            prices = data[feature_cols].values
        else:
            prices = data

        scaled_data = self.scaler.fit_transform(prices)

        X, y = [], []
        for i in range(self.lookback, len(scaled_data)):
            X.append(scaled_data[i - self.lookback : i])
            y.append(scaled_data[i, 3])

        X, y = np.array(X), np.array(y)

        split_idx = int(0.8 * len(X))
        X_train, y_train = X[:split_idx], y[:split_idx]
        X_test, y_test = X[split_idx:], y[split_idx:]

        print("✅ Data prepared:")
        print(f"   Training samples: {len(X_train)}")
        print(f"   Testing samples: {len(X_test)}")
        print(f"   Shape: {X_train.shape}")

        return X_train, y_train, X_test, y_test

    def build_model(self):
        """Build LSTM architecture"""
        self.model = Sequential(
            [
                LSTM(
                    units=64,
                    return_sequences=True,
                    input_shape=(self.lookback, self.features),
                ),
                Dropout(0.2),
                LSTM(units=64, return_sequences=True),
                Dropout(0.2),
                LSTM(units=32, return_sequences=False),
                Dropout(0.2),
                Dense(units=16, activation="relu"),
                Dropout(0.1),
                Dense(units=1, activation="sigmoid"),
            ]
        )

        self.model.compile(optimizer="adam", loss="mean_squared_error", metrics=["mae"])

        print("✅ Model architecture built")
        return self.model

    def train(self, X_train, y_train, epochs=50, batch_size=32, validation_split=0.2):
        """Train the model with callbacks"""

        if self.model is None:
            print("⚠️ Model not built. Building now...")
            self.build_model()

        os.makedirs("models", exist_ok=True)

        callbacks = [
            EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True, verbose=1),
            ModelCheckpoint(
                "models/lstm_best.h5",
                monitor="val_loss",
                save_best_only=True,
                verbose=1,
            ),
        ]

        print("\n🚀 Training LSTM model...")
        print(f"   Epochs: {epochs}")
        print(f"   Batch size: {batch_size}")
        print(f"   Validation split: {validation_split}")
        print("-" * 60)

        history = self.model.fit(
            X_train,
            y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=callbacks,
            verbose=1,
        )

        self.training_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "epochs": epochs,
                "final_loss": float(history.history["loss"][-1]),
                "final_val_loss": float(history.history["val_loss"][-1]),
                "best_val_loss": float(min(history.history["val_loss"])),
            }
        )

        print("\n✅ Training completed!")
        print(f"   Final Loss: {history.history['loss'][-1]:.6f}")
        print(f"   Final Val Loss: {history.history['val_loss'][-1]:.6f}")

        return history

    def evaluate(self, X_test, y_test):
        """Evaluate model on test data"""
        if self.model is None:
            raise ValueError("Model not built or loaded!")

        loss, mae = self.model.evaluate(X_test, y_test, verbose=0)
        predictions = self.model.predict(X_test)

        actual = self.scaler.inverse_transform(
            np.concatenate([np.zeros((len(y_test), 3)), y_test.reshape(-1, 1)], axis=1)
        )[:, 3]
        pred = self.scaler.inverse_transform(
            np.concatenate([np.zeros((len(predictions), 3)), predictions], axis=1)
        )[:, 3]

        mape = np.mean(np.abs((actual - pred) / actual)) * 100

        print("\n📊 Evaluation Results:")
        print(f"   Loss (MSE): {loss:.6f}")
        print(f"   MAE: {mae:.6f}")
        print(f"   MAPE: {mape:.2f}%")

        if mape < 5:
            print("   ✅ Accuracy: EXCELLENT")
        elif mape < 10:
            print("   ✅ Accuracy: GOOD")
        else:
            print("   ⚠️ Accuracy: FAIR - Consider retraining")

        return {"loss": loss, "mae": mae, "mape": mape}

    def predict(self, X):
        """Make predictions"""
        if self.model is None:
            print("⚠️ Model not built. Building default model...")
            self.build_model()

        if len(X.shape) == 2:
            X = X.reshape(1, X.shape[0], X.shape[1])

        prediction = self.model.predict(X, verbose=0)
        return prediction[0][0]

    def save(self, filepath="models/lstm_consolidated.h5"):
        """Save model and scaler"""
        if self.model is None:
            raise ValueError("Model not built or loaded!")

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        self.model.save(filepath)
        joblib.dump(self.scaler, filepath.replace(".h5", "_scaler.pkl"))

        history_file = filepath.replace(".h5", "_history.json")
        with open(history_file, "w") as f:
            json.dump(self.training_history, f, indent=4)

        print("\n💾 Model saved:")
        print(f"   Model: {filepath}")
        print(f"   Scaler: {filepath.replace('.h5', '_scaler.pkl')}")
        print(f"   History: {history_file}")

    def load(self, filepath="models/lstm_consolidated.h5"):
        """Load model and scaler"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")

        self.model = load_model(filepath)

        scaler_file = filepath.replace(".h5", "_scaler.pkl")
        if os.path.exists(scaler_file):
            self.scaler = joblib.load(scaler_file)

        history_file = filepath.replace(".h5", "_history.json")
        try:
            with open(history_file) as f:
                self.training_history = json.load(f)
        except FileNotFoundError:
            pass

        print(f"✅ Model loaded from {filepath}")


def train_lstm_model():
    """Complete training pipeline"""
    print("\n" + "=" * 60)
    print("🧠 LSTM MODEL TRAINING - CONSOLIDATED")
    print("=" * 60 + "\n")

    print("📊 Loading MCX Gold data...")
    try:
        df = pd.read_csv("data/mcx_gold_historical.csv", parse_dates=["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)
        print(f"✅ Loaded {len(df)} records")
        print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    except FileNotFoundError:
        print("⚠️ Data file not found. Creating sample data...")
        dates = pd.date_range(start="2023-01-01", periods=1000, freq="D")
        df = pd.DataFrame(
            {
                "timestamp": dates,
                "open": np.random.uniform(6000, 7000, 1000),
                "high": np.random.uniform(6100, 7100, 1000),
                "low": np.random.uniform(5900, 6900, 1000),
                "close": np.random.uniform(6000, 7000, 1000),
            }
        )
        os.makedirs("data", exist_ok=True)
        df.to_csv("data/mcx_gold_historical.csv", index=False)
        print("✅ Created and saved sample data")

    model = GoldLSTMModel(lookback=60, features=4)

    X_train, y_train, X_test, y_test = model.prepare_data(df)
    model.build_model()
    model.train(X_train, y_train, epochs=50, batch_size=32)
    metrics = model.evaluate(X_test, y_test)
    model.save("models/lstm_consolidated.h5")

    print("\n" + "=" * 60)
    print("✅ TRAINING COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Test predictions: python test_lstm_consolidated.py")
    print("2. Integrate with bot: import from lstm_model_consolidated")
    print("3. Add PPO agent for hybrid approach")

    return model, metrics


if __name__ == "__main__":
    train_lstm_model()

    def build_model(self):
        """Build LSTM architecture"""
        self.model = Sequential(
            [
                LSTM(units=64, return_sequences=True, input_shape=(self.lookback, self.features)),
                Dropout(0.2),
                LSTM(units=64, return_sequences=True),
                Dropout(0.2),
                LSTM(units=32, return_sequences=False),
                Dropout(0.2),
                Dense(units=16, activation="relu"),
                Dropout(0.1),
                Dense(units=1, activation="sigmoid"),
            ]
        )

        self.model.compile(optimizer="adam", loss="mean_squared_error", metrics=["mae"])

        print("✅ Model architecture built")
        return self.model

    def train(self, X_train, y_train, epochs=50, batch_size=32, validation_split=0.2):
        """Train the model with callbacks"""

        # Ensure model is built
        if self.model is None:
            print("⚠️ Model not built. Building now...")
            self.build_model()

        # Create models directory if it doesn't exist
        os.makedirs("models", exist_ok=True)

        callbacks = [
            EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True, verbose=1),
            ModelCheckpoint(
                "models/lstm_best.h5", monitor="val_loss", save_best_only=True, verbose=1
            ),
        ]

        print("\n🚀 Training LSTM model...")
        print(f"   Epochs: {epochs}")
        print(f"   Batch size: {batch_size}")
        print(f"   Validation split: {validation_split}")
        print("-" * 60)

        history = self.model.fit(
            X_train,
            y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=callbacks,
            verbose=1,
        )

        self.training_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "epochs": epochs,
                "final_loss": float(history.history["loss"][-1]),
                "final_val_loss": float(history.history["val_loss"][-1]),
                "best_val_loss": float(min(history.history["val_loss"])),
            }
        )

        print("\n✅ Training completed!")
        print(f"   Final Loss: {history.history['loss'][-1]:.6f}")
        print(f"   Final Val Loss: {history.history['val_loss'][-1]:.6f}")

        return history

    def evaluate(self, X_test, y_test):
        """Evaluate model on test data"""
        if self.model is None:
            raise ValueError("Model not built or loaded!")

        loss, mae = self.model.evaluate(X_test, y_test, verbose=0)

        # Make predictions
        predictions = self.model.predict(X_test)

        # Calculate MAPE
        actual = self.scaler.inverse_transform(
            np.concatenate([np.zeros((len(y_test), 3)), y_test.reshape(-1, 1)], axis=1)
        )[:, 3]

        pred = self.scaler.inverse_transform(
            np.concatenate([np.zeros((len(predictions), 3)), predictions], axis=1)
        )[:, 3]

        mape = np.mean(np.abs((actual - pred) / actual)) * 100

        print("\n📊 Evaluation Results:")
        print(f"   Loss (MSE): {loss:.6f}")
        print(f"   MAE: {mae:.6f}")
        print(f"   MAPE: {mape:.2f}%")

        if mape < 5:
            print("   ✅ Accuracy: EXCELLENT")
        elif mape < 10:
            print("   ✅ Accuracy: GOOD")
        else:
            print("   ⚠️ Accuracy: FAIR - Consider retraining")

        return {"loss": loss, "mae": mae, "mape": mape}

    def predict(self, X):
        """Make predictions"""
        # ✅ FIX: Auto-build model if not exists
        if self.model is None:
            print("⚠️ Model not built. Building default model...")
            self.build_model()

        if len(X.shape) == 2:
            X = X.reshape(1, X.shape[0], X.shape[1])

        prediction = self.model.predict(X, verbose=0)
        return prediction[0][0]

    def save(self, filepath="models/lstm_consolidated.h5"):
        """Save model and scaler"""
        if self.model is None:
            raise ValueError("Model not built or loaded!")

        # Create directory if needed
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        self.model.save(filepath)
        joblib.dump(self.scaler, filepath.replace(".h5", "_scaler.pkl"))

        # Save training history
        history_file = filepath.replace(".h5", "_history.json")
        with open(history_file, "w") as f:
            json.dump(self.training_history, f, indent=4)

        print("\n💾 Model saved:")
        print(f"   Model: {filepath}")
        print(f"   Scaler: {filepath.replace('.h5', '_scaler.pkl')}")
        print(f"   History: {history_file}")

    def load(self, filepath="models/lstm_consolidated.h5"):
        """Load model and scaler"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")

        self.model = load_model(filepath)

        scaler_file = filepath.replace(".h5", "_scaler.pkl")
        if os.path.exists(scaler_file):
            self.scaler = joblib.load(scaler_file)

        # Load history if exists
        history_file = filepath.replace(".h5", "_history.json")
        try:
            with open(history_file) as f:
                self.training_history = json.load(f)
        except FileNotFoundError:
            pass

        print(f"✅ Model loaded from {filepath}")


# ===== TRAINING SCRIPT =====
def train_lstm_model():
    """Complete training pipeline"""
    print("\n" + "=" * 60)
    print("🧠 LSTM MODEL TRAINING - CONSOLIDATED")
    print("=" * 60 + "\n")

    # Load data
    print("📊 Loading MCX Gold data...")
    try:
        df = pd.read_csv("data/mcx_gold_historical.csv", parse_dates=["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)
        print(f"✅ Loaded {len(df)} records")
        print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    except FileNotFoundError:
        print("⚠️ Data file not found. Creating sample data...")
        dates = pd.date_range(start="2023-01-01", periods=1000, freq="D")
        df = pd.DataFrame(
            {
                "timestamp": dates,
                "open": np.random.uniform(6000, 7000, 1000),
                "high": np.random.uniform(6100, 7100, 1000),
                "low": np.random.uniform(5900, 6900, 1000),
                "close": np.random.uniform(6000, 7000, 1000),
            }
        )
        # Save sample data
        os.makedirs("data", exist_ok=True)
        df.to_csv("data/mcx_gold_historical.csv", index=False)
        print("✅ Created and saved sample data")

    # Initialize model
    model = GoldLSTMModel(lookback=60, features=4)

    # Prepare data
    X_train, y_train, X_test, y_test = model.prepare_data(df)

    # Build model
    model.build_model()

    # Train
    model.train(X_train, y_train, epochs=50, batch_size=32)

    # Evaluate
    metrics = model.evaluate(X_test, y_test)

    # Save
    model.save("models/lstm_consolidated.h5")

    print("\n" + "=" * 60)
    print("✅ TRAINING COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Test predictions: python test_lstm_consolidated.py")
    print("2. Integrate with bot: import from lstm_model_consolidated")
    print("3. Add PPO agent for hybrid approach")

    return model, metrics


if __name__ == "__main__":
    train_lstm_model()
