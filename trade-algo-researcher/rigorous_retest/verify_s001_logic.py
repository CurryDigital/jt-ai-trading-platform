#!/usr/bin/env python3
"""
RIGOROUS TEST: S001-Candidate — RSI Extreme Mean Reversion
RSI(14) < 25, Hold 10 days
NO additional filters — simple single condition
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np

print('='*100)
print('RIGOROUS TEST: S001-Candidate (RSI < 25, Hold 10 days)')
print('VERIFYING LOGIC BEFORE FULL UNIVERSE TEST')
print('='*100)

# Step 1: Test on single ticker with full trace
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

ticker = '1398.HK'  # ICBC — same ticker I tested before

cursor.execute(f"""
    SELECT date, close::float 
    FROM silver.unified_prices 
    WHERE ticker = '{ticker}' AND date BETWEEN '2023-01-01' AND '2024-12-31'
    ORDER BY date
""")
data = cursor.fetchall()

print(f'\nStep 1: Loading data for {ticker}')
print(f'Data points: {len(data)}')

df = pd.DataFrame(data, columns=['date', 'close'])
df['date'] = pd.to_datetime(df['date'])

# Calculate RSI
delta = df['close'].diff()
gain = delta.where(delta > 0, 0).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
df['rsi'] = 100 - (100 / (1 + rs))

print(f'\nStep 2: RSI calculated')
print(f'Sample data (last 10 rows):')
print(df[['date', 'close', 'rsi']].tail(10))

# Find signals (RSI < 25 only — no other conditions)
df_clean = df.dropna()
signals = df_clean[df_clean['rsi'] < 25]

print(f'\nStep 3: Signal detection')
print(f'Total days with RSI < 25: {len(signals)}')

if len(signals) > 0:
    print(f'\nFirst 5 signals:')
    print(signals[['date', 'close', 'rsi']].head())
    
    # Calculate returns for first few signals
    print(f'\nStep 4: Return calculation for first 5 signals')
    for idx, row in signals.head().iterrows():
        if idx + 10 < len(df_clean):
            entry = row['close']
            exit_price = df_clean.iloc[idx + 10]['close']
            ret = (exit_price - entry) / entry * 100 - 0.1
            print(f"  {row['date'].strftime('%Y-%m-%d')}: Entry={entry:.2f}, Exit={exit_price:.2f}, Return={ret:.2f}%")

print('\n' + '='*100)
print('VERIFICATION: Does this logic make sense?')
print(f'- Clear single condition: RSI < 25')
print(f'- Produces {len(signals)} signals (sufficient for testing)')
print(f'- No compound conditions that conflict')
print('='*100)

conn.close()
