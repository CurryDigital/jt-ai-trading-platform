import pandas as pd
import numpy as np

class VisualAgent:
    """
    Simulates visual pattern recognition by analyzing price geometry.
    Identifies patterns like Double Bottoms, Support/Resistance, and Breakouts.
    """
    def __init__(self):
        pass

    def scan_patterns(self, df):
        if len(df) < 20: return []
        
        patterns = []
        close = df['close'].values
        
        # 1. Simple Support/Resistance Logic (Geometry)
        recent_low = np.min(close[-10:])
        recent_high = np.max(close[-10:])
        current_price = close[-1]
        
        if current_price > np.max(close[-20:-1]):
            patterns.append({"name": "Resistance Breakout", "type": "Bullish"})
        
        if current_price < np.min(close[-20:-1]):
            patterns.append({"name": "Support Breakdown", "type": "Bearish"})
            
        # 2. Double Bottom Detection (W-Pattern)
        # Simplified: Check if we have two similar lows with a peak in between
        if len(close) > 30:
            l1 = np.min(close[-30:-15])
            l2 = np.min(close[-15:])
            if abs(l1 - l2) / l1 < 0.02 and current_price > l2 * 1.05:
                patterns.append({"name": "Double Bottom", "type": "Bullish"})
                
        return patterns

visual_agent = VisualAgent()
