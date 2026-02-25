#!/usr/bin/env python3
"""
SECTOR ANALYSIS + DECAY CHECK: S001-Candidate Winners
Analyze the 48 GOLDEN tickers by sector and check decay
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
print('SECTOR ANALYSIS + DECAY CHECK: S001-Candidate (RSI < 25)')
print('Analyzing 48 GOLDEN tickers for sector patterns and decay')
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

# Proper industry classification
industry_map = {
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
    
    # HK Transport/Infra
    '0066.HK': 'HK_Transport', '0144.HK': 'HK_Transport', '0316.HK': 'HK_Transport',
    
    # HK Telecom
    '0762.HK': 'HK_Telecom', '0941.HK': 'HK_Telecom', '0788.HK': 'HK_Telecom',
    
    # HK Financial (non-bank)
    '0388.HK': 'HK_Financial', '1359.HK': 'HK_Financial',
    
    # HK Conglomerates
    '0008.HK': 'HK_Conglomerate', '0017.HK': 'HK_Conglomerate',
    
    # HK Energy
    '0883.HK': 'HK_Energy', '0386.HK': 'HK_Energy', '0857.HK': 'HK_Energy',
    '1088.HK': 'HK_Energy', '2688.HK': 'HK_Energy',
    
    # HK Consumer
    '0151.HK': 'HK_Consumer', '1044.HK': 'HK_Consumer', '1929.HK': 'HK_Consumer',
    '2020.HK': 'HK_Consumer', '2319.HK': 'HK_Consumer', '6862.HK': 'HK_Consumer',
    '9633.HK': 'HK_Consumer', '9992.HK': 'HK_Consumer',
    
    # HK Tech
    '0700.HK': 'HK_Tech', '9988.HK': 'HK_Tech', '2382.HK': 'HK_Tech',
    
    # China Banks
    '600036.SS': 'CN_Banks', '601398.SS': 'CN_Banks', '601939.SS': 'CN_Banks',
    '601988.SS': 'CN_Banks', '601288.SS': 'CN_Banks', '601166.SS': 'CN_Banks',
    
    # China Property/Construction
    '601668.SS': 'CN_Property', '601669.SS': 'CN_Property', '601800.SS': 'CN_Property',
    '601888.SS': 'CN_Property', '601186.SS': 'CN_Property',
    
    # China Energy
    '600028.SS': 'CN_Energy', '601088.SS': 'CN_Energy', '601857.SS': 'CN_Energy',
    '601808.SS': 'CN_Energy',
    
    # China Pharma/Healthcare
    '000538.SZ': 'CN_Pharma', '002007.SZ': 'CN_Pharma', '600276.SS': 'CN_Pharma',
    '600436.SS': 'CN_Pharma', '300122.SZ': 'CN_Pharma',
    
    # China Consumer
    '000568.SZ': 'CN_Consumer', '000858.SZ': 'CN_Consumer', '600519.SS': 'CN_Consumer',
    '600809.SS': 'CN_Consumer', '002594.SZ': 'CN_Consumer', '300750.SZ': 'CN_Consumer',
    
    # China Tech
    '002230.SZ': 'CN_Tech', '002415.SZ': 'CN_Tech', '300014.SZ': 'CN_Tech',
    '300760.SZ': 'CN_Tech', '688008.SS': 'CN_Tech', '688012.SS': 'CN_Tech',
    '688126.SS': 'CN_Tech', '688169.SS': 'CN_Tech', '688981.SS': 'CN_Tech',
    
    # US Banks
    'JPM': 'US_Banks', 'BAC': 'US_Banks', 'WFC': 'US_Banks', 'C': 'US_Banks',
    'GS': 'US_Banks', 'MS': 'US_Banks', 'USB': 'US_Banks',
    
    # US Tech
    'AAPL': 'US_Tech', 'MSFT': 'US_Tech', 'GOOGL': 'US_Tech', 'META': 'US_Tech',
    'NVDA': 'US_Tech', 'NFLX': 'US_Tech', 'NOW': 'US_Tech', 'TWLO': 'US_Tech',
    'TDOC': 'US_Tech',
    
    # US Consumer
    'COST': 'US_Consumer', 'WMT': 'US_Consumer', 'HD': 'US_Consumer', 'PG': 'US_Consumer',
    
    # US Industrials
    'BA': 'US_Industrials', 'GE': 'US_Industrials', 'LMT': 'US_Industrials',
    
    # US Energy
    'XOM': 'US_Energy', 'CVX': 'US_Energy',
    
    # US Healthcare
    'JNJ': 'US_Healthcare',
    
    # ETFs
    'SPY': 'US_ETF', 'QQQ': 'US_ETF', 'IWM': 'US_ETF', 'XLF': 'US_ETF',
    'XLK': 'US_ETF', 'XLE': 'US_ETF', 'XLU': 'US_ETF',
    
    # Crypto Proxies
    'COIN': 'Crypto', 'MSTR': 'Crypto',
    
    # Commodities
    'CL=F': 'Commodities', 'SI=F': 'Commodities', 'GC=F': 'Commodities',
    'NG=F': 'Commodities', 'ZW=F': 'Commodities',
    
    # FX
    'EURUSD=X': 'FX', 'GBPUSD=X': 'FX', 'USDJPY=X': 'FX', 'AUDUSD=X': 'FX',
}

# List of 48 GOLDEN tickers from previous test
golden_tickers = [
    '0002.HK', '000538.SZ', '0005.HK', '0027.HK', '0066.HK', '0101.HK', '0083.HK',
    '0001.HK', '0388.HK', '0762.HK', '1024.HK', '0003.HK', '0006.HK', '0008.HK',
    '0011.HK', '0012.HK', '0016.HK', '002142.SZ', '002230.SZ', '002415.SZ',
    '002594.SZ', '0027.HK', '0101.HK', '0144.HK', '0267.HK', '0688.HK', '0762.HK',
    '0883.HK', '0939.HK', '1109.HK', '1113.HK', '1398.HK', '1658.HK', '1929.HK',
    '2020.HK', '2382.HK', '2388.HK', '2688.HK', '3328.HK', '3690.HK', '3868.HK',
    '3968.HK', '3988.HK', '6862.HK', '000651.SZ', '002594.SZ', '0388.HK', '0762.HK'
]

def rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Analyze each golden ticker
print('\nAnalyzing 48 GOLDEN tickers by sector...\n')

results_by_sector = {}
high_decay_tickers = []

for ticker in golden_tickers:
    cursor.execute(f"""
        SELECT date, close::float 
        FROM silver.unified_prices 
        WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-25'
        ORDER BY date
    """)
    data = cursor.fetchall()
    
    if len(data) < 300:
        continue
    
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    df['rsi'] = rsi(df['close'])
    
    # Test period: 2023-2024
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    test_trades = []
    for i in range(14, len(test) - 10):
        if pd.notna(test['rsi'].iloc[i]) and test['rsi'].iloc[i] < 25:
            entry = test['close'].iloc[i]
            exit_p = test['close'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            test_trades.append(ret)
    
    if len(test_trades) < 10:
        continue
    
    test_wr = (pd.Series(test_trades) > 0).mean() * 100
    
    # Validate period: 2025+
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-25')]
    val_trades = []
    for i in range(14, len(validate) - 10):
        if pd.notna(validate['rsi'].iloc[i]) and validate['rsi'].iloc[i] < 25:
            entry = validate['close'].iloc[i]
            exit_p = validate['close'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            val_trades.append(ret)
    
    val_wr = (pd.Series(val_trades) > 0).mean() * 100 if len(val_trades) >= 5 else 0
    
    # Calculate decay
    decay = test_wr - val_wr
    
    # Get sector
    sector = industry_map.get(ticker, 'Other')
    
    if sector not in results_by_sector:
        results_by_sector[sector] = []
    
    results_by_sector[sector].append({
        'ticker': ticker,
        'test_wr': test_wr,
        'val_wr': val_wr,
        'decay': decay,
        'test_n': len(test_trades),
        'val_n': len(val_trades)
    })
    
    if decay > 20:  # High decay flag
        high_decay_tickers.append((ticker, test_wr, val_wr, decay))

conn.close()

# Print sector analysis
print('='*100)
print('SECTOR BREAKDOWN OF GOLDEN TICKERS')
print('='*100)

for sector in sorted(results_by_sector.keys()):
    tickers = results_by_sector[sector]
    avg_test = np.mean([t['test_wr'] for t in tickers])
    avg_val = np.mean([t['val_wr'] for t in tickers])
    avg_decay = np.mean([t['decay'] for t in tickers])
    
    print(f'\n{sector}: {len(tickers)} tickers')
    print(f'  Avg Test: {avg_test:.1f}% | Avg Validate: {avg_val:.1f}% | Avg Decay: {avg_decay:.1f}%')
    print('  Tickers:')
    for t in tickers:
        decay_flag = '⚠️ HIGH DECAY' if t['decay'] > 20 else ''
        print(f"    {t['ticker']}: {t['test_wr']:.1f}% / {t['val_wr']:.1f}% (decay: {t['decay']:.1f}%) {decay_flag}")

# Decay analysis
print('\n' + '='*100)
print('DECAY ANALYSIS')
print('='*100)

print(f'\nHigh Decay Tickers (>20% difference): {len(high_decay_tickers)}')
for ticker, test_wr, val_wr, decay in high_decay_tickers:
    print(f'  {ticker}: Test {test_wr:.1f}% → Val {val_wr:.1f}% (decay: {decay:.1f}%)')

# Sector recommendations
print('\n' + '='*100)
print('SECTOR RECOMMENDATIONS')
print('='*100)

for sector in sorted(results_by_sector.keys()):
    tickers = results_by_sector[sector]
    avg_test = np.mean([t['test_wr'] for t in tickers])
    avg_val = np.mean([t['val_wr'] for t in tickers])
    avg_decay = np.mean([t['decay'] for t in tickers])
    
    if avg_test >= 65 and avg_val >= 55 and avg_decay < 15:
        print(f'\n✅ {sector}: STRONG (Test {avg_test:.1f}%, Val {avg_val:.1f}%, Decay {avg_decay:.1f}%)')
        print(f'   Deploy S001 on this sector')
    elif avg_test >= 60 and avg_decay < 20:
        print(f'\n🟡 {sector}: MODERATE (Test {avg_test:.1f}%, Val {avg_val:.1f}%, Decay {avg_decay:.1f}%)')
        print(f'   Consider with caution')
    else:
        print(f'\n❌ {sector}: WEAK (Test {avg_test:.1f}%, Val {avg_val:.1f}%, Decay {avg_decay:.1f}%)')
        print(f'   Do not deploy')

print('\n' + '='*100)
