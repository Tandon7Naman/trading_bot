"""
BaseStrategy: Abstract interface for all strategies.
"""
class BaseStrategy:
    def generate_signals(self, data):
        raise NotImplementedError
    def backtest(self, data):
        raise NotImplementedError
