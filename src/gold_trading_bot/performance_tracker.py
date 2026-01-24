"""
Automated Post-Market Analytics & Reporting
- Trade journal with performance metrics
- Strategy performance comparison
- Daily P&L analysis
"""
import pandas as pd
import datetime
import os

TRADE_JOURNAL_PATH = os.path.join("data", "trade_journal.csv")
PERFORMANCE_REPORT_PATH = os.path.join("reports", "daily_performance_report.csv")


def load_trade_journal():
    if os.path.exists(TRADE_JOURNAL_PATH):
        return pd.read_csv(TRADE_JOURNAL_PATH)
    else:
        return pd.DataFrame(columns=[
            "timestamp", "symbol", "side", "qty", "price", "strategy", "pnl", "fees"
        ])

def compute_performance_metrics(df):
    if df.empty:
        return {}
    metrics = {}
    metrics["total_trades"] = len(df)
    metrics["win_rate"] = (df["pnl"] > 0).mean() if len(df) > 0 else 0
    metrics["total_pnl"] = df["pnl"].sum()
    metrics["avg_pnl"] = df["pnl"].mean() if len(df) > 0 else 0
    metrics["max_drawdown"] = (df["pnl"].cumsum().cummax() - df["pnl"].cumsum()).max()
    metrics["sharpe"] = (
        df["pnl"].mean() / df["pnl"].std() * (252 ** 0.5)
        if df["pnl"].std() > 0 else 0
    )
    return metrics

def compare_strategies(df):
    if df.empty:
        return pd.DataFrame()
    return df.groupby("strategy")["pnl"].agg(["count", "sum", "mean"]).sort_values("sum", ascending=False)

def daily_pnl_analysis(df):
    if df.empty:
        return pd.DataFrame()
    df["date"] = pd.to_datetime(df["timestamp"]).dt.date
    return df.groupby("date")["pnl"].sum().reset_index()

def generate_daily_report():
    df = load_trade_journal()
    today = datetime.date.today()
    today_trades = df[pd.to_datetime(df["timestamp"]).dt.date == today]
    metrics = compute_performance_metrics(today_trades)
    strat_comp = compare_strategies(today_trades)
    daily_pnl = daily_pnl_analysis(today_trades)

    # Save daily report
    report = {
        "date": today,
        **metrics
    }
    report_df = pd.DataFrame([report])
    if os.path.exists(PERFORMANCE_REPORT_PATH):
        report_df.to_csv(PERFORMANCE_REPORT_PATH, mode="a", header=False, index=False)
    else:
        report_df.to_csv(PERFORMANCE_REPORT_PATH, index=False)

    print("[POST-MARKET] Daily performance report generated.")
    print(report_df)
    print("[POST-MARKET] Strategy comparison:")
    print(strat_comp)
    print("[POST-MARKET] Daily P&L:")
    print(daily_pnl)

if __name__ == "__main__":
    generate_daily_report()
