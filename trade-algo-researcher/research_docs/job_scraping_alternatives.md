# Job Scraping Alternatives to LinkedIn

**Problem:** LinkedIn API is enterprise-only, not available to individuals

**Solution:** Multi-source approach using freely available alternatives

---

## Recommended Stack

### 1. Indeed Publisher API (Primary)
**Best for:** Broad coverage, established companies
**Cost:** Free for non-commercial use
**Register:** https://www.indeed.com/publisher

**Pros:**
- Free API key for individuals
- Millions of listings
- Good tech coverage
- JSON/XML output

**Cons:**
- Rate limits (varies by key)
- No salary data in free tier
- Limited historical data

### 2. Direct Company Career Page Scraping (Secondary)
**Best for:** Specific target companies (Adobe, Autodesk, etc.)
**Cost:** Free
**Method:** HTTP requests + HTML parsing

**Pros:**
- Most accurate/up-to-date
- No API limits (just rate limiting)
- Company-specific formatting
- Can detect patterns

**Cons:**
- Requires maintenance (site changes)
- Rate limiting by company
- One scraper per company format

**Target Companies for DVS Tracking:**
```python
watchlist = [
    'careers.adobe.com',
    'careers.autodesk.com',
    'www.atlassian.com/company/careers',
    'www.salesforce.com/company/careers',
    'www.servicenow.com/careers',
    'careers.intuit.com',
]
```

### 3. GitHub Jobs API (Tertiary - Tech Only)
**Best for:** Engineering/AI roles at tech companies
**Cost:** Free, no auth
**Endpoint:** `https://jobs.github.com/positions.json`

**Pros:**
- Completely free
- No registration
- Tech-focused
- Good for AI/ML roles

**Cons:**
- Limited companies
- Only tech roles
- Being phased out (deprecated)

### 4. Alternative Aggregators

**SimplyHired**
- Has API for partners
- Can scrape with proper headers

**ZipRecruiter**
- API available for developers
- Requires application

**Glassdoor**
- **DO NOT SCRAPE** — aggressively blocks
- Use their official API only (enterprise)

---

## Implementation Strategy

### Tier 1: High-Priority Targets (Direct Scraping)
Manually scrape career pages of:
- All DVS-tracked companies (Adobe, Autodesk, Atlassian, etc.)
- Weekly frequency
- Focus on: AI, generative, ML, LLM keywords

### Tier 2: Broad Discovery (Indeed API)
- Query for: "generative AI", "LLM", "AI researcher"
- Filter by: Senior/Principal/Staff levels
- Track companies hiring aggressively

### Tier 3: Validation (Multi-source Cross-check)
- If Indeed shows spike in Adobe AI hiring
- Verify on Adobe careers page
- Check GitHub Jobs for engineering roles
- Confirm signal strength

---

## Sample Implementation

### Indeed API Query
```python
import requests

def search_indeed(api_key, query, location="United States"):
    url = "http://api.indeed.com/ads/apisearch"
    params = {
        'publisher': api_key,
        'q': query,  # "generative AI" OR "LLM"
        'l': location,
        'sort': 'date',
        'limit': 25,
        'format': 'json'
    }
    response = requests.get(url, params=params)
    return response.json()
```

### Direct Career Page Scraping
```python
import requests
from bs4 import BeautifulSoup

def scrape_adobe_careers():
    url = "https://careers.adobe.com/us/en/search-results"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    jobs = []
    for job in soup.find_all('div', class_='job-card'):
        title = job.find('h3').text
        if any(kw in title.lower() for kw in ['ai', 'machine learning', 'generative']):
            jobs.append({
                'title': title,
                'date': job.find('span', class_='job-date').text
            })
    
    return jobs
```

---

## Recommended Next Steps

1. **Register for Indeed Publisher API**
   - Get free API key
   - Start with 100 queries/day limit
   - Upgrade if needed

2. **Build Company-Specific Scrapers**
   - Start with Adobe, Autodesk, Atlassian
   - Focus on AI/ML job titles
   - Run weekly

3. **Create Unified Database**
   - Combine Indeed + direct scraping results
   - Track: company, title, date, seniority, keywords
   - Calculate hiring velocity (jobs/week)

4. **Signal Generation**
   - Spike in AI hiring + High DVS = Short candidate
   - Sustained AI hiring + Low DVS = Long candidate (adaptation)
   - Principal+ level hires = 6-9 month product timeline

---

## Files Updated

- `strategies/job_scraper.py` — Multi-source implementation
- `data/job_sources.json` — API keys and endpoints config

---

*Approach: Indeed for discovery, direct scraping for validation, GitHub as backup*
