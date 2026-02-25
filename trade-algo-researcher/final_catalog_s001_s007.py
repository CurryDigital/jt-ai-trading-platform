#!/usr/bin/env python3
"""
FINAL CATALOG: S001-S007 with All Sector Variations
Ready for Paper Trading Deployment
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/trade-algo-researcher')
import warnings
warnings.filterwarnings('ignore')

import json

# COMPLETE SECTOR-SPECIFIC STRATEGY CATALOG
# Based on full universe testing (418 tickers) with 3-tier validation

catalog = {
    "metadata": {
        "tested_universe": 418,
        "validation_method": "3-tier (Train 2021-22 / Test 2023-24 / Validate 2025+)",
        "transaction_costs": "0.1% per trade",
        "created_date": "2026-02-24",
        "methodology": "Full universe → Sector breakdown → Industry-specific deployment"
    },
    "strategies": []
}

# S001: RSI Mean Reversion (<30, 10D hold)
s001_variations = [
    {
        "id": "S001-01",
        "name": "RSI_MR_HK_Banks",
        "logic": "RSI(14) < 30, Hold 10 days",
        "sector": "HK Banks",
        "tickers": ["0005.HK", "0939.HK", "1398.HK", "2388.HK", "3328.HK", "3988.HK"],
        "test_wr": 89.5,
        "val_wr": 87.8,
        "total_trades": 225,
        "status": "GOLDEN",
        "allocation": "20%",
        "max_positions": 2
    },
    {
        "id": "S001-03",
        "name": "RSI_MR_CN_Banks",
        "logic": "RSI(14) < 30, Hold 10 days",
        "sector": "China Banks",
        "tickers": ["600036.SS", "601398.SS", "601939.SS", "601988.SS"],
        "test_wr": 82.4,
        "val_wr": 78.2,
        "total_trades": 135,
        "status": "GOLDEN",
        "allocation": "15%",
        "max_positions": 2
    },
    {
        "id": "S001-04",
        "name": "RSI_MR_CN_Other",
        "logic": "RSI(14) < 30, Hold 10 days",
        "sector": "China Other",
        "tickers": ["600028.SS", "601088.SS", "601857.SS", "688008.SS"],
        "test_wr": 79.6,
        "val_wr": 66.6,
        "total_trades": 153,
        "status": "GOLDEN",
        "allocation": "10%",
        "max_positions": 2
    },
    {
        "id": "S001-02",
        "name": "RSI_MR_US_Consumer_Retail",
        "logic": "RSI(14) < 30, Hold 10 days",
        "sector": "US Consumer Retail",
        "tickers": ["COST", "WMT"],
        "test_wr": 82.7,
        "val_wr": 71.2,
        "total_trades": 37,
        "status": "VALIDATED",
        "allocation": "10%",
        "max_positions": 1
    },
    {
        "id": "S001-09",
        "name": "RSI_MR_HK_Property",
        "logic": "RSI(14) < 30, Hold 10 days",
        "sector": "HK Property",
        "tickers": ["0001.HK", "0002.HK"],
        "test_wr": 73.2,
        "val_wr": 70.7,
        "total_trades": 87,
        "status": "VALIDATED",
        "allocation": "5%",
        "max_positions": 1
    },
    {
        "id": "S001-10",
        "name": "RSI_MR_US_Consumer_Staples",
        "logic": "RSI(14) < 30, Hold 10 days",
        "sector": "US Consumer Staples",
        "tickers": ["PG"],
        "test_wr": 72.5,
        "val_wr": 71.4,
        "total_trades": 51,
        "status": "VALIDATED",
        "allocation": "5%",
        "max_positions": 1
    },
    {
        "id": "S001-05",
        "name": "RSI_MR_HK_Utilities",
        "logic": "RSI(14) < 30, Hold 10 days",
        "sector": "HK Utilities",
        "tickers": ["0083.HK"],
        "test_wr": 78.0,
        "val_wr": 100.0,
        "total_trades": 41,
        "status": "VALIDATED",
        "allocation": "5%",
        "max_positions": 1
    },
    {
        "id": "S001-13",
        "name": "RSI_MR_HK_Other",
        "logic": "RSI(14) < 30, Hold 10 days",
        "sector": "HK Other",
        "tickers": ["0019.HK", "0066.HK", "0144.HK", "0175.HK", "0267.HK", "0388.HK"],
        "test_wr": 68.2,
        "val_wr": 62.0,
        "total_trades": 143,
        "status": "VALIDATED",
        "allocation": "5%",
        "max_positions": 1
    }
]

# S002: Trend Following (Price > SMA50)
s002_variations = [
    {
        "id": "S002-01",
        "name": "Trend_US_ETF_Index",
        "logic": "Price > SMA(50), Hold 10 days",
        "sector": "US ETF Index",
        "tickers": ["SPY", "QQQ"],
        "test_wr": 65.6,
        "val_wr": 68.4,
        "total_trades": 714,
        "status": "VALIDATED",
        "allocation": "10%",
        "max_positions": 1
    },
    {
        "id": "S002-02",
        "name": "Trend_US_Industrials",
        "logic": "Price > SMA(50), Hold 10 days",
        "sector": "US Industrials",
        "tickers": ["GE", "LMT", "RTX"],
        "test_wr": 65.1,
        "val_wr": 63.4,
        "total_trades": 893,
        "status": "VALIDATED",
        "allocation": "5%",
        "max_positions": 1
    },
    {
        "id": "S002-03",
        "name": "Trend_US_Other",
        "logic": "Price > SMA(50), Hold 10 days",
        "sector": "US Other",
        "tickers": ["ASML", "TSM"],
        "test_wr": 64.6,
        "val_wr": 74.3,
        "total_trades": 329,
        "status": "VALIDATED",
        "allocation": "5%",
        "max_positions": 1
    },
    {
        "id": "S002-05",
        "name": "Trend_US_Tech",
        "logic": "Price > SMA(50), Hold 10 days",
        "sector": "US Tech",
        "tickers": ["META", "NVDA", "PLTR", "SHOP"],
        "test_wr": 62.4,
        "val_wr": 58.0,
        "total_trades": 642,
        "status": "VALIDATED",
        "allocation": "5%",
        "max_positions": 1
    },
    {
        "id": "S002-06",
        "name": "Trend_US_Banks",
        "logic": "Price > SMA(50), Hold 10 days",
        "sector": "US Banks",
        "tickers": ["BAC", "JPM", "C"],
        "test_wr": 61.6,
        "val_wr": 70.0,
        "total_trades": 610,
        "status": "VALIDATED",
        "allocation": "5%",
        "max_positions": 1
    }
]

# S003: 3-Day Panic Reversal
s003_variations = [
    {
        "id": "S003-02",
        "name": "Panic_Reversal_US_ETF",
        "logic": "3 consecutive down days, Hold 5 days",
        "sector": "US ETF",
        "tickers": ["SPY", "QQQ", "IWM"],
        "test_wr": 67.9,
        "val_wr": 62.0,
        "total_trades": 156,
        "status": "VALIDATED",
        "allocation": "5%",
        "max_positions": 1
    },
    {
        "id": "S003-03",
        "name": "Panic_Reversal_US_Tech",
        "logic": "3 consecutive down days, Hold 5 days",
        "sector": "US Tech",
        "tickers": ["AAPL", "GOOGL", "META", "NVDA"],
        "test_wr": 67.7,
        "val_wr": 58.5,
        "total_trades": 378,
        "status": "VALIDATED",
        "allocation": "5%",
        "max_positions": 1
    },
    {
        "id": "S003-04",
        "name": "Panic_Reversal_HK_Property",
        "logic": "3 consecutive down days, Hold 5 days",
        "sector": "HK Property",
        "tickers": ["0001.HK", "0002.HK", "0016.HK"],
        "test_wr": 65.2,
        "val_wr": 63.0,
        "total_trades": 145,
        "status": "VALIDATED",
        "allocation": "5%",
        "max_positions": 1
    },
    {
        "id": "S003-06",
        "name": "Panic_Reversal_HK_Banks",
        "logic": "3 consecutive down days, Hold 5 days",
        "sector": "HK Banks",
        "tickers": ["0005.HK", "0939.HK"],
        "test_wr": 65.1,
        "val_wr": 68.0,
        "total_trades": 78,
        "status": "VALIDATED",
        "allocation": "5%",
        "max_positions": 1
    },
    {
        "id": "S003-07",
        "name": "Panic_Reversal_CN_Other",
        "logic": "3 consecutive down days, Hold 5 days",
        "sector": "China Other",
        "tickers": ["601088.SS", "601857.SS"],
        "test_wr": 64.0,
        "val_wr": 61.5,
        "total_trades": 127,
        "status": "VALIDATED",
        "allocation": "5%",
        "max_positions": 1
    }
]

# S004: Gap Down Recovery
s004_variations = [
    {
        "id": "S004-02",
        "name": "Gap_Recovery_HK_Other",
        "logic": "Gap down >2%, Hold 3 days",
        "sector": "HK Other",
        "tickers": ["0700.HK", "1810.HK"],
        "test_wr": 71.4,
        "val_wr": 55.0,
        "total_trades": 21,
        "status": "GOLDEN",
        "allocation": "5%",
        "max_positions": 1
    },
    {
        "id": "S004-03",
        "name": "Gap_Recovery_Other",
        "logic": "Gap down >2%, Hold 3 days",
        "sector": "Other",
        "tickers": ["ASML", "CL=F", "SI=F"],
        "test_wr": 65.5,
        "val_wr": 72.0,
        "total_trades": 89,
        "status": "VALIDATED",
        "allocation": "3%",
        "max_positions": 1
    }
]

# S005: Volume Breakout
s005_variations = [
    {
        "id": "S005-01",
        "name": "Vol_Breakout_Other",
        "logic": "Volume >1.5x avg + Price > SMA20, Hold 5 days",
        "sector": "Other",
        "tickers": ["ASML", "CL=F", "SI=F", "NG=F"],
        "test_wr": 71.0,
        "val_wr": 73.5,
        "total_trades": 90,
        "status": "GOLDEN",
        "allocation": "5%",
        "max_positions": 1
    },
    {
        "id": "S005-02",
        "name": "Vol_Breakout_US_Banks",
        "logic": "Volume >1.5x avg + Price > SMA20, Hold 5 days",
        "sector": "US Banks",
        "tickers": ["GS", "MS"],
        "test_wr": 68.4,
        "val_wr": 85.7,
        "total_trades": 19,
        "status": "VALIDATED",
        "allocation": "3%",
        "max_positions": 1
    },
    {
        "id": "S005-06",
        "name": "Vol_Breakout_CN_Banks",
        "logic": "Volume >1.5x avg + Price > SMA20, Hold 5 days",
        "sector": "China Banks",
        "tickers": ["601398.SS", "601939.SS"],
        "test_wr": 60.9,
        "val_wr": 72.3,
        "total_trades": 69,
        "status": "VALIDATED",
        "allocation": "3%",
        "max_positions": 1
    }
]

# S007: Sector Rotation
s007_variations = [
    {
        "id": "S007-01",
        "name": "Sector_Rotation_XLK_XLF",
        "logic": "XLK/XLF ratio > SMA20, Hold XLK 10 days",
        "sector": "US Sector Rotation",
        "tickers": ["XLK", "XLF"],
        "test_wr": 65.3,
        "val_wr": 64.1,
        "total_trades": 262,
        "status": "GOLDEN",
        "allocation": "10%",
        "max_positions": 1,
        "notes": "Timing signal — rotate between tech and financials"
    }
]

# Combine all
catalog["strategies"] = (s001_variations + s002_variations + s003_variations + 
                        s004_variations + s005_variations + s007_variations)

# Calculate totals
golden = [s for s in catalog["strategies"] if s["status"] == "GOLDEN"]
validated = [s for s in catalog["strategies"] if s["status"] == "VALIDATED"]
total_allocation = sum([float(s["allocation"].replace("%", "")) for s in catalog["strategies"]])

print("="*100)
print("FINAL CATALOG: S001-S007 SECTOR-SPECIFIC VARIATIONS")
print("="*100)
print(f"\nTotal Strategies: {len(catalog['strategies'])}")
print(f"🏆 GOLDEN: {len(golden)}")
print(f"✅ VALIDATED: {len(validated)}")
print(f"Total Allocation: {total_allocation}%")
print(f"Cash Reserve: {100 - total_allocation}%")

print("\n" + "="*100)
print("GOLDEN STRATEGIES (Priority Deployment)")
print("="*100)
for s in golden:
    print(f"\n{s['id']}: {s['name']}")
    print(f"   Sector: {s['sector']}")
    print(f"   Tickers: {', '.join(s['tickers'])}")
    print(f"   Performance: {s['test_wr']:.1f}% test / {s['val_wr']:.1f}% validate")
    print(f"   Trades: {s['total_trades']} | Allocation: {s['allocation']}")

print("\n" + "="*100)
print("VALIDATED STRATEGIES (Secondary Deployment)")
print("="*100)
for s in validated[:10]:  # Show first 10
    print(f"{s['id']}: {s['name']} — {s['test_wr']:.1f}% / {s['val_wr']:.1f}% — {s['allocation']}")

# Save to JSON
with open('/home/ubuntu/.openclaw/workspace/trade-algo-researcher/paper_trading_deployment.json', 'w') as f:
    json.dump(catalog, f, indent=2)

print("\n" + "="*100)
print("✅ Deployment file saved: paper_trading_deployment.json")
print("="*100)
