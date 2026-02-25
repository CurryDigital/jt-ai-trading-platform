#!/usr/bin/env python3
"""
PAPER TRADING DEPLOYMENT PACKAGE
S001-S007 Sector-Specific Variations
Properly sized allocations
"""
import json

print("="*100)
print("PAPER TRADING DEPLOYMENT PACKAGE")
print("S001-S007 Sector-Specific Strategies")
print("="*100)

# CAPITAL ALLOCATION FRAMEWORK
# Total: 100,000 HKD (per your setup)
# Reserve: 20% cash (20,000 HKD)
# Deployable: 80,000 HKD across strategies

TOTAL_CAPITAL = 100000
CASH_RESERVE_PCT = 20
CASH_RESERVE = TOTAL_CAPITAL * CASH_RESERVE_PCT / 100
DEPLOYABLE = TOTAL_CAPITAL - CASH_RESERVE

print(f"\n💰 CAPITAL ALLOCATION")
print(f"Total Capital: {TOTAL_CAPITAL:,.0f} HKD")
print(f"Cash Reserve ({CASH_RESERVE_PCT}%): {CASH_RESERVE:,.0f} HKD")
print(f"Deployable Capital: {DEPLOYABLE:,.0f} HKD")

# PRIORITY TIER DEPLOYMENT
tier1_strategies = [
    {
        "id": "S001-01",
        "name": "RSI_MR_HK_Banks",
        "tickers": ["0005.HK", "0939.HK", "1398.HK", "2388.HK", "3328.HK", "3988.HK"],
        "test_wr": 89.5,
        "val_wr": 87.8,
        "trades": 225,
        "allocation_pct": 15,  # 15% of deployable capital
        "max_concurrent": 2,
        "position_size": 7500  # per position
    },
    {
        "id": "S001-03", 
        "name": "RSI_MR_CN_Banks",
        "tickers": ["600036.SS", "601398.SS", "601939.SS", "601988.SS"],
        "test_wr": 82.4,
        "val_wr": 78.2,
        "trades": 135,
        "allocation_pct": 12,
        "max_concurrent": 2,
        "position_size": 4800
    },
    {
        "id": "S001-04",
        "name": "RSI_MR_CN_Other", 
        "tickers": ["600028.SS", "601088.SS", "601857.SS", "688008.SS"],
        "test_wr": 79.6,
        "val_wr": 66.6,
        "trades": 153,
        "allocation_pct": 10,
        "max_concurrent": 2,
        "position_size": 4000
    },
    {
        "id": "S007-01",
        "name": "Sector_Rotation_XLK_XLF",
        "tickers": ["XLK", "XLF"],
        "test_wr": 65.3,
        "val_wr": 64.1,
        "trades": 262,
        "allocation_pct": 10,
        "max_concurrent": 1,
        "position_size": 8000,
        "notes": "Hold XLK when ratio > SMA20, else cash"
    }
]

tier2_strategies = [
    {
        "id": "S001-02",
        "name": "RSI_MR_US_Consumer_Retail",
        "tickers": ["COST", "WMT"],
        "test_wr": 82.7,
        "val_wr": 71.2,
        "allocation_pct": 8,
        "max_concurrent": 1,
        "position_size": 6400
    },
    {
        "id": "S002-01",
        "name": "Trend_US_ETF_Index",
        "tickers": ["SPY", "QQQ"],
        "test_wr": 65.6,
        "val_wr": 68.4,
        "allocation_pct": 8,
        "max_concurrent": 1,
        "position_size": 6400
    },
    {
        "id": "S003-02",
        "name": "Panic_Reversal_US_ETF",
        "tickers": ["SPY", "QQQ", "IWM"],
        "test_wr": 67.9,
        "val_wr": 62.0,
        "allocation_pct": 6,
        "max_concurrent": 1,
        "position_size": 4800
    },
    {
        "id": "S001-09",
        "name": "RSI_MR_HK_Property",
        "tickers": ["0001.HK", "0002.HK"],
        "test_wr": 73.2,
        "val_wr": 70.7,
        "allocation_pct": 6,
        "max_concurrent": 1,
        "position_size": 4800
    },
    {
        "id": "S001-10",
        "name": "RSI_MR_US_Consumer_Staples",
        "tickers": ["PG"],
        "test_wr": 72.5,
        "val_wr": 71.4,
        "allocation_pct": 5,
        "max_concurrent": 1,
        "position_size": 4000
    },
    {
        "id": "S005-01",
        "name": "Vol_Breakout_Other",
        "tickers": ["ASML", "CL=F", "SI=F"],
        "test_wr": 71.0,
        "val_wr": 73.5,
        "allocation_pct": 5,
        "max_concurrent": 1,
        "position_size": 4000
    }
]

tier3_strategies = [
    {
        "id": "S002-02",
        "name": "Trend_US_Industrials",
        "tickers": ["GE", "LMT", "RTX"],
        "test_wr": 65.1,
        "val_wr": 63.4,
        "allocation_pct": 5,
        "max_concurrent": 1,
        "position_size": 4000
    },
    {
        "id": "S003-03",
        "name": "Panic_Reversal_US_Tech",
        "tickers": ["AAPL", "GOOGL", "META", "NVDA"],
        "test_wr": 67.7,
        "val_wr": 58.5,
        "allocation_pct": 5,
        "max_concurrent": 1,
        "position_size": 4000
    },
    {
        "id": "S004-02",
        "name": "Gap_Recovery_HK_Other",
        "tickers": ["0700.HK", "1810.HK"],
        "test_wr": 71.4,
        "val_wr": 55.0,
        "allocation_pct": 5,
        "max_concurrent": 1,
        "position_size": 4000
    }
]

# Calculate totals
tier1_total = sum([s["allocation_pct"] for s in tier1_strategies])
tier2_total = sum([s["allocation_pct"] for s in tier2_strategies])
tier3_total = sum([s["allocation_pct"] for s in tier3_strategies])
total_allocated = tier1_total + tier2_total + tier3_total

print(f"\n📊 TIER 1 DEPLOYMENT (🏆 GOLDEN) — {tier1_total}% of deployable capital")
print("="*100)
for s in tier1_strategies:
    capital = DEPLOYABLE * s["allocation_pct"] / 100
    print(f"\n{s['id']}: {s['name']}")
    print(f"   Tickers: {', '.join(s['tickers'])}")
    print(f"   Performance: {s['test_wr']:.1f}% test / {s['val_wr']:.1f}% validate | Trades: {s.get('trades', 'N/A')}")
    print(f"   Capital Allocation: {s['allocation_pct']}% = {capital:,.0f} HKD")
    print(f"   Position Size: {s['position_size']:,} HKD | Max Concurrent: {s['max_concurrent']}")
    if 'notes' in s:
        print(f"   Notes: {s['notes']}")

print(f"\n📊 TIER 2 DEPLOYMENT (✅ VALIDATED) — {tier2_total}% of deployable capital")
print("="*100)
for s in tier2_strategies:
    capital = DEPLOYABLE * s["allocation_pct"] / 100
    print(f"{s['id']}: {s['name']} — {s['test_wr']:.1f}% — {s['allocation_pct']}% ({capital:,.0f} HKD)")

print(f"\n📊 TIER 3 DEPLOYMENT (🟡 OPPORTUNISTIC) — {tier3_total}% of deployable capital")
print("="*100)
for s in tier3_strategies:
    capital = DEPLOYABLE * s["allocation_pct"] / 100
    print(f"{s['id']}: {s['name']} — {s['test_wr']:.1f}% — {s['allocation_pct']}% ({capital:,.0f} HKD)")

print(f"\n" + "="*100)
print("DEPLOYMENT SUMMARY")
print("="*100)
print(f"Tier 1 (GOLDEN): {tier1_total}% = {DEPLOYABLE * tier1_total / 100:,.0f} HKD")
print(f"Tier 2 (VALIDATED): {tier2_total}% = {DEPLOYABLE * tier2_total / 100:,.0f} HKD")
print(f"Tier 3 (OPPORTUNISTIC): {tier3_total}% = {DEPLOYABLE * tier3_total / 100:,.0f} HKD")
print(f"Total Allocated: {total_allocated}% = {DEPLOYABLE * total_allocated / 100:,.0f} HKD")
print(f"Cash Reserve: {CASH_RESERVE_PCT}% = {CASH_RESERVE:,.0f} HKD")
print(f"Total: 100% = {TOTAL_CAPITAL:,.0f} HKD")

# Create deployment config
deployment = {
    "account": {
        "total_capital_hkd": TOTAL_CAPITAL,
        "cash_reserve_pct": CASH_RESERVE_PCT,
        "cash_reserve_hkd": CASH_RESERVE,
        "deployable_hkd": DEPLOYABLE,
        "max_positions": 8,
        "max_correlated_positions": 2
    },
    "strategies": tier1_strategies + tier2_strategies + tier3_strategies,
    "risk_management": {
        "max_single_position_pct": 10,
        "max_sector_exposure_pct": 40,
        "stop_loss_default_pct": 5,
        "profit_target_default_pct": 10,
        "max_holding_days": 15
    },
    "monitoring": {
        "daily_pnl_report": True,
        "weekly_strategy_review": True,
        "signal_alert_immediate": True
    }
}

with open('/home/ubuntu/.openclaw/workspace/trade-algo-researcher/paper_trading_config.json', 'w') as f:
    json.dump(deployment, f, indent=2)

print(f"\n✅ Paper trading config saved: paper_trading_config.json")
print("="*100)
