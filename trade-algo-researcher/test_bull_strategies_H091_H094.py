#!/usr/bin/env python3
"""
BULL/BEAR STRATEGIES: Comprehensive Testing
H091-H100
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

def rsi(p, n=14):
    d = p.diff()
    g = d.where(d > 0, 0).rolling(n).mean()
    l = (-d.where(d < 0, 0)).rolling(n).mean()
    return 100 - (100 / (1 + g/l))

results_summary = []

# H091: QQQ Bull Market Momentum
print('='*90)
print('H091: QQQ Bull Market Momentum (Price > SMA200)')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'QQQ' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
qqq = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
qqq['date'] = pd.to_datetime(qqq['date'])
qqq['sma50'] = qqq['close'].rolling(50).mean()
qqq['sma200'] = qqq['close'].rolling(200).mean()
qqq['rsi'] = rsi(qqq['close'])

test = qqq[(qqq['date'] >= '2023-01-01') & (qqq['date'] <= '2024-12-31')]
validate = qqq[(qqq['date'] >= '2025-01-01') & (qqq['date'] <= '2026-02-20')]

def test_bull_momentum(period_df):
    trades = []
    for i in range(200, len(period_df) - 10):
        if (pd.notna(period_df['sma200'].iloc[i]) and 
            period_df['close'].iloc[i] > period_df['sma200'].iloc[i] and  # Bull market
            period_df['close'].iloc[i] > period_df['sma50'].iloc[i]):  # Uptrend
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_bull_momentum(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_bull_momentum(test)
v_res = test_bull_momentum(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H091', 'QQQ Bull Momentum', verdict, t_res['win_rate'], v_res['win_rate']))

# H092: SPY Bull Market + RSI Filter
print('\n' + '='*90)
print('H092: SPY Bull Market + RSI > 50')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = 'SPY' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
spy = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
spy['date'] = pd.to_datetime(spy['date'])
spy['sma50'] = spy['close'].rolling(50).mean()
spy['sma200'] = spy['close'].rolling(200).mean()
spy['rsi'] = rsi(spy['close'])

test = spy[(spy['date'] >= '2023-01-01') & (spy['date'] <= '2024-12-31')]
validate = spy[(spy['date'] >= '2025-01-01') & (spy['date'] <= '2026-02-20')]

def test_bull_rsi(period_df):
    trades = []
    for i in range(200, len(period_df) - 10):
        if (pd.notna(period_df['sma200'].iloc[i]) and 
            period_df['close'].iloc[i] > period_df['sma200'].iloc[i] and  # Bull market
            pd.notna(period_df['rsi'].iloc[i]) and
            period_df['rsi'].iloc[i] > 50):  # Strong momentum
            entry = period_df['close'].iloc[i]
            exit_p = period_df['close'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    if len(trades) < 10:
        return None
    r = pd.Series(trades)
    return {'trades': len(trades), 'win_rate': (r > 0).mean() * 100}

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_bull_rsi(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_bull_rsi(test)
v_res = test_bull_rsi(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H092', 'SPY Bull+RSI', verdict, t_res['win_rate'], v_res['win_rate']))

# H093: XLK Bull Market
print('\n' + '='*90)
print('H093: XLK Bull Market Trend')
print('='*90)

cursor.execute('''SELECT date, close::float FROM bronze.yf_prices WHERE ticker = 'XLK' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
xlk = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
xlk['date'] = pd.to_datetime(xlk['date'])
xlk['sma50'] = xlk['close'].rolling(50).mean()
xlk['sma200'] = xlk['close'].rolling(200).mean()

test = xlk[(xlk['date'] >= '2023-01-01') & (xlk['date'] <= '2024-12-31')]
validate = xlk[(xlk['date'] >= '2025-01-01') & (xlk['date'] <= '2026-02-20')]

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_bull_momentum(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_bull_momentum(test)
v_res = test_bull_momentum(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H093', 'XLK Bull Trend', verdict, t_res['win_rate'], v_res['win_rate']))

# H094: China A-Shares Trend
print('\n' + '='*90)
print('H094: China A-Shares (000858.SZ) Trend')
print('='*90)

cursor.execute('''SELECT date, close::float FROM silver.unified_prices WHERE ticker = '000858.SZ' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date''')
cn = pd.DataFrame(cursor.fetchall(), columns=['date', 'close'])
cn['date'] = pd.to_datetime(cn['date'])
cn['sma50'] = cn['close'].rolling(50).mean()
cn['sma200'] = cn['close'].rolling(200).mean()

test = cn[(cn['date'] >= '2023-01-01') & (cn['date'] <= '2024-12-31')]
validate = cn[(cn['date'] >= '2025-01-01') & (cn['date'] <= '2026-02-20')]

for name, period in [('Test', test), ('Validate', validate)]:
    res = test_bull_momentum(period)
    if res:
        print(f"{name}: {res['trades']} trades, {res['win_rate']:.1f}% win")
    else:
        print(f"{name}: Insufficient trades")

t_res = test_bull_momentum(test)
v_res = test_bull_momentum(validate)
if t_res and v_res:
    verdict = '✅ VALIDATED' if t_res['win_rate'] >= 60 and v_res['win_rate'] >= 55 else '❌ FAILED'
    print(f"Verdict: {verdict}")
    results_summary.append(('H094', 'China A-Share Trend', verdict, t_res['win_rate'], v_res['win_rate']))

print('\n' + '='*90)
print('BULL MARKET STRATEGIES SUMMARY')
print('='*90)
for r in results_summary:
    print(f"{r[0]}: {r[1]} - {r[2]} (Test: {r[3]:.1f}%, Val: {r[4]:.1f}%)")

conn.close()
