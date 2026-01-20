import math
from config.settings import ASSET_CONFIG

class RiskManager:
    """
    Protocol 2.2: The 3-5-7 Risk Framework.
    - 3% Max Risk per Trade (Hard Cap)
    - 5% Max Portfolio Risk (Correlation Shield)
    - 7% Profit Logic (R:R > 1:2.3)
    """
    
    # CONSTANTS (Protocol 2.2)
    MAX_TRADE_RISK_PCT = 0.03       # 3% Hard Cap
    MAX_PORTFOLIO_RISK_PCT = 0.05   # 5% Portfolio Cap
    MIN_RISK_REWARD_RATIO = 2.3     # The "7% Rule" translated to Expectancy

    @staticmethod
    def validate_setup(entry_price, sl_price, tp_price):
        """
        Protocol 2.2.3: The 7% Profit Target (Expectancy Check).
        Rejects trades with poor Risk:Reward ratios.
        """
        risk = abs(entry_price - sl_price)
        reward = abs(tp_price - entry_price)
        
        if risk == 0: return False, "Zero Risk (Invalid SL)"
        
        rr_ratio = reward / risk
        
        if rr_ratio < RiskManager.MIN_RISK_REWARD_RATIO:
            return False, f"Low R:R ({rr_ratio:.2f} < {RiskManager.MIN_RISK_REWARD_RATIO})"
            
        return True, f"Valid R:R ({rr_ratio:.2f})"

    @staticmethod
    def calculate_lot_size(equity, entry_price, sl_price, symbol="XAUUSD", 
                           confidence_score=1.0, current_portfolio_risk_usd=0.0):
        """
        Calculates position size respecting the 3% and 5% rules.
        Args:
            confidence_score: 1.0 = Normal (1%), 2.0 = High (2%), 3.0 = Max (3%)
            current_portfolio_risk_usd: The $ amount currently at risk in other trades.
        """
        config = ASSET_CONFIG.get(symbol)
        if not config: return 0.0

        # --- 1. DETERMINE RISK % (The 3% Rule) ---
        # Base risk is 1%, scaled by confidence, capped at 3%
        base_risk_pct = 0.01 
        target_risk_pct = min(base_risk_pct * confidence_score, RiskManager.MAX_TRADE_RISK_PCT)
        
        risk_amount_usd = equity * target_risk_pct

        # --- 2. CHECK PORTFOLIO CAP (The 5% Rule) ---
        max_portfolio_risk_usd = equity * RiskManager.MAX_PORTFOLIO_RISK_PCT
        available_risk_budget = max_portfolio_risk_usd - current_portfolio_risk_usd
        
        if available_risk_budget <= 0:
            print(f"   🛡️ 5% RULE: Portfolio Full! (Risk Locked: ${current_portfolio_risk_usd:.2f})")
            return 0.0
            
        # Clamp our trade risk to whatever budget is left
        final_risk_usd = min(risk_amount_usd, available_risk_budget)
        
        if final_risk_usd < (equity * 0.001): # Ignore microscopic trades
            return 0.0

        # --- 3. CALCULATE VOLUME ---
        price_distance = abs(entry_price - sl_price)
        if price_distance < config['tick_size']: return 0.0
        
        loss_per_lot = price_distance * config['contract_size']
        if loss_per_lot == 0: return 0.0
        
        raw_lots = final_risk_usd / loss_per_lot

        # --- 4. MARGIN & PHYSICS CHECKS (Protocol 4.3/9.0) ---
        # (Reusing previous logic for Margin Cap)
        leverage = config.get('leverage', 100.0)
        contract_size = config['contract_size']
        usable_equity = equity * 0.95
        margin_max_lots = usable_equity / (entry_price * contract_size / leverage)
        
        final_lots = min(raw_lots, margin_max_lots)
        
        # Normalize
        step = config.get('vol_step', 0.01)
        lots = math.floor(final_lots / step) * step
        
        min_vol = config.get('min_vol', 0.01)
        max_vol = config.get('max_vol', 10.0)
        lots = max(min_vol, min(max_vol, lots))

        print(f"   ⚖️  3-5-7 CALC: Risk ${final_risk_usd:.2f} ({target_risk_pct*100:.1f}%) | Portfolio Risk: ${current_portfolio_risk_usd:.2f} -> Size {lots}")
        return round(lots, 2)


class CircuitBreaker:
    """ Protocol 7.2: Global Kill Switch (Unchanged) """
    def __init__(self, initial_equity, daily_loss_limit=0.02, max_drawdown_limit=0.05):
        self.starting_equity = initial_equity
        self.high_water_mark = initial_equity
        self.daily_loss_limit = daily_loss_limit 
        self.max_drawdown_limit = max_drawdown_limit 

    def check_health(self, current_equity):
        if current_equity > self.high_water_mark:
            self.high_water_mark = current_equity

        loss_pct = (self.starting_equity - current_equity) / self.starting_equity
        if loss_pct >= self.daily_loss_limit:
            return False, f"DAILY LOSS LIMIT HIT (-{loss_pct*100:.2f}%)"

        drawdown_pct = (self.high_water_mark - current_equity) / self.high_water_mark
        if drawdown_pct >= self.max_drawdown_limit:
            return False, f"MAX DRAWDOWN LIMIT HIT (-{drawdown_pct*100:.2f}%)"

        return True, "Healthy"