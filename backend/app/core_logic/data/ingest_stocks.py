import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os

def get_hk_stocks_data(tickers, period="2y"):
    all_data = []
    
    for ticker in tickers:
        print(f"Fetching data for {ticker}...")
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        
        if df.empty:
            print(f"No data found for {ticker}")
            continue
            
        # Add ticker column
        df['Ticker'] = ticker
        
        # Calculate Indicators using pandas_ta
        df['RSI_14'] = ta.rsi(df['Close'], length=14)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        df['SMA_200'] = ta.sma(df['Close'], length=200)
        
        all_data.append(df)
        
    if not all_data:
        return None
        
    return pd.concat(all_data)

if __name__ == "__main__":
    # Top 10 HK Tickers (HSI Components)
    hk_tickers = [
        "0700.HK", "9988.HK", "3690.HK", "1211.HK", "2318.HK", 
        "0005.HK", "1299.HK", "1810.HK", "9618.HK", "3988.HK"
    ]
    
    combined_df = get_hk_stocks_data(hk_tickers)
    
    if combined_df is not None:
        output_file = "hk_stocks_features.csv"
        combined_df.to_csv(output_file)
        print(f"Successfully saved features to {output_file}")
    else:
        print("Failed to retrieve any data.")
