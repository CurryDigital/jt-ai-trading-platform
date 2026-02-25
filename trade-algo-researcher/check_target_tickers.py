#!/usr/bin/env python3
"""
Check available tickers for hypothesis testing
"""
import boto3
import psycopg2
import pandas as pd

def get_auth_token():
    session = boto3.Session(region_name='ap-southeast-1')
    rds = session.client('rds')
    return rds.generate_db_auth_token(
        DBHostname='openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com',
        Port=5432,
        DBUsername='openclaw_user',
        Region='ap-southeast-1'
    )

def check_tickers():
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
    
    # Check silver.historical_stock_data
    print("=== Checking silver.historical_stock_data ===")
    for ticker in target_tickers:
        cursor.execute("""
            SELECT MIN(date), MAX(date), COUNT(*) 
            FROM silver.historical_stock_data 
            WHERE symbol = %s
        """, (ticker,))
        result = cursor.fetchone()
        if result and result[2] > 0:
            print(f"{ticker}: {result[0]} to {result[1]} | {result[2]} records")
        else:
            print(f"{ticker}: NOT FOUND")
    
    # Check silver.unified_prices
    print("\n=== Checking silver.unified_prices ===")
    for ticker in target_tickers:
        cursor.execute("""
            SELECT MIN(timestamp), MAX(timestamp), COUNT(*) 
            FROM silver.unified_prices 
            WHERE symbol = %s
        """, (ticker,))
        result = cursor.fetchone()
        if result and result[2] > 0:
            print(f"{ticker}: {result[0]} to {result[1]} | {result[2]} records")
        else:
            print(f"{ticker}: NOT FOUND")
    
    # Check gold.technical_indicators
    print("\n=== Checking gold.technical_indicators ===")
    for ticker in target_tickers:
        cursor.execute("""
            SELECT MIN(timestamp), MAX(timestamp), COUNT(*) 
            FROM gold.technical_indicators 
            WHERE symbol = %s
        """, (ticker,))
        result = cursor.fetchone()
        if result and result[2] > 0:
            print(f"{ticker}: {result[0]} to {result[1]} | {result[2]} records")
        else:
            print(f"{ticker}: NOT FOUND")
    
    conn.close()

if __name__ == "__main__":
    check_tickers()
