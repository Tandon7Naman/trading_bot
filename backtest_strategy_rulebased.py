# backtest_strategy_rulebased.py
import pandas as pd
import numpy as np
import logging
import os
import json
from datetime import datetime

logging.basicConfig(
    filename='logs/backtest.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class RuleBasedBacktestEngine:
    """
    Pure technical analysis trading strategy
    No ML models - only proven indicators
    """
    
    def __init__(self, initial_capital=100000, tp_percent=2.5, sl_percent=1.5):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.tp_percent = tp_percent
        self.sl_percent = sl_percent
        self.trades = []
        self.balance_history = [initial_capital]
        
    def calculate_atr(self, df, period=14):
        """Calculate Average True Range for dynamic stop loss"""
        try:
            df['tr'] = np.maximum(
                df['high'] - df['low'],
                np.maximum(
                    abs(df['high'] - df['close'].shift()),
                    abs(df['low'] - df['close'].shift())
                )
            )
            df['atr'] = df['tr'].rolling(window=period).mean()
            return df
        except Exception as e:
            logging.error(f"Error calculating ATR: {str(e)}")
            return df

    def generate_signals(self, df):
        """
        Generate signals using:
        1. Moving Average Crossover (20/50 EMA)
        2. RSI Confirmation (30/70 levels)
        3. MACD for momentum
        """
        try:
            print("[*] Generating rule-based signals...")
            
            # Calculate EMA (more responsive than SMA)
            df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
            df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
            
            # Calculate MACD
            ema12 = df['close'].ewm(span=12, adjust=False).mean()
            ema26 = df['close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = ema12 - ema26
            df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['MACD_Histogram'] = df['MACD'] - df['Signal_Line']
            
            # Calculate ATR for dynamic stops
            df = self.calculate_atr(df, period=14)
            
            df['Signal'] = 0
            
            for i in range(2, len(df)):
                close = df['close'].iloc[i]
                ema20 = df['EMA_20'].iloc[i]
                ema50 = df['EMA_50'].iloc[i]
                rsi = df['RSI'].iloc[i]
                macd_hist = df['MACD_Histogram'].iloc[i]
                macd_hist_prev = df['MACD_Histogram'].iloc[i-1]
                
                # ===== BUY SIGNAL =====
                # Condition 1: EMA20 > EMA50 (uptrend)
                # Condition 2: Price > both EMAs (above moving average)
                # Condition 3: MACD histogram positive and increasing (momentum)
                # Condition 4: RSI < 70 (not overbought, room to rise)
                if (ema20 > ema50 and
                    close > ema20 and
                    macd_hist > 0 and macd_hist > macd_hist_prev and
                    rsi < 70 and rsi > 40):
                    df.loc[i, 'Signal'] = 1
                
                # ===== SELL SIGNAL =====
                # Condition 1: EMA20 < EMA50 (downtrend)
                # Condition 2: Price < both EMAs (below moving average)
                # Condition 3: MACD histogram negative (bearish)
                # Condition 4: RSI > 30 (not oversold, room to fall)
                elif (ema20 < ema50 and
                      close < ema20 and
                      macd_hist < 0 and
                      rsi > 30 and rsi < 60):
                    df.loc[i, 'Signal'] = -1
            
            buy_signals = int((df['Signal'] == 1).sum())
            sell_signals = int((df['Signal'] == -1).sum())
            print(f"[+] Generated signals: {buy_signals} BUY, {sell_signals} SELL")
            logging.info(f"Signals: {buy_signals} BUY, {sell_signals} SELL")
            return df
            
        except Exception as e:
            logging.error(f"Error generating signals: {str(e)}")
            print(f"[-] Error: {str(e)}")
            return df

    def execute_trades(self, df):
        """Execute trades with dynamic stop loss based on ATR"""
        try:
            print("[*] Executing trades...")
            
            in_trade = False
            entry_price = 0
            entry_idx = 0
            entry_type = None
            entry_atr = 0
            units = 100
            
            for i in range(len(df)):
                close = df['close'].iloc[i]
                signal = df['Signal'].iloc[i]
                atr = df['atr'].iloc[i]
                date = df['date'].iloc[i]
                
                # Manage existing trade
                if in_trade:
                    if entry_type == 'LONG':
                        # Dynamic stop loss based on ATR
                        sl = entry_price - (entry_atr * 2)  # 2x ATR
                        tp = entry_price * (1 + self.tp_percent / 100)
                        
                        if close >= tp:
                            pnl = (close - entry_price) * units
                            pnl_pct = ((close - entry_price) / entry_price) * 100
                            reason = 'TP'
                            
                            self.trades.append({
                                'entry_date': df['date'].iloc[entry_idx],
                                'entry_price': round(entry_price, 2),
                                'exit_date': date,
                                'exit_price': round(close, 2),
                                'type': 'LONG',
                                'units': units,
                                'pnl': round(pnl, 2),
                                'pnl_pct': round(pnl_pct, 2),
                                'reason': reason
                            })
                            
                            self.capital += pnl
                            self.balance_history.append(self.capital)
                            in_trade = False
                        
                        elif close <= sl:
                            pnl = (close - entry_price) * units
                            pnl_pct = ((close - entry_price) / entry_price) * 100
                            reason = 'SL'
                            
                            self.trades.append({
                                'entry_date': df['date'].iloc[entry_idx],
                                'entry_price': round(entry_price, 2),
                                'exit_date': date,
                                'exit_price': round(close, 2),
                                'type': 'LONG',
                                'units': units,
                                'pnl': round(pnl, 2),
                                'pnl_pct': round(pnl_pct, 2),
                                'reason': reason
                            })
                            
                            self.capital += pnl
                            self.balance_history.append(self.capital)
                            in_trade = False
                    
                    elif entry_type == 'SHORT':
                        sl = entry_price + (entry_atr * 2)
                        tp = entry_price * (1 - self.tp_percent / 100)
                        
                        if close <= tp:
                            pnl = (entry_price - close) * units
                            pnl_pct = ((entry_price - close) / entry_price) * 100
                            reason = 'TP'
                            
                            self.trades.append({
                                'entry_date': df['date'].iloc[entry_idx],
                                'entry_price': round(entry_price, 2),
                                'exit_date': date,
                                'exit_price': round(close, 2),
                                'type': 'SHORT',
                                'units': units,
                                'pnl': round(pnl, 2),
                                'pnl_pct': round(pnl_pct, 2),
                                'reason': reason
                            })
                            
                            self.capital += pnl
                            self.balance_history.append(self.capital)
                            in_trade = False
                        
                        elif close >= sl:
                            pnl = (entry_price - close) * units
                            pnl_pct = ((entry_price - close) / entry_price) * 100
                            reason = 'SL'
                            
                            self.trades.append({
                                'entry_date': df['date'].iloc[entry_idx],
                                'entry_price': round(entry_price, 2),
                                'exit_date': date,
                                'exit_price': round(close, 2),
                                'type': 'SHORT',
                                'units': units,
                                'pnl': round(pnl, 2),
                                'pnl_pct': round(pnl_pct, 2),
                                'reason': reason
                            })
                            
                            self.capital += pnl
                            self.balance_history.append(self.capital)
                            in_trade = False
                
                # Enter new trade on signal
                if not in_trade and signal != 0:
                    entry_price = close
                    entry_idx = i
                    entry_type = 'LONG' if signal == 1 else 'SHORT'
                    entry_atr = atr if not np.isnan(atr) else 1
                    in_trade = True
            
            print(f"[+] Executed {len(self.trades)} trades")
            logging.info(f"Executed {len(self.trades)} trades")
            return pd.DataFrame(self.trades)
            
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            print(f"[-] Error: {str(e)}")
            return pd.DataFrame()

    def calculate_metrics(self, trades_df):
        """Calculate performance metrics"""
        try:
            if trades_df.empty:
                return {}
            
            winning = trades_df[trades_df['pnl'] > 0]
            losing = trades_df[trades_df['pnl'] < 0]
            
            total = len(trades_df)
            win_rate = (len(winning) / total * 100) if total > 0 else 0
            
            total_pnl = trades_df['pnl'].sum()
            avg_win = winning['pnl'].mean() if len(winning) > 0 else 0
            avg_loss = losing['pnl'].mean() if len(losing) > 0 else 0
            
            profit_factor = abs(winning['pnl'].sum() / losing['pnl'].sum()) if len(losing) > 0 and losing['pnl'].sum() != 0 else 0
            
            final = self.balance_history[-1]
            roi = ((final - self.initial_capital) / self.initial_capital) * 100
            
            return {
                'Total Trades': total,
                'Winning Trades': len(winning),
                'Losing Trades': len(losing),
                'Win Rate (%)': round(win_rate, 2),
                'Avg Win': round(avg_win, 2),
                'Avg Loss': round(avg_loss, 2),
                'Profit Factor': round(profit_factor, 2),
                'Total P&L': round(total_pnl, 2),
                'Initial Capital': self.initial_capital,
                'Final Balance': round(final, 2),
                'ROI (%)': round(roi, 2)
            }
            
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            return {}

def main():
    print("\n" + "="*70)
    print("RULE-BASED BACKTEST (Technical Analysis Only)")
    print("="*70 + "\n")
    
    try:
        df = pd.read_csv('data/gld_data.csv')
        print(f"[+] Loaded {len(df)} records")
    except FileNotFoundError:
        print("[-] GLD data not found")
        return False
    
    engine = RuleBasedBacktestEngine(initial_capital=100000, tp_percent=2.5, sl_percent=1.5)
    
    # Generate signals
    df = engine.generate_signals(df)
    
    # Execute trades
    trades_df = engine.execute_trades(df)
    
    if not trades_df.empty:
        metrics = engine.calculate_metrics(trades_df)
        
        # Save results
        os.makedirs('results', exist_ok=True)
        trades_df.to_csv('results/backtest_trades_rulebased.csv', index=False)
        
        with open('results/backtest_metrics_rulebased.json', 'w') as f:
            json.dump(metrics, f, indent=2)
        
        # Print results
        print("\n" + "="*70)
        print("BACKTEST RESULTS")
        print("="*70)
        for key, value in metrics.items():
            print(f"  {key:.<35} {value}")
        print("="*70 + "\n")
        
        return True
    else:
        print("\n[-] No trades generated")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
