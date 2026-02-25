#!/usr/bin/env python3
import boto3
import psycopg2

# Connect and check silver schema
db = psycopg2.connect(
    host='openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com',
    port=5432,
    database='aitrading',
    user='openclaw_user',
    password=boto3.client('rds', region_name='ap-southeast-1').generate_db_auth_token(
        DBHostname='openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com',
        Port=5432,
        DBUsername='openclaw_user',
        Region='ap-southeast-1'
    ),
    sslmode='require'
)

cursor = db.cursor()

# Check silver historical_stock_data
cursor.execute("""
    SELECT MIN(date) as min_date, MAX(date) as max_date, COUNT(*) as count
    FROM silver.historical_stock_data
""")
result = cursor.fetchone()
print(f"silver.historical_stock_data: {result[0]} to {result[1]} | Total records: {result[2]}")

# Check sample of tickers
cursor.execute("""
    SELECT ticker, COUNT(*) as count
    FROM silver.historical_stock_data
    GROUP BY ticker
    ORDER BY count DESC
    LIMIT 20
""")
print("\nTop 20 tickers in silver.historical_stock_data:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} records")

# Check available tables in silver
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'silver'
    ORDER BY table_name
""")
print("\nTables in silver schema:")
for row in cursor.fetchall():
    print(f"  {row[0]}")

cursor.close()
db.close()
