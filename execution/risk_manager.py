import math

from config.settings import ASSET_CONFIG


class RiskManager:
    """
    Phase 2 Compliance: The 'Chief Risk Officer' Module.
    - Implements 1-2% Standard Risk Rule.
    - Implements 3% 'High Conviction' Hard Cap.
    - Implements 5% Portfolio Correlation Cap.
    """

    # 2026 Mandate Constants
    MAX_TRADE_RISK_PCT = 0.03  # 3% Hard Cap
    MAX_PORTFOLIO_RISK_PCT = 0.05  # 5% Portfolio Cap
    MIN_RISK_REWARD_RATIO = 2.0  # Minimum Expectancy

    @staticmethod
    def calculate_lot_size(
        equity, entry_price, sl_price, symbol, confidence_score=1.0, current_portfolio_risk_usd=0.0
    ):
        """
        Calculates the mathematically safe position size.
        """
        config = ASSET_CONFIG.get(symbol)
        if not config:
            print(f"   ❌ RISK ERROR: No config for {symbol}")
            return 0.0

        # --- RULE 1: THE 1-2% BASELINE ---
        base_risk_pct = 0.01
        target_risk_pct = min(base_risk_pct * confidence_score, RiskManager.MAX_TRADE_RISK_PCT)
        risk_amount_usd = equity * target_risk_pct

        # --- RULE 2: THE 5% PORTFOLIO CAP ---
        max_portfolio_risk_usd = equity * RiskManager.MAX_PORTFOLIO_RISK_PCT
        available_risk_budget = max_portfolio_risk_usd - current_portfolio_risk_usd

        if available_risk_budget <= 0:
            print(
                f"   🛡️ RISK VETO: Portfolio Overloaded! (Locked Risk: ${current_portfolio_risk_usd:.2f})"
            )
            return 0.0

        final_risk_usd = min(risk_amount_usd, available_risk_budget)

        # --- RULE 3: PHYSICS & SIZING ---
        price_distance = abs(entry_price - sl_price)
        if price_distance < config.get("tick_size", 0.01):
            return 0.0

        loss_per_lot = price_distance * config.get("contract_size", 100)
        if loss_per_lot == 0:
            return 0.0

        raw_lots = final_risk_usd / loss_per_lot

        # --- RULE 4: MARGIN & LIMITS ---
        leverage = config.get("leverage", 100.0)
        margin_required = (entry_price * config["contract_size"]) / leverage
        max_lots_by_equity = (equity * 0.95) / margin_required

        final_lots = min(raw_lots, max_lots_by_equity)

        step = config.get("vol_step", 0.01)
        lots = math.floor(final_lots / step) * step

        lots = max(config.get("min_vol", 0.01), min(config.get("max_vol", 100.0), lots))

        print(
            f"   ⚖️  RISK MATH: Target Risk ${final_risk_usd:.2f} ({target_risk_pct * 100:.1f}%) | Portfolio Budget: ${available_risk_budget:.2f} -> Size {lots}"
        )
        return round(lots, 2)

    @staticmethod
    def validate_setup(entry_price, sl_price, tp_price):
        """Phase 2 Check: Expectancy."""
        risk = abs(entry_price - sl_price)
        reward = abs(tp_price - entry_price)
        if risk == 0:
            return False, "Zero Risk"
        rr_ratio = reward / risk
        if rr_ratio < RiskManager.MIN_RISK_REWARD_RATIO:
            return False, f"Poor R:R ({rr_ratio:.2f} < {RiskManager.MIN_RISK_REWARD_RATIO})"
        return True, f"Valid R:R ({rr_ratio:.2f})"


class CircuitBreaker:
    """
    Protocol 7.2: Global Kill Switch.
    Prevents 'Risk of Ruin' by enforcing daily loss limits.
    """

    def __init__(self, initial_equity, daily_loss_limit=0.02, max_drawdown_limit=0.05):
        self.starting_equity = initial_equity
        self.high_water_mark = initial_equity
        self.daily_loss_limit = daily_loss_limit  # Shutdown if day is -2%
        self.max_drawdown_limit = max_drawdown_limit  # Shutdown if peak-to-trough -5%

    def check_health(self, current_equity):
        # Update High Water Mark
        if current_equity > self.high_water_mark:
            self.high_water_mark = current_equity

        # 1. Daily Loss Check
        loss_pct = (self.starting_equity - current_equity) / self.starting_equity
        if loss_pct >= self.daily_loss_limit:
            return False, f"DAILY LOSS LIMIT HIT (-{loss_pct * 100:.2f}%)"

        # 2. Max Drawdown Check
        drawdown_pct = (self.high_water_mark - current_equity) / self.high_water_mark
        if drawdown_pct >= self.max_drawdown_limit:
            return False, f"MAX DRAWDOWN LIMIT HIT (-{drawdown_pct * 100:.2f}%)"

        return True, "Healthy"
