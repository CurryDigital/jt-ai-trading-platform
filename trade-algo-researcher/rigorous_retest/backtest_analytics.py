#!/usr/bin/env python3
"""
Enhanced Backtest Framework with Comprehensive P&L Analytics
Tracks: Win Rate, Total Return, Profit Factor, Expectancy, Sharpe, Max DD
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class BacktestAnalytics:
    """Comprehensive backtest analytics with P&L focus"""
    
    @staticmethod
    def calculate_metrics(trades_df, hold_days=10, initial_capital=100000):
        """
        Calculate comprehensive performance metrics
        
        Args:
            trades_df: DataFrame with 'pnl' column (percentage returns per trade)
            hold_days: Average hold period in days
            initial_capital: Starting capital for calculations
        
        Returns:
            Dictionary of performance metrics
        """
        if len(trades_df) == 0:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_return_pct': 0,
                'avg_return_per_trade': 0,
                'profit_factor': 0,
                'sharpe_ratio': 0,
                'max_drawdown_pct': 0,
                'expectancy': 0,
                'win_loss_ratio': 0,
                'cagr': 0,
                'volatility': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'largest_win': 0,
                'largest_loss': 0,
                'consecutive_wins': 0,
                'consecutive_losses': 0
            }
        
        # Basic counts
        total_trades = len(trades_df)
        wins = trades_df[trades_df['pnl'] > 0]
        losses = trades_df[trades_df['pnl'] <= 0]
        
        n_wins = len(wins)
        n_losses = len(losses)
        
        # Win rate
        win_rate = (n_wins / total_trades) * 100 if total_trades > 0 else 0
        
        # Returns
        total_return_pct = trades_df['pnl'].sum()
        avg_return_per_trade = trades_df['pnl'].mean()
        
        # Profit factor (gross profits / gross losses)
        gross_profits = wins['pnl'].sum() if n_wins > 0 else 0
        gross_losses = abs(losses['pnl'].sum()) if n_losses > 0 else 0.001
        profit_factor = gross_profits / gross_losses if gross_losses > 0 else 0
        
        # Win/Loss ratio (avg win / avg loss)
        avg_win = wins['pnl'].mean() if n_wins > 0 else 0
        avg_loss = abs(losses['pnl'].mean()) if n_losses > 0 else 0.001
        win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        
        # Expectancy: (Win% × Avg Win) - (Loss% × Avg Loss)
        win_pct = n_wins / total_trades
        loss_pct = n_losses / total_trades
        expectancy = (win_pct * avg_win) - (loss_pct * avg_loss)
        
        # Volatility and Sharpe
        volatility = trades_df['pnl'].std()
        sharpe_ratio = (avg_return_per_trade / volatility * np.sqrt(252/hold_days)) if volatility > 0 else 0
        
        # Max Drawdown (simulated equity curve)
        equity_curve = initial_capital * (1 + trades_df['pnl']/100).cumprod()
        rolling_max = equity_curve.expanding().max()
        drawdown = (equity_curve - rolling_max) / rolling_max * 100
        max_drawdown_pct = abs(drawdown.min())
        
        # CAGR calculation
        total_days = hold_days * total_trades
        years = total_days / 252
        final_capital = initial_capital * (1 + total_return_pct/100)
        cagr = ((final_capital / initial_capital) ** (1/years) - 1) * 100 if years > 0 else 0
        
        # LATEST 3-MONTH P&L (most recent quarterly performance)
        if 'exit_date' in trades_df.columns:
            # Ensure exit_date is datetime
            trades_df['exit_date'] = pd.to_datetime(trades_df['exit_date'])
            
            # Get latest date in dataset
            latest_date = trades_df['exit_date'].max()
            three_months_ago = latest_date - timedelta(days=90)
            
            # Filter last 3 months
            latest_3m = trades_df[trades_df['exit_date'] >= three_months_ago]
            
            if len(latest_3m) > 0:
                latest_3m_return = latest_3m['pnl'].sum()
                latest_3m_trades = len(latest_3m)
                latest_3m_wr = (latest_3m['pnl'] > 0).mean() * 100
                latest_3m_expectancy = latest_3m['pnl'].mean()
            else:
                latest_3m_return = 0
                latest_3m_trades = 0
                latest_3m_wr = 0
                latest_3m_expectancy = 0
        else:
            # If no dates, assume all trades are historical
            latest_3m_return = 0
            latest_3m_trades = 0
            latest_3m_wr = 0
            latest_3m_expectancy = 0
        
        # Consecutive wins/losses
        trades_df['win_flag'] = trades_df['pnl'] > 0
        trades_df['group'] = (trades_df['win_flag'] != trades_df['win_flag'].shift()).cumsum()
        
        if n_wins > 0:
            consecutive_wins = trades_df[trades_df['win_flag']].groupby('group').size().max()
        else:
            consecutive_wins = 0
            
        if n_losses > 0:
            consecutive_losses = trades_df[~trades_df['win_flag']].groupby('group').size().max()
        else:
            consecutive_losses = 0
        
        # Largest win/loss
        largest_win = wins['pnl'].max() if n_wins > 0 else 0
        largest_loss = losses['pnl'].min() if n_losses > 0 else 0
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_return_pct': total_return_pct,
            'avg_return_per_trade': avg_return_per_trade,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown_pct': max_drawdown_pct,
            'expectancy': expectancy,
            'win_loss_ratio': win_loss_ratio,
            'cagr': cagr,
            'volatility': volatility,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'consecutive_wins': consecutive_wins,
            'consecutive_losses': consecutive_losses,
            # LATEST 3-MONTH METRICS
            'latest_3m_return': latest_3m_return,
            'latest_3m_trades': latest_3m_trades,
            'latest_3m_wr': latest_3m_wr,
            'latest_3m_expectancy': latest_3m_expectancy
        }
    
    @staticmethod
    def print_metrics(metrics, title="Performance Metrics"):
        """Print formatted metrics table"""
        print(f"\n{'='*70}")
        print(f"📊 {title}")
        print(f"{'='*70}")
        
        print(f"\n🎯 TRADE STATISTICS:")
        print(f"  Total Trades:       {metrics['total_trades']}")
        print(f"  Win Rate:           {metrics['win_rate']:.1f}%")
        print(f"  Win/Loss Ratio:     {metrics['win_loss_ratio']:.2f}")
        print(f"  Consecutive Wins:   {metrics['consecutive_wins']}")
        print(f"  Consecutive Losses: {metrics['consecutive_losses']}")
        
        print(f"\n💰 RETURN ANALYSIS:")
        print(f"  Total Return:       {metrics['total_return_pct']:+.2f}%")
        print(f"  Avg Return/Trade:   {metrics['avg_return_per_trade']:+.2f}%")
        print(f"  Expectancy:         {metrics['expectancy']:+.2f}%")
        print(f"  CAGR:               {metrics['cagr']:.1f}%")
        
        # LATEST 3-MONTH PERFORMANCE
        print(f"\n📅 LATEST 3-MONTH PERFORMANCE:")
        print(f"  3M Return:          {metrics['latest_3m_return']:+.2f}%")
        print(f"  3M Trades:          {metrics['latest_3m_trades']}")
        print(f"  3M Win Rate:        {metrics['latest_3m_wr']:.1f}%")
        print(f"  3M Expectancy:      {metrics['latest_3m_expectancy']:+.2f}%")
        
        # Feasibility assessment based on latest 3M
        if metrics['latest_3m_trades'] >= 5:
            if metrics['latest_3m_return'] > 5 and metrics['latest_3m_wr'] >= 55:
                print(f"  🟢 FEASIBILITY:     HOT — Recent performance strong")
            elif metrics['latest_3m_return'] > 0:
                print(f"  🟡 FEASIBILITY:     WARM — Recent performance positive")
            else:
                print(f"  🔴 FEASIBILITY:     COLD — Recent underperformance")
        else:
            print(f"  ⚪ FEASIBILITY:     INSUFFICIENT DATA — <5 trades in last 3M")
        
        print(f"\n📈 RISK METRICS:")
        print(f"  Profit Factor:      {metrics['profit_factor']:.2f}")
        print(f"  Sharpe Ratio:       {metrics['sharpe_ratio']:.2f}")
        print(f"  Max Drawdown:       {metrics['max_drawdown_pct']:.1f}%")
        print(f"  Volatility:         {metrics['volatility']:.2f}%")
        
        print(f"\n📊 P&L BREAKDOWN:")
        print(f"  Avg Win:            +{metrics['avg_win']:.2f}%")
        print(f"  Avg Loss:           {metrics['avg_loss']:.2f}%")
        print(f"  Largest Win:        +{metrics['largest_win']:.2f}%")
        print(f"  Largest Loss:       {metrics['largest_loss']:.2f}%")
        
        # Verdict
        print(f"\n🎓 VERDICT:")
        if metrics['win_rate'] >= 55 and metrics['expectancy'] > 0 and metrics['profit_factor'] > 1.2:
            print(f"  ✅ STRATEGY VALIDATED")
        elif metrics['expectancy'] > 0:
            print(f"  ⚠️  MARGINAL — Monitor closely")
        else:
            print(f"  ❌ REJECTED — Negative expectancy")
        
        print(f"{'='*70}\n")
    
    @staticmethod
    def calculate_3tier_summary(results_list):
        """
        Summarize results across 3-tier validation
        
        Args:
            results_list: List of dicts with 'train', 'test', 'validate' metrics
        
        Returns:
            Summary DataFrame
        """
        summary = []
        for result in results_list:
            row = {
                'ticker': result.get('ticker', 'Unknown'),
                'market': result.get('market', 'Unknown'),
                'train_trades': result.get('train_metrics', {}).get('total_trades', 0),
                'train_wr': result.get('train_metrics', {}).get('win_rate', 0),
                'train_return': result.get('train_metrics', {}).get('total_return_pct', 0),
                'train_expectancy': result.get('train_metrics', {}).get('expectancy', 0),
                'test_trades': result.get('test_metrics', {}).get('total_trades', 0),
                'test_wr': result.get('test_metrics', {}).get('win_rate', 0),
                'test_return': result.get('test_metrics', {}).get('total_return_pct', 0),
                'test_expectancy': result.get('test_metrics', {}).get('expectancy', 0),
                'validate_trades': result.get('validate_metrics', {}).get('total_trades', 0),
                'validate_wr': result.get('validate_metrics', {}).get('win_rate', 0),
                'validate_return': result.get('validate_metrics', {}).get('total_return_pct', 0),
                'validate_expectancy': result.get('validate_metrics', {}).get('expectancy', 0),
            }
            summary.append(row)
        
        return pd.DataFrame(summary)

    @staticmethod
    def monte_carlo_simulation(trades_df, n_simulations=1000, hold_days=10, initial_capital=100000, confidence_level=0.95):
        """
        Monte Carlo simulation to test strategy robustness
        
        Args:
            trades_df: DataFrame with trade P&Ls
            n_simulations: Number of Monte Carlo runs (default: 1000)
            hold_days: Hold period in days
            initial_capital: Starting capital
            confidence_level: Confidence interval (default: 0.95)
        
        Returns:
            Dictionary with Monte Carlo statistics
        """
        if len(trades_df) < 10:
            return {
                'mc_mean_return': 0,
                'mc_median_return': 0,
                'mc_std_return': 0,
                'mc_worst_case': 0,
                'mc_best_case': 0,
                'mc_var_95': 0,
                'mc_cvar_95': 0,
                'mc_prob_profit': 0,
                'mc_prob_double': 0,
                'mc_sharpe_mean': 0,
                'mc_sharpe_std': 0,
                'mc_robustness_score': 0
            }
        
        # Extract P&Ls
        pnls = trades_df['pnl'].values
        
        # Run Monte Carlo simulations
        mc_returns = []
        mc_sharpes = []
        mc_max_dd = []
        
        np.random.seed(42)  # For reproducibility
        
        for _ in range(n_simulations):
            # Resample trades with replacement
            sample_size = len(pnls)
            sampled_pnls = np.random.choice(pnls, size=sample_size, replace=True)
            
            # Calculate metrics for this simulation
            total_return = np.sum(sampled_pnls)
            mc_returns.append(total_return)
            
            # Calculate Sharpe for this path
            if np.std(sampled_pnls) > 0:
                sharpe = (np.mean(sampled_pnls) / np.std(sampled_pnls)) * np.sqrt(252/hold_days)
                mc_sharpes.append(sharpe)
            
            # Calculate max drawdown for this path
            equity = initial_capital * (1 + np.cumsum(sampled_pnls)/100)
            rolling_max = np.maximum.accumulate(equity)
            drawdown = (equity - rolling_max) / rolling_max * 100
            mc_max_dd.append(abs(np.min(drawdown)))
        
        mc_returns = np.array(mc_returns)
        mc_sharpes = np.array(mc_sharpes)
        mc_max_dd = np.array(mc_max_dd)
        
        # Calculate statistics
        alpha = 1 - confidence_level
        
        return {
            'mc_mean_return': np.mean(mc_returns),
            'mc_median_return': np.median(mc_returns),
            'mc_std_return': np.std(mc_returns),
            'mc_worst_case': np.percentile(mc_returns, alpha*100),
            'mc_best_case': np.percentile(mc_returns, (1-alpha)*100),
            'mc_var_95': np.percentile(mc_returns, 5),  # Value at Risk (5% worst)
            'mc_cvar_95': np.mean(mc_returns[mc_returns <= np.percentile(mc_returns, 5)]),  # Conditional VaR
            'mc_prob_profit': np.mean(mc_returns > 0) * 100,  # Probability of profit
            'mc_prob_double': np.mean(mc_returns > 100) * 100,  # Probability of doubling
            'mc_sharpe_mean': np.mean(mc_sharpes) if len(mc_sharpes) > 0 else 0,
            'mc_sharpe_std': np.std(mc_sharpes) if len(mc_sharpes) > 0 else 0,
            'mc_max_dd_mean': np.mean(mc_max_dd),
            'mc_max_dd_worst': np.max(mc_max_dd),
            'mc_robustness_score': np.mean(mc_returns > 0) * 100  # % of profitable paths
        }
    
    @staticmethod
    def transaction_cost_sensitivity(trades_df, hold_days=10, initial_capital=100000):
        """
        Test strategy sensitivity to different transaction cost levels
        
        Args:
            trades_df: DataFrame with trade P&Ls (pre-cost)
            hold_days: Hold period in days
            initial_capital: Starting capital
        
        Returns:
            Dictionary with cost sensitivity analysis
        """
        if len(trades_df) == 0:
            return {
                'cost_005_return': 0,
                'cost_010_return': 0,
                'cost_020_return': 0,
                'cost_050_return': 0,
                'cost_break_even': 0,
                'cost_robustness': 'N/A'
            }
        
        # Transaction cost levels to test
        cost_levels = [0.05, 0.10, 0.20, 0.50]  # % per trade (round-trip)
        
        results = {}
        pnls = trades_df['pnl'].values
        n_trades = len(pnls)
        
        for cost in cost_levels:
            # Subtract transaction costs from each trade
            adjusted_pnls = pnls - cost
            
            # Calculate total return with costs
            total_return = np.sum(adjusted_pnls)
            results[f'cost_{int(cost*100):03d}_return'] = total_return
            
            # Check if still profitable
            results[f'cost_{int(cost*100):03d}_profitable'] = total_return > 0
            
            # Calculate win rate with costs
            wins_with_cost = np.sum(adjusted_pnls > 0)
            results[f'cost_{int(cost*100):03d}_wr'] = (wins_with_cost / n_trades) * 100
        
        # Find break-even cost
        costs_tested = np.array(cost_levels)
        returns = np.array([results[f'cost_{int(c*100):03d}_return'] for c in cost_levels])
        
        if returns[0] > 0 and returns[-1] < 0:
            for i in range(len(costs_tested)-1):
                if returns[i] > 0 and returns[i+1] < 0:
                    break_even = costs_tested[i] + (0 - returns[i]) * (costs_tested[i+1] - costs_tested[i]) / (returns[i+1] - returns[i])
                    results['cost_break_even'] = break_even
                    break
        elif returns[-1] > 0:
            results['cost_break_even'] = costs_tested[-1] + 0.1
        else:
            results['cost_break_even'] = 0
        
        # Robustness score
        profitable_count = sum([results[f'cost_{int(c*100):03d}_profitable'] for c in cost_levels])
        results['cost_robustness'] = f"{profitable_count}/{len(cost_levels)}"
        results['cost_robustness_score'] = (profitable_count / len(cost_levels)) * 100
        
        return results
    
    @staticmethod
    def print_monte_carlo(mc_metrics):
        """Print Monte Carlo results"""
        print(f"\n🎲 MONTE CARLO SIMULATION (1,000 paths):")
        print(f"  Mean Return:        {mc_metrics['mc_mean_return']:+.2f}%")
        print(f"  Median Return:      {mc_metrics['mc_median_return']:+.2f}%")
        print(f"  Std Deviation:      {mc_metrics['mc_std_return']:.2f}%")
        print(f"  Worst Case (5%):    {mc_metrics['mc_var_95']:+.2f}%")
        print(f"  Best Case (95%):    {mc_metrics['mc_best_case']:+.2f}%")
        print(f"  Prob of Profit:     {mc_metrics['mc_prob_profit']:.1f}%")
        print(f"  Robustness Score:   {mc_metrics['mc_robustness_score']:.1f}%")
        
        if mc_metrics['mc_robustness_score'] >= 80:
            print(f"  ✅ ROBUST: Strategy works in {mc_metrics['mc_robustness_score']:.0f}% of scenarios")
        elif mc_metrics['mc_robustness_score'] >= 50:
            print(f"  ⚠️  MARGINAL: Only {mc_metrics['mc_robustness_score']:.0f}% of scenarios profitable")
        else:
            print(f"  ❌ FRAGILE: Only {mc_metrics['mc_robustness_score']:.0f}% of scenarios profitable")
    
    @staticmethod
    def print_cost_sensitivity(cost_metrics):
        """Print transaction cost sensitivity"""
        print(f"\n💸 TRANSACTION COST SENSITIVITY:")
        print(f"  {'Cost Level':<15} {'Total Return':<15} {'Win Rate':<12} {'Profitable?'}")
        print(f"  {'-'*15} {'-'*15} {'-'*12} {'-'*12}")
        
        for cost in [0.05, 0.10, 0.20, 0.50]:
            ret = cost_metrics[f'cost_{int(cost*100):03d}_return']
            wr = cost_metrics[f'cost_{int(cost*100):03d}_wr']
            prof = "✅ Yes" if cost_metrics[f'cost_{int(cost*100):03d}_profitable'] else "❌ No"
            print(f"  {cost:.2%}           {ret:+7.2f}%        {wr:5.1f}%       {prof}")
        
        print(f"\n  Break-Even Cost:    ~{cost_metrics['cost_break_even']:.2f}%")
        print(f"  Robustness:         {cost_metrics['cost_robustness']}")
        
        if cost_metrics['cost_robustness_score'] >= 75:
            print(f"  ✅ COST ROBUST: Works at multiple cost levels")
        elif cost_metrics['cost_break_even'] >= 0.10:
            print(f"  ⚠️  COST SENSITIVE: Break-even at {cost_metrics['cost_break_even']:.2f}%")
        else:
            print(f"  ❌ COST FRAGILE: Fails even at low costs")


# Example usage
if __name__ == '__main__':
    # Example trade data
    example_trades = pd.DataFrame({
        'pnl': [2.5, -1.2, 3.8, 1.5, -0.8, 4.2, -1.5, 2.1, 0.9, -2.3, 3.5, 1.8]
    })
    
    # Calculate metrics
    analytics = BacktestAnalytics()
    metrics = analytics.calculate_metrics(example_trades, hold_days=10)
    
    # Print results
    analytics.print_metrics(metrics, "Example Strategy Performance")
    
    # Monte Carlo simulation
    print("\n" + "="*70)
    mc_metrics = analytics.monte_carlo_simulation(example_trades, n_simulations=1000, hold_days=10)
    analytics.print_monte_carlo(mc_metrics)
    
    # Transaction cost sensitivity
    print("\n" + "="*70)
    cost_metrics = analytics.transaction_cost_sensitivity(example_trades, hold_days=10)
    analytics.print_cost_sensitivity(cost_metrics)
    
    print("\n" + "="*70)
    print("\n✅ BacktestAnalytics class ready for use in all testing scripts")
    print("✅ New features: Monte Carlo simulation + Transaction cost sensitivity")
