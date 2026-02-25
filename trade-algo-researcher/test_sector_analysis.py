#!/usr/bin/env python3
"""
SECTOR ANALYSIS: S001 RSI < 30
Full universe → Industry breakdown → Identify best sectors
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

def test_strategy(df, exit_days=10):
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]
    
    trades_test = []
    for i in range(14, len(test) - exit_days):
        if pd.notna(test['rsi'].iloc[i]) and test['rsi'].iloc[i] < 30:
            entry = test['close'].iloc[i]
            exit_p = test['close'].iloc[i + exit_days]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades_test.append(ret)
    
    if len(trades_test) < 10:
        return None
    
    r_test = pd.Series(trades_test)
    test_wr = (r_test > 0).mean() * 100
    
    trades_val = []
    for i in range(14, len(validate) - exit_days):
        if pd.notna(validate['rsi'].iloc[i]) and validate['rsi'].iloc[i] < 30:
            entry = validate['close'].iloc[i]
            exit_p = validate['close'].iloc[i + exit_days]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades_val.append(ret)
    
    val_wr = 0
    if len(trades_val) >= 5:
        r_val = pd.Series(trades_val)
        val_wr = (r_val > 0).mean() * 100
    
    return {'test_wr': test_wr, 'val_wr': val_wr, 'test_n': len(trades_test), 'val_n': len(trades_val)}

# Get full universe with sector classification
print('='*90)
print('S001 RSI < 30: FULL UNIVERSE → SECTOR ANALYSIS')
print('='*90)

cursor.execute('''
    SELECT DISTINCT ticker FROM silver.unified_prices 
    WHERE date >= '2021-01-01'
''')
all_tickers = [r[0] for r in cursor.fetchall()]

# Classify by sector based on ticker patterns
def classify_sector(ticker):
    if ticker.endswith('.HK'):
        # HK classification by number ranges
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

# Test all tickers and group by sector
sector_results = {}

for ticker in all_tickers:
    cursor.execute(f"SELECT COUNT(*) FROM silver.unified_prices WHERE ticker = '{ticker}' AND date >= '2021-01-01'")
    count = cursor.fetchone()[0]
    if count < 500:
        continue
    
    cursor.execute(f"SELECT date, close::float FROM silver.unified_prices WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date")
    data = cursor.fetchall()
    
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    df['rsi'] = rsi(df['close'])
    
    result = test_strategy(df, 10)
    if result and result['test_wr'] >= 60 and result['val_wr'] >= 55:
        sector = classify_sector(ticker)
        if sector not in sector_results:
            sector_results[sector] = []
        sector_results[sector].append({
            'ticker': ticker,
            'test_wr': result['test_wr'],
            'val_wr': result['val_wr'],
            'test_n': result['test_n'],
            'val_n': result['val_n']
        })

conn.close()

# Print results by sector
print('\n' + '='*90)
print('RESULTS BY SECTOR (Test >=60%, Val >=55%, n >=10)')
print('='*90)

for sector, tickers in sorted(sector_results.items(), key=lambda x: len(x[1]), reverse=True):
    avg_test = np.mean([t['test_wr'] for t in tickers])
    avg_val = np.mean([t['val_wr'] for t in tickers])
    total_test_n = sum([t['test_n'] for t in tickers])
    
    print(f"\n{sector}: {len(tickers)} tickers | Avg Test: {avg_test:.1f}% | Avg Val: {avg_val:.1f}% | Total Trades: {total_test_n}")
    print('-' * 80)
    
    # Sort by test win rate
    for t in sorted(tickers, key=lambda x: x['test_wr'], reverse=True)[:10]:
        print(f"  {t['ticker']:<15} Test: {t['test_wr']:>6.1f}%  Val: {t['val_wr']:>6.1f}%  Trades: {t['test_n']:>3}")

print('\n' + '='*90)
print('SECTOR RECOMMENDATIONS')
print('='*90)

# Identify best sectors
for sector, tickers in sorted(sector_results.items(), key=lambda x: np.mean([t['test_wr'] for t in x[1]]), reverse=True)[:5]:
    avg_test = np.mean([t['test_wr'] for t in tickers])
    avg_val = np.mean([t['val_wr'] for t in tickers])
    count = len(tickers)
    
    if avg_test >= 70 and count >= 3:
        print(f"\n🏆 {sector}: {count} tickers, {avg_test:.1f}% avg test WR")
        print(f"   Deploy S001-RSI on this sector")

print('\n' + '='*90)
