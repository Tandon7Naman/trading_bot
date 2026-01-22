class GoldPricingEngine:
    """
    Protocol 4.1.1: Precision Enforcement.
    Prevents 'Invalid Price' (MT5 Error 10015) by enforcing strict rounding.
    """

    @staticmethod
    def calculate_sl_tp(entry_price, order_type, sl_pips, tp_pips, precision=2):
        """
        Calculates SL/TP prices and rounds them to the asset's specific digits.

        Args:
            entry_price (float): The entry price.
            order_type (int): 1 for BUY, 2 for SELL.
            sl_pips (int): Distance in PIPS (1 pip = $0.10 or $0.01 depending on config).
            tp_pips (int): Distance in PIPS.
            precision (int): Decimal places to round to (Gold = 2).

        Returns:
            (float, float): Rounded SL and TP prices.
        """
        # Standard Gold: 1 Pip = $0.10 (approx) or $0.01 depending on broker.
        # Based on your Config (Protocol 2.2), tick_size is 0.01.
        # So 50 pips usually means $0.50 distance if counting ticks.
        # NOTE: Adjust multiplier to match your specific Pip definition.
        # If you define 1 Pip = 10 cents ($0.10), then multiplier is 0.10.
        pip_value = 0.10

        sl_dist = sl_pips * pip_value
        tp_dist = tp_pips * pip_value

        sl_price = 0.0
        tp_price = 0.0

        if order_type == 1:  # BUY
            sl_price = entry_price - sl_dist
            tp_price = entry_price + tp_dist
        elif order_type == 2:  # SELL
            sl_price = entry_price + sl_dist
            tp_price = entry_price - tp_dist

        # PROTOCOL 4.1.1: STRICT ROUNDING
        return round(sl_price, precision), round(tp_price, precision)
