#!/usr/bin/env python3
"""
Job Postings Scraper — Predictive Edge Module

Scrapes LinkedIn and Bright for AI-related job postings at vulnerable companies.
Provides 6-12 month leading indicator for AI disruption events.

Usage:
    python job_scraper.py --company "Adobe" --keywords "AI,generative,machine learning"
    python job_scraper.py --watchlist job_watchlist.json --days 30
"""

import argparse
import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class JobPosting:
    """Structured job posting record."""
    company: str
    title: str
    location: str
    description: str
    date_posted: datetime
    seniority: str  # Entry, Mid, Senior, Principal, Director
    ai_relevance_score: float  # 0-1
    specific_technologies: List[str]  # e.g., ["LLM", "diffusion", "transformer"]
    url: str
    source: str  # linkedin, bright, indeed
    scraped_at: datetime


class JobScorer:
    """Score job postings for AI disruption relevance."""
    
    # Seniority levels (higher = more significant)
    SENIORITY_WEIGHTS = {
        'entry': 1,
        'junior': 1,
        'mid': 2,
        'senior': 3,
        'staff': 4,
        'principal': 5,
        'director': 5,
        'head': 5,
        'vp': 4,
        'cto': 5
    }
    
    # AI-specific technologies (higher = more disruption potential)
    TECH_INDICATORS = {
        'llm': 5,
        'large language model': 5,
        'generative ai': 5,
        'generative': 4,
        'diffusion': 5,
        'transformer': 4,
        'gpt': 5,
        'stable diffusion': 5,
        'midjourney': 5,
        'text-to-image': 5,
        'text-to-video': 5,
        'text-to-3d': 5,
        'neural rendering': 4,
        'foundation model': 5,
        'autogpt': 4,
        'agent': 3,
        'copilot': 3,
        'ai researcher': 5,
        'ai scientist': 5,
        'deep learning': 3,
        'machine learning': 2,
        'computer vision': 3,
        'nlp': 3,
        'multimodal': 4
    }
    
    # Role categories
    ROLE_CATEGORIES = {
        'research': ['researcher', 'scientist', 'research scientist', 'ai researcher'],
        'engineering': ['engineer', 'developer', 'architect'],
        'product': ['product manager', 'pm', 'product owner'],
        'leadership': ['director', 'head', 'vp', 'cto', 'chief']
    }
    
    def score_posting(self, title: str, description: str) -> Dict:
        """
        Score a job posting for AI disruption relevance.
        """
        title_lower = title.lower()
        desc_lower = description.lower()
        combined = title_lower + " " + desc_lower
        
        # 1. Seniority score
        seniority = 'mid'  # default
        seniority_score = 2
        for level, weight in self.SENIORITY_WEIGHTS.items():
            if level in title_lower:
                seniority = level
                seniority_score = weight
                break
        
        # 2. Technology score
        tech_matches = []
        tech_score = 0
        for tech, weight in self.TECH_INDICATORS.items():
            if tech in combined:
                tech_matches.append(tech)
                tech_score += weight
        
        # Normalize tech score (max ~30)
        tech_score = min(tech_score / 10, 3)
        
        # 3. Role category
        role_category = 'engineering'
        for category, keywords in self.ROLE_CATEGORIES.items():
            if any(kw in title_lower for kw in keywords):
                role_category = category
                break
        
        # 4. Calculate final AI relevance score (0-1)
        # Formula: seniority (0.4) + tech specificity (0.5) + role type (0.1)
        role_multiplier = 1.0 if role_category == 'research' else 0.8 if role_category == 'leadership' else 0.6
        
        ai_relevance = min(
            (seniority_score / 5) * 0.4 + 
            (tech_score / 3) * 0.5 + 
            role_multiplier * 0.1,
            1.0
        )
        
        # 5. Predictive timeline (months until potential product launch)
        if seniority_score >= 5 and tech_score >= 2.5:
            timeline = "6-9 months"
        elif seniority_score >= 4 and tech_score >= 2:
            timeline = "9-12 months"
        elif seniority_score >= 3 and tech_score >= 1.5:
            timeline = "12-18 months"
        else:
            timeline = "18-24 months"
        
        return {
            'seniority': seniority,
            'seniority_score': seniority_score,
            'technologies': tech_matches,
            'tech_score': tech_score,
            'role_category': role_category,
            'ai_relevance': round(ai_relevance, 2),
            'predictive_timeline': timeline,
            'signal_strength': 'STRONG' if ai_relevance > 0.7 else 'MODERATE' if ai_relevance > 0.5 else 'WEAK'
        }


#!/usr/bin/env python3
"""
Job Postings Scraper — Multi-Source Predictive Edge

Uses Indeed API + Direct Career Page Scraping (LinkedIn alternatives)
Provides 6-12 month leading indicator for AI disruption events.

Usage:
    python job_scraper.py --source indeed --company "Adobe" --api-key YOUR_KEY
    python job_scraper.py --source direct --company "adobe"
    python job_scraper.py --watchlist job_watchlist.json --source hybrid
"""

import argparse
import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import logging
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class JobPosting:
    """Structured job posting record."""
    company: str
    title: str
    location: str
    description: str
    date_posted: datetime
    seniority: str
    ai_relevance_score: float
    specific_technologies: List[str]
    url: str
    source: str  # indeed, direct, github
    scraped_at: datetime


class JobScorer:
    """Score job postings for AI disruption relevance."""
    
    # Seniority levels (higher = more significant)
    SENIORITY_WEIGHTS = {
        'entry': 1, 'junior': 1, 'mid': 2, 'senior': 3,
        'staff': 4, 'principal': 5, 'director': 5, 'head': 5, 'vp': 4, 'cto': 5
    }
    
    # AI-specific technologies
    TECH_INDICATORS = {
        'llm': 5, 'large language model': 5, 'generative ai': 5, 'generative': 4,
        'diffusion': 5, 'transformer': 4, 'gpt': 5, 'stable diffusion': 5,
        'midjourney': 5, 'text-to-image': 5, 'text-to-video': 5, 'text-to-3d': 5,
        'neural rendering': 4, 'foundation model': 5, 'autogpt': 4, 'agent': 3,
        'copilot': 3, 'ai researcher': 5, 'ai scientist': 5, 'deep learning': 3,
        'machine learning': 2, 'computer vision': 3, 'nlp': 3, 'multimodal': 4
    }
    
    def score_posting(self, title: str, description: str) -> Dict:
        """Score a job posting for AI disruption relevance."""
        title_lower = title.lower()
        desc_lower = description.lower()
        combined = title_lower + " " + desc_lower
        
        # Seniority score
        seniority = 'mid'
        seniority_score = 2
        for level, weight in self.SENIORITY_WEIGHTS.items():
            if level in title_lower:
                seniority = level
                seniority_score = weight
                break
        
        # Technology score
        tech_matches = []
        tech_score = 0
        for tech, weight in self.TECH_INDICATORS.items():
            if tech in combined:
                tech_matches.append(tech)
                tech_score += weight
        
        tech_score = min(tech_score / 10, 3)
        
        # Role category
        role_category = 'engineering'
        if any(kw in title_lower for kw in ['researcher', 'scientist', 'research scientist']):
            role_category = 'research'
        elif any(kw in title_lower for kw in ['director', 'head', 'vp', 'cto']):
            role_category = 'leadership'
        
        # AI relevance score
        role_multiplier = 1.0 if role_category == 'research' else 0.8 if role_category == 'leadership' else 0.6
        ai_relevance = min((seniority_score / 5) * 0.4 + (tech_score / 3) * 0.5 + role_multiplier * 0.1, 1.0)
        
        # Timeline prediction
        if seniority_score >= 5 and tech_score >= 2.5:
            timeline = "6-9 months"
        elif seniority_score >= 4 and tech_score >= 2:
            timeline = "9-12 months"
        elif seniority_score >= 3 and tech_score >= 1.5:
            timeline = "12-18 months"
        else:
            timeline = "18-24 months"
        
        return {
            'seniority': seniority,
            'seniority_score': seniority_score,
            'technologies': tech_matches,
            'tech_score': tech_score,
            'role_category': role_category,
            'ai_relevance': round(ai_relevance, 2),
            'predictive_timeline': timeline,
            'signal_strength': 'STRONG' if ai_relevance > 0.7 else 'MODERATE' if ai_relevance > 0.5 else 'WEAK'
        }


class IndeedAPIClient:
    """Indeed Publisher API client."""
    
    BASE_URL = "http://api.indeed.com/ads/apisearch"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def search(self, query: str, company: str = None, location: str = "United States", 
               limit: int = 25) -> List[Dict]:
        """Search Indeed jobs."""
        params = {
            'publisher': self.api_key,
            'q': query,
            'l': location,
            'sort': 'date',
            'limit': limit,
            'format': 'json',
            'v': '2'
        }
        
        if company:
            params['company'] = company
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            data = response.json()
            return data.get('results', [])
        except Exception as e:
            logger.error(f"Indeed API error: {e}")
            return []


class DirectCareerScraper:
    """Scrape company career pages directly."""
    
    COMPANY_URLS = {
        'adobe': 'https://careers.adobe.com/us/en/search-results',
        'autodesk': 'https://careers.autodesk.com/us/en/search-results',
        'atlassian': 'https://www.atlassian.com/company/careers/all-jobs',
        'salesforce': 'https://careers.salesforce.com/en/jobs/',
        'servicenow': 'https://careers.servicenow.com/careers',
        'intuit': 'https://careers.intuit.com/us/en/search-results',
        'microsoft': 'https://careers.microsoft.com/us/en/search-results',
        'google': 'https://careers.google.com/jobs/',
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_company(self, company: str) -> List[JobPosting]:
        """Scrape specific company career page."""
        url = self.COMPANY_URLS.get(company.lower())
        if not url:
            logger.warning(f"No URL configured for {company}")
            return []
        
        try:
            logger.info(f"Scraping {company} careers...")
            response = self.session.get(url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Generic extraction (customize per company)
            jobs = []
            job_cards = soup.find_all(['div', 'article'], class_=re.compile('job|position|listing', re.I))
            
            for card in job_cards[:20]:  # Limit to 20
                title_elem = card.find(['h2', 'h3', 'a'], class_=re.compile('title|job-title', re.I))
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                
                # Filter for AI-related
                if not any(kw in title.lower() for kw in ['ai', 'machine learning', 'ml', 'generative', 'llm']):
                    continue
                
                # Extract other fields
                location_elem = card.find(['span', 'div'], class_=re.compile('location', re.I))
                location = location_elem.get_text(strip=True) if location_elem else 'Unknown'
                
                date_elem = card.find(['span', 'time'], class_=re.compile('date|posted', re.I))
                date_text = date_elem.get_text(strip=True) if date_elem else 'Recently'
                
                job = JobPosting(
                    company=company,
                    title=title,
                    location=location,
                    description=title,  # Simplified
                    date_posted=datetime.now() - timedelta(days=1),  # Approximate
                    seniority='unknown',
                    ai_relevance_score=0.5,  # Placeholder
                    specific_technologies=[],
                    url=url,
                    source='direct',
                    scraped_at=datetime.now()
                )
                jobs.append(job)
            
            logger.info(f"  Found {len(jobs)} AI-related jobs")
            return jobs
            
        except Exception as e:
            logger.error(f"Error scraping {company}: {e}")
            return []


class MultiSourceJobScraper:
    """Unified scraper using multiple sources."""
    
    def __init__(self, indeed_api_key: str = None):
        self.indeed = IndeedAPIClient(indeed_api_key) if indeed_api_key else None
        self.direct = DirectCareerScraper()
        self.scorer = JobScorer()
        self.results_dir = Path("data/job_postings")
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def search_indeed(self, company: str = None, keywords: List[str] = None) -> List[JobPosting]:
        """Search Indeed API."""
        if not self.indeed:
            logger.warning("No Indeed API key configured")
            return []
        
        query = ' OR '.join(keywords) if keywords else 'artificial intelligence'
        logger.info(f"Searching Indeed: {query}")
        
        results = self.indeed.search(query=query, company=company, limit=50)
        
        postings = []
        for result in results:
            title = result.get('jobtitle', '')
            desc = result.get('snippet', '')
            score = self.scorer.score_posting(title, desc)
            
            posting = JobPosting(
                company=result.get('company', company or 'Unknown'),
                title=title,
                location=result.get('formattedLocation', 'Unknown'),
                description=desc,
                date_posted=datetime.strptime(result.get('date', ''), '%a, %d %b %Y %H:%M:%S %Z') if result.get('date') else datetime.now(),
                seniority=score['seniority'],
                ai_relevance_score=score['ai_relevance'],
                specific_technologies=score['technologies'],
                url=result.get('url', ''),
                source='indeed',
                scraped_at=datetime.now()
            )
            postings.append(posting)
        
        return postings
    
    def search_direct(self, company: str) -> List[JobPosting]:
        """Search company career page directly."""
        return self.direct.scrape_company(company)
    
    def analyze_company_hybrid(self, company: str, ticker: str = None) -> Dict:
        """Analyze using both Indeed and direct scraping."""
        
        # Source 1: Indeed
        indeed_posts = self.search_indeed(company=company, 
                                         keywords=['AI', 'machine learning', 'generative', 'LLM'])
        
        # Source 2: Direct
        direct_posts = self.search_direct(company)
        
        # Combine and deduplicate
        all_posts = indeed_posts + direct_posts
        
        if not all_posts:
            return {
                'company': company,
                'ticker': ticker,
                'total_postings': 0,
                'analysis': 'No AI-related job postings found'
            }
        
        # Score and analyze
        high_relevance = [p for p in all_posts if p.ai_relevance_score > 0.7]
        moderate_relevance = [p for p in all_posts if 0.5 <= p.ai_relevance_score <= 0.7]
        
        all_technologies = []
        for post in all_posts:
            all_technologies.extend(post.specific_technologies)
        tech_counts = {tech: all_technologies.count(tech) for tech in set(all_technologies)}
        
        # Predictive signal
        if len(high_relevance) >= 3:
            signal = 'STRONG_AI_PIVOT'
            prediction = f"{company} likely launching major AI product in 6-9 months"
        elif len(high_relevance) >= 1 or len(moderate_relevance) >= 3:
            signal = 'MODERATE_AI_INVESTMENT'
            prediction = f"{company} investing in AI capabilities, product in 12-18 months"
        elif len(all_posts) >= 5:
            signal = 'WEAK_AI_SIGNAL'
            prediction = f"{company} has some AI hiring, but not disruptive level"
        else:
            signal = 'NO_AI_SIGNAL'
            prediction = f"{company} not significantly investing in AI (defensive posture)"
        
        # Save results
        self._save_results(company, all_posts)
        
        return {
            'company': company,
            'ticker': ticker,
            'analysis_date': datetime.now().isoformat(),
            'total_postings': len(all_posts),
            'indeed_count': len(indeed_posts),
            'direct_count': len(direct_posts),
            'high_relevance': len(high_relevance),
            'moderate_relevance': len(moderate_relevance),
            'top_technologies': sorted(tech_counts.items(), key=lambda x: -x[1])[:5],
            'signal': signal,
            'prediction': prediction,
            'average_relevance': sum(p.ai_relevance_score for p in all_posts) / len(all_posts),
            'recent_postings': [asdict(p) for p in all_posts[:5]]
        }
    
    def _save_results(self, company: str, postings: List[JobPosting]):
        """Save scraping results to file."""
        filename = f"{company.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.json"
        filepath = self.results_dir / filename
        
        data = {
            'company': company,
            'scraped_at': datetime.now().isoformat(),
            'postings': [asdict(p) for p in postings]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Saved {len(postings)} postings to {filepath}")


def create_sample_watchlist():
    """Create sample watchlist for testing."""
    watchlist = [
        {'name': 'Adobe', 'ticker': 'ADBE', 'sector': 'SaaS'},
        {'name': 'Autodesk', 'ticker': 'ADSK', 'sector': 'SaaS'},
        {'name': 'Atlassian', 'ticker': 'TEAM', 'sector': 'SaaS'},
        {'name': 'Intuit', 'ticker': 'INTU', 'sector': 'SaaS'},
        {'name': 'Salesforce', 'ticker': 'CRM', 'sector': 'SaaS'},
        {'name': 'ServiceNow', 'ticker': 'NOW', 'sector': 'SaaS'},
    ]
    
    filepath = Path('data/job_watchlist.json')
    filepath.parent.mkdir(exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(watchlist, f, indent=2)
    
    print(f"Created sample watchlist at {filepath}")
    return str(filepath)


def main():
    parser = argparse.ArgumentParser(description='Multi-Source Job Scraper')
    parser.add_argument('--company', type=str, help='Company name to analyze')
    parser.add_argument('--ticker', type=str, help='Stock ticker')
    parser.add_argument('--watchlist', type=str, help='Watchlist JSON file')
    parser.add_argument('--indeed-key', type=str, help='Indeed Publisher API key')
    parser.add_argument('--source', type=str, choices=['indeed', 'direct', 'hybrid'], 
                       default='hybrid', help='Data source')
    parser.add_argument('--create-watchlist', action='store_true', 
                       help='Create sample watchlist')
    
    args = parser.parse_args()
    
    if args.create_watchlist:
        create_sample_watchlist()
        return
    
    scraper = MultiSourceJobScraper(indeed_api_key=args.indeed_key)
    
    if args.watchlist:
        with open(args.watchlist, 'r') as f:
            watchlist = json.load(f)
        
        print(f"\nAnalyzing {len(watchlist)} companies...\n")
        for company_info in watchlist:
            result = scraper.analyze_company_hybrid(
                company_info['name'], 
                company_info.get('ticker')
            )
            print(f"\n{result['company']}:")
            print(f"  Signal: {result['signal']}")
            print(f"  AI Postings: {result['total_postings']}")
            print(f"  Prediction: {result['prediction'][:60]}...")
            time.sleep(1)
    
    elif args.company:
        result = scraper.analyze_company_hybrid(args.company, args.ticker)
        print(json.dumps(result, indent=2, default=str))
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
