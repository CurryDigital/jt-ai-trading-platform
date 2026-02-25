#!/usr/bin/env python3
"""
CONTINUOUS TESTING: S002-S012 on FULL UNIVERSE (400+ tickers)
Sector analysis for each strategy
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np

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

def rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def classify_sector(ticker):
    if ticker.endswith('.HK'):
        code = ticker.split('.')[0]
        if code in ['0001', '0002', '0003', '0016'] or code.startswith('11'):
            return 'HK_Property'
        elif code in ['0700', '9999', '9618', '9988', '3690', '1024', '1810']:
            return 'HK_Tech'
        elif code in ['1398', '0939', '3988', '2388', '3328', '0005']:
            return 'HK_Banks'
        elif code.startswith('6') or code in ['2628', '2318', '2319']:
            return 'HK_Finance_Insurance'
        elif code in ['0883', '0386', '0857', '1088']:
            return 'HK_Energy'
        else:
            return 'HK_Other'
    elif ticker.endswith('.SZ') or ticker.endswith('.SS'):
        return 'China_A_Shares'
    elif ticker.endswith('.SI'):
        return 'Singapore'
    elif ticker in ['BTC-USD', 'ETH-USD', 'SOL-USD', 'ADA-USD', 'DOT-USD', 'AVAX-USD', 'LINK-USD', 'XRP-USD', 'DOGE-USD', 'LTC-USD', 'BNB-USD']:
        return 'Crypto'
    elif ticker in ['GC=F', 'SI=F', 'CL=F', 'NG=F', 'ZW=F', 'ZC=F', 'ZS=F', 'HG=F', 'PL=F', 'PA=F']:
        return 'Commodities'
    elif any(x in ticker for x in ['EUR', 'USD', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD', 'HKD']):
        return 'FX'
    elif ticker in ['SPY', 'QQQ', 'IWM', 'DIA', 'VOO', 'VTI', 'VEA', 'VWO']:
        return 'US_ETF_Index'
    elif ticker in ['XLF', 'XLK', 'XLE', 'XLU', 'XLI', 'XLP', 'XLB', 'XLV', 'XLRE', 'XRT']:
        return 'US_Sector_ETF'
    elif ticker in ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AMZN', 'NFLX', 'TSLA', 'AMD', 'INTC', 'CRM', 'ORCL', 'ADBE', 'AVGO', 'QCOM', 'TXN', 'MU', 'PLTR', 'SNOW', 'DDOG', 'CRWD', 'OKTA', 'SHOP', 'SQ', 'ROKU', 'ZM', 'UBER', 'LYFT', 'DASH', 'ABNB']:
        return 'US_Tech_Growth'
    elif ticker in ['JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'BLK', 'AXP', 'USB', 'PNC', 'TFC', 'COF', 'SCHW', 'BK', 'STT', 'SPGI', 'MCO', 'ICE', 'CME', 'NDAQ']:
        return 'US_Banks_Finance'
    elif ticker in ['JNJ', 'PFE', 'UNH', 'ABBV', 'LLY', 'TMO', 'ABT', 'DHR', 'BMY', 'MRK', 'AMGN', 'GILD', 'VRTX', 'REGN', 'BIIB', 'ISRG', 'ZTS', 'CVS', 'CI', 'HUM']:
        return 'US_Healthcare'
    elif ticker in ['WMT', 'COST', 'TGT', 'HD', 'LOW', 'NKE', 'MCD', 'SBUX', 'TJX', 'DG', 'DLTR', 'ROST', 'BURL', 'GO', 'CRI', 'KSS', 'JWN', 'M', 'TSCO', 'FIVE']:
        return 'US_Consumer_Retail'
    elif ticker in ['PG', 'KO', 'PEP', 'WFC', 'KMB', 'CL', 'EL', 'GIS', 'K', 'CPB', 'CAG', 'HSY', 'MDLZ', 'SJM', 'BGS', 'FLO', 'LANC', 'REYN', 'CHD', 'KHC']:
        return 'US_Consumer_Staples'
    elif ticker in ['XOM', 'CVX', 'COP', 'EOG', 'SLB', 'OXY', 'MPC', 'VLO', 'PSX', 'WMB', 'KMI', 'OKE', 'EPD', 'ET', 'MPLX', 'ENB', 'TRP', 'SU', 'IMO', 'CNQ']:
        return 'US_Energy'
    elif ticker in ['BA', 'CAT', 'GE', 'HON', 'RTX', 'LMT', 'NOC', 'GD', 'TDG', 'HEI', 'WM', 'RSG', 'CNI', 'UNP', 'CSX', 'NSC', 'FDX', 'UPS', 'LUV', 'DAL']:
        return 'US_Industrials'
    elif ticker in ['VZ', 'T', 'TMUS', 'CMCSA', 'CHTR', 'DIS', 'NFLX', 'WBD', 'PARA', 'FOX', 'GOOG', 'META', 'SNAP', 'PINS', 'TWTR', 'MTCH', 'IAC', 'SPOT', 'LYV', 'TKO']:
        return 'US_Communications_Media'
    elif ticker in ['V', 'MA', 'AXP', 'DFS', 'SYF', 'COF', 'ALLY', 'SLM', 'NAVI', 'TROW', 'BLK', 'STT', 'BEN', 'IVZ', 'AMG', 'APAM', 'BRO', 'ERIE', 'AON', 'AJG']:
        return 'US_Financial_Services'
    else:
        return 'US_Other'

# Get all tickers with sufficient data
cursor.execute('''
    SELECT ticker, COUNT(*) as cnt 
    FROM silver.unified_prices 
    WHERE date >= '2021-01-01'
    GROUP BY ticker
    HAVING COUNT(*) >= 500
''')
valid_tickers = [r[0] for r in cursor.fetchall()]

print('='*90)
print('CONTINUOUS TESTING: S002 Trend Following on FULL UNIVERSE')
print('='*90)
print(f'Testing on {len(valid_tickers)} tickers...\n')

# S002: Trend Following (Price > SMA50)
def test_trend_following(ticker):
    cursor.execute(f"SELECT date, close::float FROM silver.unified_prices WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date")
    data = cursor.fetchall()
    if len(data) < 200:
        return None
    
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    df['sma50'] = df['close'].rolling(50).mean()
    
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]
    
    # Test period
    trades = []
    for i in range(50, len(test) - 10):
        if pd.notna(test['sma50'].iloc[i]) and test['close'].iloc[i] > test['sma50'].iloc[i]:
            entry = test['close'].iloc[i]
            exit_p = test['close'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    
    if len(trades) < 10:
        return None
    
    test_wr = (pd.Series(trades) > 0).mean() * 100
    
    # Validate period
    val_trades = []
    for i in range(50, len(validate) - 10):
        if pd.notna(validate['sma50'].iloc[i]) and validate['close'].iloc[i] > validate['sma50'].iloc[i]:
            entry = validate['close'].iloc[i]
            exit_p = validate['close'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            val_trades.append(ret)
    
    val_wr = 0
    if len(val_trades) >= 5:
        val_wr = (pd.Series(val_trades) > 0).mean() * 100
    
    return {'test_wr': test_wr, 'val_wr': val_wr, 'test_n': len(trades)}

# Test all tickers
s002_results = {}
count = 0

for ticker in valid_tickers:
    count += 1
    if count % 100 == 0:
        print(f'Progress: {count}/{len(valid_tickers)}...')
    
    result = test_trend_following(ticker)
    if result and result['test_wr'] >= 60 and result['val_wr'] >= 55:
        sector = classify_sector(ticker)
        if sector not in s002_results:
            s002_results[sector] = []
        s002_results[sector].append({
            'ticker': ticker,
            'test_wr': result['test_wr'],
            'val_wr': result['val_wr'],
            'test_n': result['test_n']
        })

print('\n' + '='*90)
print('S002 TREND FOLLOWING RESULTS BY SECTOR')
print('='*90)

for sector, tickers in sorted(s002_results.items(), key=lambda x: len(x[1]), reverse=True):
    avg_test = np.mean([t['test_wr'] for t in tickers])
    avg_val = np.mean([t['val_wr'] for t in tickers])
    total_n = sum([t['test_n'] for t in tickers])
    
    print(f"\n{sector}: {len(tickers)} tickers | Avg Test: {avg_test:.1f}% | Avg Val: {avg_val:.1f}% | Trades: {total_n}")
    print('-' * 80)
    
    for t in sorted(tickers, key=lambda x: x['test_wr'], reverse=True)[:5]:
        print(f"  {t['ticker']:<15} Test: {t['test_wr']:>6.1f}%  Val: {t['val_wr']:>6.1f}%  Trades: {t['test_n']:>3}")

print('\n' + '='*90)
print('TOP SECTORS FOR TREND FOLLOWING')
print('='*90)

for sector, tickers in sorted(s002_results.items(), key=lambda x: np.mean([t['test_wr'] for t in x[1]]), reverse=True)[:3]:
    avg_test = np.mean([t['test_wr'] for t in tickers])
    avg_val = np.mean([t['val_wr'] for t in tickers])
    count = len(tickers)
    
    if avg_test >= 65 and count >= 3:
        print(f"\n🏆 {sector}: {count} tickers, {avg_test:.1f}% avg test WR")

conn.close()

print('\n' + '='*90)
print(f'Total tickers passing: {sum(len(v) for v in s002_results.values())}/{len(valid_tickers)}')
print('='*90)
