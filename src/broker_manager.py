"""
Multi-Broker Manager for Dual-Market Gold Trading
Handles both Alpaca (XAUUSD/GLD) and Indian Broker (MCX Gold)
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)


class BrokerManager:
    """Manages multiple brokers for dual-market trading"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.brokers = {}
        self.positions = {}
        self.active_markets = []
        
    def add_broker(self, name: str, connector):
        """Add a broker connector"""
        try:
            if connector.login():
                self.brokers[name] = connector
                self.active_markets.append(name)
                logger.info(f"✅ {name} broker added successfully")
                return True
            else:
                logger.error(f"❌ Failed to connect {name}")
                return False
        except Exception as e:
            logger.error(f"❌ Error adding {name}: {e}")
            return False
    
    def get_all_positions(self) -> Dict:
        """Get positions from all brokers"""
        all_positions = {}
        
        for name, broker in self.brokers.items():
            try:
                positions = broker.get_positions()
                all_positions[name] = positions
                logger.info(f"📋 {name}: {len(positions)} positions")
            except Exception as e:
                logger.error(f"❌ Error fetching {name} positions: {e}")
                all_positions[name] = []
        
        return all_positions
    
    def get_total_exposure(self) -> Dict:
        """Calculate total exposure across all markets"""
        exposure = {
            'alpaca_usd': 0,
            'mcx_inr': 0,
            'total_usd': 0
        }
        
        all_positions = self.get_all_positions()
        
        # Alpaca exposure (USD)
        if 'alpaca' in all_positions:
            for pos in all_positions['alpaca']:
                exposure['alpaca_usd'] += abs(pos.get('market_value', 0))
        
        # MCX exposure (INR converted to USD)
        if 'mcx' in all_positions:
            usd_inr = 83.50  # Update with current rate
            for pos in all_positions['mcx']:
                inr_value = abs(pos.get('market_value', 0))
                exposure['mcx_inr'] += inr_value
                exposure['total_usd'] += (inr_value / usd_inr)
        
        exposure['total_usd'] += exposure['alpaca_usd']
        
        return exposure
    
    def is_market_open(self, market: str) -> bool:
        """Check if specific market is currently open"""
        ist = pytz.timezone('Asia/Kolkata')
        est = pytz.timezone('America/New_York')
        
        now_ist = datetime.now(ist)
        now_est = datetime.now(est)
        
        if market == 'alpaca':
            # US market: 9:30 AM - 4:00 PM EST (8 PM - 2:30 AM IST)
            # For simplicity, Alpaca paper trading is 24/7
            return True
        
        elif market == 'mcx':
            # MCX: 9:00 AM - 11:30 PM IST (Mon-Fri)
            hour = now_ist.hour
            weekday = now_ist.weekday()
            
            # Monday-Friday, 9 AM to 11:30 PM
            if weekday < 5:  # Mon-Fri
                if 9 <= hour < 23:
                    return True
                elif hour == 23 and now_ist.minute < 30:
                    return True
            return False
        
        return False
    
    def get_active_markets(self) -> List[str]:
        """Get list of currently active (open) markets"""
        active = []
        for market in self.brokers.keys():
            if self.is_market_open(market):
                active.append(market)
        return active
    
    def place_order_on_market(self, market: str, **kwargs):
        """Place order on specific market"""
        if market not in self.brokers:
            logger.error(f"❌ {market} broker not connected")
            return None
        
        try:
            order_id = self.brokers[market].place_order(**kwargs)
            if order_id:
                logger.info(f"✅ Order placed on {market}: {order_id}")
            return order_id
        except Exception as e:
            logger.error(f"❌ {market} order failed: {e}")
            return None
    
    def close_all_positions_on_market(self, market: str):
        """Close all positions on specific market"""
        if market not in self.brokers:
            return False
        
        try:
            result = self.brokers[market].close_all_positions()
            logger.info(f"🔒 Closed all {market} positions")
            return result
        except Exception as e:
            logger.error(f"❌ Error closing {market} positions: {e}")
            return False
    
    def shutdown_all(self):
        """Disconnect from all brokers"""
        for name, broker in self.brokers.items():
            try:
                broker.logout()
                logger.info(f"👋 Disconnected from {name}")
            except Exception as e:
                logger.error(f"❌ Error disconnecting {name}: {e}")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 70)
    print("BROKER MANAGER TEST")
    print("=" * 70)
    
    from alpaca_connector import AlpacaConnector
    
    # Initialize manager
    manager = BrokerManager(config={})
    
    # Add Alpaca
    alpaca = AlpacaConnector()
    manager.add_broker('alpaca', alpaca)
    
    # Check active markets
    active = manager.get_active_markets()
    print(f"\n📊 Active markets: {active}")
    
    # Get all positions
    positions = manager.get_all_positions()
    print(f"\n📋 Positions: {positions}")
    
    # Get total exposure
    exposure = manager.get_total_exposure()
    print(f"\n💰 Total exposure: ${exposure['total_usd']:,.2f}")
    
    # Shutdown
    manager.shutdown_all()
