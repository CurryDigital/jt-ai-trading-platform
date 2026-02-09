import yfinance as yf
import pandas as pd
import logging
from app.core_logic.analysis.time_series.prophet_forecast import get_prophet_prediction

logger = logging.getLogger(__name__)

class MacroService:
    def __init__(self):
        # Mapped to requested regions: US, HK, EU, CN, SG
        self.symbols = {
            "US": "^IXIC",    # NASDAQ
            "HK": "^HSI",     # Hang Seng
            "EU": "^STOXX50E", # Euro Stoxx 50
            "CN": "000001.SS", # Shanghai Composite
            "SG": "^STI"       # Straits Times
        }

    def get_market_pulse(self):
        pulse = {}
        try:
            for region, sym in self.symbols.items():
                data = yf.Ticker(sym).history(period="5d")
                if not data.empty:
                    current = data['Close'].iloc[-1]
                    prev = data['Close'].iloc[-2]
                    change = ((current - prev) / prev) * 100
                    
                    # Add Swarm/Prophet Estimations
                    try:
                        p_data = get_prophet_prediction(sym)
                        estimates = {
                            "1d": f"{p_data['P_7d']/7:+.1f}%" if p_data else "---",
                            "1w": f"{p_data['P_7d']:+.1f}%" if p_data else "---",
                            "1m": f"{p_data['P_1m']:+.1f}%" if p_data else "---"
                        }
                    except:
                        estimates = {"1d": "---", "1w": "---", "1m": "---"}

                    pulse[region] = {
                        "value": round(current, 2),
                        "change": round(change, 2),
                        "estimates": estimates
                    }
            return pulse
        except Exception as e:
            logger.error(f"Macro fetch error: {e}")
            return {}

macro_service = MacroService()
