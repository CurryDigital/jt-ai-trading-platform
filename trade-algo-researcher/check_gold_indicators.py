#!/usr/bin/env python3
"""
Check gold.technical_indicators_calculated for available indicators
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

def check_indicators():
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
    
    # Check schema
    print("=== gold.technical_indicators_calculated columns ===")
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'gold' AND table_name = 'technical_indicators_calculated'
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    for col, dtype in columns:
        print(f"  {col}: {dtype}")
    
    # Check available tickers
    print("\n=== Available tickers ===")
    cursor.execute("""
        SELECT ticker, COUNT(*) as cnt
        FROM gold.technical_indicators_calculated
        GROUP BY ticker
        ORDER BY cnt DESC
        LIMIT 20
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} records")
    
    # Check for our target tickers
    print("\n=== Target tickers availability ===")
    for ticker in target_tickers:
        cursor.execute("""
            SELECT MIN(timestamp), MAX(timestamp), COUNT(*) 
            FROM gold.technical_indicators_calculated 
            WHERE ticker = %s
        """, (ticker,))
        result = cursor.fetchone()
        if result and result[2] > 0:
            print(f"{ticker}: {result[0]} to {result[1]} | {result[2]} records")
        else:
            print(f"{ticker}: NOT FOUND")
    
    # Sample data for NVDA
    print("\n=== Sample NVDA data ===")
    cursor.execute("""
        SELECT * FROM gold.technical_indicators_calculated 
        WHERE ticker = 'NVDA' 
        ORDER BY timestamp DESC
        LIMIT 3
    """)
    col_names = [desc[0] for desc in cursor.description]
    print(f"Columns: {col_names}")
    for row in cursor.fetchall():
        print(dict(zip(col_names, row)))
    
    conn.close()

if __name__ == "__main__":
    check_indicators()
