#!/usr/bin/env python3
"""
3-PERIOD VALIDATION: Train / Test / Validate
Train: 2021-2022 | Test: 2023-2024 | Validate: 2025-2026
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np

print('='*80)
print('3-PERIOD VALIDATION: Train / Test / Validate')
print('Train: 2021-2022 | Test: 2023-2024 | Validate: 2025-Feb 2026')
print('='*80)

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

def get_data(ticker):
    cursor.execute(f'''
        SELECT date, open::float, high::float, low::float, close::float, volume::float
        FROM silver.unified_prices
        WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20'
        ORDER BY date
    ''')
    data = cursor.fetchall()
    if len(data) == 0:
        return None
    df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    df['date'] = pd.to_datetime(df['date'])
    df['return'] = df['close'].pct_change() * 100
    return df

def rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Split into 3 periods
def split_periods(df):
    train = df[(df['date'] >= '2021-01-01') & (df['date'] <= '2022-12-31')]
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]
    return train, test, validate

results = []

print('\n' + '='*80)
print('GOLDEN STRATEGIES - 3 PERIOD VALIDATION')
print('='*80)

# G003: MSTR Momentum
ticker = 'MSTR'
print(f'\nG003: MSTR Momentum Trend')
df = get_data(ticker)
if df is not None:
    df['rsi'] = rsi(df['close'])
    df['sma50'] = df['close'].rolling(50).mean()
    
    # Calculate ADX (simplified)
    df['high_low'] = df['high'] - df['low']
    df['high_close'] = abs(df['high'] - df['close'].shift())
    df['low_close'] = abs(df['low'] - df['close'].shift())
    df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
    df['atr'] = df['tr'].rolling(14).mean()
    
    # +DM and -DM
    df['plus_dm'] = df['high'].diff()
    df['minus_dm'] = -df['low'].diff()
    df['plus_dm'] = df['plus_dm'].where(df['plus_dm'] > df['minus_dm'], 0)
    df['minus_dm'] = df['minus_dm'].where(df['minus_dm'] > df['plus_dm'], 0)
    df['plus_dm'] = df['plus_dm'].where(df['plus_dm'] > 0, 0)
    df['minus_dm'] = df['minus_dm'].where(df['minus_dm'] > 0, 0)
    
    df['plus_di'] = 100 * df['plus_dm'].rolling(14).mean() / df['atr']
    df['minus_di'] = 100 * df['minus_dm'].rolling(14).mean() / df['atr']
    df['dx'] = 100 * abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di'])
    df['adx'] = df['dx'].rolling(14).mean()
    
    train, test, validate = split_periods(df)
    
    for period_name, period_df in [('Train', train), ('Test', test), ('Validate', validate)]:
        trades = []
        for i in range(50, len(period_df) - 15):
            if pd.notna(period_df['rsi'].iloc[i]) and pd.notna(period_df['adx'].iloc[i]):
                if period_df['close'].iloc[i] > period_df['sma50'].iloc[i] and period_df['adx'].iloc[i] > 25:
                    entry = period_df['close'].iloc[i+1]  # Next day open
                    exit_p = period_df['close'].iloc[i + min(15, len(period_df) - i - 2)]
                    ret = (exit_p - entry) / entry * 100 - 0.1
                    trades.append(ret)
        
        if trades:
            r = pd.Series(trades)
            wr = (r > 0).mean() * 100
            print(f'   {period_name}: {wr:.1f}% ({len(trades)} trades)')
            results.append(('G003', ticker, period_name, wr, len(trades)))

# G005: MSFT Momentum
ticker = 'MSFT'
print(f'\nG005: MSFT Momentum Trend')
df = get_data(ticker)
if df is not None:
    df['rsi'] = rsi(df['close'])
    df['sma50'] = df['close'].rolling(50).mean()
    df['adx'] = df['close'].rolling(14).std()  # Proxy for simplicity
    
    train, test, validate = split_periods(df)
    
    for period_name, period_df in [('Train', train), ('Test', test), ('Validate', validate)]:
        trades = []
        for i in range(50, len(period_df) - 15):
            if period_df['close'].iloc[i] > period_df['sma50'].iloc[i]:
                entry = period_df['close'].iloc[i+1]
                exit_p = period_df['close'].iloc[i + min(15, len(period_df) - i - 2)]
                ret = (exit_p - entry) / entry * 100 - 0.1
                trades.append(ret)
        
        if trades:
            r = pd.Series(trades)
            wr = (r > 0).mean() * 100
            print(f'   {period_name}: {wr:.1f}% ({len(trades)} trades)')
            results.append(('G005', ticker, period_name, wr, len(trades)))

conn.close()

# Summary
print('\n' + '='*80)
print('3-PERIOD VALIDATION SUMMARY')
print('='*80)

for strategy, ticker, period, wr, n in results:
    status = ''
    if period == 'Validate':
        if wr >= 60 and n >= 10:
            status = '✅ ROBUST'
        elif wr >= 55 and n >= 5:
            status = '🟡 BORDERLINE'
        else:
            status = '❌ FAILED'
    print(f'{strategy} {ticker} {period}: {wr:.1f}% ({n} trades) {status}')

print('\n' + '='*80)
print('VALIDATION CRITERIA:')
print('  Train:   ≥65% win, n≥30')
print('  Test:    ≥65% win, n≥20, decay<20%')
print('  Validate: ≥60% win, n≥10, decay<25%')
print('='*80)
