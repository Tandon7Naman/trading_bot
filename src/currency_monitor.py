import logging

import yfinance as yf


class CurrencyMonitor:
    """Monitor currency pairs and dollar index."""

    def __init__(self):
        self.usdinr_price = None
        self.dxy_price = None
        self.usdinr_change_pct = None
        self.dxy_change_pct = None

    def fetch_currencies(self):
        try:
            usdinr = yf.download("USDINR=X", period="2d", progress=False)
            self.usdinr_price = usdinr["Close"].iloc[-1]
            self.usdinr_change_pct = (
                (usdinr["Close"].iloc[-1] - usdinr["Close"].iloc[-2]) / usdinr["Close"].iloc[-2]
            ) * 100
            dxy = yf.download("^DXY", period="2d", progress=False)
            self.dxy_price = dxy["Close"].iloc[-1]
            self.dxy_change_pct = (
                (dxy["Close"].iloc[-1] - dxy["Close"].iloc[-2]) / dxy["Close"].iloc[-2]
            ) * 100
            logging.info(
                f"USD/INR: {self.usdinr_price:.2f} ({self.usdinr_change_pct:+.2f}%), DXY: {self.dxy_price:.2f} ({self.dxy_change_pct:+.2f}%)"
            )
        except Exception as e:
            logging.error(f"Currency fetch failed: {str(e)}")

    def get_currency_impact_on_gold(self):
        mcx_impact = "NEUTRAL"
        xauusd_impact = "NEUTRAL"
        if self.usdinr_change_pct is not None:
            if self.usdinr_change_pct < -0.5:
                mcx_impact = "DOWN"
            elif self.usdinr_change_pct > 0.5:
                mcx_impact = "UP"
        if self.dxy_change_pct is not None:
            if self.dxy_change_pct > 0.5:
                xauusd_impact = "DOWN"
            elif self.dxy_change_pct < -0.5:
                xauusd_impact = "UP"
        return {
            "mcx_impact": mcx_impact,
            "xauusd_impact": xauusd_impact,
            "usdinr_change": self.usdinr_change_pct,
            "dxy_change": self.dxy_change_pct,
        }


if __name__ == "__main__":
    monitor = CurrencyMonitor()
    monitor.fetch_currencies()
    impact = monitor.get_currency_impact_on_gold()
    print(f"Currency Impact: {impact}")
