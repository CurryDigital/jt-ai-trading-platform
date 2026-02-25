#!/usr/bin/env python3
"""
Check all available tables for target tickers
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

def check_all_tables():
    token = get_auth_token()
    conn = psycopg2.connect(
        host='openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com',
        port=5432,
        database='aitrading',
        user='openclaw_user',
        password=token,
        sslmode='require'
    )
    
    target_tickers = ['NVDA', 'TSLA', 'AMD', 'COIN', 'MSTR', 'SPY', 'QQQ', 'AAPL', 'MSFT', 'BTC-USD', 'ETH-USD']
    
    cursor = conn.cursor()
    
    # Find all tables with ticker/symbol columns
    cursor.execute("""
        SELECT table_schema, table_name, column_name
        FROM information_schema.columns 
        WHERE column_name IN ('ticker', 'symbol')
        AND table_schema NOT IN ('information_schema', 'pg_catalog')
        ORDER BY table_schema, table_name
    """)
    tables = cursor.fetchall()
    
    print("=== Tables with ticker/symbol column ===")
    for schema, table, col in tables:
        print(f"  {schema}.{table}.{col}")
        
        # Check which tickers exist
        for ticker in target_tickers:
            try:
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {schema}.{table} WHERE {col} = %s
                """, (ticker,))
                count = cursor.fetchone()[0]
                if count > 0:
                    cursor.execute(f"""
                        SELECT MIN(date_col), MAX(date_col) FROM (
                            SELECT {col}, 
                                CASE 
                                    WHEN 'date' IN (SELECT column_name FROM information_schema.columns 
                                                   WHERE table_schema = %s AND table_name = %s) THEN date::text
                                    WHEN 'timestamp' IN (SELECT column_name FROM information_schema.columns 
                                                        WHERE table_schema = %s AND table_name = %s) THEN timestamp::text
                                    ELSE 'unknown'
                                END as date_col
                            FROM {schema}.{table} 
                            WHERE {col} = %s
                        ) subq
                    """, (schema, table, schema, table, ticker))
                    result = cursor.fetchone()
                    print(f"    {ticker}: {count} records")
            except Exception as e:
                pass
    
    conn.close()

if __name__ == "__main__":
    check_all_tables()
