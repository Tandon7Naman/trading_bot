class SignalConfluenceFilter:
    """Require ≥2 of 3 indicators aligned for signal."""

    @staticmethod
    def check_indicator_confluence(indicators):
        rsi_aligned = 50 < indicators.get("rsi", 0) < 70
        macd_aligned = indicators.get("macd", 0) > indicators.get("signal_line", 0)
        ema_aligned = indicators.get("ema_20", 0) > indicators.get("ema_50", 0)
        aligned_count = sum([rsi_aligned, macd_aligned, ema_aligned])
        return aligned_count >= 2


if __name__ == "__main__":
    indicators = {"rsi": 60, "macd": 1.2, "signal_line": 1.0, "ema_20": 69000, "ema_50": 68800}
    print("Confluence:", SignalConfluenceFilter.check_indicator_confluence(indicators))
