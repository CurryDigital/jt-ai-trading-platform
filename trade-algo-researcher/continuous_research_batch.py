#!/usr/bin/env python3
"""
Continuous Strategy Research - New Hypotheses Batch
Uses local CSV indicator data
Train: 2021-2022 | Test: 2023-2024 | n≥30 | 95% CI
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
        """Load indicator data from CSV"""
        df = pd.read_csv(f"{self.data_path}{ticker}_indicators.csv")
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        df['train'] = df['date'] <= self.train_end
        return df
    
    def calculate_ci(self, wins: int, total: int) -> Tuple[float, float]:
        """95% Wilson score confidence interval"""
        if total == 0:
            return 0, 0
        p = wins / total
        z = 1.96
        denominator = 1 + z**2 / total
        center = (p + z**2 / (2 * total)) / denominator
        margin = z * math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denominator
        return max(0, center - margin) * 100, min(1, center + margin) * 100
    
    def test_rsi_macd_volume(self, tickers: List[str]) -> Dict:
        """H1: RSI < 40 + MACD Improving + Volume > 1.2x (Triple Confirmation)"""
        results = {}
        
        for ticker in tickers:
            df = self.load_data(ticker)
            trades_train, trades_test = [], []
            
            for i in range(1, len(df) - 5):
                row = df.iloc[i]
                prev = df.iloc[i-1]
                future = df.iloc[i + 5]
                
                # Triple confirmation
                rsi_ok = row['rsi'] < 40
                macd_improving = row['macd'] > prev['macd'] and row['macd'] < 0
                volume_ok = row.get('relative_vol_10d', 1.5) > 1.2
                
                if rsi_ok and macd_improving and volume_ok:
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
    
    def test_bearish_rsi_overbought(self, tickers: List[str]) -> Dict:
        """H2: Bearish - RSI > 70 + Price < SMA 200 (Short in downtrends)"""
        results = {}
        
        for ticker in tickers:
            df = self.load_data(ticker)
            trades_train, trades_test = [], []
            
            for i in range(200, len(df) - 5):
                row = df.iloc[i]
                future = df.iloc[i + 5]
                
                # Bearish signal: Overbought in downtrend
                rsi_overbought = row['rsi'] > 70
                below_sma200 = row['close'] < row['sma_200']
                
                if rsi_overbought and below_sma200:
                    # Short position P&L (inverse)
                    pnl = (row['close'] - future['close']) / row['close'] * 100
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
                'avg_return': round(np.mean([t['pnl_pct'] for t in trades_test]), 2) if trades_test else 0,
                'strategy_type': 'BEARISH/SHORT'
            }
        
        return results
    
    def test_atr_volatility_expansion(self, tickers: List[str]) -> Dict:
        """H3: ATR Compression (5d < 20d ATR) + Breakout = Volatility Expansion"""
        results = {}
        
        for ticker in tickers:
            df = self.load_data(ticker)
            
            # Calculate ATR metrics
            df['atr_5'] = df['atr'].rolling(5).mean()
            df['atr_20'] = df['atr'].rolling(20).mean()
            df['atr_compression'] = df['atr_5'] < df['atr_20'] * 0.85  # 15% compression
            df['breakout'] = df['close'] > df['high'].rolling(10).max().shift(1)
            
            trades_train, trades_test = [], []
            
            for i in range(25, len(df) - 5):
                row = df.iloc[i]
                future = df.iloc[i + 5]
                
                # Volatility expansion setup
                if row['atr_compression'] and row['breakout']:
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
    
    # Available tickers with full indicator data
    tickers = ['AAPL', 'MSFT', 'META', 'TSLA', 'NVDA', 'AMD', 'COIN', 'MSTR', 'QQQ', 'SPY']
    
    print("="*60)
    print("CONTINUOUS STRATEGY RESEARCH - NEW HYPOTHESES")
    print("Train: 2021-2022 | Test: 2023-2024")
    print("="*60)
    
    # H1: Triple Confirmation
    print("\n[H1] RSI + MACD + Volume Triple Confirmation")
    all_results['H1_Triple_Confirmation'] = engine.test_rsi_macd_volume(tickers)
    
    # H2: Bearish Overbought
    print("\n[H2] Bearish RSI >70 + Downtrend Filter")
    all_results['H2_Bearish_Overbought'] = engine.test_bearish_rsi_overbought(tickers)
    
    # H3: ATR Volatility Expansion
    print("\n[H3] ATR Compression + Breakout")
    all_results['H3_ATR_Volatility_Expansion'] = engine.test_atr_volatility_expansion(tickers)
    
    # Save results
    output_path = '/home/ubuntu/.openclaw/workspace/trade-algo-researcher/results/continuous_batch_2026-02-23_2055.json'
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"RESULTS SAVED: {output_path}")
    print("="*60)
    
    return all_results


if __name__ == "__main__":
    results = main()
