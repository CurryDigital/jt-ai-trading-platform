"""
Run strategy backtests on all stocks and store results
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/jt-ai-trading-platform/backend')

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import text
import logging

from app.db.session import engine
from app.core_logic.backtesting.strategy_backtester import StrategyBacktester
from app.core_logic.strategies.strategy_config import get_strategy_template

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_all_backtests():
    """Run all strategies on all active stocks"""
    
    # Get all active stocks
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT ticker, market, asset_class 
            FROM gold.asset_registry 
            WHERE is_active = TRUE 
            AND asset_class IN ('STOCK', 'FX', 'CRYPTO', 'COMMODITY')
        """))
        stocks = result.fetchall()
    
    logger.info(f"Found {len(stocks)} active assets to backtest")
    
    # Get all strategy templates
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, asset_class, name, config_json 
            FROM gold.strategy_templates 
            WHERE is_builtin = TRUE
        """))
        strategies = result.fetchall()
    
    logger.info(f"Found {len(strategies)} strategies")
    
    # Clear old backtests (keep last 30 days)
    with engine.connect() as conn:
        conn.execute(text("""
            DELETE FROM gold.strategy_backtests 
            WHERE calculated_at < NOW() - INTERVAL '30 days'
        """))
        conn.commit()
    
    total_backtests = 0
    
    # Run backtests
    for stock in stocks:
        ticker = stock.ticker
        market = stock.market
        asset_class = stock.asset_class
        
        try:
            # Fetch data
            t = yf.Ticker(ticker)
            df = t.history(period="1y")
            
            if len(df) < 60:
                logger.warning(f"Insufficient data for {ticker}")
                continue
            
            # Find applicable strategies for this asset class
            applicable_strategies = [s for s in strategies if s.asset_class == asset_class]
            
            if not applicable_strategies:
                # Fallback to generic strategies
                applicable_strategies = [s for s in strategies if s.asset_class == 'STOCK']
            
            for strat in applicable_strategies:
                try:
                    # Run backtest
                    backtester = StrategyBacktester(initial_capital=100000)
                    strategy_config = get_strategy_template(strat.id)
                    
                    if not strategy_config:
                        continue
                    
                    # Run appropriate backtest based on strategy type
                    if 'mean_reversion' in strat.id:
                        result = backtester.mean_reversion_strategy(df)
                    elif 'trend' in strat.id:
                        result = backtester.trend_following_strategy(df)
                    elif 'breakout' in strat.id:
                        result = backtester.breakout_strategy(df)
                    else:
                        result = backtester.mean_reversion_strategy(df)
                    
                    if result.num_trades < 5:
                        continue
                    
                    # Get current signal
                    signal_data = backtester.get_current_signal(df)
                    
                    # Calculate composite score
                    sharpe_norm = max(0, min(1, result.sharpe_ratio / 3.0))
                    score = (
                        result.win_rate * 0.4 +
                        sharpe_norm * 0.3 +
                        min(1, result.profit_factor / 3) * 0.2 +
                        signal_data.get('strength', 0) * 0.1
                    )
                    
                    # Insert/Update backtest result
                    with engine.connect() as conn:
                        conn.execute(text("""
                            INSERT INTO gold.strategy_backtests (
                                ticker, market, asset_class, strategy_id,
                                win_rate, sharpe_ratio, profit_factor, total_return,
                                max_drawdown, avg_trade_return, num_trades,
                                winning_trades, losing_trades,
                                current_signal, signal_strength,
                                entry_price, stop_loss, target_price,
                                strategy_score, backtest_period, rationale, calculated_at
                            ) VALUES (
                                :ticker, :market, :asset_class, :strategy_id,
                                :win_rate, :sharpe, :profit_factor, :total_return,
                                :max_dd, :avg_return, :num_trades,
                                :wins, :losses,
                                :signal, :signal_strength,
                                :entry, :stop, :target,
                                :score, :period, :rationale, NOW()
                            )
                            ON CONFLICT (ticker, strategy_id) DO UPDATE SET
                                win_rate = EXCLUDED.win_rate,
                                sharpe_ratio = EXCLUDED.sharpe_ratio,
                                profit_factor = EXCLUDED.profit_factor,
                                total_return = EXCLUDED.total_return,
                                max_drawdown = EXCLUDED.max_drawdown,
                                avg_trade_return = EXCLUDED.avg_trade_return,
                                num_trades = EXCLUDED.num_trades,
                                winning_trades = EXCLUDED.winning_trades,
                                losing_trades = EXCLUDED.losing_trades,
                                current_signal = EXCLUDED.current_signal,
                                signal_strength = EXCLUDED.signal_strength,
                                entry_price = EXCLUDED.entry_price,
                                stop_loss = EXCLUDED.stop_loss,
                                target_price = EXCLUDED.target_price,
                                strategy_score = EXCLUDED.strategy_score,
                                calculated_at = EXCLUDED.calculated_at
                        """), {
                            'ticker': ticker,
                            'market': market,
                            'asset_class': asset_class,
                            'strategy_id': strat.id,
                            'win_rate': float(result.win_rate) if result.win_rate else 0,
                            'sharpe': float(result.sharpe_ratio) if result.sharpe_ratio else 0,
                            'profit_factor': float(result.profit_factor) if result.profit_factor else 0,
                            'total_return': float(result.total_return) if result.total_return else 0,
                            'max_dd': float(result.max_drawdown) if result.max_drawdown else 0,
                            'avg_return': float(result.avg_trade_return) if result.avg_trade_return else 0,
                            'num_trades': int(result.num_trades) if result.num_trades else 0,
                            'wins': int(result.winning_trades) if result.winning_trades else 0,
                            'losses': int(result.losing_trades) if result.losing_trades else 0,
                            'signal': str(signal_data.get('signal', 'HOLD')),
                            'signal_strength': float(signal_data.get('strength', 0)) if signal_data.get('strength') else 0,
                            'entry': float(signal_data.get('entry_price')) if signal_data.get('entry_price') else None,
                            'stop': float(signal_data.get('stop_loss')) if signal_data.get('stop_loss') else None,
                            'target': float(signal_data.get('target')) if signal_data.get('target') else None,
                            'score': float(round(score, 4)),
                            'period': '1y',
                            'rationale': str(signal_data.get('rationale', ''))
                        })
                        conn.commit()
                    
                    total_backtests += 1
                    
                    if total_backtests % 100 == 0:
                        logger.info(f"Completed {total_backtests} backtests...")
                    
                except Exception as e:
                    logger.error(f"Error backtesting {ticker} with {strat.id}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            continue
    
    logger.info(f"✅ Completed {total_backtests} backtests")
    return total_backtests


if __name__ == "__main__":
    logger.info("Starting strategy backtest runner...")
    count = run_all_backtests()
    logger.info(f"Finished! Ran {count} backtests.")
