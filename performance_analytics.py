# performance_analytics.py
"""
Performance Analytics Module
- Calculates comprehensive trading statistics
- Generates HTML performance reports
- Tracks advanced metrics
"""

import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime
import os

logging.basicConfig(
    filename='logs/analytics.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class PerformanceAnalytics:
    def __init__(self, trades_file='results/backtest_trades_rulebased.csv'):
        """Initialize with trades data"""
        try:
            self.trades_df = pd.read_csv(trades_file) if os.path.exists(trades_file) else pd.DataFrame()
            logging.info(f"Loaded {len(self.trades_df)} trades from {trades_file}")
        except Exception as e:
            logging.error(f"Error loading trades: {str(e)}")
            self.trades_df = pd.DataFrame()

    def calculate_all_metrics(self):
        """Calculate comprehensive performance metrics"""
        try:
            if self.trades_df.empty:
                logging.warning("No trades to analyze")
                return {}
            
            metrics = {}
            
            # Basic metrics
            metrics['Total Trades'] = len(self.trades_df)
            winning = len(self.trades_df[self.trades_df['pnl'] > 0])
            losing = len(self.trades_df[self.trades_df['pnl'] < 0])
            metrics['Winning Trades'] = winning
            metrics['Losing Trades'] = losing
            
            # Win rate
            metrics['Win Rate (%)'] = round((winning / len(self.trades_df) * 100) if len(self.trades_df) > 0 else 0, 2)
            
            # Profit metrics
            metrics['Total P&L'] = round(self.trades_df['pnl'].sum(), 2)
            metrics['Avg Win'] = round(self.trades_df[self.trades_df['pnl'] > 0]['pnl'].mean() if winning > 0 else 0, 2)
            metrics['Avg Loss'] = round(self.trades_df[self.trades_df['pnl'] < 0]['pnl'].mean() if losing > 0 else 0, 2)
            metrics['Largest Win'] = round(self.trades_df['pnl'].max(), 2)
            metrics['Largest Loss'] = round(self.trades_df['pnl'].min(), 2)
            
            # Profit factor
            winning_sum = self.trades_df[self.trades_df['pnl'] > 0]['pnl'].sum()
            losing_sum = abs(self.trades_df[self.trades_df['pnl'] < 0]['pnl'].sum())
            metrics['Profit Factor'] = round(winning_sum / losing_sum if losing_sum > 0 else 0, 2)
            
            # Expectancy
            metrics['Expectancy'] = round(metrics['Total P&L'] / len(self.trades_df) if len(self.trades_df) > 0 else 0, 2)
            
            # Consecutive streaks
            metrics['Max Win Streak'] = self._get_max_streak(True)
            metrics['Max Loss Streak'] = self._get_max_streak(False)
            
            # Recovery factor
            metrics['Recovery Factor'] = round(metrics['Total P&L'] / abs(metrics['Largest Loss']) if metrics['Largest Loss'] < 0 else 0, 2)
            
            logging.info(f"Calculated metrics: {metrics}")
            return metrics
            
        except Exception as e:
            logging.error(f"Error calculating metrics: {str(e)}")
            return {}

    def _get_max_streak(self, winning=True):
        """Get maximum consecutive wins or losses"""
        try:
            if self.trades_df.empty:
                return 0
            
            pnl_array = self.trades_df['pnl'].values
            is_winning = pnl_array > 0
            
            max_streak = 0
            current_streak = 0
            
            for w in is_winning:
                if (w and winning) or (not w and not winning):
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    current_streak = 0
            
            return max_streak
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            return 0

    def generate_daily_summary(self):
        """Generate today's trading summary"""
        try:
            if self.trades_df.empty:
                return None
            
            if 'entry_date' in self.trades_df.columns:
                self.trades_df['entry_date'] = pd.to_datetime(self.trades_df['entry_date'])
                today = pd.Timestamp.now().date()
                today_trades = self.trades_df[self.trades_df['entry_date'].dt.date == today]
            else:
                today_trades = self.trades_df.tail(5)  # Last 5 trades
            
            if today_trades.empty:
                return None
            
            summary = {
                'Date': datetime.now().strftime('%Y-%m-%d'),
                'Total Trades': len(today_trades),
                'Winning': len(today_trades[today_trades['pnl'] > 0]),
                'Losing': len(today_trades[today_trades['pnl'] < 0]),
                'Total P&L': round(today_trades['pnl'].sum(), 2),
                'Win Rate (%)': round((len(today_trades[today_trades['pnl'] > 0]) / len(today_trades) * 100), 2)
            }
            
            logging.info(f"Daily summary: {summary}")
            return summary
            
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            return None

    def generate_html_report(self, output_file='reports/performance_report.html'):
        """Generate beautiful HTML performance report"""
        try:
            metrics = self.calculate_all_metrics()
            
            if not metrics:
                logging.warning("No metrics to report")
                return False
            
            # Create HTML
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Gold Trading Bot - Performance Report</title>
                <style>
                    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                    body {{ 
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 20px;
                        min-height: 100vh;
                    }}
                    .container {{ 
                        max-width: 1000px; 
                        margin: 0 auto; 
                        background: white; 
                        border-radius: 12px; 
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                        overflow: hidden;
                    }}
                    .header {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 40px;
                        text-align: center;
                    }}
                    .header h1 {{ font-size: 32px; margin-bottom: 10px; }}
                    .header p {{ font-size: 14px; opacity: 0.9; }}
                    .content {{ padding: 40px; }}
                    .metrics-grid {{
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 20px;
                        margin-bottom: 40px;
                    }}
                    .metric-card {{
                        background: #f8f9fa;
                        padding: 20px;
                        border-radius: 8px;
                        border-left: 4px solid #667eea;
                        transition: transform 0.3s, box-shadow 0.3s;
                    }}
                    .metric-card:hover {{ transform: translateY(-5px); box-shadow: 0 10px 25px rgba(0,0,0,0.1); }}
                    .metric-label {{ color: #666; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }}
                    .metric-value {{ color: #333; font-size: 28px; font-weight: bold; margin-top: 10px; }}
                    .positive {{ color: #27ae60; }}
                    .negative {{ color: #e74c3c; }}
                    .table-section {{
                        margin-top: 40px;
                        padding-top: 40px;
                        border-top: 2px solid #eee;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-top: 20px;
                    }}
                    th {{
                        background: #667eea;
                        color: white;
                        padding: 12px;
                        text-align: left;
                        font-weight: 600;
                    }}
                    td {{
                        padding: 12px;
                        border-bottom: 1px solid #eee;
                    }}
                    tr:hover {{ background: #f8f9fa; }}
                    .footer {{
                        text-align: center;
                        padding: 20px;
                        background: #f8f9fa;
                        color: #666;
                        font-size: 12px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                                                <h1>Gold Trading Bot Performance Report</h1>
                        <p>Performance Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                    
                    <div class="content">
                        <div class="metrics-grid">
            """
            
            # Add metric cards
            for key, value in metrics.items():
                if key == 'Total P&L':
                    color_class = 'positive' if value > 0 else 'negative'
                    html_content += f"""
                    <div class="metric-card">
                        <div class="metric-label">{key}</div>
                        <div class="metric-value {color_class}">${value:,.2f}</div>
                    </div>
                    """
                elif key in ['Win Rate (%)', 'Profit Factor', 'Recovery Factor']:
                    html_content += f"""
                    <div class="metric-card">
                        <div class="metric-label">{key}</div>
                        <div class="metric-value">{value}</div>
                    </div>
                    """
                else:
                    html_content += f"""
                    <div class="metric-card">
                        <div class="metric-label">{key}</div>
                        <div class="metric-value">{value}</div>
                    </div>
                    """
            
            # Add trades table
            html_content += """
                        </div>
                        
                        <div class="table-section">
                            <h2>Recent Trades</h2>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Entry Date</th>
                                        <th>Type</th>
                                        <th>Entry Price</th>
                                        <th>Exit Price</th>
                                        <th>P&L</th>
                                        <th>P&L %</th>
                                    </tr>
                                </thead>
                                <tbody>
            """
            
            # Add last 10 trades
            recent_trades = self.trades_df.tail(10)
            for _, trade in recent_trades.iterrows():
                color = 'positive' if trade['pnl'] > 0 else 'negative'
                html_content += f"""
                                    <tr>
                                        <td>{trade.get('entry_date', 'N/A')}</td>
                                        <td>{trade.get('type', 'N/A')}</td>
                                        <td>${trade.get('entry_price', 0):.2f}</td>
                                        <td>${trade.get('exit_price', 0):.2f}</td>
                                        <td class="{color}">${trade.get('pnl', 0):.2f}</td>
                                        <td class="{color}">{trade.get('pnl_pct', 0):.2f}%</td>
                                    </tr>
                """
            
            html_content += """
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p>Generated by Gold Trading Bot | © 2026 | All Rights Reserved</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Save file
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(html_content)
            
            logging.info(f"HTML report generated: {output_file}")
            print(f"[+] HTML report generated: {output_file}")
            return True
            
        except Exception as e:
            logging.error(f"Error generating HTML report: {str(e)}")
            return False

def main():
    print("\n" + "="*70)
    print("PERFORMANCE ANALYTICS")
    print("="*70 + "\n")
    
    analytics = PerformanceAnalytics()
    
    # Calculate metrics
    metrics = analytics.calculate_all_metrics()
    print("[+] Calculated metrics:")
    for key, value in metrics.items():
        print(f"    {key}: {value}")
    
    # Generate daily summary
    summary = analytics.generate_daily_summary()
    if summary:
        print("\n[+] Daily Summary:")
        for key, value in summary.items():
            print(f"    {key}: {value}")
    
    # Generate HTML report
    if analytics.generate_html_report():
        print("\n[+] HTML report generated successfully")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()

