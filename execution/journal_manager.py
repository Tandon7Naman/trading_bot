import csv
import os
from config.settings import JOURNAL_CONFIG

class JournalManager:
    """
    Protocol 5.2: Automated Journaling.
    Logs every trade to a CSV for 'Self-Review'.
    """
    FILE_PATH = "data/trade_journal.csv"
    
    @staticmethod
    def log_trade(trade_data):
        if not JOURNAL_CONFIG['enabled']: return

        # Ensure directory exists
        os.makedirs(os.path.dirname(JournalManager.FILE_PATH), exist_ok=True)
        file_exists = os.path.isfile(JournalManager.FILE_PATH)
        
        with open(JournalManager.FILE_PATH, mode='a', newline='') as file:
            fieldnames = [
                'Ticket', 'Symbol', 'Direction', 'Size', 
                'Entry Price', 'Exit Price', 'PnL', 
                'Strategy', 'Regime', 'Sentiment', 'Entry Time', 'Exit Time'
            ]
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()
            
            # Safe row construction
            row = {k: trade_data.get(k, 'N/A') for k in fieldnames}
            
            # Format PnL
            if isinstance(row['PnL'], (int, float)):
                row['PnL'] = f"${row['PnL']:.2f}"
                
            writer.writerow(row)
            print(f"   📓 JOURNAL: Trade #{row['Ticket']} logged.")