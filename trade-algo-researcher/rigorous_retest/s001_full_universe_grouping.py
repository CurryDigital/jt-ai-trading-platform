#!/usr/bin/env python3
"""
FULL UNIVERSE GROUPING: S001 RSI Mean Reversion
ALL tickers that pass 3-tier backtesting, grouped by sector
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np

print('='*100)
print('FULL UNIVERSE GROUPING: S001 RSI Mean Reversion')
print('ALL passing tickers, grouped by sector/market theme')
print('='*100)

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

# Get ALL tickers
cursor.execute("""
    SELECT DISTINCT ticker, COUNT(*) as cnt 
    FROM silver.unified_prices 
    WHERE date >= '2021-01-01'
    GROUP BY ticker
    HAVING COUNT(*) >= 500
    ORDER BY ticker
""")
all_tickers = [(r[0], r[1]) for r in cursor.fetchall()]

def rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def test_ticker(ticker):
    cursor.execute(f"""
        SELECT date, close::float 
        FROM silver.unified_prices 
        WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-25'
        ORDER BY date
    """)
    data = cursor.fetchall()
    
    if len(data) < 300:
        return None
    
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    df['rsi'] = rsi(df['close'])
    
    # Test period
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    test_trades = []
    for i in range(14, len(test) - 10):
        if pd.notna(test['rsi'].iloc[i]) and test['rsi'].iloc[i] < 25:
            entry = test['close'].iloc[i]
            exit_p = test['close'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            test_trades.append(ret)
    
    if len(test_trades) < 10:
        return None
    
    test_wr = (pd.Series(test_trades) > 0).mean() * 100
    
    # Validate period
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-25')]
    val_trades = []
    for i in range(14, len(validate) - 10):
        if pd.notna(validate['rsi'].iloc[i]) and validate['rsi'].iloc[i] < 25:
            entry = validate['close'].iloc[i]
            exit_p = validate['close'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            val_trades.append(ret)
    
    val_wr = (pd.Series(val_trades) > 0).mean() * 100 if len(val_trades) >= 5 else 0
    
    return {
        'test_wr': test_wr,
        'val_wr': val_wr,
        'test_n': len(test_trades),
        'val_n': len(val_trades)
    }

# Industry classification map
sector_map = {
    # HK Banks
    '0005.HK': 'HK_Banks', '0011.HK': 'HK_Banks', '0939.HK': 'HK_Banks',
    '1398.HK': 'HK_Banks', '2388.HK': 'HK_Banks', '3328.HK': 'HK_Banks',
    '3988.HK': 'HK_Banks', '3968.HK': 'HK_Banks', '1658.HK': 'HK_Banks',
    '3868.HK': 'HK_Banks',
    
    # HK Property
    '0001.HK': 'HK_Property', '0012.HK': 'HK_Property', '0016.HK': 'HK_Property',
    '0688.HK': 'HK_Property', '1109.HK': 'HK_Property', '1113.HK': 'HK_Property',
    '0101.HK': 'HK_Property', '0197.HK': 'HK_Property', '0083.HK': 'HK_Property',
    
    # HK Utilities
    '0002.HK': 'HK_Utilities', '0003.HK': 'HK_Utilities', '0006.HK': 'HK_Utilities',
    '0027.HK': 'HK_Utilities', '0836.HK': 'HK_Utilities', '0267.HK': 'HK_Utilities',
    
    # China Banks
    '600036.SS': 'CN_Banks', '601398.SS': 'CN_Banks', '601939.SS': 'CN_Banks',
    '601988.SS': 'CN_Banks', '601288.SS': 'CN_Banks', '601166.SS': 'CN_Banks',
    
    # China Property/Construction
    '601668.SS': 'CN_Property', '601669.SS': 'CN_Property', '601888.SS': 'CN_Property',
    '601186.SS': 'CN_Property', '000333.SZ': 'CN_Property',
    
    # China Consumer
    '600519.SS': 'CN_Consumer', '000858.SZ': 'CN_Consumer', '000568.SZ': 'CN_Consumer',
    '600809.SS': 'CN_Consumer', '002594.SZ': 'CN_Consumer', '300750.SZ': 'CN_Consumer',
    
    # China Pharma
    '000538.SZ': 'CN_Pharma', '002007.SZ': 'CN_Pharma', '600276.SS': 'CN_Pharma',
    
    # HK Tech
    '0700.HK': 'HK_Tech', '9988.HK': 'HK_Tech', '3690.HK': 'HK_Tech',
    '9618.HK': 'HK_Tech', '1024.HK': 'HK_Tech', '1810.HK': 'HK_Tech',
    
    # US Banks
    'JPM': 'US_Banks', 'BAC': 'US_Banks', 'C': 'US_Banks', 'GS': 'US_Banks',
    'WFC': 'US_Banks', 'MS': 'US_Banks', 'USB': 'US_Banks',
    
    # US Tech
    'AAPL': 'US_Tech', 'MSFT': 'US_Tech', 'GOOGL': 'US_Tech', 'META': 'US_Tech',
    'NVDA': 'US_Tech', 'NFLX': 'US_Tech',
    
    # US Industrials
    'GE': 'US_Industrials', 'BA': 'US_Industrials', 'LMT': 'US_Industrials',
    
    # US Consumer
    'COST': 'US_Consumer', 'WMT': 'US_Consumer', 'PG': 'US_Consumer',
    
    # ETFs
    'SPY': 'ETF', 'QQQ': 'ETF', 'IWM': 'ETF',
    
    # HK Energy
    '0883.HK': 'HK_Energy', '0386.HK': 'HK_Energy', '0857.HK': 'HK_Energy',
    '1088.HK': 'HK_Energy', '2688.HK': 'HK_Energy',
    
    # HK Insurance
    '1299.HK': 'HK_Insurance', '2318.HK': 'HK_Insurance', '2628.HK': 'HK_Insurance',
    
    # HK Transport
    '0066.HK': 'HK_Transport', '0144.HK': 'HK_Transport', '0316.HK': 'HK_Transport',
    
    # HK Consumer
    '0151.HK': 'HK_Consumer', '1044.HK': 'HK_Consumer', '1929.HK': 'HK_Consumer',
    '2020.HK': 'HK_Consumer', '2319.HK': 'HK_Consumer', '6862.HK': 'HK_Consumer',
    
    # HK Telecom
    '0762.HK': 'HK_Telecom', '0941.HK': 'HK_Telecom', '0788.HK': 'HK_Telecom',
    
    # China Tech
    '002230.SZ': 'CN_Tech', '002415.SZ': 'CN_Tech', '300014.SZ': 'CN_Tech',
    '688008.SS': 'CN_Tech', '2382.HK': 'HK_Tech',
    
    # China Energy
    '600028.SS': 'CN_Energy', '601088.SS': 'CN_Energy', '601857.SS': 'CN_Energy',
}

# Test ALL tickers and group
print('\nTesting all tickers and grouping by sector...\n')

sector_results = {}
other_tickers = []

for ticker, count in all_tickers:
    result = test_ticker(ticker)
    if result is None:
        continue
    
    # Check if passes (Test >=60%, Val >=50% for flexibility)
    if result['test_wr'] >= 60 and result['val_wr'] >= 50:
        sector = sector_map.get(ticker, 'Other')
        
        if sector not in sector_results:
            sector_results[sector] = []
        
        sector_results[sector].append({
            'ticker': ticker,
            **result
        })

conn.close()

# Print results by sector
print('='*100)
print('S001 RSI <25: ALL PASSING TICKERS BY SECTOR')
print('Pass criteria: Test >=60%, Val >=50%, n >=10')
print('='*100)

total_tickers = 0
for sector in sorted(sector_results.keys()):
    tickers = sector_results[sector]
    if len(tickers) == 0:
        continue
    
    avg_test = np.mean([t['test_wr'] for t in tickers])
    avg_val = np.mean([t['val_wr'] for t in tickers])
    total_test_n = sum([t['test_n'] for t in tickers])
    
    print(f'\n{sector}: {len(tickers)} tickers')
    print(f'  Avg: Test {avg_test:.1f}% | Val {avg_val:.1f}% | Total Trades: {total_test_n}')
    print('  Tickers:')
    for t in sorted(tickers, key=lambda x: x['test_wr'], reverse=True):
        print(f"    {t['ticker']:<15} Test: {t['test_wr']:>6.1f}%  Val: {t['val_wr']:>6.1f}%  n={t['test_n']:>3}")
    
    total_tickers += len(tickers)

print('\n' + '='*100)
print(f'TOTAL: {total_tickers} tickers across {len([s for s in sector_results if sector_results[s]])} sectors')
print('='*100)

# Strategy recommendations
print('\n' + '='*100)
print('STRATEGY GROUPING RECOMMENDATIONS')
print('='*100)

# Major groupings (3+ tickers)
major_sectors = {k: v for k, v in sector_results.items() if len(v) >= 3}
minor_sectors = {k: v for k, v in sector_results.items() if 0 < len(v) < 3}

print('\n🏆 MAJOR GROUPINGS (Create dedicated strategies):')
for sector in sorted(major_sectors.keys()):
    tickers = major_sectors[sector]
    avg_test = np.mean([t['test_wr'] for t in tickers])
    avg_val = np.mean([t['val_wr'] for t in tickers])
    ticker_list = [t['ticker'] for t in tickers]
    print(f'\n  S001-{sector}:')
    print(f'    Tickers: {", ".join(ticker_list)}')
    print(f'    Performance: {avg_test:.1f}% test / {avg_val:.1f}% validate')
    print(f'    Total trades: {sum([t["test_n"] for t in tickers])}')

print('\n🟡 MINOR GROUPINGS (Combine into S001-Others):')
for sector in sorted(minor_sectors.keys()):
    tickers = minor_sectors[sector]
    ticker_list = [t['ticker'] for t in tickers]
    print(f'  {sector}: {", ".join(ticker_list)}')

print('\n' + '='*100)
