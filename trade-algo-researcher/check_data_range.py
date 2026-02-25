#!/usr/bin/env python3
import boto3
import psycopg2

# Connect and check data range
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

# Check date range
cursor.execute("""
    SELECT MIN(date) as min_date, MAX(date) as max_date, COUNT(*) as count
    FROM gold.stock_metrics
""")
result = cursor.fetchone()
print(f"Data range: {result[0]} to {result[1]} | Total records: {result[2]}")

# Check tickers
cursor.execute("""
    SELECT ticker, COUNT(*) as count, MIN(date) as min_d, MAX(date) as max_d
    FROM gold.stock_metrics
    GROUP BY ticker
    ORDER BY count DESC
    LIMIT 20
""")
print("\nTop 20 tickers by record count:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} records ({row[2]} to {row[3]})")

cursor.close()
db.close()
