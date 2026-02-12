import os
import requests
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from app.core_logic.tools.search import search_tool

load_dotenv()

class ShockWatchAgent:
    def __init__(self, telegram_chat_id: str):
        self.chat_id = telegram_chat_id
        self.last_shock_hash = None
        self.threshold_severity = 0.7 # 0 to 1

    async def scan_for_shocks(self):
        """
        Monitors for geopolitical shocks specifically related to Trump and Bitcoin.
        """
        query = "Donald Trump Bitcoin breaking news market impact crash"
        raw_news = search_tool.search_market_news(query)
        
        if not raw_news:
            return

        # Simple hash to avoid spamming the same shock
        current_hash = hash(raw_news[:100])
        if current_hash == self.last_shock_hash:
            return
        
        self.last_shock_hash = current_hash
        
        # In a full implementation, we'd use the LLM here to score 'Severity'
        # For now, if keywords like 'crash', 'plunge', 'sell-off' are present, we alert.
        keywords = ['crash', 'plunge', 'sell-off', 'dropped', 'bitcoin', 'trump']
        found_keywords = [w for w in keywords if w in raw_news.lower()]
        
        if len(found_keywords) >= 3:
            await self.send_emergency_alert(raw_news)

    async def send_emergency_alert(self, news_context: str):
        """
        Sends an alert to the Telegram group.
        """
        message = f"🚨 **GEOPOLITICAL SHOCK DETECTED** 🚨\n\nRecent activity from Trump/Bitcoin is impacting markets.\n\n**Context:**\n{news_context[:300]}...\n\n⚠️ *Sell Swarm re-evaluation triggered for all inventory.*"
        
        # This will be routed through the OpenClaw message tool in the main orchestrator
        print(f"SHOCK_WATCH_ALERT: {message}")

shock_watch = ShockWatchAgent("-5214844249")
