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
    payload = json.dumps({"q": f"{ticker} stock institutional outlook news"})
    headers = {'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    results = response.json().get('news', [])
    return " ".join([n.get('title', '') for n in results[:3]])

def forensic_analysis(ticker, gold_row, news):
    prompt = f"""
    You are a Forensic Quant Analyst. Analyze this Gold Layer data for {ticker}:
    
    Data:
    - Money Flow Index (MFI): {gold_row['MFI']}
    - Relative Strength vs HSI (30d): {gold_row['Relative_Strength_30d']}
    - Sharpe Ratio: {gold_row['Sharpe_Ratio']}
    - Divergence Signal: {gold_row['Divergence_Signal']}
    - Volatility (ATR%): {gold_row['Vol_Pct']}%
    
    News Context:
    {news}
    
    Logic Priorities:
    1. Institutional Alignment: High MFI + High Relative Strength = Strong Accumulation.
    2. Divergence Check: If Divergence is 'Bearish_Div', warn of a Bull Trap.
    3. Efficiency: Sharpe > 2.0 indicates high-quality gains.
    
    Task:
    Provide a high-conviction conviction score (-1 to 1) and a forensic verdict.
    Forecast: 7d, 1m, 3m, 6m.
    
    Return JSON:
    {{
        "score": 0.85, 
        "verdict": "Forensic summary here",
        "forecast": {{"7d": "...", "1m": "...", "3m": "...", "6m": "..."}}
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
    df = pd.read_csv("gold_stock_features.csv")
    final_reports = []
    
    # Analyze all 15 stocks from the Gold Layer
    for _, row in df.iterrows():
        ticker = row['Ticker']
        print(f"Forensic Audit: {ticker}...")
        news = get_ticker_news(ticker)
        analysis = forensic_analysis(ticker, row, news)
        
        if analysis:
            final_reports.append({
                "Ticker": ticker,
                "Conviction": analysis['score'],
                "Verdict": analysis['verdict'],
                "7d": analysis['forecast']['7d'],
                "1m": analysis['forecast']['1m'],
                "6m": analysis['forecast']['6m']
            })
    
    final_df = pd.DataFrame(final_reports).sort_values(by="Conviction", ascending=False)
    print("\n--- FORENSIC ALPHA REPORT ---")
    for _, r in final_df.head(10).iterrows():
        print(f"\n{r['Ticker']} | Conviction: {r['Conviction']}")
        print(f"Verdict: {r['Verdict']}")
        print(f"Forecast: 7d: {r['7d']} | 1m: {r['1m']} | 6m: {r['6m']}")
    
    final_df.to_csv("forensic_alpha_results.csv", index=False)
