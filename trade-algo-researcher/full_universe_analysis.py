#!/usr/bin/env python3
"""
FULL UNIVERSE ANALYSIS: All available tickers with proper industry classification
NO CHERRY-PICKING — Report ALL results
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

# Get ALL tickers that actually have data
cursor.execute("""
    SELECT DISTINCT ticker, COUNT(*) as cnt 
    FROM silver.unified_prices 
    WHERE date >= '2021-01-01'
    GROUP BY ticker
    HAVING COUNT(*) >= 500
    ORDER BY ticker
""")
all_tickers = [(r[0], r[1]) for r in cursor.fetchall()]

print('='*100)
print('FULL UNIVERSE ANALYSIS: Testing ALL available tickers')
print(f'Total tickers with sufficient data: {len(all_tickers)}')
print('='*100)

# Proper industry classification based on actual business
industry_map = {
    # HK BANKS - Deposit taking institutions
    '0005.HK': 'HK_Banks', '0011.HK': 'HK_Banks', '0939.HK': 'HK_Banks',
    '1398.HK': 'HK_Banks', '2388.HK': 'HK_Banks', '3328.HK': 'HK_Banks',
    '3988.HK': 'HK_Banks', '3968.HK': 'HK_Banks', '1658.HK': 'HK_Banks',
    '3868.HK': 'HK_Banks',
    
    # HK PROPERTY - Real estate developers
    '0001.HK': 'HK_Property', '0012.HK': 'HK_Property', '0016.HK': 'HK_Property',
    '0688.HK': 'HK_Property', '1109.HK': 'HK_Property', '1113.HK': 'HK_Property',
    '0101.HK': 'HK_Property', '0197.HK': 'HK_Property', '0040.HK': 'HK_Property',
    '0083.HK': 'HK_Property',  # Sino Land - property developer
    
    # HK UTILITIES - Electricity, gas, water
    '0002.HK': 'HK_Utilities',  # CLP - electricity
    '0003.HK': 'HK_Utilities',  # HK Gas
    '0006.HK': 'HK_Utilities',  # Power Assets
    '0836.HK': 'HK_Utilities',  # China Resources Power
    
    # HK INSURANCE
    '1299.HK': 'HK_Insurance',  # AIA
    '2318.HK': 'HK_Insurance',  # Ping An
    '2628.HK': 'HK_Insurance',  # China Life
    
    # HK TECH/INTERNET
    '0700.HK': 'HK_Tech', '9988.HK': 'HK_Tech', '3690.HK': 'HK_Tech',
    '9618.HK': 'HK_Tech', '1024.HK': 'HK_Tech', '1810.HK': 'HK_Tech',
    '2015.HK': 'HK_Tech', '9888.HK': 'HK_Tech', '9999.HK': 'HK_Tech',
    '9866.HK': 'HK_Tech', '2382.HK': 'HK_Tech',  # Sunny Optical
    
    # HK ENERGY
    '0883.HK': 'HK_Energy', '0386.HK': 'HK_Energy', '0857.HK': 'HK_Energy',
    '1088.HK': 'HK_Energy', '1171.HK': 'HK_Energy', '2688.HK': 'HK_Energy',
    
    # HK CONGLOMERATES
    '0008.HK': 'HK_Conglomerate',  # PCCW
    '0017.HK': 'HK_Conglomerate',  # New World Development
    
    # HK TRANSPORT/INFRA
    '0066.HK': 'HK_Transport',  # MTR
    '0144.HK': 'HK_Transport',  # China Merchants Port
    '0316.HK': 'HK_Transport',  # OOIL
    '0636.HK': 'HK_Transport',  # Kerry Logistics
    
    # HK CONSUMER/STAPLES
    '0151.HK': 'HK_Consumer',  # Want Want
    '0168.HK': 'HK_Consumer',  # Tsingtao
    '0506.HK': 'HK_Consumer',  # China Foods
    '1044.HK': 'HK_Consumer',  # Hengan
    '1876.HK': 'HK_Consumer',  # Budweiser APAC
    '1929.HK': 'HK_Consumer',  # Chow Tai Fook
    '2020.HK': 'HK_Consumer',  # Anta
    '2313.HK': 'HK_Consumer',  # Shenzhou
    '2319.HK': 'HK_Consumer',  # Mengniu
    '2331.HK': 'HK_Consumer',  # Li Ning
    '6862.HK': 'HK_Consumer',  # Haidilao
    '9633.HK': 'HK_Consumer',  # Nongfu Spring
    '9992.HK': 'HK_Consumer',  # Pop Mart
    
    # HK TELECOM
    '0762.HK': 'HK_Telecom',  # China Unicom
    '0788.HK': 'HK_Telecom',  # China Tower
    '0941.HK': 'HK_Telecom',  # China Mobile
    
    # HK HEALTHCARE/BIOTECH
    '2269.HK': 'HK_Healthcare',  # WuXi Biologics
    '1093.HK': 'HK_Healthcare',  # CSPC Pharma
    '1177.HK': 'HK_Healthcare',  # Sino Biopharm
    
    # HK GAMING/HOSPITALITY
    '1928.HK': 'HK_Gaming',  # Sands China
    
    # HK FINANCIAL SERVICES (non-bank)
    '0388.HK': 'HK_Financial',  # HKEX
    '1359.HK': 'HK_Financial',  # China Cinda
}

def rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def test_s001_rsi_mr(ticker):
    """Test S001 RSI Mean Reversion on single ticker"""
    cursor.execute(f"""
        SELECT date, close::float 
        FROM silver.unified_prices 
        WHERE ticker = '{ticker}' AND date BETWEEN '2021-01-01' AND '2026-02-25'
        ORDER BY date
    """)
    data = cursor.fetchall()
    
    if len(data) < 200:
        return {'status': 'INSUFFICIENT_DATA', 'test_wr': 0, 'val_wr': 0, 'test_n': 0}
    
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    df['rsi'] = rsi(df['close'])
    df['sma20'] = df['close'].rolling(20).mean()
    
    # Test period: 2023-2024
    test = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2024-12-31')]
    test_trades = []
    for i in range(20, len(test) - 10):
        if (pd.notna(test['rsi'].iloc[i]) and test['rsi'].iloc[i] < 30 and
            pd.notna(test['sma20'].iloc[i]) and test['close'].iloc[i] > test['sma20'].iloc[i]):
            entry = test['close'].iloc[i]
            exit_p = test['close'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            test_trades.append(ret)
    
    if len(test_trades) < 10:
        return {'status': 'INSUFFICIENT_TRADES', 'test_wr': 0, 'val_wr': 0, 'test_n': len(test_trades)}
    
    test_wr = (pd.Series(test_trades) > 0).mean() * 100
    
    # Validate period: 2025+
    validate = df[(df['date'] >= '2025-01-01') & (df['date'] <= '2026-02-25')]
    val_trades = []
    for i in range(20, len(validate) - 10):
        if (pd.notna(validate['rsi'].iloc[i]) and validate['rsi'].iloc[i] < 30 and
            pd.notna(validate['sma20'].iloc[i]) and validate['close'].iloc[i] > validate['sma20'].iloc[i]):
            entry = validate['close'].iloc[i]
            exit_p = validate['close'].iloc[i + 10]
            ret = (exit_p - entry) / entry * 100 - 0.1
            val_trades.append(ret)
    
    val_wr = (pd.Series(val_trades) > 0).mean() * 100 if len(val_trades) >= 5 else 0
    
    # Determine status
    if test_wr >= 60 and val_wr >= 55:
        status = 'GOLDEN'
    elif test_wr >= 60 and val_wr >= 50:
        status = 'VALIDATED'
    elif test_wr >= 55:
        status = 'MARGINAL'
    else:
        status = 'FAIL'
    
    return {
        'status': status,
        'test_wr': test_wr,
        'val_wr': val_wr,
        'test_n': len(test_trades),
        'val_n': len(val_trades)
    }

# Test ALL tickers and group by industry
results_by_industry = {}

for ticker, count in all_tickers:
    # Determine industry
    industry = industry_map.get(ticker, 'Other')
    
    # Test the ticker
    result = test_s001_rsi_mr(ticker)
    result['ticker'] = ticker
    result['count'] = count
    
    if industry not in results_by_industry:
        results_by_industry[industry] = []
    results_by_industry[industry].append(result)

# Print results by industry
print('\n' + '='*100)
print('RESULTS BY INDUSTRY (S001 RSI Mean Reversion)')
print('='*100)

for industry in sorted(results_by_industry.keys()):
    tickers = results_by_industry[industry]
    golden = [t for t in tickers if t['status'] == 'GOLDEN']
    validated = [t for t in tickers if t['status'] == 'VALIDATED']
    marginal = [t for t in tickers if t['status'] == 'MARGINAL']
    failed = [t for t in tickers if t['status'] == 'FAIL']
    insufficient = [t for t in tickers if 'INSUFFICIENT' in t['status']]
    
    print(f'\n{industry}: {len(tickers)} tickers tested')
    print('-'*100)
    
    for t in tickers:
        if t['status'] == 'GOLDEN':
            print(f"  🏆 {t['ticker']}: {t['test_wr']:.1f}% / {t['val_wr']:.1f}% (n={t['test_n']})")
        elif t['status'] == 'VALIDATED':
            print(f"  ✅ {t['ticker']}: {t['test_wr']:.1f}% / {t['val_wr']:.1f}% (n={t['test_n']})")
        elif t['status'] == 'MARGINAL':
            print(f"  🟡 {t['ticker']}: {t['test_wr']:.1f}% / {t['val_wr']:.1f}% (n={t['test_n']})")
        elif t['status'] == 'FAIL':
            print(f"  ❌ {t['ticker']}: {t['test_wr']:.1f}% / {t['val_wr']:.1f}% (n={t['test_n']})")
        else:
            print(f"  ⚠️  {t['ticker']}: {t['status']}")
    
    print(f"\n  Summary: {len(golden)} GOLDEN, {len(validated)} VALIDATED, {len(marginal)} MARGINAL, {len(failed)} FAIL, {len(insufficient)} INSUFFICIENT")

conn.close()

print('\n' + '='*100)
print('KEY FINDINGS:')
print('='*100)
print('• Full transparency — ALL tickers tested and reported')
print('• No cherry-picking — FAIL and INSUFFICIENT shown')
print('• Proper industry classification applied')
print('• 0002.HK (CLP) correctly classified as UTILITIES')
print('• SHK (0016.HK) included in PROPERTY sector')
