
import MetaTrader5 as mt5
import pandas as pd

# Initialize
mt5.initialize()

# Get 10,000 candles of Gold (XAUUSD) 1-Hour data
rates = mt5.copy_rates_from_pos("XAUUSD", mt5.TIMEFRAME_H1, 0, 10000)

# Convert to Dataframe for AI training
df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')

print(df.head())
print("✅ Data ready for Model Learning!")
