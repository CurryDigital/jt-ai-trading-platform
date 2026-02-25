#!/usr/bin/env python3
"""
Check gold.technical_indicators_calculated for target tickers
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
    
    # Check for our target tickers
    print("=== Target tickers in gold.technical_indicators_calculated ===")
    for ticker in target_tickers:
        cursor.execute("""
            SELECT MIN(date), MAX(date), COUNT(*) 
            FROM gold.technical_indicators_calculated 
            WHERE ticker = %s
        """, (ticker,))
        result = cursor.fetchone()
        if result and result[2] > 0:
            print(f"{ticker}: {result[0]} to {result[1]} | {result[2]} records")
        else:
            print(f"{ticker}: NOT FOUND")
    
    # Sample data for available ticker
    print("\n=== Sample COIN data ===")
    cursor.execute("""
        SELECT * FROM gold.technical_indicators_calculated 
        WHERE ticker = 'COIN' 
        ORDER BY date DESC
        LIMIT 2
    """)
    col_names = [desc[0] for desc in cursor.description]
    for row in cursor.fetchall():
        for col, val in zip(col_names, row):
            print(f"  {col}: {val}")
        print()
    
    conn.close()

if __name__ == "__main__":
    check_indicators()
