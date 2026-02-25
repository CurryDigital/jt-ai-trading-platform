#!/usr/bin/env python3
"""
Comprehensive Multi-Market Hypothesis Testing
Tests all stock hypotheses across US, HK, CN, SG in parallel
Maps each strategy to its specific working universe
"""

import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path
import json
import warnings
from datetime import datetime
warnings.filterwarnings('ignore')

RESULTS_DIR = Path(__file__).parent.parent / "results"
STRATEGIES_DIR = Path(__file__).parent.parent / "strategies"
RESULTS_DIR.mkdir(exist_ok=True)

# Define complete universe
UNIVERSE = {
    'US': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'JPM', 'V', 'WMT',
           'JNJ', 'UNH', 'XOM', 'LLY', 'AVGO', 'T', 'MA', 'HD', 'PG', 'CVX',
           'MRK', 'ABBV', 'PEP', 'KO', 'BAC', 'COST', 'CSCO', 'MCD', 'ADBE', 'WFC',
           'CRM', 'PFE', 'ACN', 'DIS', 'ABT', 'LIN', 'NKE', 'TXN', 'VZ', 'DHR',
           'BMY', 'RTX', 'HON', 'AMGN', 'QCOM', 'SPGI', 'UPS', 'NEE', 'SCHW', 'LOW',
           'SPY', 'QQQ', 'IWM', 'XLF', 'XLK', 'XLE', 'XLU', 'XLI', 'XLP', 'XLB'],
    'HK': ['0001.HK', '0002.HK', '0003.HK', '0005.HK', '0006.HK', '0011.HK', '0012.HK',
           '0016.HK', '0017.HK', '0027.HK', '0066.HK', '0101.HK', '0175.HK', '0241.HK',
           '0267.HK', '0293.HK', '0386.HK', '0388.HK', '0688.HK', '0700.HK',
           '0836.HK', '0857.HK', '0883.HK', '0939.HK', '0998.HK', '1038.HK',
           '1044.HK', '1093.HK', '1109.HK', '1113.HK', '1177.HK', '1211.HK', '1299.HK',
           '1398.HK', '1658.HK', '1810.HK', '1876.HK', '1928.HK', '1997.HK',
           '2313.HK', '2318.HK', '2319.HK', '2382.HK', '2388.HK', '2628.HK', '2688.HK',
           '2888.HK', '2899.HK', '3690.HK', '9633.HK', '9988.HK', '9999.HK'],
    'CN': ['BABA', 'JD', 'PDD', 'NIO', 'LI', 'XPEV', 'BIDU', 'TCEHY', 'BEKE', 'ZTO',
           'TAL', 'GOTU', 'FUTU', 'LU', 'ZH', 'IQ', 'HUYA', 'DOYU', 'WB', 'VIPS',
           'MOMO', 'YY', 'MCHI', 'KWEB', 'ASHR', 'FXI', 'CXSE', 'CQQQ', 'CHIQ', 'CHIX',
           'YINN', 'CHAU', 'PGJ', 'GXC'],
    'SG': ['EWS', 'U11.SI', 'Z74.SI', 'D05.SI', 'G13.SI', 'S63.SI',
           'O39.SI', 'M44U.SI', 'A17U.SI', 'C38U.SI', 'S58.SI', 'Y92.SI',
           'BS6.SI', 'C61U.SI', 'H78.SI', 'N2IU.SI', 'T82U.SI', 'U14.SI',
           'C09.SI', 'S51.SI', 'CC3.SI', 'F34.SI', 'Q0F.SI', 'S68.SI',
           'RW0U.SI', 'AJBU.SI', 'BUOU.SI', 'ME8U.SI', 'CRPU.SI', 'MINT', 'CRT']
}

def get_data(ticker, start='2019-01-01', end='2024-12-31'):
    """Get OHLCV data."""
    try:
        data = yf.download(ticker, start=start, end=end, progress=False)
        if data.empty or len(data) < 100:
            return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except:
        return None

# Strategy implementations
def strategy_3day_reversal(data):
    """3-Day Reversal with volume confirmation."""
    if data is None or len(data) < 50:
        return None
    closes = data['Close'].values.flatten()
    volumes = data['Volume'].values.flatten()
    returns = pd.Series(closes).pct_change().values
    avg_volume = pd.Series(volumes).rolling(20).mean().values
    
    trades = []
    for i in range(20, len(data) - 4):
        if not (returns[i-2] < 0 and returns[i-1] < 0 and returns[i] < 0):
            continue
        if (closes[i] - closes[i-3]) / closes[i-3] > -0.05:
            continue
        if volumes[i] / avg_volume[i] < 1.3:
            continue
        pnl = (closes[i+4] - closes[i+1]) / closes[i+1]
        trades.append(pnl)
    
    if len(trades) < 5:
        return None
    return {'trades': len(trades), 'win_rate': np.mean([t > 0 for t in trades]), 
            'avg_return': np.mean(trades), 'sharpe': np.mean(trades) / np.std(trades) * np.sqrt(252/3) if np.std(trades) > 0 else 0}

def strategy_gap_fade(data):
    """Opening gap fade."""
    if data is None or len(data) < 20:
        return None
    opens = data['Open'].values.flatten()
    closes = data['Close'].values.flatten()
    
    trades = []
    for i in range(1, len(data)):
        gap = (opens[i] - closes[i-1]) / closes[i-1]
        if abs(gap) < 0.005:
            continue
        pnl = (opens[i] - closes[i]) / opens[i] if gap > 0 else (closes[i] - opens[i]) / opens[i]
        trades.append(pnl)
    
    if len(trades) < 10:
        return None
    return {'trades': len(trades), 'win_rate': np.mean([t > 0 for t in trades]),
            'avg_return': np.mean(trades), 'sharpe': np.mean(trades) / np.std(trades) * np.sqrt(252) if np.std(trades) > 0 else 0}

def strategy_rsi_mean_reversion(data):
    """RSI < 30 bounce."""
    if data is None or len(data) < 50:
        return None
    closes = data['Close'].values.flatten()
    volumes = data['Volume'].values.flatten()
    
    # Calculate RSI
    delta = pd.Series(closes).diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    avg_volume = pd.Series(volumes).rolling(20).mean()
    
    trades = []
    for i in range(30, len(data) - 5):
        if rsi.iloc[i] < 30 and volumes[i] > avg_volume.iloc[i] * 1.3:
            pnl = (closes[i+5] - closes[i+1]) / closes[i+1]
            trades.append(pnl)
    
    if len(trades) < 5:
        return None
    return {'trades': len(trades), 'win_rate': np.mean([t > 0 for t in trades]),
            'avg_return': np.mean(trades), 'sharpe': np.mean(trades) / np.std(trades) * np.sqrt(252/5) if np.std(trades) > 0 else 0}

def strategy_macd_divergence(data):
    """MACD histogram divergence."""
    if data is None or len(data) < 50:
        return None
    closes = data['Close'].values.flatten()
    ema_fast = pd.Series(closes).ewm(span=12).mean()
    ema_slow = pd.Series(closes).ewm(span=26).mean()
    macd = ema_fast - ema_slow
    macd_hist = macd - macd.ewm(span=9).mean()
    
    trades = []
    for i in range(20, len(data) - 6):
        price_high = pd.Series(closes[i-10:i]).max()
        hist_high = macd_hist.iloc[i-10:i].max()
        if closes[i] > price_high * 0.98 and macd_hist.iloc[i] < hist_high * 0.8:
            pnl = (closes[i+1] - closes[i+6]) / closes[i+1]  # Short
            trades.append(pnl)
    
    if len(trades) < 5:
        return None
    return {'trades': len(trades), 'win_rate': np.mean([t > 0 for t in trades]),
            'avg_return': np.mean(trades), 'sharpe': np.mean(trades) / np.std(trades) * np.sqrt(252/5) if np.std(trades) > 0 else 0}

def strategy_momentum_20day(data):
    """20-day momentum."""
    if data is None or len(data) < 50:
        return None
    closes = data['Close'].values.flatten()
    ret_20 = pd.Series(closes).pct_change(20)
    
    trades = []
    for i in range(30, len(data) - 20):
        if ret_20.iloc[i] > 0.05:
            pnl = (closes[i+20] - closes[i+1]) / closes[i+1]
            trades.append(pnl)
    
    if len(trades) < 5:
        return None
    return {'trades': len(trades), 'win_rate': np.mean([t > 0 for t in trades]),
            'avg_return': np.mean(trades), 'sharpe': np.mean(trades) / np.std(trades) * np.sqrt(252/20) if np.std(trades) > 0 else 0}

STRATEGIES = {
    '3Day_Reversal': strategy_3day_reversal,
    'Gap_Fade': strategy_gap_fade,
    'RSI_MeanReversion': strategy_rsi_mean_reversion,
    'MACD_Divergence': strategy_macd_divergence,
    'Momentum_20Day': strategy_momentum_20day
}

def test_all_hypotheses():
    print("=" * 80)
    print("COMPREHENSIVE MULTI-MARKET HYPOTHESIS TESTING")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("Markets: US, HK, CN, SG")
    print("Strategies: 5 technical analysis hypotheses")
    print("=" * 80)
    
    # Results structure: {strategy: {market: {ticker: results}}}
    all_results = {s: {m: {} for m in UNIVERSE.keys()} for s in STRATEGIES.keys()}
    
    for market, tickers in UNIVERSE.items():
        print(f"\n{'='*60}")
        print(f"MARKET: {market} ({len(tickers)} tickers)")
        print('='*60)
        
        for i, ticker in enumerate(tickers, 1):
            print(f"[{i}/{len(tickers)}] {ticker}...", end=' ', flush=True)
            
            data = get_data(ticker)
            if data is None:
                print("❌ No data")
                continue
            
            print(f"✓ ({len(data)} days)")
            
            for strat_name, strat_func in STRATEGIES.items():
                try:
                    result = strat_func(data)
                    if result:
                        all_results[strat_name][market][ticker] = result
                except Exception as e:
                    pass
    
    return all_results

def analyze_results(all_results):
    print("\n" + "=" * 80)
    print("RESULTS ANALYSIS")
    print("=" * 80)
    
    strategy_universes = {}
    
    for strat_name, market_results in all_results.items():
        print(f"\n{'='*60}")
        print(f"STRATEGY: {strat_name}")
        print('='*60)
        
        strategy_universes[strat_name] = {}
        
        for market, ticker_results in market_results.items():
            if not ticker_results:
                continue
            
            df = pd.DataFrame.from_dict(ticker_results, orient='index')
            df.index.name = 'ticker'
            df = df.reset_index()
            
            # Find passing tickers (win rate > 55%)
            passing = df[df['win_rate'] > 0.55]
            
            print(f"\n{market} Market:")
            print(f"  Total tested: {len(df)}")
            print(f"  Passing (WR > 55%): {len(passing)}")
            
            if len(passing) > 0:
                print(f"  Top performers:")
                top = passing.nlargest(5, 'win_rate')[['ticker', 'win_rate', 'sharpe', 'trades']]
                for _, row in top.iterrows():
                    print(f"    {row['ticker']}: {row['win_rate']:.1%} win, {row['sharpe']:.2f} Sharpe ({int(row['trades'])} trades)")
                
                # Save universe for this strategy-region
                strategy_universes[strat_name][market] = passing['ticker'].tolist()
            else:
                strategy_universes[strat_name][market] = []
    
    return strategy_universes

def create_strategy_definitions(strategy_universes):
    print("\n" + "=" * 80)
    print("STRATEGY DEFINITIONS BY REGION")
    print("=" * 80)
    
    definitions = {}
    
    for strat_name, markets in strategy_universes.items():
        for market, tickers in markets.items():
            if not tickers:
                continue
            
            key = f"{strat_name}_{market}"
            definitions[key] = {
                'strategy': strat_name,
                'market': market,
                'universe': tickers,
                'universe_size': len(tickers),
                'status': 'ACTIVE'
            }
            
            print(f"\n{key}:")
            print(f"  Universe: {len(tickers)} tickers")
            print(f"  Tickers: {', '.join(tickers[:5])}{'...' if len(tickers) > 5 else ''}")
    
    # Save definitions
    with open(RESULTS_DIR / 'strategy_region_definitions.json', 'w') as f:
        json.dump(definitions, f, indent=2)
    
    print(f"\n💾 Saved to results/strategy_region_definitions.json")
    
    return definitions

def generate_summary_table(strategy_universes):
    print("\n" + "=" * 80)
    print("STRATEGY-MARKET MATRIX")
    print("=" * 80)
    
    rows = []
    for strat_name, markets in strategy_universes.items():
        for market, tickers in markets.items():
            rows.append({
                'Strategy_Region': f"{strat_name}_{market}",
                'Strategy': strat_name,
                'Market': market,
                'Tickers': len(tickers),
                'Status': 'ACTIVE' if tickers else 'INACTIVE'
            })
    
    df = pd.DataFrame(rows)
    df = df.sort_values(['Strategy', 'Market'])
    
    print("\nActive Strategy-Region Combinations:")
    active = df[df['Status'] == 'ACTIVE']
    print(active[['Strategy_Region', 'Tickers']].to_string(index=False))
    
    print(f"\nTotal combinations: {len(df)}")
    print(f"Active: {len(active)}")
    print(f"Inactive: {len(df) - len(active)}")
    
    df.to_csv(RESULTS_DIR / 'strategy_region_matrix.csv', index=False)
    print(f"\n💾 Saved to results/strategy_region_matrix.csv")

def main():
    all_results = test_all_hypotheses()
    strategy_universes = analyze_results(all_results)
    definitions = create_strategy_definitions(strategy_universes)
    generate_summary_table(strategy_universes)
    
    print("\n" + "=" * 80)
    print("COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
