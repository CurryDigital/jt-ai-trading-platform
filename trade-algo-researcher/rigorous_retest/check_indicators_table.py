#!/usr/bin/env python3
"""
Check if technical_indicators_calculated exists
"""

import sys
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
from db_backtest_engine import TradeAlgoDB
import pandas as pd

print("Checking gold.technical_indicators_calculated...")

try:
    db = TradeAlgoDB()
    conn = db.connect()
    
    # Check if table exists
    query = """
    SELECT EXISTS (
        SELECT 1 
        FROM information_schema.tables 
        WHERE table_schema = 'gold' 
        AND table_name = 'technical_indicators_calculated'
    );
    """
    
    result = pd.read_sql(query, conn)
    exists = result.iloc[0, 0]
    
    if exists:
        print("✅ Table exists")
        
        # Check columns
        query = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'gold' AND table_name = 'technical_indicators_calculated'
        ORDER BY ordinal_position
        """
        columns = pd.read_sql(query, conn)
        print(f"\nColumns: {', '.join(columns['column_name'].tolist())}")
        
        # Check sample data
        query = "SELECT * FROM gold.technical_indicators_calculated LIMIT 3"
        sample = pd.read_sql(query, conn)
        print(f"\nSample data:\n{sample.to_string()}")
        
    else:
        print("❌ Table does NOT exist")
        print("\nNeed to calculate indicators or use different table")
    
    conn.close()
    
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
