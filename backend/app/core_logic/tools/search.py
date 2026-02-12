import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class SearchTool:
    def __init__(self):
        self.api_key = os.getenv("serper_api_key")
        self.url = "https://google.serper.dev/search"

    def search_market_news(self, query: str):
        """
        Fetches latest news using Serper API.
        """
        payload = json.dumps({
            "q": query,
            "num": 5,
            "tbs": "qdr:d" # Last 24 hours
        })
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }

        try:
            response = requests.request("POST", self.url, headers=headers, data=payload)
            data = response.json()
            results = []
            if "organic" in data:
                for item in data["organic"]:
                    results.append(f"{item.get('title')}: {item.get('snippet')}")
            return "\n".join(results)
        except Exception as e:
            return f"Search failed: {str(e)}"

search_tool = SearchTool()
