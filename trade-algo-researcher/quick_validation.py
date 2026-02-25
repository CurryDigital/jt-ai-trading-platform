#!/usr/bin/env python3
"""
SIMPLIFIED STRATEGY VALIDATION
Test key strategies only
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np

print('='*70)
print('SIMPLIFIED STRATEGY VALIDATION')
print('='*70)

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

# Get data function
def get_prices(ticker):
    cursor.execute(f'''
        SELECT date, close::float
        FROM silver.unified_prices
        WHERE ticker = '{ticker}' AND date BETWEEN '2022-01-01' AND '2024-12-31'
        ORDER BY date
    ''')
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['return'] = df['close'].pct_change() * 100
    return df

# Test 1: QQQ Lead-Lag
print('\\n=== TEST 1: QQQ Lead-Lag → 0700.HK ===')
qqq = get_prices('QQQ')
hk = get_prices('0700.HK')
hk['prev'] = hk['close'].shift(1)
hk['gap'] = (hk['close'] - hk['prev']) / hk['prev'] * 100

qqq['next_date'] = pd.to_datetime(qqq['date']) + pd.Timedelta(days=1)
merged = qqq.merge(hk[['date', 'gap']], left_on='next_date', right_on='date', how='inner')

signals = merged[merged['return'] > 2.0]
wr = (signals['gap'] > 0).mean() * 100
print(f'Signals: {len(signals)}, Win%: {wr:.1f}%')

# Test 2: NVDA AI Theme
print('\\n=== TEST 2: NVDA > +5% → 0700.HK ===')
nvda = get_prices('NVDA')
nvda['next_date'] = pd.to_datetime(nvda['date']) + pd.Timedelta(days=1)
merged2 = nvda.merge(hk[['date', 'gap']], left_on='next_date', right_on='date', how='inner')

signals2 = merged2[merged2['return'] > 5.0]
wr2 = (signals2['gap'] > 0).mean() * 100
print(f'Signals: {len(signals2)}, Win%: {wr2:.1f}%')

# Test 3: IWM Lead-Lag
print('\\n=== TEST 3: IWM Lead-Lag → 0700.HK ===')
iwm = get_prices('IWM')
iwm['next_date'] = pd.to_datetime(iwm['date']) + pd.Timedelta(days=1)
merged3 = iwm.merge(hk[['date', 'gap']], left_on='next_date', right_on='date', how='inner')

signals3 = merged3[merged3['return'] > 2.0]
wr3 = (signals3['gap'] > 0).mean() * 100
print(f'Signals: {len(signals3)}, Win%: {wr3:.1f}%')

# Test 4: MSTR SPY Filter
print('\\n=== TEST 4: MSTR RSI Strategy ===')
mstr = get_prices('MSTR')
spy = get_prices('SPY')

# Calculate simple RSI
delta = mstr['close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
mstr['rsi'] = 100 - (100 / (1 + rs))

# SPY above 200d
spy['sma200'] = spy['close'].rolling(200).mean()
spy['above_200d'] = spy['close'] > spy['sma200']

merged4 = mstr.merge(spy[['date', 'above_200d']], on='date', how='inner')

trades = []
for i in range(len(merged4) - 10):
    if pd.notna(merged4['rsi'].iloc[i]) and merged4['rsi'].iloc[i] < 25 and merged4['above_200d'].iloc[i]:
        entry = merged4['close'].iloc[i]
        exit_p = merged4['close'].iloc[i + 10]
        ret = (exit_p - entry) / entry * 100 - 0.1
        trades.append(ret)

if trades:
    r = pd.Series(trades)
    wr4 = (r > 0).mean() * 100
    print(f'Trades: {len(trades)}, Win%: {wr4:.1f}%, Avg: {r.mean():.2f}%')

conn.close()

print('\\n' + '='*70)
print('VALIDATION SUMMARY')
print('='*70)
print(f'✅ QQQ Lead-Lag: {wr:.1f}% win rate')
print(f'✅ NVDA AI Theme: {wr2:.1f}% win rate')
print(f'✅ IWM Lead-Lag: {wr3:.1f}% win rate')
print(f'✅ MSTR Strategy: {wr4:.1f}% win rate')
print('='*70)
