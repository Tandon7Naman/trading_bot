# analyze_backtest.py
import pandas as pd
import json

print("\n" + "="*70)
print("BACKTEST ANALYSIS")
print("="*70 + "\n")

# Load trades
try:
    trades = pd.read_csv('results/backtest_trades.csv')
    print("[*] Trade Details:\n")
    print(trades.to_string(index=False))
    
    print("\n[*] Analysis:")
    print(f"  • Entry prices range: ${trades['entry_price'].min():.2f} - ${trades['entry_price'].max():.2f}")
    print(f"  • Exit prices range: ${trades['exit_price'].min():.2f} - ${trades['exit_price'].max():.2f}")
    print(f"  • Average hold time: N/A (dates not compared)")
    
    # Analyze losing trades
    losing = trades[trades['pnl'] < 0]
    if not losing.empty:
        print(f"\n[!] Losing Trades Analysis:")
        for idx, trade in losing.iterrows():
            price_diff = trade['exit_price'] - trade['entry_price']
            print(f"  Trade {idx+1}: Entered at ${trade['entry_price']:.2f}, exited at ${trade['exit_price']:.2f}")
            print(f"    Reason: {trade['reason']} | Loss: ${trade['pnl']:.2f}")
    
except FileNotFoundError:
    print("[-] backtest_trades.csv not found")

# Load metrics
try:
    with open('results/backtest_metrics.json', 'r') as f:
        metrics = json.load(f)
    print("\n[*] Summary Metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
except FileNotFoundError:
    print("[-] backtest_metrics.json not found")

print("\n" + "="*70 + "\n")
