import sqlite3
import os
import json
from datetime import datetime

class DBManager:
    """
    Protocol 9.2: SQLite State Management.
    Implements the schema defined in Table 9.2 for robust data persistence.
    """
    def __init__(self, db_path='data/bot_state.db'):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_tables()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_tables(self):
        """Creates the Tables defined in Table 9.2"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # 1. ACCOUNT STATE (Equity/Balance)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS account (
                id INTEGER PRIMARY KEY,
                equity REAL,
                balance REAL,
                updated_at TEXT
            )
        ''')

        # 2. TRADES TABLE (Table 9.2 Schema)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                broker_ticket INTEGER,
                symbol TEXT,
                direction TEXT,
                size REAL,
                entry_price REAL,
                sl_price REAL,
                tp_price REAL,
                status TEXT,
                magic_number INTEGER,
                entry_time TEXT,
                exit_price REAL,
                exit_time TEXT,
                pnl REAL
            )
        ''')
        
        # 3. PENDING ORDERS (For Limit Orders)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                action INTEGER,
                limit_price REAL,
                qty REAL,
                sl REAL,
                tp REAL,
                type TEXT,
                date TEXT
            )
        ''')

        # Initialize Account if empty
        cursor.execute("SELECT count(*) FROM account")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO account (id, equity, balance, updated_at) VALUES (1, 500000.0, 500000.0, ?)", 
                           (datetime.now().isoformat(),))
        
        conn.commit()
        conn.close()

    # --- PUBLIC METHODS ---

    def get_account(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT equity, balance FROM account WHERE id=1")
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"equity": row[0], "balance": row[1]}
        return {"equity": 500000.0, "balance": 500000.0}

    def update_equity(self, equity, balance=None):
        conn = self._get_conn()
        if balance:
            conn.execute("UPDATE account SET equity=?, balance=?, updated_at=? WHERE id=1", 
                         (equity, balance, datetime.now().isoformat()))
        else:
            conn.execute("UPDATE account SET equity=?, updated_at=? WHERE id=1", 
                         (equity, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def get_open_position(self, symbol):
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trades WHERE symbol=? AND status='OPEN'", (symbol,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            # Convert SQLite Row to Dict
            return {
                "id": row['trade_id'],
                "type": row['direction'],
                "symbol": row['symbol'],
                "entry_price": row['entry_price'],
                "qty": row['size'],
                "sl": row['sl_price'],
                "tp": row['tp_price']
            }
        return "FLAT"

    def add_trade(self, ticket, symbol, direction, size, price, sl, tp, magic=123456):
        conn = self._get_conn()
        conn.execute('''
            INSERT INTO trades (broker_ticket, symbol, direction, size, entry_price, sl_price, tp_price, status, magic_number, entry_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'OPEN', ?, ?)
        ''', (ticket, symbol, direction, size, price, sl, tp, magic, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def close_trade(self, symbol, exit_price, pnl):
        conn = self._get_conn()
        conn.execute('''
            UPDATE trades 
            SET status='CLOSED', exit_price=?, pnl=?, exit_time=?
            WHERE symbol=? AND status='OPEN'
        ''', (exit_price, pnl, datetime.now().isoformat(), symbol))
        conn.commit()
        conn.close()

    # --- PENDING ORDERS SUPPORT ---
    def add_order(self, order_dict):
        conn = self._get_conn()
        conn.execute('''
            INSERT INTO orders (symbol, action, limit_price, qty, sl, tp, type, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_dict['symbol'], order_dict['action'], order_dict['limit_price'], 
            order_dict['qty'], order_dict['sl'], order_dict['tp'], 
            order_dict['type'], order_dict['date']
        ))
        conn.commit()
        conn.close()

    def get_orders(self, symbol):
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE symbol=?", (symbol,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows] # Return list of dicts

    def remove_order(self, order_id):
        conn = self._get_conn()
        conn.execute("DELETE FROM orders WHERE order_id=?", (order_id,))
        conn.commit()
        conn.close()
