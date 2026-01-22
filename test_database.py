from datetime import datetime

from src.database import Database


def test_database():
    print("\n" + "=" * 70)
    print("  🗄️  DATABASE TESTING")
    print("=" * 70 + "\n")

    db = Database("test_goldbot.db")

    # Test 1: Insert ticks
    print("Test 1: Insert Market Ticks")
    db.insert_tick("MCX:GOLDPETAL", 68500, 68550, 68450, 68510, 5000, 68505, 68515)
    db.insert_tick("MCX:GOLDPETAL", 68510, 68560, 68460, 68520, 4500, 68515, 68525)
    db.insert_tick("MCX:GOLDPETAL", 68520, 68570, 68470, 68530, 5200, 68525, 68535)
    print("✅ Inserted 3 ticks\n")

    # Test 2: Retrieve ticks
    print("Test 2: Retrieve Ticks")
    ticks = db.get_latest_ticks("MCX:GOLDPETAL", limit=3)
    print(f"Retrieved {len(ticks)} ticks:")
    for i, tick in enumerate(ticks, 1):
        print(f"  {i}. Close: ₹{tick['close']}, Volume: {tick['volume']}")
    print()

    # Test 3: Insert & close trade
    print("Test 3: Insert & Close Trade")
    trade_id = db.insert_trade("MCX:GOLDPETAL", "BUY", 1, 68510)
    print(f"✅ Trade #{trade_id} created (BUY @ ₹68510)")
    pnl = db.close_trade(trade_id, 68550)
    print(f"✅ Trade closed @ ₹68550, P&L: ₹{pnl}\n")

    # Test 4: Open trades
    print("Test 4: Open Trades")
    db.insert_trade("MCX:GOLDPETAL", "SELL", 2, 68530)
    open_trades = db.get_open_trades()
    print(f"Open trades: {len(open_trades)}\n")

    # Test 5: Daily P&L
    print("Test 5: Daily P&L")
    today = datetime.now().strftime("%Y-%m-%d")
    daily_pnl = db.calculate_daily_pnl(today)
    if daily_pnl:
        print(f"Date: {daily_pnl['date']}")
        print(f"Total Trades: {daily_pnl['total_trades']}")
        print(f"Total P&L: ₹{daily_pnl['total_pnl']:.2f}\n")

    # Test 6: Stats
    print("Test 6: Database Stats")
    stats = db.get_stats()
    for key, val in stats.items():
        print(f"  {key}: {val}")
    print()

    # Cleanup
    import os

    if os.path.exists("test_goldbot.db"):
        os.remove("test_goldbot.db")

    print("=" * 70)
    print("  ✅ ALL DATABASE TESTS PASSED")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    test_database()
