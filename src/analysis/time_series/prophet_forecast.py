import pandas as pd
from prophet import Prophet
import yfinance as yf
import logging

# Suppress Prophet logging
logging.getLogger('prophet').setLevel(logging.ERROR)
logging.getLogger('cmdstanpy').setLevel(logging.ERROR)

def get_prophet_prediction(ticker):
    print(f"Prophet Training: {ticker}...")
    df = yf.Ticker(ticker).history(period="2y")
    if df.empty: return None
    
    # Prepare for Prophet (ds and y)
    pdf = df.reset_index()[['Date', 'Close']]
    pdf.columns = ['ds', 'y']
    pdf['ds'] = pdf['ds'].dt.tz_localize(None)
    
    m = Prophet(daily_seasonality=False)
    m.fit(pdf)
    
    # Forecast 6 months (180 days)
    future = m.make_future_dataframe(periods=180)
    forecast = m.predict(future)
    
    last_price = pdf['y'].iloc[-1]
    
    # Extract points: 7d, 30d, 90d, 180d
    p_7d = forecast['yhat'].iloc[-173] # Approx 7 days ahead
    p_1m = forecast['yhat'].iloc[-150]
    p_3m = forecast['yhat'].iloc[-90]
    p_6m = forecast['yhat'].iloc[-1]
    
    return {
        "Ticker": ticker,
        "Current": round(last_price, 2),
        "P_7d": round((p_7d / last_price - 1) * 100, 2),
        "P_1m": round((p_1m / last_price - 1) * 100, 2),
        "P_3m": round((p_3m / last_price - 1) * 100, 2),
        "P_6m": round((p_6m / last_price - 1) * 100, 2)
    }

def run_analysis(ticker, data_path="data/processed/hk_stocks_features.csv"):
    """
    Analyzes trend using Prophet. Returns a signal from -1 to 1.
    """
    try:
        from prophet import Prophet
        df = pd.read_csv(data_path)
        df.columns = [c.lower() for c in df.columns]
        ticker_df = df[df['ticker'] == ticker].copy()
        
        if len(ticker_df) < 30:
            return 0.0

        # Prepare for Prophet
        prophet_df = ticker_df[['date', 'close']].rename(columns={'date': 'ds', 'close': 'y'})
        prophet_df['ds'] = pd.to_datetime(prophet_df['ds']).dt.tz_localize(None)
        
        model = Prophet(daily_seasonality=False, changepoint_prior_scale=0.05)
        model.fit(prophet_df)
        
        future = model.make_future_dataframe(periods=7)
        forecast = model.predict(future)
        
        # Logic: Compare last price to 7-day forecast
        current_price = prophet_df['y'].iloc[-1]
        predicted_price = forecast['yhat'].iloc[-1]
        
        signal = (predicted_price - current_price) / current_price
        return max(min(signal * 10, 1.0), -1.0) # Scaled for signal strength
    except Exception as e:
        print(f"Prophet Error for {ticker}: {e}")
        return 0.0

if __name__ == "__main__":
    # Existing CLI logic...
    universe = ["0981.HK", "2333.HK", "0968.HK", "2318.HK", "9988.HK", "0005.HK"]
    results = []
    for t in universe:
        res = get_prophet_prediction(t)
        if res: results.append(res)
    
    pd.DataFrame(results).to_csv("prophet_baselines.csv", index=False)
    print("Prophet baselines saved.")
