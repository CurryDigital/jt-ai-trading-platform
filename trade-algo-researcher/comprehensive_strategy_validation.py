#!/usr/bin/env python3
"""
COMPREHENSIVE STRATEGY RE-TEST
Validate all Golden, Near-Golden, and Cross-Market strategies
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
print('COMPREHENSIVE STRATEGY VALIDATION')
print('Re-testing all strategies with full data')
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

results = []

# Helper function
def get_data(ticker, start='2022-01-01', end='2024-12-31'):
    cursor.execute(f'''
        SELECT date, open::float, high::float, low::float, close::float, volume::float
        FROM silver.unified_prices
        WHERE ticker = '{ticker}' AND date BETWEEN '{start}' AND '{end}'
        ORDER BY date
    ''')
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    df['return'] = df['close'].pct_change() * 100
    return df

# STRATEGY 1: COIN Strong Uptrend
print('\\n' + '='*70)
print('STRATEGY 1: COIN Strong Uptrend GOLD')
print('='*70)

spy_df = get_data('SPY')
spy_df['sma50'] = spy_df['close'].rolling(50).mean()
spy_df['sma200'] = spy_df['close'].rolling(200).mean()
spy_df['golden_cross'] = spy_df['sma50'] > spy_df['sma200']

coin_df = get_data('COIN')
coin_df['rsi_14'] = 100 - (100 / (1 + coin_df['close'].pct_change().rolling(14).apply(
    lambda x: x[x > 0].mean() / abs(x[x < 0]).mean() if x[x < 0].mean() != 0 else 1)))

# Simplified RSI calculation
coin_df['gain'] = coin_df['return'].where(coin_df['return'] > 0, 0)
coin_df['loss'] = -coin_df['return'].where(coin_df['return'] < 0, 0)
coin_df['avg_gain'] = coin_df['gain'].rolling(14).mean()
coin_df['avg_loss'] = coin_df['loss'].rolling(14).mean()
coin_df['rs'] = coin_df['avg_gain'] / coin_df['avg_loss']
coin_df['rsi_14'] = 100 - (100 / (1 + coin_df['rs']))

merged = coin_df.merge(spy_df[['date', 'golden_cross']], on='date', how='inner')

trades = []
for idx, row in merged.iterrows():
    if pd.notna(row['rsi_14']) and row['rsi_14'] < 25 and row['golden_cross']:
        entry_idx = merged.index.get_loc(idx)
        exit_idx = entry_idx + 10
        if exit_idx < len(merged):
            ret = (merged.iloc[exit_idx]['close'] - row['close']) / row['close'] * 100 - 0.1
            trades.append(ret)

if trades:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    print(f'Trades: {len(trades)}, Win%: {wr:.1f}%, Avg Return: {r.mean():.2f}%')
    results.append(('COIN Strong Uptrend', len(trades), wr, r.mean(), '✅' if wr >= 70 else '🟡'))

# STRATEGY 2: IWM SPY Regime
print('\\n' + '='*70)
print('STRATEGY 2: IWM SPY Regime')
print('='*70)

iwm_df = get_data('IWM')
iwm_df['rsi_14'] = 100 - (100 / (1 + iwm_df['gain'].rolling(14).mean() / iwm_df['loss'].rolling(14).mean()))

# Re-calculate properly
iwm_df['gain'] = iwm_df['return'].where(iwm_df['return'] > 0, 0)
iwm_df['loss'] = -iwm_df['return'].where(iwm_df['return'] < 0, 0)
iwm_df['avg_gain'] = iwm_df['gain'].rolling(14).mean()
iwm_df['avg_loss'] = iwm_df['loss'].rolling(14).mean()
iwm_df['rs'] = iwm_df['avg_gain'] / iwm_df['avg_loss']
iwm_df['rsi_14'] = 100 - (100 / (1 + iwm_df['rs']))

merged_iwm = iwm_df.merge(spy_df[['date', 'sma200']], on='date', how='inner')
merged_iwm['spy_above_200d'] = merged_iwm['close'] > merged_iwm['sma200']

trades_iwm = []
for idx, row in merged_iwm.iterrows():
    if pd.notna(row['rsi_14']) and row['rsi_14'] < 20 and row['spy_above_200d']:
        entry_idx = merged_iwm.index.get_loc(idx)
        exit_idx = entry_idx + 10
        if exit_idx < len(merged_iwm):
            ret = (merged_iwm.iloc[exit_idx]['close'] - row['close']) / row['close'] * 100 - 0.1
            trades_iwm.append(ret)

if trades_iwm:
    r = pd.Series(trades_iwm)
    wr = (r > 0).mean() * 100
    print(f'Trades: {len(trades_iwm)}, Win%: {wr:.1f}%, Avg Return: {r.mean():.2f}%')
    results.append(('IWM SPY Regime', len(trades_iwm), wr, r.mean(), '✅' if wr >= 70 else '🟡'))

# STRATEGY 3: QQQ Lead-Lag
print('\\n' + '='*70)
print('STRATEGY 3: QQQ Lead-Lag → 0700.HK')
print('='*70)

qqq_df = get_data('QQQ')
hk_df = get_data('0700.HK')
hk_df['prev_close'] = hk_df['close'].shift(1)
hk_df['overnight_gap'] = (hk_df['open'] - hk_df['prev_close']) / hk_df['prev_close'] * 100

qqq_df['date_plus_1'] = pd.to_datetime(qqq_df['date']) + pd.Timedelta(days=1)
hk_df['date'] = pd.to_datetime(hk_df['date'])
merged_qqq = qqq_df.merge(hk_df[['date', 'overnight_gap']], left_on='date_plus_1', right_on='date', how='inner')

signals = merged_qqq[merged_qqq['return'] > 2.0]
if len(signals) > 0:
    wr = (signals['overnight_gap'] > 0).mean() * 100
    avg_gap = signals['overnight_gap'].mean()
    print(f'Signals: {len(signals)}, Win%: {wr:.1f}%, Avg Gap: {avg_gap:.2f}%')
    results.append(('QQQ Lead-Lag', len(signals), wr, avg_gap, '✅' if wr >= 70 else '🟡'))

# STRATEGY 4: NVDA AI Theme
print('\\n' + '='*70)
print('STRATEGY 4: NVDA > +5% → 0700.HK')
print('='*70)

nvda_df = get_data('NVDA')
merged_nvda = nvda_df.merge(hk_df[['date', 'overnight_gap']], left_on='date_plus_1', right_on='date', how='inner')

signals_nvda = merged_nvda[merged_nvda['return'] > 5.0]
if len(signals_nvda) > 0:
    wr = (signals_nvda['overnight_gap'] > 0).mean() * 100
    avg_gap = signals_nvda['overnight_gap'].mean()
    print(f'Signals: {len(signals_nvda)}, Win%: {wr:.1f}%, Avg Gap: {avg_gap:.2f}%')
    results.append(('NVDA AI Theme', len(signals_nvda), wr, avg_gap, '✅' if wr >= 70 else '🟡'))

# STRATEGY 5: MSTR SPY Regime
print('\\n' + '='*70)
print('STRATEGY 5: MSTR + SPY Filter')
print('='*70)

mstr_df = get_data('MSTR')
mstr_df['gain'] = mstr_df['return'].where(mstr_df['return'] > 0, 0)
mstr_df['loss'] = -mstr_df['return'].where(mstr_df['return'] < 0, 0)
mstr_df['avg_gain'] = mstr_df['gain'].rolling(14).mean()
mstr_df['avg_loss'] = mstr_df['loss'].rolling(14).mean()
mstr_df['rs'] = mstr_df['avg_gain'] / mstr_df['avg_loss']
mstr_df['rsi_14'] = 100 - (100 / (1 + mstr_df['rs']))

merged_mstr = mstr_df.merge(spy_df[['date', 'sma200', 'sma50']], on='date', how='inner')
merged_mstr['spy_above_50d'] = merged_mstr['close'] > merged_mstr['sma50']

trades_mstr = []
for idx, row in merged_mstr.iterrows():
    if pd.notna(row['rsi_14']) and row['rsi_14'] < 25 and row['spy_above_50d']:
        entry_idx = merged_mstr.index.get_loc(idx)
        exit_idx = entry_idx + 10
        if exit_idx < len(merged_mstr):
            ret = (merged_mstr.iloc[exit_idx]['close'] - row['close']) / row['close'] * 100 - 0.1
            trades_mstr.append(ret)

if trades_mstr:
    r = pd.Series(trades_mstr)
    wr = (r > 0).mean() * 100
    print(f'Trades: {len(trades_mstr)}, Win%: {wr:.1f}%, Avg Return: {r.mean():.2f}%')
    results.append(('MSTR SPY Regime', len(trades_mstr), wr, r.mean(), '✅' if wr >= 70 else '🟡'))

conn.close()

print('\\n' + '='*70)
print('VALIDATION SUMMARY')
print('='*70)

results_df = pd.DataFrame(results, columns=['Strategy', 'Trades', 'Win%', 'Avg_Return', 'Status'])
results_df = results_df.sort_values('Win%', ascending=False)

print('\\n{:<25} {:<10} {:<10} {:<12} {:<8}'.format(
    'Strategy', 'Trades', 'Win%', 'Avg Return', 'Status'
))
print('-'*70)

for _, row in results_df.iterrows():
    print('{:<25} {:<10} {:<10.1f} {:<12.2f} {:<8}'.format(
        row['Strategy'], row['Trades'], row['Win%'], row['Avg_Return'], row['Status']
    ))

# Check which are reliable
reliable = results_df[results_df['Win%'] >= 70]
moderate = results_df[(results_df['Win%'] >= 55) & (results_df['Win%'] < 70)]
weak = results_df[results_df['Win%'] < 55]

print('\\n' + '='*70)
print('FINAL ASSESSMENT')
print('='*70)

print(f'\\n✅ RELIABLE (70%+ win): {len(reliable)} strategies')
for _, row in reliable.iterrows():
    print(f'   - {row["Strategy"]}: {row["Win%"]:.1f}%')

print(f'\\n🟡 MODERATE (55-70% win): {len(moderate)} strategies')
for _, row in moderate.iterrows():
    print(f'   - {row["Strategy"]}: {row["Win%"]:.1f}%')

if len(weak) > 0:
    print(f'\\n❌ WEAK (<55% win): {len(weak)} strategies')
    for _, row in weak.iterrows():
        print(f'   - {row["Strategy"]}: {row["Win%"]:.1f}%')

print('\\n' + '='*70)
