# HKEX IPO Data Sources - Research Guide

**Date:** 2026-02-20  
**Purpose:** Data acquisition options for HK IPO Post-Listing Momentum strategy  
**Data Needed:** IPO calendar, prospectus data (oversubscription, lockup dates, greenshoe), historical IPO performance

---

## 🎯 Data Requirements Recap

For the **HK IPO Post-Listing Momentum** strategy, you need:

| Data Point | Purpose | Frequency |
|------------|---------|-----------|
| **IPO Calendar** | Upcoming listings for live trading | Real-time |
| **Prospectus Data** | Oversubscription ratio, lockup dates, cornerstone investors | Per IPO |
| **Greenshoe Exercise** | Stabilization period tracking | Event-driven |
| **Historical IPO Prices** | OHLCV for backtesting | Historical |
| **Listing Date / First Trade** | Entry signal timing | Per IPO |

---

## Option 1: HKEX Official Website (FREE)

### URL: https://www.hkex.com.hk/Market-Data/Securities-Prices/Upcoming-IPO

**Available Data:**
- ✅ IPO calendar (upcoming listings)
- ✅ Listing date
- ✅ Offer price range
- ✅ Number of shares offered
- ✅ Prospectus PDF links

**Scraping Approach:**
```python
import requests
from bs4 import BeautifulSoup

url = "https://www.hkex.com.hk/Market-Data/Securities-Prices/Upcoming-IPO"
response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
soup = BeautifulSoup(response.content, 'html.parser')

# Parse IPO table
ipo_table = soup.find('table', {'class': 'ipo-table'})
```

**Pros:**
- Free
- Official source
- Real-time updates

**Cons:**
- Requires web scraping
- No historical data API
- Rate limiting

---

## Option 2: HKEXnews (FREE - Announcements)

### URL: https://www.hkexnews.hk

**Available Data:**
- ✅ All regulatory filings (prospectuses)
- ✅ IPO announcements
- ✅ Listing documents
- ✅ Historical filings (years of data)

**Data Points in Prospectus:**
- Oversubscription ratio (retail/institutional)
- Cornerstone investor allocation
- Lock-up period (typically 6-12 months)
- Greenshoe option details
- Sponsor information

**Scraping Approach:**
```python
# Search for IPO announcements
search_url = "https://www.hkexnews.hk/search/titlesearch.xhtml"
# Filter by: "New Listing" announcements
```

**Pros:**
- Free
- Comprehensive regulatory data
- Historical records available

**Cons:**
- PDF parsing required for prospectuses
- No structured API
- Manual data extraction

---

## Option 3: Yahoo Finance / Google Finance (FREE)

**Available Data:**
- ✅ Historical OHLCV after listing
- ✅ Market cap
- ✅ Basic company info

**Not Available:**
- ❌ IPO calendar
- ❌ Oversubscription data
- ❌ Prospectus details

**Use Case:** Price data for backtesting once you know the ticker

```python
import yfinance as yf

# Get historical data for recent IPO
 ticker = '9999.HK'  # Example
 data = yf.download(ticker, start='2024-01-01', end='2024-12-31')
```

---

## Option 4: Bloomberg API ($$$)

**Available Data:**
- ✅ Complete IPO calendar
- ✅ Oversubscription ratios
- ✅ Cornerstone investor details
- ✅ Historical IPO database
- ✅ Real-time updates

**Cost:** $2,000-5,000/month (professional terminal)

**API Endpoint Example:**
```python
# Bloomberg Terminal API
import blpapi

# Request IPO calendar
refDataService = session.getService("//blp/refdata")
request = refDataService.createRequest("ReferenceDataRequest")
request.append("securities", "HK IPO Calendar")
```

**Pros:**
- Comprehensive data
- Structured API
- Historical + real-time

**Cons:**
- Expensive
- Requires terminal license

---

## Option 5: Refinitiv Eikon / Datastream ($$)

**Available Data:**
- ✅ IPO database (historical + upcoming)
- ✅ Pricing data
- ✅ Fundamental data
- ✅ News sentiment

**Cost:** $1,000-3,000/month

**Pros:**
- Good historical coverage
- API available
- More affordable than Bloomberg

**Cons:**
- Still expensive
- Limited real-time for IPOs

---

## Option 6: East Money / Sina Finance (FREE - Chinese)

### URLs:
- https://emweb.securities.eastmoney.com/PC_HSF10/CompanySurvey/Index
- https://finance.sina.com.cn/stock/hkstock/ipo/

**Available Data:**
- ✅ HK IPO calendar
- ✅ Oversubscription ratios (Chinese retail interest)
- ✅ Company fundamentals
- ✅ News/announcements

**Language:** Chinese (requires translation)

**Pros:**
- Free
- Good retail sentiment data
- Real-time updates

**Cons:**
- Chinese language
- Requires scraping
- Less reliable than official sources

---

## Option 7: Web Scraping + Database Build (RECOMMENDED)

**Approach:** Build your own database by scraping HKEX

### Step-by-Step:

1. **Scrape IPO Calendar (Daily)**
```python
# cron job: daily at 18:00 HKT
# Scrape https://www.hkex.com.hk/Market-Data/Securities-Prices/Upcoming-IPO
# Store in: gold.hk_ipo_calendar
```

2. **Download Prospectuses (Event-driven)**
```python
# When new IPO announced:
# Download PDF from HKEXnews
# Extract: oversubscription, lockup, greenshoe
# Store in: gold.hk_ipo_details
```

3. **Track Listing Performance (Daily)**
```python
# After listing:
# Get OHLCV from yfinance
# Calculate Day 1-30 returns
# Store in: gold.hk_ipo_performance
```

### Database Schema:
```sql
-- IPO Calendar
gold.hk_ipo_calendar (
    ticker VARCHAR(10),
    company_name VARCHAR(255),
    listing_date DATE,
    offer_price DECIMAL(10,2),
    shares_offered BIGINT,
    market_cap_hkd DECIMAL(15,2),
    sector VARCHAR(50),
    sponsor VARCHAR(100),
    status VARCHAR(20),  -- upcoming / listed / withdrawn
    created_at TIMESTAMP
);

-- IPO Details from Prospectus
gold.hk_ipo_details (
    ticker VARCHAR(10),
    retail_oversubscription DECIMAL(5,2),  -- 100x = 100.00
    institutional_oversubscription DECIMAL(5,2),
    cornerstone_allocation_pct DECIMAL(5,2),
    lockup_period_days INT,
    greenshoe_exercised BOOLEAN,
    greenshoe_pct DECIMAL(5,2),
    stabilization_manager VARCHAR(100),
    extracted_at TIMESTAMP
);

-- IPO Performance
gold.hk_ipo_performance (
    ticker VARCHAR(10),
    day_1_return DECIMAL(8,4),
    day_3_return DECIMAL(8,4),
    day_5_return DECIMAL(8,4),
    day_10_return DECIMAL(8,4),
    day_20_return DECIMAL(8,4),
    day_30_return DECIMAL(8,4),
    max_day_30_return DECIMAL(8,4),
    min_day_30_return DECIMAL(8,4),
    volume_day_1 BIGINT,
    avg_volume_day_2_5 BIGINT
);
```

---

## 🎯 RECOMMENDED APPROACH

### Phase 1: Quick Start (This Week)
1. **Manual scrape** HKEX website for 2020-2024 IPOs
2. **Download** 20-30 recent prospectus PDFs
3. **Extract** key data manually (oversubscription, lockup)
4. **Get** OHLCV from yfinance for backtesting

### Phase 2: Automation (Next 2 Weeks)
1. **Build** Python scraper for HKEX calendar
2. **Set up** cron job (daily 18:00 HKT)
3. **Create** PDF parser for prospectus extraction
4. **Populate** database with historical data

### Phase 3: Live Trading (Ongoing)
1. **Daily** scraper runs automatically
2. **Alert** when new IPO meets criteria
3. **Track** performance post-listing
4. **Update** strategy parameters

---

## 💰 Cost Comparison

| Source | Cost | Effort | Data Quality | Recommendation |
|--------|------|--------|--------------|----------------|
| HKEX Website | FREE | High | Good | ✅ Start here |
| HKEXnews | FREE | High | Excellent | ✅ For prospectuses |
| Bloomberg | $$$ | Low | Excellent | ❌ Too expensive |
| Refinitiv | $$ | Low | Good | ❌ Not worth it |
| East Money | FREE | Medium | Fair | ⚠️ Chinese only |
| Build Your Own | FREE | Very High | Excellent | ✅ Long-term solution |

---

## 🚀 IMMEDIATE ACTION

**I can help you:**

1. **Scrape HKEX** for 2020-2024 IPO calendar (Python script)
2. **Download** prospectus PDFs for top 50 recent IPOs
3. **Extract** key data points (oversubscription, lockup)
4. **Build** database schema and populate

**Time Estimate:**
- Scraper: 2-3 hours
- Data collection: 1 day
- Backtest: 2-3 hours

**Ready to start building the scraper?**
