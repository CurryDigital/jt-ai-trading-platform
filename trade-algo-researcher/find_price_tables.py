#!/usr/bin/env python3
"""
Find where COIN, MSTR, SPY, QQQ price data is stored
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

def find_price_tables():
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
    
    target_tickers = ['COIN', 'MSTR', 'SPY', 'QQQ']
    
    # Find all tables with price-like columns
    cursor.execute("""
        SELECT DISTINCT table_schema, table_name 
        FROM information_schema.columns 
        WHERE column_name IN ('open', 'high', 'low', 'close', 'adj_close')
        AND table_schema NOT IN ('information_schema', 'pg_catalog')
        ORDER BY table_schema, table_name
    """)
    tables = cursor.fetchall()
    
    print("=== Tables with OHLC columns ===")
    for schema, table in tables:
        print(f"\n{schema}.{table}:")
        for ticker in target_tickers:
            try:
                # Check if ticker column exists
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.columns 
                    WHERE table_schema = %s AND table_name = %s AND column_name = 'ticker'
                """, (schema, table))
                has_ticker = cursor.fetchone()[0] > 0
                
                if has_ticker:
                    cursor.execute(f"""
                        SELECT MIN(date), MAX(date), COUNT(*) 
                        FROM {schema}.{table}
                        WHERE ticker = %s
                    """, (ticker,))
                    row = cursor.fetchone()
                    if row and row[2] > 0:
                        print(f"  {ticker}: {row[0]} to {row[1]} | {row[2]} records")
            except Exception as e:
                pass
    
    conn.close()

if __name__ == "__main__":
    find_price_tables()
