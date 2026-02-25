#!/usr/bin/env python3
"""
Quick Data Fetch for Testing
Fetches 5-year data and saves to CSV for local testing
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
from pathlib import Path
import time

def fetch_test_universe():
    """Fetch core universe for quick testing."""
    
    # Core test universe (20 stocks)
    tickers = [
        'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN',  # Mega cap tech
        'ADBE', 'ADSK', 'TEAM', 'NOW', 'INTU',     # SaaS/AI disruption
        'VRT', 'FN', 'STX',                         # GPU supply chain
        'SPY', 'QQQ',                               # Benchmarks
    ]
    
    start_date = '2019-01-01'
    end_date = '2024-12-31'
    
    print("🚀 Fetching test universe...")
    print(f"   {len(tickers)} tickers")
    print(f"   Period: {start_date} to {end_date}")
    print()
    
    all_data = []
    
    for ticker in tickers:
        try:
            print(f"   Fetching {ticker}...", end=' ')
            stock = yf.Ticker(ticker)
            df = stock.history(start=start_date, end=end_date)
            
            if not df.empty:
                df = df.reset_index()
                df['ticker'] = ticker
                df['returns'] = df['Close'].pct_change()
                all_data.append(df)
                print(f"✓ ({len(df)} rows)")
            else:
                print(f"✗ (no data)")
            
            time.sleep(0.3)  # Rate limiting
            
        except Exception as e:
            print(f"✗ ({e})")
    
    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        
        # Save to CSV
        output_dir = Path(__file__).parent / 'test_data'
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / 'test_universe_5year.csv'
        combined.to_csv(output_file, index=False)
        
        print()
        print(f"✅ Saved to: {output_file}")
        print(f"   Total rows: {len(combined):,}")
        print(f"   Date range: {combined['Date'].min()} to {combined['Date'].max()}")
        print()
        print("Ready for local backtest testing!")
        
        return combined
    else:
        print("❌ No data fetched")
        return None


if __name__ == '__main__':
    fetch_test_universe()
