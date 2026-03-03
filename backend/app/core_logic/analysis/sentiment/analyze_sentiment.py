import os
import json
import requests
import logging
from dotenv import load_dotenv
from app.services.macro_service import macro_service

load_dotenv()
logger = logging.getLogger(__name__)

# Azure OpenAI removed - stub for future implementation
SERPER_KEY = os.getenv("SERPER_KEY")

def get_ticker_news(ticker):
    try:
        url = "https://google.serper.dev/news"
        payload = json.dumps({"q": f"{ticker} stock institutional sentiment news"})
        headers = {'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json'}
        response = requests.request("POST", url, headers=headers, data=payload)
        return " ".join([n.get('title', '') for n in response.json().get('news', [])[:5]])
    except: return ""

def run_analysis(ticker):
    """
    STUB: Azure OpenAI removed.
    Returns neutral sentiment (0.0) - implement with alternative LLM if needed.
    """
    logger.info(f"Sentiment analysis disabled for {ticker} - Azure OpenAI removed")
    return 0.0
