#!/usr/bin/env python3
"""
Check database schema — find correct table names
"""

import sys
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
from db_backtest_engine import TradeAlgoDB

print("=" * 80)
print("CHECKING DATABASE SCHEMA")
print("=" * 80)

try:
    db = TradeAlgoDB()
    conn = db.connect()
    print("✅ Connected to database")
    print()
    
    # List all schemas
    print("SCHEMAS:")
    query = "SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')"
    import pandas as pd
    schemas = pd.read_sql(query, conn)
    for schema in schemas['schema_name']:
        print(f"  - {schema}")
    
    print()
    
    # List tables in gold schema
    print("TABLES IN 'gold' SCHEMA:")
    query = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'gold'
    ORDER BY table_name
    """
    tables = pd.read_sql(query, conn)
    for table in tables['table_name']:
        print(f"  - {table}")
    
    print()
    
    # List tables in silver schema
    print("TABLES IN 'silver' SCHEMA:")
    query = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'silver'
    ORDER BY table_name
    """
    tables = pd.read_sql(query, conn)
    for table in tables['table_name']:
        print(f"  - {table}")
    
    print()
    
    # Check if unified_prices exists
    print("CHECKING unified_prices table:")
    try:
        query = "SELECT COUNT(*) as count FROM gold.unified_prices LIMIT 1"
        result = pd.read_sql(query, conn)
        print(f"  ✅ gold.unified_prices exists: {result['count'].iloc[0]} records")
        
        # Check columns
        query = """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'gold' AND table_name = 'unified_prices'
        ORDER BY ordinal_position
        """
        columns = pd.read_sql(query, conn)
        print(f"  Columns: {', '.join(columns['column_name'].tolist())}")
        
        # Sample data
        query = "SELECT * FROM gold.unified_prices LIMIT 5"
        sample = pd.read_sql(query, conn)
        print(f"\n  Sample data:")
        print(sample.to_string())
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
    
    conn.close()
    print(f"\n{'='*80}")
    
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    print(f"{'='*80}")
