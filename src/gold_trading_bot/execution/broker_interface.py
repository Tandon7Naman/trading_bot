"""
BrokerInterface: Abstract broker API.
"""
class BrokerInterface:
    def place_order(self, order):
        raise NotImplementedError
    def get_account_info(self):
        raise NotImplementedError
