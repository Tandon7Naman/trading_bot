import numpy as np
from datetime import datetime

class FeatureEngine:
    """Extract 15 features from market data for AI"""
    
    def __init__(self):
        self.min_history = 30
    
    # Technical Features (4)
    def calculate_rsi(self, closes, period=14):
        if len(closes) < period:
            return 0.0
        closes = np.array(closes, dtype=float)
        deltas = np.diff(closes)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 0
        rsi = 100.0 - (100.0 / (1.0 + rs)) if rs != 0 else 50.0
        normalized = ((rsi - 50) / 50)
        return float(np.clip(normalized, -1, 1))
    
    def calculate_macd(self, closes, fast=12, slow=26):
        if len(closes) < slow:
            return 0.0
        closes = np.array(closes, dtype=float)
        ema_fast = self._ema(closes, fast)
        ema_slow = self._ema(closes, slow)
        macd_line = ema_fast - ema_slow
        hist = macd_line[-1] if len(macd_line) > 0 else 0
        return float(np.tanh(hist / 100))
    
    def calculate_bollinger_bands(self, closes, period=20):
        if len(closes) < period:
            return 0.0
        closes = np.array(closes[-period:], dtype=float)
        sma = np.mean(closes)
        std = np.std(closes)
        upper = sma + (std * 2)
        lower = sma - (std * 2)
        width = (upper - lower) / sma if sma != 0 else 0
        return float(np.clip(width / 0.2, 0, 1))
    
    def calculate_adx(self, highs, lows, closes, period=14):
        if len(closes) < period:
            return 0.5
        highs = np.array(highs[-period:], dtype=float)
        lows = np.array(lows[-period:], dtype=float)
        closes = np.array(closes[-period:], dtype=float)
        up_moves = np.maximum(highs[1:] - highs[:-1], 0)
        down_moves = np.maximum(lows[:-1] - lows[1:], 0)
        adx_value = (up_moves.mean() - down_moves.mean()) / (closes.std() + 0.001)
        adx_value = np.clip(adx_value, -1, 1)
        return float((adx_value + 1) / 2)
    
    # Microstructure (2)
    def calculate_bid_ask_spread(self, bid, ask, close):
        if close == 0 or bid == 0 or ask == 0:
            return 0.0
        spread = (ask - bid) / close
        return float(np.clip(spread / 0.002, 0, 1))
    
    def calculate_order_imbalance(self, buy_volume, sell_volume):
        total = buy_volume + sell_volume
        if total == 0:
            return 0.0
        imbalance = (buy_volume - sell_volume) / total
        return float(np.clip(imbalance, -1, 1))
    
    # Macro (3)
    def calculate_usdinr_feature(self, usdinr_rate):
        normalized = np.clip((usdinr_rate - 75) / 10, 0, 1)
        return float(normalized)
    
    def calculate_us_yield_feature(self, us_10y_yield):
        normalized = np.clip((us_10y_yield - 2) / 3, 0, 1)
        return float(normalized)
    
    def calculate_au_ag_ratio_feature(self, gold_price, silver_price):
        if silver_price == 0:
            return 0.5
        ratio = gold_price / silver_price
        normalized = np.clip((ratio - 50) / 30, 0, 1)
        return float(normalized)
    
    # Fundamental (2)
    def calculate_monsoon_feature(self, actual_rainfall_mm, lpa_mm):
        if lpa_mm == 0:
            return 0.0
        deviation = (actual_rainfall_mm - lpa_mm) / lpa_mm
        return float(np.tanh(deviation))
    
    def calculate_real_yield_feature(self, nominal_yield, inflation_rate):
        real_yield = nominal_yield - inflation_rate
        return float(np.tanh(real_yield / 2))
    
    # Regulatory (2)
    def calculate_import_duty_feature(self, duty_rate):
        normalized = np.clip((duty_rate - 0.04) / 0.11, 0, 1)
        return float(normalized)
    
    def calculate_duty_shock_feature(self, duty_history_7days):
        if len(duty_history_7days) < 2:
            return 0.0
        changed = max(duty_history_7days) != min(duty_history_7days)
        return 1.0 if changed else 0.0
    
    # Seasonal (1)
    def calculate_lunar_demand_feature(self):
        today = datetime.now()
        if today.month in [11, 12, 1]:
            return 0.6
        return 0.0
    
    # Fair Value (1)
    def calculate_fair_value_feature(self, spot_gold_usd, usdinr, duty_rate, current_price, bank_premium_pct=0.015, gst_rate=0.03):
        """
        Calculates the deviation of the current price from the fully-costed fair value.
        This version includes unit conversion, import duty, bank premium, and GST.
        """
        # Constants for conversion
        GRAMS_PER_OUNCE = 31.1034768
        CONVERSION_FACTOR_10G = 10 / GRAMS_PER_OUNCE

        # Calculate the fair value
        base_price_inr = spot_gold_usd * usdinr * CONVERSION_FACTOR_10G
        landed_cost = base_price_inr * (1 + duty_rate)
        landed_cost_with_premium = landed_cost * (1 + bank_premium_pct)
        fair_value = landed_cost_with_premium * (1 + gst_rate)

        if current_price == 0:
            return 0.0
        
        # Calculate the deviation and normalize it
        deviation = (current_price - fair_value) / fair_value
        return float(np.tanh(deviation * 10)) # Use a multiplier to increase sensitivity

    
    # Helper
    def _ema(self, data, period):
        data = np.array(data, dtype=float)
        if len(data) == 0:
            return np.array([])
        ema = np.zeros_like(data)
        ema[0] = data[0]
        multiplier = 2 / (period + 1)
        for i in range(1, len(data)):
            ema[i] = data[i] * multiplier + ema[i-1] * (1 - multiplier)
        return ema
    
    # Main Function
    def extract_features(self, market_data):
        features = [
            self.calculate_rsi(market_data['closes']),
            self.calculate_macd(market_data['closes']),
            self.calculate_bollinger_bands(market_data['closes']),
            self.calculate_adx(market_data['highs'], market_data['lows'], market_data['closes']),
            self.calculate_bid_ask_spread(market_data['bid'], market_data['ask'], market_data['closes'][-1]),
            self.calculate_order_imbalance(market_data['buy_volume'], market_data['sell_volume']),
            self.calculate_usdinr_feature(market_data['usdinr']),
            self.calculate_us_yield_feature(market_data['us_10y_yield']),
            self.calculate_au_ag_ratio_feature(market_data['closes'][-1], 1000),
            self.calculate_monsoon_feature(market_data['monsoon_rainfall'], market_data['monsoon_lpa']),
            self.calculate_real_yield_feature(market_data['us_10y_yield'], market_data['inflation_rate']),
            self.calculate_import_duty_feature(market_data['import_duty']),
            self.calculate_duty_shock_feature(market_data['duty_history']),
            self.calculate_lunar_demand_feature(),
            self.calculate_fair_value_feature(market_data['spot_gold_usd'], market_data['usdinr'], 
                                             market_data['import_duty'], market_data['current_price'])
        ]
        features = np.array(features, dtype=np.float32)
        features = np.nan_to_num(features, 0)
        features = np.clip(features, -1, 1)
        return features

if __name__ == "__main__":
    fe = FeatureEngine()
    mock_data = {
        'closes': [68500 + i*5 for i in range(30)],
        'highs': [68550 + i*5 for i in range(30)],
        'lows': [68450 + i*5 for i in range(30)],
        'bid': 68505, 'ask': 68515,
        'buy_volume': 10000, 'sell_volume': 8000,
        'spot_gold_usd': 2500, 'usdinr': 83.5,
        'us_10y_yield': 4.0, 'inflation_rate': 5.5,
        'monsoon_rainfall': 150, 'monsoon_lpa': 140,
        'import_duty': 0.06, 'duty_history': [0.06]*7,
        'current_price': 68650
    }
    features = fe.extract_features(mock_data)
    print(f"\n✅ Extracted {len(features)} features")
    print(f"Values: {features}")
