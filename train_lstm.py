import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

DATA_PATH = Path("data/GLD_daily.csv")
MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)


WINDOW = 30    # lookback bars
HORIZON = 1    # predict 1 bar ahead


def load_data():
    df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    prices = df["close"].values.reshape(-1, 1)
    scaler = MinMaxScaler()
    prices_scaled = scaler.fit_transform(prices)

    X, y = [], []
    for i in range(WINDOW, len(prices_scaled) - HORIZON):
        window = prices_scaled[i - WINDOW:i]
        ret = prices[i + HORIZON] / prices[i] - 1
        label = 1 if ret > 0 else 0      # 1 = up, 0 = down
        X.append(window)
        y.append(label)

    X = np.array(X)
    y = np.array(y)

    split = int(len(X) * 0.8)
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]

    return X_train, y_train, X_val, y_val, scaler


def build_model():
    model = Sequential([
        LSTM(64, input_shape=(WINDOW, 1)),
        Dropout(0.2),
        Dense(1, activation="sigmoid"),
    ])
    model.compile(
        optimizer="adam",
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )
    return model


def main():
    print("Loading data…")
    X_train, y_train, X_val, y_val, scaler = load_data()
    print(f"Train samples: {len(X_train)}, Val samples: {len(X_val)}")

    print("Building model…")
    model = build_model()

    ckpt_path = MODEL_DIR / "lstm_gld_direction.h5"
    callbacks = [
        EarlyStopping(patience=5, restore_best_weights=True),
        ModelCheckpoint(str(ckpt_path), save_best_only=True, monitor="val_accuracy"),
    ]

    print("Training…")
    model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=50,
        batch_size=32,
        callbacks=callbacks,
        verbose=1,
    )

    # Save scaler params for later use if needed
    np.save(MODEL_DIR / "lstm_gld_scaler_min.npy", scaler.min_)
    np.save(MODEL_DIR / "lstm_gld_scaler_scale.npy", scaler.scale_)

    print(f"✅ Saved model to {ckpt_path}")


if __name__ == "__main__":
    main()
