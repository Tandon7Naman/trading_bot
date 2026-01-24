class BotError(Exception):
    """Base class for all bot exceptions."""

    pass


class DataFeedError(BotError):
    """Raised when data feed is stale, empty, or disconnected."""

    pass


class BrokerConnectionError(BotError):
    """Raised when the broker (MT5/Paper) is unreachable."""

    pass


class RiskViolationError(BotError):
    """Raised when a trade exceeds risk limits (e.g., Drawdown > 5%)."""

    pass



    pass
