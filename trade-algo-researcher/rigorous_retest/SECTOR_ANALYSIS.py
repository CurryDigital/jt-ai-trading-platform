#!/usr/bin/env python3
"""
SECTOR ANALYSIS — Break down full universe results by market/sector
Find which subsets actually work
"""

import pandas as pd
import numpy as np
import sys
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
from db_backtest_engine import TradeAlgoDB

db = TradeAlgoDB()
conn = db.connect()

TRAIN_START, TRAIN_END = '2021-01-01', '2022-12-31'
TEST_START, TEST_END = '2023-01-01', '2024-12-31'

POSITION_SIZE = 10000

def classify_ticker(ticker):
    """Classify ticker by market"""
    if ticker.endswith('.HK'):
        return 'HK'
    elif ticker.endswith('.SI'):
        return 'SG'
    elif ticker.endswith('.SS') or ticker.endswith('.SZ'):
        return 'CN'
    elif '-USD' in ticker or ticker in ['BTC', 'ETH', 'SOL', 'ADA', 'DOT']:
        return 'CRYPTO'
    elif '=X' in ticker:
        return 'FX'
    elif ticker.endswith('=F'):
        return 'FUTURES'
    else:
        return 'US'

def get_sector(ticker, market):
    """Simple sector classification"""
    ticker_upper = ticker.upper()
    
    if market == 'HK':
        # HK banks
        if ticker_upper in ['0005.HK', '0011.HK', '0238.HK', '0939.HK', '1398.HK', '2388.HK', '3328.HK', '3988.HK']:
            return 'BANKS'
        # HK Tech
        elif ticker_upper in ['0700.HK', '9988.HK', '3690.HK', '1810.HK', '1024.HK', '9999.HK']:
            return 'TECH'
        # HK Property
        elif ticker_upper in ['0001.HK', '0016.HK', '0017.HK', '0113.HK', '1109.HK']:
            return 'PROPERTY'
        else:
            return 'OTHER'
    
    elif market == 'SG':
        # Singapore banks
        if ticker_upper in ['D05.SI', 'O39.SI', 'U11.SI']:
            return 'BANKS'
        # Singapore REITs
        elif 'U' in ticker_upper or ticker_upper in ['A17U.SI', 'C38U.SI', 'ME8U.SI', 'N2IU.SI', 'BUOU.SI']:
            return 'REIT'
        else:
            return 'OTHER'
    
    elif market == 'US':
        # US Tech
        if ticker_upper in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'AMD', 'NFLX', 'CRM', 'ADBE']:
            return 'TECH'
        # US Banks
        elif ticker_upper in ['JPM', 'BAC', 'GS', 'WFC', 'C', 'MS']:
            return 'BANKS'
        # US ETFs
        elif ticker_upper in ['SPY', 'QQQ', 'IWM', 'XLF', 'XLK', 'XLE', 'XLP']:
            return 'ETF'
        else:
            return 'OTHER'
    
    elif market == 'CRYPTO':
        return 'CRYPTO'
    
    else:
        return 'OTHER'

def fetch_data(ticker):
    query = f"""
    SELECT date, close FROM silver.unified_prices
    WHERE ticker = '{ticker}' AND date >= '2021-01-01' ORDER BY date
    """
    df = pd.read_sql(query, conn)
    if len(df) == 0:
        return None
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def fetch_indicators(ticker):
    query = f"""
    SELECT date, rsi_14 FROM gold.technical_indicators_calculated
    WHERE ticker = '{ticker}' AND date >= '2021-01-01' ORDER BY date
    """
    df = pd.read_sql(query, conn)
    if len(df) == 0:
        return None
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def test_ticker(ticker, entry_fn, hold_days):
    """Test single ticker, return metrics"""
    prices = fetch_data(ticker)
    ind = fetch_indicators(ticker)
    
    if prices is None or ind is None:
        return None
    
    df = prices.join(ind, how='inner')
    df['sma20'] = df['close'].rolling(20).mean()
    df['sma50'] = df['close'].rolling(50).mean()
    
    trades = []
    in_position = False
    exit_date = None
    
    for i in range(50, len(df) - hold_days):
        current_date = df.index[i]
        
        if in_position and current_date >= exit_date:
            in_position = False
        
        if not in_position:
            try:
                if entry_fn(df, i):
                    entry_price = df.iloc[i]['close']
                    exit_idx = i + hold_days
                    exit_price = df.iloc[exit_idx]['close']
                    exit_date = df.index[exit_idx]
                    
                    shares = POSITION_SIZE / entry_price
                    gross_pnl = (exit_price - entry_price) * shares
                    cost = POSITION_SIZE * 0.001 * 2
                    net_pnl = gross_pnl - cost
                    pnl_pct = (net_pnl / POSITION_SIZE) * 100
                    
                    trades.append({
                        'entry_date': current_date,
                        'pnl': pnl_pct,
                        'in_test': TEST_START <= current_date <= TEST_END
                    })
                    in_position = True
            except:
                continue
    
    if len(trades) < 5:
        return None
    
    trades_df = pd.DataFrame(trades)
    test_trades = trades_df[trades_df['in_test'] == True]
    
    if len(test_trades) < 3:
        return None
    
    wr = (test_trades['pnl'] > 0).sum() / len(test_trades) * 100
    total_pnl = trades_df['pnl'].sum()
    
    return {
        'ticker': ticker,
        'market': classify_ticker(ticker),
        'sector': get_sector(ticker, classify_ticker(ticker)),
        'test_trades': len(test_trades),
        'test_wr': wr,
        'total_pnl': total_pnl
    }

# Get all tickers
print("Loading tickers...")
ticker_query = """
SELECT ticker FROM silver.unified_prices 
GROUP BY ticker HAVING COUNT(*) >= 500
ORDER BY COUNT(*) DESC
"""
ticker_df = pd.read_sql(ticker_query, conn)
all_tickers = ticker_df['ticker'].tolist()

print(f"Analyzing {len(all_tickers)} tickers by sector...")

# Test best strategy: RSI < 30, 10d
strategy_name = "RSI < 30, 10d"
entry_fn = lambda df, i: df.iloc[i]['rsi_14'] < 30
hold_days = 10

all_results = []

for i, ticker in enumerate(all_tickers):
    if i % 50 == 0:
        print(f"  Progress: {i}/{len(all_tickers)}")
    
    result = test_ticker(ticker, entry_fn, hold_days)
    if result:
        all_results.append(result)

# Convert to DataFrame
results_df = pd.DataFrame(all_results)

print(f"\n{'='*100}")
print(f"SECTOR ANALYSIS: {strategy_name}")
print(f"{'='*100}")
print(f"Total tickers with signals: {len(results_df)}")

# Aggregate by market
print(f"\n{'='*100}")
print("BY MARKET")
print(f"{'='*100}")

market_summary = results_df.groupby('market').agg({
    'ticker': 'count',
    'test_trades': 'sum',
    'test_wr': 'mean',
    'total_pnl': 'sum'
}).round(1)
market_summary.columns = ['Tickers', 'Total_Trades', 'Avg_WR', 'Total_PnL']
market_summary = market_summary.sort_values('Avg_WR', ascending=False)
print(market_summary.to_string())

# Aggregate by sector (within each market)
print(f"\n{'='*100}")
print("BY SECTOR (Top 15)")
print(f"{'='*100}")

# Create market_sector column
results_df['market_sector'] = results_df['market'] + '_' + results_df['sector']

sector_summary = results_df.groupby('market_sector').agg({
    'ticker': 'count',
    'test_trades': 'sum',
    'test_wr': 'mean',
    'total_pnl': 'sum'
}).round(1)
sector_summary.columns = ['Tickers', 'Total_Trades', 'Avg_WR', 'Total_PnL']
sector_summary = sector_summary[sector_summary['Tickers'] >= 3]  # Min 3 tickers
sector_summary = sector_summary.sort_values('Avg_WR', ascending=False)
print(sector_summary.head(15).to_string())

# Top individual tickers
print(f"\n{'='*100}")
print("TOP 20 INDIVIDUAL TICKERS (Test Period)")
print(f"{'='*100}")

top_tickers = results_df[results_df['test_trades'] >= 5].nlargest(20, 'test_wr')
print(top_tickers[['ticker', 'market', 'sector', 'test_trades', 'test_wr', 'total_pnl']].to_string(index=False))

# Bottom performers
print(f"\n{'='*100}")
print("BOTTOM 10 TICKERS (Avoid)")
print(f"{'='*100}")

bottom_tickers = results_df[results_df['test_trades'] >= 5].nsmallest(10, 'test_wr')
print(bottom_tickers[['ticker', 'market', 'sector', 'test_trades', 'test_wr', 'total_pnl']].to_string(index=False))

conn.close()
print(f"\n{'='*100}")
