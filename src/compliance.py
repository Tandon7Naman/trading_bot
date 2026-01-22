from datetime import datetime

from config.config import Config


class ComplianceGuard:
    def __init__(self):
        self.max_daily_loss = Config.MAX_DAILY_LOSS
        self.current_pnl = 0.0
        self.is_alive = True
        self.kill_reason = None

    def check_health(self, current_pnl):
        self.current_pnl = current_pnl
        if current_pnl <= -self.max_daily_loss:
            self.trigger_kill_switch(
                reason="Max Daily Loss Breached",
                details=f"Loss: ₹{current_pnl:,.0f} | Limit: ₹{-self.max_daily_loss:,.0f}",
            )
            return False
        return True

    def trigger_kill_switch(self, reason, details=""):
        self.is_alive = False
        self.kill_reason = reason
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alert_msg = f"""
╔════════════════════════════════════════════════════════════════╗
║                   🚨 KILL SWITCH ACTIVATED 🚨                  ║
╠════════════════════════════════════════════════════════════════╣
║ Timestamp:  {timestamp}
║ Reason:     {reason}
║ {details}
║
║ ➤ All positions must be closed immediately
║ ➤ Bot will stop accepting new orders
║ ➤ Review logs for root cause
║ ➤ Notify administrator
╚════════════════════════════════════════════════════════════════╝
        """
        print(alert_msg)
        with open(Config.AUDIT_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n{timestamp} | KILL_SWITCH_ACTIVATED | {reason} | {details}\n")

    def can_trade(self):
        return self.is_alive

    def get_status(self):
        return {
            "is_alive": self.is_alive,
            "current_pnl": self.current_pnl,
            "max_daily_loss": self.max_daily_loss,
            "kill_reason": self.kill_reason,
            "status": "ACTIVE" if self.is_alive else "STOPPED",
        }


if __name__ == "__main__":
    guard = ComplianceGuard()
    print("Test 1: Normal PnL (-500)")
    safe = guard.check_health(-500)
    print(f"Result: {'✅ SAFE' if safe else '❌ BLOCKED'}\n")

    print("Test 2: Critical PnL (-50000)")
    unsafe = guard.check_health(-50000)
    print(f"Result: {'✅ SAFE' if unsafe else '❌ KILL SWITCH ACTIVATED'}\n")
