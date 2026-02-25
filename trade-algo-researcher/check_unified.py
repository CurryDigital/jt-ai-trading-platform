#!/usr/bin/env python3
"""
Check silver.unified_prices for target tickers
"""
import boto3
import psycopg2

def get_auth_token():
    session = boto3.Session(region_name='ap-southeast-1')
    rds = session.client('rds')
    return rds.generate_db_auth_token(
        DBHostname='openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com',
        Port=5432,
        DBUsername='openclaw_user',
        Region='ap-southeast-1'
    )

def check_unified_prices():
    token = get_auth_token()
    conn = psycopg2.connect(
        host='openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com',
        port=5432,
        database='aitrading',
        user='openclaw_user',
        password=token,
        sslmode='require'
    )
    cursor = conn.cursor()
    
    # Check column names
    print("=== silver.unified_prices columns ===")
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'silver' AND table_name = 'unified_prices'
        ORDER BY ordinal_position
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    # Check tickers
    target_tickers = ['NVDA', 'TSLA', 'AMD', 'COIN', 'MSTR', 'SPY', 'QQQ', 'AAPL', 'MSFT']
    print("\n=== silver.unified_prices availability ===")
    for ticker in target_tickers:
        cursor.execute("""
            SELECT MIN(timestamp), MAX(timestamp), COUNT(*) 
            FROM silver.unified_prices
            WHERE ticker = %s
        """, (ticker,))
        row = cursor.fetchone()
        if row and row[2] > 0:
            print(f"{ticker}: {row[0]} to {row[1]} | {row[2]} records")
        else:
            print(f"{ticker}: NOT FOUND")
    
    # Sample data
    print("\n=== Sample COIN data ===")
    cursor.execute("""
        SELECT * FROM silver.unified_prices
        WHERE ticker = 'COIN'
        ORDER BY timestamp DESC
        LIMIT 2
    """)
    col_names = [desc[0] for desc in cursor.description]
    print(f"Columns: {col_names}")
    for row in cursor.fetchall():
        print(row)
    
    conn.close()

if __name__ == "__main__":
    check_unified_prices()
