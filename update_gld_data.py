import yfinance as yf
import pandas as pd
import os
from datetime import date, timedelta

def update_gld_data(file_path="data/GLD_daily.csv", ticker="GLD"):
    """
    Updates the GLD data file with the latest daily data from Yahoo Finance.
    Only fetches data since the last entry in the file.
    """
    if os.path.exists(file_path):
        existing_data = pd.read_csv(file_path, index_col='timestamp', parse_dates=True)
        last_date = existing_data.index.max().date()
        start_date = last_date + timedelta(days=1)
        today = date.today()

        if start_date > today:
            print("Data is already up to date.")
            return

        print(f"Updating {ticker} data from {start_date} to {today}...")
        new_data = yf.download(ticker, start=start_date, end=today.strftime('%Y-%m-%d'))
        
        if not new_data.empty:
            updated_data = pd.concat([existing_data, new_data])
            # yfinance sometimes includes a row for the current day with partial data,
            # so we remove duplicates, keeping the last entry.
            updated_data = updated_data[~updated_data.index.duplicated(keep='last')]
            updated_data.to_csv(file_path)
            print(f"Data updated and saved to {file_path}")
        else:
            print("No new data to download.")

    else:
        print(f"Data file not found at {file_path}. Downloading full history...")
        today = date.today().strftime('%Y-%m-%d')
        full_data = yf.download(ticker, start="2004-11-18", end=today)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        full_data.to_csv(file_path)
        print(f"Full data history saved to {file_path}")

if __name__ == "__main__":
    update_gld_data()
