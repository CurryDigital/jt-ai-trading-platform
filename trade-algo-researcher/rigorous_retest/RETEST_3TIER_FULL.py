#!/usr/bin/env python3
"""
RE-TEST WITH FULL 3-TIER ANALYSIS + LAST Q P&L
Train 2021-2022 / Test 2023-2024 / Validate 2025+
"""

import pandas as pd
import numpy as np
import sys
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
from db_backtest_engine import TradeAlgoDB
from backtest_analytics import BacktestAnalytics

db = TradeAlgoDB()
conn = db.connect()

# 3-Tier Periods
TRAIN_START, TRAIN_END = '2021-01-01', '2022-12-31'
TEST_START, TEST_END = '2023-01-01', '2024-12-31'
VALIDATE_START = '2025-01-01'
LAST_Q_START = '2024-10-01'  # Last quarter for P&L

def fetch_data(ticker):
    query = f"""
    SELECT date, close FROM silver.unified_prices
    WHERE ticker = '{ticker}' AND date >= '2021-01-01' ORDER BY date
    """
    df = pd.read_sql(query, conn)
    if len(df) == 0:
        return None
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def fetch_rsi(ticker):
    query = f"""
    SELECT date, rsi_14 FROM gold.technical_indicators_calculated
    WHERE ticker = '{ticker}' AND date >= '2021-01-01' ORDER BY date
    """
    df = pd.read_sql(query, conn)
    if len(df) == 0:
        return None
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def test_rsi_full_3tier(ticker, threshold=35):
    """Test RSI with FULL 3-tier breakdown + Last Q P&L"""
    prices = fetch_data(ticker)
    rsi = fetch_rsi(ticker)
    
    if prices is None or rsi is None:
        return None
    
    df = prices.join(rsi, how='inner')
    
    HOLD_DAYS = 10
    all_trades = []
    in_position = False
    entry_date = None
    entry_price = None
    
    for i in range(len(df) - HOLD_DAYS):
        row = df.iloc[i]
        
        if not in_position and row['rsi_14'] < threshold and not pd.isna(row['close']):
            in_position = True
            entry_date = df.index[i]
            entry_price = row['close']
        elif in_position:
            days_held = (df.index[i] - entry_date).days
            if days_held >= HOLD_DAYS:
                exit_price = df.iloc[i]['close']
                pnl = (exit_price - entry_price) / entry_price * 100
                all_trades.append({
                    'entry_date': entry_date,
                    'exit_date': df.index[i],
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl': pnl
                })
                in_position = False
                entry_date = None
                entry_price = None
    
    if len(all_trades) < 20:
        return None
    
    trades_df = pd.DataFrame(all_trades)
    trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date'])
    
    # Split into tiers
    train_trades = trades_df[(trades_df['entry_date'] >= TRAIN_START) & (trades_df['entry_date'] <= TRAIN_END)]
    test_trades = trades_df[(trades_df['entry_date'] >= TEST_START) & (trades_df['entry_date'] <= TEST_END)]
    validate_trades = trades_df[trades_df['entry_date'] >= VALIDATE_START]
    last_q_trades = trades_df[trades_df['entry_date'] >= LAST_Q_START]
    
    analytics = BacktestAnalytics()
    
    # Calculate metrics for each tier
    def calc_metrics(trades):
        if len(trades) < 3:
            return {'trades': len(trades), 'wr': 0, 'avg_pnl': 0, 'total_pnl': 0}
        m = analytics.calculate_metrics(trades, hold_days=HOLD_DAYS)
        total_pnl = trades['pnl'].sum()
        avg_pnl = trades['pnl'].mean()
        return {
            'trades': len(trades),
            'wr': m['win_rate'],
            'avg_pnl': avg_pnl,
            'total_pnl': total_pnl
        }
    
    train_m = calc_metrics(train_trades)
    test_m = calc_metrics(test_trades)
    validate_m = calc_metrics(validate_trades)
    last_q_m = calc_metrics(last_q_trades)
    
    # MC on test period
    mc = analytics.monte_carlo_simulation(test_trades, n_simulations=1000, hold_days=HOLD_DAYS) if len(test_trades) >= 10 else {'mc_robustness_score': 0}
    
    # Decay analysis
    decay_train_test = train_m['wr'] - test_m['wr'] if train_m['trades'] > 0 and test_m['trades'] > 0 else 0
    decay_test_validate = test_m['wr'] - validate_m['wr'] if test_m['trades'] > 0 and validate_m['trades'] > 0 else 0
    
    return {
        'ticker': ticker,
        'threshold': threshold,
        'total_trades': len(all_trades),
        
        # 3-Tier Win Rates
        'train_wr': train_m['wr'],
        'train_trades': train_m['trades'],
        'test_wr': test_m['wr'],
        'test_trades': test_m['trades'],
        'validate_wr': validate_m['wr'],
        'validate_trades': validate_m['trades'],
        
        # Decay
        'decay_train_test': decay_train_test,
        'decay_test_validate': decay_test_validate,
        'max_decay': max(abs(decay_train_test), abs(decay_test_validate)),
        
        # Last Q P&L
        'last_q_pnl': last_q_m['total_pnl'],
        'last_q_trades': last_q_m['trades'],
        
        # MC
        'mc_robust': mc['mc_robustness_score'],
    }

def classify_tier_1(result):
    """Strict Tier 1: Must pass ALL criteria"""
    checks = {
        'test_wr_55': result['test_wr'] >= 55,
        'test_trades_20': result['test_trades'] >= 20,
        'mc_70': result['mc_robust'] >= 70,
        'max_decay_20': result['max_decay'] <= 20,
        'last_q_positive': result['last_q_pnl'] > 0,
    }
    score = sum(checks.values())
    return score == 5, score, checks

def main():
    print("=" * 100)
    print("FULL 3-TIER ANALYSIS + LAST Q P&L")
    print("Train 2021-2022 | Test 2023-2024 | Validate 2025+ | Last Q P&L")
    print("=" * 100)
    
    # Top performers to re-test with full analysis
    tickers = [
        'META', 'GOOGL', 'SHOP', 'COIN', '0700.HK', '1398.HK',
        'QQQ', 'AMZN', 'MSFT', 'AAPL', 'PLTR', 'BTC-USD',
        'TSLA', 'AMD', 'NVDA', 'SOL-USD', '3988.HK', '0005.HK'
    ]
    
    tier_1 = []
    tier_2 = []
    rejected = []
    
    for ticker in tickers:
        print(f"\n🧪 {ticker}")
        result = test_rsi_full_3tier(ticker)
        
        if result is None:
            print(f"  ❌ Insufficient data")
            continue
        
        is_tier_1, score, checks = classify_tier_1(result)
        
        # Print 3-tier breakdown
        print(f"  Trades: Train={result['train_trades']} | Test={result['test_trades']} | Validate={result['validate_trades']}")
        print(f"  Win Rate: Train={result['train_wr']:.1f}% | Test={result['test_wr']:.1f}% | Validate={result['validate_wr']:.1f}%")
        print(f"  Decay: T→T={result['decay_train_test']:.1f}% | T→V={result['decay_test_validate']:.1f}% | Max={result['max_decay']:.1f}%")
        print(f"  Last Q P&L: {result['last_q_pnl']:.1f}% ({result['last_q_trades']} trades)")
        print(f"  MC Robust: {result['mc_robust']:.1f}% | Score: {score}/5")
        
        if is_tier_1:
            print(f"  🏆 TIER 1 GOLDEN")
            tier_1.append(result)
        elif score >= 3:
            print(f"  ⭐ TIER 2 VALIDATED")
            tier_2.append(result)
        else:
            print(f"  ❌ REJECTED")
            rejected.append(result)
    
    # Summary
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    
    print(f"\n🏆 TIER 1 GOLDEN: {len(tier_1)}")
    for r in tier_1:
        print(f"  {r['ticker']}: Test {r['test_wr']:.1f}%, Val {r['validate_wr']:.1f}%, LastQ {r['last_q_pnl']:.1f}%, MC {r['mc_robust']:.1f}%")
    
    print(f"\n⭐ TIER 2 VALIDATED: {len(tier_2)}")
    for r in tier_2:
        print(f"  {r['ticker']}: Test {r['test_wr']:.1f}%, Val {r['validate_wr']:.1f}%, LastQ {r['last_q_pnl']:.1f}%")
    
    print(f"\n❌ REJECTED: {len(rejected)}")
    
    conn.close()
    print(f"\n{'='*100}")

if __name__ == '__main__':
    main()
