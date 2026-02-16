import pandas as pd
import numpy as np
import yfinance as yf

class QuantService:
    def __init__(self):
        self.fx_pairs = ["EURUSD=X", "USDJPY=X", "GBPUSD=X", "AUDUSD=X"]

    def calculate_volatility_signals(self):
        results = []
        for pair in self.fx_pairs:
            # Fetch 1m data for short-term volatility
            data = yf.Ticker(pair).history(period="1d", interval="1m")
            if data.empty: continue
            
            # 1. Bollinger Band Calculation
            data['MA20'] = data['Close'].rolling(window=20).mean()
            data['STD20'] = data['Close'].rolling(window=20).std()
            data['Upper'] = data['MA20'] + (2.5 * data['STD20'])
            data['Lower'] = data['MA20'] - (2.5 * data['STD20'])
            
            # 2. Z-Score (Price distance from Mean)
            current_price = data['Close'].iloc[-1]
            mean = data['MA20'].iloc[-1]
            std = data['STD20'].iloc[-1]
            z_score = (current_price - mean) / std if std != 0 else 0
            
            # 3. Volatility Signal
            # High positive Z = Overbought (Expect move Down)
            # High negative Z = Oversold (Expect move Up)
            signal = "NEUTRAL"
            if z_score > 2.0: signal = "OVEREXTENDED (SELL)"
            elif z_score < -2.0: signal = "OVEREXTENDED (BUY)"
            
            results.append({
                "pair": pair.replace("=X", ""),
                "price": round(current_price, 5),
                "z_score": round(z_score, 2),
                "signal": signal,
                "volatility": round(std / mean * 1000, 4) # Relative vol
            })
        return results

quant_service = QuantService()
