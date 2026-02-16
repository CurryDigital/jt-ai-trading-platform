import requests
import json

SERPER_KEY = "fbccff7e2b07f4c417387bafadd141b97f1583be"

def research_prophet_strategy():
    url = "https://google.serper.dev/search"
    q = "best way to combine Facebook Prophet forecasts with LLM sentiment scores for stocks"
    payload = json.dumps({"q": q})
    headers = {'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    results = response.json().get('organic', [])
    return [r.get('snippet') for r in results[:3]]

if __name__ == "__main__":
    snippets = research_prophet_strategy()
    for s in snippets:
        print(f"- {s}")
