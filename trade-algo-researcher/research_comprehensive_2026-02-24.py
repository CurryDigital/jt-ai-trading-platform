#!/usr/bin/env python3
"""
Continuous Strategy Research — February 24, 2026
Mission: Comprehensive Strategy Research & Enhancement

Tests:
1. NEW hypotheses (RSI+MACD+Volume, Bearish, Cross-sector, Volatility breakout, Multi-timeframe)
2. Enhance EXISTING validated strategies (ADX filters, hold periods, volume, regime filters)
3. Test on ADDITIONAL tickers (Financials, Energy, Healthcare)
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Configuration
TRAIN_START = "2021-01-01"
TRAIN_END = "2022-12-31"
TEST_START = "2023-01-01"
TEST_END = "2024-12-31"

# Tickers to test
CORE_TICKERS = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMD', 'META', 'SPY', 'QQQ', 'MSTR', 'COIN']
FINANCIAL_TICKERS = ['JPM', 'BAC', 'GS', 'V', 'MA']
ENERGY_TICKERS = ['XLE', 'CVX', 'XOM']
HEALTHCARE_TICKERS = ['XLV', 'JNJ', 'PFE']

ALL_TICKERS = CORE_TICKERS + FINANCIAL_TICKERS + ENERGY_TICKERS + HEALTHCARE_TICKERS

def calculate_indicators(df):
    """Calculate all technical indicators"""
    df = df.copy()
    
    # Handle MultiIndex columns from yfinance
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # Price data - use Adj Close if available, otherwise Close
    if 'Adj Close' in df.columns:
        df['Close'] = df['Adj Close']
    elif 'Close' in df.columns:
        df['Close'] = df['Close']
    
    # Ensure we have all required columns
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Moving averages
    for period in [10, 20, 50, 200]:
        df[f'SMA_{period}'] = df['Close'].rolling(window=period).mean()
    
    # Weekly SMA (for multi-timeframe)
    df['Weekly_SMA_10'] = df['Close'].rolling(window=50).mean()  # Approx 10 weeks
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    # Bollinger Bands
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    bb_std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle'] * 100
    df['BB_PctB'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
    
    # ATR and ATR-based volatility
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()
    df['ATR_20'] = tr.rolling(window=20).mean()
    df['ATR_Ratio'] = df['ATR'] / df['Close'] * 100
    
    # ATR Compression (lowest 20 days)
    df['ATR_Lowest_20'] = df['ATR'].rolling(window=20).min()
    df['ATR_Compression'] = df['ATR'] <= df['ATR_Lowest_20'] * 1.05
    
    # ADX
    plus_dm = df['High'].diff()
    minus_dm = df['Low'].diff(-1).abs()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    
    atr = tr.rolling(window=14).mean()
    plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=14).mean() / atr)
    dx = (np.abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    df['ADX'] = dx.rolling(window=14).mean()
    df['Plus_DI'] = plus_di
    df['Minus_DI'] = minus_di
    
    # Volume
    df['Volume_SMA_20'] = df['Volume'].rolling(window=20).mean()
    df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA_20']
    
    # Daily returns
    df['Return_1d'] = df['Close'].pct_change()
    df['Return_3d'] = df['Close'].pct_change(3)
    df['Return_5d'] = df['Close'].pct_change(5)
    df['Return_10d'] = df['Close'].pct_change(10)
    
    return df

def backtest_strategy(df, entry_mask, hold_days=5, is_short=False):
    """Backtest a strategy and return results"""
    results = []
    
    for i in range(len(df) - hold_days):
        if entry_mask.iloc[i]:
            entry_price = df['Close'].iloc[i]
            if is_short:
                exit_price = df['Close'].iloc[i + hold_days]
                ret = (entry_price - exit_price) / entry_price
            else:
                exit_price = df['Close'].iloc[i + hold_days]
                ret = (exit_price - entry_price) / entry_price
            
            results.append({
                'entry_date': df.index[i],
                'exit_date': df.index[i + hold_days],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'return': ret,
                'win': 1 if ret > 0 else 0
            })
    
    return pd.DataFrame(results)

def calculate_confidence_interval(wins, total):
    """Calculate 95% confidence interval for win rate"""
    if total == 0:
        return (0, 0)
    p = wins / total
    z = 1.96  # 95% CI
    margin = z * np.sqrt(p * (1 - p) / total)
    return (max(0, p - margin) * 100, min(1, p + margin) * 100)

def run_hypothesis(df_train, df_test, name, entry_fn, hold_days=5, is_short=False):
    """Run a hypothesis on train and test data"""
    try:
        train_mask = entry_fn(df_train)
        test_mask = entry_fn(df_test)
        
        train_results = backtest_strategy(df_train, train_mask, hold_days, is_short)
        test_results = backtest_strategy(df_test, test_mask, hold_days, is_short)
        
        if len(train_results) == 0 or len(test_results) == 0:
            return None
        
        train_wr = train_results['win'].mean() * 100
        test_wr = test_results['win'].mean() * 100
        decay = train_wr - test_wr
        
        train_n = len(train_results)
        test_n = len(test_results)
        
        ci_lower, ci_upper = calculate_confidence_interval(test_results['win'].sum(), test_n)
        avg_return = test_results['return'].mean() * 100
        
        # Determine status
        if test_wr >= 70 and test_n >= 30 and abs(decay) < 15:
            status = "GOLDEN"
        elif test_wr >= 55 and test_n >= 10:
            status = "VALIDATED"
        elif test_wr >= 50 and test_n >= 5:
            status = "NEAR-VALIDATED"
        else:
            status = "REJECTED"
        
        return {
            'name': name,
            'train_wr': round(train_wr, 1),
            'test_wr': round(test_wr, 1),
            'train_n': train_n,
            'test_n': test_n,
            'decay': round(decay, 1),
            'ci_lower': round(ci_lower, 1),
            'ci_upper': round(ci_upper, 1),
            'avg_return': round(avg_return, 2),
            'status': status,
            'is_short': is_short
        }
    except Exception as e:
        print(f"Error in {name}: {e}")
        return None

def fetch_data(ticker):
    """Fetch and prepare data for a ticker"""
    try:
        df = yf.download(ticker, start=TRAIN_START, end=TEST_END, progress=False)
        if len(df) < 100:
            print(f"Insufficient data for {ticker}")
            return None, None
        
        df = calculate_indicators(df)
        
        # Split train/test
        train_mask = df.index <= TRAIN_END
        test_mask = df.index >= TEST_START
        
        df_train = df[train_mask].dropna()
        df_test = df[test_mask].dropna()
        
        if len(df_train) < 50 or len(df_test) < 30:
            return None, None
        
        return df_train, df_test
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None, None

def run_all_hypotheses_for_ticker(ticker, df_train, df_test):
    """Run all hypothesis tests for a single ticker"""
    results = []
    
    # ========== NEW HYPOTHESIS TESTS ==========
    
    # H1: RSI + MACD + Volume Combinations
    results.append(run_hypothesis(df_train, df_test, "H1a_RSI40_MACD_Volume", 
        lambda df: (df['RSI'] < 40) & (df['MACD'] > df['MACD_Signal']) & (df['Volume_Ratio'] > 1.0) & (df['Close'] > df['SMA_50'])))
    
    results.append(run_hypothesis(df_train, df_test, "H1b_RSI50_MACD0_Volume", 
        lambda df: (df['RSI'] < 50) & (df['RSI'] > 30) & (df['MACD'] > 0) & (df['Volume_Ratio'] > 1.0) & (df['Close'] > df['SMA_20'])))
    
    results.append(run_hypothesis(df_train, df_test, "H1c_RSI45_MACDHist_Volume", 
        lambda df: (df['RSI'] < 45) & (df['MACD_Hist'] > 0) & (df['MACD_Hist'].shift(1) <= 0) & (df['Volume_Ratio'] > 0.9)))
    
    results.append(run_hypothesis(df_train, df_test, "H1d_RSI35_MACD_Cross", 
        lambda df: (df['RSI'] < 35) & (df['MACD'] > df['MACD_Signal']) & (df['MACD'].shift(1) <= df['MACD_Signal'].shift(1)) & (df['Volume_Ratio'] > 1.0)))
    
    # H2: Bearish Strategies (Short-selling)
    results.append(run_hypothesis(df_train, df_test, "H2a_Bearish_RSI70_Short", 
        lambda df: (df['RSI'] > 70) & (df['Close'] < df['SMA_20']), 5, True))
    
    results.append(run_hypothesis(df_train, df_test, "H2b_Bearish_RSI75_ADX_Short", 
        lambda df: (df['RSI'] > 75) & (df['ADX'] > 30) & (df['Close'] < df['SMA_50']), 5, True))
    
    results.append(run_hypothesis(df_train, df_test, "H2c_Bearish_BB_Upper_Short", 
        lambda df: (df['Close'] > df['BB_Upper'] * 0.98) & (df['RSI'] > 65) & (df['Volume_Ratio'] > 1.2), 5, True))
    
    results.append(run_hypothesis(df_train, df_test, "H2d_Bearish_MACD_Diverge_Short", 
        lambda df: (df['MACD'] < df['MACD'].shift(5)) & (df['Close'] > df['Close'].shift(5)) & (df['RSI'] > 60), 5, True))
    
    # H4: Volatility Breakout Patterns (different from BB Squeeze)
    results.append(run_hypothesis(df_train, df_test, "H4a_ATR_Breakout", 
        lambda df: (df['ATR_Compression'].shift(1)) & (df['Close'] > df['High'].shift(1)) & (df['Close'] > df['SMA_50'])))
    
    results.append(run_hypothesis(df_train, df_test, "H4b_Volatility_Expansion", 
        lambda df: (df['ATR_Ratio'] < df['ATR_Ratio'].rolling(20).quantile(0.2).shift(1)) & 
                   (df['ATR_Ratio'] > df['ATR_Ratio'].shift(1) * 1.5) & (df['Close'] > df['SMA_50'])))
    
    results.append(run_hypothesis(df_train, df_test, "H4c_Keltner_Breakout", 
        lambda df: (df['Close'] > df['SMA_20'] + 2 * df['ATR_20']) & (df['Volume_Ratio'] > 1.0) & (df['ADX'] > 25)))
    
    results.append(run_hypothesis(df_train, df_test, "H4d_Range_Breakout", 
        lambda df: ((df['High'].rolling(20).max() - df['Low'].rolling(20).min()) / df['Close'] < 0.05) & 
                   (df['Close'] > df['High'].rolling(20).max().shift(1))))
    
    # H5: Multi-timeframe Confluence
    results.append(run_hypothesis(df_train, df_test, "H5a_Daily_Weekly_Align", 
        lambda df: (df['Close'] > df['SMA_50']) & (df['Close'] > df['Weekly_SMA_10']) & (df['RSI'] < 50) & (df['RSI'] > 35)))
    
    results.append(run_hypothesis(df_train, df_test, "H5b_Trend_Align_RSI", 
        lambda df: (df['SMA_20'] > df['SMA_50']) & (df['SMA_50'] > df['SMA_200']) & (df['RSI'] < 45)))
    
    results.append(run_hypothesis(df_train, df_test, "H5c_ADX_Trend_Weekly", 
        lambda df: (df['ADX'] > 25) & (df['Close'] > df['SMA_50']) & (df['Close'] > df['Weekly_SMA_10']) & (df['RSI'] < 55)))
    
    # ========== ENHANCEMENT TESTS ==========
    
    # E1: ADX Filters on existing strategies
    results.append(run_hypothesis(df_train, df_test, "E1a_RSI30_ADX20", 
        lambda df: (df['RSI'] < 30) & (df['ADX'] > 20) & (df['Close'] > df['SMA_50'])))
    
    results.append(run_hypothesis(df_train, df_test, "E1b_RSI30_ADX25", 
        lambda df: (df['RSI'] < 30) & (df['ADX'] > 25) & (df['Close'] > df['SMA_50'])))
    
    results.append(run_hypothesis(df_train, df_test, "E1c_RSI30_ADX30", 
        lambda df: (df['RSI'] < 30) & (df['ADX'] > 30) & (df['Close'] > df['SMA_50'])))
    
    # E2: Different Hold Periods
    for hold_days in [3, 10]:
        results.append(run_hypothesis(df_train, df_test, f"E2a_RSI30_Hold{hold_days}", 
            lambda df: (df['RSI'] < 30) & (df['Close'] > df['SMA_50']), hold_days))
    
    # E3: Volume Confirmation
    results.append(run_hypothesis(df_train, df_test, "E3a_RSI30_Volume1.1x", 
        lambda df: (df['RSI'] < 30) & (df['Volume_Ratio'] > 1.1) & (df['Close'] > df['SMA_50'])))
    
    results.append(run_hypothesis(df_train, df_test, "E3b_RSI30_Volume1.3x", 
        lambda df: (df['RSI'] < 30) & (df['Volume_Ratio'] > 1.3) & (df['Close'] > df['SMA_50'])))
    
    # E4: Market Regime Filters (SPY trend)
    # Note: For single ticker tests, we'll approximate with price > SMA200
    results.append(run_hypothesis(df_train, df_test, "E4a_RSI30_Uptrend_Only", 
        lambda df: (df['RSI'] < 30) & (df['Close'] > df['SMA_200']) & (df['SMA_50'] > df['SMA_200'])))
    
    results.append(run_hypothesis(df_train, df_test, "E4b_RSI30_Strong_Uptrend", 
        lambda df: (df['RSI'] < 30) & (df['Close'] > df['SMA_200']) & (df['ADX'] > 25)))
    
    # ========== EXISTING STRATEGY VARIATIONS ==========
    
    # BB Walk variations
    results.append(run_hypothesis(df_train, df_test, "BB_Walk_ADX25", 
        lambda df: (df['Close'] > df['BB_Upper'] * 0.98) & (df['ADX'] > 25) & (df['Close'] > df['SMA_50']), 3))
    
    results.append(run_hypothesis(df_train, df_test, "BB_Walk_ADX35", 
        lambda df: (df['Close'] > df['BB_Upper'] * 0.98) & (df['ADX'] > 35) & (df['Close'] > df['SMA_50']), 3))
    
    # Momentum variations
    results.append(run_hypothesis(df_train, df_test, "Momentum_ADX20_RSI60", 
        lambda df: (df['Close'] > df['SMA_50']) & (df['ADX'] > 20) & (df['RSI'] < 60), 5))
    
    # Filter out None results
    return [r for r in results if r is not None]

def main():
    """Main research execution"""
    print("=" * 80)
    print("CONTINUOUS STRATEGY RESEARCH — February 24, 2026")
    print("=" * 80)
    print(f"Train Period: {TRAIN_START} to {TRAIN_END}")
    print(f"Test Period: {TEST_START} to {TEST_END}")
    print(f"Tickers: {len(ALL_TICKERS)} ({', '.join(ALL_TICKERS)})")
    print("=" * 80)
    
    all_results = []
    
    for ticker in ALL_TICKERS:
        print(f"\n📊 Testing {ticker}...")
        df_train, df_test = fetch_data(ticker)
        
        if df_train is None:
            print(f"  ⚠️  Skipping {ticker} - insufficient data")
            continue
        
        results = run_all_hypotheses_for_ticker(ticker, df_train, df_test)
        
        for r in results:
            r['ticker'] = ticker
            all_results.append(r)
        
        # Count by status
        golden = sum(1 for r in results if r['status'] == 'GOLDEN')
        validated = sum(1 for r in results if r['status'] == 'VALIDATED')
        rejected = sum(1 for r in results if r['status'] == 'REJECTED')
        
        print(f"  ✅ Golden: {golden} | Validated: {validated} | Rejected: {rejected}")
    
    # Convert to DataFrame for analysis
    df_results = pd.DataFrame(all_results)
    
    if len(df_results) == 0:
        print("\n❌ No results generated")
        return None
    
    # Summary by category
    print("\n" + "=" * 80)
    print("SUMMARY BY HYPOTHESIS CATEGORY")
    print("=" * 80)
    
    categories = {
        'H1: RSI+MACD+Volume': 'H1',
        'H2: Bearish Strategies': 'H2',
        'H3: Cross-Sector (by ticker group)': 'H3',
        'H4: Volatility Breakout': 'H4',
        'H5: Multi-timeframe': 'H5',
        'E1: ADX Enhancement': 'E1',
        'E2: Hold Period': 'E2',
        'E3: Volume Enhancement': 'E3',
        'E4: Regime Filter': 'E4',
        'Existing Variations': 'BB_Walk|Momentum'
    }
    
    for cat_name, prefix in categories.items():
        if prefix in ['H3']:
            continue  # Skip H3, handled separately
        cat_results = df_results[df_results['name'].str.contains(prefix)]
        if len(cat_results) > 0:
            golden = len(cat_results[cat_results['status'] == 'GOLDEN'])
            validated = len(cat_results[cat_results['status'] == 'VALIDATED'])
            rejected = len(cat_results[cat_results['status'] == 'REJECTED'])
            avg_wr = cat_results['test_wr'].mean()
            print(f"{cat_name:30s}: Golden={golden:2d}, Valid={validated:2d}, Rej={rejected:2d}, AvgWR={avg_wr:.1f}%")
    
    # H3: Cross-sector analysis
    print("\n" + "-" * 80)
    print("H3: CROSS-SECTOR STRATEGY TRANSFER")
    print("-" * 80)
    
    sector_map = {
        'Tech': CORE_TICKERS,
        'Financials': FINANCIAL_TICKERS,
        'Energy': ENERGY_TICKERS,
        'Healthcare': HEALTHCARE_TICKERS
    }
    
    for sector, tickers in sector_map.items():
        sector_results = df_results[df_results['ticker'].isin(tickers)]
        if len(sector_results) > 0:
            golden = len(sector_results[sector_results['status'] == 'GOLDEN'])
            validated = len(sector_results[sector_results['status'] == 'VALIDATED'])
            avg_wr = sector_results['test_wr'].mean()
            print(f"{sector:15s}: Golden={golden:2d}, Validated={validated:2d}, AvgWR={avg_wr:.1f}%")
    
    # Top performers
    print("\n" + "=" * 80)
    print("🏆 TOP 20 PERFORMERS (Golden + Validated)")
    print("=" * 80)
    
    top_results = df_results[df_results['status'].isin(['GOLDEN', 'VALIDATED'])].sort_values('test_wr', ascending=False).head(20)
    
    for idx, row in top_results.iterrows():
        short_flag = " [SHORT]" if row['is_short'] else ""
        print(f"{row['test_wr']:5.1f}% | {row['ticker']:5s} | {row['name']:35s} | n={row['test_n']:3d} | CI=[{row['ci_lower']:.1f}%, {row['ci_upper']:.1f}%]{short_flag}")
    
    # Golden strategies detail
    print("\n" + "=" * 80)
    print("🏆 GOLDEN STRATEGIES DETAIL")
    print("=" * 80)
    
    golden_results = df_results[df_results['status'] == 'GOLDEN'].sort_values('test_wr', ascending=False)
    
    if len(golden_results) > 0:
        for idx, row in golden_results.iterrows():
            short_flag = " [SHORT]" if row['is_short'] else ""
            print(f"\n{row['ticker']:5s} | {row['name']:35s}{short_flag}")
            print(f"       Test WR: {row['test_wr']:.1f}% | n={row['test_n']} | Decay: {row['decay']:.1f}%")
            print(f"       95% CI: [{row['ci_lower']:.1f}%, {row['ci_upper']:.1f}%] | Avg Return: {row['avg_return']:.2f}%")
    else:
        print("No Golden strategies found in this batch.")
    
    # Save results
    df_results.to_csv('/home/ubuntu/.openclaw/workspace/trade-algo-researcher/results/continuous_research_2026-02-24_comprehensive.csv', index=False)
    print(f"\n✅ Results saved to results/continuous_research_2026-02-24_comprehensive.csv")
    print(f"   Total tests run: {len(df_results)}")
    print(f"   Golden strategies: {len(df_results[df_results['status'] == 'GOLDEN'])}")
    print(f"   Validated strategies: {len(df_results[df_results['status'] == 'VALIDATED'])}")
    print(f"   Rejected: {len(df_results[df_results['status'] == 'REJECTED'])}")
    
    return df_results

if __name__ == "__main__":
    results = main()
