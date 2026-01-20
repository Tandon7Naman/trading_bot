import math
from config.settings import ASSET_CONFIG

class RiskManager:
    """
    Protocol 4.3 & 9.0: Margin Validation & Key Sync.
    Uses 'min_vol', 'max_vol' from the new config structure.
    """
    
    @staticmethod
    def calculate_lot_size(equity, entry_price, sl_price, symbol="XAUUSD", risk_pct=0.01):
        config = ASSET_CONFIG.get(symbol)
        if not config:
            print(f"   ⚠️ Risk Manager: Unknown config for {symbol}")
            return 0.01

        # 1. RISK BASED SIZING
        risk_amount = equity * risk_pct
        price_distance = abs(entry_price - sl_price)
        
        if price_distance < config['tick_size']:
            print("   ⚠️ Risk Manager: SL too close to Entry!")
            return 0.0
            
        loss_per_lot = price_distance * config['contract_size']
        risk_lots = risk_amount / loss_per_lot
        
        # 2. MARGIN BASED SIZING
        leverage = config.get('leverage', 100.0)
        contract_size = config['contract_size']
        usable_equity = equity * 0.95
        
        notional_value_per_lot = entry_price * contract_size
        margin_per_lot = notional_value_per_lot / leverage
        margin_max_lots = usable_equity / margin_per_lot
        
        # 3. LOGIC SELECTION
        raw_lots = min(risk_lots, margin_max_lots)
        
        # 4. NORMALIZE (Using Protocol 9.0 Keys: vol_step, min_vol, max_vol)
        step = config.get('vol_step', 0.01)
        lots = math.floor(raw_lots / step) * step
        
        min_vol = config.get('min_vol', 0.01)
        max_vol = config.get('max_vol', 10.0)
        
        lots = max(min_vol, min(max_vol, lots))
        
        constraint = "RISK" if risk_lots < margin_max_lots else "MARGIN"
        print(f"   ⚖️  SIZE CALC ({constraint}): Risk {risk_lots:.2f} | Margin Cap {margin_max_lots:.2f} -> Final {lots} Lots")
        return round(lots, 2)


class CircuitBreaker:
    """
    Protocol 7.2: Global Kill Switch.
    """
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