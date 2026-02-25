#!/usr/bin/env python3
"""
Check table schema
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

def check_schema():
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
    
    # Check column names for silver.historical_stock_data
    print("=== silver.historical_stock_data columns ===")
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'silver' AND table_name = 'historical_stock_data'
        ORDER BY ordinal_position
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    # Check sample data
    print("\n=== Sample data from silver.historical_stock_data ===")
    cursor.execute("""
        SELECT * FROM silver.historical_stock_data LIMIT 3
    """)
    columns = [desc[0] for desc in cursor.description]
    print(f"Columns: {columns}")
    for row in cursor.fetchall():
        print(row)
    
    conn.close()

if __name__ == "__main__":
    check_schema()
