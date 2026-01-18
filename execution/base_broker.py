from abc import ABC, abstractmethod

class GenericBroker(ABC):
    """
    Protocol 2.3: The Generic Broker Contract.
    All brokers (Paper, MT5, Binance) must implement these 4 methods.
    """
    
    @abstractmethod
    def connect(self):
        """Establishes connection to the broker/API."""
        pass

    @abstractmethod
    def get_tick(self, symbol):
        """Returns the latest price tick for a symbol."""
        pass

    @abstractmethod
    def get_positions(self):
        """Returns current account equity and open positions."""
        pass

    @abstractmethod
    def place_order(self, action, symbol, price, qty, **kwargs):
        """
        Sends an order to the broker.
        action: 1=BUY, 2=SELL
        """
        pass
