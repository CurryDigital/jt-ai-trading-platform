import pandas as pd
from src.models.orchestrator import ModelOrchestrator
from src.backtesting.backtester import Backtester
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def main():
    data_path = "data/processed/hk_stocks_features.csv"
    try:
        df = pd.read_csv(data_path)
        # Normalize column names to lowercase for consistency
        df.columns = [c.lower() for c in df.columns]
        tickers = df['ticker'].unique()[:5] if 'ticker' in df.columns else []
        if len(tickers) == 0:
            logging.error("No tickers found in data.")
            return
        logging.info(f"Loaded data for {len(tickers)} tickers.")
    except Exception as e:
        logging.error(f"Failed to load data: {e}")
        return

    # Generate consolidated signals
    orchestrator = ModelOrchestrator()
    signals = orchestrator.run_full_pipeline(tickers)
    
    print("\n--- Generated Signals ---")
    print(signals[['ticker', 'ts_signal', 'sent_signal', 'alpha_signal', 'final_score']])

    # Run Backtest
    # For this integration test, we use the 'close' from our feature set
    price_df = df[df['ticker'].isin(tickers)][['ticker', 'close']].copy()
    
    bt = Backtester()
    results, metrics = bt.run(signals, price_df)
    
    print("\n--- Backtest Metrics ---")
    for key, value in metrics.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()
