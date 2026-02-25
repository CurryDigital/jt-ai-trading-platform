#!/usr/bin/env python3
"""
EXPLORATION: Market Sentiment + Technical Strategies
Combine sentiment_mart with RSI/BB signals for enhanced alpha
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
print('EXPLORATION: Market Sentiment + Technical Strategies')
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

# Get market sentiment data
cursor.execute('''
    SELECT date, entity_name, sentiment_score, bullish_reasons, bearish_reasons
    FROM gold.sentiment_mart
    WHERE perspective = 'market' AND entity_name = 'US'
    ORDER BY date DESC
''')
sentiment_data = cursor.fetchall()

print(f'\\n=== Market Sentiment Data (US) ===')
print(f'Total records: {len(sentiment_data)}')

sentiment_df = pd.DataFrame(sentiment_data, columns=['date', 'entity_name', 'sentiment_score', 'bullish_reasons', 'bearish_reasons'])
print(f'\\nSentiment Score Range: {sentiment_df["sentiment_score"].min()} to {sentiment_df["sentiment_score"].max()}')
print(f'\\nLatest 5 sentiment readings:')
for _, row in sentiment_df.head(5).iterrows():
    print(f'  {row["date"]}: Score={row["sentiment_score"]}, Bullish={len(row["bullish_reasons"]) if row["bullish_reasons"] else 0} factors, Bearish={len(row["bearish_reasons"]) if row["bearish_reasons"] else 0} factors')

# Categorize sentiment
sentiment_df['sentiment_category'] = pd.cut(
    sentiment_df['sentiment_score'], 
    bins=[0, 0.3, 0.5, 0.7, 1.0],
    labels=['Very Bearish', 'Bearish', 'Bullish', 'Very Bullish']
)

print(f'\\n=== Sentiment Distribution ===')
print(sentiment_df['sentiment_category'].value_counts())

# Get stock data for testing (COIN as example)
cursor.execute('''
    SELECT t.date, t.close::float, ti.rsi_14
    FROM silver.unified_prices t
    JOIN gold.technical_indicators_calculated ti ON t.ticker = ti.ticker AND t.date = ti.date
    WHERE t.ticker = 'COIN' AND t.date BETWEEN '2022-06-01' AND '2024-12-31'
    ORDER BY t.date
''')
coin_data = cursor.fetchall()
coin_df = pd.DataFrame(coin_data, columns=['date', 'close', 'rsi_14'])

print(f'\\n=== COIN Data ===')
print(f'Records: {len(coin_df)}')

# Merge sentiment with stock data
# Need to match dates - sentiment has timestamp, stock has date
coin_df['date_only'] = pd.to_datetime(coin_df['date']).dt.date
sentiment_df['date_only'] = pd.to_datetime(sentiment_df['date']).dt.date

merged = coin_df.merge(sentiment_df[['date_only', 'sentiment_score', 'sentiment_category']], 
                       left_on='date_only', right_on='date_only', how='left')

print(f'\\n=== Merged Data ===')
print(f'Records with sentiment: {merged["sentiment_score"].notna().sum()}')

# Test strategies with sentiment filter
strategies = [
    ('RSI<25 (baseline)', lambda r: r['rsi_14'] < 25, None),
    ('RSI<25 + Bullish Sentiment', lambda r: r['rsi_14'] < 25, 'Bullish'),
    ('RSI<25 + Very Bullish', lambda r: r['rsi_14'] < 25, 'Very Bullish'),
    ('RSI<25 + Not Bearish', lambda r: r['rsi_14'] < 25, ['Bullish', 'Very Bullish']),
]

print('\\n=== BACKTEST RESULTS ===')
print('{:<40} {:<10} {:<10} {:<12}'.format('Strategy', 'Trades', 'Win%', 'Avg Return'))
print('-'*75)

for name, condition, sentiment_filter in strategies:
    trades = []
    for idx, row in merged.iterrows():
        if pd.notna(row['rsi_14']) and condition(row):
            # Check sentiment filter
            if sentiment_filter:
                if isinstance(sentiment_filter, list):
                    if row['sentiment_category'] not in sentiment_filter:
                        continue
                else:
                    if row['sentiment_category'] != sentiment_filter:
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
print('\\nTested: Combining market sentiment with RSI mean reversion on COIN')
print('\\nHypothesis: Bullish sentiment should improve mean reversion performance')
print('\\nIf sentiment filter improves win rate → New alpha source discovered')
print('If no improvement → Sentiment already priced in for this strategy')
print('='*70)
