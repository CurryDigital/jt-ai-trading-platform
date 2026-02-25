# Information Arbitrage Framework

**Version:** 1.0  
**Date:** 2026-02-16  
**Researcher:** Senior Quant PhD  
**Objective:** Exploit velocity of price discovery + second-order effects  
**Scope:** **UNIVERSAL** — Applies to ANY sector, ANY disruption, ANY market regime

---

## ⚠️ Important Note: Examples Are Templates

The case studies in this document (Adobe, Panama, etc.) are **illustrative templates** demonstrating how to apply the frameworks. They are **not** the only scenarios to monitor.

**The edge is in SYSTEMATIC APPLICATION:**
- Apply Information Decay Analysis to **any** -10% move in **any** sector
- Apply DVS Scoring to **any** industry facing **any** disruption
- Apply Network Mapping to **any** interconnected system

**Think holistically, not narrowly.**

---

## Core Philosophy

**The Market is Slow.** Information does not diffuse instantly. It moves in waves:

1. **Primary Wave (T+0 to T+4hrs):** The directly affected asset prices immediately
2. **Secondary Wave (T+1 to T+5 days):** Peers, competitors, and substitutes price partially
3. **Tertiary Wave (T+1 to T+4 weeks):** Suppliers, customers, and network effects price
4. **Quaternary Wave (T+1 to T+3 months):** Macroeconomic and policy implications price

**Alpha = Positioning in Secondary and Tertiary waves before they break.**

---

## Framework 1: Information Decay Analysis

### The τ (Tau) Metric

Information decay τ measures how quickly a market fully prices new information.

```
τ = time for price to reach 90% of final adjustment
```

**Measurement Method:**
1. Identify information event (news, earnings, disruption)
2. Track price of directly affected asset (primary)
3. Track price of peer/competitor assets (secondary)
4. Calculate cross-correlation lag
5. τ_secondary = lag where correlation peaks

### Case Study Template: Adobe/AI Event

**Event:** AI video generation disrupts Adobe Creative Cloud moat  
**Date:** [To be filled with actual event date]  
**Primary Asset:** ADBE  
**Peak-to-Trough:** -43% ($464 → $263)

**Secondary Assets (SaaS Peers):**
| Ticker | Company | τ (days) | Price Impact | Status |
|--------|---------|----------|--------------|--------|
| ADSK | Autodesk | [Measure] | [Track] | Monitoring |
| INTU | Intuit | [Measure] | [Track] | Monitoring |
| CRM | Salesforce | [Measure] | [Track] | Monitoring |
| NOW | ServiceNow | [Measure] | [Track] | Monitoring |
| TEAM | Atlassian | [Measure] | [Track] | Monitoring |

**Tertiary Assets (Supply Chain):**
| Ticker | Company | Relationship | Expected τ | Status |
|--------|---------|--------------|------------|--------|
| VRT | Vertiv | Data center cooling | 2-4 weeks | Research |
| FN | Fabrinet | Optical components | 2-4 weeks | Research |
| MP | MP Materials | Rare earths | 4-8 weeks | Research |

### Trading Strategy

**Primary Wave:** Too fast (HFT territory) — Skip  
**Secondary Wave (τ = 1-5 days):** 
- Short peers with similar risk profiles
- Duration: 3-10 days
- Target: -5-15% on peers

**Tertiary Wave (τ = 2-4 weeks):**
- Long/short suppliers based on exposure
- Duration: 2-6 weeks
- Target: ±10-20% on suppliers

---

## Framework 2: Adobe Correlation Framework (Disruption Mapping)

### Disruption Vulnerability Score (DVS)

Score companies on four dimensions:

```python
DVS = (Human_Labor_Moat × AI_Replacement_Probability × 
       Customer_Concentration × Response_Slowness)
```

**1. Human-Labor Moat (0-10)**
- 10 = Pure human creativity (design, writing, coding)
- 5 = Hybrid human-AI workflow
- 0 = Already automated

**2. AI Replacement Probability (0-10)**
- 10 = AI can fully replace core product (text-to-video, code generation)
- 5 = AI augments but doesn't replace
- 0 = AI irrelevant to product

**3. Customer Concentration (0-10)**
- 10 = >50% revenue from vulnerable segment
- 5 = 20-50% exposure
- 0 = Diversified, resilient customer base

**4. Response Slowness (0-10)**
- 10 = No AI job postings, no partnerships, no product roadmap
- 5 = Some AI mentions but no delivery
- 0 = Already shipped AI features

### Scoring Interpretation

| DVS Range | Action | Expected Return | Time Horizon |
|-----------|--------|-----------------|--------------|
| 80-100 | Strong Short | -15-25% | 1-3 months |
| 60-79 | Moderate Short | -10-15% | 1-2 months |
| 40-59 | Watch List | -5-10% | Uncertain |
| 20-39 | Neutral | ±5% | — |
| 0-19 | AI Beneficiary | +10-20% | 2-6 months |

### Adobe Peer Analysis (Template)

| Company | Ticker | HL_Moat | AI_Prob | Cust_Conc | Response | DVS | Action |
|---------|--------|---------|---------|-----------|----------|-----|--------|
| Adobe | ADBE | 9 | 9 | 7 | 6 | 340 | Already priced |
| Autodesk | ADSK | 8 | 7 | 6 | 5 | 168 | **Short** |
| Intuit | INTU | 6 | 5 | 5 | 4 | 60 | Watch |
| Salesforce | CRM | 5 | 4 | 4 | 7 | 56 | Neutral |
| ServiceNow | NOW | 4 | 5 | 5 | 8 | 80 | **Short** |
| Atlassian | TEAM | 7 | 6 | 6 | 4 | 101 | **Strong Short** |

---

## Framework 3: Geopolitical Network Effects

### The Panama Case Study

**Event:** CK Hutchison vs. Panama port dispute  
**Network Type:** Physical infrastructure (ports)  
**Propagation Mechanism:** Route changes, rate volatility, supply chain disruption

**Network Mapping:**

```
Primary Node: CK Hutchison (port operator)
    ↓ exit → capacity reduction
Secondary Nodes: Alternative port operators
    - Maersk/APM Terminals
    - COSCO Shipping Ports
    - Local Panama operators
    ↓ capacity shift → rate changes
Tertiary Nodes: Shipping lines
    - Maersk Line
    - MSC
    - COSCO
    ↓ rate volatility → cargo diversion
Quaternary Nodes: Cargo owners
    - US Gulf exporters
    - Asian importers
    - LNG shippers
    ↓ supply disruption → inventory builds
Quinary Nodes: Regional economies
    - Panama GDP
    - US Gulf Coast trade
    - Asian manufacturing
```

### Impact Prediction Matrix

| Node Type | Assets | Impact Probability | Expected τ | 30-Day Outlook |
|-----------|--------|-------------------|------------|----------------|
| Primary | CK Hutchison | High (100%) | T+0 | Exit complete |
| Secondary | Maersk, COSCO | High (80%) | T+7-14 days | +10-15% rate |
| Tertiary | Container lines | Medium (60%) | T+14-30 days | ±5-10% volatility |
| Quaternary | LNG shippers | Low-Med (40%) | T+30-60 days | Route changes |

### Leading Indicators

**Before headlines hit:**
1. Legal filings in maritime courts
2. Port authority meeting minutes
3. Shipping rate futures (FFA)
4. Container booking patterns
5. Insurance premium changes

**Information sources:**
- Lloyd's List (maritime intelligence)
- Drewry (shipping consultants)
- Freightos (rate platform)
- Port authorities (public records)

---

## Framework 4: Predictive Edge ("One Step Earlier")

### The Job Postings Signal

**Hypothesis:** Job postings for AI roles predict 6-12 month product launches.

**Method:**
1. Scrape LinkedIn/Bright for AI-related job postings
2. Track by company and role type
3. Correlate with subsequent product announcements
4. Build lead-lag model

**Signal Types:**
- **Strong:** "Principal AI Scientist — Video Generation" (specific, senior)
- **Medium:** "Machine Learning Engineer — Creative Tools" (relevant)
- **Weak:** "Data Analyst" (too generic)

**Validation:**
- Measure time from posting to product launch
- Track accuracy across historical data
- Weight by role seniority and specificity

### The Patent Signal

**Method:**
1. Monitor USPTO filings for AI-related patents
2. Track assignee companies
3. Classify by technology area (video, NLP, audio)
4. Predict 12-24 month product roadmaps

**Information edge:** 6-18 months before public product launch

### The Conference Signal

**Method:**
1. Monitor academic conference submissions (NeurIPS, ICML, CVPR)
2. Track industry sponsorships
3. Identify research focus shifts
4. Predict 6-12 month industry directions

---

## Output Format

Every analysis must include:

### 1. Event Summary
- What happened
- When
- Primary asset impact

### 2. Information Decay Analysis
- τ_primary (if measurable)
- τ_secondary (estimated)
- τ_tertiary (estimated)

### 3. Network Effect Mapping
- Directly affected assets
- Secondary beneficiaries/victims
- Tertiary network effects

### 4. 30-Day Outlook
| Asset | Direction | Impact Probability | Expected Return | Entry Timing |
|-------|-----------|-------------------|-----------------|--------------|
| [Ticker] | Long/Short | High/Med/Low | ±X% | T+N days |

### 5. Predictive Edge
- What signals preceded this event?
- How do we spot the next one earlier?
- Leading indicators to monitor

### 6. Risk Factors
- What could invalidate this thesis?
- Black swan scenarios
- Correlation breakdown risks

---

## Implementation Notes

### Data Requirements

| Data Type | Source | Frequency | Cost |
|-----------|--------|-----------|------|
| Job postings | LinkedIn, Bright | Daily | Free/low |
| Patents | USPTO API | Weekly | Free |
| Shipping rates | Freightos, Drewry | Daily | $$$ |
| Legal filings | Court APIs | Event | Free |
| News sentiment | RavenPack | Real-time | $$$ |
| Price data | IBKR | Real-time | Free |

### Integration with ARASO

The Information Arbitrage framework overlays on ARASO:

1. **Factor model** identifies residual deviations
2. **Information decay analysis** explains WHY residuals are moving
3. **Network effects** predict WHERE residuals will move next
4. **HMM** filters whether to trade (mean-reverting vs information-driven)
5. **30-day outlook** sets position sizing and duration

---

*Framework Version: 1.0*  
*Next Update: After Adobe case study completion*
