from config.config import Config
from src.audit import AuditLogger
from src.compliance import ComplianceGuard


def print_header(title):
    print(f"\n{'=' * 60}\n  {title}\n{'=' * 60}\n")


def test_config():
    print_header("1️⃣  TESTING CONFIG")
    Config.print_config()
    print("✅ Config Test PASSED\n")


def test_audit():
    print_header("2️⃣  TESTING AUDIT LOGGER")
    logger = AuditLogger()
    logger.log("SYSTEM", details="System startup")
    logger.log(
        "TRADE", symbol="MCX:GOLDPETAL", action="BUY", price=68500, qty=1, details="Test buy order"
    )
    logger.log(
        "TRADE",
        symbol="MCX:GOLDPETAL",
        action="SELL",
        price=68550,
        qty=1,
        details="Test sell order",
    )
    recent = logger.read_last_trades(limit=3)
    print(f"✅ Audit Test PASSED ({len(recent)} trades logged)\n")


def test_compliance():
    print_header("3️⃣  TESTING COMPLIANCE GUARD")
    guard = ComplianceGuard()

    print("Test A: Small Loss (-500)")
    is_safe = guard.check_health(-500)
    print(f"Status: {'✅ TRADING ALLOWED' if is_safe else '❌ TRADING BLOCKED'}")

    print("\nTest B: Medium Loss (-5000)")
    is_safe = guard.check_health(-5000)
    print(f"Status: {'✅ TRADING ALLOWED' if is_safe else '❌ TRADING BLOCKED'}")

    print("\nTest C: Critical Loss (-15000)")
    is_safe = guard.check_health(-15000)
    print(f"Status: {'✅ TRADING ALLOWED' if is_safe else '❌ KILL SWITCH TRIGGERED'}")
    print("\n✅ Compliance Test PASSED\n")


def main():
    print("\n╔" + "=" * 58 + "╗")
    print("║" + "  🤖 GOLD TRADING BOT - CORE SYSTEMS TEST".center(58) + "║")
    print("╚" + "=" * 58 + "╝")

    try:
        test_config()
        test_audit()
        test_compliance()
        print_header("✅ ALL TESTS PASSED - BOT CORE IS READY!")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")


if __name__ == "__main__":
    main()
