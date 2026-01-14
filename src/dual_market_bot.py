"""
Dual-Market Gold Trading Bot
Trades both XAUUSD/GLD (Alpaca) and MCX Gold (Indian broker)
"""
import logging
from datetime import datetime
import time
from broker_manager import BrokerManager
from alpaca_connector import AlpacaConnector
import yfinance as yf

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DualMarketGoldBot:
    """Bot that trades gold on both international and Indian markets"""
    
    def __init__(self):
        self.manager = BrokerManager(config={})
        self.running = False
        
        # Trading parameters
        self.alpaca_symbol = "GLD"  # Gold ETF
        self.mcx_symbol = "GOLD26FEBFUT"  # MCX Gold futures
        
        # Risk limits
        self.max_position_size_usd = 10000  # $10K per market
        self.max_total_exposure_usd = 20000  # $20K total
        
        # Price thresholds
        self.gold_target_price = 2700  # Target price
        self.gold_stop_loss = 2600  # Stop loss
        
    def initialize_brokers(self):
        """Connect to all brokers"""
        logger.info("🔄 Initializing brokers...")
        
        # Add Alpaca (always available for paper trading)
        alpaca = AlpacaConnector()
        if self.manager.add_broker('alpaca', alpaca):
            logger.info("✅ Alpaca ready")
        else:
            logger.error("❌ Alpaca failed")
        
        # Add Indian broker (when available)
        # Uncomment when you have Indian broker credentials:
        # from fyers_connector import FyersConnector
        # fyers = FyersConnector()
        # if self.manager.add_broker('mcx', fyers):
        #     logger.info("✅ MCX ready")
        
        return len(self.manager.brokers) > 0
    
    def get_gold_prices(self):
        """Get current gold prices from multiple sources with fallbacks"""
        prices = {}
        
        # Method 1: Try Gold Futures (GC=F) - Most reliable
        try:
            gold_futures = yf.Ticker("GC=F")
            data = gold_futures.history(period="1d")
            if not data.empty:
                price = data['Close'].iloc[-1]
                if 2000 < price < 3500:  # Sanity check
                    prices['xauusd'] = price
                    logger.info(f"📊 Gold Futures: ${price:.2f}/oz")
                    return prices  # Return immediately if successful
        except Exception as e:
            logger.warning(f"GC=F failed: {e}")
        
        # Method 2: Derive from GLD (always works)
        try:
            gld = yf.Ticker("GLD")
            data = gld.history(period="1d", interval="1m")
            if not data.empty:
                gld_price = data['Close'].iloc[-1]
                prices['gld'] = gld_price
                # Derive gold price from GLD
                # GLD holds approximately 0.095 oz per share
                estimated_gold = gld_price / 0.095
                if 2000 < estimated_gold < 3500:
                    prices['xauusd'] = estimated_gold
                    logger.info(f"📊 GLD: ${gld_price:.2f}/share")
                    logger.info(f"📊 Gold (derived): ${estimated_gold:.2f}/oz")
                    return prices
        except Exception as e:
            logger.error(f"GLD derivation failed: {e}")
        
        # Method 3: Try XAUUSD=X as last resort
        try:
            gold_spot = yf.Ticker("XAUUSD=X")
            data = gold_spot.history(period="5d")  # Wider period
            if not data.empty:
                price = data['Close'].iloc[-1]
                if 2000 < price < 3500:
                    prices['xauusd'] = price
                    logger.info(f"📊 XAUUSD: ${price:.2f}/oz")
                    return prices
        except Exception as e:
            logger.warning(f"XAUUSD=X failed: {e}")
        
        # If all methods fail
        if not prices:
            logger.error("❌ All gold price sources failed!")
        
        return prices
    
    def calculate_arbitrage(self, prices):
        """Check for arbitrage opportunities between markets"""
        if 'xauusd' not in prices or 'gld' not in prices:
            return None
        
        # Expected GLD price based on XAUUSD
        expected_gld = prices['xauusd'] * 0.095  # GLD holds ~0.095 oz
        actual_gld = prices['gld']
        
        difference = ((actual_gld - expected_gld) / expected_gld) * 100
        
        arbitrage = {
            'expected_gld': expected_gld,
            'actual_gld': actual_gld,
            'difference_pct': difference,
            'opportunity': abs(difference) > 1.0  # >1% difference
        }
        
        if arbitrage['opportunity']:
            if difference > 0:
                logger.warning(f"📈 ARBITRAGE: GLD overvalued by {difference:.2f}%")
            else:
                logger.warning(f"📉 ARBITRAGE: GLD undervalued by {abs(difference):.2f}%")
        
        return arbitrage
    
    def generate_signals(self, prices):
        """Generate trading signals for both markets"""
        signals = {'alpaca': None, 'mcx': None}
        
        if 'xauusd' not in prices:
            return signals
        
        gold_price = prices['xauusd']
        
        # Simple trend-following strategy
        if gold_price < 2620:
            signals['alpaca'] = 'BUY'
            signals['mcx'] = 'BUY'
            logger.info("📈 SIGNAL: BUY (Gold undervalued)")
        
        elif gold_price > 2680:
            signals['alpaca'] = 'SELL'
            signals['mcx'] = 'SELL'
            logger.info("📉 SIGNAL: SELL (Gold overvalued)")
        
        else:
            signals['alpaca'] = 'HOLD'
            signals['mcx'] = 'HOLD'
            logger.info("➖ SIGNAL: HOLD (Neutral zone)")
        
        return signals
    
    def execute_trades(self, signals):
        """Execute trades on active markets"""
        for market, signal in signals.items():
            if signal is None or signal == 'HOLD':
                continue
            
            if market not in self.manager.brokers:
                continue
            
            if not self.manager.is_market_open(market):
                logger.info(f"⏰ {market} market closed, skipping")
                continue
            
            # Check current exposure
            exposure = self.manager.get_total_exposure()
            if exposure['total_usd'] > self.max_total_exposure_usd:
                logger.warning("⚠️ Max exposure reached, skipping trade")
                continue
            
            # Execute based on signal
            if signal == 'BUY':
                self.execute_buy(market)
            elif signal == 'SELL':
                self.execute_sell(market)
    
    def execute_buy(self, market):
        """Execute buy order on specific market"""
        if market == 'alpaca':
            # Buy GLD
            order_id = self.manager.place_order_on_market(
                market='alpaca',
                symbol=self.alpaca_symbol,
                quantity=1,
                side='buy'
            )
            if order_id:
                logger.info(f"✅ BUY order placed on Alpaca: {order_id}")
        elif market == 'mcx':
            # Place MCX buy order (implement when MCX connector is ready)
            pass
    
    def execute_sell(self, market):
        """Execute sell order on specific market"""
        if market == 'alpaca':
            # Sell GLD
            order_id = self.manager.place_order_on_market(
                market='alpaca',
                symbol=self.alpaca_symbol,
                quantity=1,
                side='sell'
            )
            if order_id:
                logger.info(f"✅ SELL order placed on Alpaca: {order_id}")
        elif market == 'mcx':
            # Place MCX sell order (implement when MCX connector is ready)
            pass
    
    def run(self):
        """Main bot loop"""
        self.running = True
        logger.info("🚀 Dual-Market Gold Bot started!")
        
        self.initialize_brokers()
        
        while self.running:
            prices = self.get_gold_prices()
            arbitrage = self.calculate_arbitrage(prices)
            signals = self.generate_signals(prices)
            self.execute_trades(signals)
            
            # Sleep between cycles
            time.sleep(60)


if __name__ == "__main__":
    bot = DualMarketGoldBot()
    bot.run()
