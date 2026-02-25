#!/usr/bin/env python3
"""
Nightly Wrap — Daily Log Consolidation Script

Automated consolidation of raw daily logs into Durable Facts.
Triggered at 05:00 HKT after US market close.

Usage:
    python nightly_wrap.py --date 2026-02-16 [--dry-run]

Process:
    1. Read today's raw log
    2. Validate observations against price action (via aitrading_schema)
    3. Extract 5-10 Durable Facts
    4. Append to MEMORY.md
    5. Archive raw log
    6. Run fact decay
"""

import argparse
import gzip
import json
import os
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Paths
WORKSPACE = Path("/home/ubuntu/.openclaw/workspace/trade-algo-researcher")
MEMORY_DIR = WORKSPACE / "memory"
ARCHIVE_DIR = MEMORY_DIR / "archive" / "daily"
FACTS_DIR = MEMORY_DIR / "facts"
MEMORY_MD = WORKSPACE / "MEMORY.md"
CONTEXT_MD = WORKSPACE / "context.md"

# Ensure directories exist
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
FACTS_DIR.mkdir(parents=True, exist_ok=True)


def parse_daily_log(date_str: str) -> Dict:
    """Parse raw daily log and extract sections."""
    log_file = MEMORY_DIR / f"{date_str}.md"
    
    if not log_file.exists():
        print(f"⚠️  No daily log found for {date_str}")
        return {}
    
    with open(log_file, 'r') as f:
        content = f.read()
    
    # Extract sections
    sections = {}
    
    # Raw News
    news_match = re.search(r'## 📰 Raw News.*?\n(.*?)(?=## |\Z)', content, re.DOTALL)
    if news_match:
        sections['raw_news'] = news_match.group(1).strip()
    
    # Key Person Moves
    kp_match = re.search(r'## 🎯 Key Person Moves.*?\n(.*?)(?=## |\Z)', content, re.DOTALL)
    if kp_match:
        sections['key_persons'] = kp_match.group(1).strip()
    
    # Price Action
    pa_match = re.search(r'## 📈 Price Action Observations.*?\n(.*?)(?=## |\Z)', content, re.DOTALL)
    if pa_match:
        sections['price_action'] = pa_match.group(1).strip()
    
    # Hypotheses
    hyp_match = re.search(r'## 🔬 Hypotheses Being Tested.*?\n(.*?)(?=## |\Z)', content, re.DOTALL)
    if hyp_match:
        sections['hypotheses'] = hyp_match.group(1).strip()
    
    # Errors/Lessons
    err_match = re.search(r'## ⚠️ Errors.*?\n(.*?)(?=## |\Z)', content, re.DOTALL)
    if err_match:
        sections['errors'] = err_match.group(1).strip()
    
    # End-of-session summary
    summary_match = re.search(r'## 🏁 End-of-Session Summary.*?\n(.*?)(?=---|\Z)', content, re.DOTALL)
    if summary_match:
        sections['summary'] = summary_match.group(1).strip()
    
    return sections


def validate_observations(observations: List[str], date_str: str) -> List[Dict]:
    """
    Validate observations against price action.
    In production, this would query aitrading_schema.
    For now, placeholder implementation.
    """
    validated = []
    
    for obs in observations:
        # Skip empty lines
        if not obs.strip():
            continue
        
        # Simple heuristic validation
        # In production: Query database for actual prices
        validation = {
            'observation': obs.strip(),
            'validated': None,  # Would check against actual price action
            'confidence': 0.7,  # Base confidence
            'price_check': 'pending_db_query'
        }
        
        # Boost confidence for certain patterns
        if 'dropped' in obs.lower() and '%' in obs:
            validation['confidence'] = 0.85
        elif 'earnings' in obs.lower():
            validation['confidence'] = 0.9
        elif 'guidance' in obs.lower():
            validation['confidence'] = 0.9
        
        validated.append(validation)
    
    return validated


def extract_durable_facts(sections: Dict, date_str: str) -> List[Dict]:
    """Extract 5-10 Durable Facts from daily log sections."""
    facts = []
    
    # Extract from end-of-session summary (preferred)
    if 'summary' in sections:
        summary_lines = sections['summary'].split('\n')
        for line in summary_lines:
            # Look for numbered items in Key Facts section
            match = re.match(r'^\d+\.\s+(.+)$', line.strip())
            if match and len(facts) < 10:
                fact_text = match.group(1).strip()
                if len(fact_text) > 20:  # Skip trivial entries
                    facts.append({
                        'date': date_str,
                        'fact': fact_text,
                        'source': 'daily_log_summary',
                        'confidence': 0.8,
                        'weight': 0.8,
                        'expiry': (datetime.strptime(date_str, '%Y-%m-%d') + timedelta(days=180)).strftime('%Y-%m-%d')
                    })
    
    # Extract from raw news if we need more
    if len(facts) < 5 and 'raw_news' in sections:
        news_lines = [l for l in sections['raw_news'].split('\n') if l.strip().startswith('-')]
        for line in news_lines[:5]:
            if len(facts) >= 10:
                break
            fact_text = line.strip('- ').strip()
            if len(fact_text) > 30:
                facts.append({
                    'date': date_str,
                    'fact': fact_text,
                    'source': 'raw_news',
                    'confidence': 0.6,
                    'weight': 0.6,
                    'expiry': (datetime.strptime(date_str, '%Y-%m-%d') + timedelta(days=90)).strftime('%Y-%m-%d')
                })
    
    # Extract from price action if we need more
    if len(facts) < 5 and 'price_action' in sections:
        pa_lines = [l for l in sections['price_action'].split('\n') if '|' in l and 'Ticker' not in l]
        for line in pa_lines[:3]:
            if len(facts) >= 10:
                break
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3:
                fact_text = f"{parts[0]} moved {parts[1]} with {parts[2]} volume"
                facts.append({
                    'date': date_str,
                    'fact': fact_text,
                    'source': 'price_action',
                    'confidence': 0.9,
                    'weight': 0.9,
                    'expiry': (datetime.strptime(date_str, '%Y-%m-%d') + timedelta(days=30)).strftime('%Y-%m-%d')
                })
    
    return facts[:10]  # Enforce maximum 10 facts


def append_to_memory_md(facts: List[Dict], date_str: str):
    """Append Durable Facts to MEMORY.md."""
    
    # Read existing MEMORY.md
    if MEMORY_MD.exists():
        with open(MEMORY_MD, 'r') as f:
            content = f.read()
    else:
        content = "# MEMORY.md\n\n## Durable Facts (Auto-Consolidated)\n\n"
    
    # Check if we already have facts for this date
    if f"[{date_str}]" in content:
        print(f"⚠️  Facts for {date_str} already in MEMORY.md — skipping")
        return
    
    # Format new facts
    new_facts_section = f"\n### [{date_str}] Daily Consolidation\n\n"
    for i, fact in enumerate(facts, 1):
        new_facts_section += f"{i}. **{fact['fact']}** | Weight: {fact['weight']:.2f} | Expiry: {fact['expiry']}\n"
    
    new_facts_section += "\n"
    
    # Find insertion point (after "## Durable Facts" section)
    if "## Durable Facts" in content:
        # Insert after the header
        parts = content.split("## Durable Facts", 1)
        new_content = parts[0] + "## Durable Facts" + new_facts_section + parts[1]
    else:
        # Append to end
        new_content = content + new_facts_section
    
    # Write back
    with open(MEMORY_MD, 'w') as f:
        f.write(new_content)
    
    print(f"✅ Appended {len(facts)} facts to MEMORY.md")


def archive_raw_log(date_str: str, dry_run: bool = False):
    """Archive and compress raw daily log."""
    source = MEMORY_DIR / f"{date_str}.md"
    dest = ARCHIVE_DIR / f"{date_str}.md.gz"
    
    if not source.exists():
        print(f"⚠️  No raw log to archive for {date_str}")
        return
    
    if dry_run:
        print(f"[DRY RUN] Would archive {source} to {dest}")
        return
    
    # Compress and move
    with open(source, 'rb') as f_in:
        with gzip.open(dest, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    # Remove original
    source.unlink()
    
    print(f"✅ Archived {source.name} to {dest}")


def update_context_md(date_str: str, facts: List[Dict]):
    """Update context.md with key facts from today."""
    if not CONTEXT_MD.exists():
        return
    
    with open(CONTEXT_MD, 'r') as f:
        content = f.read()
    
    # Add "Last Consolidation" timestamp
    content = re.sub(
        r'\*\*Last Updated:\*\* \d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC',
        f'**Last Updated:** {date_str} (Nightly Wrap Complete)',
        content
    )
    
    with open(CONTEXT_MD, 'w') as f:
        f.write(content)


def run_fact_decay(dry_run: bool = False):
    """Run fact store decay."""
    import subprocess
    
    cmd = ["python3", "fact_store.py", "decay"]
    if not dry_run:
        cmd.append("--apply")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=WORKSPACE)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
    except Exception as e:
        print(f"⚠️  Fact decay error: {e}")


def main():
    parser = argparse.ArgumentParser(description='Nightly Wrap — Daily Log Consolidation')
    parser.add_argument('--date', type=str, default=datetime.now().strftime('%Y-%m-%d'),
                       help='Date to process (YYYY-MM-DD)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview without making changes')
    args = parser.parse_args()
    
    date_str = args.date
    print(f"\n🌙 NIGHTLY WRAP: Processing {date_str}")
    print("=" * 50)
    
    # Step 1: Parse daily log
    print("\n📖 Step 1: Parsing daily log...")
    sections = parse_daily_log(date_str)
    if not sections:
        print("❌ No content to process")
        return
    print(f"✅ Found sections: {list(sections.keys())}")
    
    # Step 2: Validate observations
    print("\n✅ Step 2: Validating observations...")
    # In production: Query aitrading_schema
    print("[Would query aitrading_schema for price validation]")
    
    # Step 3: Extract Durable Facts
    print("\n🔍 Step 3: Extracting Durable Facts...")
    facts = extract_durable_facts(sections, date_str)
    print(f"✅ Extracted {len(facts)} facts:")
    for i, fact in enumerate(facts, 1):
        print(f"   {i}. {fact['fact'][:60]}... (weight: {fact['weight']:.2f})")
    
    if not facts:
        print("⚠️  No facts extracted — check daily log format")
        return
    
    # Step 4: Append to MEMORY.md
    print("\n📝 Step 4: Appending to MEMORY.md...")
    if not args.dry_run:
        append_to_memory_md(facts, date_str)
    else:
        print(f"[DRY RUN] Would append {len(facts)} facts to MEMORY.md")
    
    # Step 5: Archive raw log
    print("\n📦 Step 5: Archiving raw log...")
    archive_raw_log(date_str, dry_run=args.dry_run)
    
    # Step 6: Update context.md
    print("\n🔄 Step 6: Updating context.md...")
    if not args.dry_run:
        update_context_md(date_str, facts)
    
    # Step 7: Run fact decay
    print("\n🧹 Step 7: Running fact decay...")
    run_fact_decay(dry_run=args.dry_run)
    
    print("\n" + "=" * 50)
    print(f"✅ Nightly Wrap Complete for {date_str}")
    print(f"   Facts consolidated: {len(facts)}")
    print(f"   Raw log archived: {date_str}.md.gz")
    print(f"   Ready for next session with clean slate")


if __name__ == '__main__':
    main()
