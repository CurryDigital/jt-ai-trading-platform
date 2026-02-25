#!/usr/bin/env python3
"""
Check unified_prices columns
"""

import sys
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
from db_backtest_engine import TradeAlgoDB
import pandas as pd

print("Checking silver.unified_prices columns...")

try:
    db = TradeAlgoDB()
    conn = db.connect()
    
    query = """
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'silver' AND table_name = 'unified_prices'
    ORDER BY ordinal_position
    """
    
    columns = pd.read_sql(query, conn)
    print("\nColumns in silver.unified_prices:")
    for _, row in columns.iterrows():
        print(f"  - {row['column_name']} ({row['data_type']})")
    
    # Sample data
    print("\nSample data:")
    query = "SELECT * FROM silver.unified_prices LIMIT 3"
    sample = pd.read_sql(query, conn)
    print(sample.to_string())
    
    conn.close()
    
except Exception as e:
    print(f"Error: {str(e)}")
