#!/usr/bin/env python3
import boto3
import psycopg2

# Connect
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

# Check for stock tickers
print("Looking for stock tickers in silver.historical_stock_data...")
cursor.execute("""
    SELECT DISTINCT ticker
    FROM silver.historical_stock_data
    WHERE ticker NOT LIKE '%-USD' 
    AND ticker NOT LIKE '%=X'
    AND ticker NOT LIKE '%.HK'
    AND ticker NOT LIKE '%.SS'
    AND ticker NOT LIKE '%.SZ'
    ORDER BY ticker
""")
stock_tickers = cursor.fetchall()
print(f"Found {len(stock_tickers)} non-crypto/forex tickers:")
for t in stock_tickers[:50]:
    print(f"  {t[0]}")

# Check technical_indicators
cursor.execute("""
    SELECT MIN(date) as min_date, MAX(date) as max_date, COUNT(*) as count
    FROM silver.technical_indicators
""")
result = cursor.fetchone()
print(f"\nsilver.technical_indicators: {result[0]} to {result[1]} | Total records: {result[2]}")

# Check columns in technical_indicators
cursor.execute("""
    SELECT column_name
    FROM information_schema.columns 
    WHERE table_schema = 'silver' 
    AND table_name = 'technical_indicators'
    ORDER BY ordinal_position
""")
print("\nColumns in silver.technical_indicators:")
for col in cursor.fetchall():
    print(f"  {col[0]}")

# Check tickers in technical_indicators
cursor.execute("""
    SELECT DISTINCT ticker, COUNT(*) as count
    FROM silver.technical_indicators
    GROUP BY ticker
    ORDER BY count DESC
    LIMIT 20
""")
print("\nTop tickers in technical_indicators:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} records")

cursor.close()
db.close()
