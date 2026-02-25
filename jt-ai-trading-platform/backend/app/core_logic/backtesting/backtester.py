import pandas as pd
import numpy as np
import logging

class Backtester:
    """
    Standardized backtesting framework to evaluate ModelOrchestrator signals.
    """
    def __init__(self, initial_capital=100000.0):
        self.initial_capital = initial_capital
        self.logger = logging.getLogger(__name__)

    def run(self, signal_df, price_df):
        """
        Executes backtest logic.
        signal_df: DataFrame with 'ticker' and 'final_score'
        price_df: DataFrame with 'ticker', 'date', and 'close'
        """
        self.logger.info("Starting backtest...")
        
        # Merge signals with price data
        results = pd.merge(price_df, signal_df, on='ticker')
        
        # Calculate daily returns
        results['returns'] = results.groupby('ticker')['close'].pct_change()
        
        # Simple Logic: Position = final_score (clamped -1 to 1)
        # In a real scenario, this would involve time-series alignment
        results['position'] = results['final_score'].clip(-1, 1)
        results['strategy_returns'] = results['position'].shift(1) * results['returns']
        
        # Calculate Metrics
        metrics = self._calculate_metrics(results)
        return results, metrics

    def _calculate_metrics(self, results):
        cumulative_return = (1 + results['strategy_returns'].fillna(0)).prod() - 1
        sharpe_ratio = (results['strategy_returns'].mean() / results['strategy_returns'].std()) * np.sqrt(252) if results['strategy_returns'].std() != 0 else 0
        
        # Max Drawdown
        cum_rets = (1 + results['strategy_returns'].fillna(0)).cumprod()
        running_max = cum_rets.cummax()
        drawdown = (cum_rets - running_max) / running_max
        max_drawdown = drawdown.min()

        return {
            'Cumulative Return': f"{cumulative_return:.2%}",
            'Sharpe Ratio': f"{sharpe_ratio:.2f}",
            'Max Drawdown': f"{max_drawdown:.2%}"
        }

if __name__ == "__main__":
    # Test stub
    sample_signals = pd.DataFrame([{'ticker': 'AAPL', 'final_score': 0.8}])
    sample_prices = pd.DataFrame([
        {'ticker': 'AAPL', 'date': '2026-01-01', 'close': 150},
        {'ticker': 'AAPL', 'date': '2026-01-02', 'close': 155}
    ])
    
    bt = Backtester()
    res, met = bt.run(sample_signals, sample_prices)
    print("Metrics:", met)
