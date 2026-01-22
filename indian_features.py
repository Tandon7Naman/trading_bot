"""
Indian Market Specific Features
Adds: Monsoon factor, Lunar demand, Import duty, Fair value, Real yield
"""

from datetime import datetime

import numpy as np


class IndianMarketFeatures:
    """
    Calculate India-specific features for gold trading
    """

    def __init__(self):
        self.current_duty_rate = 0.06  # 6% import duty
        self.duty_history = []

    def calculate_monsoon_factor(self, actual_rainfall, lpa_rainfall):
        """
        Feature #11: Monsoon Impact
        Good monsoon → Rural demand ↑ → Gold demand ↑
        """
        if lpa_rainfall == 0:
            return 0.0

        deviation = (actual_rainfall - lpa_rainfall) / lpa_rainfall
        # Normalize to [-1, 1]
        return np.tanh(deviation)

    def calculate_lunar_demand_index(self, date=None):
        """
        Feature #12: Hindu Lunar Calendar Demand
        Festivals → High gold buying
        """
        if date is None:
            date = datetime.now()

        month = date.month
        day = date.day

        # Akshaya Tritiya (April-May) - Most auspicious
        if month in [4, 5] and 8 <= day <= 12:
            return 1.0

        # Dhanteras (Oct-Nov) - Diwali shopping
        elif month in [10, 11] and 12 <= day <= 16:
            return 0.8

        # Wedding season (Nov-Jan)
        elif month in [11, 12, 1]:
            return 0.6

        # Pitra Paksha (Sept) - Inauspicious
        elif month == 9 and day >= 15:
            return -0.5

        else:
            return 0.0

    def calculate_import_duty_feature(self, current_duty=None):
        """
        Feature #13: Import Duty Level
        Duty typically 4-15%, affects local prices
        """
        if current_duty is None:
            current_duty = self.current_duty_rate

        # Normalize: 4% = 0, 15% = 1
        min_duty, max_duty = 0.04, 0.15
        normalized_duty = (current_duty - min_duty) / (max_duty - min_duty)
        return np.clip(normalized_duty, 0, 1)

    def calculate_fair_value_premium(self, mcx_price, international_price_usd, usd_inr_rate):
        """
        Feature #14: Fair Value Premium/Discount
        Compares local price to landed international price.
        Premium suggests high local demand.
        """
        if international_price_usd <= 0 or usd_inr_rate <= 0:
            return 0.0

        # Convert international price to INR per 10 grams
        # (assuming international price is per troy ounce)
        price_per_gram_usd = international_price_usd / 31.1035
        price_per_10_grams_inr = price_per_gram_usd * 10 * usd_inr_rate

        # Calculate landed price with import duty
        landed_price = price_per_10_grams_inr * (1 + self.current_duty_rate)

        # Calculate premium/discount percentage
        premium = (mcx_price - landed_price) / landed_price

        # Normalize with tanh to keep it in a reasonable range
        return np.tanh(premium * 10)  # Multiplier to make it more sensitive

    def calculate_real_yield(self, gsec_yield, inflation_rate):
        """
        Feature #15: Real Yield
        Lower real yield makes gold more attractive.
        gsec_yield: 10-year government bond yield
        inflation_rate: CPI inflation
        """
        real_yield = gsec_yield - inflation_rate
        # Normalize: We can treat a range, e.g., -5% to 5%
        # A higher real yield is negative for gold, so we invert the signal.
        normalized_yield = -(np.tanh(real_yield / 5.0))  # Normalize over a +/- 5% range
        return normalized_yield

    def add_all_features(self, df, external_data):
        """
        Adds all Indian market features to the DataFrame.

        Args:
            df (pd.DataFrame): Must have a 'timestamp' column.
            external_data (pd.DataFrame): Must have 'timestamp', 'actual_rainfall',
                                          'lpa_rainfall', 'gsec_yield', 'cpi_inflation',
                                          'international_price_usd', 'usd_inr_rate'.
                                          Should be indexed by timestamp.

        Returns:
            pd.DataFrame: DataFrame with added features.
        """
        if "timestamp" not in df.columns:
            raise ValueError("Input DataFrame must have a 'timestamp' column.")

        df["monsoon_factor"] = df.apply(
            lambda row: self.calculate_monsoon_factor(
                external_data.loc[row.name, "actual_rainfall"],
                external_data.loc[row.name, "lpa_rainfall"],
            ),
            axis=1,
        )

        df["lunar_demand"] = df["timestamp"].apply(self.calculate_lunar_demand_index)

        df["import_duty"] = self.calculate_import_duty_feature(self.current_duty_rate)

        df["fair_value_premium"] = df.apply(
            lambda row: self.calculate_fair_value_premium(
                row["close"],
                external_data.loc[row.name, "international_price_usd"],
                external_data.loc[row.name, "usd_inr_rate"],
            ),
            axis=1,
        )

        df["real_yield"] = df.apply(
            lambda row: self.calculate_real_yield(
                external_data.loc[row.name, "gsec_yield"],
                external_data.loc[row.name, "cpi_inflation"],
            ),
            axis=1,
        )

        return df
