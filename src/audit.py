import csv
import os
from datetime import datetime
from config.config import Config

class AuditLogger:
    def __init__(self):
        self.file_path = Config.AUDIT_FILE
        self._initialize_file()

    def _initialize_file(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Algo_ID", "Event_Type", "Symbol", "Action", "Price", "Quantity", "Details"])
            print(f"✅ Audit log created: {self.file_path}")

    def log(self, event_type, symbol="N/A", action="INFO", price=0, qty=0, details=""):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        try:
            with open(self.file_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, Config.ALGO_ID, event_type, symbol, action, price, qty, details])
            
            emoji = {'TRADE': '📊', 'ALERT': '⚠️', 'ERROR': '❌', 'SYSTEM': '⚙️', 'INFO': 'ℹ️'}.get(event_type, '📝')
            print(f"{emoji} [{event_type}] {action} {symbol} @ ₹{price} | {details}")
        except Exception as e:
            print(f"❌ Audit log error: {str(e)}")

    def read_last_trades(self, limit=10):
        trades = []
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    trades.append(row)
            return trades[-limit:]
        except:
            return []

if __name__ == "__main__":
    logger = AuditLogger()
    logger.log("SYSTEM", details="Audit logger initialized")