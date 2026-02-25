#!/usr/bin/env python3
"""
EFFICIENT MASSIVE TEST - Core 50+ Hypotheses
Streamlined testing of all major hypothesis categories
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
print('EFFICIENT MASSIVE TEST: 50+ Core Hypotheses')
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

results = []

# Get all data upfront
print('Loading data...')
tickers = {}
for t in ['QQQ', 'SPY', '0700.HK', 'MSTR', 'COIN', 'IWM', 'NVDA']:
    cursor.execute(f"SELECT date, open::float, high::float, low::float, close::float, volume::float FROM silver.unified_prices WHERE ticker = '{t}' AND date BETWEEN '2021-01-01' AND '2024-12-31' ORDER BY date")
    data = cursor.fetchall()
    if data:
        df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
        df['date'] = pd.to_datetime(df['date'])
        tickers[t] = df

conn.close()

def rsi(p):
    d = p.diff()
    g = d.where(d > 0, 0).rolling(14).mean()
    l = (-d.where(d < 0, 0)).rolling(14).mean()
    rs = g / l
    return 100 - (100 / (1 + rs))

def classify(tr, te, tn):
    if tn < 5: return '⏳'
    if te >= 70 and abs(tr-te) < 15: return '✅ GOLDEN'
    if te >= 55: return '🟡 VALID'
    return '❌ REJECT'

# Pre-calculate indicators
print('Calculating indicators...')
for t, df in tickers.items():
    df['rsi'] = rsi(df['close'])
    df['sma20'] = df['close'].rolling(20).mean()
    df['std20'] = df['close'].rolling(20).std()
    df['bb_lower'] = df['sma20'] - 2 * df['std20']
    df['bb_upper'] = df['sma20'] + 2 * df['std20']
    df['bb_pct_b'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    df['vol_avg'] = df['volume'].rolling(20).mean()
    df['dow'] = df['date'].dt.dayofweek
    df['ret'] = df['close'].pct_change() * 100
    df['next_ret'] = (df['close'].shift(-10) - df['close']) / df['close'] * 100 - 0.1

# ============================================
# 1. RSI HYPOTHESES (20+)
# ============================================
print('\n' + '='*80)
print('1. RSI HYPOTHESES (20+)')
print('='*80)

for t, df in tickers.items():
    train = df[df['date'] < '2023-01-01']
    test = df[df['date'] >= '2023-01-01']
    
    for thresh in [10, 15, 20, 25, 30]:
        tr = train[(train['rsi'] < thresh) & (train['rsi'].notna())]['next_ret']
        te = test[(test['rsi'] < thresh) & (test['rsi'].notna())]['next_ret']
        
        tr_wr = (tr > 0).mean() * 100 if len(tr) > 0 else 0
        te_wr = (te > 0).mean() * 100 if len(te) > 0 else 0
        status = classify(tr_wr, te_wr, len(te))
        
        results.append({'name': f'RSI<{thresh} on {t}', 'tr': tr_wr, 'te': te_wr, 'n': len(te), 'st': status})
        if len(te) >= 5:
            print(f"RSI<{thresh} on {t:<10} | Train: {tr_wr:5.1f}% | Test: {te_wr:5.1f}% | N={len(te):<3} | {status}")

# ============================================
# 2. BB HYPOTHESES (15+)
# ============================================
print('\n' + '='*80)
print('2. BB HYPOTHESES (15+)')
print('='*80)

for t, df in tickers.items():
    train = df[df['date'] < '2023-01-01']
    test = df[df['date'] >= '2023-01-01']
    
    for thresh in [0, 0.1, 0.2]:
        tr = train[(train['bb_pct_b'] < thresh) & (train['bb_pct_b'].notna())]['next_ret']
        te = test[(test['bb_pct_b'] < thresh) & (test['bb_pct_b'].notna())]['next_ret']
        
        tr_wr = (tr > 0).mean() * 100 if len(tr) > 0 else 0
        te_wr = (te > 0).mean() * 100 if len(te) > 0 else 0
        status = classify(tr_wr, te_wr, len(te))
        
        results.append({'name': f'BB%<={thresh} on {t}', 'tr': tr_wr, 'te': te_wr, 'n': len(te), 'st': status})
        if len(te) >= 5:
            print(f"BB%<={thresh} on {t:<10} | Train: {tr_wr:5.1f}% | Test: {te_wr:5.1f}% | N={len(te):<3} | {status}")

# ============================================
# 3. VOLUME HYPOTHESES (10+)
# ============================================
print('\n' + '='*80)
print('3. VOLUME HYPOTHESES (10+)')
print('='*80)

for t, df in tickers.items():
    train = df[df['date'] < '2023-01-01']
    test = df[df['date'] >= '2023-01-01']
    
    for v_mult in [1.5, 2.0, 2.5]:
        tr = train[(train['volume'] > train['vol_avg'] * v_mult) & (train['ret'] > 2)]['next_ret']
        te = test[(test['volume'] > test['vol_avg'] * v_mult) & (test['ret'] > 2)]['next_ret']
        
        tr_wr = (tr > 0).mean() * 100 if len(tr) > 0 else 0
        te_wr = (te > 0).mean() * 100 if len(te) > 0 else 0
        status = classify(tr_wr, te_wr, len(te))
        
        results.append({'name': f'Vol>{v_mult}x+Break on {t}', 'tr': tr_wr, 'te': te_wr, 'n': len(te), 'st': status})
        if len(te) >= 5:
            print(f"Vol>{v_mult}x+Break on {t:<10} | Train: {tr_wr:5.1f}% | Test: {te_wr:5.1f}% | N={len(te):<3} | {status}")

# ============================================
# 4. CROSS-MARKET (10+)
# ============================================
print('\n' + '='*80)
print('4. CROSS-MARKET LEAD-LAG (10+)')
print('='*80)

if '0700.HK' in tickers:
    hk = tickers['0700.HK'].copy()
    hk['prev'] = hk['close'].shift(1)
    hk['gap'] = (hk['close'] - hk['prev']) / hk['prev'] * 100
    
    for us_t in ['QQQ', 'NVDA', 'MSTR', 'COIN', 'IWM']:
        if us_t not in tickers:
            continue
        us = tickers[us_t].copy()
        us['next_date'] = us['date'] + pd.Timedelta(days=1)
        merged = us.merge(hk[['date', 'gap']], left_on='next_date', right_on='date', how='inner')
        
        for thresh in [2.0, 3.0, 5.0]:
            train = merged[merged['date_y'] < '2023-01-01']
            test = merged[merged['date_y'] >= '2023-01-01']
            
            tr = train[train['ret'] > thresh]['gap']
            te = test[test['ret'] > thresh]['gap']
            
            tr_wr = (tr > 0).mean() * 100 if len(tr) > 0 else 0
            te_wr = (te > 0).mean() * 100 if len(te) > 0 else 0
            status = classify(tr_wr, te_wr, len(te))
            
            results.append({'name': f'{us_t}>+{thresh}% → HK', 'tr': tr_wr, 'te': te_wr, 'n': len(te), 'st': status})
            if len(te) >= 5:
                print(f"{us_t}>+{thresh}% → HK    | Train: {tr_wr:5.1f}% | Test: {te_wr:5.1f}% | N={len(te):<3} | {status}")

# ============================================
# SUMMARY
# ============================================
print('\n' + '='*80)
print('FINAL SUMMARY')
print('='*80)

valid = [r for r in results if r['n'] >= 5]
valid.sort(key=lambda x: x['te'], reverse=True)

print(f'\nTotal hypotheses tested: {len(results)}')
print(f'With sufficient data: {len(valid)}')

golden = [r for r in valid if r['st'] == '✅ GOLDEN']
validated = [r for r in valid if r['st'] == '🟡 VALID']
rejected = [r for r in valid if r['st'] == '❌ REJECT']

print(f'\n✅ GOLDEN: {len(golden)}')
for r in golden[:5]:
    print(f"   {r['name']}: {r['te']:.1f}%")

print(f'\n🟡 VALIDATED: {len(validated)}')
for r in validated[:10]:
    print(f"   {r['name']}: {r['te']:.1f}%")

print(f'\n❌ REJECTED: {len(rejected)}')
print(f'⏳ INSUFFICIENT: {len(results) - len(valid)}')

print('\n' + '='*80)
print('TOP 15 PERFORMERS')
print('='*80)
print(f"{'Rank':<5} {'Hypothesis':<35} {'Train':<8} {'Test':<8} {'N':<4}")
print('-'*65)
for i, r in enumerate(valid[:15], 1):
    print(f"{i:<5} {r['name'][:35]:<35} {r['tr']:7.1f}% {r['te']:7.1f}% {r['n']:<4}")
