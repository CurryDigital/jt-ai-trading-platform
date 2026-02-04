import requests
import json

SERPER_KEY = "fbccff7e2b07f4c417387bafadd141b97f1583be"

def search_potential_stocks():
    url = "https://google.serper.dev/search"
    queries = [
        "best performing mid-cap stocks hong kong 2026",
        "HKEX high growth potential stocks 2026 analyst picks",
        "undervalued hong kong stocks with high institutional ownership"
    ]
    
    potential_tickers = set()
    for q in queries:
        payload = json.dumps({"q": q})
        headers = {'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json'}
        response = requests.request("POST", url, headers=headers, data=payload)
        for result in response.json().get('organic', []):
            snippet = result.get('snippet', '')
            # Simple heuristic to extract potential HK ticker patterns (e.g., 1234.HK or (1234))
            import re
            found = re.findall(r'\b\d{4}\.HK\b|\(\d{4}\)', snippet)
            for f in found:
                t = f.replace('(','').replace(')','')
                if '.' not in t: t += '.HK'
                potential_tickers.add(t)
    
    return list(potential_tickers)

if __name__ == "__main__":
    tickers = search_potential_stocks()
    print(json.dumps(tickers))
