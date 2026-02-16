import os
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from app.core_logic.tools.search import search_tool
from app.core_logic.tools.technical_indicators_tools import TechnicalIndicatorsTools

load_dotenv()

class WholisticResearchSwarm:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            temperature=0.7
        )
        self.tech_tools = TechnicalIndicatorsTools()

    async def get_enhanced_context(self, ticker: str) -> Dict[str, Any]:
        """Fetches both News (Serper) and Technicals."""
        news = search_tool.search_market_news(f"{ticker} Trump Bitcoin geopolitical impact")
        # Simulating technical fetch - in production this uses yfinance/alphavantage
        technicals = {"rsi": 65, "macd": "Bearish Cross", "bollinger": "Near Upper Band"}
        return {"news": news, "technicals": technicals}

    async def wholistic_debate(self, ticker: str, buy_price: float = None):
        context = await self.get_enhanced_context(ticker)
        
        prompt = f"""
        Asset: {ticker}
        Purchase Price: {buy_price if buy_price else 'N/A'}
        Technical Indicators: {context['technicals']}
        Geopolitical News: {context['news']}

        You are a Multi-Agent Swarm (Aggressive Bull, Defensive Bear, Risk Manager).
        Debate the 1D, 7D, and 1M outlook considering Trump behavior and Bitcoin shocks.
        
        If purchase price is provided, determine if we SELL, HOLD, or BUY-THE-DIP.
        
        Return JSON:
        - decision: SELL / HOLD / BUY / TRIM
        - conviction: 0-1
        - reasoning: include technical vs news trade-offs
        - crash_risk: High/Medium/Low
        """
        return self.llm.invoke(prompt).content

wholistic_swarm = WholisticResearchSwarm()
