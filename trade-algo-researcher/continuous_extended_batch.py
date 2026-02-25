#!/usr/bin/env python3
"""
Continuous Strategy Research - Extended Batch
New hypotheses: Feb 23, 2026 21:55 UTC
"""

import pandas as pd
import numpy as np
import json
import math
from datetime import datetime
from typing import Dict, Tuple, List

class ResearchEngine:
    def __init__(self):
        self.data_path = '/home/ubuntu/.openclaw/workspace/trade-algo-researcher/data/'
        self.train_end = '2022-12-31'
        self.test_start = '2023-01-01'
        
    def load_data(self, ticker: str) -> pd.DataFrame:
        df = pd.read_csv(f"{self.data_path}{ticker}_indicators.csv")
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        df['train'] = df['date'] <= self.train_end
        return df
    
    def calculate_ci(self, wins: int, total: int) -> Tuple[float, float]:
        if total == 0:
            return 0, 0
        p = wins / total
        z = 1.96
        denominator = 1 + z**2 / total
        center = (p + z**2 / (2 * total)) / denominator
        margin = z * math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denominator
        return max(0, center - margin) * 100, min(1, center + margin) * 100
    
    def test_stoch_bb_combo(self, tickers: List[str]) -> Dict:
        """H1: Stochastic < 20 + Price below BB Lower = Mean Reversion"""
        results = {}
        for ticker in tickers:
            df = self.load_data(ticker)
            trades_train, trades_test = [], []
            
            for i in range(1, len(df) - 5):
                row = df.iloc[i]
                future = df.iloc[i + 5]
                
                stoch_ok = row.get('stoch_k', 50) < 20
                bb_ok = row['close'] < row.get('bb_lower', row['close'])
                
                if stoch_ok and bb_ok:
                    pnl = (future['close'] - row['close']) / row['close'] * 100
                    trade = {'pnl_pct': pnl, 'date': row['date']}
                    if row['train']:
                        trades_train.append(trade)
                    else:
                        trades_test.append(trade)
            
            train_wins = sum(1 for t in trades_train if t['pnl_pct'] > 0)
            test_wins = sum(1 for t in trades_test if t['pnl_pct'] > 0)
            train_wr = (train_wins / len(trades_train) * 100) if trades_train else 0
            test_wr = (test_wins / len(trades_test) * 100) if trades_test else 0
            decay = train_wr - test_wr
            ci_low, ci_high = self.calculate_ci(test_wins, len(trades_test))
            
            results[ticker] = {
                'train_win_pct': round(train_wr, 1),
                'test_win_pct': round(test_wr, 1),
                'train_n': len(trades_train),
                'test_n': len(trades_test),
                'decay_pct': round(decay, 1),
                'ci_95': f"[{ci_low:.1f}%, {ci_high:.1f}%]",
                'avg_return': round(np.mean([t['pnl_pct'] for t in trades_test]), 2) if trades_test else 0
            }
        return results
    
    def test_rsi_divergence(self, tickers: List[str]) -> Dict:
        """H2: RSI Bullish Divergence - price lower low, RSI higher low"""
        results = {}
        for ticker in tickers:
            df = self.load_data(ticker)
            trades_train, trades_test = [], []
            
            for i in range(15, len(df) - 5):
                row = df.iloc[i]
                prev_low_idx = i - 10
                
                # Check if we have enough data
                if prev_low_idx < 0:
                    continue
                    
                price_now = row['close']
                price_prev = df.iloc[prev_low_idx]['close']
                rsi_now = row['rsi']
                rsi_prev = df.iloc[prev_low_idx]['rsi']
                
                # Bullish divergence: price lower but RSI higher
                price_lower = price_now < price_prev * 0.97  # 3% lower
                rsi_higher = rsi_now > rsi_prev * 1.03  # RSI improving
                oversold = rsi_now < 45
                
                if price_lower and rsi_higher and oversold:
                    future = df.iloc[i + 5]
                    pnl = (future['close'] - row['close']) / row['close'] * 100
                    trade = {'pnl_pct': pnl, 'date': row['date']}
                    if row['train']:
                        trades_train.append(trade)
                    else:
                        trades_test.append(trade)
            
            train_wins = sum(1 for t in trades_train if t['pnl_pct'] > 0)
            test_wins = sum(1 for t in trades_test if t['pnl_pct'] > 0)
            train_wr = (train_wins / len(trades_train) * 100) if trades_train else 0
            test_wr = (test_wins / len(trades_test) * 100) if trades_test else 0
            decay = train_wr - test_wr
            ci_low, ci_high = self.calculate_ci(test_wins, len(trades_test))
            
            results[ticker] = {
                'train_win_pct': round(train_wr, 1),
                'test_win_pct': round(test_wr, 1),
                'train_n': len(trades_train),
                'test_n': len(trades_test),
                'decay_pct': round(decay, 1),
                'ci_95': f"[{ci_low:.1f}%, {ci_high:.1f}%]",
                'avg_return': round(np.mean([t['pnl_pct'] for t in trades_test]), 2) if trades_test else 0
            }
        return results
    
    def test_bb_squeeze(self, tickers: List[str]) -> Dict:
        """H3: BB Width < 5% (squeeze) + RSI < 40 = Volatility Expansion"""
        results = {}
        for ticker in tickers:
            df = self.load_data(ticker)
            
            # Calculate BB width
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle'] * 100
            
            trades_train, trades_test = [], []
            
            for i in range(20, len(df) - 5):
                row = df.iloc[i]
                future = df.iloc[i + 5]
                
                squeeze = row['bb_width'] < 5.0
                oversold = row['rsi'] < 40
                
                if squeeze and oversold:
                    pnl = (future['close'] - row['close']) / row['close'] * 100
                    trade = {'pnl_pct': pnl, 'date': row['date']}
                    if row['train']:
                        trades_train.append(trade)
                    else:
                        trades_test.append(trade)
            
            train_wins = sum(1 for t in trades_train if t['pnl_pct'] > 0)
            test_wins = sum(1 for t in trades_test if t['pnl_pct'] > 0)
            train_wr = (train_wins / len(trades_train) * 100) if trades_train else 0
            test_wr = (test_wins / len(trades_test) * 100) if trades_test else 0
            decay = train_wr - test_wr
            ci_low, ci_high = self.calculate_ci(test_wins, len(trades_test))
            
            results[ticker] = {
                'train_win_pct': round(train_wr, 1),
                'test_win_pct': round(test_wr, 1),
                'train_n': len(trades_train),
                'test_n': len(trades_test),
                'decay_pct': round(decay, 1),
                'ci_95': f"[{ci_low:.1f}%, {ci_high:.1f}%]",
                'avg_return': round(np.mean([t['pnl_pct'] for t in trades_test]), 2) if trades_test else 0
            }
        return results
    
    def test_momentum_trend(self, tickers: List[str]) -> Dict:
        """H4: Price > 50d SMA + ADX > 25 = Trend Following"""
        results = {}
        for ticker in tickers:
            df = self.load_data(ticker)
            trades_train, trades_test = [], []
            
            for i in range(50, len(df) - 5):
                row = df.iloc[i]
                future = df.iloc[i + 5]
                
                trend_ok = row['close'] > row['sma_50']
                strength_ok = row.get('adx', 0) > 25
                
                if trend_ok and strength_ok:
                    pnl = (future['close'] - row['close']) / row['close'] * 100
                    trade = {'pnl_pct': pnl, 'date': row['date']}
                    if row['train']:
                        trades_train.append(trade)
                    else:
                        trades_test.append(trade)
            
            train_wins = sum(1 for t in trades_train if t['pnl_pct'] > 0)
            test_wins = sum(1 for t in trades_test if t['pnl_pct'] > 0)
            train_wr = (train_wins / len(trades_train) * 100) if trades_train else 0
            test_wr = (test_wins / len(trades_test) * 100) if trades_test else 0
            decay = train_wr - test_wr
            ci_low, ci_high = self.calculate_ci(test_wins, len(trades_test))
            
            results[ticker] = {
                'train_win_pct': round(train_wr, 1),
                'test_win_pct': round(test_wr, 1),
                'train_n': len(trades_train),
                'test_n': len(trades_test),
                'decay_pct': round(decay, 1),
                'ci_95': f"[{ci_low:.1f}%, {ci_high:.1f}%]",
                'avg_return': round(np.mean([t['pnl_pct'] for t in trades_test]), 2) if trades_test else 0
            }
        return results


def main():
    engine = ResearchEngine()
    all_results = {}
    
    tickers = ['AAPL', 'MSFT', 'META', 'TSLA', 'NVDA', 'AMD', 'COIN', 'MSTR', 'QQQ', 'SPY']
    
    print("="*70)
    print("CONTINUOUS STRATEGY RESEARCH - EXTENDED BATCH")
    print("Train: 2021-2022 | Test: 2023-2024 | n≥30 target")
    print("="*70)
    
    # H1: Stoch + BB
    print("\n[H1] Stochastic <20 + Below BB Lower")
    all_results['H1_Stoch_BB'] = engine.test_stoch_bb_combo(tickers)
    
    # H2: RSI Divergence
    print("[H2] RSI Bullish Divergence")
    all_results['H2_RSI_Divergence'] = engine.test_rsi_divergence(tickers)
    
    # H3: BB Squeeze
    print("[H3] BB Squeeze + RSI <40")
    all_results['H3_BB_Squeeze'] = engine.test_bb_squeeze(tickers)
    
    # H4: Momentum Trend
    print("[H4] Trend Following (Price >50d SMA + ADX>25)")
    all_results['H4_Momentum_Trend'] = engine.test_momentum_trend(tickers)
    
    # Save results
    output_path = '/home/ubuntu/.openclaw/workspace/trade-algo-researcher/results/continuous_batch_extended_2026-02-23.json'
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"RESULTS SAVED: {output_path}")
    print("="*70)
    
    # Print summary
    print("\n" + "="*70)
    print("SUMMARY BY HYPOTHESIS")
    print("="*70)
    
    for hyp_name, results in all_results.items():
        golden = sum(1 for r in results.values() if r['test_win_pct'] >= 70 and r['test_n'] >= 30)
        validated = sum(1 for r in results.values() if r['test_win_pct'] >= 55 and r['test_win_pct'] < 70 and r['test_n'] >= 10)
        total = len(results)
        print(f"\n{hyp_name}:")
        print(f"  Golden (≥70%, n≥30): {golden}/{total}")
        print(f"  Validated (55-70%): {validated}/{total}")
        
        # Best performer
        best = max(results.items(), key=lambda x: x[1]['test_win_pct'] if x[1]['test_n'] >= 10 else 0)
        if best[1]['test_n'] >= 10:
            print(f"  Best: {best[0]} {best[1]['test_win_pct']}% (n={best[1]['test_n']})")
    
    return all_results


if __name__ == "__main__":
    results = main()
