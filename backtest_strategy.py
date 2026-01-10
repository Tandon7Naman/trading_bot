# backtest_strategy.py
import pandas as pd
import numpy as np
import joblib
import logging
import os
import json
from datetime import datetime

logging.basicConfig(
    filename='logs/backtest.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class BacktestEngine:
    def __init__(self, initial_capital=100000, tp_percent=2.0, sl_percent=1.5):
        """Initialize backtest engine"""
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.tp_percent = tp_percent
        self.sl_percent = sl_percent
        self.trades = []
        self.balance_history = [initial_capital]
        
    def generate_predictions(self, df, lookback=30):
        """Generate predictions using trained model"""
        try:
            print("[*] Loading model and generating predictions...")
            
            # Load model and preprocessing objects
            model = joblib.load('models/lstm_model.pkl')
            scaler = joblib.load('models/scaler.pkl')
            feature_cols = joblib.load('models/feature_cols.pkl')
            
            print(f"[+] Model loaded. Features: {feature_cols}")
            
            # Prepare data
            data = df[feature_cols].values.astype(float)
            
            # Fill NaN
            for i in range(data.shape[1]):
                col_mean = np.nanmean(data[:, i])
                data[np.isnan(data[:, i]), i] = col_mean
            
            # Normalize
            scaled_data = scaler.transform(data)
            
            # Generate predictions
            predictions = []
            for i in range(len(scaled_data) - lookback):
                sequence = scaled_data[i:i+lookback].flatten().reshape(1, -1)
                pred = model.predict(sequence)[0]
                # Inverse transform
                pred_full = np.zeros((1, len(feature_cols)))
                pred_full[0, 0] = pred
                pred_inverse = scaler.inverse_transform(pred_full)[0, 0]
                predictions.append(pred_inverse)
            
            # Pad predictions
            predictions = [np.nan] * lookback + predictions
            df['Prediction'] = predictions
            
            valid_preds = len([p for p in predictions if not np.isnan(p)])
            print(f"[+] Generated {valid_preds} predictions")
            logging.info(f"Generated {valid_preds} predictions")
            return df
            
        except Exception as e:
            logging.error(f"Error generating predictions: {str(e)}")
            print(f"[-] Error: {str(e)}")
            return df

    def generate_signals(self, df):
        """Generate trading signals based on RSI and prediction"""
        try:
            print("[*] Generating trading signals...")
            
            df['Signal'] = 0
            
            # Use RSI for signal confirmation
            for i in range(1, len(df)):
                if np.isnan(df['Prediction'].iloc[i]):
                    continue
                
                current_price = df['close'].iloc[i]
                predicted_price = df['Prediction'].iloc[i]
                rsi = df['RSI'].iloc[i]
                sma20 = df['SMA_20'].iloc[i]
                sma50 = df['SMA_50'].iloc[i]
                
                # BUY Signal: Predicted > Current + Price above SMAs + RSI < 70
                if (predicted_price > current_price * 1.01 and  # 1% predicted increase
                    current_price > sma20 and
                    sma20 > sma50 and
                    rsi < 70):
                    df.loc[i, 'Signal'] = 1  # BUY
                
                # SELL Signal: Predicted < Current - Price below SMAs + RSI > 30
                elif (predicted_price < current_price * 0.99 and  # 1% predicted decrease
                      current_price < sma20 and
                      sma20 < sma50 and
                      rsi > 30):
                    df.loc[i, 'Signal'] = -1  # SELL
            
            buy_signals = int((df['Signal'] == 1).sum())
            sell_signals = int((df['Signal'] == -1).sum())
            print(f"[+] Generated signals: {buy_signals} BUY, {sell_signals} SELL")
            logging.info(f"Generated signals: {buy_signals} BUY, {sell_signals} SELL")
            return df
            
        except Exception as e:
            logging.error(f"Error generating signals: {str(e)}")
            print(f"[-] Error: {str(e)}")
            return df

    def execute_trades(self, df):
        """Execute trades with TP/SL management"""
        try:
            print("[*] Executing trades...")
            
            in_trade = False
            entry_price = 0
            entry_idx = 0
            entry_type = None
            trade_units = 100  # Trade 100 units per trade
            
            for i in range(len(df)):
                current_price = df['close'].iloc[i]
                signal = df['Signal'].iloc[i]
                current_date = df['date'].iloc[i]
                
                # Close existing trade if TP/SL hit
                if in_trade:
                    if entry_type == 'LONG':
                        tp_price = entry_price * (1 + self.tp_percent / 100)
                        sl_price = entry_price * (1 - self.sl_percent / 100)
                        
                        if current_price >= tp_price or current_price <= sl_price:
                            pnl = (current_price - entry_price) * trade_units
                            pnl_percent = ((current_price - entry_price) / entry_price) * 100
                            
                            self.trades.append({
                                'entry_date': df['date'].iloc[entry_idx],
                                'entry_price': round(entry_price, 2),
                                'exit_date': current_date,
                                'exit_price': round(current_price, 2),
                                'type': 'LONG',
                                'units': trade_units,
                                'pnl': round(pnl, 2),
                                'pnl_percent': round(pnl_percent, 2),
                                'reason': 'TP' if current_price >= tp_price else 'SL'
                            })
                            
                            self.capital += pnl
                            self.balance_history.append(self.capital)
                            in_trade = False
                    
                    elif entry_type == 'SHORT':
                        tp_price = entry_price * (1 - self.tp_percent / 100)
                        sl_price = entry_price * (1 + self.sl_percent / 100)
                        
                        if current_price <= tp_price or current_price >= sl_price:
                            pnl = (entry_price - current_price) * trade_units
                            pnl_percent = ((entry_price - current_price) / entry_price) * 100
                            
                            self.trades.append({
                                'entry_date': df['date'].iloc[entry_idx],
                                'entry_price': round(entry_price, 2),
                                'exit_date': current_date,
                                'exit_price': round(current_price, 2),
                                'type': 'SHORT',
                                'units': trade_units,
                                'pnl': round(pnl, 2),
                                'pnl_percent': round(pnl_percent, 2),
                                'reason': 'TP' if current_price <= tp_price else 'SL'
                            })
                            
                            self.capital += pnl
                            self.balance_history.append(self.capital)
                            in_trade = False
                
                # Enter new trade on signal
                if not in_trade and signal != 0:
                    entry_price = current_price
                    entry_idx = i
                    entry_type = 'LONG' if signal == 1 else 'SHORT'
                    in_trade = True
            
            logging.info(f"Executed {len(self.trades)} trades")
            print(f"[+] Trade execution complete: {len(self.trades)} trades")
            return pd.DataFrame(self.trades)
            
        except Exception as e:
            logging.error(f"Error executing trades: {str(e)}")
            print(f"[-] Error: {str(e)}")
            return pd.DataFrame()

    def calculate_metrics(self, trades_df):
        """Calculate performance metrics"""
        try:
            if trades_df.empty:
                logging.warning("No trades to analyze")
                return {}
            
            winning_trades = trades_df[trades_df['pnl'] > 0]
            losing_trades = trades_df[trades_df['pnl'] < 0]
            
            total_trades = len(trades_df)
            win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
            
            total_pnl = trades_df['pnl'].sum()
            avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
            avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0
            profit_factor = abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum()) if len(losing_trades) > 0 and losing_trades['pnl'].sum() != 0 else 0
            
            final_balance = self.balance_history[-1]
            roi = ((final_balance - self.initial_capital) / self.initial_capital) * 100
            
            metrics = {
                'Total Trades': total_trades,
                'Winning Trades': len(winning_trades),
                'Losing Trades': len(losing_trades),
                'Win Rate (%)': round(win_rate, 2),
                'Total P&L': round(total_pnl, 2),
                'Avg Win': round(avg_win, 2),
                'Avg Loss': round(avg_loss, 2),
                'Profit Factor': round(profit_factor, 2),
                'Initial Capital': self.initial_capital,
                'Final Balance': round(final_balance, 2),
                'ROI (%)': round(roi, 2)
            }
            
            logging.info(f"Backtest Metrics: {metrics}")
            return metrics
            
        except Exception as e:
            logging.error(f"Error calculating metrics: {str(e)}")
            print(f"[-] Error: {str(e)}")
            return {}

def main():
    print("\n" + "="*70)
    print("BACKTEST STRATEGY")
    print("="*70 + "\n")
    
    try:
        df = pd.read_csv('data/gld_data.csv')
        print(f"[+] Loaded {len(df)} records from GLD data")
    except FileNotFoundError:
        print("[-] GLD data file not found")
        logging.error("GLD data not found")
        return False
    
    # Initialize engine
    engine = BacktestEngine(initial_capital=100000, tp_percent=2.0, sl_percent=1.5)
    
    # Generate predictions
    df = engine.generate_predictions(df, lookback=30)
    
    # Generate signals
    df = engine.generate_signals(df)
    
    # Execute trades
    trades_df = engine.execute_trades(df)
    
    if not trades_df.empty:
        # Calculate metrics
        metrics = engine.calculate_metrics(trades_df)
        
        # Save results
        os.makedirs('results', exist_ok=True)
        trades_df.to_csv('results/backtest_trades.csv', index=False)
        
        with open('results/backtest_metrics.json', 'w') as f:
            json.dump(metrics, f, indent=2)
        
        # Print results
        print("\n" + "="*70)
        print("BACKTEST RESULTS")
        print("="*70)
        for key, value in metrics.items():
            print(f"  {key:.<30} {value}")
        print("="*70 + "\n")
        
        # Save trades CSV
        print("[+] Results saved:")
        print(f"    • trades: results/backtest_trades.csv")
        print(f"    • metrics: results/backtest_metrics.json\n")
        
        return True
    else:
        print("\n[-] No trades generated in backtest")
        print("[*] This could be due to:")
        print("    • Strict signal conditions (RSI/SMA filters)")
        print("    • Model predictions not meeting thresholds")
        print("    • Consider adjusting signal generation logic\n")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
