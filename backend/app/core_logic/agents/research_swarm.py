import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

load_dotenv()

from app.core_logic.tools.search import search_tool

class ResearchSwarm:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            temperature=0.7
        )

    async def debate_market_outlook(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wholistic debate finding winners in chaos (e.g. Trump anti-BTC environment).
        """
        search_query = "Trump Bitcoin crash HK market winners safe havens defensive stocks gold USD"
        geopolitical_shocks = search_tool.search_market_news(search_query)

        prompt = f"""
        Current Shock: {geopolitical_shocks}
        
        Act as a panel of Wholistic Analysts. 
        When Trump is harsh on Bitcoin and HK crashes, DON'T just be bearish. Find the winners.
        
        Debate:
        1. Bull: Where is the rotation going? (Gold, USD, Utilities, specific HK defensives).
        2. Bear: What is the true floor for the crashing sectors?
        3. Risk Manager: How to hedge?

        Return a JSON with:
        - market_mood: Defensive / Aggressive / Rotation
        - top_recommendations: [List of specific sectors or stock types that thrive in this specific chaos]
        - contrarian_buy_signal: (Is there a 'blood in the streets' opportunity in HK?)
        - expected_trends: {{1D, 7D, 1M}}
        """
        return self.llm.invoke(prompt).content

    async def debate_sell_signal(self, inventory_item: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Specialized debate with Regime-Switching weights (Paper 1 implementation).
        """
        search_query = f"{inventory_item['ticker']} stock latest news analysis impact Trump Bitcoin"
        news_context = search_tool.search_market_news(search_query)
        
        regime = market_data.get('regime', 'STAGNANT')
        
        # Implementation of Paper 1: Dynamic Agent Weighting based on Regime
        weights = "EQUAL (33% each)"
        if regime == "PANIC":
            weights = "RISK MANAGER DOMINANT (60%), Bear (30%), Bull (10%)"
        elif regime == "GROWTH":
            weights = "BULL DOMINANT (60%), Risk Manager (30%), Bear (10%)"
        elif regime == "CRASH":
            weights = "BEAR/RISK DOMINANT (45% each), Bull (10%)"

        prompt = f"""
        Inventory Item: {inventory_item} (Purchase Price: {inventory_item.get('purchase_price', 'N/A')})
        Market Context: {market_data}
        Current Market Regime: {regime}
        Active Weighting Strategy: {weights}
        News Context: {news_context}

        Act as a panel of 3 agents (Bull, Bear, Risk Manager) debating this asset.
        
        INSTRUCTIONS:
        1. Apply the weightings: {weights}. The dominant agent(s) must lead the final decision.
        2. Evaluate Price Action vs Purchase Price.
        3. Cross-Asset Check: If DXY or Yields are spiking, increase Risk Manager caution.

        Return a JSON with:
        - decision: (SELL / HOLD / TRIM / BUY)
        - confidence_rating: (0.0 to 1.0, weighted by regime logic)
        - expected_exit_horizon: (Immediate / 1w / 2w / 1m / etc)
        - reasoning: brief summary of the debate, explicitly citing the regime-based weights used.
        """
        response = self.llm.invoke(prompt).content
        return {"ticker": inventory_item['ticker'], "analysis": response}

# Lazy initialization - only create when actually used
_research_swarm_instance = None

def get_research_swarm():
    global _research_swarm_instance
    if _research_swarm_instance is None:
        _research_swarm_instance = ResearchSwarm()
    return _research_swarm_instance

# Backward compatibility - but this will fail if env vars not set
# Use get_research_swarm() instead in new code
try:
    research_swarm = ResearchSwarm()
except Exception as e:
    print(f"Warning: Could not initialize research_swarm (Azure OpenAI not configured): {e}")
    research_swarm = None
