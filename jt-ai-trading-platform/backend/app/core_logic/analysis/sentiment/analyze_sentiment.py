import os
import json
import requests
import logging
from openai import AzureOpenAI
from dotenv import load_dotenv
from app.services.macro_service import macro_service

load_dotenv()
logger = logging.getLogger(__name__)

# Configuration
SERPER_KEY = os.getenv("SERPER_KEY")
AZURE_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_VERSION = os.getenv("AZURE_OPENAI_VERSION")
AZURE_MODEL = os.getenv("AZURE_OPENAI_MODEL", "gpt-4.1-nano")

client = AzureOpenAI(api_key=AZURE_KEY, api_version=AZURE_VERSION, azure_endpoint=AZURE_ENDPOINT)

def get_ticker_news(ticker):
    try:
        url = "https://google.serper.dev/news"
        payload = json.dumps({"q": f"{ticker} stock institutional sentiment news"})
        headers = {'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json'}
        response = requests.request("POST", url, headers=headers, data=payload)
        return " ".join([n.get('title', '') for n in response.json().get('news', [])[:5]])
    except: return ""

def run_analysis(ticker):
    logger.info(f"Running Macro-Aware LLM Sentiment for {ticker}...")
    try:
        macro_context = macro_service.get_market_pulse()
        news = get_ticker_news(ticker)
        
        prompt = f"""
        Analyze {ticker} with GLOBAL MACRO CONTEXT.
        
        Macro Pulse:
        - US 10Y Yield: {macro_context.get('US_10Y', {}).get('value')}
        - Gold (Geopolitical/War Risk): {macro_context.get('GOLD', {}).get('value')}
        - Bitcoin (Market Liquidity): {macro_context.get('BTC', {}).get('value')}
        - USD Index: {macro_context.get('DXY', {}).get('value')}
        
        Recent News: {news}
        
        Logic: 
        1. If Gold is up (>1%), macro risk is high. Penalize high-beta tech.
        2. If BTC is bullish and DXY is bearish, prioritize growth.
        
        Return JSON ONLY: {{"score": 0.45, "reason": "Brief summary"}}
        """
        response = client.chat.completions.create(
            model=AZURE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        res = json.loads(response.choices[0].message.content)
        return float(res.get("score", 0.0))
    except Exception as e:
        logger.error(f"Sentiment Error: {e}")
        return 0.0
