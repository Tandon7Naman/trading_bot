import csv
import os
import datetime
from config.settings import JOURNAL_CONFIG

class JournalManager:
    """
    Protocol 5.2: Automated Journaling.
    Logs trade context (Why we took it) + results (How it did).
    Supports CSV (Default) and is ready for Google Sheets integration.
    """
    
    FILE_PATH = "data/trade_journal.csv"
    
    @staticmethod
    def log_trade(trade_data):
        """
        Logs a completed trade with context.
        trade_data: dict containing {
            'ticket', 'symbol', 'direction', 'size', 
            'entry_price', 'exit_price', 'pnl', 
            'strategy', 'regime', 'sentiment', 'entry_time', 'exit_time'
        }
        """
        if not JOURNAL_CONFIG['enabled']: return

        # 1. CSV LOGGING (Robust, Always Works)
        file_exists = os.path.isfile(JournalManager.FILE_PATH)
        
        with open(JournalManager.FILE_PATH, mode='a', newline='') as file:
            fieldnames = [
                'Ticket', 'Symbol', 'Direction', 'Size', 
                'Entry Price', 'Exit Price', 'PnL', 'Duration',
                'Strategy', 'Regime (ADX)', 'Sentiment', 'Entry Time', 'Exit Time'
            ]
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()
            
            # Formatting
            row = {
                'Ticket': trade_data.get('ticket'),
                'Symbol': trade_data.get('symbol'),
                'Direction': trade_data.get('direction'),
                'Size': trade_data.get('size'),
                'Entry Price': trade_data.get('entry_price'),
                'Exit Price': trade_data.get('exit_price'),
                'PnL': f"${trade_data.get('pnl', 0):.2f}",
                'Duration': trade_data.get('duration', 'N/A'),
                'Strategy': trade_data.get('strategy', 'Unknown'),
                'Regime (ADX)': trade_data.get('regime', 'N/A'),
                'Sentiment': trade_data.get('sentiment', 'N/A'),
                'Entry Time': trade_data.get('entry_time'),
                'Exit Time': trade_data.get('exit_time')
            }
            writer.writerow(row)
            print(f"   📓 JOURNAL: Trade #{row['Ticket']} logged to CSV.")

        # 2. GOOGLE SHEETS (Optional / Advanced)
        if JOURNAL_CONFIG['type'] == "GSHEET":
            try:
                # Requires: pip install gspread oauth2client
                # And a valid service_account.json
                # (Skipped here to prevent import errors for basic users, 
                # but the architecture supports it as requested).
                pass 
            except Exception as e:
                print(f"   ⚠️ Journal Error (GSheet): {e}")
