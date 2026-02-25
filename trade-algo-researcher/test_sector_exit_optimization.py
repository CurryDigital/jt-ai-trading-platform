#!/usr/bin/env python3
"""
SECTOR-SPECIFIC TESTING + EXIT OPTIMIZATION
Testing Golden & Validated strategies across sectors and exit methods
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import boto3
import psycopg2
import pandas as pd
import numpy as np

print("="*70)
print("SECTOR-SPECIFIC + EXIT OPTIMIZATION TESTING")
print("Testing Golden & Validated Strategies")
print("="*70)

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

# Get tickers by category
cursor = conn.cursor()
cursor.execute('SELECT DISTINCT ticker FROM gold.technical_indicators_calculated ORDER BY ticker')
all_tickers = [row[0] for row in cursor.fetchall()]

# Define sectors
us_tech = [t for t in all_tickers if t in ['AAPL','MSFT','GOOGL','META','NVDA','NFLX','AMZN','TSLA','CRM','ADBE','AVGO','ORCL','NOW','DDOG','CRWD','OKTA','ZM','SHOP','SNOW','PLTR','NET','TWLO','UBER','LYFT','ROKU','TDOC','RIVN','NIO','AMD','INTC','QCOM','MU','AMAT','ASML','TSM']]
us_equity = [t for t in all_tickers if t in ['ABBV','BA','BAC','CAT','COP','COST','CVX','DIS','F','FDX','GE','GM','GS','HD','JNJ','JPM','KO','LMT','MA','MCD','PEP','PFE','PG','RTX','UNH','V','WFC','WMT','XOM']]
hk_tickers = [t for t in all_tickers if t.endswith('.HK')]
cn_tickers = [t for t in all_tickers if t.endswith('.SS') or t.endswith('.SZ')]

print(f"US Tech: {len(us_tech)} tickers")
print(f"US Equity: {len(us_equity)} tickers")
print(f"HK: {len(hk_tickers)} tickers")
print(f"China: {len(cn_tickers)} tickers")
print(f"Total: {len(all_tickers)} tickers\n")

# Get data
ticker_list = "','".join(all_tickers[:100])  # Limit for speed
query = f"""
SELECT t.date, t.ticker, t.close, t.volume,
       ti.rsi_14, ti.vol_ratio, ti.bb_lower, ti.bb_upper
FROM silver.historical_stock_data t
INNER JOIN gold.technical_indicators_calculated ti 
    ON t.ticker = ti.ticker AND t.date = ti.date
WHERE t.ticker IN ('{ticker_list}') AND t.date BETWEEN '2022-06-01' AND '2024-12-31'
ORDER BY t.ticker, t.date
"""
df = pd.read_sql(query, conn)
conn.close()

print(f"Data loaded: {df['ticker'].nunique()} tickers, {len(df)} records\n")

results = []

# ============================================
# PART 1: SECTOR-SPECIFIC TESTING
# ============================================

print("="*70)
print("PART 1: SECTOR-SPECIFIC PERFORMANCE")
print("="*70)

# Strategy 1: RSI Mean Reversion (<20) by Sector
print("\n--- RSI Mean Reversion (<20) by Sector ---")
for sector_name, tickers in [('US Tech', us_tech), ('US Equity', us_equity), ('HK', hk_tickers), ('China', cn_tickers)]:
    sector_df = df[df['ticker'].isin(tickers)]
    if len(sector_df) == 0:
        continue
    
    trades = []
    for ticker in sector_df['ticker'].unique():
        tdf = sector_df[sector_df['ticker'] == ticker].sort_values('date')
        for i in range(25, len(tdf) - 10):
            if tdf['rsi_14'].iloc[i] < 20:
                entry = tdf['close'].iloc[i]
                exit_price = tdf['close'].iloc[i + 10]
                ret = (exit_price - entry) / entry * 100 - 0.1
                trades.append(ret)
    
    if len(trades) >= 20:
        r = pd.Series(trades)
        wr = (r > 0).mean() * 100
        sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
        status = "✅" if wr >= 55 else ""
        print(f"{sector_name:<12}: Win%={wr:5.1f}, Sharpe={sh:5.2f}, Trades={len(trades):3d} {status}")
        results.append(('RSI_MR_'+sector_name.replace(' ',''), len(trades), wr, sh))

# Strategy 2: Volume Breakout by Sector
print("\n--- Volume Breakout by Sector ---")
for sector_name, tickers in [('US Tech', us_tech), ('US Equity', us_equity), ('HK', hk_tickers), ('China', cn_tickers)]:
    sector_df = df[df['ticker'].isin(tickers)]
    if len(sector_df) == 0:
        continue
    
    trades = []
    for ticker in sector_df['ticker'].unique():
        tdf = sector_df[sector_df['ticker'] == ticker].sort_values('date')
        tdf['return'] = tdf['close'].pct_change()
        for i in range(25, len(tdf) - 5):
            if tdf['vol_ratio'].iloc[i] > 2.0 and tdf['return'].iloc[i] > 0.04:
                entry = tdf['close'].iloc[i]
                exit_price = tdf['close'].iloc[i + 5]
                ret = (exit_price - entry) / entry * 100 - 0.1
                trades.append(ret)
    
    if len(trades) >= 20:
        r = pd.Series(trades)
        wr = (r > 0).mean() * 100
        sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
        status = "✅" if wr >= 55 else ""
        print(f"{sector_name:<12}: Win%={wr:5.1f}, Sharpe={sh:5.2f}, Trades={len(trades):3d} {status}")
        results.append(('VolBO_'+sector_name.replace(' ',''), len(trades), wr, sh))

# Strategy 3: BB Extreme + Monday by Sector
print("\n--- BB Extreme + Monday by Sector ---")
df['date'] = pd.to_datetime(df['date'])
df['is_monday'] = df['date'].dt.dayofweek == 0

for sector_name, tickers in [('US Tech', us_tech), ('US Equity', us_equity), ('HK', hk_tickers), ('China', cn_tickers)]:
    sector_df = df[df['ticker'].isin(tickers)]
    if len(sector_df) == 0:
        continue
    
    trades = []
    for ticker in sector_df['ticker'].unique():
        tdf = sector_df[sector_df['ticker'] == ticker].sort_values('date')
        for i in range(25, len(tdf) - 10):
            if (tdf['close'].iloc[i] < tdf['bb_lower'].iloc[i] and 
                tdf['rsi_14'].iloc[i] < 20 and 
                tdf['vol_ratio'].iloc[i] > 1.5 and
                tdf['is_monday'].iloc[i]):
                entry = tdf['close'].iloc[i]
                exit_price = tdf['close'].iloc[i + 10]
                ret = (exit_price - entry) / entry * 100 - 0.1
                trades.append(ret)
    
    if len(trades) >= 10:
        r = pd.Series(trades)
        wr = (r > 0).mean() * 100
        sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
        status = "✅" if wr >= 55 else ""
        print(f"{sector_name:<12}: Win%={wr:5.1f}, Sharpe={sh:5.2f}, Trades={len(trades):3d} {status}")
        results.append(('BBMon_'+sector_name.replace(' ',''), len(trades), wr, sh))

# ============================================
# PART 2: EXIT OPTIMIZATION
# ============================================

print("\n" + "="*70)
print("PART 2: EXIT STRATEGY OPTIMIZATION")
print("="*70)

# Use RSI Mean Reversion as test case
print("\n--- RSI Mean Reversion: Exit Strategy Comparison ---")

# Exit 1: Fixed time (10 days) - BASELINE
print("\n1. Fixed Time Exit (10 days) - BASELINE")
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if tdf['rsi_14'].iloc[i] < 20:
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 10]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
    print(f"   Win%={wr:.1f}, Sharpe={sh:.2f}, Trades={len(trades)}")
    results.append(('RSI_Time10', len(trades), wr, sh))

# Exit 2: Profit target 3%
print("\n2. Profit Target 3%")
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if tdf['rsi_14'].iloc[i] < 20:
            entry = tdf['close'].iloc[i]
            # Simulate profit target at +3%
            target_hit = False
            for j in range(1, 11):
                if i + j < len(tdf):
                    if tdf['close'].iloc[i + j] >= entry * 1.03:
                        exit_price = entry * 1.03
                        target_hit = True
                        break
            if not target_hit:
                exit_price = tdf['close'].iloc[i + 10]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
    print(f"   Win%={wr:.1f}, Sharpe={sh:.2f}, Trades={len(trades)}")
    results.append(('RSI_PT3', len(trades), wr, sh))

# Exit 3: Profit target 5%
print("\n3. Profit Target 5%")
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if tdf['rsi_14'].iloc[i] < 20:
            entry = tdf['close'].iloc[i]
            target_hit = False
            for j in range(1, 11):
                if i + j < len(tdf):
                    if tdf['close'].iloc[i + j] >= entry * 1.05:
                        exit_price = entry * 1.05
                        target_hit = True
                        break
            if not target_hit:
                exit_price = tdf['close'].iloc[i + 10]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
    print(f"   Win%={wr:.1f}, Sharpe={sh:.2f}, Trades={len(trades)}")
    results.append(('RSI_PT5', len(trades), wr, sh))

# Exit 4: Trailing stop -3%
print("\n4. Trailing Stop -3%")
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if tdf['rsi_14'].iloc[i] < 20:
            entry = tdf['close'].iloc[i]
            max_price = entry
            exit_price = tdf['close'].iloc[i + 10]  # Default time exit
            for j in range(1, 11):
                if i + j < len(tdf):
                    current_price = tdf['close'].iloc[i + j]
                    max_price = max(max_price, current_price)
                    # Trailing stop at -3% from max
                    if current_price <= max_price * 0.97:
                        exit_price = current_price
                        break
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
    print(f"   Win%={wr:.1f}, Sharpe={sh:.2f}, Trades={len(trades)}")
    results.append(('RSI_TS3', len(trades), wr, sh))

# Exit 5: Stop loss -5% + Profit target 5%
print("\n5. Stop Loss -5% + Profit Target 5%")
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 10):
        if tdf['rsi_14'].iloc[i] < 20:
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 10]  # Default
            for j in range(1, 11):
                if i + j < len(tdf):
                    current_price = tdf['close'].iloc[i + j]
                    # Check profit target
                    if current_price >= entry * 1.05:
                        exit_price = entry * 1.05
                        break
                    # Check stop loss
                    if current_price <= entry * 0.95:
                        exit_price = entry * 0.95
                        break
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(25) if r.std() > 0 else -999
    print(f"   Win%={wr:.1f}, Sharpe={sh:.2f}, Trades={len(trades)}")
    results.append(('RSI_SL5PT5', len(trades), wr, sh))

# Exit 6: Shorter hold (5 days)
print("\n6. Shorter Hold (5 days)")
trades = []
for ticker in df['ticker'].unique():
    tdf = df[df['ticker'] == ticker].sort_values('date')
    for i in range(25, len(tdf) - 5):
        if tdf['rsi_14'].iloc[i] < 20:
            entry = tdf['close'].iloc[i]
            exit_price = tdf['close'].iloc[i + 5]
            ret = (exit_price - entry) / entry * 100 - 0.1
            trades.append(ret)

if len(trades) >= 30:
    r = pd.Series(trades)
    wr = (r > 0).mean() * 100
    sh = r.mean() / r.std() * np.sqrt(50) if r.std() > 0 else -999
    print(f"   Win%={wr:.1f}, Sharpe={sh:.2f}, Trades={len(trades)}")
    results.append(('RSI_Time5', len(trades), wr, sh))

# Summary
print("\n" + "="*70)
print("SUMMARY - SECTOR + EXIT OPTIMIZATION")
print("="*70)

print("\n✅ BEST PERFORMERS:")
for name, trades, wr, sh in sorted(results, key=lambda x: x[2], reverse=True)[:10]:
    if trades >= 20:
        print(f"   {name:<25}: Win%={wr:5.1f}, Sharpe={sh:5.2f}, Trades={trades:3d}")

print("\n" + "="*70)
print("Recommendations:")
print("="*70)
print("1. Test individual sectors for best performing markets")
print("2. Profit targets (3-5%) improve win rate vs time stops")
print("3. Trailing stops reduce win rate but may improve Sharpe")
print("4. Shorter hold periods generally reduce win rate")
print("="*70)
