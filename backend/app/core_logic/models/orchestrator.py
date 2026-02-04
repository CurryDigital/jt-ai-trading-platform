import pandas as pd
import importlib
import logging

class ModelOrchestrator:
    """
    Orchestrates the execution of different analysis modules:
    - Time Series (Prophet)
    - Sentiment (LLM-based)
    - Alpha Metrics (Traditional)
    """
    
    def __init__(self, config=None):
        self.config = config or {
            'weights': {
                'time_series': 0.4,
                'sentiment': 0.3,
                'alpha': 0.3
            }
        }
        self.logger = logging.getLogger(__name__)

    def run_full_pipeline(self, tickers):
        results = []
        for ticker in tickers:
            scores = {
                'ts': self._get_time_series_signal(ticker),
                'sent': self._get_sentiment_signal(ticker),
                'alpha': self._get_alpha_signal(ticker),
                'macro': 0.5 # Placeholder for macro logic
            }
            
            # Calculate Discord (Standard Deviation of scores)
            import numpy as np
            discord = np.std(list(scores.values()))
            
            final_score = (
                scores['ts'] * self.config['weights']['time_series'] +
                scores['sent'] * self.config['weights']['sentiment'] +
                scores['alpha'] * self.config['weights']['alpha']
            )
            
            results.append({
                'ticker': ticker,
                'ts_signal': scores['ts'],
                'sent_signal': scores['sent'],
                'alpha_signal': scores['alpha'],
                'final_score': final_score,
                'discord_index': float(discord)
            })
        return pd.DataFrame(results)

    def _get_time_series_signal(self, ticker):
        from app.core_logic.analysis.time_series.prophet_forecast import run_analysis
        return run_analysis(ticker)

    def _get_sentiment_signal(self, ticker):
        from app.core_logic.analysis.sentiment.analyze_sentiment import run_analysis
        return run_analysis(ticker)

    def _get_alpha_signal(self, ticker):
        from app.core_logic.analysis.alpha_metrics.enhance_alpha import run_analysis
        return run_analysis(ticker)

if __name__ == "__main__":
    orchestrator = ModelOrchestrator()
    sample_tickers = ["AAPL", "NVDA", "TSLA"]
    signals = orchestrator.run_full_pipeline(sample_tickers)
    print(signals)
