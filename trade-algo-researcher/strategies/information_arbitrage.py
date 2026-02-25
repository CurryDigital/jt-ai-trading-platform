#!/usr/bin/env python3
"""
Information Arbitrage Analysis Module
Analyzes information decay, disruption mapping, and network effects
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DisruptionVulnerabilityScore:
    """DVS calculation for a company."""
    ticker: str
    company_name: str
    human_labor_moat: int  # 0-10
    ai_replacement_probability: int  # 0-10
    customer_concentration: int  # 0-10
    response_slowness: int  # 0-10
    
    @property
    def dvs(self) -> int:
        """Calculate DVS."""
        return (self.human_labor_moat * 
                self.ai_replacement_probability * 
                self.customer_concentration * 
                self.response_slowness)
    
    @property
    def risk_level(self) -> str:
        """Interpret DVS."""
        if self.dvs >= 4000:
            return "EXTREME"
        elif self.dvs >= 2000:
            return "HIGH"
        elif self.dvs >= 1000:
            return "MODERATE"
        elif self.dvs >= 500:
            return "LOW"
        else:
            return "MINIMAL"
    
    def to_dict(self) -> Dict:
        return {
            'ticker': self.ticker,
            'company': self.company_name,
            'hl_moat': self.human_labor_moat,
            'ai_prob': self.ai_replacement_probability,
            'cust_conc': self.customer_concentration,
            'response': self.response_slowness,
            'dvs': self.dvs,
            'risk_level': self.risk_level
        }


class InformationDecayAnalyzer:
    """
    Analyze information decay τ (tau) metrics.
    """
    
    def calculate_tau(self, 
                     primary_prices: pd.Series,
                     secondary_prices: pd.Series,
                     event_time: datetime,
                     max_lag: int = 20) -> Dict:
        """
        Calculate information decay lag between primary and secondary assets.
        
        Args:
            primary_prices: Price series of directly affected asset
            secondary_prices: Price series of peer/supplier asset
            event_time: When news broke
            max_lag: Maximum days to check
            
        Returns:
            Dictionary with tau metrics
        """
        # Calculate returns
        primary_returns = primary_prices.pct_change().dropna()
        secondary_returns = secondary_prices.pct_change().dropna()
        
        # Align series
        aligned = pd.concat([primary_returns, secondary_returns], axis=1).dropna()
        aligned.columns = ['primary', 'secondary']
        
        # Find correlation at different lags
        correlations = []
        for lag in range(max_lag + 1):
            if lag == 0:
                corr = aligned['primary'].corr(aligned['secondary'])
            else:
                corr = aligned['primary'].corr(aligned['secondary'].shift(lag))
            correlations.append(corr)
        
        # Find optimal lag (peak correlation)
        optimal_lag = np.argmax(correlations)
        tau = optimal_lag
        
        return {
            'tau_days': tau,
            'optimal_lag': optimal_lag,
            'correlation_at_lag': correlations[optimal_lag],
            'all_correlations': correlations,
            'interpretation': self._interpret_tau(tau)
        }
    
    def _interpret_tau(self, tau: int) -> str:
        """Interpret tau value."""
        if tau <= 1:
            return "Very fast (HFT territory, skip)"
        elif tau <= 3:
            return "Fast (secondary wave, limited alpha)"
        elif tau <= 7:
            return "Medium (secondary wave, good alpha)"
        elif tau <= 21:
            return "Slow (tertiary wave, excellent alpha)"
        else:
            return "Very slow (quaternary wave, speculative)"


class NetworkEffectMapper:
    """
    Map network effects for geopolitical/industry events.
    """
    
    def __init__(self):
        self.networks = {}
    
    def map_panama_network(self) -> Dict:
        """
        Map CK Hutchison/Panama port dispute network effects.
        """
        return {
            'event': 'CK Hutchison Panama Port Exit',
            'primary': {
                'CK Hutchison': {'tickers': ['CKH', '0001.HK'], 'impact': 'direct'}
            },
            'secondary': {
                'Maersk/APM': {'tickers': ['MAERSK-B.CO'], 'impact': 'beneficiary'},
                'COSCO': {'tickers': ['COSCO', '1919.HK'], 'impact': 'beneficiary'},
                'Panama Local': {'tickers': ['local_operators'], 'impact': 'beneficiary'}
            },
            'tertiary': {
                'Container Lines': {'tickers': ['ZIM', 'DAC', 'GSL'], 'impact': 'rate_volatility'},
                'US Gulf Exporters': {'tickers': ['agriculture', 'energy'], 'impact': 'route_change'}
            },
            'quaternary': {
                'Regional Trade': {'impact': 'volume_shift'},
                'Panama GDP': {'impact': 'negative'}
            }
        }
    
    def map_gpu_supply_chain(self) -> Dict:
        """
        Map GPU demand surge network effects.
        """
        return {
            'event': 'AI GPU Demand Surge',
            'primary': {
                'NVIDIA': {'tickers': ['NVDA'], 'impact': 'direct'}
            },
            'secondary': {
                'TSMC': {'tickers': ['TSM'], 'impact': 'fabrication'},
                'SK Hynix': {'tickers': ['000660.KS'], 'impact': 'memory'},
                'Amkor': {'tickers': ['AMKR'], 'impact': 'packaging'}
            },
            'tertiary': {
                'ASML': {'tickers': ['ASML'], 'impact': 'lithography'},
                'Applied Materials': {'tickers': ['AMAT'], 'impact': 'equipment'},
                'Lam Research': {'tickers': ['LRCX'], 'impact': 'etch'},
                'Vertiv': {'tickers': ['VRT'], 'impact': 'cooling'},
                'Fabrinet': {'tickers': ['FN'], 'impact': 'optical'}
            },
            'quaternary': {
                'MP Materials': {'tickers': ['MP'], 'impact': 'rare_earths'},
                'Power Grid': {'impact': 'electricity_demand'}
            }
        }


class PredictiveEdgeScorer:
    """
    Score predictive edge from leading indicators.
    """
    
    def score_job_postings(self, postings: List[Dict]) -> Dict:
        """
        Score job postings as leading indicators.
        
        Args:
            postings: List of job posting dicts with 'title', 'company', 'date'
            
        Returns:
            Score and interpretation
        """
        scores = []
        
        for posting in postings:
            score = 0
            title = posting.get('title', '').lower()
            
            # Role seniority
            if 'principal' in title or 'director' in title or 'head of' in title:
                score += 3
            elif 'senior' in title:
                score += 2
            elif 'lead' in title:
                score += 1
            
            # Specificity
            if any(x in title for x in ['generative', 'genai', 'llm', 'foundation model']):
                score += 3
            elif any(x in title for x in ['ai', 'machine learning', 'deep learning']):
                score += 2
            
            # Domain relevance
            if any(x in title for x in ['video', 'image', 'vision', 'creative']):
                score += 2
            
            scores.append(score)
        
        avg_score = np.mean(scores) if scores else 0
        
        return {
            'avg_score': avg_score,
            'num_postings': len(postings),
            'interpretation': self._interpret_job_score(avg_score),
            'predictive_timeline': '6-12 months' if avg_score > 5 else '12-18 months'
        }
    
    def _interpret_job_score(self, score: float) -> str:
        if score >= 7:
            return "Strong signal — likely major product launch in 6-12 months"
        elif score >= 5:
            return "Moderate signal — AI integration likely in 12-18 months"
        elif score >= 3:
            return "Weak signal — exploratory phase"
        else:
            return "No signal — generic hiring"


def main():
    """Example usage."""
    
    # DVS Calculation
    adobe = DisruptionVulnerabilityScore(
        ticker='ADBE',
        company_name='Adobe',
        human_labor_moat=9,
        ai_replacement_probability=9,
        customer_concentration=7,
        response_slowness=6
    )
    
    print(f"Adobe DVS: {adobe.dvs} ({adobe.risk_level})")
    
    atlassian = DisruptionVulnerabilityScore(
        ticker='TEAM',
        company_name='Atlassian',
        human_labor_moat=7,
        ai_replacement_probability=6,
        customer_concentration=6,
        response_slowness=4
    )
    
    print(f"Atlassian DVS: {atlassian.dvs} ({atlassian.risk_level})")
    
    # Information decay analysis placeholder
    analyzer = InformationDecayAnalyzer()
    print("\nInformation Decay Analysis:")
    print("- Use calculate_tau() with price series to measure lag")
    
    # Network mapping
    mapper = NetworkEffectMapper()
    gpu_network = mapper.map_gpu_supply_chain()
    print("\nGPU Supply Chain Network:")
    for tier, nodes in gpu_network.items():
        if tier != 'event':
            print(f"  {tier}: {list(nodes.keys())}")


if __name__ == '__main__':
    main()
