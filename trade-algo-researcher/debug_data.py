#!/usr/bin/env python3
"""
Debug data availability for target tickers
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

def check_data():
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
    
    target_tickers = ['NVDA', 'TSLA', 'AMD', 'COIN', 'MSTR', 'SPY', 'QQQ', 'AAPL', 'MSFT']
    
    for ticker in target_tickers:
        print(f"\n=== {ticker} ===")
        
        # Check price data
        cursor.execute("""
            SELECT MIN(date), MAX(date), COUNT(*) 
            FROM silver.historical_stock_data
            WHERE ticker = %s
        """, (ticker,))
        row = cursor.fetchone()
        print(f"Price data: {row[0]} to {row[1]} | {row[2]} records")
        
        # Check indicator data
        cursor.execute("""
            SELECT MIN(date), MAX(date), COUNT(*) 
            FROM gold.technical_indicators_calculated
            WHERE ticker = %s
        """, (ticker,))
        row = cursor.fetchone()
        print(f"Indicators: {row[0]} to {row[1]} | {row[2]} records")
        
        # Check RSI > 70 count for H1
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM gold.technical_indicators_calculated
            WHERE ticker = %s AND rsi_14 > 70
        """, (ticker,))
        row = cursor.fetchone()
        print(f"RSI > 70: {row[0]} records")
        
        # Check Stoch > 80 AND > 75 for H2
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM gold.technical_indicators_calculated
            WHERE ticker = %s AND stoch_k > 80 AND stoch_d > 75
        """, (ticker,))
        row = cursor.fetchone()
        print(f"Stoch >80/>75: {row[0]} records")
    
    conn.close()

if __name__ == "__main__":
    check_data()
