#!/usr/bin/env python3
"""
REVALIDATION: JT's Existing Golden Strategies
Test on full universe with proper 3-tier methodology
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

def get_data(ticker):
    cursor.execute(f"SELECT date, close::float, volume::float, high::float, low::float, open::float FROM silver.unified_prices WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-20' ORDER BY date")
    data = cursor.fetchall()
    if len(data) < 200:
        return None
    df = pd.DataFrame(data, columns=['date', 'close', 'volume', 'high', 'low', 'open'])
    df['date'] = pd.to_datetime(df['date'])
    return df

# Strategies to revalidate
strategies = {
    'G001_COIN_RSI20': {
        'tickers': ['COIN'],
        'entry': lambda df, i: pd.notna(df['rsi'].iloc[i]) and df['rsi'].iloc[i] < 20 and df['close'].iloc[i] > df['sma20'].iloc[i],
        'exit_days': 10,
        'pt': 10, 'sl': -5,
        'claimed_wr': 100
    },
    'G002_MSTR_RSI20': {
        'tickers': ['MSTR'],
        'entry': lambda df, i: pd.notna(df['rsi'].iloc[i]) and df['rsi'].iloc[i] < 20 and df['close'].iloc[i] > df['sma20'].iloc[i],
        'exit_days': 10,
        'pt': 10, 'sl': -5,
        'claimed_wr': 87.5
    },
    'G003_MSTR_Momentum': {
        'tickers': ['MSTR'],
        'entry': lambda df, i: df['close'].iloc[i] > df['sma20'].iloc[i] and df['volume'].iloc[i] > df['vol_avg'].iloc[i] * 1.5,
        'exit_days': 15,
        'claimed_wr': 82.9
    },
    'G004_NVDA_BB_Squeeze': {
        'tickers': ['NVDA'],
        'entry': lambda df, i: df['bb_width'].iloc[i] < 0.05 and df['close'].iloc[i] > df['bb_upper'].iloc[i],
        'exit_days': 10,
        'claimed_wr': 77.8
    },
    'G005_MSFT_Momentum': {
        'tickers': ['MSFT'],
        'entry': lambda df, i: df['close'].iloc[i] > df['sma50'].iloc[i] and df['volume'].iloc[i] > df['vol_avg'].iloc[i] * 2.0,
        'exit_days': 15,
        'claimed_wr': 77.6
    },
    'G006_TSLA_Momentum': {
        'tickers': ['TSLA'],
        'entry': lambda df, i: df['close'].iloc[i] > df['sma20'].iloc[i] and df['volume'].iloc[i] > df['vol_avg'].iloc[i] * 2.0,
        'exit_days': 15,
        'claimed_wr': 77.6
    },
    'G007_NVDA_Momentum': {
        'tickers': ['NVDA'],
        'entry': lambda df, i: df['close'].iloc[i] > df['sma20'].iloc[i] and df['volume'].iloc[i] > df['vol_avg'].iloc[i] * 1.5,
        'exit_days': 15,
        'claimed_wr': 75.5
    },
    'G008_XLP_BB_Squeeze': {
        'tickers': ['COST', 'KO', 'PEP', 'PG', 'WMT'],  # XLP components
        'entry': lambda df, i: df['bb_width'].iloc[i] < 0.04 and df['close'].iloc[i] > df['bb_upper'].iloc[i],
        'exit_days': 10,
        'claimed_wr': 75.0
    },
    'G009_JNJ_BB_Squeeze': {
        'tickers': ['JNJ'],
        'entry': lambda df, i: df['bb_width'].iloc[i] < 0.05 and df['close'].iloc[i] > df['bb_upper'].iloc[i],
        'exit_days': 10,
        'claimed_wr': 75.0
    },
    'G010_Tech_3Day_Reversal': {
        'tickers': ['MSFT', 'AAPL', 'NVDA', 'QQQ'],
        'entry': lambda df, i: (df['close'].iloc[i-3] > df['close'].iloc[i-2] > df['close'].iloc[i-1] > df['close'].iloc[i] and 
                                pd.notna(df['rsi'].iloc[i]) and df['rsi'].iloc[i] < 30),
        'exit_days': 5,
        'pt': 5, 'sl': -3,
        'claimed_wr': 71.0
    },
    'G011_CVX_BB_Squeeze': {
        'tickers': ['CVX'],
        'entry': lambda df, i: df['bb_width'].iloc[i] < 0.05 and df['close'].iloc[i] > df['bb_upper'].iloc[i],
        'exit_days': 10,
        'claimed_wr': 71.4
    },
}

results = []

print('='*100)
print('REVALIDATION: JT EXISTING GOLDEN STRATEGIES')
print('='*100)
print(f"{'Strategy':<30} {'Ticker':<8} {'Claimed':<8} {'Test':<8} {'Validate':<8} {'Status':<12} {'n'}")
print('-'*100)

for strat_name, config in strategies.items():
    for ticker in config['tickers']:
        df = get_data(ticker)
        if df is None:
            results.append({
                'strategy': strat_name, 'ticker': ticker,
                'claimed': config['claimed_wr'], 'test_wr': 0, 'val_wr': 0,
                'n_trades': 0, 'status': 'NO DATA'
            })
            print(f"{strat_name:<30} {ticker:<8} {config['claimed_wr']:<8.1f} {'N/A':<8} {'N/A':<8} {'NO DATA':<12} 0")
            continue
        
        # Calculate indicators
        df['rsi'] = rsi(df['close'])
        df['sma20'] = df['close'].rolling(20).mean()
        df['sma50'] = df['close'].rolling(50).mean()
        df['vol_avg'] = df['volume'].rolling(20).mean()
        df['sma20_price'] = df['close'].rolling(20).mean()
        df['std20'] = df['close'].rolling(20).std()
        df['bb_upper'] = df['sma20_price'] + (df['std20'] * 2)
        df['bb_lower'] = df['sma20_price'] - (df['std20'] * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['sma20_price']
        
        # Split periods
        train = df[(df['date'] >= '2021-01-01') & (df['date'] <= '2022-12-31')]
        test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
        validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]
        
        # Test period
        test_trades = []
        start_idx = 60 if 'bb' in strat_name.lower() else 20
        exit_days = config.get('exit_days', 10)
        
        for i in range(start_idx, len(test) - exit_days):
            try:
                if config['entry'](test, i):
                    entry = test['close'].iloc[i]
                    exit_p = test['close'].iloc[i + exit_days]
                    ret = (exit_p - entry) / entry * 100 - 0.1
                    test_trades.append(ret)
            except:
                continue
        
        if len(test_trades) < 10:
            results.append({
                'strategy': strat_name, 'ticker': ticker,
                'claimed': config['claimed_wr'], 'test_wr': 0, 'val_wr': 0,
                'n_trades': len(test_trades), 'status': 'INSUFFICIENT DATA'
            })
            print(f"{strat_name:<30} {ticker:<8} {config['claimed_wr']:<8.1f} {'N/A':<8} {'N/A':<8} {'LOW N':<12} {len(test_trades)}")
            continue
        
        test_wr = (pd.Series(test_trades) > 0).mean() * 100
        
        # Validate period
        val_trades = []
        for i in range(start_idx, len(validate) - exit_days):
            try:
                if config['entry'](validate, i):
                    entry = validate['close'].iloc[i]
                    exit_p = validate['close'].iloc[i + exit_days]
                    ret = (exit_p - entry) / entry * 100 - 0.1
                    val_trades.append(ret)
            except:
                continue
        
        val_wr = 0
        if len(val_trades) >= 5:
            val_wr = (pd.Series(val_trades) > 0).mean() * 100
        
        # Status determination
        if test_wr >= 70 and val_wr >= 60:
            status = '🏆 GOLDEN'
        elif test_wr >= 60 and val_wr >= 55:
            status = '✅ VALIDATED'
        elif test_wr >= 55:
            status = '🟡 TIER 3'
        else:
            status = '❌ REJECT'
        
        # Check decay vs claimed
        decay = config['claimed_wr'] - test_wr
        
        results.append({
            'strategy': strat_name, 'ticker': ticker,
            'claimed': config['claimed_wr'], 'test_wr': test_wr, 'val_wr': val_wr,
            'n_trades': len(test_trades), 'status': status, 'decay': decay
        })
        
        print(f"{strat_name:<30} {ticker:<8} {config['claimed_wr']:<8.1f} {test_wr:<8.1f} {val_wr:<8.1f} {status:<12} {len(test_trades)}")

conn.close()

print('\n' + '='*100)
print('SUMMARY BY STATUS')
print('='*100)

golden = [r for r in results if '🏆' in r['status']]
validated = [r for r in results if '✅' in r['status']]
tier3 = [r for r in results if '🟡' in r['status']]
rejected = [r for r in results if '❌' in r['status']]

print(f"\n🏆 GOLDEN (Test ≥70%, Val ≥60%): {len(golden)} strategies")
for r in golden:
    print(f"   {r['strategy']} {r['ticker']}: {r['test_wr']:.1f}% (claimed {r['claimed']:.1f}%)")

print(f"\n✅ VALIDATED (Test ≥60%, Val ≥55%): {len(validated)} strategies")
for r in validated:
    print(f"   {r['strategy']} {r['ticker']}: {r['test_wr']:.1f}% (claimed {r['claimed']:.1f}%)")

print(f"\n🟡 TIER 3 (Test ≥55%): {len(tier3)} strategies")
for r in tier3:
    print(f"   {r['strategy']} {r['ticker']}: {r['test_wr']:.1f}%")

print(f"\n❌ REJECT (Test <55%): {len(rejected)} strategies")
for r in rejected:
    print(f"   {r['strategy']} {r['ticker']}: {r['test_wr']:.1f}% (claimed {r['claimed']:.1f}%, decay {r['decay']:.1f}%)")

print('\n' + '='*100)
print('DECAY ANALYSIS (Claimed vs Actual)')
print('='*100)
high_decay = [r for r in results if r.get('decay', 0) > 20 and r['test_wr'] > 0]
if high_decay:
    print("\n⚠️  HIGH DECAY (>20% difference from claimed):")
    for r in high_decay:
        print(f"   {r['strategy']} {r['ticker']}: Claimed {r['claimed']:.1f}% → Actual {r['test_wr']:.1f}% (decay {r['decay']:.1f}%)")
else:
    print("\n✅ No significant decay detected")

print('\n' + '='*100)
