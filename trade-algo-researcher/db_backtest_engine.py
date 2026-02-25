#!/usr/bin/env python3
"""
Database-driven backtesting engine for Trade Algo Researcher
Uses silver (raw), gold (signals), and consumption (JT output) schemas
"""

import boto3
import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradeAlgoDB:
    """PostgreSQL connection manager with IAM auth"""
    
    def __init__(self):
        self.host = 'openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com'
        self.port = 5432
        self.database = 'aitrading'
        self.user = 'openclaw_user'
        self.region = 'ap-southeast-1'
        self.connection = None
        
    def get_auth_token(self) -> str:
        """Generate IAM auth token"""
        session = boto3.Session(region_name=self.region)
        rds = session.client('rds')
        token = rds.generate_db_auth_token(
            DBHostname=self.host,
            Port=self.port,
            DBUsername=self.user,
            Region=self.region
        )
        return token
    
    def connect(self):
        """Establish database connection"""
        try:
            token = self.get_auth_token()
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=token,
                sslmode='require'
            )
            logger.info("Connected to aitrading database")
            return self.connection
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise
    
    def query(self, sql: str, params: tuple = None) -> pd.DataFrame:
        """Execute query and return DataFrame"""
        if not self.connection:
            self.connect()
        
        try:
            df = pd.read_sql(sql, self.connection, params=params)
            return df
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise
    
    def execute(self, sql: str, params: tuple = None):
        """Execute non-query SQL"""
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql, params)
            self.connection.commit()
            cursor.close()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Execute failed: {e}")
            raise
    
    def close(self):
        """Close connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")


class DataRetrieval:
    """Retrieve data from silver, gold, and consumption schemas"""
    
    def __init__(self, db: TradeAlgoDB):
        self.db = db
    
    # ==================== SILVER SCHEMA (Raw Data) ====================
    
    def get_ohlcv(self, tickers: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """
        Retrieve OHLCV price data from silver.historical_stock_data
        
        Args:
            tickers: List of ticker symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            DataFrame with columns: date, ticker, open, high, low, close, volume, returns
        """
        ticker_list = "','".join(tickers)
        sql = f"""
        SELECT date, ticker, open, high, low, close, volume, returns
        FROM silver.historical_stock_data
        WHERE ticker IN ('{ticker_list}')
        AND date BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY ticker, date
        """
        return self.db.query(sql)
    
    def get_historical_news(self, tickers: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """Retrieve news sentiment from silver.historical_news"""
        ticker_list = "','".join(tickers)
        sql = f"""
        SELECT * FROM silver.historical_news
        WHERE ticker IN ('{ticker_list}')
        AND date BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY date DESC
        """
        return self.db.query(sql)
    
    # ==================== GOLD SCHEMA (Signals) ====================
    
    def get_stock_metrics(self, tickers: List[str], date: Optional[str] = None) -> pd.DataFrame:
        """
        Retrieve technical indicators from gold.stock_metrics
        
        Key columns: rsi_14, macd_hist, sma_50, sma_200, relative_vol_10d, beta, sharpe_ratio
        """
        ticker_list = "','".join(tickers)
        
        if date:
            sql = f"""
            SELECT date, ticker, sector, close, volume, vwap,
                   relative_vol_10d, rsi_14, macd_hist, 
                   sma_50, sma_200, dist_from_52w_high, atr_14, beta, sharpe_ratio
            FROM gold.stock_metrics
            WHERE ticker IN ('{ticker_list}')
            AND date = '{date}'
            ORDER BY rsi_14 ASC
            """
        else:
            # Get latest for each ticker
            sql = f"""
            SELECT DISTINCT ON (ticker)
                   date, ticker, sector, close, volume, vwap,
                   relative_vol_10d, rsi_14, macd_hist,
                   sma_50, sma_200, dist_from_52w_high, atr_14, beta, sharpe_ratio
            FROM gold.stock_metrics
            WHERE ticker IN ('{ticker_list}')
            ORDER BY ticker, date DESC
            """
        return self.db.query(sql)
    
    def get_rsi_signals(self, rsi_threshold: float = 30, 
                        volume_threshold: float = 1.3,
                        date: Optional[str] = None) -> pd.DataFrame:
        """
        Get RSI mean reversion signals from gold.stock_metrics
        
        Args:
            rsi_threshold: RSI below this = oversold signal
            volume_threshold: Volume relative to 10-day avg
            date: Specific date or None for latest
        """
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        sql = f"""
        SELECT date, ticker, sector, close, volume, relative_vol_10d, rsi_14, atr_14
        FROM gold.stock_metrics
        WHERE date = '{date}'
        AND rsi_14 < {rsi_threshold}
        AND relative_vol_10d > {volume_threshold}
        AND close > 5  -- Avoid penny stocks
        ORDER BY rsi_14 ASC
        LIMIT 50
        """
        return self.db.query(sql)
    
    def get_fx_metrics(self, pairs: List[str] = None, 
                       start_date: str = None, 
                       end_date: str = None) -> pd.DataFrame:
        """
        Retrieve FX data from gold.fx_metrics
        Key for AH Premium arbitrage (HKD/CNY proxy)
        """
        if pairs:
            pair_list = "','".join(pairs)
            pair_filter = f"AND ticker IN ('{pair_list}')"
        else:
            pair_filter = ""
        
        date_filter = ""
        if start_date and end_date:
            date_filter = f"AND date BETWEEN '{start_date}' AND '{end_date}'"
        elif start_date:
            date_filter = f"AND date >= '{start_date}'"
        
        sql = f"""
        SELECT date, ticker, close_price, rsi_14, interest_rate_diff,
               market_regime, prophet_forecast, candlestick_pattern
        FROM gold.fx_metrics
        WHERE 1=1 {pair_filter} {date_filter}
        ORDER BY date DESC
        LIMIT 100
        """
        return self.db.query(sql)
    
    def get_commodity_metrics(self, tickers: List[str] = None) -> pd.DataFrame:
        """
        Retrieve commodity data from gold.commodity_metrics
        Key for Gold/Silver ratio strategy
        """
        if tickers:
            ticker_list = "','".join(tickers)
            ticker_filter = f"AND ticker IN ('{ticker_list}')"
        else:
            ticker_filter = "AND ticker IN ('GC=F', 'SI=F')"  # Default to gold/silver
        
        sql = f"""
        SELECT date, ticker, close_price, rsi_14, prophet_forecast, candlestick_pattern
        FROM gold.commodity_metrics
        WHERE 1=1 {ticker_filter}
        ORDER BY date DESC
        LIMIT 10
        """
        return self.db.query(sql)
    
    def get_earnings_data(self, tickers: List[str] = None,
                          start_date: str = None,
                          min_surprise: float = None) -> pd.DataFrame:
        """
        Retrieve earnings data from gold.earnings_data
        Key for PEAD strategy
        """
        ticker_filter = ""
        if tickers:
            ticker_list = "','".join(tickers)
            ticker_filter = f"AND ticker IN ('{ticker_list}')"
        
        date_filter = ""
        if start_date:
            date_filter = f"AND earnings_date >= '{start_date}'"
        
        surprise_filter = ""
        if min_surprise:
            surprise_filter = f"AND surprise_pct >= {min_surprise}"
        
        sql = f"""
        SELECT * FROM gold.earnings_data
        WHERE 1=1 {ticker_filter} {date_filter} {surprise_filter}
        ORDER BY earnings_date DESC
        LIMIT 100
        """
        return self.db.query(sql)
    
    def get_sue_scores(self, date: str = None, min_sue: float = 2.0) -> pd.DataFrame:
        """
        Get Standardized Unexpected Earnings from gold.sue_scores
        """
        date_filter = f"AND date = '{date}'" if date else ""
        
        sql = f"""
        SELECT * FROM gold.sue_scores
        WHERE sue_score >= {min_sue} {date_filter}
        ORDER BY sue_score DESC
        LIMIT 50
        """
        return self.db.query(sql)
    
    def get_market_regimes(self, lookback_days: int = 30) -> pd.DataFrame:
        """
        Retrieve HMM market regime classifications
        """
        sql = f"""
        SELECT * FROM gold.market_regimes
        WHERE date >= CURRENT_DATE - INTERVAL '{lookback_days} days'
        ORDER BY date DESC
        """
        return self.db.query(sql)
    
    # ==================== CONSUMPTION SCHEMA (JT Output) ====================
    
    def get_jt_stock_signals(self, market: str = None, 
                            min_confidence: float = 70,
                            min_score: float = 50) -> pd.DataFrame:
        """
        Retrieve JT AI Trading platform stock recommendations
        from consumption.stock
        """
        market_filter = f"AND market = '{market}'" if market else ""
        
        sql = f"""
        SELECT timestamp, ticker, market, final_score, 
               trad_confidence, swarm_confidence, win_rate,
               est_1d, est_7d, est_1m,
               close_price, daily_change, strategy_tags
        FROM consumption.stock
        WHERE timestamp >= CURRENT_DATE
        AND trad_confidence >= {min_confidence}
        AND final_score >= {min_score}
        {market_filter}
        ORDER BY final_score DESC
        LIMIT 50
        """
        return self.db.query(sql)
    
    def get_jt_trades(self, start_date: str = None) -> pd.DataFrame:
        """Retrieve executed trades from consumption.trades"""
        date_filter = f"AND timestamp >= '{start_date}'" if start_date else ""
        
        sql = f"""
        SELECT * FROM consumption.trades
        WHERE 1=1 {date_filter}
        ORDER BY timestamp DESC
        LIMIT 100
        """
        return self.db.query(sql)


class BacktestEngine:
    """Execute backtests using database data"""
    
    def __init__(self, db: TradeAlgoDB):
        self.db = db
        self.data = DataRetrieval(db)
    
    def run_rsi_backtest(self, 
                         tickers: List[str],
                         start_date: str,
                         end_date: str,
                         rsi_entry: float = 30,
                         rsi_exit: float = 50,
                         volume_threshold: float = 1.3,
                         max_hold_days: int = 5) -> Dict:
        """
        Backtest RSI Mean Reversion strategy using gold.stock_metrics
        """
        logger.info(f"Running RSI backtest for {len(tickers)} tickers")
        
        # Get all stock metrics data
        metrics = self.data.get_stock_metrics(tickers, start_date)
        
        trades = []
        for ticker in tickers:
            ticker_data = metrics[metrics['ticker'] == ticker].sort_values('date')
            
            position = None
            entry_date = None
            entry_price = None
            
            for idx, row in ticker_data.iterrows():
                if position is None:
                    # Look for entry
                    if (row['rsi_14'] < rsi_entry and 
                        row['relative_vol_10d'] > volume_threshold):
                        position = 'LONG'
                        entry_date = row['date']
                        entry_price = row['close']
                else:
                    # Look for exit
                    hold_days = (row['date'] - entry_date).days
                    pnl = (row['close'] - entry_price) / entry_price
                    
                    exit_signal = (row['rsi_14'] > rsi_exit or 
                                   hold_days >= max_hold_days or
                                   pnl < -0.03)  # Stop loss
                    
                    if exit_signal:
                        trades.append({
                            'ticker': ticker,
                            'entry_date': entry_date,
                            'exit_date': row['date'],
                            'entry_price': entry_price,
                            'exit_price': row['close'],
                            'pnl_pct': pnl * 100,
                            'hold_days': hold_days,
                            'exit_reason': 'RSI' if row['rsi_14'] > rsi_exit else 
                                          'TIME' if hold_days >= max_hold_days else 'STOP'
                        })
                        position = None
        
        trades_df = pd.DataFrame(trades)
        
        if len(trades_df) == 0:
            return {'error': 'No trades generated'}
        
        results = {
            'total_trades': len(trades_df),
            'win_rate': (trades_df['pnl_pct'] > 0).mean() * 100,
            'avg_return': trades_df['pnl_pct'].mean(),
            'total_return': trades_df['pnl_pct'].sum(),
            'sharpe': trades_df['pnl_pct'].mean() / trades_df['pnl_pct'].std() if trades_df['pnl_pct'].std() > 0 else 0,
            'max_drawdown': trades_df['pnl_pct'].min(),
            'avg_hold_days': trades_df['hold_days'].mean(),
            'trades': trades_df.to_dict('records')
        }
        
        return results
    
    def run_momentum_backtest(self,
                              tickers: List[str],
                              start_date: str,
                              end_date: str,
                              lookback_days: int = 20,
                              hold_days: int = 20) -> Dict:
        """
        Backtest momentum strategy using gold.stock_metrics
        """
        logger.info(f"Running Momentum backtest")
        
        # Get price data from silver
        prices = self.data.get_ohlcv(tickers, start_date, end_date)
        
        trades = []
        
        for ticker in tickers:
            ticker_data = prices[prices['ticker'] == ticker].sort_values('date')
            
            if len(ticker_data) < lookback_days + hold_days:
                continue
            
            for i in range(lookback_days, len(ticker_data) - hold_days):
                # Calculate past return
                past_return = (ticker_data.iloc[i]['close'] / 
                              ticker_data.iloc[i - lookback_days]['close'] - 1)
                
                if past_return > 0.05:  # 5% momentum threshold
                    # Future return
                    future_return = (ticker_data.iloc[i + hold_days]['close'] / 
                                    ticker_data.iloc[i]['close'] - 1)
                    
                    trades.append({
                        'ticker': ticker,
                        'entry_date': ticker_data.iloc[i]['date'],
                        'exit_date': ticker_data.iloc[i + hold_days]['date'],
                        'past_return': past_return * 100,
                        'future_return': future_return * 100
                    })
        
        trades_df = pd.DataFrame(trades)
        
        if len(trades_df) == 0:
            return {'error': 'No trades generated'}
        
        results = {
            'total_trades': len(trades_df),
            'win_rate': (trades_df['future_return'] > 0).mean() * 100,
            'avg_return': trades_df['future_return'].mean(),
            'momentum_persistence': np.corrcoef(
                trades_df['past_return'], 
                trades_df['future_return']
            )[0,1] if len(trades_df) > 1 else 0
        }
        
        return results
    
    def run_pead_backtest(self,
                          tickers: List[str],
                          start_date: str,
                          end_date: str,
                          min_surprise: float = 0.05,
                          hold_days: int = 5) -> Dict:
        """
        Backtest PEAD strategy using gold.earnings_data
        """
        logger.info(f"Running PEAD backtest")
        
        # Get earnings data
        earnings = self.data.get_earnings_data(
            tickers, start_date, min_surprise
        )
        
        # Get price data
        prices = self.data.get_ohlcv(tickers, start_date, end_date)
        
        trades = []
        
        for _, earning in earnings.iterrows():
            ticker = earning['ticker']
            earn_date = earning['earnings_date']
            surprise = earning['surprise_pct']
            
            # Find entry price (next day after earnings)
            ticker_prices = prices[prices['ticker'] == ticker]
            post_earn = ticker_prices[ticker_prices['date'] > earn_date].head(hold_days + 1)
            
            if len(post_earn) < hold_days:
                continue
            
            entry_price = post_earn.iloc[0]['open']
            exit_price = post_earn.iloc[min(hold_days, len(post_earn) - 1)]['close']
            
            pnl = (exit_price - entry_price) / entry_price
            
            trades.append({
                'ticker': ticker,
                'earnings_date': earn_date,
                'entry_date': post_earn.iloc[0]['date'],
                'exit_date': post_earn.iloc[min(hold_days, len(post_earn) - 1)]['date'],
                'surprise_pct': surprise * 100,
                'pnl_pct': pnl * 100
            })
        
        trades_df = pd.DataFrame(trades)
        
        if len(trades_df) == 0:
            return {'error': 'No trades generated'}
        
        results = {
            'total_trades': len(trades_df),
            'win_rate': (trades_df['pnl_pct'] > 0).mean() * 100,
            'avg_return': trades_df['pnl_pct'].mean(),
            'correlation_surprise_return': np.corrcoef(
                trades_df['surprise_pct'], 
                trades_df['pnl_pct']
            )[0,1] if len(trades_df) > 1 else 0
        }
        
        return results


class BacktestStorage:
    """Store backtest results in openclaw_researcher schema"""
    
    def __init__(self, db: TradeAlgoDB):
        self.db = db
    
    def save_backtest_result(self,
                            hypothesis_name: str,
                            start_date: str,
                            end_date: str,
                            results: Dict,
                            parameters: Dict) -> int:
        """
        Save backtest summary to openclaw_researcher.backtest_results
        Returns backtest_id
        """
        sql = """
        INSERT INTO openclaw_researcher.backtest_results 
        (hypothesis_name, start_date, end_date, total_return_pct,
         sharpe_ratio, max_drawdown_pct, win_rate_pct, total_trades,
         status, parameters, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        params = (
            hypothesis_name,
            start_date,
            end_date,
            results.get('total_return'),
            results.get('sharpe'),
            results.get('max_drawdown'),
            results.get('win_rate'),
            results.get('total_trades'),
            'completed',
            json.dumps(parameters),
            f"Backtest completed at {datetime.now()}"
        )
        
        cursor = self.db.connection.cursor()
        cursor.execute(sql, params)
        backtest_id = cursor.fetchone()[0]
        self.db.connection.commit()
        cursor.close()
        
        logger.info(f"Backtest saved with ID: {backtest_id}")
        return backtest_id
    
    def save_trades(self, backtest_id: int, trades: List[Dict]):
        """
        Save individual trades to openclaw_researcher.backtest_trades
        """
        sql = """
        INSERT INTO openclaw_researcher.backtest_trades
        (backtest_id, ticker, entry_date, exit_date, entry_price, exit_price,
         direction, pnl_pct, exit_reason, holding_days)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor = self.db.connection.cursor()
        
        for trade in trades:
            params = (
                backtest_id,
                trade.get('ticker'),
                trade.get('entry_date'),
                trade.get('exit_date'),
                trade.get('entry_price'),
                trade.get('exit_price'),
                'LONG',
                trade.get('pnl_pct'),
                trade.get('exit_reason', 'SIGNAL'),
                trade.get('hold_days', 0)
            )
            cursor.execute(sql, params)
        
        self.db.connection.commit()
        cursor.close()
        logger.info(f"Saved {len(trades)} trades")
    
    def update_hypothesis_status(self, hypothesis_name: str, 
                                 sharpe: float, status: str = 'validated'):
        """
        Update hypothesis registry after backtest
        """
        sql = """
        UPDATE openclaw_researcher.hypothesis_registry
        SET backtest_count = backtest_count + 1,
            best_sharpe = GREATEST(best_sharpe, %s),
            last_backtest_date = CURRENT_DATE,
            current_status = %s
        WHERE hypothesis_name = %s
        """
        
        self.db.execute(sql, (sharpe, status, hypothesis_name))
        logger.info(f"Updated {hypothesis_name} status to {status}")


# ==================== UTILITY FUNCTIONS ====================

def get_all_tickers_from_gold(market: str = None, min_volume: float = 1000000) -> List[str]:
    """
    Get all available tickers from gold.stock_metrics
    """
    db = TradeAlgoDB()
    db.connect()
    
    market_filter = f"AND sector LIKE '%{market}%'" if market else ""
    
    sql = f"""
    SELECT DISTINCT ticker FROM gold.stock_metrics
    WHERE volume >= {min_volume}
    {market_filter}
    ORDER BY ticker
    """
    
    df = db.query(sql)
    db.close()
    
    return df['ticker'].tolist()


def get_correlation_matrix(tickers: List[str], 
                           lookback_days: int = 90) -> pd.DataFrame:
    """
    Calculate correlation matrix for a universe
    """
    db = TradeAlgoDB()
    db.connect()
    data = DataRetrieval(db)
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
    
    prices = data.get_ohlcv(tickers, start_date, end_date)
    
    # Pivot to wide format
    price_pivot = prices.pivot(index='date', columns='ticker', values='close')
    
    # Calculate returns
    returns = price_pivot.pct_change().dropna()
    
    # Correlation matrix
    corr_matrix = returns.corr()
    
    db.close()
    return corr_matrix


if __name__ == "__main__":
    # Example usage
    db = TradeAlgoDB()
    db.connect()
    
    data = DataRetrieval(db)
    
    # Get RSI signals
    print("=== RSI Oversold Signals ===")
    rsi_signals = data.get_rsi_signals(rsi_threshold=30)
    print(rsi_signals.head(10))
    
    # Get commodity data
    print("\n=== Gold/Silver Data ===")
    commodities = data.get_commodity_metrics(['GC=F', 'SI=F'])
    print(commodities)
    
    # Get FX data for AH Premium
    print("\n=== FX Data ===")
    fx = data.get_fx_metrics(['USDJPY=X', 'USDCNH=X'])
    print(fx)
    
    db.close()
