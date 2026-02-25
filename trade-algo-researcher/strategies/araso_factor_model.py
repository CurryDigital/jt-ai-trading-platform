"""
ARASO Factor Model Implementation
Dynamic PCA with Exponential Decay + HMM Regime Detection

Phase 2: Core implementation for researcher schema
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from sqlalchemy import create_engine, text
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FactorModelConfig:
    """Configuration for dynamic factor model."""
    n_factors: int = 15
    decay_factor: float = 0.94  # RiskMetrics-style decay
    lookback_days: int = 63  # ~3 months
    min_observations: int = 30
    pca_variance_threshold: float = 0.85
    

@dataclass
class HMMConfig:
    """Configuration for HMM regime detection."""
    n_states: int = 2
    mr_state_threshold: float = 0.7
    training_window: int = 252  # 1 year
    retrain_frequency: int = 63  # Quarterly


class DatabaseConnector:
    """PostgreSQL connection manager for JT platform."""
    
    def __init__(self, host: str = "openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com",
                 database: str = "postgres",
                 username: str = None,
                 password: str = None):
        self.host = host
        self.database = database
        self.username = username
        self.password = password
        self.engine = None
        
    def connect(self):
        """Create database connection."""
        # In production, use IAM auth token rotation
        connection_string = f"postgresql://{self.username}:{self.password}@{self.host}:5432/{self.database}"
        self.engine = create_engine(connection_string)
        return self.engine
    
    def fetch_returns(self, tickers: List[str], start_date: datetime, 
                      end_date: datetime) -> pd.DataFrame:
        """Fetch returns from silver.historical_stock_data."""
        query = """
        SELECT date, ticker, returns
        FROM silver.historical_stock_data
        WHERE ticker = ANY(:tickers)
        AND date BETWEEN :start_date AND :end_date
        AND returns IS NOT NULL
        ORDER BY date, ticker
        """
        
        with self.engine.connect() as conn:
            df = pd.read_sql(text(query), conn, 
                           params={'tickers': tickers, 
                                  'start_date': start_date,
                                  'end_date': end_date})
        
        # Pivot to wide format
        returns_df = df.pivot(index='date', columns='ticker', values='returns')
        return returns_df
    
    def fetch_prices(self, tickers: List[str], start_date: datetime,
                     end_date: datetime) -> pd.DataFrame:
        """Fetch prices from silver layer."""
        query = """
        SELECT date, ticker, close
        FROM silver.historical_stock_data
        WHERE ticker = ANY(:tickers)
        AND date BETWEEN :start_date AND :end_date
        ORDER BY date, ticker
        """
        
        with self.engine.connect() as conn:
            df = pd.read_sql(text(query), conn,
                           params={'tickers': tickers,
                                  'start_date': start_date,
                                  'end_date': end_date})
        
        prices_df = df.pivot(index='date', columns='ticker', values='close')
        return prices_df
    
    def save_factor_returns(self, factor_returns: pd.DataFrame):
        """Save factor returns to researcher.factor_returns."""
        factor_returns.reset_index(inplace=True)
        factor_returns.to_sql('factor_returns', self.engine, 
                             schema='researcher', if_exists='append', 
                             index=False, method='multi')
    
    def save_factor_loadings(self, loadings_df: pd.DataFrame):
        """Save factor loadings to researcher.factor_loadings."""
        loadings_df.to_sql('factor_loadings', self.engine,
                          schema='researcher', if_exists='append',
                          index=False, method='multi')
    
    def save_residuals(self, residuals_df: pd.DataFrame):
        """Save residual returns to researcher.residual_returns."""
        residuals_df.to_sql('residual_returns', self.engine,
                           schema='researcher', if_exists='append',
                           index=False, method='multi')


class DynamicFactorModel:
    """
    Online PCA with exponential decay for factor extraction.
    RiskMetrics-style 0.94 decay factor.
    """
    
    def __init__(self, config: FactorModelConfig = None):
        self.config = config or FactorModelConfig()
        self.eigenvectors = None
        self.eigenvalues = None
        self.factor_returns = None
        self.explained_variance_ratio = None
        
    def fit(self, returns_df: pd.DataFrame, date: datetime) -> pd.DataFrame:
        """
        Fit PCA with exponential weighting.
        
        Args:
            returns_df: T x N matrix of stock returns
            date: Current date for timestamp
            
        Returns:
            factor_returns: T x k matrix of factor returns
        """
        # Clean data
        returns_clean = returns_df.dropna(axis=1, thresh=self.config.min_observations)
        returns_clean = returns_clean.fillna(0)  # Fill remaining with 0
        
        if len(returns_clean) < self.config.min_observations:
            logger.warning(f"Insufficient observations: {len(returns_clean)}")
            return None
        
        # Exponential weighting
        n_obs = len(returns_clean)
        weights = np.power(self.config.decay_factor, np.arange(n_obs))[::-1]
        weights /= weights.sum()
        
        # Weighted covariance matrix
        weighted_returns = returns_clean.values * np.sqrt(weights[:, None])
        cov_matrix = np.cov(weighted_returns, rowvar=False)
        
        # Handle NaN/Inf
        cov_matrix = np.nan_to_num(cov_matrix, nan=0, posinf=0, neginf=0)
        
        # PCA
        pca = PCA(n_components=min(self.config.n_factors, returns_clean.shape[1]))
        pca.fit(weighted_returns)
        
        # Store results
        self.eigenvectors = pca.components_.T  # N x k
        self.eigenvalues = pca.explained_variance_
        self.explained_variance_ratio = pca.explained_variance_ratio_
        
        # Calculate factor returns
        self.factor_returns = returns_clean @ self.eigenvectors
        
        # Create output dataframe
        factor_cols = [f'F{i+1}' for i in range(self.eigenvectors.shape[1])]
        factor_returns_df = pd.DataFrame(
            self.factor_returns, 
            index=returns_clean.index,
            columns=factor_cols
        )
        
        logger.info(f"PCA fitted: {len(factor_cols)} factors, "
                   f"{self.explained_variance_ratio.sum():.2%} variance explained")
        
        return factor_returns_df
    
    def get_factor_loadings(self, tickers: List[str]) -> pd.DataFrame:
        """Get factor loadings (betas) for each stock."""
        if self.eigenvectors is None:
            raise ValueError("Model not fitted yet")
        
        loadings_df = pd.DataFrame(
            self.eigenvectors,
            index=tickers[:self.eigenvectors.shape[0]],
            columns=[f'F{i+1}' for i in range(self.eigenvectors.shape[1])]
        )
        return loadings_df
    
    def calculate_residuals(self, returns_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate residual returns: ε_i(t) = R_i(t) - Σ(β_ik * F_k(t))
        """
        if self.factor_returns is None or self.eigenvectors is None:
            raise ValueError("Model not fitted yet")
        
        # Predicted returns from factor model
        predicted_returns = self.factor_returns @ self.eigenvectors.T
        
        # Residuals
        residuals = returns_df.values - predicted_returns
        
        residuals_df = pd.DataFrame(
            residuals,
            index=returns_df.index,
            columns=returns_df.columns
        )
        
        return residuals_df


class SimpleHMM:
    """
    Simplified HMM for regime detection.
    Two states: Random Walk (0) and Mean-Reverting (1)
    """
    
    def __init__(self, config: HMMConfig = None):
        self.config = config or HMMConfig()
        self.transition_matrix = np.array([[0.95, 0.05],
                                          [0.10, 0.90]])
        self.means = np.array([0, 0])
        self.variances = np.array([1, 1])
        
    def fit(self, residuals: np.ndarray) -> np.ndarray:
        """
        Fit HMM using Baum-Welch algorithm approximation.
        
        Args:
            residuals: Array of residual returns
            
        Returns:
            state_probs: P(State=1 | data) for each observation
        """
        try:
            from hmmlearn import hmm
            
            # Reshape for hmmlearn
            X = residuals.reshape(-1, 1)
            
            # Fit Gaussian HMM
            model = hmm.GaussianHMM(
                n_components=self.config.n_states,
                covariance_type="diag",
                n_iter=100,
                random_state=42
            )
            model.fit(X)
            
            # Get state probabilities
            state_probs = model.predict_proba(X)
            
            # Identify which state is mean-reverting (lower variance)
            var_0 = model.covars_[0, 0]
            var_1 = model.covars_[1, 0]
            
            if var_0 < var_1:
                mr_probs = state_probs[:, 0]  # State 0 is MR
            else:
                mr_probs = state_probs[:, 1]  # State 1 is MR
            
            self.transition_matrix = model.transmat_
            self.means = model.means_.flatten()
            self.variances = np.array([var_0, var_1])
            
            return mr_probs
            
        except ImportError:
            logger.warning("hmmlearn not installed, using simplified heuristic")
            # Fallback: Use volatility-based heuristic
            rolling_std = pd.Series(residuals).rolling(20).std()
            median_std = rolling_std.median()
            mr_probs = 1 / (1 + np.exp(-2 * (rolling_std - median_std)))
            return mr_probs.fillna(0.5).values


class ARASOFactorPipeline:
    """
    Complete pipeline for ARASO factor model.
    Connects data fetching, factor modeling, and database storage.
    """
    
    def __init__(self, db_connector: DatabaseConnector,
                 factor_config: FactorModelConfig = None,
                 hmm_config: HMMConfig = None):
        self.db = db_connector
        self.factor_model = DynamicFactorModel(factor_config)
        self.hmm = SimpleHMM(hmm_config)
        self.universe = []
        
    def load_universe(self) -> List[str]:
        """Load active universe from researcher.universe."""
        query = """
        SELECT ticker FROM researcher.universe 
        WHERE is_active = TRUE 
        ORDER BY ticker
        """
        
        with self.db.engine.connect() as conn:
            result = conn.execute(text(query))
            self.universe = [row[0] for row in result]
        
        logger.info(f"Loaded {len(self.universe)} tickers from universe")
        return self.universe
    
    def run_factor_model(self, current_date: datetime, 
                         lookback_days: int = 126) -> Dict:
        """
        Run complete factor model for a given date.
        
        Args:
            current_date: Date to compute factors for
            lookback_days: Days of history to use
            
        Returns:
            results: Dict with factor_returns, loadings, residuals
        """
        start_date = current_date - timedelta(days=lookback_days)
        
        # 1. Fetch returns
        logger.info(f"Fetching returns for {len(self.universe)} tickers...")
        returns_df = self.db.fetch_returns(self.universe, start_date, current_date)
        
        if returns_df.empty:
            logger.error("No returns data fetched")
            return None
        
        # 2. Fit factor model
        logger.info("Fitting dynamic PCA...")
        factor_returns = self.factor_model.fit(returns_df, current_date)
        
        if factor_returns is None:
            logger.error("Factor model fitting failed")
            return None
        
        # 3. Calculate residuals
        logger.info("Calculating residual returns...")
        residuals_df = self.factor_model.calculate_residuals(returns_df)
        
        # 4. Get factor loadings
        loadings = self.factor_model.get_factor_loadings(returns_df.columns.tolist())
        
        # 5. Standardize residuals (z-scores)
        residual_zscores = self._calculate_zscores(residuals_df)
        
        results = {
            'date': current_date,
            'factor_returns': factor_returns,
            'loadings': loadings,
            'residuals': residuals_df,
            'residual_zscores': residual_zscores,
            'explained_variance': self.factor_model.explained_variance_ratio.sum()
        }
        
        return results
    
    def _calculate_zscores(self, residuals_df: pd.DataFrame, 
                          window: int = 20) -> pd.DataFrame:
        """Calculate rolling z-scores of residuals."""
        zscores = pd.DataFrame(index=residuals_df.index, columns=residuals_df.columns)
        
        for col in residuals_df.columns:
            rolling_mean = residuals_df[col].rolling(window=window, min_periods=10).mean()
            rolling_std = residuals_df[col].rolling(window=window, min_periods=10).std()
            zscores[col] = (residuals_df[col] - rolling_mean) / (rolling_std + 1e-6)
        
        return zscores
    
    def run_hmm_for_universe(self, residuals_df: pd.DataFrame,
                             current_date: datetime) -> pd.DataFrame:
        """
        Run HMM regime detection for all stocks in universe.
        """
        hmm_results = []
        
        for ticker in residuals_df.columns:
            residuals = residuals_df[ticker].dropna()
            
            if len(residuals) < 30:
                continue
            
            # Fit HMM
            mr_probs = self.hmm.fit(residuals.values)
            
            hmm_results.append({
                'date': current_date,
                'ticker': ticker,
                'p_random_walk': 1 - mr_probs[-1],
                'p_mean_reverting': mr_probs[-1],
                'current_state': 1 if mr_probs[-1] > 0.5 else 0,
                'residual_volatility': residuals.std()
            })
        
        hmm_df = pd.DataFrame(hmm_results)
        return hmm_df
    
    def save_results(self, factor_results: Dict, hmm_df: pd.DataFrame):
        """Save all results to database."""
        date = factor_results['date']
        
        # 1. Save factor returns
        factor_returns = factor_results['factor_returns']
        factor_returns_long = factor_returns.reset_index().melt(
            id_vars='date', var_name='factor_id', value_name='return'
        )
        factor_returns_long['factor_id'] = factor_returns_long['factor_id'].str.replace('F', '').astype(int)
        
        # Add eigenvalues
        for i, (ev, evr) in enumerate(zip(
            self.factor_model.eigenvalues,
            self.factor_model.explained_variance_ratio
        )):
            mask = factor_returns_long['factor_id'] == (i + 1)
            factor_returns_long.loc[mask, 'eigenvalue'] = ev
            factor_returns_long.loc[mask, 'cumulative_variance_explained'] = evr
        
        self.db.save_factor_returns(factor_returns_long)
        
        # 2. Save factor loadings
        loadings = factor_results['loadings']
        loadings_long = loadings.reset_index().melt(
            id_vars='index', var_name='factor_id', value_name='beta'
        )
        loadings_long.columns = ['ticker', 'factor_id', 'beta']
        loadings_long['date'] = date
        loadings_long['factor_id'] = loadings_long['factor_id'].str.replace('F', '').astype(int)
        loadings_long['decay_factor'] = self.factor_model.config.decay_factor
        
        self.db.save_factor_loadings(loadings_long)
        
        # 3. Save residuals
        residuals = factor_results['residuals']
        zscores = factor_results['residual_zscores']
        
        residuals_long = residuals.reset_index().melt(
            id_vars='date', var_name='ticker', value_name='residual'
        )
        residuals_long['actual_return'] = residuals_long['residual']  # Simplified
        residuals_long['predicted_return'] = 0.0
        
        # Add z-scores
        zscores_long = zscores.reset_index().melt(
            id_vars='date', var_name='ticker', value_name='residual_zscore'
        )
        residuals_long = residuals_long.merge(
            zscores_long, on=['date', 'ticker'], how='left'
        )
        
        residuals_long['n_factors_used'] = self.factor_model.config.n_factors
        
        self.db.save_residuals(residuals_long)
        
        logger.info(f"Saved results for {date}: "
                   f"{len(factor_returns_long)} factor returns, "
                   f"{len(loadings_long)} loadings, "
                   f"{len(residuals_long)} residuals")


def main():
    """
    Example usage of ARASO factor model pipeline.
    """
    # Initialize components
    db = DatabaseConnector(
        username="your_username",  # Replace with actual credentials
        password="your_password"
    )
    db.connect()
    
    # Create pipeline
    pipeline = ARASOFactorPipeline(db)
    
    # Load universe
    universe = pipeline.load_universe()
    
    # Run for specific date
    test_date = datetime(2024, 12, 31)
    
    results = pipeline.run_factor_model(test_date)
    
    if results:
        # Run HMM
        hmm_df = pipeline.run_hmm_for_universe(
            results['residuals'], 
            test_date
        )
        
        # Save to database
        pipeline.save_results(results, hmm_df)
        
        print(f"\nFactor Model Results for {test_date.date()}")
        print(f"Variance explained: {results['explained_variance']:.2%}")
        print(f"\nTop 5 residuals (z-score):")
        latest_z = results['residual_zscores'].iloc[-1].abs().nlargest(5)
        for ticker, zscore in latest_z.items():
            print(f"  {ticker}: {zscore:.2f}")


if __name__ == '__main__':
    main()
