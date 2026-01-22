from src.backtest import BacktestEngine


def test_backtest():
    print("\n" + "=" * 70)
    print("  🧪 BACKTEST ENGINE TEST")
    print("=" * 70 + "\n")

    # Run 1-year backtest with required arguments
    backtest = BacktestEngine(
        csv_path="data/gld_data.csv",
        model_path="models/lstm_consolidated.h5",
        scaler_path="models/scaler.save",
        start_date="2023-01-01",
        initial_equity=500000.0,
        ohlc_cols=["open", "high", "low", "close"],
        date_col="timestamp",
        lookback=60,
    )
    metrics = backtest.run_backtest()

    # Print results
    print(metrics)

    # Verify metrics exist
    required_keys = [
        "initial_capital",
        "final_equity",
        "total_pnl",
        "return_pct",
        "max_drawdown_pct",
        "total_trades",
        "win_rate_pct",
        "sharpe_ratio",
    ]

    for key in required_keys:
        assert key in metrics, f"Missing metric: {key}"

    print("✅ All metrics calculated successfully")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    test_backtest()
