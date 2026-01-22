from abc import ABC, abstractmethod


class BrokerInterface(ABC):
    """
    Protocol 7.1: The 'Iron Contract'.
    Any Broker (Paper or Live) MUST implement these methods.
    This allows the Strategy to switch execution engines instantly.
    """

    @abstractmethod
    def connect(self):
        """Establishes connection to the exchange/database."""
        pass

    @abstractmethod
    def get_tick(self, symbol):
        """Returns the current real-time price."""
        pass

    @abstractmethod
    def get_positions(self):
        """Returns account equity, open positions, and pending orders."""
        pass

    @abstractmethod
    def place_order(self, action, symbol, price, qty, **kwargs):
        """
        Executes a trade.
        Args:
            action (int): 1=Buy, 2=Sell.
            symbol (str): Asset name.
            price (float): Limit or Market price.
            qty (float): Lot size.
            kwargs: 'sl', 'tp', 'type' (MARKET/LIMIT), 'tif', 'atr'.
        """
        pass

    @abstractmethod
    def check_limits(self, current_price, symbol):
        """Checks if Price hit SL, TP, or Limit Orders."""
        pass
