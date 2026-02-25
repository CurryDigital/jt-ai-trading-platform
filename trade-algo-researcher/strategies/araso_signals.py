"""
ARASO Signal Generation Module
Generates trading signals from factor model residuals + HMM states + sentiment overlay
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SignalType(Enum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"
    HOLD = "HOLD"


class Direction(Enum):
    SHORT = -1
    FLAT = 0
    LONG = 1


@dataclass
class ARASOConfig:
    """ARASO strategy configuration."""
    # Entry/Exit thresholds
    entry_threshold: float = 1.5  # Z-score
    exit_threshold: float = 0.3   # Z-score
    hmm_threshold: float = 0.7    # P(mean_reverting)
    
    # Position sizing
    kelly_fraction: float = 0.25
    max_risk_per_trade: float = 0.02  # 2%
    size_per_z: float = 10000  # $ per z-score unit
    
    # Risk limits
    max_hold_days: int = 20
    stop_loss_z: float = 3.0
    max_position_pct: float = 0.05  # 5% of portfolio
    
    # Portfolio constraints
    beta_neutral: bool = True
    sector_neutral: bool = True
    dollar_neutral: bool = True
    max_sector_exposure: float = 0.15


@dataclass
class MacroRegime:
    """Macro regime classification."""
    date: datetime
    vix: float
    yield_spread: float
    cpi_surprise: float
    classification: str  # expansion, contraction, high_uncertainty, recovery
    position_scale: float = 1.0
    trading_enabled: bool = True


class MacroRegimeFilter:
    """
    Classify macro regime and adjust position sizing.
    """
    
    def classify_regime(self, vix: float, yield_spread: float, 
                       cpi_surprise: float = 0) -> MacroRegime:
        """
        Classify macro regime based on key indicators.
        """
        date = datetime.now()
        
        # High uncertainty regime
        if vix > 30:
            if yield_spread < 0:
                return MacroRegime(
                    date=date, vix=vix, yield_spread=yield_spread,
                    cpi_surprise=cpi_surprise,
                    classification='high_uncertainty',
                    position_scale=0.3,
                    trading_enabled=True
                )
            return MacroRegime(
                date=date, vix=vix, yield_spread=yield_spread,
                cpi_surprise=cpi_surprise,
                classification='contraction',
                position_scale=0.5,
                trading_enabled=True
            )
        
        # Contraction warning
        if yield_spread < -0.5 and vix > 25:
            return MacroRegime(
                date=date, vix=vix, yield_spread=yield_spread,
                cpi_surprise=cpi_surprise,
                classification='contraction',
                position_scale=0.5,
                trading_enabled=True
            )
        
        # Expansion
        if vix < 20 and yield_spread > 0.5:
            return MacroRegime(
                date=date, vix=vix, yield_spread=yield_spread,
                cpi_surprise=cpi_surprise,
                classification='expansion',
                position_scale=1.0,
                trading_enabled=True
            )
        
        # Recovery / Normal
        return MacroRegime(
            date=date, vix=vix, yield_spread=yield_spread,
            cpi_surprise=cpi_surprise,
            classification='recovery',
            position_scale=0.8,
            trading_enabled=True
        )


class SentimentOverlay:
    """
    News sentiment filter for ARASO signals.
    Placeholder implementation - integrate with RavenPack/Benzinga.
    """
    
    def __init__(self, sentiment_data: Optional[pd.DataFrame] = None):
        self.sentiment_data = sentiment_data or pd.DataFrame()
        self.history = {}
    
    def get_sentiment_zscore(self, ticker: str, date: datetime,
                            lookback: int = 5) -> Dict:
        """
        Get sentiment z-score for a ticker.
        
        Returns:
            {'z_score': float, 'direction': int, 'confidence': float}
        """
        # Placeholder - in production, query RavenPack/Benzinga
        # For now, return neutral sentiment
        return {
            'z_score': 0.0,
            'direction': 0,
            'confidence': 0.0,
            'has_data': False
        }
    
    def adjust_entry(self, residual_z: float, 
                    sentiment: Dict) -> Tuple[float, bool]:
        """
        Adjust entry threshold based on sentiment.
        
        Returns:
            (adjusted_z, should_trade)
        """
        if not sentiment['has_data']:
            return residual_z, True
        
        sentiment_z = sentiment['z_score']
        
        # Strong sentiment in same direction as residual signal
        # → Mean-reversion less likely (skip trade)
        if np.sign(residual_z) == np.sign(sentiment_z) and abs(sentiment_z) > 1.5:
            logger.info(f"Skipping trade: strong sentiment ({sentiment_z:.2f}) "
                       f"aligns with residual ({residual_z:.2f})")
            return residual_z, False
        
        # Strong sentiment against residual signal
        # → Accelerates mean-reversion (enter early)
        if np.sign(residual_z) != np.sign(sentiment_z) and abs(sentiment_z) > 1.0:
            return residual_z * 0.7, True
        
        return residual_z, True


class LeadLagAnalyzer:
    """
    Analyze sector ETF → individual stock lead-lag relationships.
    """
    
    SECTOR_ETFS = {
        'Technology': 'XLK',
        'Financials': 'XLF',
        'Healthcare': 'XLV',
        'Energy': 'XLE',
        'Industrials': 'XLI',
        'Consumer Discretionary': 'XLY',
        'Consumer Staples': 'XLP',
        'Utilities': 'XLU',
        'Materials': 'XLB',
        'Real Estate': 'XLRE',
        'Communication Services': 'XLC'
    }
    
    def __init__(self):
        self.lead_lag_params = {}  # ticker -> optimal lag
    
    def compute_lead_lag(self, stock_returns: pd.Series,
                        sector_returns: pd.Series,
                        max_lag: int = 5) -> Dict:
        """
        Compute optimal lead-lag between sector ETF and stock.
        """
        correlations = []
        
        for lag in range(max_lag + 1):
            if lag == 0:
                corr = stock_returns.corr(sector_returns)
            else:
                corr = stock_returns.corr(sector_returns.shift(lag))
            correlations.append(corr)
        
        optimal_lag = np.argmax(np.abs(correlations))
        
        return {
            'optimal_lag': optimal_lag,
            'correlation': correlations[optimal_lag],
            'direction': np.sign(correlations[optimal_lag])
        }
    
    def should_delay_entry(self, ticker: str, sector_signal: Dict) -> Dict:
        """
        Determine if entry should be delayed based on sector lead.
        """
        if ticker not in self.lead_lag_params:
            return {'delay_bars': 0, 'confidence': 0}
        
        params = self.lead_lag_params[ticker]
        
        if params['correlation'] > 0.5 and params['optimal_lag'] > 0:
            return {
                'delay_bars': params['optimal_lag'],
                'confidence': params['correlation']
            }
        
        return {'delay_bars': 0, 'confidence': 0}


class ARASOSignalGenerator:
    """
    Generate ARASO trading signals from factor model outputs.
    """
    
    def __init__(self, config: ARASOConfig = None):
        self.config = config or ARASOConfig()
        self.macro_filter = MacroRegimeFilter()
        self.sentiment = SentimentOverlay()
        self.lead_lag = LeadLagAnalyzer()
        self.positions = {}  # Track current positions
    
    def generate_signals(self, date: datetime,
                        residuals_df: pd.DataFrame,
                        hmm_df: pd.DataFrame,
                        macro_regime: MacroRegime,
                        universe_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals for all stocks in universe.
        
        Args:
            date: Current date
            residuals_df: DataFrame with residual and zscore columns
            hmm_df: DataFrame with HMM state probabilities
            macro_regime: Current macro regime
            universe_df: Universe with sector info
            
        Returns:
            signals_df: DataFrame with all signals
        """
        signals = []
        
        # Get latest data
        latest_residuals = residuals_df.loc[residuals_df.index == residuals_df.index[-1]]
        
        for ticker in latest_residuals.columns:
            if ticker == 'residual_zscore':
                continue
            
            # Get residual z-score
            residual_z = latest_residuals[ticker].values[0] if ticker in latest_residuals.columns else 0
            
            # Get HMM probability
            hmm_row = hmm_df[hmm_df['ticker'] == ticker]
            if hmm_row.empty:
                continue
            
            p_mr = hmm_row['p_mean_reverting'].values[0]
            
            # Skip if not in mean-reverting regime
            if p_mr < self.config.hmm_threshold:
                continue
            
            # Get sentiment overlay
            sentiment = self.sentiment.get_sentiment_zscore(ticker, date)
            adjusted_z, should_trade = self.sentiment.adjust_entry(residual_z, sentiment)
            
            if not should_trade:
                continue
            
            # Check lead-lag
            sector_info = universe_df[universe_df['ticker'] == ticker]
            if not sector_info.empty:
                sector = sector_info['sector'].values[0]
                # Would check sector signal here in full implementation
            
            # Generate signal
            if abs(adjusted_z) > self.config.entry_threshold:
                direction = Direction.SHORT if adjusted_z > 0 else Direction.LONG
                
                # Calculate position size
                base_size = abs(adjusted_z) * self.config.size_per_z
                regime_scale = macro_regime.position_scale
                position_value = base_size * regime_scale
                
                # Confidence score
                confidence = p_mr * (abs(adjusted_z) / self.config.entry_threshold)
                
                signals.append({
                    'date': date,
                    'ticker': ticker,
                    'signal_type': SignalType.ENTRY.value,
                    'direction': direction.value,
                    'residual_zscore': residual_z,
                    'hmm_mr_probability': p_mr,
                    'sentiment_zscore': sentiment['z_score'],
                    'macro_regime': macro_regime.classification,
                    'position_scale': regime_scale,
                    'target_position_value': position_value,
                    'confidence_score': confidence,
                    'reason': f"Residual z={residual_z:.2f}, HMM={p_mr:.2f}"
                })
        
        signals_df = pd.DataFrame(signals)
        return signals_df
    
    def check_exits(self, date: datetime,
                   positions: Dict,
                   residuals_df: pd.DataFrame,
                   hmm_df: pd.DataFrame) -> pd.DataFrame:
        """
        Check existing positions for exit conditions.
        """
        exits = []
        
        for ticker, position in positions.items():
            # Get current residual z-score
            if ticker not in residuals_df.columns:
                continue
            
            current_z = residuals_df[ticker].iloc[-1]
            entry_z = position['entry_zscore']
            
            # Get current HMM state
            hmm_row = hmm_df[hmm_df['ticker'] == ticker]
            if hmm_row.empty:
                continue
            
            p_mr = hmm_row['p_mean_reverting'].values[0]
            
            exit_signal = False
            exit_reason = ""
            
            # 1. Mean reversion completed
            if abs(current_z) < self.config.exit_threshold:
                exit_signal = True
                exit_reason = 'mean_reversion_complete'
            
            # 2. HMM regime change
            elif p_mr < 0.3:
                exit_signal = True
                exit_reason = 'regime_change'
            
            # 3. Stop loss (3σ move against position)
            elif abs(current_z) > self.config.stop_loss_zscore:
                if np.sign(current_z) == np.sign(position['direction']):
                    exit_signal = True
                    exit_reason = 'stop_loss'
            
            # 4. Maximum hold time
            hold_days = (date - position['entry_date']).days
            if hold_days > self.config.max_hold_days:
                exit_signal = True
                exit_reason = 'max_hold_time'
            
            if exit_signal:
                exits.append({
                    'date': date,
                    'ticker': ticker,
                    'signal_type': SignalType.EXIT.value,
                    'direction': Direction.FLAT.value,
                    'residual_zscore': current_z,
                    'hmm_mr_probability': p_mr,
                    'exit_reason': exit_reason,
                    'hold_days': hold_days
                })
        
        exits_df = pd.DataFrame(exits)
        return exits_df


def main():
    """Example signal generation."""
    from araso_factor_model import DatabaseConnector
    
    # Initialize
    db = DatabaseConnector()
    db.connect()
    
    generator = ARASOSignalGenerator()
    
    # Get current macro regime
    macro = generator.macro_filter.classify_regime(
        vix=18.5,
        yield_spread=0.8,
        cpi_surprise=0.1
    )
    
    print(f"Macro Regime: {macro.classification}")
    print(f"Position Scale: {macro.position_scale}")
    print(f"Trading Enabled: {macro.trading_enabled}")


if __name__ == '__main__':
    main()
