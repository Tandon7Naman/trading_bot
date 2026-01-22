import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.models import Sequential


class GoldLSTMModel:
    def __init__(self, lookback=60):
        self.lookback = lookback
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))

    def prepare_data(self, data):
        """
        Prepare data for LSTM training
        """
        # Scale the data
        scaled_data = self.scaler.fit_transform(data.reshape(-1, 1))

        X, y = [], []
        for i in range(self.lookback, len(scaled_data)):
            X.append(scaled_data[i - self.lookback : i, 0])
            y.append(scaled_data[i, 0])

        return np.array(X), np.array(y)

    def build_model(self, input_shape):
        """
        Build LSTM architecture
        """
        self.model = Sequential(
            [
                LSTM(units=50, return_sequences=True, input_shape=input_shape),
                Dropout(0.2),
                LSTM(units=50, return_sequences=True),
                Dropout(0.2),
                LSTM(units=50),
                Dropout(0.2),
                Dense(units=1),
            ]
        )

        self.model.compile(optimizer="adam", loss="mean_squared_error")
        return self.model

    def train(self, X_train, y_train, epochs=50, batch_size=32):
        """
        Train the LSTM model
        """
        early_stop = EarlyStopping(monitor="loss", patience=5)

        self.model.fit(
            X_train,
            y_train,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stop],
            verbose=1,
        )

    def predict(self, X_test):
        """
        Make predictions
        """
        predictions = self.model.predict(X_test)
        return self.scaler.inverse_transform(predictions)

    def save_model(self, filepath="gold_lstm_model.h5"):
        """
        Save trained model
        """
        self.model.save(filepath)
        joblib.dump(self.scaler, "scaler.pkl")
        print(f"✅ Model saved to {filepath}")


# Usage Example
if __name__ == "__main__":
    # Load data
    df = pd.read_csv("mcx_gold_historical.csv")
    prices = df["Close_MCX"].values

    # Initialize and train
    lstm_model = GoldLSTMModel(lookback=60)
    X, y = lstm_model.prepare_data(prices)

    # Split data
    split = int(0.8 * len(X))
    X_train, y_train = X[:split], y[:split]

    # Reshape for LSTM
    X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))

    # Build and train
    lstm_model.build_model((X_train.shape[1], 1))
    lstm_model.train(X_train, y_train, epochs=50)
    lstm_model.save_model()
