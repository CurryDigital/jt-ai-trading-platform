# Hypothesis: Bitcoin Miner Capitulation Bottom Signal

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Crypto (BTC)  
**Direction:** Long  
**Horizon:** 1-3 months  
**Target Sharpe:** 1.5-2.5

---

## Core Idea

When Bitcoin price drops below all-in cost of production, miners become unprofitable and capitulate by selling inventory and shutting off machines. This creates forced selling that marks local price bottoms.

**Signal Components:**
1. Hash ribbons (30d MA crossing below 60d MA) = Miner stress
2. Price below estimated mining cost = Unprofitable
3. Hash rate drop = Machines going offline
4. Miner outflows spike = Inventory liquidation

---

## Academic Foundation

**Hayes (2019):** "Bitcoin Miner Capitulation" (Adaptive Capital)
- First systematic analysis of miner profitability cycles
- Demonstrated predictive power of hash ribbons

**Kaloudis (2021):** Coin Metrics miner research
- Miner balance sheet analysis
- Correlation between miner behavior and price bottoms

**Cambridge Bitcoin Electricity Consumption Index:**
- Global mining cost estimates
- Regional profitability variations

---

## Signal Construction

### Hash Ribbons
```python
def hash_ribbons(hash_rate_daily):
    """
    Generate hash ribbon indicator
    """
    ma30 = hash_rate_daily.rolling(30).mean()
    ma60 = hash_rate_daily.rolling(60).mean()
    
    # Capitulation: 30d MA crosses below 60d MA
    capitulation = (ma30 < ma60) & (ma30.shift(1) >= ma60.shift(1))
    
    # Recovery: 30d MA crosses back above 60d MA (buy signal)
    recovery = (ma30 > ma60) & (ma30.shift(1) <= ma60.shift(1))
    
    return capitulation, recovery
```

### All-In Mining Cost Estimate
```python
def mining_cost_estimate(difficulty, electricity_cost=0.06):
    """
    Estimate break-even BTC price for average miner
    """
    # Simplified model: hash rate, difficulty, electricity
    daily_btc_per_th = 1 / (difficulty * 2**32 / 1e12 / 86400)
    daily_revenue = daily_btc_per_th * btc_price
    daily_cost = electricity_cost * 24 * 0.05  # kWh per TH
    
    break_even_price = daily_cost / daily_btc_per_th
    return break_even_price
```

### Composite Signal
1. **Hash ribbon capitulation** (30d < 60d MA)
2. **Price < 90% of mining cost** (unprofitable)
3. **Hash rate dropping** (miners shutting off)
4. **Miner outflows spike** (selling inventory)

**Entry:** When 3 of 4 conditions met
**Exit:** Hash ribbon recovery or 3 months

---

## Historical Performance

### December 2018 Capitulation
- BTC dropped to $3,200
- Hash ribbons capitulated
- Recovery to $13,000 (300%+ gain)

### March 2020 Capitulation
- COVID crash to $3,800
- Brief hash ribbon signal
- Recovery to $60,000 (1500%+ gain)

### June 2022 Capitulation
- Luna collapse, BTC to $17,000
- Prolonged hash ribbon capitulation
- Recovery to $30,000+ (75%+ gain)

---

## Risk Factors

1. **ASIC efficiency:** New machines lower cost basis
2. **Electricity costs:** Vary by region significantly
3. **Halving events:** Instant 50% revenue drop
4. **False signals:** May capitate multiple times in bear market
5. **Opportunity cost:** May stay in capitulation for months

---

## Data Requirements

- Bitcoin hash rate (Glassnode, Coin Metrics)
- Bitcoin difficulty (blockchain data)
- Miner outflows (Glassnode)
- Electricity cost estimates (Cambridge index)

---

*Next step: Download hash rate data and backtest 2016-2024.*
