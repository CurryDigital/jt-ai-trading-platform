#!/usr/bin/env python3
"""
Generate Synthetic Data for Backtesting
Creates realistic sample data for PEAD and Commodity strategies
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent

def generate_earnings_data(num_stocks=50, quarters=20, seed=42):
    """Generate synthetic earnings data for PEAD backtest."""
    np.random.seed(seed)
    
    tickers = [f'STK{i:03d}' for i in range(num_stocks)]
    data = []
    
    base_date = datetime(2019, 1, 15)
    
    for ticker in tickers:
        # Generate quarterly earnings
        for q in range(quarters):
            date = base_date + timedelta(days=q * 91)  # Quarterly
            
            # Generate EPS with trend and seasonality
            trend = q * 0.02  # Growth trend
            seasonal = 0.1 * np.sin(2 * np.pi * q / 4)  # Quarterly seasonality
            base_eps = 1.0 + trend + seasonal
            
            # Analyst estimates (with error)
            estimate_error = np.random.normal(0, 0.08)
            eps_estimate = base_eps + estimate_error
            
            # Actual EPS (with surprise component)
            surprise = np.random.normal(0, 0.12)
            eps_actual = eps_estimate + surprise
            
            # Revenue (correlated with EPS)
            revenue_estimate = 10.0 + trend * 10 + np.random.normal(0, 0.5)
            revenue_actual = revenue_estimate + np.random.normal(0, 0.8)
            
            data.append({
                'ticker': ticker,
                'announcement_date': date.strftime('%Y-%m-%d'),
                'eps_actual': round(eps_actual, 2),
                'eps_estimate': round(eps_estimate, 2),
                'revenue_actual': round(revenue_actual, 2),
                'revenue_estimate': round(revenue_estimate, 2),
                'fiscal_quarter': f'FY{2019 + q//4}-Q{(q % 4) + 1}'
            })
    
    df = pd.DataFrame(data)
    return df


def generate_commodity_data(commodity='NG', years=20, seed=42):
    """Generate synthetic futures data for commodity seasonality backtest."""
    np.random.seed(seed + hash(commodity) % 1000)
    
    # Generate daily dates
    start_date = datetime(2004, 1, 1)
    end_date = datetime(2024, 12, 31)
    dates = pd.date_range(start=start_date, end=end_date, freq='B')  # Business days
    
    # Base price depends on commodity
    base_prices = {
        'NG': 4.0,   # Natural Gas ~$4/MMBtu
        'RB': 2.0,   # Gasoline ~$2/gallon
        'HO': 2.5,   # Heating Oil ~$2.50/gallon
        'ZC': 4.0    # Corn ~$4/bushel
    }
    
    base_price = base_prices.get(commodity, 3.0)
    
    # Generate price series with trend, seasonality, and noise
    n_days = len(dates)
    
    # Long-term trend
    trend = np.linspace(0, 0.5, n_days)
    
    # Seasonal component
    day_of_year = np.array([d.dayofyear for d in dates])
    seasonal_amplitude = 0.3
    seasonal = seasonal_amplitude * np.sin(2 * np.pi * day_of_year / 365)
    
    # Random walk component
    returns = np.random.normal(0.0002, 0.02, n_days)
    price_changes = np.cumprod(1 + returns)
    
    # Combine components
    closes = base_price * (1 + trend * 0.5) * (1 + seasonal) * price_changes
    closes = np.maximum(closes, base_price * 0.3)  # Floor price
    
    # Generate OHLC from closes
    data = []
    for i, (date, close) in enumerate(zip(dates, closes)):
        # Intraday volatility
        daily_range = close * np.random.uniform(0.01, 0.04)
        
        open_price = close * (1 + np.random.normal(0, 0.005))
        high = max(open_price, close) + daily_range * np.random.uniform(0.3, 0.7)
        low = min(open_price, close) - daily_range * np.random.uniform(0.3, 0.7)
        
        volume = int(np.random.uniform(10000, 100000) * (1 + abs(returns[i]) * 10))
        
        data.append({
            'date': date.strftime('%Y-%m-%d'),
            'open': round(open_price, 3),
            'high': round(high, 3),
            'low': round(low, 3),
            'close': round(close, 3),
            'volume': volume,
            'commodity': commodity
        })
    
    df = pd.DataFrame(data)
    return df


def main():
    print("Generating synthetic data for backtesting...\n")
    
    # Create directories
    earnings_dir = DATA_DIR / "earnings"
    commodities_dir = DATA_DIR / "commodities"
    earnings_dir.mkdir(exist_ok=True)
    commodities_dir.mkdir(exist_ok=True)
    
    # Generate earnings data
    print("1. Generating earnings data (50 stocks, 20 quarters)...")
    earnings_df = generate_earnings_data(num_stocks=50, quarters=20)
    earnings_file = earnings_dir / "earnings_data_synthetic.csv"
    earnings_df.to_csv(earnings_file, index=False)
    print(f"   Saved: {earnings_file} ({len(earnings_df)} records)")
    
    # Generate commodity data
    commodities = ['NG', 'RB', 'HO', 'ZC']
    print(f"\n2. Generating commodity data ({len(commodities)} symbols, 20 years)...")
    
    for comm in commodities:
        df = generate_commodity_data(commodity=comm)
        filename = commodities_dir / f"{comm}_daily_synthetic.csv"
        df.to_csv(filename, index=False)
        print(f"   Saved: {filename} ({len(df)} records)")
    
    print("\n" + "="*60)
    print("SYNTHETIC DATA GENERATION COMPLETE")
    print("="*60)
    print(f"\nEarnings: {len(earnings_df)} records")
    print(f"Commodities: {len(commodities)} symbols, ~{len(df) * len(commodities)} total records")
    print("\nNote: This is synthetic data for testing backtest engines.")
    print("Replace with real data from JT Trading Agent for production.")


if __name__ == '__main__':
    main()
