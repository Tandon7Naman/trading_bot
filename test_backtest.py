from src.backtest import BacktestEngine

def test_backtest():
    print("\n" + "="*70)
    print("  🧪 BACKTEST ENGINE TEST")
    print("="*70 + "\n")
    
    # Run 1-year backtest
    backtest = BacktestEngine()
    metrics = backtest.run_backtest(
        num_days=252,           # 1 year
        initial_capital=500000,
        position_size=1.0,
        lookback=20
    )
    
    # Print results
    backtest.print_results(metrics)
    
    # Verify metrics exist
    required_keys = [
        'initial_capital', 'final_equity', 'total_pnl', 'return_pct',
        'max_drawdown_pct', 'total_trades', 'win_rate_pct', 'sharpe_ratio'
    ]
    
    for key in required_keys:
        assert key in metrics, f"Missing metric: {key}"
    
    print(f"✅ All metrics calculated successfully")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    test_backtest()
