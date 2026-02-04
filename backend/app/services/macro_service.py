import yfinance as yf
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class MacroService:
    def __init__(self):
        self.symbols = {
            "US_10Y": "^TNX",
            "DXY": "DX-Y.NYB",
            "CNY_USD": "CNY=X",
            "HSI": "^HSI",
            "GOLD": "GC=F",
            "BTC": "BTC-USD",
            "NASDAQ": "^IXIC",
            "DOW": "^DJI"
        }

    def get_market_pulse(self):
        pulse = {}
        try:
            for key, sym in self.symbols.items():
                data = yf.Ticker(sym).history(period="5d")
                if not data.empty:
                    current = data['Close'].iloc[-1]
                    prev = data['Close'].iloc[-2]
                    change = ((current - prev) / prev) * 100
                    pulse[key] = {"value": round(current, 2), "change": round(change, 2)}
            return pulse
        except Exception as e:
            logger.error(f"Macro fetch error: {e}")
            return {}

macro_service = MacroService()
