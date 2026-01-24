import logging


class RiskManager:

        def update_peak_balance(self, current_balance):
            if current_balance > self.peak_balance:
                self.peak_balance = current_balance

        def check_drawdown_protection(self, current_balance):
            drawdown = (self.peak_balance - current_balance) / self.peak_balance
            if drawdown >= (self.max_drawdown_pct / 100):
                logging.error(f"Max drawdown limit reached ({drawdown*100:.2f}%) - CIRCUIT BREAKER ACTIVATED")
                return False
            return True
    """Professional risk management following Kelly Criterion and practical limits."""

    def __init__(self, account_size, max_loss_pct=2, max_drawdown_pct=5):
        self.account_size = account_size
        self.max_loss_pct = max_loss_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.peak_balance = account_size
        self.daily_trades = 0
        self.daily_loss = 0

    def calculate_position_size(self, entry_price, stop_loss_price, win_rate=0.55):
        risk_per_trade = self.account_size * 0.02
        risk_per_share = abs(entry_price - stop_loss_price)
        if risk_per_share == 0:
            return 0
        position_size = int(risk_per_trade / risk_per_share)
        max_position = max(1, int((self.account_size * 0.20) / entry_price))
        final_size = min(position_size, max_position)
        return max(final_size, 1) if position_size > 0 and max_position > 0 else 0

    def check_trade_allowed(self, current_balance, daily_trades=0, daily_loss=0):
        if daily_trades >= 5:
            logging.warning("Daily trade limit (5) reached")
            return False
        if daily_loss > (current_balance * 0.05):
            logging.error("Daily loss limit (5%) reached - HALT TRADING")
            return False
        return True


if __name__ == "__main__":
    rm = RiskManager(100000)
    print("Position Size:", rm.calculate_position_size(69000, 68800))
    print("Trade Allowed:", rm.check_trade_allowed(95000, 2, 1000))
