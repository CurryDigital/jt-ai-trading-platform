import pandas as pd
import requests
import os
from openai import AzureOpenAI
import json

# Config
SERPER_KEY = "fbccff7e2b07f4c417387bafadd141b97f1583be"
AZURE_KEY = "9Hjt8RDYsjBflHI9C0qSJRQYSqfb04qgNyjm6JA42AnnV4BKb7qVJQQJ99BFACqBBLyXJ3w3AAABACOGWJK7"
AZURE_ENDPOINT = "https://databricksllmpoc.openai.azure.com/"
AZURE_VERSION = "2025-03-01-preview"

client = AzureOpenAI(
    api_key=AZURE_KEY,
    api_version=AZURE_VERSION,
    azure_endpoint=AZURE_ENDPOINT
)

def get_ticker_news(ticker):
    url = "https://google.serper.dev/news"
    payload = json.dumps({"q": f"{ticker} stock news hong kong"})
    headers = {'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    results = response.json().get('news', [])
    return " ".join([n.get('title', '') for n in results[:5]])

def analyze_sentiment(ticker, headlines, rsi, sma_50):
    prompt = f"""
    You are a quantitative stock analyst. Analyze the following data for {ticker}:
    
    Technical KPIs:
    - RSI (14): {rsi}
    - SMA (50): {sma_50}
    
    Recent News Headlines:
    {headlines}
    
    Tasks:
    1. Determine a sentiment score from -1 to 1.
    2. Provide a 1-sentence reasoning.
    3. Forecast expected price movement (%) for: 7 days, 1 month, 3 months, 6 months.
    
    Return ONLY JSON:
    {{
        "score": 0.5, 
        "reason": "Reasoning here",
        "forecast": {{
            "7d": "+2%",
            "1m": "+5%",
            "3m": "+10%",
            "6m": "+15%"
        }}
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
        return {"score": 0, "reason": "Analysis failed", "forecast": {"7d": "0%", "1m": "0%", "3m": "0%", "6m": "0%"}}

if __name__ == "__main__":
    df = pd.read_csv("hk_stocks_features.csv")
    latest = df.groupby('Ticker').tail(1).copy()
    
    recommendations = []
    for _, row in latest.iterrows():
        ticker = row['Ticker']
        print(f"Analyzing {ticker}...")
        news = get_ticker_news(ticker)
        analysis = analyze_sentiment(ticker, news, row['RSI_14'], row['SMA_50'])
        
        # Logic Enrichment: Weighted Score
        tech_score = 0
        if row['Close'] > row['SMA_50']: tech_score += 0.5
        if 40 < row['RSI_14'] < 60: tech_score += 0.5
        
        final_score = (tech_score * 0.5) + (analysis['score'] * 0.5)
        
        recommendations.append({
            "Ticker": ticker,
            "Price": round(row['Close'], 2),
            "Technical_Score": tech_score,
            "Sentiment": analysis['score'],
            "Final_Score": round(final_score, 2),
            "Reason": analysis['reason'],
            "7d": analysis['forecast'].get('7d', '0%'),
            "1m": analysis['forecast'].get('1m', '0%'),
            "3m": analysis['forecast'].get('3m', '0%'),
            "6m": analysis['forecast'].get('6m', '0%')
        })
    
    res_df = pd.DataFrame(recommendations)
    top_10 = res_df.sort_values(by='Final_Score', ascending=False).head(10)
    
    print("\n--- TOP 10 HK STOCK POTENTIALS & FORECASTS ---")
    for _, row in top_10.iterrows():
        print(f"\nTicker: {row['Ticker']} | Final Score: {row['Final_Score']}")
        print(f"Reason: {row['Reason']}")
        print(f"Forecasts: 7d: {row['7d']} | 1m: {row['1m']} | 3m: {row['3m']} | 6m: {row['6m']}")
    
    top_10.to_csv("top_10_forecast.csv", index=False)
