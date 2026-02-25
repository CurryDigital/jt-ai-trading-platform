#!/usr/bin/env python3
"""
Check available tickers and indicators
"""
import boto3
import psycopg2
import pandas as pd

def get_auth_token():
    session = boto3.Session(region_name='ap-southeast-1')
    rds = session.client('rds')
    return rds.generate_db_auth_token(
        DBHostname='openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com',
        Port=5432,
        DBUsername='openclaw_user',
        Region='ap-southeast-1'
    )

def check_tickers():
    token = get_auth_token()
    conn = psycopg2.connect(
        host='openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com',
        port=5432,
        database='aitrading',
        user='openclaw_user',
        password=token,
        sslmode='require'
    )
    
    target_tickers = ['NVDA', 'TSLA', 'AMD', 'COIN', 'MSTR', 'SPY', 'QQQ', 'AAPL', 'MSFT']
    
    cursor = conn.cursor()
    
    # Check silver.historical_stock_data
    print("=== silver.historical_stock_data ===")
    for ticker in target_tickers:
        cursor.execute("""
            SELECT MIN(date), MAX(date), COUNT(*) 
            FROM silver.historical_stock_data 
            WHERE ticker = %s
        """, (ticker,))
        result = cursor.fetchone()
        if result and result[2] > 0:
            print(f"{ticker}: {result[0]} to {result[1]} | {result[2]} records")
        else:
            print(f"{ticker}: NOT FOUND")
    
    # Check gold.technical_indicators schema
    print("\n=== gold.technical_indicators columns ===")
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'gold' AND table_name = 'technical_indicators'
        ORDER BY ordinal_position
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    # Check gold.technical_indicators data availability
    print("\n=== gold.technical_indicators availability ===")
    for ticker in target_tickers:
        cursor.execute("""
            SELECT MIN(timestamp), MAX(timestamp), COUNT(*) 
            FROM gold.technical_indicators 
            WHERE ticker = %s
        """, (ticker,))
        result = cursor.fetchone()
        if result and result[2] > 0:
            print(f"{ticker}: {result[0]} to {result[1]} | {result[2]} records")
        else:
            print(f"{ticker}: NOT FOUND")
    
    # Sample data from gold.technical_indicators
    print("\n=== Sample gold.technical_indicators ===")
    cursor.execute("""
        SELECT * FROM gold.technical_indicators WHERE ticker = 'NVDA' LIMIT 3
    """)
    columns = [desc[0] for desc in cursor.description]
    print(f"Columns: {columns}")
    for row in cursor.fetchall():
        print(row)
    
    conn.close()

if __name__ == "__main__":
    check_tickers()
