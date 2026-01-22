import logging

import yfinance as yf


class GlobalCuesMonitor:
    """Monitor global markets for bias direction."""

    def __init__(self):
        self.sgx_nifty = None
        self.us_futures = {}
        self.asia_indices = {}
        self.session_bias = None

    def fetch_sgx_nifty(self):
        try:
            sgx = yf.download("^NSEI", period="2d", progress=False)
            self.sgx_nifty = sgx["Close"].iloc[-1] - sgx["Close"].iloc[-2]
            return self.sgx_nifty
        except Exception as e:
            logging.warning(f"SGX fetch failed: {str(e)}")
            return None

    def fetch_us_futures(self):
        symbols = {"Dow": "^DJI", "S&P 500": "^GSPC", "Nasdaq": "^IXIC"}
        for name, symbol in symbols.items():
            try:
                data = yf.download(symbol, period="2d", progress=False)
                change_pct = (
                    (data["Close"].iloc[-1] - data["Close"].iloc[-2]) / data["Close"].iloc[-2]
                ) * 100
                self.us_futures[name] = change_pct
            except Exception as e:
                logging.warning(f"US futures fetch failed for {name}: {str(e)}")

    def fetch_asia_indices(self):
        symbols = {"Nikkei": "^N225", "Hang Seng": "^HSI"}
        for name, symbol in symbols.items():
            try:
                data = yf.download(symbol, period="2d", progress=False)
                change_pct = (
                    (data["Close"].iloc[-1] - data["Close"].iloc[-2]) / data["Close"].iloc[-2]
                ) * 100
                self.asia_indices[name] = change_pct
            except Exception as e:
                logging.warning(f"Asia fetch failed for {name}: {str(e)}")

    def determine_session_bias(self):
        bias_scores = []
        if self.sgx_nifty and self.sgx_nifty > 0:
            bias_scores.append(1)
        for change in self.us_futures.values():
            if change > 0.5:
                bias_scores.append(1)
            elif change < -0.5:
                bias_scores.append(-1)
        for change in self.asia_indices.values():
            if change > 0.5:
                bias_scores.append(1)
            elif change < -0.5:
                bias_scores.append(-1)
        if not bias_scores:
            self.session_bias = "NEUTRAL"
        else:
            avg = sum(bias_scores) / len(bias_scores)
            self.session_bias = "BULLISH" if avg > 0.5 else "BEARISH" if avg < -0.5 else "NEUTRAL"
        return self.session_bias


if __name__ == "__main__":
    monitor = GlobalCuesMonitor()
    monitor.fetch_sgx_nifty()
    monitor.fetch_us_futures()
    monitor.fetch_asia_indices()
    bias = monitor.determine_session_bias()
    print(f"Session Bias: {bias}")
