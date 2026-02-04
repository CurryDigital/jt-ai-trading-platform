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
            self.logger.info(f"Processing {ticker}...")
            
            # 1. Run Time Series Analysis
            ts_signal = self._get_time_series_signal(ticker)
            
            # 2. Run Sentiment Analysis
            sent_signal = self._get_sentiment_signal(ticker)
            
            # 3. Run Alpha Metrics
            alpha_signal = self._get_alpha_signal(ticker)
            
            # 4. Aggregate
            final_score = (
                ts_signal * self.config['weights']['time_series'] +
                sent_signal * self.config['weights']['sentiment'] +
                alpha_signal * self.config['weights']['alpha']
            )
            
            results.append({
                'ticker': ticker,
                'ts_signal': ts_signal,
                'sent_signal': sent_signal,
                'alpha_signal': alpha_signal,
                'final_score': final_score
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
