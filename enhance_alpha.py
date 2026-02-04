import yfinance as yf
import pandas as pd
import pandas_ta as ta

def get_enhanced_data(tickers):
    all_data = []
    for ticker in tickers:
        print(f"Processing {ticker}...")
        df = yf.Ticker(ticker).history(period="1y")
        if df.empty: continue
        
        df['Ticker'] = ticker
        # Core Indicators
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        
        # Accuracy Boosters:
        # 1. Momentum: Rate of Change (10 day)
        df['ROC'] = ta.roc(df['Close'], length=10)
        # 2. Volatility: ATR (Average True Range)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        # 3. Efficiency: ROC / ATR (Risk-adjusted momentum)
        df['Efficiency_Score'] = df['ROC'] / df['ATR']
        
        all_data.append(df.tail(1))
        
    return pd.concat(all_data)

if __name__ == "__main__":
    # Expanded Universe: High Growth / Mid-to-Large Cap Alpha
    universe = [
        "0700.HK", "9988.HK", "3690.HK", "1211.HK", "2318.HK",
        "9868.HK", "2015.HK", "1024.HK", "6618.HK", "2688.HK",
        "2269.HK", "0981.HK", "3968.HK", "2333.HK", "0968.HK"
    ]
    
    df = get_enhanced_data(universe)
    df.to_csv("enhanced_alpha_universe.csv", index=False)
    print("Universe processed with Efficiency Scores.")
