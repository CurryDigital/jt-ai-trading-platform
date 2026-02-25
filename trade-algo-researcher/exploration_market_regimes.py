#!/usr/bin/env python3
"""
EXPLORATION: Create Market-Level Indicators from SPY/QQQ
Calculate VIX proxy, breadth, trend strength for regime filtering
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
print('EXPLORATION: Market-Level Indicators from SPY/QQQ')
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

# Get SPY data
cursor.execute('''
    SELECT date, open::float, high::float, low::float, close::float, volume::float
    FROM silver.unified_prices
    WHERE ticker = 'SPY' AND date BETWEEN '2022-06-01' AND '2024-12-31'
    ORDER BY date
''')
spy_data = cursor.fetchall()
spy_df = pd.DataFrame(spy_data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])

print(f'\\n=== SPY Data Loaded ===')
print(f'Records: {len(spy_df)}')

# Calculate market-level indicators
# 1. VIX Proxy (Parkinson volatility)
spy_df['log_hl'] = np.log(spy_df['high'] / spy_df['low'])
spy_df['parkinson_vol'] = np.sqrt(spy_df['log_hl']**2 / (4 * np.log(2)))
spy_df['vix_proxy'] = spy_df['parkinson_vol'].rolling(20).mean() * np.sqrt(252) * 100

# 2. Trend Strength (ADX-like from price action)
spy_df['dm_plus'] = np.where(spy_df['high'] - spy_df['high'].shift(1) > spy_df['low'].shift(1) - spy_df['low'], 
                             np.maximum(spy_df['high'] - spy_df['high'].shift(1), 0), 0)
spy_df['dm_minus'] = np.where(spy_df['low'].shift(1) - spy_df['low'] > spy_df['high'] - spy_df['high'].shift(1),
                              np.maximum(spy_df['low'].shift(1) - spy_df['low'], 0), 0)
spy_df['tr'] = np.maximum(spy_df['high'] - spy_df['low'], 
                          np.maximum(abs(spy_df['high'] - spy_df['close'].shift(1)),
                                     abs(spy_df['low'] - spy_df['close'].shift(1))))
spy_df['atr'] = spy_df['tr'].rolling(14).mean()
spy_df['di_plus'] = 100 * spy_df['dm_plus'].rolling(14).mean() / spy_df['atr']
spy_df['di_minus'] = 100 * spy_df['dm_minus'].rolling(14).mean() / spy_df['atr']
spy_df['dx'] = 100 * abs(spy_df['di_plus'] - spy_df['di_minus']) / (spy_df['di_plus'] + spy_df['di_minus'])
spy_df['adx'] = spy_df['dx'].rolling(14).mean()

# 3. Market Regime Classification
spy_df['sma50'] = spy_df['close'].rolling(50).mean()
spy_df['sma200'] = spy_df['close'].rolling(200).mean()
spy_df['price_vs_50d'] = spy_df['close'] > spy_df['sma50']
spy_df['price_vs_200d'] = spy_df['close'] > spy_df['sma200']

# Classify regimes
def classify_regime(row):
    if row['price_vs_200d'] and row['adx'] > 25:
        return 'Strong Uptrend'
    elif row['price_vs_200d'] and row['adx'] <= 25:
        return 'Weak Uptrend'
    elif not row['price_vs_200d'] and row['adx'] > 25:
        return 'Strong Downtrend'
    elif not row['price_vs_200d'] and row['adx'] <= 25:
        return 'Weak Downtrend'
    else:
        return 'Undefined'

spy_df['market_regime'] = spy_df.apply(classify_regime, axis=1)

# 4. Volatility Regime
spy_df['vol_percentile'] = spy_df['vix_proxy'].rolling(252).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1])
spy_df['vol_regime'] = pd.cut(spy_df['vol_percentile'], 
                               bins=[0, 0.3, 0.7, 1.0],
                               labels=['Low Vol', 'Normal Vol', 'High Vol'])

print(f'\\n=== Market Regime Distribution ===')
print(spy_df['market_regime'].value_counts())

print(f'\\n=== Volatility Regime Distribution ===')
print(spy_df['vol_regime'].value_counts())

# Get COIN data for testing
cursor.execute('''
    SELECT t.date, t.close::float, ti.rsi_14
    FROM silver.unified_prices t
    JOIN gold.technical_indicators_calculated ti ON t.ticker = ti.ticker AND t.date = ti.date
    WHERE t.ticker = 'COIN' AND t.date BETWEEN '2022-06-01' AND '2024-12-31'
    ORDER BY t.date
''')
coin_data = cursor.fetchall()
coin_df = pd.DataFrame(coin_data, columns=['date', 'close', 'rsi_14'])

# Merge with market regimes
merged = coin_df.merge(spy_df[['date', 'market_regime', 'vol_regime', 'vix_proxy', 'adx']], on='date', how='inner')

print(f'\\n=== Testing Strategies with Market Regimes ===')

# Test strategies
strategies = [
    ('RSI<25 (baseline)', lambda r: r['rsi_14'] < 25, None, None),
    ('RSI<25 + Strong Uptrend', lambda r: r['rsi_14'] < 25, 'Strong Uptrend', None),
    ('RSI<25 + Weak Uptrend', lambda r: r['rsi_14'] < 25, 'Weak Uptrend', None),
    ('RSI<25 + Not Downtrend', lambda r: r['rsi_14'] < 25, ['Strong Uptrend', 'Weak Uptrend'], None),
    ('RSI<25 + Low Vol', lambda r: r['rsi_14'] < 25, None, 'Low Vol'),
    ('RSI<25 + Normal Vol', lambda r: r['rsi_14'] < 25, None, 'Normal Vol'),
]

print('\\n{:<40} {:<10} {:<10} {:<12}'.format('Strategy', 'Trades', 'Win%', 'Avg Return'))
print('-'*75)

for name, condition, regime_filter, vol_filter in strategies:
    trades = []
    for idx, row in merged.iterrows():
        if pd.notna(row['rsi_14']) and condition(row):
            # Check regime filter
            if regime_filter:
                if isinstance(regime_filter, list):
                    if row['market_regime'] not in regime_filter:
                        continue
                else:
                    if row['market_regime'] != regime_filter:
                        continue
            
            # Check vol filter
            if vol_filter and row['vol_regime'] != vol_filter:
                continue
            
            entry_idx = idx
            exit_idx = entry_idx + 10
            if exit_idx < len(merged):
                entry_price = row['close']
                exit_price = merged.iloc[exit_idx]['close']
                ret = ((exit_price - entry_price) / entry_price) * 100 - 0.1
                trades.append(ret)
    
    if len(trades) >= 5:
        win_rate = (pd.Series(trades) > 0).mean() * 100
        avg_ret = pd.Series(trades).mean()
        status = '✅' if win_rate >= 55 else '⚠️' if win_rate >= 50 else '❌'
        print(f'{status} {name:<38} {len(trades):<10} {win_rate:<10.1f} {avg_ret:<12.2f}')
    else:
        print(f'⚠️  {name:<38} {len(trades):<10} (insufficient)')

conn.close()

print('\\n' + '='*70)
print('EXPLORATION SUMMARY')
print('='*70)
print('\\n✅ Created market-level indicators from SPY:')
print('   1. VIX Proxy (Parkinson volatility)')
print('   2. ADX (Trend strength)')
print('   3. Market Regime (Strong/Weak Uptrend/Downtrend)')
print('   4. Volatility Regime (Low/Normal/High)')
print('\\nTested: Do these regimes improve COIN mean reversion?')
print('='*70)
