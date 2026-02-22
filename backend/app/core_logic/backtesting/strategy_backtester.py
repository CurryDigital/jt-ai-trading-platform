"""
Proper Strategy Backtester with Entry/Exit Rules
Automated signal generation based on historical performance
"""
import pandas as pd
import numpy as np
import pandas_ta as ta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class Trade:
    entry_date: datetime
    exit_date: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    position: str  # 'LONG' or 'SHORT'
    size: float
    pnl: float
    pnl_pct: float
    exit_reason: str  # 'TARGET', 'STOP', 'TIME', 'SIGNAL'
    
@dataclass
class BacktestResult:
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    avg_trade_return: float
    num_trades: int
    winning_trades: int
    losing_trades: int
    trades: List[Trade]
    equity_curve: List[float]
    monthly_returns: Dict[str, float]

class StrategyBacktester:
    """
    Multi-strategy backtester with proper entry/exit rules
    """
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators needed for strategies"""
        df = df.copy()
        
        # Trend indicators
        df['SMA_20'] = ta.sma(df['Close'], length=20)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        df['EMA_12'] = ta.ema(df['Close'], length=12)
        df['EMA_26'] = ta.ema(df['Close'], length=26)
        
        # Momentum indicators
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['RSI_MA'] = ta.sma(df['RSI'], length=9)
        
        # MACD
        try:
            macd = ta.macd(df['Close'], fast=12, slow=26, signal=9)
            if macd is not None:
                df['MACD'] = macd.get('MACD_12_26_9', 0)
                df['MACD_Signal'] = macd.get('MACD_SIGNAL_12_26_9', 0)
                df['MACD_Hist'] = macd.get('MACD_HISTOGRAM_12_26_9', 0)
            else:
                df['MACD'] = 0
                df['MACD_Signal'] = 0
                df['MACD_Hist'] = 0
        except:
            df['MACD'] = 0
            df['MACD_Signal'] = 0
            df['MACD_Hist'] = 0
        
        # Volatility
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        try:
            bb = ta.bbands(df['Close'], length=20)
            if bb is not None:
                df['BB_Upper'] = bb.get('BBU_20_2.0', df['Close'])
                df['BB_Middle'] = bb.get('BBM_20_2.0', df['Close'])
                df['BB_Lower'] = bb.get('BBL_20_2.0', df['Close'])
            else:
                df['BB_Upper'] = df['Close'] * 1.02
                df['BB_Middle'] = df['Close']
                df['BB_Lower'] = df['Close'] * 0.98
        except:
            df['BB_Upper'] = df['Close'] * 1.02
            df['BB_Middle'] = df['Close']
            df['BB_Lower'] = df['Close'] * 0.98
        
        # Volume
        df['Volume_SMA'] = ta.sma(df['Volume'], length=20)
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
        
        return df
    
    def mean_reversion_strategy(self, df: pd.DataFrame, 
                                 rsi_entry: int = 30,
                                 rsi_exit: int = 70,
                                 max_holding_days: int = 10,
                                 position_size: float = 0.1) -> BacktestResult:
        """
        Mean Reversion Strategy:
        - ENTRY: RSI < 30 (oversold) AND price below lower Bollinger Band
        - EXIT: RSI > 70 OR price hits upper BB OR max holding days
        - STOP: 2x ATR below entry
        """
        df = self.calculate_indicators(df)
        trades = []
        equity = self.initial_capital
        equity_curve = [equity]
        in_position = False
        entry_date = None
        entry_price = None
        position_value = None
        
        for i in range(50, len(df)):
            current = df.iloc[i]
            date = df.index[i]
            
            if not in_position:
                # ENTRY RULES
                # 1. RSI oversold
                # 2. Price below lower BB
                # 3. Volume confirmation (above average)
                if (current['RSI'] < rsi_entry and 
                    current['Close'] < current['BB_Lower'] and
                    current['Volume_Ratio'] > 1.0):
                    
                    entry_price = current['Close']
                    entry_date = date
                    stop_loss = entry_price - (2 * current['ATR'])
                    target = entry_price + (3 * current['ATR'])
                    position_value = equity * position_size
                    shares = position_value / entry_price
                    in_position = True
                    
            else:
                # EXIT RULES
                holding_days = (date - entry_date).days
                current_price = current['Close']
                
                exit_triggered = False
                exit_reason = None
                exit_price = current_price
                
                # 1. Target hit (RSI > exit threshold)
                if current['RSI'] > rsi_exit:
                    exit_triggered = True
                    exit_reason = 'TARGET'
                
                # 2. Price hits upper Bollinger Band
                elif current_price >= current['BB_Upper']:
                    exit_triggered = True
                    exit_reason = 'TARGET'
                
                # 3. Stop loss
                elif current_price <= stop_loss:
                    exit_triggered = True
                    exit_reason = 'STOP'
                    exit_price = stop_loss
                
                # 4. Max holding period
                elif holding_days >= max_holding_days:
                    exit_triggered = True
                    exit_reason = 'TIME'
                
                if exit_triggered:
                    pnl = (exit_price - entry_price) * shares
                    pnl_pct = (exit_price / entry_price - 1) * 100
                    equity += pnl
                    
                    trades.append(Trade(
                        entry_date=entry_date,
                        exit_date=date,
                        entry_price=entry_price,
                        exit_price=exit_price,
                        position='LONG',
                        size=shares,
                        pnl=pnl,
                        pnl_pct=pnl_pct,
                        exit_reason=exit_reason
                    ))
                    
                    in_position = False
                    entry_date = None
                    entry_price = None
            
            equity_curve.append(equity)
        
        # Close any open position at end
        if in_position:
            current = df.iloc[-1]
            exit_price = current['Close']
            pnl = (exit_price - entry_price) * shares
            pnl_pct = (exit_price / entry_price - 1) * 100
            equity += pnl
            
            trades.append(Trade(
                entry_date=entry_date,
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
        
        return self._calculate_metrics(trades, equity_curve)
    
    def trend_following_strategy(self, df: pd.DataFrame,
                                  sma_fast: int = 20,
                                  sma_slow: int = 50,
                                  max_holding_days: int = 20,
                                  position_size: float = 0.15) -> BacktestResult:
        """
        Trend Following Strategy:
        - ENTRY: SMA 20 crosses above SMA 50 AND MACD positive
        - EXIT: SMA 20 crosses below SMA 50 OR time-based
        - STOP: 3x ATR below entry
        """
        df = self.calculate_indicators(df)
        trades = []
        equity = self.initial_capital
        equity_curve = [equity]
        in_position = False
        entry_date = None
        entry_price = None
        position_value = None
        
        for i in range(50, len(df)):
            current = df.iloc[i]
            prev = df.iloc[i-1]
            date = df.index[i]
            
            # SMA Cross detection
            sma_cross_up = (prev['SMA_20'] <= prev['SMA_50'] and 
                           current['SMA_20'] > current['SMA_50'])
            sma_cross_down = (prev['SMA_20'] >= prev['SMA_50'] and 
                             current['SMA_20'] < current['SMA_50'])
            
            if not in_position:
                # ENTRY: SMA cross up + MACD positive + volume
                if (sma_cross_up and 
                    current['MACD'] > 0 and
                    current['Volume_Ratio'] > 1.2):
                    
                    entry_price = current['Close']
                    entry_date = date
                    stop_loss = entry_price - (3 * current['ATR'])
                    position_value = equity * position_size
                    shares = position_value / entry_price
                    in_position = True
                    
            else:
                holding_days = (date - entry_date).days
                current_price = current['Close']
                
                exit_triggered = False
                exit_reason = None
                exit_price = current_price
                
                # EXIT RULES
                # 1. SMA cross down
                if sma_cross_down:
                    exit_triggered = True
                    exit_reason = 'SIGNAL'
                
                # 2. Stop loss
                elif current_price <= stop_loss:
                    exit_triggered = True
                    exit_reason = 'STOP'
                    exit_price = stop_loss
                
                # 3. Max holding
                elif holding_days >= max_holding_days:
                    exit_triggered = True
                    exit_reason = 'TIME'
                
                if exit_triggered:
                    pnl = (exit_price - entry_price) * shares
                    pnl_pct = (exit_price / entry_price - 1) * 100
                    equity += pnl
                    
                    trades.append(Trade(
                        entry_date=entry_date,
                        exit_date=date,
                        entry_price=entry_price,
                        exit_price=exit_price,
                        position='LONG',
                        size=shares,
                        pnl=pnl,
                        pnl_pct=pnl_pct,
                        exit_reason=exit_reason
                    ))
                    
                    in_position = False
            
            equity_curve.append(equity)
        
        # Close open position
        if in_position:
            current = df.iloc[-1]
            exit_price = current['Close']
            pnl = (exit_price - entry_price) * shares
            pnl_pct = (exit_price / entry_price - 1) * 100
            equity += pnl
            
            trades.append(Trade(
                entry_date=entry_date,
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
        
        return self._calculate_metrics(trades, equity_curve)
    
    def breakout_strategy(self, df: pd.DataFrame,
                          lookback: int = 20,
                          max_holding_days: int = 5,
                          position_size: float = 0.1) -> BacktestResult:
        """
        Breakout Strategy:
        - ENTRY: Price breaks above 20-day high with volume spike
        - EXIT: 3% profit target OR 2% stop OR 5 days
        """
        df = self.calculate_indicators(df)
        df['High_20'] = df['High'].rolling(window=lookback).max()
        
        trades = []
        equity = self.initial_capital
        equity_curve = [equity]
        in_position = False
        entry_date = None
        entry_price = None
        target_price = None
        stop_price = None
        shares = None
        
        for i in range(lookback, len(df)):
            current = df.iloc[i]
            prev = df.iloc[i-1]
            date = df.index[i]
            
            if not in_position:
                # ENTRY: Price breaks above 20-day high
                if (current['Close'] > prev['High_20'] and
                    current['Volume_Ratio'] > 1.5):
                    
                    entry_price = current['Close']
                    entry_date = date
                    target_price = entry_price * 1.03  # 3% profit
                    stop_price = entry_price * 0.98    # 2% stop
                    position_value = equity * position_size
                    shares = position_value / entry_price
                    in_position = True
                    
            else:
                holding_days = (date - entry_date).days
                current_price = current['Close']
                
                exit_triggered = False
                exit_reason = None
                exit_price = current_price
                
                # EXIT RULES
                if current_price >= target_price:
                    exit_triggered = True
                    exit_reason = 'TARGET'
                    exit_price = target_price
                
                elif current_price <= stop_price:
                    exit_triggered = True
                    exit_reason = 'STOP'
                    exit_price = stop_price
                
                elif holding_days >= max_holding_days:
                    exit_triggered = True
                    exit_reason = 'TIME'
                
                if exit_triggered:
                    pnl = (exit_price - entry_price) * shares
                    pnl_pct = (exit_price / entry_price - 1) * 100
                    equity += pnl
                    
                    trades.append(Trade(
                        entry_date=entry_date,
                        exit_date=date,
                        entry_price=entry_price,
                        exit_price=exit_price,
                        position='LONG',
                        size=shares,
                        pnl=pnl,
                        pnl_pct=pnl_pct,
                        exit_reason=exit_reason
                    ))
                    
                    in_position = False
            
            equity_curve.append(equity)
        
        # Close open position
        if in_position:
            current = df.iloc[-1]
            exit_price = current['Close']
            pnl = (exit_price - entry_price) * shares
            pnl_pct = (exit_price / entry_price - 1) * 100
            equity += pnl
            
            trades.append(Trade(
                entry_date=entry_date,
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
        
        return self._calculate_metrics(trades, equity_curve)
    
    def _calculate_metrics(self, trades: List[Trade], 
                          equity_curve: List[float]) -> BacktestResult:
        """Calculate performance metrics from trades"""
        
        if not trades:
            return BacktestResult(
                total_return=0,
                sharpe_ratio=0,
                max_drawdown=0,
                win_rate=0,
                profit_factor=0,
                avg_trade_return=0,
                num_trades=0,
                winning_trades=0,
                losing_trades=0,
                trades=[],
                equity_curve=equity_curve,
                monthly_returns={}
            )
        
        # Basic counts
        num_trades = len(trades)
        winning_trades = sum(1 for t in trades if t.pnl > 0)
        losing_trades = num_trades - winning_trades
        win_rate = winning_trades / num_trades
        
        # Returns
        total_return = (equity_curve[-1] / self.initial_capital - 1) * 100
        avg_trade_return = np.mean([t.pnl_pct for t in trades])
        
        # Profit factor
        gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Sharpe ratio (annualized)
        if len(equity_curve) > 1:
            returns = pd.Series(equity_curve).pct_change().dropna()
            if len(returns) > 1 and returns.std() > 0:
                sharpe = (returns.mean() / returns.std()) * np.sqrt(252)
            else:
                sharpe = 0
        else:
            sharpe = 0
        
        # Max drawdown
        equity_series = pd.Series(equity_curve)
        rolling_max = equity_series.expanding().max()
        drawdown = (equity_series - rolling_max) / rolling_max
        max_drawdown = abs(drawdown.min()) * 100
        
        # Monthly returns
        monthly_returns = {}
        
        return BacktestResult(
            total_return=round(total_return, 2),
            sharpe_ratio=round(sharpe, 2),
            max_drawdown=round(max_drawdown, 2),
            win_rate=round(win_rate, 2),
            profit_factor=round(profit_factor, 2),
            avg_trade_return=round(avg_trade_return, 2),
            num_trades=num_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            trades=trades,
            equity_curve=equity_curve,
            monthly_returns=monthly_returns
        )
    
    def get_current_signal(self, df: pd.DataFrame) -> Dict:
        """Get current signal for the stock based on latest data"""
        df = self.calculate_indicators(df)
        
        if len(df) < 50:
            return {'signal': 'HOLD', 'strength': 0, 'reason': 'Insufficient data'}
        
        current = df.iloc[-1]
        
        # Check mean reversion entry
        rsi = current.get('RSI', 50)
        bb_lower = current.get('BB_Lower', current['Close'] * 0.98)
        bb_upper = current.get('BB_Upper', current['Close'] * 1.02)
        
        entry_signal = False
        strength = 0.0
        
        # Mean reversion: RSI oversold and price below lower BB
        if rsi < 35 and current['Close'] < bb_lower:
            entry_signal = True
            strength = (35 - rsi) / 35 * 0.5 + (bb_lower - current['Close']) / bb_lower * 0.5
            signal_type = 'BUY'
        # Trend following: Price above SMA 20 and 20 > 50
        elif current['Close'] > current.get('SMA_20', 0) and current.get('SMA_20', 0) > current.get('SMA_50', 0):
            entry_signal = True
            strength = 0.6
            signal_type = 'BUY'
        else:
            signal_type = 'HOLD'
            strength = 0.0
        
        # Calculate stop and target based on ATR
        atr = current.get('ATR', current['Close'] * 0.02)
        stop = current['Close'] - (2 * atr)
        target = current['Close'] + (3 * atr)
        
        return {
            'signal': signal_type,
            'strength': round(min(1.0, strength), 2),
            'entry_price': round(current['Close'], 2),
            'stop_loss': round(stop, 2),
            'target': round(target, 2),
            'rationale': f"RSI: {rsi:.1f}, Price vs BB: {((current['Close'] - bb_lower) / bb_lower * 100):.1f}%"
        }
    
    def run_all_strategies(self, df: pd.DataFrame) -> Dict[str, BacktestResult]:
        """Run all strategies and return results"""
        return {
            'mean_reversion': self.mean_reversion_strategy(df),
            'trend_following': self.trend_following_strategy(df),
            'breakout': self.breakout_strategy(df)
        }
    
    def get_best_strategy(self, df: pd.DataFrame) -> Tuple[str, BacktestResult]:
        """Find the best performing strategy for this stock"""
        results = self.run_all_strategies(df)
        
        # Score each strategy based on multiple factors
        best_strategy = None
        best_score = -float('inf')
        
        for name, result in results.items():
            if result.num_trades < 5:  # Need minimum sample size
                continue
            
            # Composite score: win_rate * sharpe * log(num_trades)
            score = (result.win_rate * 
                    max(0, result.sharpe_ratio) * 
                    np.log1p(result.num_trades))
            
            if score > best_score:
                best_score = score
                best_strategy = (name, result)
        
        return best_strategy or ('none', results['mean_reversion'])


# Signal Generator for Pipeline
def generate_signals_from_backtest(df: pd.DataFrame, ticker: str) -> Dict:
    """
    Generate trading signals based on backtest results
    Returns signal data for the pipeline
    """
    backtester = StrategyBacktester(initial_capital=100000)
    
    # Get best strategy
    strategy_name, result = backtester.get_best_strategy(df)
    
    if result.num_trades < 3:
        return {
            'signal': 'HOLD',
            'confidence': 0.3,
            'strategy': 'NONE',
            'win_rate': 0.5,
            'expected_return': 0,
            'stop_loss': None,
            'target': None,
            'rationale': 'Insufficient data for reliable signal'
        }
    
    # Current indicators for entry check
    df = backtester.calculate_indicators(df)
    current = df.iloc[-1]
    
    # Check entry conditions based on best strategy
    entry_signal = False
    exit_signal = False
    
    if strategy_name == 'mean_reversion':
        entry_signal = (current['RSI'] < 35 and 
                       current['Close'] < current['BB_Lower'])
        exit_signal = current['RSI'] > 65
        
    elif strategy_name == 'trend_following':
        entry_signal = (current['SMA_20'] > current['SMA_50'] and 
                       current['MACD'] > 0 and
                       current['MACD'] > current['MACD_Signal'])
        exit_signal = current['SMA_20'] < current['SMA_50']
        
    elif strategy_name == 'breakout':
        high_20 = df['High'].rolling(window=20).max().iloc[-1]
        entry_signal = current['Close'] > high_20 * 0.98  # Near breakout
        exit_signal = False
    
    # Determine action
    if entry_signal:
        action = 'BUY'
    elif exit_signal:
        action = 'SELL'
    else:
        action = 'HOLD'
    
    # Calculate position size based on win rate and sharpe
    if result.sharpe_ratio > 1.5 and result.win_rate > 0.6:
        position_size = 0.15  # 15% of portfolio
    elif result.sharpe_ratio > 1.0 and result.win_rate > 0.55:
        position_size = 0.10  # 10% of portfolio
    else:
        position_size = 0.05  # 5% of portfolio
    
    # Calculate stop and target based on ATR
    atr = current['ATR'] if 'ATR' in current else current['Close'] * 0.02
    stop_loss = current['Close'] - (2 * atr)
    target = current['Close'] + (3 * atr)
    
    return {
        'signal': action,
        'confidence': min(0.95, result.win_rate * 1.2),  # Scale up slightly
        'strategy': strategy_name.upper(),
        'win_rate': result.win_rate,
        'sharpe_ratio': result.sharpe_ratio,
        'expected_return': result.avg_trade_return,
        'num_trades_backtest': result.num_trades,
        'stop_loss': round(stop_loss, 2),
        'target': round(target, 2),
        'position_size': position_size,
        'rationale': f"{strategy_name.replace('_', ' ').title()} strategy. "
                    f"Backtest: {result.win_rate*100:.0f}% win rate, "
                    f"{result.sharpe_ratio:.2f} Sharpe, "
                    f"{result.num_trades} trades. "
                    f"Current {action} signal."
    }


if __name__ == "__main__":
    # Test with sample data
    import yfinance as yf
    
    ticker = "AAPL"
    df = yf.Ticker(ticker).history(period="2y")
    
    print(f"\n=== Backtesting {ticker} ===\n")
    
    backtester = StrategyBacktester()
    results = backtester.run_all_strategies(df)
    
    for name, result in results.items():
        print(f"\n{name.upper()}:")
        print(f"  Trades: {result.num_trades} ({result.winning_trades}W / {result.losing_trades}L)")
        print(f"  Win Rate: {result.win_rate*100:.1f}%")
        print(f"  Sharpe: {result.sharpe_ratio:.2f}")
        print(f"  Total Return: {result.total_return:.1f}%")
        print(f"  Max DD: {result.max_drawdown:.1f}%")
    
    # Get best strategy signal
    print("\n=== CURRENT SIGNAL ===")
    signal = generate_signals_from_backtest(df, ticker)
    for k, v in signal.items():
        print(f"  {k}: {v}")
