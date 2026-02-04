import pandas as pd
import json
from openai import AzureOpenAI
import requests

# Config
SERPER_KEY = "fbccff7e2b07f4c417387bafadd141b97f1583be"
AZURE_KEY = "9Hjt8RDYsjBflHI9C0qSJRQYSqfb04qgNyjm6JA42AnnV4BKb7qVJQQJ99BFACqBBLyXJ3w3AAABACOGWJK7"
AZURE_ENDPOINT = "https://databricksllmpoc.openai.azure.com/"
AZURE_VERSION = "2025-03-01-preview"

client = AzureOpenAI(api_key=AZURE_KEY, api_version=AZURE_VERSION, azure_endpoint=AZURE_ENDPOINT)

def get_ticker_news(ticker):
    url = "https://google.serper.dev/news"
    payload = json.dumps({"q": f"{ticker} stock growth catalyst news"})
    headers = {'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    results = response.json().get('news', [])
    return " ".join([n.get('title', '') for n in results[:5]])

def audit_forecast(ticker, prophet_data, news):
    prompt = f"""
    You are a Senior Investment Auditor. 
    Ticker: {ticker}
    Prophet Baseline Forecast (Percentage Returns):
    7d: {prophet_data['P_7d']}% | 1m: {prophet_data['P_1m']}% | 6m: {prophet_data['P_6m']}%
    
    Recent News Catalysts:
    {news}
    
    Task:
    Adjust the Prophet baseline based on the news. If news is bullish and Prophet is bearish, raise it. If news is bearish, dampen it.
    
    Return JSON:
    {{
        "adjusted_7d": "+2%", 
        "adjusted_1m": "+5%", 
        "adjusted_6m": "+15%",
        "reasoning": "Explain why you adjusted Prophet's numbers"
    }}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return json.loads(response.choices[0].message.content)
    except:
        return None

if __name__ == "__main__":
    df = pd.read_csv("prophet_baselines.csv")
    final_reports = []
    for _, row in df.iterrows():
        ticker = row['Ticker']
        print(f"Auditing {ticker}...")
        news = get_ticker_news(ticker)
        audit = audit_forecast(ticker, row, news)
        if audit:
            final_reports.append({
                "Ticker": ticker,
                "Price": row['Current'],
                "7d": audit['adjusted_7d'],
                "1m": audit['adjusted_1m'],
                "6m": audit['adjusted_6m'],
                "Audit_Reason": audit['reasoning']
            })
    
    print("\n--- HYBRID PROPHET-LLM FINAL REPORT ---")
    report_df = pd.DataFrame(final_reports)
    print(report_df[['Ticker', '7d', '1m', '6m', 'Audit_Reason']].to_string())
