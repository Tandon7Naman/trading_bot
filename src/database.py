import sqlite3
import os
from datetime import datetime
from config.config import Config

class Database:
    """SQLite database for market data and trades"""
    
    def __init__(self, db_path="goldbot.db"):
        self.db_path = db_path
        self.initialize()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def initialize(self):
        """Create tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Market ticks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_ticks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                symbol TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER,
                bid REAL,
                ask REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Trades table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                algo_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                pnl REAL,
                status TEXT,
                order_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Daily P&L summary
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_pnl (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                total_trades INTEGER,
                winning_trades INTEGER,
                losing_trades INTEGER,
                total_pnl REAL,
                max_drawdown REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Features for ML model
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                symbol TEXT NOT NULL,
                rsi REAL, macd REAL, bb_width REAL, adx REAL,
                bid_ask_spread REAL, order_imbalance REAL,
                usdinr REAL, us_yield REAL, au_ag_ratio REAL,
                monsoon_factor REAL, real_yield REAL,
                import_duty REAL, duty_shock REAL,
                lunar_demand REAL, fair_value REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        print(f"✅ Database initialized: {self.db_path}")
    
    def insert_tick(self, symbol, open_p, high, low, close, volume, bid=None, ask=None):
        """Insert market tick"""
        conn = self.get_connection()
        cursor = conn.cursor()
        timestamp = datetime.now()
        cursor.execute("""
            INSERT INTO market_ticks (timestamp, symbol, open, high, low, close, volume, bid, ask)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, symbol, open_p, high, low, close, volume, bid, ask))
        conn.commit()
        conn.close()
    
    def get_latest_ticks(self, symbol, limit=100):
        """Get last N ticks"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM market_ticks WHERE symbol = ? ORDER BY timestamp DESC LIMIT ?
        """, (symbol, limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in reversed(rows)]
    
    def insert_trade(self, symbol, side, quantity, entry_price, algo_id=None, order_id=None, status="PENDING"):
        """Log trade"""
        if algo_id is None:
            algo_id = Config.ALGO_ID
        conn = self.get_connection()
        cursor = conn.cursor()
        timestamp = datetime.now()
        cursor.execute("""
            INSERT INTO trades (timestamp, algo_id, symbol, side, quantity, entry_price, status, order_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, algo_id, symbol, side, quantity, entry_price, status, order_id))
        conn.commit()
        trade_id = cursor.lastrowid
        conn.close()
        return trade_id
    
    def close_trade(self, trade_id, exit_price):
        """Close trade and calculate P&L"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trades WHERE id = ?", (trade_id,))
        trade = dict(cursor.fetchone())
        
        quantity = trade['quantity']
        entry = trade['entry_price']
        
        if trade['side'] == 'BUY':
            pnl = (exit_price - entry) * quantity
        else:
            pnl = (entry - exit_price) * quantity
        
        cursor.execute("""
            UPDATE trades SET exit_price = ?, pnl = ?, status = 'CLOSED' WHERE id = ?
        """, (exit_price, pnl, trade_id))
        
        conn.commit()
        conn.close()
        return pnl
    
    def get_open_trades(self):
        """Get all open trades"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM trades WHERE status != 'CLOSED' ORDER BY timestamp DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_trades_for_date(self, date_str):
        """Get trades for a date"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM trades WHERE DATE(timestamp) = ? ORDER BY timestamp ASC
        """, (date_str,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def insert_features(self, symbol, features_dict):
        """Insert feature vector"""
        conn = self.get_connection()
        cursor = conn.cursor()
        timestamp = datetime.now()
        cursor.execute("""
            INSERT INTO features 
            (timestamp, symbol, rsi, macd, bb_width, adx, bid_ask_spread, order_imbalance, usdinr, us_yield, au_ag_ratio, monsoon_factor, real_yield, import_duty, duty_shock, lunar_demand, fair_value)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, symbol,
            features_dict.get('rsi', 0), features_dict.get('macd', 0),
            features_dict.get('bb_width', 0), features_dict.get('adx', 0),
            features_dict.get('bid_ask_spread', 0), features_dict.get('order_imbalance', 0),
            features_dict.get('usdinr', 0), features_dict.get('us_yield', 0),
            features_dict.get('au_ag_ratio', 0), features_dict.get('monsoon_factor', 0),
            features_dict.get('real_yield', 0), features_dict.get('import_duty', 0),
            features_dict.get('duty_shock', 0), features_dict.get('lunar_demand', 0),
            features_dict.get('fair_value', 0)
        ))
        conn.commit()
        conn.close()
    
    def calculate_daily_pnl(self, date_str):
        """Calculate daily P&L"""
        trades = self.get_trades_for_date(date_str)
        if not trades:
            return None
        
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t['pnl'] and t['pnl'] > 0)
        losing_trades = sum(1 for t in trades if t['pnl'] and t['pnl'] < 0)
        total_pnl = sum(t['pnl'] for t in trades if t['pnl'])
        drawdowns = [abs(t['pnl']) for t in trades if t['pnl'] and t['pnl'] < 0]
        max_drawdown = max(drawdowns) if drawdowns else 0
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO daily_pnl (date, total_trades, winning_trades, losing_trades, total_pnl, max_drawdown)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (date_str, total_trades, winning_trades, losing_trades, total_pnl, max_drawdown))
        conn.commit()
        conn.close()
        
        return {'date': date_str, 'total_trades': total_trades, 'winning_trades': winning_trades, 'losing_trades': losing_trades, 'total_pnl': total_pnl, 'max_drawdown': max_drawdown}
    
    def get_stats(self):
        """Get database stats"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM market_ticks")
        ticks = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM trades")
        trades = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM features")
        features = cursor.fetchone()[0]
        conn.close()
        return {'market_ticks': ticks, 'trades': trades, 'features': features}

if __name__ == "__main__":
    db = Database()
    db.insert_tick("MCX:GOLDPETAL", 68500, 68550, 68450, 68510, 5000, 68505, 68515)
    ticks = db.get_latest_ticks("MCX:GOLDPETAL")
    print(f"✅ Database working. {len(ticks)} ticks found")
