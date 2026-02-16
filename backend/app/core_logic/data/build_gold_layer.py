import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np

def build_gold_layer(tickers, benchmark="^HSI"):
    # 1. Fetch Benchmark Data
    print(f"Fetching benchmark {benchmark}...")
    bench_df = yf.Ticker(benchmark).history(period="1y")['Close']
    bench_returns = bench_df.pct_change()

    all_data = []
    for ticker in tickers:
        print(f"Processing Gold Features for {ticker}...")
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        if df.empty or len(df) < 50: continue

        # --- A. Institutional/Volume Features ---
        # MFI (Money Flow Index) - Measures institutional "buy/sell" pressure
        df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)
        # VWAP (Volume Weighted Average Price)
        df['VWAP'] = ta.vwap(df['High'], df['Low'], df['Close'], df['Volume'])
        
        # --- B. Relative Strength Features ---
        df['Returns'] = df['Close'].pct_change()
        # Beta calculation (Covariance with Market / Variance of Market)
        rolling_cov = df['Returns'].rolling(window=30).cov(bench_returns)
        rolling_var = bench_returns.rolling(window=30).var()
        df['Beta_30d'] = rolling_cov / rolling_var
        # Relative Strength (Stock Return - Benchmark Return)
        df['Relative_Strength_30d'] = df['Returns'].rolling(30).sum() - bench_returns.rolling(30).sum()

        # --- C. Risk & Efficiency Features ---
        # Sharpe Ratio (Annualized)
        df['Sharpe_Ratio'] = (df['Returns'].rolling(30).mean() / df['Returns'].rolling(30).std()) * np.sqrt(252)
        # Volatility (ATR normalized by Price)
        df['Vol_Pct'] = (ta.atr(df['High'], df['Low'], df['Close'], length=14) / df['Close']) * 100

        # --- D. Contradiction Detection Signal ---
        # Momentum of Price vs Momentum of MFI
        df['Price_Mom'] = ta.mom(df['Close'], length=10)
        df['MFI_Mom'] = ta.mom(df['MFI'], length=10)
        # If Price is going up but MFI is going down -> Potential Bearish Divergence
        df['Divergence_Signal'] = np.where((df['Price_Mom'] > 0) & (df['MFI_Mom'] < 0), "Bearish_Div", 
                                  np.where((df['Price_Mom'] < 0) & (df['MFI_Mom'] > 0), "Bullish_Div", "Neutral"))

        # Add metadata and cleanup
        df['Ticker'] = ticker
        all_data.append(df.tail(1)) # We want the latest Gold state

    return pd.concat(all_data)

if __name__ == "__main__":
    universe = [
        "0700.HK", "9988.HK", "3690.HK", "1211.HK", "2318.HK",
        "9868.HK", "2015.HK", "1024.HK", "6618.HK", "2688.HK",
        "2269.HK", "0981.HK", "3968.HK", "2333.HK", "0968.HK"
    ]
    
    gold_df = build_gold_layer(universe)
    gold_df.to_csv("gold_stock_features.csv", index=False)
    print("\n--- GOLD LAYER BUILT ---")
    print(gold_df[['Ticker', 'MFI', 'Relative_Strength_30d', 'Sharpe_Ratio', 'Divergence_Signal']].to_string())
