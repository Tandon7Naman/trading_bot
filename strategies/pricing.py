import math

class GoldPricingEngine:
    """
    Protocol 3.1: Pricing Physics and Pip Anomalies.
    Standardizes 'Pip' values across different broker precisions (2-digit vs 3-digit).
    """
    
    @staticmethod
    def get_precision(price):
        """
        Determines the number of decimal places in the current price.
        """
        price_str = f"{price:.5f}".rstrip('0')
        if '.' in price_str:
            return len(price_str.split('.')[1])
        return 0

    @staticmethod
    def calculate_sl_tp(entry_price, action, sl_pips, tp_pips):
        """
        Calculates absolute Price levels for Stop Loss and Take Profit.
        
        CRITICAL FIX (Protocol 3.1):
        We define 1 Gold Pip = $0.10 price movement.
        We DO NOT use 'points' (0.01 or 0.001) to avoid the 3-decimal bug.
        """
        
        # Standard Gold Pip Value in USD (Safe Hardcode)
        # 10 Pips = $1.00 move
        # 1 Pip = $0.10 move
        PIP_VALUE = 0.10
        
        sl_dist = sl_pips * PIP_VALUE
        tp_dist = tp_pips * PIP_VALUE
        
        if action == 1: # BUY
            sl_price = entry_price - sl_dist
            tp_price = entry_price + tp_dist
        elif action == 2: # SELL
            sl_price = entry_price + sl_dist
            tp_price = entry_price - tp_dist
        else:
            return 0.0, 0.0
            
        # Rounding to match broker precision (prevents 'Invalid Price' errors)
        digits = GoldPricingEngine.get_precision(entry_price)
        return round(sl_price, digits), round(tp_price, digits)
