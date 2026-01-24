"""
Automated Strategy Sandbox & Promotion Engine
- Runs all strategies on historical data
- Compares performance metrics
- Auto-promotes best strategy to production
"""
import os
import importlib
import pandas as pd
from src.gold_trading_bot.performance_tracker import compute_performance_metrics

STRATEGY_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "strategies")
PROD_STRATEGY_PATH = os.path.join(os.path.dirname(__file__), "..", "main_bot_advanced.py")


def discover_strategies():
    # Discover all strategy files in strategies/
    files = [f for f in os.listdir(STRATEGY_DIR) if f.endswith(".py") and not f.startswith("__")]
    return [f[:-3] for f in files]

def run_backtest(strategy_name, data):
    # Dynamically import strategy module
    module_path = f"strategies.{strategy_name}"
    strategy_mod = importlib.import_module(module_path)
    if hasattr(strategy_mod, "backtest"):
        return strategy_mod.backtest(data)
    else:
        raise NotImplementedError(f"Strategy {strategy_name} missing backtest(data) function.")

def auto_promote(best_strategy):
    # Replace main_bot_advanced.py logic with best strategy (symbolic, not full code swap)
    with open(PROD_STRATEGY_PATH, "w") as f:
        f.write(f"# PROMOTED STRATEGY: {best_strategy}\n")
        f.write(f"from strategies.{best_strategy} import *\n")
        f.write("# ...existing production logic...\n")
    print(f"[SANDBOX] Promoted {best_strategy} to production.")

def run_sandbox(data_path):
    data = pd.read_csv(data_path)
    strategies = discover_strategies()
    results = {}
    for strat in strategies:
        print(f"[SANDBOX] Backtesting {strat}...")
        trades = run_backtest(strat, data)
        metrics = compute_performance_metrics(trades)
        results[strat] = metrics
        print(f"[SANDBOX] {strat} metrics: {metrics}")
    # Select best strategy (highest total_pnl, can customize)
    best = max(results, key=lambda k: results[k].get("total_pnl", 0))
    print(f"[SANDBOX] Best strategy: {best}")
    auto_promote(best)

if __name__ == "__main__":
    # Example: run_sandbox("data/gld_data.csv")
    run_sandbox("data/gld_data.csv")
