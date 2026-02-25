#!/usr/bin/env python3
"""
Test 28 Hypotheses with Available Data
Uses silver.historical_stock_data and gold schema
NO PROXIES - Only data that exists in RDS
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')

from db_backtest_engine import TradeAlgoDB, BacktestStorage
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json


def calculate_rsi(prices, window=14):
    """Calculate RSI"""
    deltas = prices.diff()
    gain = (deltas.where(deltas > 0, 0)).rolling(window=window).mean()
    loss = (-deltas.where(deltas < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calculate_bollinger(prices, window=20, num_std=2):
    """Calculate Bollinger Bands"""
    sma = prices.rolling(window=window).mean()
    std = prices.rolling(window=window).std()
    upper = sma + (std * num_std)
    lower = sma - (std * num_std)
    bandwidth = (upper - lower) / sma
    return upper, sma, lower, bandwidth


def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD"""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


class AvailableDataBacktester:
    """Backtest using only available RDS data"""
    
    def __init__(self):
        self.db = TradeAlgoDB()
        self.db.connect()
        self.storage = BacktestStorage(self.db)
        
    def get_price_data(self, tickers, start_date, end_date):
        """Get OHLCV from silver schema"""
        ticker_list = "','".join(tickers)
        sql = f"""
        SELECT date, ticker, open, high, low, close, volume
        FROM silver.historical_stock_data
        WHERE ticker IN ('{ticker_list}')
        AND date BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY ticker, date
        """
        return self.db.query(sql)
    
    def save_results(self, hypothesis_name, results, parameters, start_date, end_date):
        """Save backtest results"""
        import psycopg2
        
        # Convert numpy types to Python types
        def convert(val):
            if hasattr(val, 'item'):
                return val.item()
            return val
        
        # Manual insert to avoid numpy issues
        conn = psycopg2.connect(
            host='openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com',
            port=5432, database='aitrading', user='openclaw_user',
            password=self.db.get_auth_token(), sslmode='require'
        )
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO openclaw_researcher.backtest_results 
        (hypothesis_name, start_date, end_date, total_trades, win_rate_pct,
         sharpe_ratio, max_drawdown_pct, status, parameters, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """, (
            hypothesis_name, start_date, end_date,
            int(convert(results.get('total_trades', 0))),
            float(convert(results.get('win_rate', 0))),
            float(convert(results.get('sharpe', 0))),
            float(convert(results.get('max_drawdown', 0))),
            'completed',
            json.dumps(parameters),
            f'Backtest completed {datetime.now()}'
        ))
        
        backtest_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        # Update hypothesis status
        sharpe = float(convert(results.get('sharpe', 0)))
        status = 'validated' if sharpe >= 1.0 else 'testing'
        
        conn = psycopg2.connect(
            host='openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com',
            port=5432, database='aitrading', user='openclaw_user',
            password=self.db.get_auth_token(), sslmode='require'
        )
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE openclaw_researcher.hypothesis_registry
        SET backtest_count = backtest_count + 1,
            best_sharpe = GREATEST(COALESCE(best_sharpe, 0), %s),
            last_backtest_date = CURRENT_DATE,
            current_status = %s
        WHERE hypothesis_name = %s
        """, (sharpe, status, hypothesis_name))
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"  Saved: ID {backtest_id}, Status: {status.upper()}")
        return backtest_id, status
    
    def close(self):
        self.db.close()


def test_bollinger_squeeze():
    """Test Bollinger Squeeze Breakout"""
    print("\n" + "="*70)
    print("TEST 1: Bollinger Squeeze Breakout")
    print("="*70)
    
    bt = AvailableDataBacktester()
    
    tickers = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'TSLA',
               'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'BAC', 'ABBV',
               'PFE', 'KO', 'PEP', 'COST', 'WMT', 'ADBE', 'CRM', 'ACN']
    
    prices = bt.get_price_data(tickers, '2021-03-01', '2024-12-31')
    
    trades = []
    for ticker in tickers:
        data = prices[prices['ticker'] == ticker].sort_values('date').copy()
        if len(data) < 50:
            continue
        
        # Calculate Bollinger Bands
        data['bb_upper'], data['bb_mid'], data['bb_lower'], data['bb_width'] = \
            calculate_bollinger(data['close'])
        data['rsi'] = calculate_rsi(data['close'])
        data = data.dropna()
        
        position = None
        entry_price = None
        entry_date = None
        squeeze_triggered = False
        
        for i in range(20, len(data)):
            row = data.iloc[i]
            prev_row = data.iloc[i-1]
            
            # Squeeze detection: width < 5th percentile of recent
            recent_width = data.iloc[i-20:i]['bb_width']
            width_pct = (row['bb_width'] - recent_width.min()) / (recent_width.max() - recent_width.min() + 0.0001)
            
            if position is None:
                # Entry: Squeeze + Breakout above upper band + RSI confirmation
                if width_pct < 0.05 and row['close'] > row['bb_upper'] and row['rsi'] > 50:
                    position = 'LONG'
                    entry_price = row['close']
                    entry_date = row['date']
                    squeeze_triggered = True
            else:
                # Exit: Hold for 5 days or RSI > 70 or price < mid band
                hold_days = i - data[data['date'] == entry_date].index[0] if len(data[data['date'] == entry_date]) > 0 else 0
                pnl = (row['close'] - entry_price) / entry_price
                
                if hold_days >= 5 or row['rsi'] > 70 or row['close'] < row['bb_mid']:
                    trades.append({
                        'ticker': ticker,
                        'entry_date': entry_date,
                        'exit_date': row['date'],
                        'pnl_pct': pnl * 100,
                        'hold_days': hold_days
                    })
                    position = None
    
    bt.close()
    
    if len(trades) == 0:
        print("No trades generated")
        return None
    
    trades_df = pd.DataFrame(trades)
    returns = trades_df['pnl_pct']
    sharpe = returns.mean() / returns.std() * np.sqrt(252 / trades_df['hold_days'].mean()) if returns.std() > 0 else 0
    
    results = {
        'total_trades': len(trades_df),
        'win_rate': (returns > 0).mean() * 100,
        'avg_return': returns.mean(),
        'sharpe': sharpe,
        'max_drawdown': returns.min()
    }
    
    print(f"Results: {results['total_trades']} trades, {results['win_rate']:.1f}% win, Sharpe {results['sharpe']:.2f}")
    
    bt = AvailableDataBacktester()
    backtest_id, status = bt.save_results('Bollinger Squeeze', results, 
                                          {'window': 20, 'squeeze_threshold': 0.05},
                                          '2021-03-01', '2024-12-31')
    bt.close()
    
    return results


def test_engulfing_pattern():
    """Test Candlestick Engulfing Pattern"""
    print("\n" + "="*70)
    print("TEST 2: Engulfing Pattern")
    print("="*70)
    
    bt = AvailableDataBacktester()
    
    tickers = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'TSLA',
               'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'BAC', 'ABBV']
    
    prices = bt.get_price_data(tickers, '2021-01-01', '2024-12-31')
    
    trades = []
    for ticker in tickers:
        data = prices[prices['ticker'] == ticker].sort_values('date').copy()
        if len(data) < 10:
            continue
        
        # Calculate candlestick properties
        data['body'] = abs(data['close'] - data['open'])
        data['upper_shadow'] = data['high'] - data[['open', 'close']].max(axis=1)
        data['lower_shadow'] = data[['open', 'close']].min(axis=1) - data['low']
        data['range'] = data['high'] - data['low']
        data['rsi'] = calculate_rsi(data['close'])
        data = data.dropna()
        
        for i in range(1, len(data)-5):
            prev = data.iloc[i-1]
            curr = data.iloc[i]
            
            # Bullish Engulfing: Prev red, curr green, curr body > prev body
            prev_red = prev['close'] < prev['open']
            curr_green = curr['close'] > curr['open']
            engulfs = curr['body'] > prev['body']
            above_support = curr['rsi'] < 50  # Not overbought
            
            if prev_red and curr_green and engulfs and above_support:
                entry_price = curr['close']
                exit_price = data.iloc[i+5]['close']  # Hold 5 days
                pnl = (exit_price - entry_price) / entry_price * 100
                
                trades.append({
                    'ticker': ticker,
                    'entry_date': curr['date'],
                    'pnl_pct': pnl
                })
    
    bt.close()
    
    if len(trades) == 0:
        print("No trades generated")
        return None
    
    trades_df = pd.DataFrame(trades)
    returns = trades_df['pnl_pct']
    sharpe = returns.mean() / returns.std() * np.sqrt(52) if returns.std() > 0 else 0
    
    results = {
        'total_trades': len(trades_df),
        'win_rate': (returns > 0).mean() * 100,
        'avg_return': returns.mean(),
        'sharpe': sharpe,
        'max_drawdown': returns.min()
    }
    
    print(f"Results: {results['total_trades']} trades, {results['win_rate']:.1f}% win, Sharpe {results['sharpe']:.2f}")
    
    bt = AvailableDataBacktester()
    backtest_id, status = bt.save_results('Engulfing Pattern', results,
                                          {'pattern': 'bullish_engulfing', 'hold_days': 5},
                                          '2021-01-01', '2024-12-31')
    bt.close()
    
    return results


def test_mean_reversion_3day():
    """Test 3-Day Reversal"""
    print("\n" + "="*70)
    print("TEST 3: 3-Day Reversal")
    print("="*70)
    
    bt = AvailableDataBacktester()
    
    tickers = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'TSLA',
               'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'BAC', 'ABBV',
               'PFE', 'KO', 'PEP', 'COST', 'WMT', 'ADBE']
    
    prices = bt.get_price_data(tickers, '2021-01-01', '2024-12-31')
    
    trades = []
    for ticker in tickers:
        data = prices[prices['ticker'] == ticker].sort_values('date').copy()
        data['returns'] = data['close'].pct_change()
        data = data.dropna()
        
        for i in range(3, len(data)-5):
            # 3 consecutive down days
            d1 = data.iloc[i-3]['returns'] < 0
            d2 = data.iloc[i-2]['returns'] < 0
            d3 = data.iloc[i-1]['returns'] < 0
            
            # Total decline > 5%
            total_decline = (data.iloc[i-1]['close'] / data.iloc[i-3]['close'] - 1) < -0.05
            
            if d1 and d2 and d3 and total_decline:
                entry_price = data.iloc[i]['open']
                exit_price = data.iloc[i+5]['close']
                pnl = (exit_price - entry_price) / entry_price * 100
                
                trades.append({
                    'ticker': ticker,
                    'entry_date': data.iloc[i]['date'],
                    'pnl_pct': pnl
                })
    
    bt.close()
    
    if len(trades) == 0:
        print("No trades generated")
        return None
    
    trades_df = pd.DataFrame(trades)
    returns = trades_df['pnl_pct']
    sharpe = returns.mean() / returns.std() * np.sqrt(52) if returns.std() > 0 else 0
    
    results = {
        'total_trades': len(trades_df),
        'win_rate': (returns > 0).mean() * 100,
        'avg_return': returns.mean(),
        'sharpe': sharpe,
        'max_drawdown': returns.min()
    }
    
    print(f"Results: {results['total_trades']} trades, {results['win_rate']:.1f}% win, Sharpe {results['sharpe']:.2f}")
    
    bt = AvailableDataBacktester()
    backtest_id, status = bt.save_results('3-Day Reversal', results,
                                          {'consecutive_days': 3, 'decline_threshold': 0.05},
                                          '2021-01-01', '2024-12-31')
    bt.close()
    
    return results


def show_summary():
    """Show backtest summary"""
    print("\n" + "="*70)
    print("BACKTEST SUMMARY - Tests with Available Data")
    print("="*70)
    
    import boto3
    import psycopg2
    
    session = boto3.Session(region_name='ap-southeast-1')
    rds = session.client('rds')
    token = rds.generate_db_auth_token(
        DBHostname='openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com',
        Port=5432, DBUsername='openclaw_user', Region='ap-southeast-1'
    )
    
    conn = psycopg2.connect(
        host='openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com',
        port=5432, database='aitrading', user='openclaw_user',
        password=token, sslmode='require'
    )
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT hypothesis_name, total_trades, win_rate_pct, sharpe_ratio, max_drawdown_pct
    FROM openclaw_researcher.backtest_results
    WHERE status = 'completed'
    ORDER BY sharpe_ratio DESC NULLS LAST
    """)
    
    print("\nCompleted Backtests (Ranked by Sharpe):")
    print("-"*70)
    for row in cursor.fetchall():
        sharpe_str = f"{row[3]:.2f}" if row[3] else "N/A"
        win_str = f"{row[2]:.1f}" if row[2] else "N/A"
        status_icon = "✅" if row[3] and row[3] >= 1.0 else "🧪"
        print(f"{status_icon} {row[0][:35]:35} | Trades: {row[1]:4} | Win: {win_str:5}% | Sharpe: {sharpe_str:5}")
    
    cursor.execute("""
    SELECT current_status, COUNT(*), ROUND(AVG(best_sharpe), 2)
    FROM openclaw_researcher.hypothesis_registry
    GROUP BY current_status
    ORDER BY current_status
    """)
    
    print("\n" + "="*70)
    print("HYPOTHESIS STATUS SUMMARY")
    print("="*70)
    for row in cursor.fetchall():
        icon = {"idea": "💡", "testing": "🧪", "validated": "✅", "promoted": "🏆", "rejected": "❌"}.get(row[0], "⏳")
        best_sharpe = f"(avg best: {row[2]})" if row[2] else ""
        print(f"{icon} {row[0].upper():12}: {row[1]:3} hypotheses {best_sharpe}")
    
    cursor.close()
    conn.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', choices=['bollinger', 'engulfing', '3day', 'all'], default='all')
    args = parser.parse_args()
    
    if args.test in ['bollinger', 'all']:
        test_bollinger_squeeze()
    
    if args.test in ['engulfing', 'all']:
        test_engulfing_pattern()
    
    if args.test in ['3day', 'all']:
        test_mean_reversion_3day()
    
    show_summary()
    
    print("\n" + "="*70)
    print("Batch testing complete!")
    print("="*70)
