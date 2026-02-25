#!/usr/bin/env python3
"""
ARASO Backtest Engine
5-Year Historical Validation with Rolling Factor Model

Phase 3 Implementation
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from sqlalchemy import create_engine, text
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Backtest configuration."""
    start_date: datetime = field(default_factory=lambda: datetime(2019, 1, 1))
    end_date: datetime = field(default_factory=lambda: datetime(2024, 12, 31))
    initial_capital: float = 1_000_000
    rebalance_freq: int = 5  # Days between factor model updates
    transaction_cost: float = 0.001  # 10bps per trade
    max_positions: int = 20
    
    # Risk limits
    max_sector_exposure: float = 0.15
    max_single_position: float = 0.05
    stop_loss_pct: float = 0.03  # 3%
    
    # Signal thresholds
    entry_zscore: float = 1.5
    exit_zscore: float = 0.3
    hmm_threshold: float = 0.7


@dataclass
class Trade:
    """Individual trade record."""
    ticker: str
    entry_date: datetime
    exit_date: Optional[datetime]
    direction: int  # 1=long, -1=short
    entry_price: float
    exit_price: Optional[float]
    shares: int
    pnl: Optional[float]
    exit_reason: Optional[str]
    

@dataclass
class DailyPortfolio:
    """Daily portfolio snapshot."""
    date: datetime
    total_value: float
    cash: float
    positions: Dict[str, Dict]
    daily_pnl: float
    daily_return: float


class ARASOBacktester:
    """
    Complete backtesting engine for ARASO strategy.
    """
    
    def __init__(self, db_connector, config: BacktestConfig = None):
        self.db = db_connector
        self.config = config or BacktestConfig()
        self.trades: List[Trade] = []
        self.portfolio_history: List[DailyPortfolio] = []
        self.signals_history: List[Dict] = []
        
    def fetch_historical_data(self, tickers: List[str], 
                             start: datetime, 
                             end: datetime) -> pd.DataFrame:
        """
        Fetch historical prices from silver layer.
        """
        query = """
        SELECT date, ticker, close, volume
        FROM silver.historical_stock_data
        WHERE ticker = ANY(:tickers)
        AND date BETWEEN :start AND :end
        ORDER BY date, ticker
        """
        
        with self.db.engine.connect() as conn:
            df = pd.read_sql(text(query), conn,
                           params={'tickers': tickers,
                                  'start': start,
                                  'end': end})
        
        # Pivot to wide format
        prices = df.pivot(index='date', columns='ticker', values='close')
        volumes = df.pivot(index='date', columns='ticker', values='volume')
        
        return prices, volumes
    
    def calculate_returns(self, prices: pd.DataFrame) -> pd.DataFrame:
        """Calculate daily returns."""
        return prices.pct_change().dropna()
    
    def rolling_factor_model(self, returns: pd.DataFrame, 
                            window: int = 63) -> pd.DataFrame:
        """
        Calculate rolling factor exposures.
        Simplified version - in production use DynamicFactorModel.
        """
        # For backtest: use rolling PCA
        from sklearn.decomposition import PCA
        
        factor_returns = pd.DataFrame(index=returns.index)
        
        for i in range(window, len(returns)):
            date = returns.index[i]
            window_returns = returns.iloc[i-window:i].dropna(axis=1)
            
            if len(window_returns.columns) < 5:
                continue
            
            # Simple PCA (first 5 factors)
            pca = PCA(n_components=min(5, len(window_returns.columns)))
            factors = pca.fit_transform(window_returns.fillna(0))
            
            factor_returns.loc[date, 'F1'] = factors[-1, 0]
            factor_returns.loc[date, 'F2'] = factors[-1, 1] if factors.shape[1] > 1 else 0
            factor_returns.loc[date, 'F3'] = factors[-1, 2] if factors.shape[1] > 2 else 0
        
        return factor_returns
    
    def calculate_residuals(self, returns: pd.DataFrame, 
                           factor_returns: pd.DataFrame) -> pd.DataFrame:
        """Calculate residual returns."""
        # Simplified: subtract market factor
        residuals = returns.copy()
        
        for col in returns.columns:
            if 'F1' in factor_returns.columns:
                # Simple beta estimation
                beta = returns[col].corr(factor_returns['F1'])
                residuals[col] = returns[col] - beta * factor_returns['F1']
        
        return residuals
    
    def generate_signals(self, date: datetime, 
                        residuals: pd.Series,
                        zscores: pd.Series,
                        current_positions: Dict) -> List[Dict]:
        """
        Generate entry/exit signals for a given date.
        """
        signals = []
        
        for ticker in residuals.index:
            if ticker == 'F1':  # Skip factor columns
                continue
            
            z = zscores.get(ticker, 0)
            
            # Skip if already at max positions
            if len(current_positions) >= self.config.max_positions:
                # Only allow exits
                if ticker in current_positions:
                    pos = current_positions[ticker]
                    if abs(z) < self.config.exit_zscore:
                        signals.append({
                            'ticker': ticker,
                            'action': 'EXIT',
                            'direction': 0,
                            'zscore': z,
                            'reason': 'mean_reversion_complete'
                        })
                continue
            
            # Check for entry
            if abs(z) > self.config.entry_zscore:
                direction = -1 if z > 0 else 1  # Short if overbought, long if oversold
                
                signals.append({
                    'ticker': ticker,
                    'action': 'ENTRY',
                    'direction': direction,
                    'zscore': z,
                    'target_weight': min(abs(z) * 0.02, self.config.max_single_position)
                })
            
            # Check for exit of existing position
            elif ticker in current_positions:
                pos = current_positions[ticker]
                if abs(z) < self.config.exit_zscore:
                    signals.append({
                        'ticker': ticker,
                        'action': 'EXIT',
                        'direction': 0,
                        'zscore': z,
                        'reason': 'mean_reversion_complete'
                    })
        
        return signals
    
    def execute_signals(self, date: datetime, 
                       signals: List[Dict],
                       prices: pd.Series,
                       current_positions: Dict,
                       cash: float) -> Tuple[Dict, float, List[Trade]]:
        """
        Execute signals and update portfolio.
        """
        new_positions = current_positions.copy()
        new_cash = cash
        trades_executed = []
        
        for signal in signals:
            ticker = signal['ticker']
            action = signal['action']
            price = prices.get(ticker)
            
            if pd.isna(price):
                continue
            
            if action == 'EXIT' and ticker in current_positions:
                # Close position
                pos = current_positions[ticker]
                exit_value = pos['shares'] * price
                new_cash += exit_value * (1 - self.config.transaction_cost)
                
                # Record trade
                trade = Trade(
                    ticker=ticker,
                    entry_date=pos['entry_date'],
                    exit_date=date,
                    direction=pos['direction'],
                    entry_price=pos['entry_price'],
                    exit_price=price,
                    shares=pos['shares'],
                    pnl=(price - pos['entry_price']) * pos['shares'] * pos['direction'],
                    exit_reason=signal.get('reason', 'unknown')
                )
                trades_executed.append(trade)
                
                del new_positions[ticker]
            
            elif action == 'ENTRY' and ticker not in current_positions:
                # Open new position
                target_weight = signal['target_weight']
                position_value = target_weight * (cash + sum(
                    p['shares'] * prices.get(t, 0) 
                    for t, p in current_positions.items()
                ))
                
                shares = int(position_value / price)
                if shares < 1:
                    continue
                
                cost = shares * price * (1 + self.config.transaction_cost)
                if cost > cash:
                    continue
                
                new_cash -= cost
                new_positions[ticker] = {
                    'shares': shares * signal['direction'],
                    'entry_price': price,
                    'entry_date': date,
                    'direction': signal['direction'],
                    'entry_zscore': signal['zscore']
                }
        
        return new_positions, new_cash, trades_executed
    
    def run_backtest(self, universe: List[str]) -> Dict:
        """
        Run complete 5-year backtest.
        """
        logger.info(f"Starting backtest from {self.config.start_date} to {self.config.end_date}")
        logger.info(f"Universe: {len(universe)} tickers")
        
        # Fetch data
        prices, volumes = self.fetch_historical_data(
            universe, 
            self.config.start_date, 
            self.config.end_date
        )
        
        returns = self.calculate_returns(prices)
        
        # Calculate rolling factor model
        logger.info("Calculating rolling factor model...")
        factor_returns = self.rolling_factor_model(returns)
        residuals = self.calculate_residuals(returns, factor_returns)
        
        # Calculate z-scores
        zscores = residuals.rolling(window=20).apply(
            lambda x: (x.iloc[-1] - x.mean()) / x.std() if x.std() != 0 else 0
        )
        
        # Initialize portfolio
        cash = self.config.initial_capital
        positions = {}
        
        # Run simulation
        rebalance_dates = prices.index[::self.config.rebalance_freq]
        
        logger.info(f"Running simulation over {len(rebalance_dates)} rebalance dates...")
        
        for i, date in enumerate(rebalance_dates):
            if i % 50 == 0:
                logger.info(f"Processing {date}... ({i}/{len(rebalance_dates)})")
            
            # Get current prices
            current_prices = prices.loc[date] if date in prices.index else None
            if current_prices is None:
                continue
            
            # Generate signals
            if date in residuals.index and date in zscores.index:
                signals = self.generate_signals(
                    date,
                    residuals.loc[date],
                    zscores.loc[date],
                    positions
                )
                
                # Execute signals
                if signals:
                    positions, cash, trades = self.execute_signals(
                        date, signals, current_prices, positions, cash
                    )
                    self.trades.extend(trades)
            
            # Calculate portfolio value
            position_values = sum(
                p['shares'] * current_prices.get(t, 0)
                for t, p in positions.items()
            )
            total_value = cash + position_values
            
            # Record daily portfolio
            daily_pnl = total_value - (self.portfolio_history[-1].total_value if self.portfolio_history else self.config.initial_capital)
            daily_return = daily_pnl / (self.portfolio_history[-1].total_value if self.portfolio_history else self.config.initial_capital)
            
            self.portfolio_history.append(DailyPortfolio(
                date=date,
                total_value=total_value,
                cash=cash,
                positions=positions.copy(),
                daily_pnl=daily_pnl,
                daily_return=daily_return
            ))
        
        # Calculate performance metrics
        results = self.calculate_metrics()
        
        return results
    
    def calculate_metrics(self) -> Dict:
        """Calculate comprehensive performance metrics."""
        if not self.portfolio_history:
            return {}
        
        portfolio_df = pd.DataFrame([
            {
                'date': p.date,
                'total_value': p.total_value,
                'daily_return': p.daily_return
            }
            for p in self.portfolio_history
        ])
        
        returns = portfolio_df['daily_return'].dropna()
        
        # Basic metrics
        total_return = (portfolio_df['total_value'].iloc[-1] / self.config.initial_capital) - 1
        annualized_return = (1 + total_return) ** (252 / len(returns)) - 1
        volatility = returns.std() * np.sqrt(252)
        sharpe = annualized_return / volatility if volatility > 0 else 0
        
        # Drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Win rate
        trades_df = pd.DataFrame([
            {
                'ticker': t.ticker,
                'pnl': t.pnl,
                'direction': t.direction,
                'exit_reason': t.exit_reason
            }
            for t in self.trades if t.pnl is not None
        ])
        
        if len(trades_df) > 0:
            win_rate = (trades_df['pnl'] > 0).mean()
            avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if (trades_df['pnl'] > 0).any() else 0
            avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean() if (trades_df['pnl'] < 0).any() else 0
            profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        else:
            win_rate = avg_win = avg_loss = profit_factor = 0
        
        metrics = {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'num_trades': len(self.trades),
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'final_value': portfolio_df['total_value'].iloc[-1],
            'initial_value': self.config.initial_capital
        }
        
        return metrics
    
    def print_report(self, results: Dict):
        """Print formatted backtest report."""
        print("\n" + "=" * 60)
        print("ARASO BACKTEST RESULTS")
        print("=" * 60)
        print(f"Period: {self.config.start_date.date()} to {self.config.end_date.date()}")
        print(f"Initial Capital: ${self.config.initial_capital:,.0f}")
        print(f"Final Value: ${results.get('final_value', 0):,.0f}")
        print("-" * 60)
        print(f"Total Return: {results.get('total_return', 0)*100:.2f}%")
        print(f"Annualized Return: {results.get('annualized_return', 0)*100:.2f}%")
        print(f"Volatility: {results.get('volatility', 0)*100:.2f}%")
        print(f"Sharpe Ratio: {results.get('sharpe_ratio', 0):.2f}")
        print(f"Max Drawdown: {results.get('max_drawdown', 0)*100:.2f}%")
        print("-" * 60)
        print(f"Number of Trades: {results.get('num_trades', 0)}")
        print(f"Win Rate: {results.get('win_rate', 0)*100:.1f}%")
        print(f"Profit Factor: {results.get('profit_factor', 0):.2f}")
        print(f"Avg Win: ${results.get('avg_win', 0):,.0f}")
        print(f"Avg Loss: ${results.get('avg_loss', 0):,.0f}")
        print("=" * 60)
    
    def save_results(self, results: Dict, filename: str = None):
        """Save backtest results to file."""
        if filename is None:
            filename = f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        output = {
            'config': {
                'start_date': self.config.start_date.isoformat(),
                'end_date': self.config.end_date.isoformat(),
                'initial_capital': self.config.initial_capital,
                'max_positions': self.config.max_positions
            },
            'metrics': results,
            'trades': [
                {
                    'ticker': t.ticker,
                    'entry_date': t.entry_date.isoformat() if t.entry_date else None,
                    'exit_date': t.exit_date.isoformat() if t.exit_date else None,
                    'direction': t.direction,
                    'entry_price': t.entry_price,
                    'exit_price': t.exit_price,
                    'pnl': t.pnl,
                    'exit_reason': t.exit_reason
                }
                for t in self.trades
            ]
        }
        
        filepath = f"results/{filename}"
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        logger.info(f"Results saved to {filepath}")


def main():
    """Example backtest execution."""
    from araso_factor_model import DatabaseConnector
    
    # Initialize
    db = DatabaseConnector(
        username="your_username",
        password="your_password"
    )
    db.connect()
    
    # Universe (example: tech-focused for AI disruption thesis)
    universe = [
        'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'TSLA',
        'ADBE', 'ADSK', 'INTU', 'CRM', 'NOW', 'TEAM',
        'VRT', 'FN', 'MP'
    ]
    
    # Configure
    config = BacktestConfig(
        start_date=datetime(2019, 1, 1),
        end_date=datetime(2024, 12, 31),
        initial_capital=1_000_000
    )
    
    # Run backtest
    backtester = ARASOBacktester(db, config)
    results = backtester.run_backtest(universe)
    
    # Report
    backtester.print_report(results)
    backtester.save_results(results)
    
    return results


if __name__ == '__main__':
    main()
