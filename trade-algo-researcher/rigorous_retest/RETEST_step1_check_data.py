#!/usr/bin/env python3
"""
STEP 1: Check Data Availability — Using Correct DB Connection
"""

import pandas as pd
import sys
import warnings
warnings.filterwarnings('ignore')

# Use correct database connection
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
from db_backtest_engine import TradeAlgoDB

# All tickers to check
ALL_TICKERS_CHECK = [
    # Tier 1: Golden
    '1398.HK', '3988.HK', '3328.HK', '2388.HK', '0939.HK', '0005.HK', '3968.HK',
    '9988.HK', '9999.HK', '1024.HK', '0700.HK',
    # Tier 2: Validated  
    'PLTR', 'ASML', 'AMD', 'ZM',
    'SOL-USD', 'ADA-USD', 'MSTR', 'DOT-USD',
    'JPM', 'BAC', 'GS', 'C',
    # Tier 3: Batch 15
    '0023.HK', '0998.HK', '2388.HK', '3618.HK',
    'NZDJPY=X',
    # Tier 5: SG
    'D05.SI', 'O39.SI', 'U11.SI', 'Z74.SI', 'G13.SI',
    'C6L.SI', 'C38U.SI', 'A17U.SI', 'N2IU.SI', 'ME8U.SI',
]

print("=" * 90)
print("STEP 1: CHECKING DATA AVAILABILITY (REAL RDS)")
print("=" * 90)
print(f"Tickers to check: {len(ALL_TICKERS_CHECK)}")
print()

try:
    # Connect to database
    print("Connecting to RDS database...")
    db = TradeAlgoDB()
    conn = db.connect()
    print("✅ Database connected successfully")
    print()
    
    # Query each ticker
    results = []
    
    for ticker in ALL_TICKERS_CHECK:
        try:
            query = f"""
            SELECT 
                COUNT(*) as record_count,
                MIN(date) as earliest_date,
                MAX(date) as latest_date
            FROM silver.unified_prices
            WHERE ticker = '{ticker}'
            """
            
            df = pd.read_sql(query, conn)
            
            record_count = df['record_count'].iloc[0]
            earliest = df['earliest_date'].iloc[0]
            latest = df['latest_date'].iloc[0]
            
            # Check if sufficient for testing (2021-2025)
            if record_count >= 1000:
                status = "✅ GOOD"
            elif record_count >= 500:
                status = "⚠️ OK"
            elif record_count > 0:
                status = "⚠️ LOW"
            else:
                status = "❌ MISSING"
            
            results.append({
                'ticker': ticker,
                'records': record_count,
                'earliest': earliest,
                'latest': latest,
                'status': status
            })
            
            print(f"{ticker:12} | {record_count:5} records | {status}")
            
        except Exception as e:
            results.append({
                'ticker': ticker,
                'records': 0,
                'earliest': None,
                'latest': None,
                'status': f"❌ ERROR"
            })
            print(f"{ticker:12} | ❌ ERROR: {str(e)[:40]}")
    
    # Summary
    print("\n" + "=" * 90)
    print("SUMMARY")
    print("=" * 90)
    
    df_results = pd.DataFrame(results)
    
    good = len(df_results[df_results['status'] == "✅ GOOD"])
    ok = len(df_results[df_results['status'] == "⚠️ OK"])
    low = len(df_results[df_results['status'] == "⚠️ LOW"])
    missing = len(df_results[df_results['status'] == "❌ MISSING"])
    error = len(df_results[df_results['status'] == "❌ ERROR"])
    
    print(f"\n✅ Good (1000+ records): {good}")
    print(f"⚠️  OK (500-999): {ok}")
    print(f"⚠️  Low (1-499): {low}")
    print(f"❌ Missing: {missing}")
    print(f"❌ Error: {error}")
    
    # Save results
    df_results.to_csv('/home/ubuntu/.openclaw/workspace/trade-algo-researcher/rigorous_retest/RETEST_data_availability.csv', index=False)
    print(f"\n📁 Results saved to RETEST_data_availability.csv")
    
    # List tickers ready for testing (GOOD + OK)
    ready = df_results[df_results['status'].isin(["✅ GOOD", "⚠️ OK"])]['ticker'].tolist()
    print(f"\n✅ TICKERS READY FOR TESTING ({len(ready)}):")
    for t in ready:
        print(f"  - {t}")
    
    # List missing for data requests
    if missing + error > 0:
        need_data = df_results[df_results['status'].isin(["❌ MISSING", "❌ ERROR"])]['ticker'].tolist()
        print(f"\n❌ NEED DATA REQUESTS ({len(need_data)}):")
        for t in need_data:
            print(f"  - {t}")
    
    # Close connection
    conn.close()
    print(f"\n{'='*90}")
    
except Exception as e:
    print(f"\n❌ DATABASE ERROR")
    print(f"Error: {str(e)}")
    print(f"\n{'='*90}")
