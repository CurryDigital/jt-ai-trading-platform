"""
Strategy Screener - Backtest any strategy on all stocks
"""
import pandas as pd
import numpy as np
import pandas_ta as ta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

from app.core_logic.strategies.strategy_config import StrategyConfig, get_strategy_template
from app.core_logic.backtesting.strategy_backtester import StrategyBacktester, Trade

logger = logging.getLogger(__name__)

@dataclass
class StrategyScreenerResult:
    """Result of screening a stock with a strategy"""
    ticker: str
    market: str
    current_price: float
    
    # Backtest metrics
    win_rate: float
    sharpe_ratio: float
    profit_factor: float
    total_return: float
    max_drawdown: float
    num_trades: int
    avg_trade_return: float
    
    # Current signal
    signal: str  # BUY, SELL, HOLD
    signal_strength: float  # 0-1
    entry_price: Optional[float]
    stop_loss: Optional[float]
    target: Optional[float]
    
    # Ranking score
    strategy_score: float  # Composite score for ranking
    
    # Metadata
    rationale: str
    last_updated: str

class ConfigurableBacktester:
    """Backtester that uses StrategyConfig for rules"""
    
    def __init__(self, strategy: StrategyConfig, initial_capital: float = 100000.0):
        self.strategy = strategy
        self.initial_capital = initial_capital
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all indicators needed for strategy rules"""
        df = df.copy()
        
        # Get unique periods needed
        rsi_periods = set()
        sma_periods = set()
        
        for condition in self.strategy.entry_conditions + self.strategy.exit_conditions:
            if 'period' in condition:
                if condition['type'].startswith('rsi'):
                    rsi_periods.add(condition['period'])
                elif condition['type'].startswith('sma') or condition['type'].startswith('price'):
                    sma_periods.add(condition['period'])
            if 'fast' in condition:
                sma_periods.add(condition['fast'])
            if 'slow' in condition:
                sma_periods.add(condition['slow'])
        
        # Calculate RSI
        for period in rsi_periods:
            df[f'RSI_{period}'] = ta.rsi(df['Close'], length=period)
        
        # Calculate SMAs
        for period in sma_periods:
            df[f'SMA_{period}'] = ta.sma(df['Close'], length=period)
        
        # Always calculate common indicators
        df['SMA_20'] = ta.sma(df['Close'], length=20)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        df['RSI_14'] = ta.rsi(df['Close'], length=14)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        # MACD
        macd = ta.macd(df['Close'])
        if macd is not None:
            df['MACD'] = macd['MACD_12_26_9']
            df['MACD_Signal'] = macd['MACD_SIGNAL_12_26_9']
        
        # Bollinger Bands
        bb = ta.bbands(df['Close'], length=20)
        if bb is not None:
            df['BB_Upper'] = bb['BBU_20_2.0']
            df['BB_Lower'] = bb['BBL_20_2.0']
            df['BB_Middle'] = bb['BBM_20_2.0']
        
        # Volume
        df['Volume_SMA'] = ta.sma(df['Volume'], length=20)
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
        
        # Breakout levels
        df['High_20'] = df['High'].rolling(window=20).max()
        df['Low_20'] = df['Low'].rolling(window=20).min()
        
        return df
    
    def check_entry_conditions(self, df: pd.DataFrame, idx: int) -> bool:
        """Check if ALL entry conditions are met"""
        if idx < 50:  # Need enough data
            return False
            
        current = df.iloc[idx]
        
        for condition in self.strategy.entry_conditions:
            condition_type = condition['type']
            
            if condition_type == 'rsi_oversold':
                period = condition.get('period', 14)
                threshold = condition.get('threshold', 30)
                if current.get(f'RSI_{period}', 50) >= threshold:
                    return False
                    
            elif condition_type == 'rsi_overbought':
                period = condition.get('period', 14)
                threshold = condition.get('threshold', 70)
                if current.get(f'RSI_{period}', 50) <= threshold:
                    return False
                    
            elif condition_type == 'sma_cross_up':
                fast = condition.get('fast', 20)
                slow = condition.get('slow', 50)
                if idx > 0:
                    prev = df.iloc[idx-1]
                    if not (prev[f'SMA_{fast}'] <= prev[f'SMA_{slow}'] and 
                           current[f'SMA_{fast}'] > current[f'SMA_{slow}']):
                        return False
                else:
                    return False
                    
            elif condition_type == 'price_below_sma':
                period = condition.get('period', 20)
                if current['Close'] >= current.get(f'SMA_{period}', float('inf')):
                    return False
                    
            elif condition_type == 'price_above_sma':
                period = condition.get('period', 20)
                if current['Close'] <= current.get(f'SMA_{period}', 0):
                    return False
                    
            elif condition_type == 'macd_bullish':
                if current.get('MACD', 0) <= 0:
                    return False
                    
            elif condition_type == 'bb_lower_touch':
                if current['Close'] >= current.get('BB_Lower', 0):
                    return False
                    
            elif condition_type == 'breakout_high':
                lookback = condition.get('lookback', 20)
                if idx > 0:
                    prev = df.iloc[idx-1]
                    if current['Close'] <= prev.get(f'High_{lookback}', 0):
                        return False
                else:
                    return False
                    
            elif condition_type == 'volume_spike':
                threshold = condition.get('threshold', 1.0)
                if current.get('Volume_Ratio', 0) <= threshold:
                    return False
        
        return True  # All conditions met
    
    def check_exit_conditions(self, df: pd.DataFrame, idx: int, 
                             entry_price: float, entry_idx: int) -> Tuple[bool, str]:
        """Check if ANY exit condition is met. Returns (should_exit, reason)"""
        current = df.iloc[idx]
        holding_days = idx - entry_idx
        
        # Check stop loss first
        if self.strategy.stop_loss_type == 'atr':
            atr = current.get('ATR', entry_price * 0.02)
            stop_price = entry_price - (self.strategy.stop_loss_value * atr)
            if current['Close'] <= stop_price:
                return True, 'STOP'
        elif self.strategy.stop_loss_type == 'fixed_percent':
            stop_price = entry_price * (1 - self.strategy.stop_loss_value / 100)
            if current['Close'] <= stop_price:
                return True, 'STOP'
        
        # Check max holding
        if holding_days >= self.strategy.max_holding_days:
            return True, 'TIME'
        
        # Check other exit conditions
        for condition in self.strategy.exit_conditions:
            condition_type = condition['type']
            
            if condition_type == 'rsi_reversion':
                threshold = condition.get('threshold', 70)
                if current.get('RSI_14', 50) >= threshold:
                    return True, 'TARGET'
                    
            elif condition_type == 'sma_cross_opposite':
                if idx > 0:
                    prev = df.iloc[idx-1]
                    if (prev.get('SMA_20', 0) >= prev.get('SMA_50', 0) and 
                        current.get('SMA_20', 0) < current.get('SMA_50', 0)):
                        return True, 'SIGNAL'
                        
            elif condition_type == 'bb_upper_touch':
                if current['Close'] >= current.get('BB_Upper', float('inf')):
                    return True, 'TARGET'
                    
            elif condition_type == 'profit_target':
                target_pct = condition.get('percent', 5.0)
                target_price = entry_price * (1 + target_pct / 100)
                if current['Close'] >= target_price:
                    return True, 'TARGET'
        
        return False, ''
    
    def run_backtest(self, df: pd.DataFrame) -> Tuple[List[Trade], List[float]]:
        """Run backtest with configured strategy"""
        df = self.calculate_indicators(df)
        
        trades = []
        equity = self.initial_capital
        equity_curve = [equity]
        in_position = False
        entry_idx = None
        entry_price = None
        shares = None
        
        for i in range(50, len(df)):
            current = df.iloc[i]
            
            if not in_position:
                if self.check_entry_conditions(df, i):
                    entry_price = current['Close']
                    entry_idx = i
                    
                    # Calculate position size
                    if self.strategy.position_size_type == 'fixed':
                        position_value = equity * self.strategy.position_size_value
                    else:
                        position_value = equity * 0.1  # Default
                    
                    shares = position_value / entry_price
                    in_position = True
                    
            else:
                should_exit, reason = self.check_exit_conditions(
                    df, i, entry_price, entry_idx
                )
                
                if should_exit:
                    exit_price = current['Close']
                    if reason == 'STOP' and self.strategy.stop_loss_type == 'atr':
                        atr = current.get('ATR', entry_price * 0.02)
                        exit_price = entry_price - (self.strategy.stop_loss_value * atr)
                    
                    pnl = (exit_price - entry_price) * shares
                    pnl_pct = (exit_price / entry_price - 1) * 100
                    equity += pnl
                    
                    trades.append(Trade(
                        entry_date=df.index[entry_idx],
                        exit_date=df.index[i],
                        entry_price=entry_price,
                        exit_price=exit_price,
                        position='LONG',
                        size=shares,
                        pnl=pnl,
                        pnl_pct=pnl_pct,
                        exit_reason=reason
                    ))
                    
                    in_position = False
                    entry_idx = None
                    entry_price = None
            
            equity_curve.append(equity)
        
        # Close any open position
        if in_position:
            current = df.iloc[-1]
            exit_price = current['Close']
            pnl = (exit_price - entry_price) * shares
            pnl_pct = (exit_price / entry_price - 1) * 100
            equity += pnl
            
            trades.append(Trade(
                entry_date=df.index[entry_idx],
                exit_date=df.index[-1],
                entry_price=entry_price,
                exit_price=exit_price,
                position='LONG',
                size=shares,
                pnl=pnl,
                pnl_pct=pnl_pct,
                exit_reason='SIGNAL'
            ))
            equity_curve[-1] = equity
        
        return trades, equity_curve
    
    def get_current_signal(self, df: pd.DataFrame) -> Dict:
        """Get current signal for the stock"""
        df = self.calculate_indicators(df)
        
        if len(df) < 50:
            return {'signal': 'HOLD', 'strength': 0, 'reason': 'Insufficient data'}
        
        current = df.iloc[-1]
        
        # Check entry
        entry_ready = self.check_entry_conditions(df, len(df) - 1)
        
        # Calculate signal strength (0-1)
        strength = 0.0
        
        if entry_ready:
            signal = 'BUY'
            # Calculate strength based on how many conditions are strongly met
            for condition in self.strategy.entry_conditions:
                if condition['type'] == 'rsi_oversold':
                    rsi = current.get(f"RSI_{condition.get('period', 14)}", 50)
                    strength += (condition.get('threshold', 30) - rsi) / 30
                elif condition['type'] == 'volume_spike':
                    vol_ratio = current.get('Volume_Ratio', 1)
                    strength += min(1, (vol_ratio - 1) / 2)
            
            strength = min(1.0, strength / len(self.strategy.entry_conditions))
            
        else:
            signal = 'HOLD'
            strength = 0.0
        
        # Calculate stop and target
        atr = current.get('ATR', current['Close'] * 0.02)
        if self.strategy.stop_loss_type == 'atr':
            stop = current['Close'] - (self.strategy.stop_loss_value * atr)
        else:
            stop = current['Close'] * (1 - self.strategy.stop_loss_value / 100)
        
        target = current['Close'] + (3 * atr)  # 3:1 risk/reward
        
        return {
            'signal': signal,
            'strength': round(strength, 2),
            'entry_price': current['Close'],
            'stop_loss': round(stop, 2),
            'target': round(target, 2),
            'rationale': f"{self.strategy.name} strategy"
        }


def screen_stocks_with_strategy(
    strategy_id: str,
    tickers: List[str],
    min_win_rate: Optional[float] = None,
    min_sharpe: Optional[float] = None,
    min_trades: int = 5
) -> List[StrategyScreenerResult]:
    """
    Screen all stocks with a specific strategy
    Returns stocks ranked by strategy performance
    """
    import yfinance as yf
    from datetime import datetime
    
    strategy = get_strategy_template(strategy_id)
    if not strategy:
        logger.error(f"Strategy {strategy_id} not found")
        return []
    
    # Override min thresholds if provided
    if min_win_rate:
        strategy.min_win_rate = min_win_rate
    if min_sharpe:
        strategy.min_sharpe = min_sharpe
    
    backtester = ConfigurableBacktester(strategy)
    results = []
    
    for ticker in tickers:
        try:
            df = yf.Ticker(ticker).history(period="1y")
            if len(df) < 60:
                continue
            
            # Run backtest
            trades, equity_curve = backtester.run_backtest(df)
            
            if len(trades) < min_trades:
                continue
            
            # Calculate metrics
            wins = sum(1 for t in trades if t.pnl > 0)
            win_rate = wins / len(trades)
            
            returns = pd.Series(equity_curve).pct_change().dropna()
            sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
            
            total_return = (equity_curve[-1] / equity_curve[0] - 1) * 100
            
            equity_series = pd.Series(equity_curve)
            rolling_max = equity_series.expanding().max()
            drawdown = (equity_series - rolling_max) / rolling_max
            max_dd = abs(drawdown.min()) * 100
            
            gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
            gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            avg_return = np.mean([t.pnl_pct for t in trades])
            
            # Get current signal
            signal_data = backtester.get_current_signal(df)
            
            # Calculate strategy score
            weights = strategy.score_weights
            strategy_score = (
                win_rate * weights.get('win_rate', 0.4) +
                max(0, sharpe / 3) * weights.get('sharpe', 0.3) +
                min(1, profit_factor / 3) * weights.get('profit_factor', 0.2) +
                signal_data['strength'] * weights.get('recency', 0.1)
            )
            
            # Check minimum thresholds
            if win_rate < strategy.min_win_rate or sharpe < strategy.min_sharpe:
                continue
            
            results.append(StrategyScreenerResult(
                ticker=ticker,
                market='US',  # TODO: Detect from ticker
                current_price=df['Close'].iloc[-1],
                win_rate=round(win_rate, 2),
                sharpe_ratio=round(sharpe, 2),
                profit_factor=round(profit_factor, 2),
                total_return=round(total_return, 2),
                max_drawdown=round(max_dd, 2),
                num_trades=len(trades),
                avg_trade_return=round(avg_return, 2),
                signal=signal_data['signal'],
                signal_strength=signal_data['strength'],
                entry_price=signal_data['entry_price'],
                stop_loss=signal_data['stop_loss'],
                target=signal_data['target'],
                strategy_score=round(strategy_score, 3),
                rationale=signal_data['rationale'],
                last_updated=datetime.now().isoformat()
            ))
            
        except Exception as e:
            logger.error(f"Error screening {ticker}: {e}")
            continue
    
    # Sort by strategy score
    results.sort(key=lambda x: x.strategy_score, reverse=True)
    
    return results


if __name__ == "__main__":
    # Test screener
    tickers = ["AAPL", "MSFT", "NVDA", "TSLA"]
    
    print("=== Screening with Mean Reversion ===\n")
    results = screen_stocks_with_strategy("mean_reversion", tickers)
    
    for r in results:
        print(f"{r.ticker}: Score={r.strategy_score:.2f}, WR={r.win_rate:.0%}, "
              f"Sharpe={r.sharpe_ratio:.2f}, Signal={r.signal}")
