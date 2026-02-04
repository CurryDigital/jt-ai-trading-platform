import os
import json
import requests
import logging
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
SERPER_KEY = os.getenv("SERPER_KEY")
AZURE_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_VERSION = os.getenv("AZURE_OPENAI_VERSION")
AZURE_MODEL = os.getenv("AZURE_OPENAI_MODEL", "gpt-4.1-nano")

client = AzureOpenAI(
    api_key=AZURE_KEY, 
    api_version=AZURE_VERSION, 
    azure_endpoint=AZURE_ENDPOINT
)

def get_ticker_news(ticker):
    """Fetches recent news headlines for a ticker using Serper."""
    try:
        url = "https://google.serper.dev/news"
        payload = json.dumps({"q": f"{ticker} stock market sentiment news"})
        headers = {'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json'}
        response = requests.request("POST", url, headers=headers, data=payload)
        results = response.json().get('news', [])
        return " ".join([n.get('title', '') for n in results[:5]])
    except Exception as e:
        logger.error(f"News fetch error for {ticker}: {e}")
        return ""

def analyze_sentiment(ticker, news_text):
    """Analyzes news text using Azure OpenAI and returns a score -1 to 1."""
    if not news_text:
        return 0.0
        
    prompt = f"""
    Analyze the following news headlines for the stock {ticker}.
    Determine the overall market sentiment and institutional outlook.
    
    News Headlines:
    {news_text}
    
    Task:
    Provide a consolidated sentiment score between -1 (extremely bearish) and 1 (extremely bullish).
    
    Return ONLY a JSON object:
    {{
        "score": 0.45
    }}
    """
    try:
        response = client.chat.completions.create(
            model=AZURE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        result = json.loads(response.choices[0].message.content)
        return float(result.get("score", 0.0))
    except Exception as e:
        logger.error(f"Azure OpenAI error for {ticker}: {e}")
        return 0.0

def run_analysis(ticker):
    """Standardized interface for the Model Orchestrator."""
    logger.info(f"Running LLM Sentiment Analysis for {ticker}...")
    news = get_ticker_news(ticker)
    score = analyze_sentiment(ticker, news)
    return score

if __name__ == "__main__":
    # Test execution
    print(f"Test Signal for 0700.HK: {run_analysis('0700.HK')}")
