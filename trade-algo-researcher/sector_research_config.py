#!/usr/bin/env python3
"""
Sector-Specific Strategy Research
Tests Golden strategies across sector boundaries
"""

SECTOR_TICKERS = {
    "tech_growth": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMD", "TSLA", "AMZN", "CRM", "NFLX"],
    "tech_legacy": ["INTC", "IBM", "CSCO", "ORCL", "QCOM", "MU", "AMAT"],
    "finance": ["JPM", "BAC", "GS", "MS", "C", "WFC", "AXP", "BLK"],
    "healthcare": ["JNJ", "PFE", "UNH", "ABBV", "LLY", "MRK", "TMO", "ABT"],
    "energy": ["XOM", "CVX", "COP", "EOG", "SLB", "OXY", "MPC", "VLO"],
    "consumer": ["AMZN", "WMT", "COST", "HD", "MCD", "NKE", "SBUX", "TGT"],
    "industrial": ["CAT", "BA", "GE", "HON", "UNP", "RTX", "LMT", "UPS"],
    "crypto_stocks": ["MSTR", "COIN", "RIOT", "MARA", "BITF", "HUT"],
    "sector_etfs": ["XLF", "XLV", "XLE", "XLI", "XLP", "XLU", "XLK", "XLB"]
}

# Strategy definitions for cross-sector testing
STRATEGIES_TO_TEST = {
    "bb_squeeze": {
        "name": "Bollinger Band Squeeze + RSI < 40",
        "entry_logic": "bb_width < 0.05 AND rsi < 40",
        "hold_days": 5,
        "golden_assets": ["MSFT", "NVDA", "QQQ", "META"]
    },
    "rsi_mean_reversion": {
        "name": "RSI < 30 Mean Reversion",
        "entry_logic": "rsi < 30",
        "hold_days": 5,
        "golden_assets": ["GOOGL", "NVDA", "META", "COIN", "MSTR"]
    },
    "stoch_trend": {
        "name": "Stochastic + Trend Combo",
        "entry_logic": "stoch_k < 20 AND close < sma_50",
        "hold_days": 5,
        "golden_assets": ["NVDA"]
    },
    "momentum_trend": {
        "name": "Momentum Trend (ADX > 25)",
        "entry_logic": "close > sma_50 AND adx > 25",
        "hold_days": 10,
        "golden_assets": ["MSTR", "TSLA", "MSFT", "NVDA", "SPY", "QQQ", "AAPL", "AMD"]
    }
}

# Test matrix for cross-sector validation
CROSS_SECTOR_TESTS = [
    {
        "name": "BB Squeeze on Finance",
        "strategy": "bb_squeeze",
        "tickers": ["JPM", "BAC", "GS", "MS", "C", "XLF"],
        "expected_win_rate": 0.65
    },
    {
        "name": "RSI Mean Reversion on Healthcare",
        "strategy": "rsi_mean_reversion",
        "tickers": ["JNJ", "PFE", "UNH", "ABBV", "XLV"],
        "expected_win_rate": 0.60
    },
    {
        "name": "Momentum Trend on Energy",
        "strategy": "momentum_trend",
        "tickers": ["XOM", "CVX", "COP", "XLE"],
        "expected_win_rate": 0.65
    },
    {
        "name": "BB Squeeze on Consumer",
        "strategy": "bb_squeeze",
        "tickers": ["WMT", "COST", "HD", "MCD", "NKE"],
        "expected_win_rate": 0.60
    }
]

# New hypotheses for testing
NEW_HYPOTHESES = [
    {
        "id": "H1",
        "name": "RSI + MACD + Volume Triple",
        "entry": "rsi < 35 AND macd_hist > macd_hist.shift(1) AND volume > volume_sma20 * 1.15",
        "hold_days": 5,
        "tickers": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "TSLA", "AMD"]
    },
    {
        "id": "H2", 
        "name": "Morning Star Pattern",
        "entry": "bearish_candle(1) AND doji(0) AND bullish_candle(1) AND close > open(2)",
        "hold_days": 5,
        "tickers": ["SPY", "QQQ", "AAPL", "MSFT", "GOOGL", "AMZN"]
    },
    {
        "id": "H3",
        "name": "Bearish RSI >70 + SPY < 200d",
        "entry": "rsi > 70 AND spy_close < spy_sma200",
        "hold_days": 5,
        "direction": "short",
        "tickers": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "TSLA", "AMD"]
    },
    {
        "id": "H4",
        "name": "ATR Compression Breakout",
        "entry": "atr_14 < atr_14.rolling(20).quantile(0.2) AND close > high_10d.shift(1)",
        "hold_days": 5,
        "tickers": ["MSFT", "QQQ", "META", "NVDA", "AAPL", "GOOGL"]
    }
]

# Enhanced versions of existing validated strategies
ENHANCEMENT_TESTS = [
    {
        "base_strategy": "META BB Squeeze",
        "enhancement": "Add Volume > 1.2x",
        "entry": "bb_width < 0.05 AND rsi < 40 AND volume > volume_sma20 * 1.2",
        "target_improvement": 0.05
    },
    {
        "base_strategy": "AMD Trend",
        "enhancement": "Add ADX > 25 Filter",
        "entry": "close > sma_50 AND adx > 25 AND adx > adx.shift(1)",
        "target_improvement": 0.03
    },
    {
        "base_strategy": "RSI < 30 Universal",
        "enhancement": "Add MACD Improving",
        "entry": "rsi < 30 AND macd_hist > macd_hist.shift(1)",
        "target_improvement": 0.05
    }
]
