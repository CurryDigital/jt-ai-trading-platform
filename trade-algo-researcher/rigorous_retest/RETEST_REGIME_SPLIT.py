#!/usr/bin/env python3
"""
RE-TEST WITH REGIME DETECTION
Split strategies by Bull vs Bear market
Use SPY 200-day MA as regime indicator
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

def fetch_spy_regime():
    """Fetch SPY data and calculate regime (Price > 200d MA = Bull)"""
    query = """
    SELECT date, close FROM silver.unified_prices
    WHERE ticker = 'SPY' AND date >= '2021-01-01' ORDER BY date
    """
    df = pd.read_sql(query, conn)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df['spy_sma200'] = df['close'].rolling(200).mean()
    df['regime'] = np.where(df['close'] > df['spy_sma200'], 'BULL', 'BEAR')
    return df[['regime']]

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

def test_rsi_with_regime(ticker, threshold=35):
    """Test RSI strategy with regime split"""
    prices = fetch_data(ticker)
    rsi = fetch_rsi(ticker)
    regime_df = fetch_spy_regime()
    
    if prices is None or rsi is None:
        return None
    
    # Merge all data
    df = prices.join(rsi, how='inner').join(regime_df, how='inner')
    
    HOLD_DAYS = 10
    trades = []
    in_position = False
    entry_date = None
    entry_regime = None
    
    for i in range(len(df) - HOLD_DAYS):
        row = df.iloc[i]
        
        if not in_position and row['rsi_14'] < threshold and not pd.isna(row['close']):
            in_position = True
            entry_date = df.index[i]
            entry_regime = row['regime']
        elif in_position:
            days_held = (df.index[i] - entry_date).days
            if days_held >= HOLD_DAYS:
                pnl = (df.iloc[i]['close'] - df.loc[entry_date, 'close']) / df.loc[entry_date, 'close'] * 100
                trades.append({
                    'entry_date': entry_date,
                    'exit_date': df.index[i],
                    'pnl': pnl,
                    'regime': entry_regime
                })
                in_position = False
                entry_date = None
                entry_regime = None
    
    if len(trades) < 20:
        return None
    
    trades_df = pd.DataFrame(trades)
    trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date'])
    
    # Split by regime
    bull_trades = trades_df[trades_df['regime'] == 'BULL']
    bear_trades = trades_df[trades_df['regime'] == 'BEAR']
    
    analytics = BacktestAnalytics()
    
    def calc_metrics(trades_subset):
        if len(trades_subset) < 5:
            return {'trades': len(trades_subset), 'wr': 0, 'avg_pnl': 0, 'total_pnl': 0}
        m = analytics.calculate_metrics(trades_subset, hold_days=HOLD_DAYS)
        return {
            'trades': len(trades_subset),
            'wr': m['win_rate'],
            'avg_pnl': trades_subset['pnl'].mean(),
            'total_pnl': trades_subset['pnl'].sum()
        }
    
    bull_m = calc_metrics(bull_trades)
    bear_m = calc_metrics(bear_trades)
    
    # Overall MC
    test_period = trades_df[(trades_df['entry_date'] >= '2023-01-01') & (trades_df['entry_date'] <= '2024-12-31')]
    mc = analytics.monte_carlo_simulation(test_period, n_simulations=1000, hold_days=HOLD_DAYS) if len(test_period) >= 10 else {'mc_robustness_score': 0}
    
    return {
        'ticker': ticker,
        'total_trades': len(trades_df),
        'bull_trades': bull_m['trades'],
        'bull_wr': bull_m['wr'],
        'bull_pnl': bull_m['total_pnl'],
        'bear_trades': bear_m['trades'],
        'bear_wr': bear_m['wr'],
        'bear_pnl': bear_m['total_pnl'],
        'mc_robust': mc['mc_robustness_score'],
        'better_regime': 'BULL' if bull_m['wr'] > bear_m['wr'] else 'BEAR'
    }

def main():
    print("=" * 100)
    print("REGIME-AWARE TESTING: Bull vs Bear Strategies")
    print("Regime = SPY price vs 200-day MA")
    print("=" * 100)
    
    tickers = [
        'TSLA', 'SOL-USD', 'META', 'GOOGL', 'SHOP', 'COIN',
        'PLTR', 'BTC-USD', '0700.HK', '1398.HK', '3988.HK',
        'QQQ', 'AMZN', 'MSFT', 'AAPL', 'AMD', 'NVDA', '0005.HK'
    ]
    
    bull_strategies = []
    bear_strategies = []
    mixed_strategies = []
    
    for ticker in tickers:
        print(f"\n🧪 {ticker}")
        result = test_rsi_with_regime(ticker)
        
        if result is None:
            print(f"  ❌ Insufficient data")
            continue
        
        print(f"  Total: {result['total_trades']} trades")
        print(f"  BULL: {result['bull_trades']} trades, WR {result['bull_wr']:.1f}%, P&L {result['bull_pnl']:.1f}%")
        print(f"  BEAR: {result['bear_trades']} trades, WR {result['bear_wr']:.1f}%, P&L {result['bear_pnl']:.1f}%")
        print(f"  Better in: {result['better_regime']} | MC: {result['mc_robust']:.1f}%")
        
        # Classify
        bull_strong = result['bull_wr'] >= 55 and result['bull_trades'] >= 10
        bear_strong = result['bear_wr'] >= 55 and result['bear_trades'] >= 10
        
        if bull_strong and not bear_strong:
            print(f"  🐂 BULL-ONLY STRATEGY")
            bull_strategies.append(result)
        elif bear_strong and not bull_strong:
            print(f"  🐻 BEAR-ONLY STRATEGY")
            bear_strategies.append(result)
        elif bull_strong and bear_strong:
            print(f"  ⚖️  BOTH REGIMES")
            mixed_strategies.append(result)
        else:
            print(f"  ❌ Weak in both")
    
    # Summary
    print("\n" + "=" * 100)
    print("REGIME-BASED STRATEGY CLASSIFICATION")
    print("=" * 100)
    
    print(f"\n🐂 BULL-ONLY STRATEGIES: {len(bull_strategies)}")
    for r in bull_strategies:
        print(f"  {r['ticker']}: BULL {r['bull_wr']:.1f}% ({r['bull_trades']}t) vs BEAR {r['bear_wr']:.1f}% ({r['bear_trades']}t)")
    
    print(f"\n🐻 BEAR-ONLY STRATEGIES: {len(bear_strategies)}")
    for r in bear_strategies:
        print(f"  {r['ticker']}: BEAR {r['bear_wr']:.1f}% ({r['bear_trades']}t) vs BULL {r['bull_wr']:.1f}% ({r['bull_trades']}t)")
    
    print(f"\n⚖️  BOTH REGIMES: {len(mixed_strategies)}")
    for r in mixed_strategies:
        print(f"  {r['ticker']}: BULL {r['bull_wr']:.1f}% | BEAR {r['bear_wr']:.1f}%")
    
    conn.close()
    print(f"\n{'='*100}")

if __name__ == '__main__':
    main()
