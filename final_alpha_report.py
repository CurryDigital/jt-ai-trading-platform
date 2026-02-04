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

client = AzureOpenAI(api_key=AZURE_KEY, api_version=AZURE_VERSION, azure_endpoint=AZURE_ENDPOINT)

def get_ticker_news(ticker):
    url = "https://google.serper.dev/news"
    payload = json.dumps({"q": f"{ticker} stock growth catalyst hong kong"})
    headers = {'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    results = response.json().get('news', [])
    return " ".join([n.get('title', '') for n in results[:5]])

def analyze_alpha(ticker, news, efficiency, rsi):
    prompt = f"""
    Analyze {ticker} for High-Alpha Potential.
    Efficiency Score (Risk-Adj Momentum): {efficiency}
    RSI: {rsi}
    News: {news}
    
    Task:
    1. Score from -1 to 1 based on 'Potential for Outperformance'.
    2. Provide Reasoning.
    3. Forecast 7d, 1m, 3m, 6m.
    
    Return JSON: {{"score": 0.8, "reason": "...", "forecast": {{"7d": "...", "1m": "...", "3m": "...", "6m": "..."}}}}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return json.loads(response.choices[0].message.content)
    except:
        return {"score": 0, "reason": "Failed", "forecast": {}}

if __name__ == "__main__":
    df = pd.read_csv("enhanced_alpha_universe.csv")
    results = []
    for _, row in df.iterrows():
        ticker = row['Ticker']
        print(f"[{_ + 1}/{len(df)}] Analyzing {ticker}...", flush=True)
        try:
            news = get_ticker_news(ticker)
            analysis = analyze_alpha(ticker, news, row['Efficiency_Score'], row['RSI'])
            
            results.append({
                "Ticker": ticker,
                "Alpha_Score": analysis.get('score', 0),
                "Efficiency": round(row['Efficiency_Score'], 4),
                "Reason": analysis.get('reason', 'N/A'),
                "7d": analysis.get('forecast', {}).get('7d'),
                "6m": analysis.get('forecast', {}).get('6m')
            })
        except Exception as e:
            print(f"Error on {ticker}: {e}")
    
    final = pd.DataFrame(results).sort_values(by="Alpha_Score", ascending=False).head(10)
    print("\n--- TOP 10 HIGH POTENTIAL ALPHA STOCKS ---")
    for _, r in final.iterrows():
        print(f"\n{r['Ticker']} | Alpha: {r['Alpha_Score']} | Efficiency: {r['Efficiency']}")
        print(f"Reason: {r['Reason']}")
        print(f"Forecast: 7d: {r['7d']} | 6m: {r['6m']}")
