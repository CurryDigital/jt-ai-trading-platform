"""
Backtesting Engine for Strategy Validation
Runs historical simulations and stores results for comparison
"""

import logging
import datetime
import numpy as np
import pandas as pd
import yfinance as yf
from typing import Dict, List, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, QuantStrategy, get_hkt_now
from app.services.strategy_manager import strategy_manager

logger = logging.getLogger(__name__)


class BacktestEngine:
    """Engine for running strategy backtests on historical data"""
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
    
    def run_backtest(
        self,
        strategy_id: int,
        start_date: str,
        end_date: str,
        initial_capital: float = 10000.0,
        commission_rate: float = 0.001  # 0.1% per trade
    ) -> Dict:
        """
        Run a complete backtest for a strategy
        
        Returns backtest results with metrics
        """
        strategy = self.db.query(QuantStrategy).filter(
            QuantStrategy.id == strategy_id
        ).first()
        
        if not strategy:
            return {"error": f"Strategy {strategy_id} not found"}
        
        # Get historical data
        ticker = strategy.target_ticker
        template_id = strategy.params.get("template_id", "MR_FX") if strategy.params else "MR_FX"
        
        try:
            # Download historical data
            data = self._fetch_historical_data(ticker, start_date, end_date)
            if data is None or len(data) < 10:
                return {"error": f"Insufficient historical data for {ticker} (got {len(data) if data is not None else 0} rows, need 10+)"}
            
            # Run simulation based on template type
            if "MR" in template_id:
                results = self._run_mean_reversion_backtest(
                    data, initial_capital, commission_rate
                )
            elif "TREND" in template_id or "MOMENTUM" in template_id:
                results = self._run_trend_following_backtest(
                    data, initial_capital, commission_rate
                )
            elif "BREAKOUT" in template_id:
                results = self._run_breakout_backtest(
                    data, initial_capital, commission_rate
                )
            else:
                # Default simple backtest
                results = self._run_simple_backtest(
                    data, initial_capital, commission_rate
                )
            
            # Store backtest results
            self._store_backtest_result(strategy_id, start_date, end_date, results)
            
            return {
                "strategy_id": strategy_id,
                "strategy_name": strategy.name,
                "ticker": ticker,
                "template_id": template_id,
                "period": {"start": start_date, "end": end_date},
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Backtest error: {e}")
            return {"error": str(e)}
    
    def _fetch_historical_data(
        self,
        ticker: str,
        start_date: str,
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """Fetch historical price data from yfinance or database cache"""
        try:
            # Try database cache first
            from sqlalchemy import text
            result = self.db.execute(text("""
                SELECT date, close, high, low, volume 
                FROM silver.historical_stock_data 
                WHERE ticker = :ticker 
                AND date >= :start 
                AND date <= :end
                ORDER BY date
            """), {"ticker": ticker, "start": start_date, "end": end_date}).fetchall()
            
            if result and len(result) >= 30:
                df = pd.DataFrame(result, columns=['Date', 'Close', 'High', 'Low', 'Volume'])
                df.set_index('Date', inplace=True)
                return df
            
            # Fallback to yfinance
            yf_ticker = ticker
            if ticker.endswith("=X"):
                # FX pairs sometimes need different format
                yf_ticker = ticker
            
            data = yf.download(
                yf_ticker,
                start=start_date,
                end=end_date,
                progress=False,
                auto_adjust=True
            )
            
            if data.empty:
                # Try alternative ticker format
                alt_ticker = ticker.replace("=X", "")
                data = yf.download(
                    alt_ticker,
                    start=start_date,
                    end=end_date,
                    progress=False,
                    auto_adjust=True
                )
            
            if data.empty:
                return None
            
            # Flatten multi-level columns if present
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch data for {ticker}: {e}")
            return None
    
    def _run_mean_reversion_backtest(
        self,
        data: pd.DataFrame,
        initial_capital: float,
        commission_rate: float
    ) -> Dict:
        """Mean reversion strategy: Buy oversold, sell overbought"""
        
        closes = data['Close'].values.flatten()
        
        # Calculate RSI using pandas
        delta = pd.Series(closes).diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).values
        
        # Calculate Bollinger Bands using pandas
        rolling_mean = pd.Series(closes).rolling(window=20).mean().values
        rolling_std = pd.Series(closes).rolling(window=20).std().values
        bb_upper = rolling_mean + (rolling_std * 2.5)
        bb_lower = rolling_mean - (rolling_std * 2.5)
        
        capital = initial_capital
        position = 0  # 0 = no position, 1 = long, -1 = short
        position_size = 0
        entry_price = 0
        
        trades = []
        equity_curve = [{"date": data.index[0].strftime('%Y-%m-%d'), "equity": capital}]
        
        for i in range(30, len(closes)):  # Start after indicator warmup
            price = closes[i]
            date = data.index[i].strftime('%Y-%m-%d')
            
            # Trading logic
            signal = 0
            
            # Mean reversion signals
            if rsi[i] < 30 and price <= bb_lower[i]:
                signal = 1  # Buy oversold
            elif rsi[i] > 70 and price >= bb_upper[i]:
                signal = -1  # Sell overbought
            
            # Execute trades
            if signal == 1 and position <= 0:  # Buy
                if position == -1:  # Close short
                    pnl = (entry_price - price) * position_size
                    capital += pnl * (1 - commission_rate)
                    trades.append({
                        "date": date, "side": "COVER", "price": price,
                        "pnl": pnl, "commission": pnl * commission_rate
                    })
                
                # Open long
                position_size = capital * 0.95 / price  # 95% position sizing
                entry_price = price
                position = 1
                trades.append({"date": date, "side": "BUY", "price": price, "size": position_size})
                
            elif signal == -1 and position >= 0:  # Sell
                if position == 1:  # Close long
                    pnl = (price - entry_price) * position_size
                    capital += pnl * (1 - commission_rate)
                    trades.append({
                        "date": date, "side": "SELL", "price": price,
                        "pnl": pnl, "commission": pnl * commission_rate
                    })
                
                # Open short (if allowed)
                position_size = capital * 0.95 / price
                entry_price = price
                position = -1
                trades.append({"date": date, "side": "SHORT", "price": price, "size": position_size})
            
            # Calculate current equity
            if position == 1:
                current_equity = capital + (price - entry_price) * position_size
            elif position == -1:
                current_equity = capital + (entry_price - price) * position_size
            else:
                current_equity = capital
            
            equity_curve.append({"date": date, "equity": current_equity})
        
        # Close final position
        if position != 0:
            final_price = closes[-1]
            if position == 1:
                pnl = (final_price - entry_price) * position_size
            else:
                pnl = (entry_price - final_price) * position_size
            capital += pnl * (1 - commission_rate)
            trades.append({
                "date": data.index[-1].strftime('%Y-%m-%d'),
                "side": "CLOSE", "price": final_price, "pnl": pnl
            })
        
        return self._calculate_metrics(trades, equity_curve, initial_capital)
    
    def _run_trend_following_backtest(
        self,
        data: pd.DataFrame,
        initial_capital: float,
        commission_rate: float
    ) -> Dict:
        """Trend following strategy: Buy on uptrend, sell on downtrend"""
        
        closes = data['Close'].values.flatten()
        
        # Calculate EMAs using pandas
        ema20 = pd.Series(closes).ewm(span=20, adjust=False).mean().values
        ema50 = pd.Series(closes).ewm(span=50, adjust=False).mean().values
        
        # Calculate ATR manually
        highs = data['High'].values.flatten() if 'High' in data else closes
        lows = data['Low'].values.flatten() if 'Low' in data else closes
        tr1 = highs - lows
        tr2 = np.abs(highs - np.roll(closes, 1))
        tr3 = np.abs(lows - np.roll(closes, 1))
        atr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1).rolling(window=14).mean().values
        
        capital = initial_capital
        position = 0
        position_size = 0
        entry_price = 0
        
        trades = []
        equity_curve = [{"date": data.index[0].strftime('%Y-%m-%d'), "equity": capital}]
        
        for i in range(50, len(closes)):
            price = closes[i]
            date = data.index[i].strftime('%Y-%m-%d')
            
            # Trend following logic
            signal = 0
            if ema20[i] > ema50[i] and ema20[i-1] <= ema50[i-1]:
                signal = 1  # Golden cross - buy
            elif ema20[i] < ema50[i] and ema20[i-1] >= ema50[i-1]:
                signal = -1  # Death cross - sell
            
            # Execute trades
            if signal == 1 and position <= 0:
                if position == -1:
                    pnl = (entry_price - price) * position_size
                    capital += pnl * (1 - commission_rate)
                    trades.append({"date": date, "side": "COVER", "price": price, "pnl": pnl})
                
                position_size = capital * 0.95 / price
                entry_price = price
                position = 1
                trades.append({"date": date, "side": "BUY", "price": price, "size": position_size})
                
            elif signal == -1 and position >= 0:
                if position == 1:
                    pnl = (price - entry_price) * position_size
                    capital += pnl * (1 - commission_rate)
                    trades.append({"date": date, "side": "SELL", "price": price, "pnl": pnl})
                
                position_size = capital * 0.95 / price
                entry_price = price
                position = -1
                trades.append({"date": date, "side": "SHORT", "price": price, "size": position_size})
            
            # Calculate equity
            if position == 1:
                current_equity = capital + (price - entry_price) * position_size
            elif position == -1:
                current_equity = capital + (entry_price - price) * position_size
            else:
                current_equity = capital
            
            equity_curve.append({"date": date, "equity": current_equity})
        
        # Close final position
        if position != 0:
            final_price = closes[-1]
            if position == 1:
                pnl = (final_price - entry_price) * position_size
            else:
                pnl = (entry_price - final_price) * position_size
            capital += pnl * (1 - commission_rate)
            trades.append({
                "date": data.index[-1].strftime('%Y-%m-%d'),
                "side": "CLOSE", "price": final_price, "pnl": pnl
            })
        
        return self._calculate_metrics(trades, equity_curve, initial_capital)
    
    def _run_breakout_backtest(
        self,
        data: pd.DataFrame,
        initial_capital: float,
        commission_rate: float
    ) -> Dict:
        """Breakout strategy: Buy on range breakout"""
        import talib
        
        closes = data['Close'].values.flatten()
        highs = data['High'].values.flatten() if 'High' in data else closes
        lows = data['Low'].values.flatten() if 'Low' in data else closes
        
        capital = initial_capital
        position = 0
        position_size = 0
        entry_price = 0
        
        trades = []
        equity_curve = [{"date": data.index[0].strftime('%Y-%m-%d'), "equity": capital}]
        
        lookback = 20
        
        for i in range(lookback, len(closes)):
            price = closes[i]
            date = data.index[i].strftime('%Y-%m-%d')
            
            # Calculate range
            range_high = np.max(highs[i-lookback:i])
            range_low = np.min(lows[i-lookback:i])
            
            signal = 0
            if price > range_high * 0.99 and position <= 0:  # Breakout up
                signal = 1
            elif price < range_low * 1.01 and position >= 0:  # Breakout down
                signal = -1
            
            # Execute
            if signal == 1 and position <= 0:
                if position == -1:
                    pnl = (entry_price - price) * position_size
                    capital += pnl * (1 - commission_rate)
                    trades.append({"date": date, "side": "COVER", "price": price, "pnl": pnl})
                
                position_size = capital * 0.95 / price
                entry_price = price
                position = 1
                trades.append({"date": date, "side": "BUY", "price": price, "size": position_size})
                
            elif signal == -1 and position >= 0:
                if position == 1:
                    pnl = (price - entry_price) * position_size
                    capital += pnl * (1 - commission_rate)
                    trades.append({"date": date, "side": "SELL", "price": price, "pnl": pnl})
                
                position_size = capital * 0.95 / price
                entry_price = price
                position = -1
                trades.append({"date": date, "side": "SHORT", "price": price, "size": position_size})
            
            # Equity
            if position == 1:
                current_equity = capital + (price - entry_price) * position_size
            elif position == -1:
                current_equity = capital + (entry_price - price) * position_size
            else:
                current_equity = capital
            
            equity_curve.append({"date": date, "equity": current_equity})
        
        # Close final
        if position != 0:
            final_price = closes[-1]
            if position == 1:
                pnl = (final_price - entry_price) * position_size
            else:
                pnl = (entry_price - final_price) * position_size
            capital += pnl * (1 - commission_rate)
            trades.append({
                "date": data.index[-1].strftime('%Y-%m-%d'),
                "side": "CLOSE", "price": final_price, "pnl": pnl
            })
        
        return self._calculate_metrics(trades, equity_curve, initial_capital)
    
    def _run_simple_backtest(
        self,
        data: pd.DataFrame,
        initial_capital: float,
        commission_rate: float
    ) -> Dict:
        """Simple momentum-based backtest as fallback"""
        closes = data['Close'].values.flatten()
        
        capital = initial_capital
        position = 0
        position_size = 0
        entry_price = 0
        
        trades = []
        equity_curve = [{"date": data.index[0].strftime('%Y-%m-%d'), "equity": capital}]
        
        for i in range(10, len(closes)):
            price = closes[i]
            date = data.index[i].strftime('%Y-%m-%d')
            
            # Simple momentum: buy if up 2 days, sell if down 2 days
            signal = 0
            if closes[i] > closes[i-1] > closes[i-2] and position <= 0:
                signal = 1
            elif closes[i] < closes[i-1] < closes[i-2] and position >= 0:
                signal = -1
            
            if signal == 1 and position <= 0:
                if position == -1:
                    pnl = (entry_price - price) * position_size
                    capital += pnl * (1 - commission_rate)
                    trades.append({"date": date, "side": "COVER", "price": price, "pnl": pnl})
                
                position_size = capital * 0.95 / price
                entry_price = price
                position = 1
                trades.append({"date": date, "side": "BUY", "price": price, "size": position_size})
                
            elif signal == -1 and position >= 0:
                if position == 1:
                    pnl = (price - entry_price) * position_size
                    capital += pnl * (1 - commission_rate)
                    trades.append({"date": date, "side": "SELL", "price": price, "pnl": pnl})
                
                position_size = capital * 0.95 / price
                entry_price = price
                position = -1
                trades.append({"date": date, "side": "SHORT", "price": price, "size": position_size})
            
            if position == 1:
                current_equity = capital + (price - entry_price) * position_size
            elif position == -1:
                current_equity = capital + (entry_price - price) * position_size
            else:
                current_equity = capital
            
            equity_curve.append({"date": date, "equity": current_equity})
        
        if position != 0:
            final_price = closes[-1]
            if position == 1:
                pnl = (final_price - entry_price) * position_size
            else:
                pnl = (entry_price - final_price) * position_size
            capital += pnl * (1 - commission_rate)
            trades.append({
                "date": data.index[-1].strftime('%Y-%m-%d'),
                "side": "CLOSE", "price": final_price, "pnl": pnl
            })
        
        return self._calculate_metrics(trades, equity_curve, initial_capital)
    
    def _calculate_metrics(
        self,
        trades: List[Dict],
        equity_curve: List[Dict],
        initial_capital: float
    ) -> Dict:
        """Calculate backtest performance metrics"""
        if not trades:
            return {
                "total_return": 0,
                "total_return_pct": 0,
                "sharpe_ratio": 0,
                "max_drawdown": 0,
                "win_rate": 0,
                "total_trades": 0,
                "profitable_trades": 0,
                "losing_trades": 0,
                "avg_trade_return": 0,
                "trades": [],
                "equity_curve": equity_curve
            }
        
        # Filter to closing trades only for PnL calculation
        closing_trades = [t for t in trades if t.get("pnl") is not None]
        
        if not closing_trades:
            return {
                "total_return": 0,
                "total_return_pct": 0,
                "sharpe_ratio": 0,
                "max_drawdown": 0,
                "win_rate": 0,
                "total_trades": len(trades),
                "profitable_trades": 0,
                "losing_trades": 0,
                "avg_trade_return": 0,
                "trades": trades,
                "equity_curve": equity_curve
            }
        
        pnls = [t["pnl"] for t in closing_trades]
        winning_trades = [p for p in pnls if p > 0]
        losing_trades = [p for p in pnls if p < 0]
        
        # Calculate returns
        final_equity = equity_curve[-1]["equity"] if equity_curve else initial_capital
        total_return = final_equity - initial_capital
        total_return_pct = (total_return / initial_capital) * 100
        
        # Calculate daily returns for Sharpe
        if len(equity_curve) > 1:
            daily_returns = []
            for i in range(1, len(equity_curve)):
                prev = equity_curve[i-1]["equity"]
                curr = equity_curve[i]["equity"]
                if prev > 0:
                    daily_returns.append((curr - prev) / prev)
            
            if daily_returns and np.std(daily_returns) > 0:
                sharpe = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252)
            else:
                sharpe = 0
        else:
            sharpe = 0
        
        # Max drawdown
        peak = initial_capital
        max_dd = 0
        for point in equity_curve:
            equity = point["equity"]
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak
            if dd > max_dd:
                max_dd = dd
        
        return {
            "total_return": round(total_return, 2),
            "total_return_pct": round(total_return_pct, 2),
            "sharpe_ratio": round(sharpe, 2),
            "max_drawdown": round(max_dd * 100, 2),
            "win_rate": round(len(winning_trades) / len(closing_trades) * 100, 1) if closing_trades else 0,
            "total_trades": len(trades),
            "profitable_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "avg_trade_return": round(np.mean(pnls), 2) if pnls else 0,
            "trades": trades[-20:],  # Last 20 trades only to keep size reasonable
            "equity_curve": equity_curve[::5]  # Sample every 5th point
        }
    
    def _store_backtest_result(
        self,
        strategy_id: int,
        start_date: str,
        end_date: str,
        results: Dict
    ):
        """Store backtest result in database"""
        try:
            # First delete any existing backtest for this strategy+period
            self.db.execute(text("""
                DELETE FROM gold.backtest_runs 
                WHERE strategy_id = :sid AND start_date = :start AND end_date = :end
            """), {
                "sid": strategy_id,
                "start": start_date,
                "end": end_date
            })
            
            # Then insert new result
            self.db.execute(text("""
                INSERT INTO gold.backtest_runs 
                (strategy_id, run_date, start_date, end_date, total_return_pct, 
                 sharpe_ratio, max_drawdown_pct, win_rate, total_trades, 
                 avg_trade_return, raw_results)
                VALUES (:sid, NOW(), :start, :end, :ret, :sharpe, :dd, :wr, :trades, :avg, :raw)
            """), {
                "sid": strategy_id,
                "start": start_date,
                "end": end_date,
                "ret": results.get("total_return_pct", 0),
                "sharpe": results.get("sharpe_ratio", 0),
                "dd": results.get("max_drawdown", 0),
                "wr": results.get("win_rate", 0),
                "trades": results.get("total_trades", 0),
                "avg": results.get("avg_trade_return", 0),
                "raw": json.dumps(results)
            })
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to store backtest: {e}")
            self.db.rollback()
    
    def get_backtest_history(self, strategy_id: int) -> List[Dict]:
        """Get all backtest runs for a strategy"""
        try:
            results = self.db.execute(text("""
                SELECT * FROM gold.backtest_runs
                WHERE strategy_id = :sid
                ORDER BY run_date DESC
            """), {"sid": strategy_id}).fetchall()
            
            return [{
                "id": r.id,
                "run_date": r.run_date.isoformat() if r.run_date else None,
                "start_date": r.start_date.isoformat() if r.start_date else None,
                "end_date": r.end_date.isoformat() if r.end_date else None,
                "total_return_pct": r.total_return_pct,
                "sharpe_ratio": r.sharpe_ratio,
                "max_drawdown_pct": r.max_drawdown_pct,
                "win_rate": r.win_rate,
                "total_trades": r.total_trades,
                "avg_trade_return": r.avg_trade_return
            } for r in results]
        except Exception as e:
            logger.error(f"Failed to get backtest history: {e}")
            return []
    
    def compare_backtest_vs_live(self, strategy_id: int) -> Dict:
        """Compare backtest results with live performance"""
        strategy = self.db.query(QuantStrategy).filter(
            QuantStrategy.id == strategy_id
        ).first()
        
        if not strategy:
            return {"error": "Strategy not found"}
        
        # Get latest backtest
        backtests = self.get_backtest_history(strategy_id)
        if not backtests:
            return {"error": "No backtest data available"}
        
        latest_backtest = backtests[0]
        
        # Get live performance
        live_pnl = strategy.current_pnl or 0
        live_trades = strategy.total_trades or 0
        live_win_rate = (strategy.winning_trades / strategy.total_trades * 100) if strategy.total_trades else 0
        
        return {
            "strategy_id": strategy_id,
            "strategy_name": strategy.name,
            "backtest": latest_backtest,
            "live_performance": {
                "total_pnl": live_pnl,
                "total_trades": live_trades,
                "win_rate": round(live_win_rate, 1)
            },
            "comparison": {
                "return_diff": round(live_pnl - latest_backtest["total_return_pct"], 2),
                "trade_diff": live_trades - latest_backtest["total_trades"],
                "win_rate_diff": round(live_win_rate - latest_backtest["win_rate"], 1)
            }
        }


# Initialize engine
backtest_engine = BacktestEngine()

# Need json import
import json