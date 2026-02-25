#!/usr/bin/env python3
"""
STEP 1: Check Data Availability for ALL Tickers
Query RDS to see what data we actually have
"""

import pandas as pd
import sys
import warnings
warnings.filterwarnings('ignore')

# All tickers to check
ALL_TICKERS_CHECK = [
    # Tier 1: Golden
    '1398.HK', '3988.HK', '3328.HK', '2388.HK', '0939.HK', '0005.HK', '3968.HK',
    '9988.HK', '9999.HK', '1024.HK', '0700.HK',
    # Tier 2: Validated
    'PLTR', 'ASML', 'AMD', 'ZM',
    'SOL-USD', 'ADA-USD', 'MSTR', 'DOT-USD',
    '3328.HK', '3988.HK', '0939.HK',  # S002
    'JPM', 'BAC', 'GS', 'C',
    # Tier 3: Batch 15
    '0023.HK', '0998.HK', '2388.HK', '3618.HK',
    '0700.HK', '9988.HK',  # pairs
    'NZDJPY=X',
    # Tier 5: SG
    'D05.SI', 'O39.SI', 'U11.SI', 'Z74.SI', 'G13.SI',
    'C6L.SI', 'C38U.SI', 'A17U.SI', 'N2IU.SI', 'ME8U.SI',
]

print("=" * 80)
print("STEP 1: CHECKING DATA AVAILABILITY")
print("=" * 80)
print(f"Tickers to check: {len(ALL_TICKERS_CHECK)}")
print()

# Try to connect to database
try:
    sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
    from db_backtest_engine import DataRetrieval
    
    print("Attempting database connection...")
    db = DataRetrieval()
    print("✅ Database connected")
    
    # Query each ticker
    results = []
    for ticker in ALL_TICKERS_CHECK:
        try:
            query = f"""
            SELECT 
                '{ticker}' as ticker,
                COUNT(*) as record_count,
                MIN(date) as earliest_date,
                MAX(date) as latest_date
            FROM gold.daily_prices
            WHERE ticker = '{ticker}'
            """
            
            df = db.query_to_df(query)
            
            if df is not None and len(df) > 0:
                record_count = df['record_count'].iloc[0]
                earliest = df['earliest_date'].iloc[0]
                latest = df['latest_date'].iloc[0]
                
                status = "✅ AVAILABLE" if record_count >= 500 else "⚠️ LOW COUNT"
                
                results.append({
                    'ticker': ticker,
                    'records': record_count,
                    'earliest': earliest,
                    'latest': latest,
                    'status': status
                })
                
                print(f"{ticker:12} | {record_count:5} records | {earliest} to {latest} | {status}")
            else:
                results.append({
                    'ticker': ticker,
                    'records': 0,
                    'earliest': None,
                    'latest': None,
                    'status': "❌ MISSING"
                })
                print(f"{ticker:12} | ❌ NO DATA")
                
        except Exception as e:
            results.append({
                'ticker': ticker,
                'records': 0,
                'earliest': None,
                'latest': None,
                'status': f"❌ ERROR: {str(e)[:30]}"
            })
            print(f"{ticker:12} | ❌ ERROR: {str(e)[:40]}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    df_results = pd.DataFrame(results)
    
    available = len(df_results[df_results['records'] >= 500])
    low_count = len(df_results[(df_results['records'] > 0) & (df_results['records'] < 500)])
    missing = len(df_results[df_results['records'] == 0])
    
    print(f"\n✅ Available (500+ records): {available}")
    print(f"⚠️  Low count (<500): {low_count}")
    print(f"❌ Missing: {missing}")
    
    # Save results
    df_results.to_csv('/home/ubuntu/.openclaw/workspace/trade-algo-researcher/rigorous_retest/DATA_AVAILABILITY_CHECK.csv', index=False)
    print(f"\n📁 Results saved to DATA_AVAILABILITY_CHECK.csv")
    
    # List missing tickers for data requests
    if missing > 0:
        print(f"\n❌ MISSING TICKERS (Need Data Requests):")
        missing_tickers = df_results[df_results['records'] == 0]['ticker'].tolist()
        for t in missing_tickers:
            print(f"  - {t}")
    
    print(f"\n{'='*80}")
    
except Exception as e:
    print(f"\n❌ DATABASE CONNECTION FAILED")
    print(f"Error: {str(e)}")
    print(f"\nCannot proceed without database access.")
    print(f"Options:")
    print(f"  1. Fix database connection")
    print(f"  2. Use alternative data source")
    print(f"  3. File data availability request")
    print(f"\n{'='*80}")
