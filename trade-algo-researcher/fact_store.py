#!/usr/bin/env python3
"""
Fact Store Manager
Utilities for working with the evidence-weighted JSONL fact store.

Usage:
    python fact_store.py query --entity ARASO --min-weight 0.7
    python fact_store.py decay
    python fact_store.py archive --threshold 0.3
"""

import json
import os
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Optional
import argparse

FACTS_DIR = Path("/home/ubuntu/.openclaw/workspace/trade-algo-researcher/memory/facts")
ARCHIVE_DIR = Path("/home/ubuntu/.openclaw/workspace/trade-algo-researcher/memory/archive")
DECAY_LAMBDA = 0.01  # Half-life ~69 days


def load_facts(filepath: Path) -> List[Dict]:
    """Load facts from JSONL file."""
    facts = []
    if not filepath.exists():
        return facts
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                facts.append(json.loads(line))
    return facts


def save_facts(filepath: Path, facts: List[Dict]):
    """Save facts to JSONL file."""
    with open(filepath, 'w') as f:
        for fact in facts:
            f.write(json.dumps(fact) + '\n')


def calculate_decayed_weight(fact: Dict, as_of: Optional[datetime] = None) -> float:
    """Calculate current weight with exponential decay."""
    if as_of is None:
        as_of = datetime.now(timezone.utc)
    
    created_str = fact['timestamp'].replace('Z', '+00:00')
    created = datetime.fromisoformat(created_str)
    days_elapsed = (as_of - created).days
    
    initial_weight = fact.get('weight', fact.get('confidence', 0.5))
    decayed = initial_weight * math.exp(-DECAY_LAMBDA * days_elapsed)
    
    return round(decayed, 4)


def query_facts(
    entity: Optional[str] = None,
    fact_type: Optional[str] = None,
    tags: Optional[List[str]] = None,
    min_weight: float = 0.0,
    after: Optional[str] = None,
    before: Optional[str] = None
) -> List[Dict]:
    """Query facts with filters."""
    results = []
    
    for fact_file in FACTS_DIR.glob('*.jsonl'):
        facts = load_facts(fact_file)
        
        for fact in facts:
            # Apply filters
            if entity and fact.get('entity') != entity:
                continue
            if fact_type and fact.get('fact_type') != fact_type:
                continue
            if tags and not any(tag in fact.get('tags', []) for tag in tags):
                continue
            if after and fact['timestamp'] < after:
                continue
            if before and fact['timestamp'] > before:
                continue
            
            # Calculate current weight
            current_weight = calculate_decayed_weight(fact)
            if current_weight < min_weight:
                continue
            
            fact['current_weight'] = current_weight
            results.append(fact)
    
    # Sort by weight descending, then timestamp
    results.sort(key=lambda x: (-x['current_weight'], x['timestamp']))
    return results


def decay_all_facts(dry_run: bool = True) -> Dict:
    """Apply decay to all facts and report."""
    stats = {'total': 0, 'archived': 0, 'updated': 0}
    
    for fact_file in FACTS_DIR.glob('*.jsonl'):
        facts = load_facts(fact_file)
        new_facts = []
        
        for fact in facts:
            stats['total'] += 1
            current_weight = calculate_decayed_weight(fact)
            
            if current_weight < 0.3:
                # Archive low-weight facts
                archive_path = ARCHIVE_DIR / 'low_confidence' / fact_file.name
                archive_path.parent.mkdir(parents=True, exist_ok=True)
                
                if not dry_run:
                    with open(archive_path, 'a') as f:
                        fact['archived_at'] = datetime.now(timezone.utc).isoformat()
                        fact['archive_reason'] = 'weight_decay'
                        f.write(json.dumps(fact) + '\n')
                stats['archived'] += 1
            else:
                fact['current_weight'] = current_weight
                new_facts.append(fact)
                stats['updated'] += 1
        
        if not dry_run:
            save_facts(fact_file, new_facts)
    
    return stats


def format_fact(fact: Dict) -> str:
    """Format a fact for display."""
    lines = [
        f"[{fact['timestamp'][:10]}] {fact['fact_type'].upper()}",
        f"  Entity: {fact.get('entity', 'N/A')}",
        f"  Fact: {fact['fact']}",
        f"  Weight: {fact.get('current_weight', fact.get('weight', 'N/A')):.3f}",
        f"  Confidence: {fact['confidence']:.2f}",
        f"  Tags: {', '.join(fact.get('tags', []))}",
        ""
    ]
    return '\n'.join(lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fact Store Manager')
    subparsers = parser.add_subparsers(dest='command')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Query facts')
    query_parser.add_argument('--entity', help='Filter by entity')
    query_parser.add_argument('--type', help='Filter by fact type')
    query_parser.add_argument('--tags', nargs='+', help='Filter by tags')
    query_parser.add_argument('--min-weight', type=float, default=0.0)
    query_parser.add_argument('--after', help='After date (YYYY-MM-DD)')
    query_parser.add_argument('--limit', type=int, default=10)
    
    # Decay command
    decay_parser = subparsers.add_parser('decay', help='Apply decay to all facts')
    decay_parser.add_argument('--apply', action='store_true', help='Actually apply changes (default dry-run)')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show fact store statistics')
    
    args = parser.parse_args()
    
    if args.command == 'query':
        results = query_facts(
            entity=args.entity,
            fact_type=args.type,
            tags=args.tags,
            min_weight=args.min_weight,
            after=args.after
        )
        print(f"Found {len(results)} facts:\n")
        for fact in results[:args.limit]:
            print(format_fact(fact))
    
    elif args.command == 'decay':
        stats = decay_all_facts(dry_run=not args.apply)
        print(f"Decay run {'(APPLIED)' if args.apply else '(DRY RUN)'}:")
        print(f"  Total facts: {stats['total']}")
        print(f"  To be archived: {stats['archived']}")
        print(f"  Surviving: {stats['updated']}")
    
    elif args.command == 'stats':
        total_facts = 0
        by_type = {}
        by_source = {}
        
        for fact_file in FACTS_DIR.glob('*.jsonl'):
            facts = load_facts(fact_file)
            total_facts += len(facts)
            for fact in facts:
                by_type[fact.get('fact_type', 'unknown')] = by_type.get(fact.get('fact_type', 'unknown'), 0) + 1
                by_source[fact.get('source', 'unknown')] = by_source.get(fact.get('source', 'unknown'), 0) + 1
        
        print(f"Fact Store Statistics:")
        print(f"  Total facts: {total_facts}")
        print(f"\nBy type:")
        for t, c in sorted(by_type.items(), key=lambda x: -x[1]):
            print(f"    {t}: {c}")
        print(f"\nBy source:")
        for s, c in sorted(by_source.items(), key=lambda x: -x[1]):
            print(f"    {s}: {c}")
    
    else:
        parser.print_help()
