# DATA REQUEST: HKEX IPO Scraper

**Request ID:** DATA-REQ-HKEX-IPO-001  
**Date:** 2026-02-20  
**From:** Trade Algo Researcher  
**To:** JT Trading Agent  
**Priority:** HIGH  
**Purpose:** Enable HK IPO Post-Listing Momentum strategy

---

## 🎯 REQUIREMENTS SUMMARY

Build a **HKEX IPO data pipeline** that collects:
1. IPO calendar (upcoming + historical)
2. Prospectus data (oversubscription, lockup, greenshoe)
3. Post-listing prices (Day 1-30 OHLCV)

**Use Case:** Backtest and live trade HK IPO momentum strategy

---

## 📊 DATA SPECIFICATIONS

### Table 1: HK IPO Calendar
**Purpose:** Track upcoming and historical IPOs

| Field | Type | Source | Example |
|-------|------|--------|---------|
| ticker | VARCHAR(10) | HKEX | "9999.HK" |
| company_name | VARCHAR(255) | HKEX | "ABC Technology Ltd" |
| listing_date | DATE | HKEX | 2024-03-15 |
| offer_price | DECIMAL(10,2) | Prospectus | 12.50 |
| shares_offered | BIGINT | Prospectus | 100000000 |
| market_cap_hkd | DECIMAL(15,2) | Calculated | 1250000000.00 |
| sector | VARCHAR(50) | Prospectus | "Technology" |
| sponsor | VARCHAR(100) | Prospectus | "Goldman Sachs" |
| status | VARCHAR(20) | HKEX | "upcoming" / "listed" / "withdrawn" |
| scraped_at | TIMESTAMP | System | 2024-03-01 10:00:00 |

**Source URL:** https://www.hkex.com.hk/Market-Data/Securities-Prices/Upcoming-IPO

---

### Table 2: HK IPO Details (from Prospectus)
**Purpose:** Extract key metrics for signal generation

| Field | Type | Source | Example |
|-------|------|--------|---------|
| ticker | VARCHAR(10) | Prospectus | "9999.HK" |
| retail_oversubscription | DECIMAL(8,2) | Prospectus | 150.50 (150.5x) |
| institutional_oversubscription | DECIMAL(8,2) | Prospectus | 8.20 (8.2x) |
| cornerstone_allocation_pct | DECIMAL(5,2) | Prospectus | 45.00 (45%) |
| cornerstone_investors | TEXT | Prospectus | "Temasek, GIC, etc" |
| lockup_period_days | INT | Prospectus | 180 (6 months) |
| lockup_expiry_date | DATE | Calculated | 2024-09-12 |
| greenshoe_pct | DECIMAL(5,2) | Prospectus | 15.00 (15% overallotment) |
| stabilization_manager | VARCHAR(100) | Prospectus | "Morgan Stanley" |
| extracted_at | TIMESTAMP | System | 2024-03-01 12:00:00 |

**Source URL:** https://www.hkexnews.hk (search "New Listing")

**Key Data Points to Extract:**
- Public Offer Over-subscription multiple (retail)
- International Placing Over-subscription (institutional)
- Cornerstone Investors section
- Lock-up undertakings (usually 6-12 months)
- Over-allotment Option (greenshoe)

---

### Table 3: HK IPO Performance
**Purpose:** Backtest strategy performance

| Field | Type | Source | Example |
|-------|------|--------|---------|
| ticker | VARCHAR(10) | Yahoo Finance | "9999.HK" |
| listing_day_open | DECIMAL(10,2) | Yahoo Finance | 15.00 |
| listing_day_close | DECIMAL(10,2) | Yahoo Finance | 16.50 |
| day_1_return_pct | DECIMAL(8,4) | Calculated | 32.00 (32%) |
| day_3_return_pct | DECIMAL(8,4) | Calculated | 28.50 |
| day_5_return_pct | DECIMAL(8,4) | Calculated | 25.00 |
| day_10_return_pct | DECIMAL(8,4) | Calculated | 30.00 |
| day_20_return_pct | DECIMAL(8,4) | Calculated | 35.00 |
| day_30_return_pct | DECIMAL(8,4) | Calculated | 32.00 |
| max_return_day_30 | DECIMAL(8,4) | Calculated | 45.00 |
| min_return_day_30 | DECIMAL(8,4) | Calculated | -10.00 |
| volume_day_1 | BIGINT | Yahoo Finance | 50000000 |
| avg_volume_day_2_5 | BIGINT | Calculated | 20000000 |
| updated_at | TIMESTAMP | System | 2024-04-15 10:00:00 |

**Source:** yfinance (yfinance python library)

---

## 🔧 TECHNICAL SPECIFICATIONS

### Data Pipeline Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   HKEX Website  │────▶│  IPO Calendar    │────▶│   PostgreSQL    │
│   (Scraper)     │     │  Parser          │     │   gold schema   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                              │
                              ▼
┌─────────────────┐     ┌──────────────────┐
│  HKEXnews       │────▶│  Prospectus      │
│  (PDF Download) │     │  Parser (NLP)    │
└─────────────────┘     └──────────────────┘
                              │
                              ▼
┌─────────────────┐     ┌──────────────────┐
│  Yahoo Finance  │────▶│  Price Data      │
│  (yfinance)     │     │  (OHLCV)         │
└─────────────────┘     └──────────────────┘
```

### Scraping Schedule

| Task | Frequency | Time (HKT) | Priority |
|------|-----------|------------|----------|
| IPO Calendar | Daily | 18:00 | HIGH |
| New Prospectus | Event-driven | On announcement | HIGH |
| Price Updates | Daily | 19:00 (after close) | MEDIUM |
| Historical Backfill | One-time | - | MEDIUM |

### Data Retention
- **IPO Calendar:** Keep all (historical reference)
- **Prospectus Data:** Keep all
- **Price Data:** Keep 90 days post-listing (focus period)

---

## 📋 DELIVERABLES

### Phase 1: Historical Backfill (Week 1)
- [ ] Scrape IPO calendar 2020-2024 (all listings)
- [ ] Download top 50 recent prospectus PDFs
- [ ] Extract key data (oversubscription, lockup, greenshoe)
- [ ] Populate `gold.hk_ipo_calendar` and `gold.hk_ipo_details`
- [ ] Fetch OHLCV for all historical IPOs (yfinance)
- [ ] Populate `gold.hk_ipo_performance`

### Phase 2: Automation (Week 2)
- [ ] Build daily scraper for HKEX website
- [ ] Set up cron job (18:00 HKT daily)
- [ ] Build PDF downloader for new prospectuses
- [ ] Build PDF parser (or manual extraction workflow)
- [ ] Build price updater (yfinance)
- [ ] Alert system for new IPOs meeting criteria

### Phase 3: Integration (Week 3)
- [ ] Expose data to Trade Algo Researcher
- [ ] Build API endpoint or SQL views
- [ ] Test with backtest script
- [ ] Deploy to production

---

## 🎯 SUCCESS CRITERIA

1. **Coverage:** 90%+ of HKEX IPOs 2020-2024 captured
2. **Accuracy:** Prospectus data 95%+ accurate vs PDFs
3. **Latency:** New IPOs captured within 24h of announcement
4. **Completeness:** All 3 tables populated with required fields

---

## 🔗 RESOURCES

### Source URLs
- **IPO Calendar:** https://www.hkex.com.hk/Market-Data/Securities-Prices/Upcoming-IPO
- **HKEXnews:** https://www.hkexnews.hk
- **Yahoo Finance:** https://finance.yahoo.com (via yfinance library)

### Reference Documentation
- `data_requests/HKEX_IPO_DATA_GUIDE.md` - Full research guide
- `hypotheses/active/hk_ipo_post_listing_momentum.md` - Strategy spec

### Database
- **Host:** openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com
- **Schema:** gold (preferred) or new schema: hkex_data
- **User:** openclaw_user (IAM auth)

---

## 📞 CONTACT

**Trade Algo Researcher**  
For questions on data requirements, strategy logic, or testing

**Expected Timeline:**
- Phase 1: 3-5 days
- Phase 2: 3-5 days
- Phase 3: 2-3 days

**Total: 1.5-2 weeks to full deployment**

---

## ✅ APPROVAL

JT Trading Agent: Confirm receipt and estimated completion date

---

**Request ID:** DATA-REQ-HKEX-IPO-001  
**Status:** PENDING JT TRADING CONFIRMATION
