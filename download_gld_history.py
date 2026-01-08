from datetime import datetime
import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from config_alpaca import ALPACA_API_KEY, ALPACA_SECRET_KEY

client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)

request_params = StockBarsRequest(
    symbol_or_symbols=["GLD"],
    timeframe=TimeFrame.Day,
    start="2015-01-01",
    end=datetime.utcnow().strftime("%Y-%m-%d"),
)

bars = client.get_stock_bars(request_params)
df = bars.df.reset_index()  # multi-index → columns

df.to_csv("data/GLD_daily.csv", index=False)
print(f"Saved {len(df)} rows to data/GLD_daily.csv")
