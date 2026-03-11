import os
import pandas as pd
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# Azure OpenAI removed - stub for future implementation
# TODO: Replace with appropriate LLM service if needed

SERPER_KEY = os.getenv("SERPER_KEY")

def get_ticker_news(ticker):
    url = "https://google.serper.dev/news"
    payload = json.dumps({"q": f"{ticker} stock growth catalyst hong kong"})
    headers = {'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    results = response.json().get('news', [])
    return " ".join([n.get('title', '') for n in results[:5]])

def analyze_alpha(ticker, news, efficiency, rsi):
    """
    STUB: Azure OpenAI removed.
    Returns empty placeholder - implement with alternative LLM if needed.
    """
    return {
        "score": 0,
        "reason": "Alpha analysis disabled - Azure OpenAI removed",
        "forecast": {"7d": "N/A", "1m": "N/A", "3m": "N/A", "6m": "N/A"}
    }

if __name__ == "__main__":
    print("final_alpha_report.py - Azure OpenAI functionality removed.")
    print("This script no longer performs LLM-based alpha analysis.")
