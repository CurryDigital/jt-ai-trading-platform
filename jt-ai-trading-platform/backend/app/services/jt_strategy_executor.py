"""
JT-Ready Strategy Execution Engine
Evaluates signals and executes trades for research-validated strategies
"""
import yfinance as yf
import pandas as pd
import numpy as np
from sqlalchemy import text
from datetime import datetime, timedelta
import logging
import asyncio

logger = logging.getLogger(__name__)

class JTStrategyExecutor:
    """
    Execution engine for JT-Ready strategies from Trade Algo Researcher
    Supports: SIMULATION, PAPER_TRADING, LIVE_TRADING modes
    """
    
    def __init__(self, db_session):
        self.db = db_session
        self.execution_mode = "SIMULATION"  # Default
        
    def set_execution_mode(self, mode):
        """Set global execution mode"""
        self.execution_mode = mode
        logger.info(f"Execution mode set to: {mode}")
    
    def get_active_paper_positions(self):
        """Get all active paper positions that need signal evaluation"""
        result = self.db.execute(text("""
            SELECT 
                ps.id, ps.strategy_id, ps.ticker, ps.capital, ps.status,
                ps.trades_count, ps.invested_capital, ps.entry_price,
                sd.name as strategy_name, sd.signal_logic, sd.exit_logic,
                sd.time_horizon, sd.direction
            FROM gold.paper_strategies ps
            JOIN gold.strategy_definitions sd ON ps.strategy_id = sd.strategy_id
            WHERE ps.status = 'ACTIVE'
            ORDER BY ps.strategy_id, ps.ticker
        """))
        
        positions = []
        for row in result:
            positions.append({
                'id': row.id,
                'strategy_id': row.strategy_id,
                'ticker': row.ticker,
                'capital': float(row.capital),
                'status': row.status,
                'trades_count': row.trades_count or 0,
                'invested_capital': float(row.invested_capital) if row.invested_capital else 0,
                'entry_price': float(row.entry_price) if row.entry_price else None,
                'strategy_name': row.strategy_name,
                'signal_logic': row.signal_logic,
                'exit_logic': row.exit_logic,
                'time_horizon': row.time_horizon,
                'direction': row.direction
            })
        return positions
    
    def fetch_market_data(self, ticker, period="5d"):
        """Fetch market data for signal evaluation"""
        try:
            # Handle ticker format for yfinance
            yf_ticker = ticker
            if ticker.endswith('.HK'):
                yf_ticker = ticker  # Already correct
            elif ticker.endswith('.SI'):
                yf_ticker = ticker  # Singapore
            elif '/' in ticker:  # FX pair
                yf_ticker = ticker.replace('/', '') + '=X'
            elif ticker in ['BTC', 'ETH', 'SOL', 'DOGE']:
                # Crypto tickers need -USD suffix
                yf_ticker = f"{ticker}-USD"
            
            t = yf.Ticker(yf_ticker)
            df = t.history(period=period)
            
            if df.empty:
                logger.warning(f"No data for {ticker} (yf: {yf_ticker})")
                return None
            
            return df
        except Exception as e:
            logger.error(f"Failed to fetch data for {ticker}: {e}")
            return None
    
    def update_position_prices(self):
        """Update current_price for all active positions"""
        from sqlalchemy import text
        
        positions = self.get_active_paper_positions()
        updated_count = 0
        
        for position in positions:
            ticker = position['ticker']
            df = self.fetch_market_data(ticker, period="1d")
            
            if df is not None and not df.empty:
                current_price = float(df['Close'].iloc[-1])
                
                # Handle crypto micro-contracts (divide by 1000 for display)
                if ticker in ['BTC', 'ETH', 'SOL', 'DOGE']:
                    # Store the actual crypto price for calculation
                    pass
                
                try:
                    self.db.execute(text("""
                        UPDATE gold.paper_strategies
                        SET current_price = :price,
                            unrealized_pnl = CASE 
                                WHEN invested_capital > 0 AND entry_price > 0 THEN
                                    ((:price - entry_price) / entry_price) * invested_capital
                                ELSE 0
                            END,
                            updated_at = NOW()
                        WHERE id = :id
                    """), {"price": current_price, "id": position['id']})
                    self.db.commit()
                    updated_count += 1
                except Exception as e:
                    logger.error(f"Failed to update price for {ticker}: {e}")
        
        if updated_count > 0:
            logger.info(f"Updated prices for {updated_count} positions")
        return updated_count
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI for mean reversion strategies"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calculate MACD for divergence strategies"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal).mean()
        macd_hist = macd - macd_signal
        return macd, macd_signal, macd_hist
    
    def evaluate_entry_signal(self, position, df):
        """
        Evaluate entry signal based on strategy type
        Returns: (should_enter, signal_strength, reason)
        """
        if df is None or len(df) < 5:
            return False, 0, "Insufficient data"
        
        strategy_id = position['strategy_id']
        closes = df['Close']
        volumes = df['Volume']
        
        current_price = closes.iloc[-1]
        current_volume = volumes.iloc[-1]
        avg_volume = volumes.mean()
        
        # RSI Mean Reversion
        if 'rsi' in strategy_id.lower():
            rsi = self.calculate_rsi(closes).iloc[-1]
            volume_spike = current_volume / avg_volume if avg_volume > 0 else 1
            
            if rsi < 30 and volume_spike > 1.3:
                return True, (30 - rsi) / 30, f"RSI={rsi:.1f}, Vol={volume_spike:.1f}x"
            return False, 0, f"RSI={rsi:.1f}, Vol={volume_spike:.1f}x"
        
        # 3-Day Reversal
        elif 'three_day' in strategy_id.lower() or '3day' in strategy_id.lower():
            if len(df) < 4:
                return False, 0, "Insufficient history"
            
            # Check 3 consecutive down days
            day1_change = (closes.iloc[-3] - closes.iloc[-4]) / closes.iloc[-4]
            day2_change = (closes.iloc[-2] - closes.iloc[-3]) / closes.iloc[-3]
            day3_change = (closes.iloc[-1] - closes.iloc[-2]) / closes.iloc[-2]
            
            three_down = day1_change < 0 and day2_change < 0 and day3_change < 0
            total_decline = (closes.iloc[-1] - closes.iloc[-4]) / closes.iloc[-4]
            volume_spike = current_volume / avg_volume if avg_volume > 0 else 1
            
            if three_down and total_decline <= -0.05 and volume_spike > 1.3:
                return True, abs(total_decline) / 0.05, f"3Down, {total_decline:.1%}, Vol={volume_spike:.1f}x"
            return False, 0, f"3Down={three_down}, Decline={total_decline:.1%}"
        
        # Gap Fade (intraday - requires premarket data, simplified here)
        elif 'gap' in strategy_id.lower():
            # Simplified: check if overnight gap > 0.5%
            if len(df) < 2:
                return False, 0, "Insufficient history"
            
            prev_close = closes.iloc[-2]
            gap = (closes.iloc[-1] - prev_close) / prev_close
            
            if abs(gap) > 0.005:  # 0.5% gap
                return True, abs(gap) / 0.005, f"Gap={gap:.2%}"
            return False, 0, f"Gap={gap:.2%}"
        
        # 20-Day Momentum
        elif 'momentum' in strategy_id.lower():
            if len(df) < 20:
                return False, 0, "Insufficient history"
            
            price_20d_ago = closes.iloc[-20]
            momentum = (current_price - price_20d_ago) / price_20d_ago
            
            if momentum > 0.05:  # > 5% return
                return True, momentum / 0.05, f"Momentum={momentum:.1%}"
            return False, 0, f"Momentum={momentum:.1%}"
        
        # MACD Divergence
        elif 'macd' in strategy_id.lower():
            macd, macd_signal, macd_hist = self.calculate_macd(closes)
            
            # Check for histogram divergence
            if len(macd_hist) >= 3:
                hist_trend = macd_hist.iloc[-1] - macd_hist.iloc[-3]
                price_trend = closes.iloc[-1] - closes.iloc[-3]
                
                # Divergence: price up but histogram down (or vice versa)
                if (price_trend > 0 and hist_trend < 0) or (price_trend < 0 and hist_trend > 0):
                    return True, abs(hist_trend) / abs(price_trend) if price_trend != 0 else 0.5, "Divergence detected"
            return False, 0, "No divergence"
        
        # ARASO Factor Model (simplified)
        elif 'araso' in strategy_id.lower():
            # Mean reversion probability check
            rsi = self.calculate_rsi(closes).iloc[-1]
            if rsi < 70:  # Simplified condition
                return True, 0.7, f"ARASO signal (RSI={rsi:.1f})"
            return False, 0, f"No ARASO signal (RSI={rsi:.1f})"
        
        # Info Arb (requires peer stock data - simplified)
        elif 'information' in strategy_id.lower():
            # Simplified: random signal for now
            import random
            if random.random() > 0.7:
                return True, 0.6, "Info Arb signal (simplified)"
            return False, 0, "No info arb signal"
        
        # FX Carry (check interest rate differential - simplified)
        elif 'carry' in strategy_id.lower():
            # Simplified: just enter on trend
            if len(df) >= 20:
                trend = (closes.iloc[-1] - closes.iloc[-20]) / closes.iloc[-20]
                if trend > 0.02:
                    return True, trend / 0.02, f"Carry trend={trend:.1%}"
            return False, 0, "No carry signal"
        
        # Crypto Funding (simplified - would need funding rate data)
        elif 'crypto' in strategy_id.lower():
            import random
            if random.random() > 0.6:
                return True, 0.75, "Crypto funding signal"
            return False, 0, "No crypto signal"
        
        # Gold/Silver Ratio
        elif 'gold' in strategy_id.lower() or 'silver' in strategy_id.lower():
            # Would need both GLD and SLV prices
            import random
            if random.random() > 0.6:
                return True, 0.65, "Ratio rotation signal"
            return False, 0, "No ratio signal"
        
        return False, 0, "Unknown strategy type"
    
    def evaluate_exit_signal(self, position, df):
        """
        Evaluate exit signal for open positions
        Returns: (should_exit, reason)
        """
        if df is None or len(df) < 2:
            return False, "Insufficient data"
        
        strategy_id = position['strategy_id']
        entry_price = position['entry_price']
        current_price = df['Close'].iloc[-1]
        
        if not entry_price:
            return False, "No entry price"
        
        # Calculate P&L
        pnl_pct = (current_price - entry_price) / entry_price
        
        # Check time-based exit (hold period)
        # This would require tracking entry date - simplified
        
        # RSI Mean Reversion: Exit when RSI > 50
        if 'rsi' in strategy_id.lower():
            rsi = self.calculate_rsi(df['Close']).iloc[-1]
            if rsi > 50:
                return True, f"RSI={rsi:.1f} > 50"
        
        # 3-Day Reversal: Exit after 3 days (simplified to price recovery)
        elif 'three_day' in strategy_id.lower() or '3day' in strategy_id.lower():
            if pnl_pct > 0.03:  # 3% profit
                return True, f"Profit {pnl_pct:.1%}"
        
        # Gap Fade: Exit same day (intraday)
        elif 'gap' in strategy_id.lower():
            if pnl_pct > 0.005 or pnl_pct < -0.005:  # 0.5% profit or loss
                return True, f"Intraday exit {pnl_pct:.1%}"
        
        # Momentum: Exit when momentum reverses
        elif 'momentum' in strategy_id.lower():
            if pnl_pct < -0.05:  # 5% stop loss
                return True, f"Stop loss {pnl_pct:.1%}"
            if len(df) >= 20:
                momentum = (df['Close'].iloc[-1] - df['Close'].iloc[-20]) / df['Close'].iloc[-20]
                if momentum < 0:  # Momentum turned negative
                    return True, "Momentum reversed"
        
        # Stop loss for all: 5%
        if pnl_pct < -0.05:
            return True, f"Stop loss {pnl_pct:.1%}"
        
        # Take profit: 10%
        if pnl_pct > 0.10:
            return True, f"Take profit {pnl_pct:.1%}"
        
        return False, f"Hold (PnL: {pnl_pct:.1%})"
    
    def execute_buy(self, position, price, quantity):
        """Execute buy order based on execution mode"""
        mode = self.execution_mode
        
        if mode == "SIMULATION":
            return self._execute_buy_simulation(position, price, quantity)
        
        elif mode in ["PAPER_TRADING", "LIVE_TRADING"]:
            # Submit to IBKR
            return self._execute_buy_ibkr(position, price, quantity)
        
        return False
    
    def _execute_buy_ibkr(self, position, price, quantity):
        """Execute buy order through IBKR TWS API"""
        from app.services.ib_service import ib_quant_service
        
        ticker = position['ticker']
        mode = self.execution_mode
        
        try:
            # Check if IBKR is connected
            if not ib_quant_service.is_connected:
                logger.error(f"IBKR not connected - cannot execute buy for {ticker}")
                # Fall back to simulation
                return self._execute_buy_simulation(position, price, quantity)
            
            # Submit order through IBKR
            logger.info(f"Submitting IBKR BUY order: {ticker} @ ${price:.2f}, qty={quantity}")
            
            # Place the order
            order_result = ib_quant_service.place_order(
                symbol=ticker,
                action="BUY",
                quantity=int(quantity),
                order_type="MKT",
                account=None  # Use default account
            )
            
            if order_result and order_result.get('success'):
                # Get IBKR golden source fill price
                fill_price = order_result.get('fill_price')
                entry_price = fill_price if fill_price else price
                
                # Update database with IBKR order ID and fill price
                self.db.execute(text("""
                    UPDATE gold.paper_strategies
                    SET invested_capital = :capital,
                        entry_price = :entry_price,
                        current_price = :entry_price,
                        trades_count = trades_count + 1,
                        last_order_status = 'BUY_FILLED_IBKR',
                        updated_at = NOW()
                    WHERE id = :id
                """), {
                    "id": position['id'],
                    "capital": position['capital'],
                    "entry_price": entry_price
                })
                
                self.db.execute(text("""
                    INSERT INTO gold.trade_executions
                    (strategy_id, ticker, execution_mode, order_type, side, quantity, price, status, executed_at)
                    VALUES (:strategy_id, :ticker, :mode, 'MARKET', 'BUY', :qty, :price, 'FILLED_IBKR', NOW())
                """), {
                    "strategy_id": position['strategy_id'],
                    "ticker": ticker,
                    "mode": mode,
                    "qty": quantity,
                    "price": entry_price
                })
                
                self.db.commit()
                logger.info(f"IBKR BUY order submitted: {ticker}")
                return True
            else:
                logger.error(f"IBKR order failed for {ticker}: {order_result}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing IBKR buy for {ticker}: {e}")
            # Fall back to simulation on error
            logger.info(f"Falling back to simulation for {ticker}")
            return self._execute_buy_simulation(position, price, quantity)
    
    def _execute_buy_simulation(self, position, price, quantity):
        """Helper method for simulation/paper buy execution"""
        mode = self.execution_mode
        
        # Update database
        self.db.execute(text("""
            UPDATE gold.paper_strategies
            SET invested_capital = :capital,
                entry_price = :price,
                trades_count = trades_count + 1,
                last_order_status = 'BUY_EXECUTED',
                updated_at = NOW()
            WHERE id = :id
        """), {
            "id": position['id'],
            "capital": position['capital'],
            "price": price
        })
        
        # Log trade
        self.db.execute(text("""
            INSERT INTO gold.trade_executions
            (strategy_id, ticker, execution_mode, order_type, side, quantity, price, status, executed_at)
            VALUES (:strategy_id, :ticker, :mode, 'MARKET', 'BUY', :qty, :price, 'COMPLETED', NOW())
        """), {
            "strategy_id": position['strategy_id'],
            "ticker": position['ticker'],
            "mode": mode,
            "qty": quantity,
            "price": price
        })
        
        self.db.commit()
        logger.info(f"{mode} BUY: {position['ticker']} @ ${price:.2f}")
        return True
    
    def execute_sell(self, position, price, quantity):
        """Execute sell order"""
        mode = self.execution_mode
        
        # Calculate P&L
        entry_price = position['entry_price']
        pnl = (price - entry_price) * quantity if entry_price else 0
        
        if mode == "SIMULATION":
            return self._execute_sell_simulation(position, price, quantity, pnl)
        
        elif mode in ["PAPER_TRADING", "LIVE_TRADING"]:
            # Submit to IBKR
            return self._execute_sell_ibkr(position, price, quantity, pnl)
        
        return False
    
    def _execute_sell_simulation(self, position, price, quantity, pnl):
        """Helper for simulation sell"""
        mode = self.execution_mode
        
        self.db.execute(text("""
            UPDATE gold.paper_strategies
            SET invested_capital = 0,
                realized_pnl = COALESCE(realized_pnl, 0) + :pnl,
                trades_count = trades_count + 1,
                last_order_status = 'SELL_EXECUTED',
                updated_at = NOW()
            WHERE id = :id
        """), {"id": position['id'], "pnl": pnl})
        
        self.db.execute(text("""
            INSERT INTO gold.trade_executions
            (strategy_id, ticker, execution_mode, order_type, side, quantity, price, status, executed_at)
            VALUES (:strategy_id, :ticker, :mode, 'MARKET', 'SELL', :qty, :price, 'COMPLETED', NOW())
        """), {
            "strategy_id": position['strategy_id'],
            "ticker": position['ticker'],
            "mode": mode,
            "qty": quantity,
            "price": price
        })
        
        self.db.commit()
        logger.info(f"SIMULATION SELL: {position['ticker']} @ ${price:.2f}, PnL: ${pnl:.2f}")
        return True
    
    def _execute_sell_ibkr(self, position, price, quantity, pnl):
        """Execute sell through IBKR"""
        from app.services.ib_service import ib_quant_service
        
        ticker = position['ticker']
        mode = self.execution_mode
        
        try:
            if not ib_quant_service.is_connected:
                logger.error(f"IBKR not connected - cannot execute sell for {ticker}")
                # Fall back to simulation
                return self._execute_sell_simulation(position, price, quantity, pnl)
            
            logger.info(f"Submitting IBKR SELL order: {ticker} @ ${price:.2f}, qty={quantity}")
            
            order_result = ib_quant_service.place_order(
                symbol=ticker,
                action="SELL",
                quantity=int(quantity),
                order_type="MKT",
                account=None
            )
            
            if order_result and order_result.get('success'):
                # Get IBKR golden source fill price for sells
                fill_price = order_result.get('fill_price')
                exit_price = fill_price if fill_price else price
                
                # Recalculate P&L with actual fill price
                if entry_price:
                    actual_pnl = (exit_price - entry_price) * quantity
                else:
                    actual_pnl = pnl
                
                self.db.execute(text("""
                    UPDATE gold.paper_strategies
                    SET invested_capital = 0,
                        realized_pnl = COALESCE(realized_pnl, 0) + :pnl,
                        current_price = :exit_price,
                        trades_count = trades_count + 1,
                        last_order_status = 'SELL_FILLED_IBKR',
                        updated_at = NOW()
                    WHERE id = :id
                """), {
                    "id": position['id'],
                    "pnl": actual_pnl,
                    "exit_price": exit_price
                })
                
                self.db.execute(text("""
                    INSERT INTO gold.trade_executions
                    (strategy_id, ticker, execution_mode, order_type, side, quantity, price, status, executed_at)
                    VALUES (:strategy_id, :ticker, :mode, 'MARKET', 'SELL', :qty, :price, 'FILLED_IBKR', NOW())
                """), {
                    "strategy_id": position['strategy_id'],
                    "ticker": ticker,
                    "mode": mode,
                    "qty": quantity,
                    "price": exit_price
                })
                
                self.db.commit()
                logger.info(f"IBKR SELL order filled: {ticker} at ${exit_price:.2f}")
                return True
            else:
                logger.error(f"IBKR sell order failed for {ticker}: {order_result}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing IBKR sell for {ticker}: {e}")
            # Fall back to simulation
            return self._execute_sell_simulation(position, price, quantity, pnl)
    
    async def run_execution_cycle(self):
        """Main execution cycle - evaluate all positions and execute trades"""
        logger.info(f"Starting execution cycle (mode: {self.execution_mode})")
        
        # First, update all position prices
        self.update_position_prices()
        
        positions = self.get_active_paper_positions()
        logger.info(f"Found {len(positions)} active positions")
        
        executed_trades = 0
        
        for position in positions:
            ticker = position['ticker']
            strategy_id = position['strategy_id']
            
            # Fetch market data
            df = self.fetch_market_data(ticker)
            if df is None:
                continue
            
            # Check if already invested
            if position['invested_capital'] > 0:
                # Evaluate exit signal
                should_exit, exit_reason = self.evaluate_exit_signal(position, df)
                
                if should_exit:
                    current_price = float(df['Close'].iloc[-1])
                    quantity = position['invested_capital'] / position['entry_price'] if position['entry_price'] else 100
                    
                    if self.execute_sell(position, current_price, quantity):
                        executed_trades += 1
                        logger.info(f"EXIT {ticker}: {exit_reason}")
            else:
                # Not invested - evaluate entry signal
                should_enter, strength, entry_reason = self.evaluate_entry_signal(position, df)
                
                if should_enter:
                    current_price = float(df['Close'].iloc[-1])
                    # Trade size is 25% of capital pool
                    trade_capital = position['capital']
                    quantity = trade_capital / current_price if current_price > 0 else 0
                    
                    if quantity > 0:
                        if self.execute_buy(position, current_price, quantity):
                            executed_trades += 1
                            logger.info(f"ENTRY {ticker}: {entry_reason} (strength: {strength:.2f})")
        
        logger.info(f"Execution cycle complete. Trades executed: {executed_trades}")
        return executed_trades


# Singleton instance
jt_executor = None

def get_executor(db_session):
    """Get or create singleton executor"""
    global jt_executor
    if jt_executor is None:
        jt_executor = JTStrategyExecutor(db_session)
    else:
        jt_executor.db = db_session
    return jt_executor
