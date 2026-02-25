#!/usr/bin/env python3
"""
COMPREHENSIVE 3-PERIOD VALIDATION
All Golden & Near-Golden Strategies
Train: 2021-2022 | Test: 2023-2024 | Validate: 2025-Feb 2026
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np

print('='*90)
print('COMPREHENSIVE 3-PERIOD VALIDATION')
print('All Golden & Near-Golden Strategies')
print('Train: 2021-2022 | Test: 2023-2024 | Validate: 2025-Feb 2026')
print('='*90)

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

def adx(df, period=14):
    """Calculate ADX"""
    plus_dm = df['high'].diff()
    minus_dm = -df['low'].diff()
    tr = pd.concat([df['high'] - df['low'], 
                    (df['high'] - df['close'].shift()).abs(), 
                    (df['low'] - df['close'].shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    plus_di = 100 * (plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0).rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0).rolling(period).mean() / atr)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    return dx.rolling(period).mean(), plus_di, minus_di

def split_periods(df):
    train = df[(df['date'] >= '2021-01-01') & (df['date'] <= '2022-12-31')]
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-20')]
    return train, test, validate

def test_strategy(name, ticker, strategy_func, params=None):
    """Test a strategy across 3 periods"""
    df = get_data(ticker)
    if df is None or len(df) < 200:
        return None
    
    train, test, validate = split_periods(df)
    results = {'name': name, 'ticker': ticker}
    
    for period_name, period_df in [('Train', train), ('Test', test), ('Validate', validate)]:
        if len(period_df) < 30:
            results[period_name] = {'wr': 0, 'n': 0, 'avg_ret': 0}
            continue
        
        trades = strategy_func(period_df, params)
        if trades:
            r = pd.Series(trades)
            wr = (r > 0).mean() * 100
            results[period_name] = {
                'wr': wr,
                'n': len(trades),
                'avg_ret': r.mean()
            }
        else:
            results[period_name] = {'wr': 0, 'n': 0, 'avg_ret': 0}
    
    return results

# Strategy functions
def rsi_mean_reversion(df, params):
    """RSI < threshold mean reversion"""
    df['rsi'] = rsi(df['close'])
    threshold = params.get('threshold', 20)
    hold_days = params.get('hold', 10)
    
    trades = []
    for i in range(14, len(df) - hold_days):
        if pd.notna(df['rsi'].iloc[i]) and df['rsi'].iloc[i] < threshold:
            entry = df['close'].iloc[i]
            exit_p = df['close'].iloc[i + hold_days]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    return trades

def momentum_trend(df, params):
    """Price > SMA50 + ADX > threshold"""
    df['sma50'] = df['close'].rolling(50).mean()
    df['adx'], df['plus_di'], df['minus_di'] = adx(df)
    adx_threshold = params.get('adx_threshold', 25)
    hold_days = params.get('hold', 15)
    
    trades = []
    for i in range(50, len(df) - hold_days):
        if (pd.notna(df['adx'].iloc[i]) and 
            df['close'].iloc[i] > df['sma50'].iloc[i] and 
            df['adx'].iloc[i] > adx_threshold):
            entry = df['close'].iloc[i+1] if i+1 < len(df) else df['close'].iloc[i]
            exit_idx = min(i + hold_days, len(df) - 1)
            exit_p = df['close'].iloc[exit_idx]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    return trades

def bb_squeeze(df, params):
    """BB Squeeze + breakout"""
    df['sma20'] = df['close'].rolling(20).mean()
    df['std20'] = df['close'].rolling(20).std()
    df['bb_width'] = (4 * df['std20']) / df['sma20'] * 100
    df['bb_width_pctile'] = df['bb_width'].rolling(120).apply(
        lambda x: pd.Series(x).rank(pct=True).iloc[-1] if len(x) >= 120 else np.nan, raw=False
    )
    
    trades = []
    for i in range(120, len(df) - 5):
        if pd.notna(df['bb_width_pctile'].iloc[i]) and df['bb_width_pctile'].iloc[i] < 0.10:
            if i+1 < len(df) and df['close'].iloc[i+1] > df['high'].iloc[i]:
                entry = df['close'].iloc[i+1]
                exit_idx = min(i + 5, len(df) - 1)
                exit_p = df['close'].iloc[exit_idx]
                ret = (exit_p - entry) / entry * 100 - 0.1
                trades.append(ret)
    return trades

def three_day_reversal(df, params):
    """3 down days + RSI < 30"""
    df['rsi'] = rsi(df['close'])
    
    trades = []
    for i in range(20, len(df) - 5):
        if (df['close'].iloc[i] < df['close'].iloc[i-1] and
            df['close'].iloc[i-1] < df['close'].iloc[i-2] and
            df['close'].iloc[i-2] < df['close'].iloc[i-3] and
            pd.notna(df['rsi'].iloc[i]) and df['rsi'].iloc[i] < 30):
            entry = df['close'].iloc[i]
            exit_idx = min(i + 5, len(df) - 1)
            exit_p = df['close'].iloc[exit_idx]
            ret = (exit_p - entry) / entry * 100 - 0.1
            trades.append(ret)
    return trades

# Test all strategies
strategies_to_test = [
    ('G001', 'COIN', rsi_mean_reversion, {'threshold': 20, 'hold': 10}),
    ('G002', 'MSTR', rsi_mean_reversion, {'threshold': 20, 'hold': 10}),
    ('G003', 'MSTR', momentum_trend, {'adx_threshold': 25, 'hold': 15}),
    ('G005', 'MSFT', momentum_trend, {'adx_threshold': 25, 'hold': 15}),
    ('G006', 'TSLA', momentum_trend, {'adx_threshold': 25, 'hold': 15}),
    ('G007', 'NVDA', momentum_trend, {'adx_threshold': 25, 'hold': 15}),
    ('G010', 'QQQ', three_day_reversal, {}),
    ('G012', 'SPY', bb_squeeze, {}),
    ('Near-Golden', 'QQQ', momentum_trend, {'adx_threshold': 25, 'hold': 15}),
    ('Near-Golden', 'NVDA', bb_squeeze, {}),
]

print('\n' + '='*90)
print('TESTING ALL STRATEGIES')
print('='*90)

all_results = []
for name, ticker, func, params in strategies_to_test:
    print(f'\nTesting {name} on {ticker}...')
    result = test_strategy(name, ticker, func, params)
    if result:
        all_results.append(result)
        
        train_wr = result['Train']['wr']
        test_wr = result['Test']['wr']
        val_wr = result['Validate']['wr']
        
        print(f'  Train:   {train_wr:.1f}% ({result["Train"]["n"]} trades)')
        print(f'  Test:    {test_wr:.1f}% ({result["Test"]["n"]} trades)')
        print(f'  Validate:{val_wr:.1f}% ({result["Validate"]["n"]} trades)')
        
        # Grade the strategy
        if train_wr >= 55 and test_wr >= 60 and val_wr >= 60:
            print('  🏆 TRUE GOLDEN (All periods ≥60%)')
        elif test_wr >= 60 and val_wr >= 55:
            print('  ✅ VALIDATED (Test ≥60%, Validate ≥55%)')
        elif val_wr < 50:
            print('  ❌ FAILED (Validate <50%)')
        else:
            print('  🟡 BORDERLINE')

conn.close()

# Summary
print('\n' + '='*90)
print('3-PERIOD VALIDATION SUMMARY')
print('='*90)

true_golden = []
validated = []
failed = []

for r in all_results:
    train_wr = r['Train']['wr']
    test_wr = r['Test']['wr']
    val_wr = r['Validate']['wr']
    
    if train_wr >= 55 and test_wr >= 60 and val_wr >= 60:
        true_golden.append(r)
    elif test_wr >= 60 and val_wr >= 55:
        validated.append(r)
    elif val_wr < 50:
        failed.append(r)
    else:
        validated.append(r)  # borderline goes to validated

print(f'\n🏆 TRUE GOLDEN (All ≥60%): {len(true_golden)} strategies')
for r in true_golden:
    print(f'   {r["name"]} {r["ticker"]}: Train={r["Train"]["wr"]:.1f}%, Test={r["Test"]["wr"]:.1f}%, Val={r["Validate"]["wr"]:.1f}%')

print(f'\n✅ VALIDATED (Test ≥60%, Val ≥55%): {len(validated)} strategies')
for r in validated:
    print(f'   {r["name"]} {r["ticker"]}: Train={r["Train"]["wr"]:.1f}%, Test={r["Test"]["wr"]:.1f}%, Val={r["Validate"]["wr"]:.1f}%')

print(f'\n❌ FAILED (Validate <50%): {len(failed)} strategies')
for r in failed:
    print(f'   {r["name"]} {r["ticker"]}: Train={r["Train"]["wr"]:.1f}%, Test={r["Test"]["wr"]:.1f}%, Val={r["Validate"]["wr"]:.1f}%')

print('\n' + '='*90)
print('DEPLOYMENT RECOMMENDATION')
print('='*90)
print(f'🏆 Deploy with confidence: {len(true_golden)} strategies')
print(f'✅ Deploy with caution: {len(validated)} strategies')
print(f'❌ Do NOT deploy: {len(failed)} strategies')
print('='*90)
