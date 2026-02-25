#!/usr/bin/env python3
"""
Continuous Strategy Research - Batch Testing Script
Uses silver.historical_stock_data with on-the-fly indicator calculation
Train: 2021-2022 | Test: 2023-2024 | n≥30 | 95% CI
"""

import boto3
import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import json
import logging
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradeAlgoDB:
    def __init__(self):
        self.host = 'openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com'
        self.port = 5432
        self.database = 'aitrading'
        self.user = 'openclaw_user'
        self.region = 'ap-southeast-1'
        self.connection = None
        
    def get_auth_token(self) -> str:
        session = boto3.Session(region_name=self.region)
        rds = session.client('rds')
        token = rds.generate_db_auth_token(
            DBHostname=self.host, Port=self.port, DBUsername=self.user, Region=self.region
        )
        return token
    
    def connect(self):
        try:
            token = self.get_auth_token()
            self.connection = psycopg2.connect(
                host=self.host, port=self.port, database=self.database,
                user=self.user, password=token, sslmode='require'
            )
            logger.info("Connected to aitrading database")
            return self.connection
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise
    
    def query(self, sql: str, params: tuple = None) -> pd.DataFrame:
        if not self.connection:
            self.connect()
        try:
            df = pd.read_sql(sql, self.connection, params=params)
            return df
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise
    
    def close(self):
        if self.connection:
            self.connection.close()


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate MACD line, signal line, and histogram"""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
    """Calculate Simple Moving Average"""
    return prices.rolling(window=period).mean()


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Average True Range"""
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
    """Calculate Stochastic Oscillator %K and %D"""
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    d = k.rolling(window=d_period).mean()
    return k, d


class ResearchEngine:
    def __init__(self):
        self.db = TradeAlgoDB()
        self.db.connect()
        self.train_start = '2021-01-01'
        self.train_end = '2022-12-31'
        self.test_start = '2023-01-01'
        self.test_end = '2024-12-31'
        
    def get_price_data(self, tickers: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """Get price data from silver.historical_stock_data"""
        ticker_list = "','".join(tickers)
        sql = f"""
        SELECT date, ticker, open, high, low, close, volume
        FROM silver.historical_stock_data
        WHERE ticker IN ('{ticker_list}')
        AND date BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY ticker, date
        """
        df = self.db.query(sql)
        
        # Calculate indicators
        if not df.empty:
            df = df.sort_values(['ticker', 'date'])
            
            # Calculate indicators for each ticker
            result_dfs = []
            for ticker in df['ticker'].unique():
                tdf = df[df['ticker'] == ticker].copy()
                tdf['rsi_14'] = calculate_rsi(tdf['close'])
                tdf['sma_50'] = calculate_sma(tdf['close'], 50)
                tdf['sma_200'] = calculate_sma(tdf['close'], 200)
                macd_line, macd_signal, macd_hist = calculate_macd(tdf['close'])
                tdf['macd_line'] = macd_line
                tdf['macd_signal'] = macd_signal
                tdf['macd_hist'] = macd_hist
                tdf['atr_14'] = calculate_atr(tdf['high'], tdf['low'], tdf['close'])
                stoch_k, stoch_d = calculate_stochastic(tdf['high'], tdf['low'], tdf['close'])
                tdf['stoch_k'] = stoch_k
                tdf['stoch_d'] = stoch_d
                tdf['vol_avg_20'] = tdf['volume'].rolling(20).mean()
                tdf['relative_vol_10d'] = tdf['volume'] / tdf['volume'].rolling(10).mean()
                result_dfs.append(tdf)
            
            df = pd.concat(result_dfs, ignore_index=True)
        
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
    
    def test_sector_mean_reversion(self, tickers: List[str]) -> Dict:
        """H1: Sector-Specific Mean Reversion - RSI < 30"""
        logger.info("Testing H1: Sector Mean Reversion")
        
        df = self.get_price_data(tickers, self.train_start, self.test_end)
        results = {}
        
        for ticker in tickers:
            tdf = df[df['ticker'] == ticker].sort_values('date')
            if len(tdf) < 100:
                continue
            
            tdf['train'] = tdf['date'] <= self.train_end
            trades_train, trades_test = [], []
            
            for i in range(len(tdf) - 5):
                row = tdf.iloc[i]
                future = tdf.iloc[i + 5]
                
                if row['rsi_14'] < 30 and not pd.isna(row['rsi_14']):
                    pnl = (future['close'] - row['close']) / row['close'] * 100
                    trade = {'pnl_pct': pnl}
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
    
    def test_volume_breakout(self, tickers: List[str]) -> Dict:
        """H4: Volume > 2x avg + New 10D High"""
        logger.info("Testing H4: Volume Profile Breakout")
        
        df = self.get_price_data(tickers, self.train_start, self.test_end)
        results = {}
        
        for ticker in tickers:
            tdf = df[df['ticker'] == ticker].sort_values('date')
            if len(tdf) < 100:
                continue
            
            tdf['train'] = tdf['date'] <= self.train_end
            tdf['high_10d'] = tdf['high'].rolling(10).max().shift(1)
            
            trades_train, trades_test = [], []
            
            for i in range(20, len(tdf) - 5):
                row = tdf.iloc[i]
                future = tdf.iloc[i + 5]
                
                if (row['relative_vol_10d'] > 2.0 and 
                    row['close'] > row['high_10d'] and
                    not pd.isna(row['relative_vol_10d'])):
                    
                    pnl = (future['close'] - row['close']) / row['close'] * 100
                    trade = {'pnl_pct': pnl}
                    
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
    
    def test_macd_divergence(self, tickers: List[str]) -> Dict:
        """H3: MACD Histogram Bullish Divergence"""
        logger.info("Testing H3: MACD Histogram Divergence")
        
        df = self.get_price_data(tickers, self.train_start, self.test_end)
        results = {}
        
        for ticker in tickers:
            tdf = df[df['ticker'] == ticker].sort_values('date')
            if len(tdf) < 100:
                continue
            
            tdf['train'] = tdf['date'] <= self.train_end
            trades_train, trades_test = [], []
            
            for i in range(10, len(tdf) - 5):
                row = tdf.iloc[i]
                future = tdf.iloc[i + 5]
                prev_window = tdf.iloc[i-10:i]
                
                if len(prev_window) < 5:
                    continue
                
                prev_low_idx = prev_window['low'].idxmin()
                prev_low_row = tdf.loc[prev_low_idx]
                
                price_lower_low = row['low'] < prev_low_row['low'] * 0.99
                macd_higher_low = row['macd_hist'] > prev_low_row['macd_hist'] * 1.01
                
                if (price_lower_low and macd_higher_low and 
                    row['macd_hist'] < 0 and
                    not pd.isna(row['macd_hist'])):
                    
                    pnl = (future['close'] - row['close']) / row['close'] * 100
                    trade = {'pnl_pct': pnl}
                    
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
    
    def test_stochastic_bb_combo(self, tickers: List[str]) -> Dict:
        """Test Stochastic <20 + Price near SMA50 (proxy for BB lower)"""
        logger.info("Testing Stochastic + Trend Combo")
        
        df = self.get_price_data(tickers, self.train_start, self.test_end)
        results = {}
        
        for ticker in tickers:
            tdf = df[df['ticker'] == ticker].sort_values('date')
            if len(tdf) < 100:
                continue
            
            tdf['train'] = tdf['date'] <= self.train_end
            tdf['dist_from_sma50'] = (tdf['close'] - tdf['sma_50']) / tdf['sma_50']
            
            trades_train, trades_test = [], []
            
            for i in range(len(tdf) - 5):
                row = tdf.iloc[i]
                future = tdf.iloc[i + 5]
                
                # Stoch < 20 AND price below SMA50 (oversold)
                if (row['stoch_k'] < 20 and 
                    row['dist_from_sma50'] < -0.02 and
                    not pd.isna(row['stoch_k'])):
                    
                    pnl = (future['close'] - row['close']) / row['close'] * 100
                    trade = {'pnl_pct': pnl}
                    
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
    
    def enhance_20d_high_breakout(self, tickers: List[str]) -> Dict:
        """Enhance 20D High Breakout + Volume + RSI Filter"""
        logger.info("Enhancing 20D High Breakout")
        
        df = self.get_price_data(tickers, self.train_start, self.test_end)
        results = {}
        
        for ticker in tickers:
            tdf = df[df['ticker'] == ticker].sort_values('date')
            if len(tdf) < 100:
                continue
            
            tdf['train'] = tdf['date'] <= self.train_end
            tdf['high_20d'] = tdf['high'].rolling(20).max().shift(1)
            
            orig_test, enh_test = [], []
            
            for i in range(20, len(tdf) - 5):
                row = tdf.iloc[i]
                future = tdf.iloc[i + 5]
                
                # Original: 20D high breakout
                if row['close'] > row['high_20d'] and not pd.isna(row['high_20d']):
                    pnl = (future['close'] - row['close']) / row['close'] * 100
                    if not row['train']:
                        orig_test.append({'pnl_pct': pnl})
                
                # Enhanced: + Volume > 1.5x + RSI < 60
                if (row['close'] > row['high_20d'] and 
                    row['relative_vol_10d'] > 1.5 and
                    row['rsi_14'] < 60 and
                    not pd.isna(row['high_20d'])):
                    pnl = (future['close'] - row['close']) / row['close'] * 100
                    if not row['train']:
                        enh_test.append({'pnl_pct': pnl})
            
            orig_wins = sum(1 for t in orig_test if t['pnl_pct'] > 0)
            enh_wins = sum(1 for t in enh_test if t['pnl_pct'] > 0)
            orig_wr = (orig_wins / len(orig_test) * 100) if orig_test else 0
            enh_wr = (enh_wins / len(enh_test) * 100) if enh_test else 0
            ci_low, ci_high = self.calculate_ci(enh_wins, len(enh_test))
            
            results[ticker] = {
                'original_win_pct': round(orig_wr, 1),
                'original_n': len(orig_test),
                'enhanced_win_pct': round(enh_wr, 1),
                'enhanced_n': len(enh_test),
                'improvement': round(enh_wr - orig_wr, 1),
                'ci_95': f"[{ci_low:.1f}%, {ci_high:.1f}%]"
            }
        
        return results
    
    def close(self):
        self.db.close()


def main():
    engine = ResearchEngine()
    all_results = {}
    
    # Available stock tickers
    stock_tickers = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'NVDA', 'AMD', 'CRM', 'DIS']
    
    # H1: Sector Mean Reversion
    logger.info("\n" + "="*60)
    logger.info("H1: SECTOR-SPECIFIC MEAN REVERSION")
    logger.info("="*60)
    all_results['H1_Sector_Mean_Reversion'] = engine.test_sector_mean_reversion(stock_tickers)
    
    # H3: MACD Divergence
    logger.info("\n" + "="*60)
    logger.info("H3: MACD HISTOGRAM DIVERGENCE")
    logger.info("="*60)
    all_results['H3_MACD_Divergence'] = engine.test_macd_divergence(stock_tickers)
    
    # H4: Volume Breakout
    logger.info("\n" + "="*60)
    logger.info("H4: VOLUME PROFILE BREAKOUT")
    logger.info("="*60)
    all_results['H4_Volume_Breakout'] = engine.test_volume_breakout(stock_tickers)
    
    # H5: Stochastic + Trend Combo (proxy for Stoch+BB)
    logger.info("\n" + "="*60)
    logger.info("H5: STOCHASTIC + TREND COMBO")
    logger.info("="*60)
    all_results['H5_Stoch_Trend_Combo'] = engine.test_stochastic_bb_combo(stock_tickers)
    
    # Enhancement: 20D High Breakout
    logger.info("\n" + "="*60)
    logger.info("E1: 20D HIGH BREAKOUT ENHANCED")
    logger.info("="*60)
    all_results['E1_20D_High_Enhanced'] = engine.enhance_20d_high_breakout(stock_tickers)
    
    # Save results
    with open('/home/ubuntu/.openclaw/workspace/trade-algo-researcher/results/research_batch_2026-02-23.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    
    engine.close()
    
    logger.info("\n" + "="*60)
    logger.info("RESEARCH COMPLETE")
    logger.info("="*60)
    
    return all_results


if __name__ == "__main__":
    results = main()
    print(json.dumps(results, indent=2))
