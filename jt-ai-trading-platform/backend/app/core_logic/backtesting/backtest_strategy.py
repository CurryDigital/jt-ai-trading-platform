import pandas as pd
import numpy as np
import pandas_ta as ta
import yfinance as yf

def run_backtest(ticker, period="2y"):
    # 1. Fetch Data
    df = yf.Ticker(ticker).history(period=period)
    if df.empty: return None

    # 2. Calculate Technicals
    df['SMA_50'] = ta.sma(df['Close'], length=50)
    df['SMA_200'] = ta.sma(df['Close'], length=200)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    # 3. Define Strategy Logic (The Logic Enrichment)
    # We want Price > SMA50 (Trend) AND RSI < 65 (Not overbought)
    df['Signal'] = 0
    df.loc[(df['Close'] > df['SMA_50']) & (df['RSI'] < 65), 'Signal'] = 1
    
    # 4. Calculate Returns
    df['Log_Returns'] = np.log(df['Close'] / df['Close'].shift(1))
    df['Strategy_Returns'] = df['Log_Returns'] * df['Signal'].shift(1)
    
    # 5. Performance Metrics
    win_rate = len(df[df['Strategy_Returns'] > 0]) / len(df[df['Strategy_Returns'] != 0]) if len(df[df['Strategy_Returns'] != 0]) > 0 else 0
    cum_return = np.exp(df['Strategy_Returns'].sum()) - 1
    
    return {
        "Ticker": ticker,
        "Win_Rate": round(win_rate * 100, 2),
        "Total_Return": round(cum_return * 100, 2),
        "Sharpe": round(df['Strategy_Returns'].mean() / df['Strategy_Returns'].std() * np.sqrt(252), 2) if df['Strategy_Returns'].std() != 0 else 0
    }

if __name__ == "__main__":
    tickers = ["0700.HK", "9988.HK", "3690.HK", "1211.HK", "2318.HK"]
    results = []
    
    print("--- Backtesting Strategy: Trend + RSI Filter ---")
    for t in tickers:
        res = run_backtest(t)
        if res:
            results.append(res)
            print(f"{t}: Return {res['Total_Return']}% | Win Rate {res['Win_Rate']}%")

    report = pd.DataFrame(results)
    report.to_csv("backtest_results.csv", index=False)
