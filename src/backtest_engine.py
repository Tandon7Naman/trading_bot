from typing import Any

import joblib
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model


def prepare_lstm_data(data: np.ndarray, scaler, lookback: int = 60) -> np.ndarray:
    """Prepares data for LSTM model prediction."""
    if len(data) < lookback:
        return np.array([])

    scaled_data = scaler.transform(data)

    X = []
    for i in range(lookback, len(scaled_data) + 1):
        X.append(scaled_data[i - lookback : i, :])

    return np.array(X)


# BacktestEngine class
class BacktestEngine:
    """A generic engine for backtesting a trading strategy based on a signal model."""

    def __init__(
        self,
        csv_path: str,
        model_path: str,
        scaler_path: str,
        start_date: str,
        initial_equity: float = 100_000.0,
        ohlc_cols: list[str] = None,
        date_col: str = "timestamp",
        lookback: int = 60,
    ):
        """
        Initializes the backtesting engine.

        Args:
            csv_path (str): Path to the historical data CSV file.
            model_path (str): Path to the trained .h5 model file.
            scaler_path (str): Path to the fitted scaler .pkl file.
            start_date (str): The date from which to start the backtest (YYYY-MM-DD).
            initial_equity (float): Starting capital for the backtest.
            ohlc_cols (List[str]): A list of column names for Open, High, Low, Close.
            date_col (str): The name of the date/timestamp column.
            lookback (int): The lookback period required by the model.
        """
        self.csv_path = csv_path
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.start_date = pd.to_datetime(start_date)
        self.initial_equity = initial_equity
        self.ohlc_cols = ohlc_cols if ohlc_cols else ["Open", "High", "Low", "Close"]
        self.date_col = date_col
        self.lookback = lookback

        self.model = None
        self.scaler = None
        self.data = None
        self.trades = []
        self.equity_curve = []

    def _load_data(self):
        """Loads and prepares the data for backtesting."""
        print("Loading and preparing data...")
        try:
            self.model = load_model(self.model_path)
            with open(self.scaler_path, "rb") as f:
                self.scaler = joblib.load(f)
        except Exception as e:
            print(f"Error loading model or scaler: {e}")
            return False

        df = pd.read_csv(self.csv_path, parse_dates=[self.date_col])
        df = df[df[self.date_col] >= self.start_date].copy()
        df.sort_values(by=self.date_col, inplace=True)
        df.reset_index(drop=True, inplace=True)

        if len(df) < self.lookback:
            print(
                f"Error: Not enough data for the lookback period. Need {self.lookback}, have {len(df)}."
            )
            return False

        self.data = df
        print(
            f"Data loaded successfully. Backtest period: {self.data[self.date_col].min():%Y-%m-%d} to {self.data[self.date_col].max():%Y-%m-%d}"
        )
        return True

    def run_backtest(self):
        """Executes the backtest from start to finish."""
        if not self._load_data():
            return None

        print(f"\nRunning backtest with initial equity of ₹{self.initial_equity:,.2f}...")

        equity = self.initial_equity
        position = 0  # 0 for no position, 1 for long
        entry_price = 0

        # Feature columns are assumed to be the OHLC columns
        feature_cols = self.ohlc_cols

        for i in range(self.lookback, len(self.data)):
            # Prepare data for the current step
            current_data_window = self.data[feature_cols].iloc[i - self.lookback : i].values

            # Scale data and reshape for LSTM
            scaled_window = self.scaler.transform(current_data_window)
            X_test = np.reshape(scaled_window, (1, self.lookback, len(feature_cols)))

            # Get model prediction
            prediction = self.model.predict(X_test)[0][0]
            signal = 1 if prediction > 0.5 else 0  # 1 for UP (Buy), 0 for DOWN (Sell/Hold)

            current_price = self.data[self.ohlc_cols[3]].iloc[i]  # Close price
            current_date = self.data[self.date_col].iloc[i]

            # Trading Logic
            if signal == 1 and position == 0:  # Buy signal and no position
                position = 1
                entry_price = current_price
                self.trades.append(
                    {"type": "BUY", "date": current_date, "price": entry_price, "pnl": 0}
                )
            elif signal == 0 and position == 1:  # Sell signal and in a long position
                position = 0
                exit_price = current_price
                pnl = exit_price - entry_price
                equity += pnl

                # Update last trade
                if self.trades:
                    last_trade = self.trades[-1]
                    if last_trade["type"] == "BUY" and "exit_date" not in last_trade:
                        last_trade["pnl"] = pnl
                        last_trade["exit_date"] = current_date
                        last_trade["exit_price"] = exit_price

            self.equity_curve.append(equity)

        print("Backtest finished.")
        return self.calculate_performance()

    def calculate_performance(self):
        """Calculates and returns performance metrics."""
        if not self.trades:
            return {"message": "No trades were executed."}

        final_equity = self.equity_curve[-1] if self.equity_curve else self.initial_equity
        total_return_pct = ((final_equity - self.initial_equity) / self.initial_equity) * 100

        pnls = [t["pnl"] for t in self.trades if "pnl" in t and t["pnl"] != 0]
        winning_trades = [p for p in pnls if p > 0]
        losing_trades = [p for p in pnls if p < 0]

        num_trades = len(pnls)
        win_rate = (len(winning_trades) / num_trades) * 100 if num_trades > 0 else 0

        # Calculate Max Drawdown
        equity_series = pd.Series([self.initial_equity] + self.equity_curve)
        cumulative_max = equity_series.cummax()
        drawdown = (equity_series - cumulative_max) / cumulative_max
        max_drawdown = abs(drawdown.min()) * 100

        metrics = {
            "Total Return (%)": total_return_pct,
            "Max Drawdown (%)": max_drawdown,
            "Total Trades": num_trades,
            "Win Rate (%)": win_rate,
            "Winning Trades": len(winning_trades),
            "Losing Trades": len(losing_trades),
            "Average Win": np.mean(winning_trades) if winning_trades else 0,
            "Average Loss": np.mean(losing_trades) if losing_trades else 0,
        }
        return metrics

    def print_performance_summary(self, metrics: dict[str, Any]):
        """Prints a formatted summary of the backtest results."""
        print("\n" + "=" * 60)
        print("BACKTEST PERFORMANCE SUMMARY")
        print("=" * 60)
        if not metrics or "Total Trades" not in metrics or metrics["Total Trades"] == 0:
            print("No trades were executed.")
            print("=" * 60)
            return

        print(f"Total Return:       {metrics['Total Return (%)']:.2f}%")
        print(f"Max Drawdown:       {metrics['Max Drawdown (%)']:.2f}%")
        print("-" * 60)
        print(f"Total Trades:       {metrics['Total Trades']}")
        print(f"Win Rate:           {metrics['Win Rate (%)']:.2f}%")
        print(f"  - Wins:           {metrics['Winning Trades']}")
        print(f"  - Losses:         {metrics['Losing Trades']}")
        print("-" * 60)
        print(f"Average Win:        ₹{metrics['Average Win']:,.2f}")
        print(f"Average Loss:       ₹{metrics['Average Loss']:,.2f}")
        print("=" * 60)
