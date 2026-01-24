# Strategy Sandbox & Auto-Promotion Engine

This module provides an automated framework for:
- Running all strategies in the `strategies/` directory on historical data
- Comparing their performance using standardized metrics
- Automatically promoting the best-performing strategy to production (by updating `main_bot_advanced.py`)

## Usage

1. Place all strategy files in `src/strategies/`, each with a `backtest(data: pd.DataFrame) -> pd.DataFrame` function that returns a trade log (with `pnl` column).
2. Run the sandbox:

```bash
python src/gold_trading_bot/strategy_sandbox/sandbox_runner.py
```

3. The best strategy (by total P&L) will be auto-promoted to production.

## Customization
- Edit `sandbox_runner.py` to change the promotion logic (e.g., use Sharpe, win rate, etc.)
- Extend to support multi-asset or multi-period evaluation as needed.
