#!/usr/bin/env python3
import boto3
import psycopg2

# Connect and check columns
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
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'gold' 
    AND table_name = 'stock_metrics'
    ORDER BY ordinal_position
""")

columns = cursor.fetchall()
print("Columns in gold.stock_metrics:")
for col in columns:
    print(f"  {col[0]} ({col[1]})")

cursor.close()
db.close()
